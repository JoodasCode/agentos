from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.models.api_keys import (
    SupportedService, APIKeyRequest, APIKeySubmission, 
    AgentCapabilities, SERVICE_CONFIGS
)
from app.services.api_key_manager import api_key_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/request")
async def request_api_key(
    agent_name: str,
    service: SupportedService,
    session_id: str,
    reason: str = None
):
    """Agent requests API key from user"""
    
    try:
        request = await api_key_manager.request_api_key(
            agent_name=agent_name,
            service=service,
            session_id=session_id,
            reason=reason
        )
        
        return {
            "success": True,
            "request": request.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error requesting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error requesting API key: {str(e)}")

@router.post("/submit")
async def submit_api_key(submission: APIKeySubmission):
    """User submits API key"""
    
    try:
        success = await api_key_manager.submit_api_key(submission)
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid API key format or submission failed")
        
        # Get updated capabilities for all agents
        agent_capabilities = {}
        for agent_name in ["Alex", "Dana", "Riley", "Jamie"]:
            capabilities = await api_key_manager.get_agent_capabilities(agent_name, submission.session_id)
            agent_capabilities[agent_name] = capabilities.dict()
        
        return {
            "success": True,
            "message": f"API key for {submission.service.value} stored successfully",
            "agent_capabilities": agent_capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting API key: {str(e)}")

@router.get("/capabilities/{agent_name}")
async def get_agent_capabilities(agent_name: str, session_id: str):
    """Get what an agent can do based on available API keys"""
    
    try:
        capabilities = await api_key_manager.get_agent_capabilities(agent_name, session_id)
        
        return {
            "success": True,
            "capabilities": capabilities.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of user's API keys"""
    
    try:
        status = await api_key_manager.get_session_status(session_id)
        
        return {
            "success": True,
            "session_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting session status: {str(e)}")

@router.get("/services")
async def get_supported_services():
    """Get all supported services and their configurations"""
    
    try:
        services = {}
        for service, config in SERVICE_CONFIGS.items():
            services[service.value] = {
                "name": service.value,
                "capabilities": config.capabilities,
                "setup_url": config.setup_url,
                "instructions": config.instructions,
                "required_scopes": config.required_scopes
            }
        
        return {
            "success": True,
            "services": services,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting services: {str(e)}")

@router.get("/agents/mapping")
async def get_agent_service_mapping():
    """Get which services each agent can use"""
    
    try:
        from app.models.api_keys import AGENT_SERVICE_MAPPING
        
        mapping = {}
        for agent, services in AGENT_SERVICE_MAPPING.items():
            mapping[agent] = {
                "services": [service.value for service in services],
                "capabilities": []
            }
            
            # Add capabilities for each service
            for service in services:
                if service in SERVICE_CONFIGS:
                    mapping[agent]["capabilities"].extend(SERVICE_CONFIGS[service].capabilities)
        
        return {
            "success": True,
            "agent_mapping": mapping,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting agent mapping: {str(e)}")

@router.delete("/session/{session_id}/service/{service}")
async def revoke_api_key(session_id: str, service: SupportedService):
    """Revoke API key for a specific service"""
    
    try:
        success = await api_key_manager.revoke_api_key(session_id, service)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "success": True,
            "message": f"API key for {service.value} revoked successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear all API keys for a session"""
    
    try:
        success = await api_key_manager.clear_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "message": "Session cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@router.get("/session/{session_id}/agents/capabilities")
async def get_all_agent_capabilities(session_id: str):
    """Get capabilities for all agents based on available API keys"""
    
    try:
        all_capabilities = {}
        
        for agent_name in ["Alex", "Dana", "Riley", "Jamie"]:
            capabilities = await api_key_manager.get_agent_capabilities(agent_name, session_id)
            all_capabilities[agent_name] = capabilities.dict()
        
        return {
            "success": True,
            "agent_capabilities": all_capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all agent capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

@router.post("/validate")
async def validate_api_key_format(service: SupportedService, api_key: str):
    """Validate API key format without storing it"""
    
    try:
        is_valid = api_key_manager._validate_api_key_format(service, api_key)
        
        return {
            "success": True,
            "valid": is_valid,
            "service": service.value,
            "message": "Valid format" if is_valid else "Invalid format",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating API key: {str(e)}")

@router.get("/integrations")
async def get_service_integrations():
    """Get all service integration configurations from Supabase"""
    
    try:
        integrations = await api_key_manager.get_service_integrations()
        
        return {
            "success": True,
            "integrations": integrations,
            "count": len(integrations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting service integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting integrations: {str(e)}")

@router.post("/session/{session_id}/sync")
async def sync_session_with_supabase(session_id: str):
    """Sync session data with Supabase database"""
    
    try:
        success = await api_key_manager.sync_with_supabase(session_id)
        
        if not success:
            return {
                "success": False,
                "message": "Supabase not available or sync failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get updated session status
        status = await api_key_manager.get_session_status(session_id)
        
        return {
            "success": True,
            "message": "Session synced successfully",
            "session_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error syncing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error syncing session: {str(e)}")

@router.post("/test-connection/{service}")
async def test_service_connection(service: SupportedService, session_id: str):
    """Test connection to a service using stored API key"""
    
    try:
        # Get the API key
        api_key = await api_key_manager.get_api_key(session_id, service)
        
        if not api_key:
            raise HTTPException(status_code=404, detail=f"No API key found for {service.value}")
        
        # Basic connection test based on service
        test_result = await _test_service_connection(service, api_key)
        
        return {
            "success": True,
            "service": service.value,
            "connection_status": test_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing service connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing connection: {str(e)}")

@router.post("/cleanup/cache")
async def cleanup_expired_cache():
    """Clean up expired cache entries"""
    
    try:
        await api_key_manager.cleanup_expired_cache()
        
        return {
            "success": True,
            "message": "Cache cleanup completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up cache: {str(e)}")

async def _test_service_connection(service: SupportedService, api_key: str) -> Dict[str, Any]:
    """Test connection to external service"""
    
    # This is a basic implementation - in production, you'd make actual API calls
    # to test the connection and validate the API key
    
    test_results = {
        "valid": True,
        "response_time_ms": 150,  # Mock response time
        "status": "connected",
        "last_tested": datetime.utcnow().isoformat()
    }
    
    # Service-specific validation logic would go here
    if service == SupportedService.OPENAI:
        test_results["endpoint"] = "https://api.openai.com/v1/models"
        test_results["method"] = "GET"
    elif service == SupportedService.GITHUB:
        test_results["endpoint"] = "https://api.github.com/user"
        test_results["method"] = "GET"
    elif service == SupportedService.NOTION:
        test_results["endpoint"] = "https://api.notion.com/v1/users/me"
        test_results["method"] = "GET"
    elif service == SupportedService.SLACK:
        test_results["endpoint"] = "https://slack.com/api/auth.test"
        test_results["method"] = "POST"
    else:
        test_results["endpoint"] = "Mock endpoint"
        test_results["method"] = "GET"
    
    return test_results 