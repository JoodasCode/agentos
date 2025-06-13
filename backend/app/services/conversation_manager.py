import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.agents.alex import Alex
from app.agents.dana import Dana
from app.agents.riley import Riley
from app.agents.jamie import Jamie
from app.models.conversation import (
    ConversationResponse, ConversationState, AgentResponse, 
    ConversationType, QuickOption, Message, MessageType
)
from app.core.logging import get_logger
from app.services.action_bridge import ActionBridge
from agentscope.message import Msg

logger = get_logger(__name__)

class ConversationManager:
    """Manages natural conversation flow with proactive questioning"""
    
    def __init__(self):
        # Initialize agents
        self.alex = Alex()
        self.dana = Dana()
        self.riley = Riley()
        self.jamie = Jamie()
        self.agents = [self.alex, self.dana, self.riley, self.jamie]
        
        # Initialize action bridge for Trigger.dev integration
        self.action_bridge = ActionBridge()
        
        # Conversation storage (in production, this would be in database)
        self.conversations: Dict[str, Dict] = {}
        
        logger.info("ConversationManager initialized with 4 agents and action bridge")
    
    async def handle_user_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str, 
        context: Dict[str, Any] = None
    ) -> ConversationResponse:
        """Process user message and orchestrate agent responses with intelligent questioning"""
        
        try:
            logger.info("Processing user message", 
                       conversation_id=conversation_id, 
                       user_id=user_id,
                       message_length=len(message))
            
            # Get or create conversation state
            conversation_state = self._get_or_create_conversation(conversation_id, user_id)
            
            # Add user message to conversation
            user_msg = Message(
                type=MessageType.USER,
                content=message,
                sender=user_id
            )
            conversation_state["messages"].append(user_msg.dict())
            
            # Determine conversation flow
            flow_decision = await self._analyze_conversation_flow(message, conversation_state)
            
            if flow_decision["type"] == "new_conversation":
                return await self._start_new_conversation(message, conversation_state, context or {})
            elif flow_decision["type"] == "continue_conversation":
                return await self._continue_conversation(message, conversation_state, context or {})
            elif flow_decision["type"] == "ready_for_action":
                return await self._transition_to_action(message, conversation_state, context or {})
            
        except Exception as e:
            logger.error("Error handling user message", 
                        error=str(e), 
                        conversation_id=conversation_id)
            
            # Return error response
            return ConversationResponse(
                type=ConversationType.CONTINUED_CONVERSATION,
                conversation_id=conversation_id,
                agent_responses=[
                    AgentResponse(
                        agent_name="System",
                        content="I apologize, but I'm having trouble processing your message right now. Could you try again?",
                        timestamp=datetime.utcnow()
                    )
                ],
                conversation_state=ConversationState()
            )
    
    def _get_or_create_conversation(self, conversation_id: str, user_id: str) -> Dict:
        """Get existing conversation or create new one"""
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "messages": [],
                "state": {
                    "active": True,
                    "current_topic": None,
                    "lead_agent": None,
                    "pending_questions": [],
                    "answered_questions": [],
                    "missing_info": [],
                    "ready_for_action": False,
                    "conversation_summary": None
                }
            }
            logger.info("Created new conversation", conversation_id=conversation_id)
        else:
            self.conversations[conversation_id]["updated_at"] = datetime.utcnow()
        
        return self.conversations[conversation_id]
    
    async def _analyze_conversation_flow(self, message: str, conversation_state: Dict) -> Dict:
        """Analyze message and determine conversation flow"""
        
        message_count = len(conversation_state["messages"])
        
        # First message = new conversation
        if message_count <= 1:
            return {"type": "new_conversation", "reason": "first_message"}
        
        # Check if user wants to proceed with action
        message_lower = message.lower()
        action_keywords = ["let's do it", "sounds good", "go ahead", "start", "begin", "ready", "execute"]
        if any(keyword in message_lower for keyword in action_keywords):
            return {"type": "ready_for_action", "reason": "user_ready"}
        
        # Continue conversation by default
        return {"type": "continue_conversation", "reason": "need_more_info"}
    
    async def _start_new_conversation(self, message: str, conversation_state: Dict, context: Dict) -> ConversationResponse:
        """Start a new conversation with appropriate lead agent"""
        
        # Determine lead agent based on message content
        lead_agent = self._select_lead_agent(message)
        conversation_state["state"]["lead_agent"] = lead_agent.name
        
        logger.info("Starting new conversation", 
                   lead_agent=lead_agent.name,
                   conversation_id=conversation_state["id"])
        
        # Generate lead agent response using real AgentScope
        try:
            agent_response_data = await lead_agent.respond(message, context)
            lead_response = AgentResponse(
                agent_name=agent_response_data["agent_name"],
                content=agent_response_data["content"],
                timestamp=agent_response_data["timestamp"]
            )
        except Exception as e:
            logger.error(f"Error getting response from {lead_agent.name}: {e}")
            lead_response = AgentResponse(
                agent_name=lead_agent.name,
                content=f"Hi! I'm {lead_agent.name}. I'd love to help you with this. Let me understand what you're looking to accomplish.",
                timestamp=datetime.utcnow()
            )
        
        # Update conversation state
        state = ConversationState(**conversation_state["state"])
        
        return ConversationResponse(
            type=ConversationType.NEW_CONVERSATION,
            conversation_id=conversation_state["id"],
            agent_responses=[lead_response],
            conversation_state=state
        )
    
    async def _continue_conversation(self, message: str, conversation_state: Dict, context: Dict) -> ConversationResponse:
        """Continue ongoing conversation with intelligent follow-up questions"""
        
        # Determine which agents should respond
        responding_agents = []
        
        # Check if any agent should contribute based on message content
        for agent in self.agents:
            if hasattr(agent, 'should_contribute') and agent.should_contribute({"last_message": message}):
                responding_agents.append(agent)
        
        # If no specific agents triggered, have the lead agent respond
        if not responding_agents:
            lead_agent_name = conversation_state["state"].get("lead_agent", "Alex")
            lead_agent = next((agent for agent in self.agents if agent.name == lead_agent_name), self.alex)
            responding_agents = [lead_agent]
        
        # Generate responses using real AgentScope
        responses = []
        for agent in responding_agents:
            try:
                agent_response_data = await agent.respond(message, context)
                response = AgentResponse(
                    agent_name=agent_response_data["agent_name"],
                    content=agent_response_data["content"],
                    timestamp=agent_response_data["timestamp"]
                )
                responses.append(response)
            except Exception as e:
                logger.error(f"Error getting response from {agent.name}: {e}")
                # Fallback response
                response = AgentResponse(
                    agent_name=agent.name,
                    content=f"Thanks for that information! Let me help you move forward with this.",
                    timestamp=datetime.utcnow()
                )
                responses.append(response)
        
        # Update conversation state
        state = ConversationState(**conversation_state["state"])
        
        return ConversationResponse(
            type=ConversationType.CONTINUED_CONVERSATION,
            conversation_id=conversation_state["id"],
            agent_responses=responses,
            conversation_state=state
        )
    
    async def _transition_to_action(self, message: str, conversation_state: Dict, context: Dict) -> ConversationResponse:
        """Transition from conversation to coordinated action"""
        
        logger.info("Transitioning to action", conversation_id=conversation_state["id"])
        
        try:
            # Convert conversation to action plan
            action_plan = await self.action_bridge.convert_conversation_to_actions(conversation_state)
            
            if action_plan["ready_to_execute"]:
                # Execute the action plan
                execution_results = await self.action_bridge.execute_action_plan(action_plan)
                
                # Create success response
                alex_response = AgentResponse(
                    agent_name="Alex",
                    content=f"""Perfect! I've analyzed our conversation and triggered the automation workflows.

Here's what's now running:
{self._format_execution_summary(execution_results)}

You'll receive updates as each step completes. I'm monitoring everything to ensure smooth execution!""",
                    timestamp=datetime.utcnow()
                )
                
                # Update conversation state
                conversation_state["state"]["ready_for_action"] = True
                conversation_state["state"]["execution_results"] = execution_results
                
            else:
                # Need more information
                missing_info = []
                for job_type, validation in action_plan["validation_results"].items():
                    if not validation["valid"]:
                        missing_info.extend(validation.get("suggestions", []))
                
                alex_response = AgentResponse(
                    agent_name="Alex",
                    content=f"""I'd love to get this started, but I need a bit more information first:

{chr(10).join(f"• {info}" for info in missing_info[:3])}

Once we have these details, I can trigger the full automation sequence!""",
                    timestamp=datetime.utcnow()
                )
        
        except Exception as e:
            logger.error("Error in action transition", error=str(e))
            alex_response = AgentResponse(
                agent_name="Alex",
                content="I'm having trouble setting up the automation right now. Let me gather a bit more information and we'll try again.",
                timestamp=datetime.utcnow()
            )
        
        state = ConversationState(**conversation_state["state"])
        
        return ConversationResponse(
            type=ConversationType.READY_FOR_ACTION,
            conversation_id=conversation_state["id"],
            agent_responses=[alex_response],
            conversation_state=state
        )
    
    def _select_lead_agent(self, message: str):
        """Select the most appropriate lead agent based on message content"""
        
        message_lower = message.lower()
        
        # Dana leads for content/creative topics (check first - more specific)
        if any(word in message_lower for word in ["content", "copy", "creative", "brand", "message", "marketing"]):
            return self.dana
        
        # Riley leads for data/analytics topics (check second - more specific)
        elif any(word in message_lower for word in ["data", "analytics", "metrics", "track", "measure", "performance"]):
            return self.riley
        
        # Jamie leads for operations/scheduling topics (check third - more specific)
        elif any(word in message_lower for word in ["schedule", "workflow", "process", "automation", "operations"]):
            return self.jamie
        
        # Alex leads for strategy/planning topics (broader terms, check last)
        elif any(word in message_lower for word in ["plan", "strategy", "launch", "project", "goal", "timeline"]):
            return self.alex
        
        # Default to Alex for general inquiries
        else:
            return self.alex
    
    def _format_execution_summary(self, execution_results: Dict[str, Any]) -> str:
        """Format execution results into a readable summary"""
        
        if not execution_results.get("success", False):
            return "• Automation setup encountered an issue - investigating now"
        
        summary_lines = []
        for job_type, result in execution_results.get("execution_results", {}).items():
            if result.get("success", False):
                job_name = job_type.replace("_", " ").title()
                summary_lines.append(f"• {job_name} - Job ID: {result.get('job_id', 'N/A')}")
        
        if not summary_lines:
            summary_lines = ["• Automation workflows are being prepared"]
        
        return "\n".join(summary_lines)
    
    async def handle_quick_response(
        self, 
        option_id: str, 
        value: str, 
        user_id: str, 
        conversation_id: str
    ) -> ConversationResponse:
        """Handle quick response button clicks"""
        
        # Convert quick response to a regular message
        message = f"Selected: {value}"
        
        return await self.handle_user_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context={"quick_response": True, "option_id": option_id, "value": value}
        )
    
    async def get_conversation_history(self, conversation_id: str, user_id: str) -> List[Dict]:
        """Get conversation history"""
        
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]["messages"]
        return []
    
    async def get_conversation_status(self, conversation_id: str) -> Dict:
        """Get current conversation status"""
        
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]["state"]
        
        return {
            "active": False,
            "error": "Conversation not found"
        } 