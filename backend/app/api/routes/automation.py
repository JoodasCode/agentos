"""
Automation API Routes - Real Trigger.dev Integration
Provides endpoints to trigger automation workflows
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.trigger_service import trigger_service
from app.services.api_key_manager import api_key_manager
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Request Models
class ProductHuntLaunchRequest(BaseModel):
    product_name: str = Field(..., description="Name of the product to launch")
    launch_date: str = Field(..., description="Launch date in ISO format")
    description: str = Field(..., description="Product description")
    website: str = Field(..., description="Product website URL")
    twitter_handle: Optional[str] = Field(None, description="Twitter handle for promotion")
    slack_webhook: Optional[str] = Field(None, description="Slack webhook for notifications")

class ContentGenerationRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Content topic")
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(default="professional", description="Content tone")
    platforms: Optional[List[str]] = Field(None, description="Target platforms")
    scheduled_date: Optional[str] = Field(None, description="Scheduled publication date")
    notion_database_id: Optional[str] = Field(None, description="Notion database ID")
    slack_channel: Optional[str] = Field(None, description="Slack channel for notifications")

class AnalyticsTrackingRequest(BaseModel):
    event_type: str = Field(..., description="Type of event to track")
    user_id: str = Field(..., description="User ID")
    properties: Dict[str, Any] = Field(..., description="Event properties")
    scheduled_date: Optional[str] = Field(None, description="Scheduled tracking date")

# Response Models
class AutomationResponse(BaseModel):
    success: bool
    task_id: str
    run_id: Optional[str] = None
    status: Optional[str] = None
    triggered_at: str
    error: Optional[str] = None

@router.post("/product-hunt-launch", response_model=AutomationResponse)
async def trigger_product_hunt_launch(
    request: ProductHuntLaunchRequest,
    user_id: str = "default_user"  # In production, get from auth
):
    """Trigger Product Hunt launch automation"""
    try:
        logger.info(f"Triggering Product Hunt launch automation - product: {request.product_name}, user_id: {user_id}")
        
        result = await trigger_service.trigger_product_hunt_launch(
            product_name=request.product_name,
            launch_date=request.launch_date,
            description=request.description,
            website=request.website,
            twitter_handle=request.twitter_handle,
            slack_webhook=request.slack_webhook
        )
        
        return AutomationResponse(**result)
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger Product Hunt launch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")

@router.post("/content-generation", response_model=AutomationResponse)
async def trigger_content_generation(
    request: ContentGenerationRequest,
    user_id: str = "default_user"  # In production, get from auth
):
    """Trigger content generation automation"""
    try:
        logger.info(f"Triggering content generation automation - content_type: {request.content_type}, user_id: {user_id}")
        
        # Get API keys for integrations if needed
        notion_config = None
        slack_config = None
        
        if request.notion_database_id:
            notion_key = await api_key_manager.get_api_key(user_id, "notion")
            if notion_key:
                notion_config = {
                    "databaseId": request.notion_database_id,
                    "apiKey": notion_key
                }
        
        if request.slack_channel:
            slack_key = await api_key_manager.get_api_key(user_id, "slack")
            if slack_key:
                slack_config = {
                    "channel": request.slack_channel,
                    "webhook": slack_key  # Assuming webhook URL stored as API key
                }
        
        result = await trigger_service.trigger_content_generation(
            content_type=request.content_type,
            topic=request.topic,
            target_audience=request.target_audience,
            tone=request.tone,
            platforms=request.platforms,
            scheduled_date=request.scheduled_date,
            notion_config=notion_config,
            slack_config=slack_config
        )
        
        return AutomationResponse(**result)
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger content generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")

@router.post("/analytics-tracking", response_model=AutomationResponse)
async def trigger_analytics_tracking(
    request: AnalyticsTrackingRequest,
    user_id: str = "default_user"  # In production, get from auth
):
    """Trigger analytics tracking automation"""
    try:
        logger.info(f"Triggering analytics tracking automation - event_type: {request.event_type}, user_id: {user_id}")
        
        result = await trigger_service.trigger_analytics_tracking(
            event_type=request.event_type,
            user_id=user_id,
            properties=request.properties,
            scheduled_date=request.scheduled_date
        )
        
        return AutomationResponse(**result)
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger analytics tracking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")

@router.get("/runs/{run_id}")
async def get_run_status(run_id: str):
    """Get the status of a Trigger.dev run"""
    try:
        result = await trigger_service.get_run_status(run_id)
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get run status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/runs")
async def list_runs(
    task_id: Optional[str] = None,
    limit: int = 50
):
    """List recent Trigger.dev runs"""
    try:
        result = await trigger_service.list_runs(task_id=task_id, limit=limit)
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list runs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")

@router.get("/health")
async def automation_health():
    """Check automation service health"""
    return {
        "trigger_dev_available": trigger_service.is_available(),
        "project_ref": trigger_service.project_ref,
        "timestamp": datetime.utcnow().isoformat()
    } 