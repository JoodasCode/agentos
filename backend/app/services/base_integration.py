from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import httpx
import asyncio
from enum import Enum

from app.core.logging import get_logger
from app.services.api_key_manager import api_key_manager
from app.models.api_keys import SupportedService

logger = get_logger(__name__)

class IntegrationStatus(str, Enum):
    """Integration status types"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"

class BaseIntegration(ABC):
    """Base class for all service integrations"""
    
    def __init__(self, service: SupportedService):
        self.service = service
        self.service_name = service.value
        self.status = IntegrationStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.rate_limit_reset: Optional[datetime] = None
        
        # HTTP client with common settings
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "AgentOS/1.0"}
        )
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the service API"""
        pass
    
    @property
    @abstractmethod
    def required_scopes(self) -> List[str]:
        """Required OAuth scopes for this integration"""
        pass
    
    async def get_api_key(self, session_id: str) -> Optional[str]:
        """Get API key for this service from the key manager"""
        try:
            api_key = await api_key_manager.get_api_key(session_id, self.service)
            if api_key:
                self.status = IntegrationStatus.CONNECTED
                return api_key
            else:
                self.status = IntegrationStatus.DISCONNECTED
                return None
        except Exception as e:
            logger.error(f"Error getting API key for {self.service_name}: {str(e)}")
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)
            return None
    
    async def test_connection(self, session_id: str) -> Dict[str, Any]:
        """Test connection to the service"""
        try:
            api_key = await self.get_api_key(session_id)
            if not api_key:
                return {
                    "connected": False,
                    "status": "no_api_key",
                    "message": f"No API key found for {self.service_name}"
                }
            
            # Call service-specific test method
            result = await self._test_api_connection(api_key)
            
            if result.get("connected"):
                self.status = IntegrationStatus.CONNECTED
            else:
                self.status = IntegrationStatus.ERROR
                self.last_error = result.get("message", "Connection test failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Connection test failed for {self.service_name}: {str(e)}")
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)
            return {
                "connected": False,
                "status": "error",
                "message": str(e)
            }
    
    @abstractmethod
    async def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Service-specific connection test implementation"""
        pass
    
    async def make_api_request(
        self, 
        method: str, 
        endpoint: str, 
        api_key: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request to the service"""
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare headers with authentication
        request_headers = await self._prepare_auth_headers(api_key)
        if headers:
            request_headers.update(headers)
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                self.status = IntegrationStatus.RATE_LIMITED
                retry_after = response.headers.get("Retry-After", "60")
                self.rate_limit_reset = datetime.utcnow().timestamp() + int(retry_after)
                
                return {
                    "success": False,
                    "error": "rate_limited",
                    "retry_after": int(retry_after),
                    "message": f"Rate limited. Retry after {retry_after} seconds."
                }
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self.status = IntegrationStatus.UNAUTHORIZED
                return {
                    "success": False,
                    "error": "unauthorized",
                    "message": "Invalid or expired API key"
                }
            
            # Parse response
            if response.status_code >= 400:
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                
                return {
                    "success": False,
                    "error": "api_error",
                    "status_code": response.status_code,
                    "message": error_msg
                }
            
            # Success
            self.status = IntegrationStatus.CONNECTED
            return {
                "success": True,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
            
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "timeout",
                "message": "Request timed out"
            }
        except Exception as e:
            logger.error(f"API request error for {self.service_name}: {str(e)}")
            return {
                "success": False,
                "error": "request_error",
                "message": str(e)
            }
    
    @abstractmethod
    async def _prepare_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Prepare authentication headers for API requests"""
        pass
    
    # Trigger.dev Integration Methods
    
    async def create_trigger_workflow(
        self, 
        workflow_name: str, 
        workflow_config: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Create a Trigger.dev workflow for this integration"""
        
        try:
            # Validate API key exists
            api_key = await self.get_api_key(session_id)
            if not api_key:
                return {
                    "success": False,
                    "error": "no_api_key",
                    "message": f"No API key configured for {self.service_name}"
                }
            
            # Prepare workflow payload
            workflow_payload = {
                "name": workflow_name,
                "service": self.service_name,
                "config": workflow_config,
                "integration_status": self.status.value,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Call service-specific workflow creation
            result = await self._create_service_workflow(workflow_payload, api_key)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating workflow for {self.service_name}: {str(e)}")
            return {
                "success": False,
                "error": "workflow_error",
                "message": str(e)
            }
    
    @abstractmethod
    async def _create_service_workflow(
        self, 
        workflow_payload: Dict[str, Any], 
        api_key: str
    ) -> Dict[str, Any]:
        """Service-specific workflow creation implementation"""
        pass
    
    # Common utility methods
    
    def get_integration_info(self) -> Dict[str, Any]:
        """Get current integration status and info"""
        return {
            "service": self.service_name,
            "status": self.status.value,
            "connected": self.status == IntegrationStatus.CONNECTED,
            "last_error": self.last_error,
            "rate_limit_reset": self.rate_limit_reset,
            "required_scopes": self.required_scopes
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        try:
            if hasattr(self, 'client') and self.client:
                asyncio.create_task(self.client.aclose())
        except:
            pass 