import agentscope
from agentscope.agents import DialogAgent
from agentscope.message import Msg
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.models.conversation import QuickOption, InteractionMode, QuestionType

logger = get_logger(__name__)

class TriggerAwareQuestionEngine:
    """Ensures agent questions align with available Trigger.dev capabilities"""
    
    def __init__(self):
        self.available_jobs = self._load_available_jobs()
    
    def _load_available_jobs(self) -> Dict:
        """Load all available Trigger.dev jobs and their parameters"""
        return {
            # Product Hunt Launch Jobs
            "product_hunt.launch.create_assets": {
                "parameters": ["launch_date", "product_name", "tagline", "description", "logo_url", "gallery_images"],
                "scheduling": ["immediate", "scheduled"],
                "timeline_options": ["same_day", "1_week", "2_weeks", "1_month", "custom_date"]
            },
            "product_hunt.launch.schedule_posts": {
                "parameters": ["launch_date", "social_platforms", "post_content", "timing_strategy"],
                "platforms": ["twitter", "linkedin", "facebook", "instagram"],
                "timing_strategies": ["launch_day_only", "pre_launch_teasers", "post_launch_follow_up"]
            },
            "content.generate.marketing_copy": {
                "parameters": ["tone", "audience", "platform", "content_type", "brand_guidelines"],
                "tones": ["professional", "casual", "technical", "playful", "authoritative"],
                "platforms": ["product_hunt", "twitter", "linkedin", "website", "email"],
                "content_types": ["tagline", "description", "social_posts", "email_sequence"]
            },
            "analytics.track.launch_metrics": {
                "parameters": ["metrics_to_track", "reporting_frequency", "alert_thresholds"],
                "metrics": ["signups", "revenue", "traffic", "social_engagement", "product_hunt_rank"],
                "frequencies": ["real_time", "hourly", "daily", "weekly"]
            },
            "notifications.send.reminders": {
                "parameters": ["reminder_type", "schedule", "recipients", "message_template"],
                "reminder_types": ["launch_prep", "content_review", "go_live", "follow_up"],
                "schedules": ["1_day_before", "1_hour_before", "at_launch", "1_day_after"]
            }
        }
    
    def get_valid_options_for_question(self, question_type: str, context: dict) -> List[QuickOption]:
        """Return only options that Trigger.dev can actually execute"""
        
        if question_type == "timeline":
            valid_timelines = []
            for job_id, job_config in self.available_jobs.items():
                if "timeline_options" in job_config:
                    valid_timelines.extend(job_config["timeline_options"])
            
            options = [
                QuickOption(id="same_day", value="same_day", label="Today", available="same_day" in valid_timelines),
                QuickOption(id="1_week", value="1_week", label="Next Week", available="1_week" in valid_timelines),
                QuickOption(id="2_weeks", value="2_weeks", label="In 2 Weeks", available="2_weeks" in valid_timelines),
                QuickOption(id="1_month", value="1_month", label="Next Month", available="1_month" in valid_timelines),
                QuickOption(id="custom_date", value="custom_date", label="Specific Date", available="custom_date" in valid_timelines)
            ]
            return [opt for opt in options if opt.available]
        
        elif question_type == "content_tone":
            content_job = self.available_jobs.get("content.generate.marketing_copy", {})
            available_tones = content_job.get("tones", [])
            
            return [
                QuickOption(id=tone, value=tone, label=tone.title(), available=True)
                for tone in available_tones
            ]
        
        elif question_type == "social_platforms":
            social_job = self.available_jobs.get("product_hunt.launch.schedule_posts", {})
            available_platforms = social_job.get("platforms", [])
            
            return [
                QuickOption(id=platform, value=platform, label=platform.title(), available=True)
                for platform in available_platforms
            ]
        
        elif question_type == "success_metrics":
            analytics_job = self.available_jobs.get("analytics.track.launch_metrics", {})
            available_metrics = analytics_job.get("metrics", [])
            
            return [
                QuickOption(id=metric, value=metric, label=metric.replace("_", " ").title(), available=True)
                for metric in available_metrics
            ]
        
        return []

