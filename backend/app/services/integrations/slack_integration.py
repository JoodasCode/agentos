from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.services.base_integration import BaseIntegration, IntegrationStatus
from app.models.api_keys import SupportedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class SlackIntegration(BaseIntegration):
    """Slack API integration for messaging, channel management, and team communication automation"""
    
    def __init__(self):
        super().__init__(SupportedService.SLACK)
    
    @property
    def base_url(self) -> str:
        return "https://slack.com/api"
    
    @property
    def required_scopes(self) -> List[str]:
        return [
            "channels:read",
            "channels:write", 
            "chat:write",
            "users:read",
            "users:read.email",
            "files:write"
        ]
    
    async def _prepare_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Prepare Slack API headers"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test Slack API connection by getting auth info"""
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="auth.test",
                api_key=api_key
            )
            
            if result.get("success"):
                auth_data = result.get("data", {})
                if auth_data.get("ok"):
                    return {
                        "connected": True,
                        "status": "success",
                        "message": "Successfully connected to Slack",
                        "workspace_info": {
                            "team": auth_data.get("team", "Unknown"),
                            "user": auth_data.get("user", "Unknown"),
                            "user_id": auth_data.get("user_id", "Unknown"),
                            "team_id": auth_data.get("team_id", "Unknown")
                        }
                    }
                else:
                    return {
                        "connected": False,
                        "status": "error",
                        "message": auth_data.get("error", "Authentication failed")
                    }
            else:
                return {
                    "connected": False,
                    "status": "error",
                    "message": result.get("message", "Failed to connect to Slack")
                }
                
        except Exception as e:
            logger.error(f"Slack connection test failed: {str(e)}")
            return {
                "connected": False,
                "status": "error", 
                "message": str(e)
            }
    
    # Core Slack Operations
    
    async def get_channels(self, session_id: str, types: str = "public_channel,private_channel") -> Dict[str, Any]:
        """Get all channels in the workspace"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="conversations.list",
                api_key=api_key,
                params={"types": types, "limit": 100}
            )
            
            if result.get("success"):
                data = result.get("data", {})
                if data.get("ok"):
                    channels = []
                    for channel in data.get("channels", []):
                        channels.append({
                            "id": channel.get("id"),
                            "name": channel.get("name"),
                            "is_private": channel.get("is_private", False),
                            "is_member": channel.get("is_member", False),
                            "topic": channel.get("topic", {}).get("value", ""),
                            "purpose": channel.get("purpose", {}).get("value", ""),
                            "member_count": channel.get("num_members", 0)
                        })
                    
                    return {
                        "success": True,
                        "channels": channels,
                        "count": len(channels)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Failed to get channels")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Slack channels: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_users(self, session_id: str) -> Dict[str, Any]:
        """Get all users in the workspace"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="users.list",
                api_key=api_key,
                params={"limit": 100}
            )
            
            if result.get("success"):
                data = result.get("data", {})
                if data.get("ok"):
                    users = []
                    for user in data.get("members", []):
                        if not user.get("deleted", False) and not user.get("is_bot", False):
                            users.append({
                                "id": user.get("id"),
                                "name": user.get("name"),
                                "real_name": user.get("real_name", ""),
                                "display_name": user.get("profile", {}).get("display_name", ""),
                                "email": user.get("profile", {}).get("email", ""),
                                "is_admin": user.get("is_admin", False),
                                "is_owner": user.get("is_owner", False)
                            })
                    
                    return {
                        "success": True,
                        "users": users,
                        "count": len(users)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Failed to get users")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Slack users: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_message(
        self, 
        session_id: str, 
        channel: str, 
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a message to a channel or user"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            data = {
                "channel": channel,
                "text": text
            }
            
            if thread_ts:
                data["thread_ts"] = thread_ts
            
            if blocks:
                data["blocks"] = blocks
            
            result = await self.make_api_request(
                method="POST",
                endpoint="chat.postMessage",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                response_data = result.get("data", {})
                if response_data.get("ok"):
                    return {
                        "success": True,
                        "message": {
                            "ts": response_data.get("ts"),
                            "channel": response_data.get("channel"),
                            "text": text
                        }
                    }
                else:
                    return {"success": False, "error": response_data.get("error", "Failed to send message")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_channel(
        self, 
        session_id: str, 
        name: str, 
        is_private: bool = False,
        topic: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new channel"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            data = {
                "name": name,
                "is_private": is_private
            }
            
            result = await self.make_api_request(
                method="POST",
                endpoint="conversations.create",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                response_data = result.get("data", {})
                if response_data.get("ok"):
                    channel_data = response_data.get("channel", {})
                    channel_id = channel_data.get("id")
                    
                    # Set topic and purpose if provided
                    if topic and channel_id:
                        await self.make_api_request(
                            method="POST",
                            endpoint="conversations.setTopic",
                            api_key=api_key,
                            data={"channel": channel_id, "topic": topic}
                        )
                    
                    if purpose and channel_id:
                        await self.make_api_request(
                            method="POST",
                            endpoint="conversations.setPurpose",
                            api_key=api_key,
                            data={"channel": channel_id, "purpose": purpose}
                        )
                    
                    return {
                        "success": True,
                        "channel": {
                            "id": channel_id,
                            "name": channel_data.get("name"),
                            "is_private": channel_data.get("is_private", False),
                            "created": channel_data.get("created")
                        }
                    }
                else:
                    return {"success": False, "error": response_data.get("error", "Failed to create channel")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating Slack channel: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def invite_to_channel(
        self, 
        session_id: str, 
        channel: str, 
        users: List[str]
    ) -> Dict[str, Any]:
        """Invite users to a channel"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            data = {
                "channel": channel,
                "users": ",".join(users)
            }
            
            result = await self.make_api_request(
                method="POST",
                endpoint="conversations.invite",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                response_data = result.get("data", {})
                if response_data.get("ok"):
                    return {
                        "success": True,
                        "message": f"Successfully invited {len(users)} users to channel"
                    }
                else:
                    return {"success": False, "error": response_data.get("error", "Failed to invite users")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error inviting users to Slack channel: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_message(
        self, 
        session_id: str, 
        channel: str, 
        text: str,
        post_at: int,  # Unix timestamp
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Schedule a message to be sent later"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            data = {
                "channel": channel,
                "text": text,
                "post_at": post_at
            }
            
            if blocks:
                data["blocks"] = blocks
            
            result = await self.make_api_request(
                method="POST",
                endpoint="chat.scheduleMessage",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                response_data = result.get("data", {})
                if response_data.get("ok"):
                    return {
                        "success": True,
                        "scheduled_message": {
                            "id": response_data.get("scheduled_message_id"),
                            "channel": channel,
                            "post_at": post_at
                        }
                    }
                else:
                    return {"success": False, "error": response_data.get("error", "Failed to schedule message")}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error scheduling Slack message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Trigger.dev Workflow Integration
    
    async def _create_service_workflow(
        self, 
        workflow_payload: Dict[str, Any], 
        api_key: str
    ) -> Dict[str, Any]:
        """Create Slack-specific Trigger.dev workflows"""
        
        workflow_name = workflow_payload.get("name")
        config = workflow_payload.get("config", {})
        
        # Define available Slack workflows
        slack_workflows = {
            "team_notifications": {
                "description": "Send automated notifications to team channels",
                "triggers": ["milestone_reached", "deadline_approaching", "error_occurred"],
                "actions": ["send_message", "create_channel", "schedule_message"]
            },
            "project_updates": {
                "description": "Share project progress and updates with team",
                "triggers": ["status_changed", "task_completed", "manual"],
                "actions": ["send_message", "create_thread", "mention_users"]
            },
            "meeting_coordination": {
                "description": "Coordinate meetings and send reminders",
                "triggers": ["meeting_scheduled", "reminder_time"],
                "actions": ["send_message", "schedule_message", "create_channel"]
            },
            "alert_system": {
                "description": "Send alerts and urgent notifications",
                "triggers": ["error_detected", "threshold_exceeded", "manual"],
                "actions": ["send_message", "mention_channel", "escalate"]
            }
        }
        
        workflow_type = config.get("workflow_type", "team_notifications")
        
        if workflow_type not in slack_workflows:
            return {
                "success": False,
                "error": "invalid_workflow_type",
                "available_workflows": list(slack_workflows.keys())
            }
        
        # Create workflow configuration
        workflow_config = {
            "name": workflow_name,
            "service": "slack",
            "type": workflow_type,
            "config": slack_workflows[workflow_type],
            "user_config": config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In a real implementation, this would call Trigger.dev API
        return {
            "success": True,
            "workflow": workflow_config,
            "message": f"Slack workflow '{workflow_name}' created successfully"
        }
    
    # Helper Methods
    
    def create_rich_message_blocks(
        self, 
        title: str, 
        content: str, 
        color: str = "good",
        fields: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Create rich message blocks for better formatting"""
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n{content}"
                }
            }
        ]
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{field['title']}*\n{field['value']}"
                    }
                    for field in fields
                ]
            })
        
        return blocks
    
    def create_action_blocks(self, actions: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create action buttons for interactive messages"""
        
        elements = []
        for action in actions:
            elements.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": action.get("text", "Action")
                },
                "value": action.get("value", ""),
                "action_id": action.get("action_id", f"action_{len(elements)}")
            })
        
        return {
            "type": "actions",
            "elements": elements
        }

# Global instance
slack_integration = SlackIntegration() 