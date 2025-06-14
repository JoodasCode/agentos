"""
Trigger.dev Service - Real integration with Trigger.dev v3
Handles triggering automation workflows from the FastAPI backend
"""

import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class TriggerDevService:
    """Real Trigger.dev v3 integration service"""
    
    def __init__(self):
        # Use our local API bridge instead of direct Trigger.dev API
        self.api_url = os.getenv('TRIGGER_BRIDGE_URL', 'http://localhost:3001')
        self.secret_key = os.getenv('TRIGGER_SECRET_KEY')  # Still needed for auth
        self.project_ref = os.getenv('TRIGGER_PROJECT_REF', 'agentos-automation')
        
        if not self.secret_key:
            logger.warning("TRIGGER_SECRET_KEY not set - Trigger.dev integration disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Trigger.dev service initialized", project_ref=self.project_ref)
    
    def is_available(self) -> bool:
        """Check if Trigger.dev is properly configured"""
        return self.enabled and bool(self.secret_key)
    
    async def trigger_product_hunt_launch(
        self,
        product_name: str,
        launch_date: str,
        description: str,
        website: str,
        twitter_handle: Optional[str] = None,
        slack_webhook: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger Product Hunt launch automation"""
        if not self.is_available():
            raise ValueError("Trigger.dev not configured")
        
        payload = {
            "productName": product_name,
            "launchDate": launch_date,
            "description": description,
            "website": website,
            "twitterHandle": twitter_handle,
            "slackWebhook": slack_webhook
        }
        
        return await self._trigger_task("product-hunt-launch", payload)
    
    async def trigger_content_generation(
        self,
        content_type: str,
        topic: str,
        target_audience: str,
        tone: str = "professional",
        platforms: Optional[List[str]] = None,
        scheduled_date: Optional[str] = None,
        notion_config: Optional[Dict[str, str]] = None,
        slack_config: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Trigger content generation automation"""
        if not self.is_available():
            raise ValueError("Trigger.dev not configured")
        
        integrations = {}
        if notion_config:
            integrations["notion"] = notion_config
        if slack_config:
            integrations["slack"] = slack_config
        
        payload = {
            "contentType": content_type,
            "topic": topic,
            "targetAudience": target_audience,
            "tone": tone,
            "platforms": platforms,
            "scheduledDate": scheduled_date,
            "integrations": integrations
        }
        
        return await self._trigger_task("content-generation", payload)
    
    async def trigger_analytics_tracking(
        self,
        event_type: str,
        user_id: str,
        properties: Dict[str, Any],
        scheduled_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger analytics tracking automation"""
        if not self.is_available():
            raise ValueError("Trigger.dev not configured")
        
        payload = {
            "eventType": event_type,
            "userId": user_id,
            "properties": properties,
            "scheduledDate": scheduled_date,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self._trigger_task("analytics-tracking", payload)
    
    async def _trigger_task(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to trigger a Trigger.dev task"""
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            trigger_data = {
                "taskId": task_id,
                "payload": payload
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/trigger/{task_id}",
                    json=payload,  # Send payload directly, not wrapped
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully triggered task {task_id}", 
                              task_id=task_id, run_id=result.get('id'))
                    return {
                        "success": True,
                        "task_id": task_id,
                        "run_id": result.get('id'),
                        "status": result.get('status'),
                        "triggered_at": datetime.utcnow().isoformat()
                    }
                else:
                    error_msg = f"Trigger.dev API error: {response.status_code} - {response.text}"
                    logger.error(error_msg, task_id=task_id)
                    return {
                        "success": False,
                        "error": error_msg,
                        "task_id": task_id
                    }
                    
        except Exception as e:
            error_msg = f"Failed to trigger task {task_id}: {str(e)}"
            logger.error(error_msg, task_id=task_id, error=str(e))
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id
            }
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get the status of a Trigger.dev run"""
        if not self.is_available():
            raise ValueError("Trigger.dev not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/v1/runs/{run_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Failed to get run status: {response.status_code} - {response.text}"
                    logger.error(error_msg, run_id=run_id)
                    return {"error": error_msg}
                    
        except Exception as e:
            error_msg = f"Failed to get run status: {str(e)}"
            logger.error(error_msg, run_id=run_id, error=str(e))
            return {"error": error_msg}
    
    async def list_runs(self, task_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """List recent Trigger.dev runs"""
        if not self.is_available():
            raise ValueError("Trigger.dev not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            params = {"limit": limit}
            if task_id:
                params["taskId"] = task_id
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/v1/runs",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Failed to list runs: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {"error": error_msg}
                    
        except Exception as e:
            error_msg = f"Failed to list runs: {str(e)}"
            logger.error(error_msg, error=str(e))
            return {"error": error_msg}

# Global instance
trigger_service = TriggerDevService() 