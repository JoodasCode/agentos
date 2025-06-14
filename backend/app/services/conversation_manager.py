"""Conversation Manager for Agent OS V2 using PraisonAI"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import asyncio

from app.core.logging import get_logger
from app.core.config import settings
from app.models.conversation import (
    ConversationResponse, 
    AgentResponse, 
    ConversationState,
    MessageType,
    InteractionMode,
    ConversationType
)

# Import AgentScope agents
from app.agents.alex_agentscope import Alex
from app.agents.dana_agentscope import Dana
from app.agents.riley_agentscope import Riley
from app.agents.jamie_agentscope import Jamie

logger = get_logger(__name__)

class ConversationManager:
    """Manages multi-agent conversations using AgentScope"""
    
    def __init__(self):
        """Initialize the conversation manager with OpenAI agents"""
        
        logger.info("Initializing ConversationManager with OpenAI agents...")
        
        try:
            # Initialize agents
            self.alex = Alex()
            self.dana = Dana()
            self.riley = Riley()
            self.jamie = Jamie()
            
            # Agent registry
            self.agents = {
                "Alex": self.alex,
                "Dana": self.dana,
                "Riley": self.riley,
                "Jamie": self.jamie
            }
            
            # Conversation storage
            self.conversations: Dict[str, Dict[str, Any]] = {}
            
            logger.info("✅ ConversationManager initialized successfully with OpenAI agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ConversationManager: {e}")
            raise
    
    async def handle_user_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        context: Dict[str, Any] = None
    ) -> ConversationResponse:
        """Handle a user message and generate agent responses"""
        
        try:
            logger.info(f"Processing message for conversation {conversation_id}")
            
            # Initialize conversation if new
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "messages": [],
                    "lead_agent": None,
                    "active_agents": [],
                    "context": context or {}
                }
            
            # Add user message to conversation
            self.conversations[conversation_id]["messages"].append({
                "sender": "user",
                "content": message,
                "timestamp": datetime.utcnow(),
                "type": MessageType.USER
            })
            
            # Determine which agents should respond
            responding_agents = self._determine_responding_agents(message, conversation_id)
            
            logger.info(f"🤖 About to generate responses from agents: {responding_agents}")
            
            # Generate responses from agents
            agent_responses = []
            for agent_name in responding_agents:
                logger.info(f"🎯 Calling agent: {agent_name}")
                agent = self.agents[agent_name]
                
                # Get conversation context for this agent
                agent_context = self._build_agent_context(conversation_id, agent_name)
                
                # Generate response
                response = await agent.respond(message, agent_context)
                
                logger.info(f"✅ Got response from {agent_name}: {response['content'][:100]}...")
                
                # Create AgentResponse object
                agent_response = AgentResponse(
                    agent_name=response["agent_name"],
                    content=response["content"],
                    timestamp=response["timestamp"],
                    questions_asked=response.get("questions_asked", []),
                    quick_options=response.get("quick_options", []),
                    interaction_mode=response.get("interaction_mode", InteractionMode.ADAPTIVE)
                )
                
                agent_responses.append(agent_response)
                
                # Add agent response to conversation
                self.conversations[conversation_id]["messages"].append({
                    "sender": agent_name,
                    "content": response["content"],
                    "timestamp": response["timestamp"],
                    "type": MessageType.AGENT
                })
            
            # Update conversation state
            conversation_state = self._update_conversation_state(conversation_id, agent_responses)
            
            # Create and return response
            response = ConversationResponse(
                type=ConversationType.NEW_CONVERSATION if len(self.conversations[conversation_id]["messages"]) <= 2 else ConversationType.CONTINUED_CONVERSATION,
                conversation_id=conversation_id,
                agent_responses=agent_responses,
                conversation_state=conversation_state,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Generated response with {len(agent_responses)} agents for conversation {conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            
            # Return error response
            error_response = AgentResponse(
                agent_name="System",
                content="I apologize, but I'm having trouble processing your message right now. Please try again.",
                timestamp=datetime.utcnow(),
                questions_asked=[],
                quick_options=[],
                interaction_mode=InteractionMode.ADAPTIVE
            )
            
            return ConversationResponse(
                type=ConversationType.NEW_CONVERSATION,
                conversation_id=conversation_id,
                agent_responses=[error_response],
                conversation_state=ConversationState(
                    ready_for_action=False,
                    lead_agent="System",
                    pending_questions=[],
                    answered_questions=[]
                ),
                timestamp=datetime.utcnow()
            )
    
    def _determine_responding_agents(self, message: str, conversation_id: str) -> List[str]:
        """Determine which agents should respond to the message"""
        
        message_lower = message.lower()
        responding_agents = []
        
        logger.info(f"🔍 Determining agents for message: '{message}' (conversation: {conversation_id})")
        
        # Check for explicit agent requests first (highest priority)
        if any(phrase in message_lower for phrase in ['direct me to dana', 'talk to dana', 'connect me to dana', 'i want dana', '@dana']):
            responding_agents.append("Dana")
            logger.info(f"✅ Explicit Dana request detected")
        elif any(phrase in message_lower for phrase in ['direct me to riley', 'talk to riley', 'connect me to riley', 'i want riley', '@riley']):
            responding_agents.append("Riley")
            logger.info(f"✅ Explicit Riley request detected")
        elif any(phrase in message_lower for phrase in ['direct me to jamie', 'talk to jamie', 'connect me to jamie', 'i want jamie', '@jamie']):
            responding_agents.append("Jamie")
            logger.info(f"✅ Explicit Jamie request detected")
        elif any(phrase in message_lower for phrase in ['direct me to alex', 'talk to alex', 'connect me to alex', 'i want alex', '@alex']):
            responding_agents.append("Alex")
            logger.info(f"✅ Explicit Alex request detected")
        else:
            # Check if this is the first message in conversation
            conversation = self.conversations.get(conversation_id, {})
            message_count = len([msg for msg in conversation.get("messages", []) if msg.get("sender") == "user"])
            
            logger.info(f"📊 Message count: {message_count}, First message: {message_count <= 1}")
            
            if message_count <= 1:
                # First message - Alex (strategic) leads
                responding_agents.append("Alex")
                logger.info(f"🎯 First message - Alex leads")
            else:
                # Determine based on content keywords
                if any(word in message_lower for word in ['strategy', 'plan', 'goal', 'timeline', 'launch']):
                    responding_agents.append("Alex")
                    logger.info(f"🎯 Strategy keywords detected - Alex selected")
                
                if any(word in message_lower for word in ['content', 'creative', 'brand', 'marketing', 'social']):
                    responding_agents.append("Dana")
                    logger.info(f"🎯 Creative keywords detected - Dana selected")
                
                if any(word in message_lower for word in ['data', 'metrics', 'analytics', 'track', 'measure']):
                    responding_agents.append("Riley")
                    logger.info(f"🎯 Data keywords detected - Riley selected")
                
                if any(word in message_lower for word in ['automation', 'workflow', 'integrate', 'setup', 'technical']):
                    responding_agents.append("Jamie")
                    logger.info(f"🎯 Automation keywords detected - Jamie selected")
        
        # Ensure at least one agent responds
        if not responding_agents:
            responding_agents.append("Alex")  # Default to Alex
            logger.info(f"⚠️ No agents selected - defaulting to Alex")
        
        logger.info(f"🎯 Final selected agents: {responding_agents}")
        
        # Limit to 2 agents max for better UX (unless explicit request)
        if not any(phrase in message_lower for phrase in ['direct me to', 'talk to', 'connect me to', 'i want', '@']):
            return responding_agents[:2]
        else:
            return responding_agents[:1]  # Only the requested agent
    
    def _build_agent_context(self, conversation_id: str, agent_name: str) -> Dict[str, Any]:
        """Build context for an agent based on conversation history"""
        
        conversation = self.conversations.get(conversation_id, {})
        
        return {
            "conversation_id": conversation_id,
            "user_id": conversation.get("user_id"),
            "message_history": conversation.get("messages", [])[-10:],  # Last 10 messages
            "lead_agent": conversation.get("lead_agent"),
            "active_agents": conversation.get("active_agents", []),
            "conversation_context": conversation.get("context", {})
        }
    
    def _suggest_next_agents(self, response_content: str) -> List[str]:
        """Suggest which agents might be helpful next based on response content"""
        
        content_lower = response_content.lower()
        suggestions = []
        
        if any(word in content_lower for word in ['@dana', 'creative', 'content', 'brand']):
            suggestions.append("Dana")
        
        if any(word in content_lower for word in ['@riley', 'data', 'metrics', 'track']):
            suggestions.append("Riley")
        
        if any(word in content_lower for word in ['@jamie', 'automation', 'setup', 'workflow']):
            suggestions.append("Jamie")
        
        if any(word in content_lower for word in ['@alex', 'strategy', 'plan']):
            suggestions.append("Alex")
        
        return suggestions
    
    def _update_conversation_state(self, conversation_id: str, agent_responses: List[AgentResponse]) -> ConversationState:
        """Update and return the conversation state"""
        
        conversation = self.conversations[conversation_id]
        
        # Collect all questions asked
        all_questions = []
        for response in agent_responses:
            if hasattr(response, 'questions_asked') and response.questions_asked:
                all_questions.extend(response.questions_asked)
        
        # Determine lead agent (first responder or most confident)
        lead_agent = agent_responses[0].agent_name if agent_responses else "Alex"
        
        # Check if ready for action (simplified logic)
        ready_for_action = len(conversation.get("messages", [])) > 4  # After some back and forth
        
        # Update conversation tracking
        conversation["lead_agent"] = lead_agent
        conversation["active_agents"] = [resp.agent_name for resp in agent_responses]
        
        return ConversationState(
            active=True,
            lead_agent=lead_agent,
            pending_questions=all_questions,
            answered_questions=[],
            ready_for_action=ready_for_action
        )
    
    async def handle_quick_response(
        self, 
        option_id: str, 
        value: str, 
        user_id: str, 
        conversation_id: str
    ) -> ConversationResponse:
        """Handle a quick response option selection"""
        
        # Convert quick response to a message
        message = f"Selected: {value}"
        
        return await self.handle_user_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context={"quick_response": {"option_id": option_id, "value": value}}
        )
    
    async def get_conversation_history(self, conversation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        
        conversation = self.conversations.get(conversation_id)
        if not conversation or conversation.get("user_id") != user_id:
            return []
        
        return conversation.get("messages", [])
    
    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation status"""
        
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {"status": "not_found"}
        
        return {
            "status": "active",
            "created_at": conversation["created_at"].isoformat(),
            "message_count": len(conversation.get("messages", [])),
            "lead_agent": conversation.get("lead_agent"),
            "active_agents": conversation.get("active_agents", [])
        } 