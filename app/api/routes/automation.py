from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.services.action_bridge import ActionBridge
from app.services.trigger_service import TriggerService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize services
action_bridge = ActionBridge()
trigger_service = TriggerService()

@router.post("/convert-conversation")
async def convert_conversation_to_actions(conversation_data: Dict[str, Any]):
    """Convert conversation context into actionable job parameters"""
    
    return {
        "success": True,
        "action_plan": {
            "execution_plan": {
                "jobs": [
                    {
                        "type": "product_hunt_launch",
                        "priority": "high",
                        "estimated_time": "3-5 days"
                    }
                ]
            },
            "ready_to_execute": False,
            "validation_results": {
                "product_hunt_launch": {
                    "valid": False,
                    "missing_params": ["launch_date", "product_name"],
                    "suggestions": ["Please provide launch date", "Please provide product name"]
                }
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/execute-plan")
async def execute_action_plan(action_plan: Dict[str, Any]):
    """Execute the complete action plan"""
    
    try:
        logger.info("Executing action plan", 
                   job_count=len(action_plan.get("job_parameters", {})))
        
        execution_results = await action_bridge.execute_action_plan(action_plan)
        
        logger.info("Action plan executed", 
                   success=execution_results["success"],
                   successful_jobs=execution_results.get("successful_jobs", 0))
        
        return {
            "success": True,
            "execution_results": execution_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error executing action plan", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error executing action plan: {str(e)}")

@router.get("/capabilities")
async def get_automation_capabilities():
    """Get all available automation capabilities"""
    
    return {
        "success": True,
        "capabilities": {
            "product_hunt_launch": {
                "name": "Product Hunt Launch Automation",
                "description": "Complete Product Hunt launch workflow",
                "timeline_options": ["same-day", "1-week", "2-weeks", "1-month", "custom"]
            },
            "content_generation": {
                "name": "Marketing Content Generation", 
                "description": "Generate marketing content across platforms",
                "tone_options": ["professional", "casual", "technical", "playful", "authoritative"]
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/capabilities/{capability_name}/options/{option_type}")
async def get_capability_options(capability_name: str, option_type: str):
    """Get specific options for a capability"""
    
    try:
        options = await trigger_service.get_capability_options(capability_name, option_type)
        
        return {
            "success": True,
            "capability": capability_name,
            "option_type": option_type,
            "options": options,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting capability options", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting options: {str(e)}")

@router.post("/validate-job")
async def validate_job_parameters(job_data: Dict[str, Any]):
    """Validate job parameters before execution"""
    
    try:
        job_type = job_data.get("job_type")
        parameters = job_data.get("parameters", {})
        
        if not job_type:
            raise HTTPException(status_code=400, detail="job_type is required")
        
        validation_result = await trigger_service.validate_job_parameters(job_type, parameters)
        
        return {
            "success": True,
            "job_type": job_type,
            "validation_result": validation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error validating job parameters", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error validating job: {str(e)}")

@router.post("/execute-job")
async def execute_single_job(job_data: Dict[str, Any]):
    """Execute a single job"""
    
    try:
        job_type = job_data.get("job_type")
        parameters = job_data.get("parameters", {})
        
        if not job_type:
            raise HTTPException(status_code=400, detail="job_type is required")
        
        # Validate parameters first
        validation = await trigger_service.validate_job_parameters(job_type, parameters)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Invalid job parameters",
                "validation_result": validation
            }
        
        # Execute job
        execution_result = await trigger_service.execute_job(job_type, parameters)
        
        logger.info("Job executed", 
                   job_type=job_type,
                   job_id=execution_result["job_id"])
        
        return {
            "success": True,
            "execution_result": execution_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error executing job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error executing job: {str(e)}")

@router.get("/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a running job"""
    
    try:
        status = await trigger_service.get_job_status(job_id)
        
        return {
            "success": True,
            "job_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting job status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

@router.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    
    try:
        result = await trigger_service.cancel_job(job_id)
        
        logger.info("Job cancelled", job_id=job_id)
        
        return {
            "success": True,
            "cancellation_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error cancelling job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")

@router.get("/jobs/history")
async def get_job_history(limit: int = 10):
    """Get recent job execution history"""
    
    try:
        history = await trigger_service.get_job_history(limit)
        
        return {
            "success": True,
            "job_history": history,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting job history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting job history: {str(e)}")

@router.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get status of all jobs in an execution"""
    
    try:
        # This would typically fetch from database in production
        # For now, return mock status
        return {
            "success": True,
            "execution_id": execution_id,
            "status": "running",
            "jobs": [
                {
                    "job_type": "product_hunt_launch",
                    "status": "running",
                    "progress": 45
                },
                {
                    "job_type": "content_generation",
                    "status": "completed",
                    "progress": 100
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting execution status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting execution status: {str(e)}") 