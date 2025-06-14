from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.services.integration_manager import integration_manager
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Request Models
class CreateNotionPageRequest(BaseModel):
    title: str
    content: str
    database_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

class SendSlackMessageRequest(BaseModel):
    channel: str
    message: str
    blocks: Optional[List[Dict]] = None

class CreateCalendarEventRequest(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class CreateGitHubIssueRequest(BaseModel):
    repo_owner: str
    repo_name: str
    title: str
    body: Optional[str] = None
    labels: Optional[List[str]] = None

class CreateWorkflowRequest(BaseModel):
    service: str
    workflow_name: str
    workflow_config: Dict[str, Any]

class ExecuteActionRequest(BaseModel):
    service: str
    action: str
    parameters: Dict[str, Any]

# Integration Status and Management
@router.get("/status")
async def get_integration_status(session_id: str):
    """Get status of all integrations for a session"""
    try:
        status = await integration_manager.get_integration_status(session_id)
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available")
async def get_available_integrations():
    """Get all available integrations and their info"""
    try:
        integrations = await integration_manager.get_available_integrations()
        return {
            "success": True,
            "integrations": integrations,
            "count": len(integrations)
        }
    except Exception as e:
        logger.error(f"Error getting available integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connections")
async def test_all_connections(session_id: str):
    """Test connections for all configured integrations"""
    try:
        results = await integration_manager.test_all_connections(session_id)
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/actions")
async def get_available_actions(session_id: str):
    """Get available actions for each connected service"""
    try:
        actions = await integration_manager.get_available_actions(session_id)
        return {
            "success": True,
            "actions": actions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting available actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Notion Integration Endpoints
@router.post("/notion/create-page")
async def create_notion_page(request: CreateNotionPageRequest, session_id: str):
    """Create a new Notion page"""
    try:
        result = await integration_manager.create_notion_page(
            session_id=session_id,
            title=request.title,
            content=request.content,
            database_id=request.database_id,
            properties=request.properties
        )
        
        if result.get("success"):
            return {
                "success": True,
                "page": result.get("page"),
                "message": f"Created Notion page: {request.title}"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create page"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Notion page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notion/databases")
async def get_notion_databases(session_id: str):
    """Get user's Notion databases"""
    try:
        result = await integration_manager.get_notion_databases(session_id)
        
        if result.get("success"):
            return {
                "success": True,
                "databases": result.get("databases", []),
                "count": result.get("count", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get databases"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Notion databases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Slack Integration Endpoints
@router.post("/slack/send-message")
async def send_slack_message(request: SendSlackMessageRequest, session_id: str):
    """Send a message to Slack"""
    try:
        result = await integration_manager.send_slack_message(
            session_id=session_id,
            channel=request.channel,
            message=request.message,
            blocks=request.blocks
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message"),
                "sent_to": request.channel
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to send message"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/channels")
async def get_slack_channels(session_id: str):
    """Get user's Slack channels"""
    try:
        result = await integration_manager.get_slack_channels(session_id)
        
        if result.get("success"):
            return {
                "success": True,
                "channels": result.get("channels", []),
                "count": result.get("count", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get channels"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Slack channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Google Calendar Integration Endpoints
@router.post("/calendar/create-event")
async def create_calendar_event(request: CreateCalendarEventRequest, session_id: str):
    """Create a Google Calendar event"""
    try:
        result = await integration_manager.create_calendar_event(
            session_id=session_id,
            title=request.title,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
            location=request.location,
            attendees=request.attendees
        )
        
        if result.get("success"):
            return {
                "success": True,
                "event": result.get("event"),
                "message": f"Created calendar event: {request.title}"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create event"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GitHub Integration Endpoints
@router.post("/github/create-issue")
async def create_github_issue(request: CreateGitHubIssueRequest, session_id: str):
    """Create a GitHub issue"""
    try:
        result = await integration_manager.create_github_issue(
            session_id=session_id,
            repo_owner=request.repo_owner,
            repo_name=request.repo_name,
            title=request.title,
            body=request.body,
            labels=request.labels
        )
        
        if result.get("success"):
            return {
                "success": True,
                "issue": result.get("issue"),
                "message": f"Created GitHub issue: {request.title}"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create issue"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating GitHub issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/github/repositories")
async def get_github_repositories(session_id: str):
    """Get user's GitHub repositories"""
    try:
        result = await integration_manager.get_github_repositories(session_id)
        
        if result.get("success"):
            return {
                "success": True,
                "repositories": result.get("repositories", []),
                "count": result.get("count", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get repositories"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow Management Endpoints
@router.post("/workflows/create")
async def create_automation_workflow(request: CreateWorkflowRequest, session_id: str):
    """Create a Trigger.dev automation workflow"""
    try:
        result = await integration_manager.create_automation_workflow(
            session_id=session_id,
            service=request.service,
            workflow_name=request.workflow_name,
            workflow_config=request.workflow_config
        )
        
        if result.get("success"):
            return {
                "success": True,
                "workflow": result.get("workflow"),
                "message": result.get("message", "Workflow created successfully")
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create workflow"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Generic Action Execution Endpoint
@router.post("/execute")
async def execute_integration_action(request: ExecuteActionRequest, session_id: str):
    """Execute a generic integration action"""
    try:
        result = await integration_manager.execute_integration_action(
            session_id=session_id,
            service=request.service,
            action=request.action,
            parameters=request.parameters
        )
        
        if result.get("success"):
            return {
                "success": True,
                "result": result,
                "action": f"{request.service}.{request.action}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Action execution failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 