class ConversationalAgent(DialogAgent):
    """Base class for conversational agents with personality, memory, and questioning intelligence"""
    
    def __init__(self, name: str, personality: dict, conversation_style: str, question_patterns: list, **kwargs):
        # Set name first so it's available in _build_conversational_prompt
        self.name = name
        self.personality = personality
        self.conversation_style = conversation_style
        self.question_patterns = question_patterns
        self.conversation_memory = []
        self.active_topics = []
        self.unanswered_questions = []
        self.trigger_engine = TriggerAwareQuestionEngine()
        
        # Initialize AgentScope DialogAgent
        from app.core.agentscope_config import get_default_model_config
        
        super().__init__(
            name=name,
            sys_prompt=self._build_conversational_prompt(),
            model_config_name=get_default_model_config(),
            **kwargs
        )
        
        logger.info(f"Initialized conversational agent: {name}")
    
    def _build_conversational_prompt(self) -> str:
        """Build the system prompt for the conversational agent"""
        
        trigger_capabilities = f"""
Available Job Categories:
- Product Hunt launch automation
- Content generation (marketing copy, social posts)
- Social media scheduling (Twitter, LinkedIn, Facebook, Instagram)  
- Analytics tracking (signups, revenue, traffic, engagement)
- Notification/reminder systems

Available content tones: {', '.join(self.trigger_engine.available_jobs.get('content.generate.marketing_copy', {}).get('tones', []))}
Available platforms: {', '.join(self.trigger_engine.available_jobs.get('product_hunt.launch.schedule_posts', {}).get('platforms', []))}
Available metrics: {', '.join(self.trigger_engine.available_jobs.get('analytics.track.launch_metrics', {}).get('metrics', []))}
"""
        
        return f"""You are {self.name}, a conversational AI agent in Agent OS V2.

PERSONALITY: {self.personality['description']}
CONVERSATION STYLE: {self.conversation_style}
EXPERTISE: {self.personality['expertise']}

QUESTION PATTERNS YOU SHOULD ASK:
{chr(10).join(f"- {pattern}" for pattern in self.question_patterns)}

TRIGGER.DEV CAPABILITIES AWARENESS:
You can only suggest options and ask questions that align with our available Trigger.dev jobs:

{trigger_capabilities}

CONVERSATION RULES:
1. Be genuinely conversational - ask questions, show curiosity, collaborate
2. Reference other agents by @name when you want their input
3. Always consider the user's needs and include them in decisions
4. Don't rush to action - explore the problem through dialogue first
5. Show your thinking process and reasoning
6. Build on what others have said in the conversation
7. Know when to take the lead and when to support others
8. ⭐ ASK PRACTICAL FOLLOW-UP QUESTIONS - timing, deadlines, preferences, constraints
9. ⭐ Don't assume details - always clarify specifics with the user
10. IMPORTANT: When offering options, only suggest what we can actually execute!

Remember: You're not just executing tasks, you're having a real conversation with real people (user + other agents). Ask the questions a real team member would ask!"""
    
    def _get_conversation_context(self) -> str:
        """Get current conversation context for the agent"""
        if not self.conversation_memory:
            return "No previous conversation context."
        
        recent_messages = self.conversation_memory[-5:]  # Last 5 messages
        context = "Recent conversation:\n"
        for msg in recent_messages:
            context += f"- {msg.get('sender', 'Unknown')}: {msg.get('content', '')[:100]}...\n"
        
        return context
    
    def add_to_memory(self, message: Dict[str, Any]):
        """Add a message to the agent's conversation memory"""
        self.conversation_memory.append({
            "timestamp": datetime.utcnow().isoformat(),
            "sender": message.get("sender"),
            "content": message.get("content"),
            "type": message.get("type")
        })
        
        # Keep memory within limits
        if len(self.conversation_memory) > settings.MAX_CONVERSATION_HISTORY:
            self.conversation_memory = self.conversation_memory[-settings.MAX_CONVERSATION_HISTORY:]
    
    def extract_questions(self, content: str) -> List[str]:
        """Extract questions from agent response"""
        # Simple regex to find questions
        questions = re.findall(r'[^.!?]*\?', content)
        return [q.strip() + '?' for q in questions if q.strip()]
    
    def generate_quick_options(self, content: str, context: Dict[str, Any]) -> List[QuickOption]:
        """Generate quick response options based on the agent's response"""
        
        # Analyze the content to determine question type
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['when', 'date', 'timeline', 'deadline']):
            return self.trigger_engine.get_valid_options_for_question("timeline", context)
        elif any(word in content_lower for word in ['tone', 'style', 'professional', 'casual']):
            return self.trigger_engine.get_valid_options_for_question("content_tone", context)
        elif any(word in content_lower for word in ['platform', 'social', 'twitter', 'linkedin']):
            return self.trigger_engine.get_valid_options_for_question("social_platforms", context)
        elif any(word in content_lower for word in ['metric', 'track', 'measure', 'analytics']):
            return self.trigger_engine.get_valid_options_for_question("success_metrics", context)
        
        return []
    
    def determine_interaction_mode(self, content: str) -> InteractionMode:
        """Determine the best interaction mode for the response"""
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['when', 'date', 'timeline']):
            return InteractionMode.QUICK_OPTIONS_WITH_CUSTOM
        elif any(word in content_lower for word in ['choose', 'select', 'prefer']) and '?' in content:
            return InteractionMode.MULTIPLE_CHOICE
        elif len(content) > 200 or any(word in content_lower for word in ['describe', 'explain', 'tell me about']):
            return InteractionMode.GUIDED_TEXT_INPUT
        else:
            return InteractionMode.ADAPTIVE
    
    async def respond(self, message_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a conversational response with questions and options"""
        
        try:
            # Add message to memory
            self.add_to_memory({
                "sender": "user",
                "content": message_content,
                "type": "user"
            })
            
            # Create AgentScope message
            from agentscope.message import Msg
            user_msg = Msg(name="user", content=message_content, role="user")
            
            # Generate response using AgentScope (this calls OpenAI)
            response_msg = self(user_msg)
            
            # Extract content from response
            response_content = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
            
            # Extract questions and generate options
            questions_asked = self.extract_questions(response_content)
            quick_options = self.generate_quick_options(response_content, context or {})
            interaction_mode = self.determine_interaction_mode(response_content)
            
            # Add response to memory
            self.add_to_memory({
                "sender": self.name,
                "content": response_content,
                "type": "agent"
            })
            
            return {
                "agent_name": self.name,
                "content": response_content,
                "questions_asked": questions_asked,
                "quick_options": quick_options,
                "interaction_mode": interaction_mode,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {e}")
            return {
                "agent_name": self.name,
                "content": f"I apologize, but I'm having trouble processing that right now. Could you try rephrasing your message?",
                "questions_asked": [],
                "quick_options": [],
                "interaction_mode": InteractionMode.ADAPTIVE,
                "timestamp": datetime.utcnow()
            } 