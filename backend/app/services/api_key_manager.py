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

logger = get_logger(__name__)

class APIKeyManager:
    """Manages API keys securely with session-based storage"""
    
    def __init__(self):
        # Generate encryption key for this session (in production, use proper key management)
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # In-memory storage (in production, use Redis or secure database)
        self.session_keys: Dict[str, UserAPIKeys] = {}
        
    def _encrypt_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
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
            
            # Get or create user session
            if submission.session_id not in self.session_keys:
                self.session_keys[submission.session_id] = UserAPIKeys(
                    session_id=submission.session_id,
                    expires_at=datetime.utcnow() + timedelta(hours=24)  # 24-hour session
                )
            
            # Encrypt and store key
            encrypted_key = self._encrypt_key(submission.api_key)
            self.session_keys[submission.session_id].keys[submission.service] = encrypted_key
            
            logger.info(f"API key stored for {submission.service.value}", 
                       session_id=submission.session_id)
            
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
        
        if session_id not in self.session_keys:
            return None
        
        user_keys = self.session_keys[session_id]
        
        # Check if session expired
        if user_keys.expires_at and datetime.utcnow() > user_keys.expires_at:
            del self.session_keys[session_id]
            return None
        
        encrypted_key = user_keys.keys.get(service)
        if not encrypted_key:
            return None
        
        try:
            return self._decrypt_key(encrypted_key)
        except Exception as e:
            logger.error(f"Error decrypting API key: {str(e)}")
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
        
        if session_id not in self.session_keys:
            return {
                "session_exists": False,
                "keys_count": 0,
                "services": [],
                "expires_at": None
            }
        
        user_keys = self.session_keys[session_id]
        
        return {
            "session_exists": True,
            "keys_count": len(user_keys.keys),
            "services": list(user_keys.keys.keys()),
            "expires_at": user_keys.expires_at.isoformat() if user_keys.expires_at else None,
            "created_at": user_keys.created_at.isoformat()
        }
    
    async def revoke_api_key(self, session_id: str, service: SupportedService) -> bool:
        """Remove API key for a service"""
        
        if session_id not in self.session_keys:
            return False
        
        user_keys = self.session_keys[session_id]
        if service in user_keys.keys:
            del user_keys.keys[service]
            logger.info(f"API key revoked for {service.value}", session_id=session_id)
            return True
        
        return False
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all API keys for a session"""
        
        if session_id in self.session_keys:
            del self.session_keys[session_id]
            logger.info("Session cleared", session_id=session_id)
            return True
        
        return False

# Global instance
api_key_manager = APIKeyManager() 