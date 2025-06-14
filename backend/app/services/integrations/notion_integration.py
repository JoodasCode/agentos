from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.services.base_integration import BaseIntegration, IntegrationStatus
from app.models.api_keys import SupportedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class NotionIntegration(BaseIntegration):
    """Notion API integration for page creation, database management, and content automation"""
    
    def __init__(self):
        super().__init__(SupportedService.NOTION)
        self.api_version = "2022-06-28"
    
    @property
    def base_url(self) -> str:
        return "https://api.notion.com/v1"
    
    @property
    def required_scopes(self) -> List[str]:
        return [
            "read_content",
            "update_content", 
            "insert_content",
            "read_user_with_email"
        ]
    
    async def _prepare_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Prepare Notion API headers"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json"
        }
    
    async def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test Notion API connection by getting user info"""
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="users/me",
                api_key=api_key
            )
            
            if result.get("success"):
                user_data = result.get("data", {})
                return {
                    "connected": True,
                    "status": "success",
                    "message": "Successfully connected to Notion",
                    "user_info": {
                        "name": user_data.get("name", "Unknown"),
                        "email": user_data.get("person", {}).get("email", "Unknown"),
                        "workspace": user_data.get("workspace_name", "Personal")
                    }
                }
            else:
                return {
                    "connected": False,
                    "status": "error",
                    "message": result.get("message", "Failed to connect to Notion")
                }
                
        except Exception as e:
            logger.error(f"Notion connection test failed: {str(e)}")
            return {
                "connected": False,
                "status": "error", 
                "message": str(e)
            }
    
    # Core Notion Operations
    
    async def get_databases(self, session_id: str) -> Dict[str, Any]:
        """Get all accessible databases in the workspace"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            result = await self.make_api_request(
                method="POST",
                endpoint="search",
                api_key=api_key,
                data={
                    "filter": {
                        "value": "database",
                        "property": "object"
                    }
                }
            )
            
            if result.get("success"):
                databases = []
                for db in result.get("data", {}).get("results", []):
                    databases.append({
                        "id": db.get("id"),
                        "title": self._extract_title(db.get("title", [])),
                        "url": db.get("url"),
                        "properties": list(db.get("properties", {}).keys())
                    })
                
                return {
                    "success": True,
                    "databases": databases,
                    "count": len(databases)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Notion databases: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_pages(self, session_id: str, database_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pages from workspace or specific database"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            if database_id:
                # Get pages from specific database
                result = await self.make_api_request(
                    method="POST",
                    endpoint=f"databases/{database_id}/query",
                    api_key=api_key,
                    data={}
                )
            else:
                # Search all pages
                result = await self.make_api_request(
                    method="POST",
                    endpoint="search",
                    api_key=api_key,
                    data={
                        "filter": {
                            "value": "page",
                            "property": "object"
                        }
                    }
                )
            
            if result.get("success"):
                pages = []
                for page in result.get("data", {}).get("results", []):
                    pages.append({
                        "id": page.get("id"),
                        "title": self._extract_title(page.get("properties", {}).get("title", {}).get("title", [])),
                        "url": page.get("url"),
                        "created_time": page.get("created_time"),
                        "last_edited_time": page.get("last_edited_time")
                    })
                
                return {
                    "success": True,
                    "pages": pages,
                    "count": len(pages)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting Notion pages: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_page(
        self, 
        session_id: str, 
        title: str, 
        content: str,
        parent_id: Optional[str] = None,
        database_id: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new page in Notion"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            # Prepare parent (either page or database)
            if database_id:
                parent = {"database_id": database_id}
            elif parent_id:
                parent = {"page_id": parent_id}
            else:
                # Create in workspace root (requires page_id)
                return {"success": False, "error": "parent_id or database_id required"}
            
            # Prepare properties
            page_properties = {}
            if database_id and properties:
                page_properties.update(properties)
            else:
                # For regular pages, title is in properties
                page_properties["title"] = {
                    "title": [{"text": {"content": title}}]
                }
            
            # Prepare content blocks
            children = self._content_to_blocks(content)
            
            data = {
                "parent": parent,
                "properties": page_properties,
                "children": children
            }
            
            result = await self.make_api_request(
                method="POST",
                endpoint="pages",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                page_data = result.get("data", {})
                return {
                    "success": True,
                    "page": {
                        "id": page_data.get("id"),
                        "title": title,
                        "url": page_data.get("url"),
                        "created_time": page_data.get("created_time")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_page(
        self, 
        session_id: str, 
        page_id: str, 
        properties: Optional[Dict] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing page"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            # Update properties if provided
            if properties:
                result = await self.make_api_request(
                    method="PATCH",
                    endpoint=f"pages/{page_id}",
                    api_key=api_key,
                    data={"properties": properties}
                )
                
                if not result.get("success"):
                    return result
            
            # Update content if provided
            if content:
                # First, get existing blocks to replace them
                blocks_result = await self.make_api_request(
                    method="GET",
                    endpoint=f"blocks/{page_id}/children",
                    api_key=api_key
                )
                
                if blocks_result.get("success"):
                    # Delete existing blocks
                    existing_blocks = blocks_result.get("data", {}).get("results", [])
                    for block in existing_blocks:
                        await self.make_api_request(
                            method="DELETE",
                            endpoint=f"blocks/{block['id']}",
                            api_key=api_key
                        )
                    
                    # Add new content
                    new_blocks = self._content_to_blocks(content)
                    await self.make_api_request(
                        method="PATCH",
                        endpoint=f"blocks/{page_id}/children",
                        api_key=api_key,
                        data={"children": new_blocks}
                    )
            
            return {"success": True, "message": "Page updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating Notion page: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def add_database_entry(
        self, 
        session_id: str, 
        database_id: str, 
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a new entry to a database"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            data = {
                "parent": {"database_id": database_id},
                "properties": properties
            }
            
            result = await self.make_api_request(
                method="POST",
                endpoint="pages",
                api_key=api_key,
                data=data
            )
            
            if result.get("success"):
                entry_data = result.get("data", {})
                return {
                    "success": True,
                    "entry": {
                        "id": entry_data.get("id"),
                        "url": entry_data.get("url"),
                        "created_time": entry_data.get("created_time")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error adding database entry: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Trigger.dev Workflow Integration
    
    async def _create_service_workflow(
        self, 
        workflow_payload: Dict[str, Any], 
        api_key: str
    ) -> Dict[str, Any]:
        """Create Notion-specific Trigger.dev workflows"""
        
        workflow_name = workflow_payload.get("name")
        config = workflow_payload.get("config", {})
        
        # Define available Notion workflows
        notion_workflows = {
            "content_to_notion": {
                "description": "Automatically create Notion pages from generated content",
                "triggers": ["content_generated", "manual"],
                "actions": ["create_page", "update_database"]
            },
            "task_management": {
                "description": "Sync tasks and projects to Notion databases",
                "triggers": ["task_created", "deadline_approaching"],
                "actions": ["add_database_entry", "update_properties"]
            },
            "meeting_notes": {
                "description": "Create meeting notes and action items in Notion",
                "triggers": ["meeting_scheduled", "meeting_ended"],
                "actions": ["create_page", "add_database_entry"]
            },
            "project_tracking": {
                "description": "Track project progress and milestones",
                "triggers": ["milestone_reached", "status_changed"],
                "actions": ["update_page", "add_database_entry"]
            }
        }
        
        workflow_type = config.get("workflow_type", "content_to_notion")
        
        if workflow_type not in notion_workflows:
            return {
                "success": False,
                "error": "invalid_workflow_type",
                "available_workflows": list(notion_workflows.keys())
            }
        
        # Create workflow configuration
        workflow_config = {
            "name": workflow_name,
            "service": "notion",
            "type": workflow_type,
            "config": notion_workflows[workflow_type],
            "user_config": config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In a real implementation, this would call Trigger.dev API
        # For now, return success with workflow details
        return {
            "success": True,
            "workflow": workflow_config,
            "message": f"Notion workflow '{workflow_name}' created successfully"
        }
    
    # Helper Methods
    
    def _extract_title(self, title_array: List[Dict]) -> str:
        """Extract title text from Notion title array"""
        if not title_array:
            return "Untitled"
        
        title_parts = []
        for item in title_array:
            if item.get("type") == "text":
                title_parts.append(item.get("text", {}).get("content", ""))
        
        return "".join(title_parts) or "Untitled"
    
    def _content_to_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Convert plain text content to Notion blocks"""
        if not content:
            return []
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        blocks = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Check if it's a heading (starts with #)
                if paragraph.startswith('# '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph[2:]}}]
                        }
                    })
                elif paragraph.startswith('## '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_2", 
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph[3:]}}]
                        }
                    })
                elif paragraph.startswith('### '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph[4:]}}]
                        }
                    })
                else:
                    # Regular paragraph
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph}}]
                        }
                    })
        
        return blocks

# Global instance
notion_integration = NotionIntegration() 