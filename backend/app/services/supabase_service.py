from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
import secrets
import hashlib
from supabase import create_client, Client
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

from app.core.config import settings
from app.core.logging import get_logger
from app.models.api_keys import SupportedService

logger = get_logger(__name__)

class SupabaseService:
    """Handles Supabase database operations for API key storage using existing schema"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.master_key: Optional[bytes] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase client and master encryption key"""
        try:
            if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_ANON_KEY
                )
                
                # Initialize master key (in production, use proper key management)
                master_key = os.getenv('MASTER_ENCRYPTION_KEY')
                if master_key:
                    self.master_key = base64.urlsafe_b64decode(master_key)
                else:
                    # Generate new key for development
                    self.master_key = secrets.token_bytes(32)
                    logger.warning("Using generated master key - not suitable for production")
                
                logger.info("Supabase service initialized successfully")
            else:
                logger.warning("Supabase credentials not configured - using in-memory storage")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase service: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Supabase is available"""
        return self.client is not None and self.master_key is not None
    
    def _derive_key(self, user_id: str, salt: bytes) -> bytes:
        """Derive encryption key from master key and user ID"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key + user_id.encode())
    
    def _encrypt_api_key(self, api_key: str, user_id: str) -> Dict[str, str]:
        """Encrypt API key using AES-256-GCM"""
        try:
            # Generate salt and IV
            salt = secrets.token_bytes(32)
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Derive key
            key = self._derive_key(user_id, salt)
            
            # Encrypt
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(iv, api_key.encode(), None)
            
            # Split ciphertext and auth tag (last 16 bytes)
            encrypted_data = ciphertext[:-16]
            auth_tag = ciphertext[-16:]
            
            # Create integrity hash
            integrity_data = salt + iv + encrypted_data + auth_tag
            integrity_hash = hashlib.sha256(integrity_data).hexdigest()
            
            return {
                'encrypted_key': base64.b64encode(encrypted_data).decode(),
                'salt': base64.b64encode(salt).decode(),
                'iv': base64.b64encode(iv).decode(),
                'auth_tag': base64.b64encode(auth_tag).decode(),
                'integrity_hash': integrity_hash
            }
            
        except Exception as e:
            logger.error(f"Error encrypting API key: {str(e)}")
            raise
    
    def _decrypt_api_key(self, encrypted_data: Dict[str, str], user_id: str) -> str:
        """Decrypt API key using AES-256-GCM"""
        try:
            # Decode components
            salt = base64.b64decode(encrypted_data['salt'])
            iv = base64.b64decode(encrypted_data['iv'])
            encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
            auth_tag = base64.b64decode(encrypted_data['auth_tag'])
            
            # Verify integrity
            integrity_data = salt + iv + encrypted_key + auth_tag
            expected_hash = hashlib.sha256(integrity_data).hexdigest()
            if expected_hash != encrypted_data['integrity_hash']:
                raise ValueError("Integrity check failed")
            
            # Derive key and decrypt
            key = self._derive_key(user_id, salt)
            aesgcm = AESGCM(key)
            
            # Reconstruct ciphertext with auth tag
            ciphertext = encrypted_key + auth_tag
            plaintext = aesgcm.decrypt(iv, ciphertext, None)
            
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting API key: {str(e)}")
            raise
    
    def _generate_key_fingerprint(self, user_id: str, service: str) -> str:
        """Generate unique fingerprint for user+service combination"""
        data = f"{user_id}:{service}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def store_api_key(
        self, 
        user_id: str, 
        service: SupportedService, 
        service_name: str,
        api_key: str,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Store encrypted API key in Supabase using existing schema"""
        if not self.is_available():
            return False
        
        try:
            # Encrypt the API key
            encrypted_data = self._encrypt_api_key(api_key, user_id)
            
            # Default expiration: 30 days
            if not expires_at:
                expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Generate unique fingerprint
            fingerprint = self._generate_key_fingerprint(user_id, service.value)
            
            data = {
                'user_id': user_id,
                'service': service.value,
                'service_name': service_name,
                'encrypted_key': encrypted_data['encrypted_key'],
                'salt': encrypted_data['salt'],
                'iv': encrypted_data['iv'],
                'auth_tag': encrypted_data['auth_tag'],
                'integrity_hash': encrypted_data['integrity_hash'],
                'algorithm': 'AES-256-GCM',
                'kdf': 'PBKDF2-SHA256',
                'iterations': 100000,
                'key_fingerprint': fingerprint,
                'status': 'active',
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'usage_count': 0
            }
            
            # Upsert (insert or update based on user_id + service)
            result = self.client.table('encrypted_api_keys').upsert(
                data,
                on_conflict='user_id,service'
            ).execute()
            
            if result.data:
                logger.info(f"API key stored for {service.value} - user_id: {user_id}")
                return True
            else:
                logger.error("Failed to store API key - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error storing API key: {str(e)}")
            return False
    
    async def get_api_key(self, user_id: str, service: SupportedService) -> Optional[str]:
        """Retrieve and decrypt API key from Supabase"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.table('encrypted_api_keys').select('*').eq(
                'user_id', user_id
            ).eq('service', service.value).eq('status', 'active').execute()
            
            if not result.data:
                return None
            
            key_data = result.data[0]
            
            # Check if expired
            if key_data['expires_at']:
                expires_at = datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at.replace(tzinfo=None):
                    # Mark as expired
                    await self._update_key_status(key_data['id'], 'expired')
                    return None
            
            # Decrypt and return
            encrypted_data = {
                'encrypted_key': key_data['encrypted_key'],
                'salt': key_data['salt'],
                'iv': key_data['iv'],
                'auth_tag': key_data['auth_tag'],
                'integrity_hash': key_data['integrity_hash']
            }
            
            # Update usage count and last used
            await self._update_key_usage(key_data['id'])
            
            return self._decrypt_api_key(encrypted_data, user_id)
            
        except Exception as e:
            logger.error(f"Error retrieving API key: {str(e)}")
            return None
    
    async def get_user_keys(self, user_id: str) -> Dict[str, Any]:
        """Get all API keys for a user"""
        if not self.is_available():
            return {}
        
        try:
            result = self.client.table('encrypted_api_keys').select('*').eq(
                'user_id', user_id
            ).eq('status', 'active').execute()
            
            if not result.data:
                return {}
            
            keys = {}
            current_time = datetime.utcnow()
            
            for key_data in result.data:
                service = key_data['service']
                
                # Check expiration
                if key_data['expires_at']:
                    expires_at = datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00'))
                    if current_time > expires_at.replace(tzinfo=None):
                        await self._update_key_status(key_data['id'], 'expired')
                        continue
                
                keys[service] = {
                    'service': service,
                    'service_name': key_data['service_name'],
                    'created_at': key_data['created_at'],
                    'expires_at': key_data['expires_at'],
                    'last_used_at': key_data['last_used_at'],
                    'usage_count': key_data['usage_count'],
                    'status': key_data['status']
                }
            
            return keys
            
        except Exception as e:
            logger.error(f"Error getting user keys: {str(e)}")
            return {}
    
    async def delete_api_key(self, user_id: str, service: SupportedService) -> bool:
        """Delete API key from Supabase"""
        if not self.is_available():
            return False
        
        try:
            result = self.client.table('encrypted_api_keys').update({
                'status': 'revoked',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('service', service.value).execute()
            
            logger.info(f"API key revoked for {service.value} - user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            return False
    
    async def clear_user_session(self, user_id: str) -> bool:
        """Revoke all API keys for a user"""
        if not self.is_available():
            return False
        
        try:
            result = self.client.table('encrypted_api_keys').update({
                'status': 'revoked',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            logger.info(f"User session cleared - user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user session: {str(e)}")
            return False
    
    async def log_api_key_usage(
        self, 
        user_id: str, 
        service: SupportedService, 
        operation: str,
        endpoint: str = None,
        success: bool = True,
        response_code: int = None,
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None,
        response_time_ms: int = None
    ) -> bool:
        """Log API key usage"""
        if not self.is_available():
            return False
        
        try:
            # Get API key ID
            key_result = self.client.table('encrypted_api_keys').select('id').eq(
                'user_id', user_id
            ).eq('service', service.value).eq('status', 'active').execute()
            
            if not key_result.data:
                return False
            
            api_key_id = key_result.data[0]['id']
            
            log_data = {
                'api_key_id': api_key_id,
                'user_id': user_id,
                'service': service.value,
                'operation': operation,
                'endpoint': endpoint,
                'success': success,
                'response_code': response_code,
                'error_message': error_message,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'request_id': request_id,
                'response_time_ms': response_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('api_key_usage_logs').insert(log_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error logging API key usage: {str(e)}")
            return False
    
    async def get_service_integrations(self) -> List[Dict[str, Any]]:
        """Get all service integration configurations"""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('service_integrations').select('*').execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting service integrations: {str(e)}")
            return []
    
    async def _update_key_status(self, key_id: str, status: str) -> bool:
        """Update API key status"""
        try:
            result = self.client.table('encrypted_api_keys').update({
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', key_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating key status: {str(e)}")
            return False
    
    async def _update_key_usage(self, key_id: str) -> bool:
        """Update API key usage count and last used timestamp"""
        try:
            # First get current usage count
            result = self.client.table('encrypted_api_keys').select('usage_count').eq('id', key_id).execute()
            
            if not result.data:
                return False
            
            current_count = result.data[0]['usage_count'] or 0
            
            # Update usage
            update_result = self.client.table('encrypted_api_keys').update({
                'usage_count': current_count + 1,
                'last_used_at': datetime.utcnow().isoformat(),
                'last_validation_at': datetime.utcnow().isoformat(),
                'validation_status': 'valid'
            }).eq('id', key_id).execute()
            
            return bool(update_result.data)
            
        except Exception as e:
            logger.error(f"Error updating key usage: {str(e)}")
            return False
    
    async def cleanup_expired_keys(self) -> int:
        """Clean up expired API keys"""
        if not self.is_available():
            return 0
        
        try:
            current_time = datetime.utcnow().isoformat()
            
            result = self.client.table('encrypted_api_keys').update({
                'status': 'expired',
                'updated_at': current_time
            }).lt('expires_at', current_time).eq('status', 'active').execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {count} expired API keys")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {str(e)}")
            return 0

# Global instance
supabase_service = SupabaseService() 