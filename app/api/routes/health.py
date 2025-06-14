from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Agent OS V2"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Agent OS V2",
        "version": "2.0.0",
        "components": {
            "api": "healthy",
            "agents": "healthy",
            "conversation_manager": "healthy"
        }
    }

@router.get("/agents")
async def agents_health_check():
    """Check the status of conversational agents"""
    
    try:
        # We'll implement actual agent health checks later
        # For now, return basic status
        agents_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "alex": {"status": "ready", "role": "Strategy Planning"},
                "dana": {"status": "ready", "role": "Creative Content"},
                "riley": {"status": "ready", "role": "Data Analysis"},
                "jamie": {"status": "ready", "role": "Operations Management"}
            },
            "conversation_manager": {"status": "ready"},
            "trigger_integration": {"status": "ready"}
        }
        
        return agents_status
        
    except Exception as e:
        logger.error("Agent health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent health check failed: {str(e)}") 