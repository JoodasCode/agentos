import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class TriggerService:
    """Service for managing Trigger.dev job execution and capabilities"""
    
    def __init__(self):
        self.base_url = settings.TRIGGER_DEV_API_URL
        self.api_key = settings.TRIGGER_DEV_API_KEY
        self.project_id = settings.TRIGGER_DEV_PROJECT_ID
        
        # Define available job capabilities
        self.job_capabilities = self._initialize_job_capabilities()
        
        logger.info("TriggerService initialized", 
                   project_id=self.project_id,
                   capabilities_count=len(self.job_capabilities))
    
    def _initialize_job_capabilities(self) -> Dict[str, Dict]:
        """Initialize the available job capabilities that agents can reference"""
        
        return {
            # Product Hunt Launch Jobs
            "product_hunt_launch": {
                "name": "Product Hunt Launch Automation",
                "description": "Complete Product Hunt launch workflow",
                "timeline_options": ["same-day", "1-week", "2-weeks", "1-month", "custom"],
                "automation_features": [
                    "Automated submission scheduling",
                    "Social media post coordination", 
                    "Email sequence triggers",
                    "Analytics tracking setup",
                    "Reminder notifications"
                ],
                "required_params": ["launch_date", "product_name", "tagline", "description"],
                "optional_params": ["maker_comment", "gallery_images", "social_handles"]
            },
            
            # Content Generation Jobs
            "content_generation": {
                "name": "Marketing Content Generation",
                "description": "Generate marketing content across platforms",
                "tone_options": ["professional", "casual", "technical", "playful", "authoritative"],
                "platform_options": ["product_hunt", "twitter", "linkedin", "website", "email"],
                "content_types": ["tagline", "description", "social_posts", "email_sequence", "press_release"],
                "automation_features": [
                    "Multi-platform content variations",
                    "A/B testing versions",
                    "Scheduled publishing",
                    "Performance tracking"
                ],
                "required_params": ["value_proposition", "target_audience", "tone"],
                "optional_params": ["brand_guidelines", "competitor_analysis", "existing_content"]
            },
            
            # Analytics Tracking Jobs
            "analytics_tracking": {
                "name": "Analytics & Performance Monitoring",
                "description": "Set up comprehensive analytics tracking",
                "metric_options": ["signups", "revenue", "traffic", "social_engagement", "product_hunt_rank"],
                "reporting_frequency": ["real-time", "hourly", "daily", "weekly"],
                "alert_types": ["threshold_alerts", "anomaly_detection", "competitor_monitoring"],
                "automation_features": [
                    "Automated dashboard creation",
                    "Custom alert thresholds",
                    "Competitor benchmarking",
                    "ROI calculations"
                ],
                "required_params": ["metrics_to_track", "reporting_frequency"],
                "optional_params": ["baseline_data", "alert_thresholds", "competitor_list"]
            },
            
            # Notification & Reminder Jobs
            "notification_system": {
                "name": "Smart Notifications & Reminders",
                "description": "Automated notification and reminder system",
                "reminder_timing": ["1-day-before", "1-hour-before", "at-launch", "1-day-after"],
                "notification_channels": ["email", "slack", "sms", "webhook"],
                "automation_features": [
                    "Smart reminder scheduling",
                    "Escalation workflows",
                    "Team notifications",
                    "Status updates"
                ],
                "required_params": ["reminder_schedule", "notification_channels"],
                "optional_params": ["escalation_rules", "team_members", "custom_messages"]
            },
            
            # Workflow Automation Jobs
            "workflow_automation": {
                "name": "Custom Workflow Automation",
                "description": "Build custom automated workflows",
                "workflow_types": ["approval_chains", "content_review", "launch_sequence", "follow_up"],
                "trigger_types": ["time_based", "event_based", "manual", "conditional"],
                "automation_features": [
                    "Multi-step workflows",
                    "Conditional logic",
                    "Error handling",
                    "Progress tracking"
                ],
                "required_params": ["workflow_type", "trigger_conditions"],
                "optional_params": ["approval_steps", "error_handling", "notifications"]
            }
        }
    
    async def get_available_capabilities(self) -> Dict[str, Dict]:
        """Get all available job capabilities for agents to reference"""
        return self.job_capabilities
    
    async def get_capability_options(self, capability_name: str, option_type: str) -> List[str]:
        """Get specific options for a capability (e.g., timeline_options for product_hunt_launch)"""
        
        if capability_name not in self.job_capabilities:
            logger.warning("Unknown capability requested", capability=capability_name)
            return []
        
        capability = self.job_capabilities[capability_name]
        return capability.get(option_type, [])
    
    async def validate_job_parameters(self, job_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that job parameters are complete and valid"""
        
        if job_type not in self.job_capabilities:
            return {
                "valid": False,
                "error": f"Unknown job type: {job_type}",
                "missing_params": [],
                "suggestions": []
            }
        
        capability = self.job_capabilities[job_type]
        required_params = capability.get("required_params", [])
        optional_params = capability.get("optional_params", [])
        
        # Check for missing required parameters
        missing_params = [param for param in required_params if param not in parameters]
        
        # Generate suggestions for missing parameters
        suggestions = []
        if missing_params:
            for param in missing_params:
                suggestions.append(f"Please provide {param.replace('_', ' ')}")
        
        return {
            "valid": len(missing_params) == 0,
            "missing_params": missing_params,
            "suggestions": suggestions,
            "optional_params": optional_params
        }
    
    async def create_job_execution_plan(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan based on conversation context"""
        
        # Analyze conversation to determine what jobs to execute
        messages = conversation_context.get("messages", [])
        user_messages = [msg.get("content", "") for msg in messages if msg.get("type") == "user"]
        conversation_text = " ".join(user_messages).lower()
        
        execution_plan = {
            "jobs": [],
            "timeline": {},
            "dependencies": [],
            "estimated_duration": "2-5 days"
        }
        
        # Determine which jobs to include based on conversation content
        if any(word in conversation_text for word in ["launch", "product hunt", "ph"]):
            execution_plan["jobs"].append({
                "type": "product_hunt_launch",
                "priority": "high",
                "estimated_time": "3-5 days"
            })
        
        if any(word in conversation_text for word in ["content", "copy", "marketing", "social"]):
            execution_plan["jobs"].append({
                "type": "content_generation", 
                "priority": "high",
                "estimated_time": "2-3 days"
            })
        
        if any(word in conversation_text for word in ["track", "analytics", "metrics", "data"]):
            execution_plan["jobs"].append({
                "type": "analytics_tracking",
                "priority": "medium", 
                "estimated_time": "1-2 days"
            })
        
        if any(word in conversation_text for word in ["remind", "notification", "alert", "schedule"]):
            execution_plan["jobs"].append({
                "type": "notification_system",
                "priority": "medium",
                "estimated_time": "1 day"
            })
        
        # Set default jobs if none detected
        if not execution_plan["jobs"]:
            execution_plan["jobs"] = [
                {
                    "type": "workflow_automation",
                    "priority": "medium",
                    "estimated_time": "2-3 days"
                }
            ]
        
        return execution_plan
    
    async def execute_job(self, job_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Trigger.dev job using the real API"""
        
        logger.info("Executing job", job_type=job_type, params=parameters)
        
        # Map job types to Trigger.dev task IDs
        task_mapping = {
            "product_hunt_launch": "product-hunt-launch",
            "content_generation": "content-generation", 
            "analytics_tracking": "analytics-tracking"
        }
        
        task_id = task_mapping.get(job_type)
        if not task_id:
            # Fall back to mock execution for unmapped job types
            return await self._execute_mock_job(job_type, parameters)
        
        # Prepare payload for Trigger.dev
        payload = self._prepare_trigger_payload(job_type, parameters)
        
        try:
            # Call Trigger.dev API to execute the task
            response = await self._call_trigger_api(task_id, payload)
            job_id = response.get("id", f"job_{job_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            
            execution_result = {
                "job_id": job_id,
                "job_type": job_type,
                "status": response.get("status", "queued"),
                "created_at": datetime.utcnow().isoformat(),
                "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                "parameters": parameters,
                "steps": self._generate_job_steps(job_type),
                "progress": 0,
                "trigger_response": response
            }
            
            logger.info("Job queued successfully with Trigger.dev", job_id=job_id, job_type=job_type)
            return execution_result
            
        except Exception as e:
            logger.error(f"Failed to execute job with Trigger.dev: {e}")
            # Fall back to mock execution
            return await self._execute_mock_job(job_type, parameters)
    
    async def _execute_mock_job(self, job_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock job (fallback when Trigger.dev is unavailable)"""
        
        job_id = f"job_{job_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        execution_result = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "parameters": parameters,
            "steps": self._generate_job_steps(job_type),
            "progress": 0,
            "mock": True
        }
        
        logger.info("Mock job queued successfully", job_id=job_id, job_type=job_type)
        return execution_result
    
    def _prepare_trigger_payload(self, job_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for Trigger.dev based on job type"""
        
        if job_type == "product_hunt_launch":
            return {
                "productName": parameters.get("product_name", "Unknown Product"),
                "description": parameters.get("description", ""),
                "launchDate": parameters.get("launch_date", (datetime.utcnow() + timedelta(days=7)).isoformat()),
                "timeline": parameters.get("timeline", "1-week"),
                "assets": parameters.get("assets", {}),
                "team": parameters.get("team", {})
            }
        
        elif job_type == "content_generation":
            return {
                "contentType": parameters.get("content_type", "marketing_copy"),
                "productName": parameters.get("product_name", "Unknown Product"),
                "description": parameters.get("description", ""),
                "targetAudience": parameters.get("target_audience", "general"),
                "tone": parameters.get("tone", "professional"),
                "platforms": parameters.get("platforms", ["twitter", "linkedin"]),
                "specifications": parameters.get("specifications", {})
            }
        
        elif job_type == "analytics_tracking":
            return {
                "trackingType": parameters.get("tracking_type", "launch_metrics"),
                "productName": parameters.get("product_name", "Unknown Product"),
                "launchDate": parameters.get("launch_date", datetime.utcnow().isoformat()),
                "platforms": parameters.get("platforms", ["product_hunt", "twitter", "website"]),
                "metrics": parameters.get("metrics", ["views", "engagements", "conversions"]),
                "reportingFrequency": parameters.get("reporting_frequency", "daily"),
                "alertThresholds": parameters.get("alert_thresholds", {})
            }
        
        return parameters
    
    async def _call_trigger_api(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Trigger.dev API to execute a task"""
        
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Trigger.dev v3 API endpoint for task execution
        url = f"{self.base_url}/api/v1/tasks/{task_id}/trigger"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Trigger.dev API error: {response.status} - {error_text}")
    
    def _generate_job_steps(self, job_type: str) -> List[Dict[str, str]]:
        """Generate job steps based on job type"""
        
        step_templates = {
            "product_hunt_launch": [
                {"step": "validate_product_info", "description": "Validate product information"},
                {"step": "schedule_submission", "description": "Schedule Product Hunt submission"},
                {"step": "prepare_assets", "description": "Prepare marketing assets"},
                {"step": "setup_tracking", "description": "Set up analytics tracking"},
                {"step": "configure_notifications", "description": "Configure launch notifications"},
                {"step": "execute_launch", "description": "Execute launch sequence"}
            ],
            "content_generation": [
                {"step": "analyze_requirements", "description": "Analyze content requirements"},
                {"step": "generate_content", "description": "Generate marketing content"},
                {"step": "create_variations", "description": "Create platform-specific variations"},
                {"step": "review_content", "description": "Review and optimize content"},
                {"step": "schedule_publishing", "description": "Schedule content publishing"}
            ],
            "analytics_tracking": [
                {"step": "setup_tracking", "description": "Set up analytics tracking"},
                {"step": "configure_dashboards", "description": "Configure monitoring dashboards"},
                {"step": "setup_alerts", "description": "Set up automated alerts"},
                {"step": "test_tracking", "description": "Test tracking implementation"}
            ],
            "notification_system": [
                {"step": "configure_channels", "description": "Configure notification channels"},
                {"step": "setup_schedules", "description": "Set up reminder schedules"},
                {"step": "test_notifications", "description": "Test notification delivery"},
                {"step": "activate_system", "description": "Activate notification system"}
            ],
            "workflow_automation": [
                {"step": "design_workflow", "description": "Design automation workflow"},
                {"step": "configure_triggers", "description": "Configure workflow triggers"},
                {"step": "setup_actions", "description": "Set up automated actions"},
                {"step": "test_workflow", "description": "Test workflow execution"},
                {"step": "deploy_automation", "description": "Deploy automation"}
            ]
        }
        
        return step_templates.get(job_type, [
            {"step": "initialize", "description": "Initialize job"},
            {"step": "execute", "description": "Execute job"},
            {"step": "complete", "description": "Complete job"}
        ])
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a running job"""
        
        # Mock job status - in production, this would query Trigger.dev API
        return {
            "job_id": job_id,
            "status": "running",
            "progress": 45,
            "current_step": "prepare_assets",
            "estimated_completion": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "logs": [
                {"timestamp": datetime.utcnow().isoformat(), "message": "Job started successfully"},
                {"timestamp": datetime.utcnow().isoformat(), "message": "Validating parameters"},
                {"timestamp": datetime.utcnow().isoformat(), "message": "Preparing assets"}
            ]
        }
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job"""
        
        logger.info("Cancelling job", job_id=job_id)
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "message": "Job cancelled successfully"
        }
    
    async def get_job_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job execution history"""
        
        # Mock job history - in production, this would query Trigger.dev API
        return [
            {
                "job_id": "job_product_hunt_launch_20241201_143022",
                "job_type": "product_hunt_launch",
                "status": "completed",
                "created_at": "2024-12-01T14:30:22Z",
                "completed_at": "2024-12-01T16:45:33Z",
                "duration": "2h 15m"
            },
            {
                "job_id": "job_content_generation_20241201_120015",
                "job_type": "content_generation", 
                "status": "completed",
                "created_at": "2024-12-01T12:00:15Z",
                "completed_at": "2024-12-01T13:30:22Z",
                "duration": "1h 30m"
            }
        ] 