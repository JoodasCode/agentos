from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class ConversationType(str, Enum):
    NEW_CONVERSATION = "new_conversation"
    CONTINUED_CONVERSATION = "continued_conversation"
    READY_FOR_ACTION = "ready_for_action"
    ACTION_TRIGGERED = "action_triggered"

class QuestionType(str, Enum):
    TIMELINE = "timeline"
    PREFERENCE = "preference"
    METRIC = "metric"
    OPEN_ENDED = "open_ended"
    SPECIFICATION = "specification"

class InteractionMode(str, Enum):
    QUICK_OPTIONS_WITH_CUSTOM = "quick_options_with_custom"
    MULTIPLE_CHOICE = "multiple_choice"
    GUIDED_TEXT_INPUT = "guided_text_input"
    ADAPTIVE = "adaptive"

class QuickOption(BaseModel):
    id: str
    value: str
    label: str
    description: Optional[str] = None
    available: bool = True

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    content: str
    sender: str  # user_id or agent_name
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    agent_name: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    questions_asked: List[str] = []
    quick_options: List[QuickOption] = []
    interaction_mode: Optional[InteractionMode] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationState(BaseModel):
    active: bool = True
    current_topic: Optional[str] = None
    lead_agent: Optional[str] = None
    pending_questions: List[str] = []
    answered_questions: List[str] = []
    missing_info: List[str] = []
    ready_for_action: bool = False
    conversation_summary: Optional[str] = None

class ConversationRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class QuickResponseRequest(BaseModel):
    option_id: str
    value: str
    conversation_id: str
    user_id: str
    context: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    type: ConversationType
    conversation_id: str
    agent_responses: List[AgentResponse]
    conversation_state: ConversationState
    quick_options: List[QuickOption] = []
    missing_info: List[str] = []
    suggested_actions: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Message]
    state: ConversationState
    created_at: datetime
    updated_at: datetime

class TriggerJobRequest(BaseModel):
    job_type: str
    parameters: Dict[str, Any]
    conversation_context: Dict[str, Any]
    user_id: str
    conversation_id: str

class TriggerJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None

# Import uuid after using it in Field
import uuid 