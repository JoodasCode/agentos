import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.services.trigger_service import TriggerService
from app.core.logging import get_logger

logger = get_logger(__name__)

class ActionBridge:
    """Bridge between conversational agents and Trigger.dev job execution"""
    
    def __init__(self):
        self.trigger_service = TriggerService()
        logger.info("ActionBridge initialized")
    
    async def convert_conversation_to_actions(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert conversation context into actionable job parameters"""
        
        logger.info("Converting conversation to actions", 
                   conversation_id=conversation_context.get("id"))
        
        # Extract key information from conversation
        extracted_info = await self._extract_conversation_info(conversation_context)
        
        # Create execution plan
        execution_plan = await self.trigger_service.create_job_execution_plan(conversation_context)
        
        # Map conversation info to job parameters
        job_parameters = await self._map_info_to_job_params(extracted_info, execution_plan)
        
        # Validate all job parameters
        validation_results = await self._validate_all_jobs(job_parameters)
        
        return {
            "execution_plan": execution_plan,
            "job_parameters": job_parameters,
            "validation_results": validation_results,
            "extracted_info": extracted_info,
            "ready_to_execute": all(result["valid"] for result in validation_results.values())
        }
    
    async def _extract_conversation_info(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured information from conversation messages"""
        
        messages = conversation_context.get("messages", [])
        user_messages = [msg.get("content", "") for msg in messages if msg.get("type") == "user"]
        conversation_text = " ".join(user_messages)
        
        # Initialize extracted info structure
        extracted_info = {
            "project_details": {},
            "timeline": {},
            "content_preferences": {},
            "analytics_requirements": {},
            "notification_preferences": {},
            "automation_preferences": {}
        }
        
        # Extract project details
        extracted_info["project_details"] = self._extract_project_details(conversation_text)
        
        # Extract timeline information
        extracted_info["timeline"] = self._extract_timeline_info(conversation_text)
        
        # Extract content preferences
        extracted_info["content_preferences"] = self._extract_content_preferences(conversation_text)
        
        # Extract analytics requirements
        extracted_info["analytics_requirements"] = self._extract_analytics_requirements(conversation_text)
        
        # Extract notification preferences
        extracted_info["notification_preferences"] = self._extract_notification_preferences(conversation_text)
        
        # Extract automation preferences
        extracted_info["automation_preferences"] = self._extract_automation_preferences(conversation_text)
        
        return extracted_info
    
    def _extract_project_details(self, text: str) -> Dict[str, Any]:
        """Extract project-related details from conversation"""
        
        text_lower = text.lower()
        
        # Simple keyword-based extraction (in production, use NLP)
        project_details = {
            "has_product_name": any(word in text_lower for word in ["product", "app", "tool", "service"]),
            "has_description": any(word in text_lower for word in ["does", "helps", "solves", "enables"]),
            "has_target_audience": any(word in text_lower for word in ["users", "customers", "audience", "market"]),
            "launch_type": "product_hunt" if any(word in text_lower for word in ["product hunt", "ph", "launch"]) else "general"
        }
        
        # Try to extract specific values
        if "product hunt" in text_lower or "ph" in text_lower:
            project_details["platform"] = "product_hunt"
        
        return project_details
    
    def _extract_timeline_info(self, text: str) -> Dict[str, Any]:
        """Extract timeline and deadline information"""
        
        text_lower = text.lower()
        
        timeline_info = {
            "urgency": "medium",
            "has_deadline": False,
            "timeline_preference": None
        }
        
        # Detect urgency
        if any(word in text_lower for word in ["asap", "urgent", "immediately", "rush"]):
            timeline_info["urgency"] = "high"
        elif any(word in text_lower for word in ["flexible", "no rush", "whenever"]):
            timeline_info["urgency"] = "low"
        
        # Detect timeline preferences
        if "same day" in text_lower or "today" in text_lower:
            timeline_info["timeline_preference"] = "same-day"
        elif "week" in text_lower:
            timeline_info["timeline_preference"] = "1-week"
        elif "month" in text_lower:
            timeline_info["timeline_preference"] = "1-month"
        
        # Detect if deadline mentioned
        timeline_info["has_deadline"] = any(word in text_lower for word in ["deadline", "by", "before", "due"])
        
        return timeline_info
    
    def _extract_content_preferences(self, text: str) -> Dict[str, Any]:
        """Extract content and messaging preferences"""
        
        text_lower = text.lower()
        
        content_prefs = {
            "tone": None,
            "platforms": [],
            "content_types": []
        }
        
        # Detect tone preferences
        tone_mapping = {
            "professional": ["professional", "business", "formal"],
            "casual": ["casual", "friendly", "relaxed"],
            "technical": ["technical", "detailed", "precise"],
            "playful": ["playful", "fun", "creative"],
            "authoritative": ["authoritative", "expert", "confident"]
        }
        
        for tone, keywords in tone_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                content_prefs["tone"] = tone
                break
        
        # Detect platforms
        platform_keywords = {
            "twitter": ["twitter", "tweet"],
            "linkedin": ["linkedin"],
            "product_hunt": ["product hunt", "ph"],
            "email": ["email", "newsletter"],
            "website": ["website", "landing page"]
        }
        
        for platform, keywords in platform_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                content_prefs["platforms"].append(platform)
        
        # Detect content types
        content_type_keywords = {
            "tagline": ["tagline", "slogan"],
            "description": ["description", "copy"],
            "social_posts": ["social", "posts", "tweets"],
            "email_sequence": ["email sequence", "drip campaign"]
        }
        
        for content_type, keywords in content_type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                content_prefs["content_types"].append(content_type)
        
        return content_prefs
    
    def _extract_analytics_requirements(self, text: str) -> Dict[str, Any]:
        """Extract analytics and tracking requirements"""
        
        text_lower = text.lower()
        
        analytics_reqs = {
            "metrics": [],
            "reporting_frequency": None,
            "alerts_wanted": False
        }
        
        # Detect metrics
        metric_keywords = {
            "signups": ["signup", "registration", "user"],
            "revenue": ["revenue", "sales", "money"],
            "traffic": ["traffic", "visitors", "pageviews"],
            "social_engagement": ["engagement", "likes", "shares"],
            "product_hunt_rank": ["rank", "ranking", "position"]
        }
        
        for metric, keywords in metric_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                analytics_reqs["metrics"].append(metric)
        
        # Detect reporting frequency
        if any(word in text_lower for word in ["real-time", "live", "instant"]):
            analytics_reqs["reporting_frequency"] = "real-time"
        elif "daily" in text_lower:
            analytics_reqs["reporting_frequency"] = "daily"
        elif "weekly" in text_lower:
            analytics_reqs["reporting_frequency"] = "weekly"
        
        # Detect alert preferences
        analytics_reqs["alerts_wanted"] = any(word in text_lower for word in ["alert", "notify", "remind"])
        
        return analytics_reqs
    
    def _extract_notification_preferences(self, text: str) -> Dict[str, Any]:
        """Extract notification and reminder preferences"""
        
        text_lower = text.lower()
        
        notification_prefs = {
            "channels": [],
            "reminder_timing": [],
            "escalation_wanted": False
        }
        
        # Detect notification channels
        channel_keywords = {
            "email": ["email"],
            "slack": ["slack"],
            "sms": ["sms", "text", "phone"]
        }
        
        for channel, keywords in channel_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                notification_prefs["channels"].append(channel)
        
        # Detect reminder timing preferences
        timing_keywords = {
            "1-day-before": ["day before", "24 hours"],
            "1-hour-before": ["hour before", "60 minutes"],
            "at-launch": ["at launch", "when live"],
            "1-day-after": ["day after", "follow up"]
        }
        
        for timing, keywords in timing_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                notification_prefs["reminder_timing"].append(timing)
        
        # Detect escalation preferences
        notification_prefs["escalation_wanted"] = any(word in text_lower for word in ["escalate", "urgent", "important"])
        
        return notification_prefs
    
    def _extract_automation_preferences(self, text: str) -> Dict[str, Any]:
        """Extract automation and workflow preferences"""
        
        text_lower = text.lower()
        
        automation_prefs = {
            "workflow_types": [],
            "approval_needed": False,
            "error_handling": "standard"
        }
        
        # Detect workflow types
        workflow_keywords = {
            "approval_chains": ["approval", "review", "sign-off"],
            "content_review": ["content review", "proofread"],
            "launch_sequence": ["launch sequence", "coordinated launch"],
            "follow_up": ["follow up", "post-launch"]
        }
        
        for workflow, keywords in workflow_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                automation_prefs["workflow_types"].append(workflow)
        
        # Detect approval preferences
        automation_prefs["approval_needed"] = any(word in text_lower for word in ["approve", "review", "check"])
        
        # Detect error handling preferences
        if any(word in text_lower for word in ["careful", "safe", "conservative"]):
            automation_prefs["error_handling"] = "conservative"
        elif any(word in text_lower for word in ["aggressive", "fast", "quick"]):
            automation_prefs["error_handling"] = "aggressive"
        
        return automation_prefs
    
    async def _map_info_to_job_params(self, extracted_info: Dict[str, Any], execution_plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Map extracted information to job parameters"""
        
        job_parameters = {}
        
        for job in execution_plan["jobs"]:
            job_type = job["type"]
            job_parameters[job_type] = await self._create_job_params(job_type, extracted_info)
        
        return job_parameters
    
    async def _create_job_params(self, job_type: str, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create parameters for a specific job type"""
        
        if job_type == "product_hunt_launch":
            return {
                "launch_date": extracted_info["timeline"].get("timeline_preference", "1-week"),
                "product_name": "Your Product",  # Would be extracted from conversation
                "tagline": "Generated from conversation",
                "description": "Generated from conversation context",
                "urgency": extracted_info["timeline"].get("urgency", "medium")
            }
        
        elif job_type == "content_generation":
            return {
                "value_proposition": "Extracted from conversation",
                "target_audience": "Identified audience",
                "tone": extracted_info["content_preferences"].get("tone", "professional"),
                "platforms": extracted_info["content_preferences"].get("platforms", ["product_hunt"]),
                "content_types": extracted_info["content_preferences"].get("content_types", ["tagline", "description"])
            }
        
        elif job_type == "analytics_tracking":
            return {
                "metrics_to_track": extracted_info["analytics_requirements"].get("metrics", ["signups", "traffic"]),
                "reporting_frequency": extracted_info["analytics_requirements"].get("reporting_frequency", "daily"),
                "alerts_enabled": extracted_info["analytics_requirements"].get("alerts_wanted", True)
            }
        
        elif job_type == "notification_system":
            return {
                "reminder_schedule": extracted_info["notification_preferences"].get("reminder_timing", ["1-day-before"]),
                "notification_channels": extracted_info["notification_preferences"].get("channels", ["email"]),
                "escalation_enabled": extracted_info["notification_preferences"].get("escalation_wanted", False)
            }
        
        elif job_type == "workflow_automation":
            return {
                "workflow_type": extracted_info["automation_preferences"].get("workflow_types", ["launch_sequence"])[0] if extracted_info["automation_preferences"].get("workflow_types") else "launch_sequence",
                "trigger_conditions": "conversation_complete",
                "approval_required": extracted_info["automation_preferences"].get("approval_needed", False)
            }
        
        return {}
    
    async def _validate_all_jobs(self, job_parameters: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Validate parameters for all jobs"""
        
        validation_results = {}
        
        for job_type, params in job_parameters.items():
            validation_results[job_type] = await self.trigger_service.validate_job_parameters(job_type, params)
        
        return validation_results
    
    async def execute_action_plan(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete action plan"""
        
        if not action_plan.get("ready_to_execute", False):
            return {
                "success": False,
                "error": "Action plan not ready for execution",
                "validation_results": action_plan.get("validation_results", {})
            }
        
        logger.info("Executing action plan", 
                   job_count=len(action_plan["job_parameters"]))
        
        execution_results = {}
        
        # Execute jobs in priority order
        jobs = action_plan["execution_plan"]["jobs"]
        sorted_jobs = sorted(jobs, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)
        
        for job in sorted_jobs:
            job_type = job["type"]
            job_params = action_plan["job_parameters"][job_type]
            
            try:
                result = await self.trigger_service.execute_job(job_type, job_params)
                execution_results[job_type] = {
                    "success": True,
                    "job_id": result["job_id"],
                    "status": result["status"],
                    "estimated_completion": result["estimated_completion"]
                }
                
                logger.info("Job executed successfully", 
                           job_type=job_type, 
                           job_id=result["job_id"])
                
            except Exception as e:
                execution_results[job_type] = {
                    "success": False,
                    "error": str(e)
                }
                
                logger.error("Job execution failed", 
                           job_type=job_type, 
                           error=str(e))
        
        return {
            "success": True,
            "execution_results": execution_results,
            "total_jobs": len(execution_results),
            "successful_jobs": len([r for r in execution_results.values() if r["success"]]),
            "failed_jobs": len([r for r in execution_results.values() if not r["success"]])
        }
    
    async def get_execution_status(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of all executing jobs"""
        
        status_results = {}
        
        for job_type, result in execution_results.get("execution_results", {}).items():
            if result["success"] and "job_id" in result:
                try:
                    status = await self.trigger_service.get_job_status(result["job_id"])
                    status_results[job_type] = status
                except Exception as e:
                    status_results[job_type] = {
                        "error": f"Failed to get status: {str(e)}"
                    }
        
        return status_results 