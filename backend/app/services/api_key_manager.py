import hashlib
import secrets
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import asyncio
from cryptography.fernet import Fernet
import base64

from app.models.api_keys import (
    SupportedService, APIKeyRequest, APIKeySubmission, 
    UserAPIKeys, AgentCapabilities, SERVICE_CONFIGS, 
    AGENT_SERVICE_MAPPING
)
from app.core.logging import get_logger
from app.services.supabase_service import supabase_service

logger = get_logger(__name__)

class APIKeyManager:
    """Manages API keys securely with Supabase persistence and in-memory caching"""
    
    def __init__(self):
        # Generate encryption key for in-memory caching
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # In-memory cache for fast access (session_id -> user_id mapping and cached keys)
        self.session_cache: Dict[str, str] = {}  # session_id -> user_id
        self.key_cache: Dict[str, Dict[SupportedService, str]] = {}  # user_id -> {service: decrypted_key}
        self.cache_timestamps: Dict[str, datetime] = {}  # user_id -> last_cache_time
        
        # Cache TTL (5 minutes)
        self.cache_ttl = timedelta(minutes=5)
        
    def _get_user_id(self, session_id: str) -> str:
        """Get or generate user_id for session_id"""
        if session_id not in self.session_cache:
            # For now, use session_id as user_id (in production, integrate with auth system)
            self.session_cache[session_id] = session_id
        return self.session_cache[session_id]
    
    def _is_cache_valid(self, user_id: str) -> bool:
        """Check if cache is still valid for user"""
        if user_id not in self.cache_timestamps:
            return False
        return datetime.utcnow() - self.cache_timestamps[user_id] < self.cache_ttl
    
    def _encrypt_key(self, api_key: str) -> str:
        """Encrypt API key for in-memory cache"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key from in-memory cache"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    async def request_api_key(
        self, 
        agent_name: str, 
        service: SupportedService, 
        session_id: str,
        reason: str = None
    ) -> APIKeyRequest:
        """Agent requests API key from user"""
        
        if service not in SERVICE_CONFIGS:
            raise ValueError(f"Unsupported service: {service}")
        
        config = SERVICE_CONFIGS[service]
        
        # Default reason if not provided
        if not reason:
            reason = f"I need access to {service.value} to help you with {', '.join(config.capabilities[:2])}"
        
        request = APIKeyRequest(
            agent_name=agent_name,
            service=service,
            reason=reason,
            capabilities_unlocked=config.capabilities,
            setup_instructions=config.instructions,
            is_required=True
        )
        
        logger.info(f"Agent {agent_name} requesting {service.value} API key", 
                   session_id=session_id, reason=reason)
        
        return request
    
    async def submit_api_key(self, submission: APIKeySubmission) -> bool:
        """User submits API key"""
        
        try:
            # Validate key format (basic validation)
            if not self._validate_api_key_format(submission.service, submission.api_key):
                logger.warning(f"Invalid API key format for {submission.service.value}")
                return False
            
            user_id = self._get_user_id(submission.session_id)
            
            # Store in Supabase if available
            if supabase_service.is_available():
                service_name = SERVICE_CONFIGS[submission.service].service.value.replace('_', ' ').title()
                success = await supabase_service.store_api_key(
                    user_id=user_id,
                    service=submission.service,
                    service_name=service_name,
                    api_key=submission.api_key
                )
                
                if not success:
                    logger.error("Failed to store API key in Supabase")
                    return False
            
            # Update in-memory cache
            if user_id not in self.key_cache:
                self.key_cache[user_id] = {}
            
            encrypted_key = self._encrypt_key(submission.api_key)
            self.key_cache[user_id][submission.service] = encrypted_key
            self.cache_timestamps[user_id] = datetime.utcnow()
            
            logger.info(f"API key stored for {submission.service.value}", 
                       session_id=submission.session_id, user_id=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing API key: {str(e)}")
            return False
    
    def _validate_api_key_format(self, service: SupportedService, api_key: str) -> bool:
        """Basic API key format validation"""
        
        validators = {
            SupportedService.OPENAI: lambda k: k.startswith('sk-') and len(k) > 20,
            SupportedService.FAL_AI: lambda k: len(k) > 10,  # Basic length check
            SupportedService.GITHUB: lambda k: k.startswith('ghp_') or k.startswith('github_pat_'),
            SupportedService.SLACK: lambda k: k.startswith('xoxb-') or k.startswith('xoxp-'),
            SupportedService.NOTION: lambda k: k.startswith('secret_') and len(k) > 30,
            SupportedService.RESEND: lambda k: k.startswith('re_') and len(k) > 10,
        }
        
        validator = validators.get(service, lambda k: len(k) > 5)
        return validator(api_key)
    
    async def get_api_key(self, session_id: str, service: SupportedService) -> Optional[str]:
        """Get decrypted API key for use"""
        
        user_id = self._get_user_id(session_id)
        
        # Try cache first if valid
        if self._is_cache_valid(user_id) and user_id in self.key_cache:
            encrypted_key = self.key_cache[user_id].get(service)
            if encrypted_key:
                try:
                    return self._decrypt_key(encrypted_key)
                except Exception as e:
                    logger.error(f"Error decrypting cached key: {str(e)}")
        
        # Fallback to Supabase
        if supabase_service.is_available():
            try:
                api_key = await supabase_service.get_api_key(user_id, service)
                if api_key:
                    # Update cache
                    if user_id not in self.key_cache:
                        self.key_cache[user_id] = {}
                    self.key_cache[user_id][service] = self._encrypt_key(api_key)
                    self.cache_timestamps[user_id] = datetime.utcnow()
                    
                    # Log usage
                    await supabase_service.log_api_key_usage(
                        user_id=user_id,
                        service=service,
                        operation="retrieve",
                        success=True
                    )
                    
                    return api_key
            except Exception as e:
                logger.error(f"Error retrieving API key from Supabase: {str(e)}")
        
        return None
    
    async def get_agent_capabilities(self, agent_name: str, session_id: str) -> AgentCapabilities:
        """Get what an agent can do based on available API keys"""
        
        # Get services this agent can use
        agent_services = AGENT_SERVICE_MAPPING.get(agent_name, [])
        
        # Check which keys are available
        available_services = []
        missing_services = []
        
        for service in agent_services:
            if await self.get_api_key(session_id, service):
                available_services.append(service)
            else:
                missing_services.append(service)
        
        # Build available actions
        available_actions = []
        for service in available_services:
            if service in SERVICE_CONFIGS:
                config = SERVICE_CONFIGS[service]
                available_actions.extend([f"✅ {cap}" for cap in config.capabilities])
        
        # Build setup suggestions for missing keys
        setup_suggestions = []
        for service in missing_services:
            if service in SERVICE_CONFIGS:
                config = SERVICE_CONFIGS[service]
                suggestion = APIKeyRequest(
                    agent_name=agent_name,
                    service=service,
                    reason=f"Unlock {', '.join(config.capabilities[:2])} capabilities",
                    capabilities_unlocked=config.capabilities,
                    setup_instructions=config.instructions
                )
                setup_suggestions.append(suggestion)
        
        return AgentCapabilities(
            agent_name=agent_name,
            available_actions=available_actions,
            missing_keys=missing_services,
            setup_suggestions=setup_suggestions
        )
    
    async def get_session_status(self, session_id: str) -> Dict:
        """Get status of user's API keys"""
        
        user_id = self._get_user_id(session_id)
        
        # Try to get from Supabase first
        if supabase_service.is_available():
            try:
                user_keys = await supabase_service.get_user_keys(user_id)
                if user_keys:
                    return {
                        "session_exists": True,
                        "keys_count": len(user_keys),
                        "services": list(user_keys.keys()),
                        "user_id": user_id,
                        "keys_details": user_keys
                    }
            except Exception as e:
                logger.error(f"Error getting user keys from Supabase: {str(e)}")
        
        # Fallback to cache
        if user_id in self.key_cache:
            return {
                "session_exists": True,
                "keys_count": len(self.key_cache[user_id]),
                "services": [service.value for service in self.key_cache[user_id].keys()],
                "user_id": user_id,
                "cache_only": True
            }
        
        return {
            "session_exists": False,
            "keys_count": 0,
            "services": [],
            "user_id": user_id
        }
    
    async def revoke_api_key(self, session_id: str, service: SupportedService) -> bool:
        """Revoke API key for a specific service"""
        
        user_id = self._get_user_id(session_id)
        
        try:
            # Remove from Supabase
            if supabase_service.is_available():
                await supabase_service.delete_api_key(user_id, service)
            
            # Remove from cache
            if user_id in self.key_cache and service in self.key_cache[user_id]:
                del self.key_cache[user_id][service]
                if not self.key_cache[user_id]:  # If no keys left, remove user from cache
                    del self.key_cache[user_id]
                    if user_id in self.cache_timestamps:
                        del self.cache_timestamps[user_id]
            
            logger.info(f"API key revoked for {service.value} - user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            return False
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all API keys for a session"""
        
        user_id = self._get_user_id(session_id)
        
        try:
            # Clear from Supabase
            if supabase_service.is_available():
                await supabase_service.clear_user_session(user_id)
            
            # Clear from cache
            if user_id in self.key_cache:
                del self.key_cache[user_id]
            if user_id in self.cache_timestamps:
                del self.cache_timestamps[user_id]
            if session_id in self.session_cache:
                del self.session_cache[session_id]
            
            logger.info(f"Session cleared - user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return False
    
    async def get_service_integrations(self) -> List[Dict]:
        """Get service integration configurations from Supabase"""
        
        if supabase_service.is_available():
            try:
                return await supabase_service.get_service_integrations()
            except Exception as e:
                logger.error(f"Error getting service integrations: {str(e)}")
        
        # Fallback to static configs
        integrations = []
        for service, config in SERVICE_CONFIGS.items():
            integrations.append({
                'service': service.value,
                'service_name': service.value.replace('_', ' ').title(),
                'description': f"Integration for {', '.join(config.capabilities[:2])}",
                'api_base_url': config.setup_url,
                'documentation_url': config.setup_url,
                'key_format_description': config.instructions,
                'supported_operations': config.capabilities,
                'required_permissions': config.required_scopes
            })
        
        return integrations
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_users = []
        
        for user_id, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            if user_id in self.key_cache:
                del self.key_cache[user_id]
            del self.cache_timestamps[user_id]
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired cache entries")
    
    async def sync_with_supabase(self, session_id: str) -> bool:
        """Sync session data with Supabase"""
        
        if not supabase_service.is_available():
            return False
        
        try:
            user_id = self._get_user_id(session_id)
            
            # Get fresh data from Supabase
            user_keys = await supabase_service.get_user_keys(user_id)
            
            # Update cache
            if user_keys:
                self.key_cache[user_id] = {}
                for service_name, key_info in user_keys.items():
                    try:
                        service = SupportedService(service_name)
                        # We don't cache the actual key, just mark it as available
                        # The key will be fetched from Supabase when needed
                        self.key_cache[user_id][service] = "available"
                    except ValueError:
                        logger.warning(f"Unknown service in Supabase: {service_name}")
                
                self.cache_timestamps[user_id] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing with Supabase: {str(e)}")
            return False

# Global instance
api_key_manager = APIKeyManager() 