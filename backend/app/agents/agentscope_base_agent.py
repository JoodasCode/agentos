"""AgentScope-based agent implementation for Agent OS V2"""

import agentscope
from agentscope.agents import DialogAgent
from agentscope.message import Msg
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from app.core.logging import get_logger
from app.core.config import settings
from app.models.conversation import QuickOption, InteractionMode

logger = get_logger(__name__)

class AgentScopeAgent(DialogAgent):
    """Base class for Agent OS V2 agents using AgentScope"""
    
    def __init__(
        self, 
        name: str,
        role: str,
        personality: Dict[str, Any],
        conversation_style: str,
        question_patterns: List[str],
        expertise_areas: List[str],
        **kwargs
    ):
        # Set name first before calling super().__init__
        self.name = name
        self.role = role
        self.personality = personality
        self.conversation_style = conversation_style
        self.question_patterns = question_patterns
        self.expertise_areas = expertise_areas
        self.conversation_memory = []
        self.active_topics = []
        self.unanswered_questions = []
        
        # Initialize AgentScope DialogAgent
        from app.core.agentscope_config import get_default_model_config
        
        super().__init__(
            name=name,
            sys_prompt=self._build_conversational_prompt(),
            model_config_name=get_default_model_config(),
            **kwargs
        )
        
        logger.info(f"✅ AgentScope agent '{name}' initialized successfully")
    
    def _build_conversational_prompt(self) -> str:
        """Build the system prompt for this agent"""
        
        prompt = f"""You are {self.name}, a {self.role} in the Agent OS V2 multi-agent system.

PERSONALITY & ROLE:
{self.personality.get('description', '')}

TRAITS: {', '.join(self.personality.get('traits', []))}
COMMUNICATION STYLE: {self.personality.get('communication_style', '')}

CONVERSATION APPROACH:
{self.conversation_style}

EXPERTISE AREAS:
{chr(10).join(f"- {area}" for area in self.expertise_areas)}

KEY QUESTIONS YOU ASK:
{chr(10).join(f"- {q}" for q in self.question_patterns)}

INSTRUCTIONS:
1. Stay in character as {self.name}
2. Ask relevant questions from your expertise area
3. Provide actionable insights and recommendations
4. Collaborate with other agents when mentioned (@AgentName)
5. Keep responses focused and valuable
6. Generate 2-3 quick response options when appropriate
7. Be conversational but professional

RESPONSE FORMAT:
- Provide your main response
- Ask 1-2 relevant follow-up questions
- Suggest quick response options when helpful
- Mention other agents (@AgentName) when their expertise is needed

Remember: You're part of a team helping users with Product Hunt launches and business strategy."""

        return prompt
    
    async def respond(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response to a user message"""
        
        try:
            # Create AgentScope message
            from agentscope.message import Msg
            
            # Generate response using AgentScope (this calls OpenAI)
            user_msg = Msg(name="user", content=message, role="user")
            response_msg = self(user_msg)
            
            # Extract response content
            response_content = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
            
            # Parse response for questions and quick options
            questions_asked = self._extract_questions(response_content)
            quick_options = self._generate_quick_options(response_content, message)
            
            # Store in conversation memory
            self.conversation_memory.append({
                "user_message": message,
                "agent_response": response_content,
                "timestamp": datetime.utcnow(),
                "context": context or {}
            })
            
            return {
                "agent_name": self.name,
                "content": response_content,
                "timestamp": datetime.utcnow(),
                "questions_asked": questions_asked,
                "quick_options": quick_options,
                "interaction_mode": InteractionMode.ADAPTIVE,
                "context": context or {}
            }
            
        except Exception as e:
            logger.error(f"Error in {self.name} response generation: {e}")
            
            # Fallback response
            return {
                "agent_name": self.name,
                "content": f"I apologize, but I'm having trouble processing your message right now. As your {self.role}, I'm here to help with {', '.join(self.expertise_areas[:2])}. Could you please try rephrasing your question?",
                "timestamp": datetime.utcnow(),
                "questions_asked": [],
                "quick_options": [],
                "interaction_mode": InteractionMode.ADAPTIVE,
                "context": context or {}
            }
    
    def _extract_questions(self, response: str) -> List[str]:
        """Extract questions from the agent's response"""
        
        # Simple regex to find questions
        questions = re.findall(r'[.!?]\s*([^.!?]*\?)', response)
        
        # Also look for questions at the end without punctuation before
        if response.strip().endswith('?'):
            last_sentence = response.strip().split('.')[-1].strip()
            if last_sentence not in questions:
                questions.append(last_sentence)
        
        return [q.strip() for q in questions if q.strip()]
    
    def _generate_quick_options(self, response: str, user_message: str) -> List[QuickOption]:
        """Generate quick response options based on the conversation"""
        
        options = []
        
        # Generate contextual quick options based on agent expertise
        if "timeline" in user_message.lower() or "when" in user_message.lower():
            options.extend([
                QuickOption(id="timeline_asap", text="ASAP", value="I need to launch as soon as possible"),
                QuickOption(id="timeline_1week", text="1 week", value="I'm planning to launch in about 1 week"),
                QuickOption(id="timeline_1month", text="1 month", value="I have about 1 month to prepare")
            ])
        
        if "budget" in user_message.lower() or "cost" in user_message.lower():
            options.extend([
                QuickOption(id="budget_low", text="Minimal budget", value="I'm working with a very limited budget"),
                QuickOption(id="budget_medium", text="Moderate budget", value="I have a moderate budget for this launch"),
                QuickOption(id="budget_flexible", text="Flexible budget", value="Budget is flexible based on ROI")
            ])
        
        # Agent-specific quick options
        options.extend(self._get_agent_specific_options(user_message))
        
        return options[:3]  # Limit to 3 options
    
    def _get_agent_specific_options(self, user_message: str) -> List[QuickOption]:
        """Override this in specific agents for custom quick options"""
        return []
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation with this agent"""
        
        return {
            "agent_name": self.name,
            "role": self.role,
            "total_interactions": len(self.conversation_memory),
            "active_topics": self.active_topics,
            "unanswered_questions": self.unanswered_questions,
            "last_interaction": self.conversation_memory[-1] if self.conversation_memory else None
        } 