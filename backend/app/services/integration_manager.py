from typing import Dict, List, Any, Optional, Type
from datetime import datetime
import asyncio

from app.services.base_integration import BaseIntegration, IntegrationStatus
from app.services.integrations.notion_integration import notion_integration
from app.services.integrations.slack_integration import slack_integration
from app.services.integrations.google_calendar_integration import google_calendar_integration
from app.services.integrations.github_integration import github_integration
from app.models.api_keys import SupportedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class IntegrationManager:
    """Manages all service integrations and provides unified interface for AI agents"""
    
    def __init__(self):
        # Register all available integrations
        self.integrations: Dict[str, BaseIntegration] = {
            SupportedService.NOTION.value: notion_integration,
            SupportedService.SLACK.value: slack_integration,
            SupportedService.GOOGLE_CALENDAR.value: google_calendar_integration,
            SupportedService.GITHUB.value: github_integration
        }
        
        logger.info(f"Integration Manager initialized with {len(self.integrations)} integrations")
    
    async def get_available_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Get all available integrations and their info"""
        integrations_info = {}
        
        for service_name, integration in self.integrations.items():
            integrations_info[service_name] = integration.get_integration_info()
        
        return integrations_info
    
    async def test_all_connections(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Test connections for all configured integrations"""
        results = {}
        
        # Test all integrations in parallel
        tasks = []
        for service_name, integration in self.integrations.items():
            task = asyncio.create_task(
                integration.test_connection(session_id),
                name=f"test_{service_name}"
            )
            tasks.append((service_name, task))
        
        # Wait for all tests to complete
        for service_name, task in tasks:
            try:
                result = await task
                results[service_name] = result
            except Exception as e:
                logger.error(f"Error testing {service_name} connection: {str(e)}")
                results[service_name] = {
                    "connected": False,
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    async def get_integration_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive status of all integrations"""
        connection_results = await self.test_all_connections(session_id)
        
        status_summary = {
            "total_integrations": len(self.integrations),
            "connected_count": 0,
            "disconnected_count": 0,
            "error_count": 0,
            "integrations": connection_results,
            "last_checked": datetime.utcnow().isoformat()
        }
        
        # Count statuses
        for result in connection_results.values():
            if result.get("connected"):
                status_summary["connected_count"] += 1
            elif result.get("status") == "error":
                status_summary["error_count"] += 1
            else:
                status_summary["disconnected_count"] += 1
        
        return status_summary
    
    # Service-specific methods for AI agents
    
    # Notion Operations
    async def create_notion_page(
        self, 
        session_id: str, 
        title: str, 
        content: str,
        database_id: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a Notion page - used by AI agents"""
        if SupportedService.NOTION.value not in self.integrations:
            return {"success": False, "error": "notion_not_available"}
        
        try:
            result = await notion_integration.create_page(
                session_id=session_id,
                title=title,
                content=content,
                database_id=database_id,
                properties=properties
            )
            
            if result.get("success"):
                logger.info(f"Created Notion page: {title}", session_id=session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_notion_databases(self, session_id: str) -> Dict[str, Any]:
        """Get user's Notion databases"""
        if SupportedService.NOTION.value not in self.integrations:
            return {"success": False, "error": "notion_not_available"}
        
        return await notion_integration.get_databases(session_id)
    
    # Slack Operations
    async def send_slack_message(
        self, 
        session_id: str, 
        channel: str, 
        message: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a Slack message - used by AI agents"""
        if SupportedService.SLACK.value not in self.integrations:
            return {"success": False, "error": "slack_not_available"}
        
        try:
            result = await slack_integration.send_message(
                session_id=session_id,
                channel=channel,
                text=message,
                blocks=blocks
            )
            
            if result.get("success"):
                logger.info(f"Sent Slack message to {channel}", session_id=session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_slack_channels(self, session_id: str) -> Dict[str, Any]:
        """Get user's Slack channels"""
        if SupportedService.SLACK.value not in self.integrations:
            return {"success": False, "error": "slack_not_available"}
        
        return await slack_integration.get_channels(session_id)
    
    # Google Calendar Operations
    async def create_calendar_event(
        self, 
        session_id: str, 
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Google Calendar event - used by AI agents"""
        if SupportedService.GOOGLE_CALENDAR.value not in self.integrations:
            return {"success": False, "error": "google_calendar_not_available"}
        
        try:
            result = await google_calendar_integration.create_event(
                session_id=session_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees
            )
            
            if result.get("success"):
                logger.info(f"Created calendar event: {title}", session_id=session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # GitHub Operations
    async def create_github_issue(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a GitHub issue - used by AI agents"""
        if SupportedService.GITHUB.value not in self.integrations:
            return {"success": False, "error": "github_not_available"}
        
        try:
            result = await github_integration.create_issue(
                session_id=session_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                title=title,
                body=body,
                labels=labels
            )
            
            if result.get("success"):
                logger.info(f"Created GitHub issue: {title}", session_id=session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_github_repositories(self, session_id: str) -> Dict[str, Any]:
        """Get user's GitHub repositories"""
        if SupportedService.GITHUB.value not in self.integrations:
            return {"success": False, "error": "github_not_available"}
        
        return await github_integration.get_repositories(session_id)
    
    # Workflow Management
    async def create_automation_workflow(
        self, 
        session_id: str, 
        service: str, 
        workflow_name: str,
        workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a Trigger.dev automation workflow for a service"""
        if service not in self.integrations:
            return {
                "success": False,
                "error": "service_not_available",
                "available_services": list(self.integrations.keys())
            }
        
        try:
            integration = self.integrations[service]
            result = await integration.create_trigger_workflow(
                workflow_name=workflow_name,
                workflow_config=workflow_config,
                session_id=session_id
            )
            
            if result.get("success"):
                logger.info(f"Created {service} workflow: {workflow_name}", session_id=session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating {service} workflow: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # AI Agent Helper Methods
    
    async def get_available_actions(self, session_id: str) -> Dict[str, List[str]]:
        """Get available actions for each connected service - for AI agents"""
        connection_status = await self.test_all_connections(session_id)
        available_actions = {}
        
        for service_name, status in connection_status.items():
            if status.get("connected"):
                if service_name == SupportedService.NOTION.value:
                    available_actions[service_name] = [
                        "create_page", "get_databases", "add_database_entry", "update_page"
                    ]
                elif service_name == SupportedService.SLACK.value:
                    available_actions[service_name] = [
                        "send_message", "create_channel", "get_channels", "schedule_message"
                    ]
                elif service_name == SupportedService.GOOGLE_CALENDAR.value:
                    available_actions[service_name] = [
                        "create_event", "get_events", "update_event", "find_free_time"
                    ]
                elif service_name == SupportedService.GITHUB.value:
                    available_actions[service_name] = [
                        "create_issue", "get_repositories", "create_pull_request", "get_issues"
                    ]
        
        return available_actions
    
    async def execute_integration_action(
        self, 
        session_id: str, 
        service: str, 
        action: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an integration action - unified interface for AI agents"""
        if service not in self.integrations:
            return {"success": False, "error": f"Service {service} not available"}
        
        integration = self.integrations[service]
        
        try:
            # Route to appropriate method based on service and action
            if service == SupportedService.NOTION.value:
                if action == "create_page":
                    return await integration.create_page(session_id, **parameters)
                elif action == "get_databases":
                    return await integration.get_databases(session_id)
                elif action == "add_database_entry":
                    return await integration.add_database_entry(session_id, **parameters)
                
            elif service == SupportedService.SLACK.value:
                if action == "send_message":
                    return await integration.send_message(session_id, **parameters)
                elif action == "get_channels":
                    return await integration.get_channels(session_id)
                elif action == "create_channel":
                    return await integration.create_channel(session_id, **parameters)
                
            elif service == SupportedService.GOOGLE_CALENDAR.value:
                if action == "create_event":
                    return await integration.create_event(session_id, **parameters)
                elif action == "get_events":
                    return await integration.get_events(session_id, **parameters)
                
            elif service == SupportedService.GITHUB.value:
                if action == "create_issue":
                    return await integration.create_issue(session_id, **parameters)
                elif action == "get_repositories":
                    return await integration.get_repositories(session_id)
                elif action == "get_issues":
                    return await integration.get_issues(session_id, **parameters)
            
            return {"success": False, "error": f"Action {action} not supported for {service}"}
            
        except Exception as e:
            logger.error(f"Error executing {service}.{action}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Cleanup
    async def cleanup_all_integrations(self):
        """Cleanup all integration resources"""
        cleanup_tasks = []
        
        for integration in self.integrations.values():
            cleanup_tasks.append(integration.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info("All integrations cleaned up")

# Global instance
integration_manager = IntegrationManager() 