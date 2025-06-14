"""Simple OpenAI-based agent implementation for Agent OS V2"""

import openai
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from app.core.logging import get_logger
from app.core.config import settings
from app.models.conversation import QuickOption, InteractionMode

logger = get_logger(__name__)

class OpenAIAgent:
    """Simple OpenAI-based agent for Agent OS V2"""
    
    def __init__(
        self, 
        name: str,
        role: str,
        personality: Dict[str, Any],
        conversation_style: str,
        question_patterns: List[str],
        expertise_areas: List[str]
    ):
        self.name = name
        self.role = role
        self.personality = personality
        self.conversation_style = conversation_style
        self.question_patterns = question_patterns
        self.expertise_areas = expertise_areas
        self.conversation_memory = []
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"Initialized OpenAI agent: {name} ({role})")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the OpenAI agent"""
        
        return f"""You are {self.name}, a {self.role} in Agent OS V2 - a multi-agent platform for Product Hunt launches and business automation.

PERSONALITY & ROLE:
{self.personality.get('description', '')}

EXPERTISE AREAS:
{', '.join(self.expertise_areas)}

CONVERSATION STYLE: {self.conversation_style}

CORE RESPONSIBILITIES:
{chr(10).join(f"- {pattern}" for pattern in self.question_patterns)}

AGENT OS V2 CONTEXT:
You work alongside other specialized agents:
- Alex (Strategic Planning): Product launch strategy, market analysis, competitive positioning
- Dana (Creative & Marketing): Content creation, social media, branding, copywriting  
- Riley (Data & Analytics): Metrics tracking, performance analysis, data insights
- Jamie (Operations): Automation setup, workflow management, technical implementation

CONVERSATION RULES:
1. Be genuinely conversational - ask follow-up questions, show curiosity
2. Reference other agents with @AgentName when you want their input
3. Always consider the user's specific needs and constraints
4. Don't rush to solutions - explore the problem through dialogue first
5. Show your reasoning and thought process
6. Build on what others have said in the conversation
7. Ask practical questions: timing, budget, deadlines, preferences
8. Be specific about what you can help with vs what others should handle
9. Stay in character but be helpful and collaborative

TRIGGER.DEV AUTOMATION AWARENESS:
You can suggest automations for:
- Product Hunt launch scheduling and posting
- Social media content generation and scheduling
- Email marketing campaigns
- Analytics tracking and reporting
- Notification systems and reminders

RESPONSE FORMAT:
- Be conversational and engaging
- Ask 1-2 specific follow-up questions
- Suggest concrete next steps when appropriate
- Mention other agents when their expertise is needed
- Keep responses focused but comprehensive (2-4 sentences typically)

Remember: You're part of a team helping users launch successful products. Be collaborative, insightful, and action-oriented while maintaining your unique personality and expertise."""
    
    def add_to_memory(self, message: Dict[str, Any]):
        """Add a message to the agent's conversation memory"""
        self.conversation_memory.append({
            "timestamp": datetime.utcnow().isoformat(),
            "sender": message.get("sender"),
            "content": message.get("content"),
            "type": message.get("type")
        })
        
        # Keep memory within limits
        if len(self.conversation_memory) > 20:  # Keep last 20 messages
            self.conversation_memory = self.conversation_memory[-20:]
    
    def extract_questions(self, content: str) -> List[str]:
        """Extract questions from agent response"""
        questions = re.findall(r'[^.!?]*\?', content)
        return [q.strip() + '?' for q in questions if q.strip()]
    
    def generate_quick_options(self, content: str, context: Dict[str, Any]) -> List[QuickOption]:
        """Generate quick response options based on the agent's response"""
        
        content_lower = content.lower()
        options = []
        
        # Timeline-related options
        if any(word in content_lower for word in ['when', 'date', 'timeline', 'deadline']):
            options.extend([
                QuickOption(id="timeline_asap", value="ASAP", label="As soon as possible", available=True),
                QuickOption(id="timeline_week", value="1 week", label="Within a week", available=True),
                QuickOption(id="timeline_month", value="1 month", label="Within a month", available=True),
                QuickOption(id="timeline_quarter", value="3 months", label="Within 3 months", available=True)
            ])
        
        # Budget-related options
        if any(word in content_lower for word in ['budget', 'cost', 'price', 'spend']):
            options.extend([
                QuickOption(id="budget_low", value="<$1000", label="Under $1,000", available=True),
                QuickOption(id="budget_mid", value="$1000-5000", label="$1,000 - $5,000", available=True),
                QuickOption(id="budget_high", value="$5000+", label="$5,000+", available=True)
            ])
        
        # Platform options
        if any(word in content_lower for word in ['platform', 'social', 'media', 'channel']):
            options.extend([
                QuickOption(id="platform_twitter", value="Twitter", label="Twitter/X", available=True),
                QuickOption(id="platform_linkedin", value="LinkedIn", label="LinkedIn", available=True),
                QuickOption(id="platform_facebook", value="Facebook", label="Facebook", available=True),
                QuickOption(id="platform_instagram", value="Instagram", label="Instagram", available=True)
            ])
        
        return options[:6]  # Limit to 6 options
    
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
        """Generate a conversational response using OpenAI"""
        
        try:
            # Add message to memory
            self.add_to_memory({
                "sender": "user",
                "content": message_content,
                "type": "user"
            })
            
            # Build conversation history for OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history
            for msg in self.conversation_memory[-10:]:  # Last 10 messages
                if msg.get("sender") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("sender") == self.name:
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the more affordable model
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            response_content = response.choices[0].message.content
            
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