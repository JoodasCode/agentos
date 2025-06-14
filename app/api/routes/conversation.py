from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from app.core.logging import get_logger
from app.models.conversation import ConversationRequest, ConversationResponse, MessageType, QuickResponseRequest

router = APIRouter()
logger = get_logger(__name__)

# Conversation manager will be injected from main.py
conversation_manager = None

def set_conversation_manager(manager):
    """Set the conversation manager instance"""
    global conversation_manager
    conversation_manager = manager

class ChatMessage(BaseModel):
    content: str
    user_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class QuickResponse(BaseModel):
    option_id: str
    value: str
    conversation_id: str
    user_id: str

@router.post("/start")
async def start_conversation(message_data: Dict[str, Any]):
    """Start a new conversation"""
    
    message = message_data.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Mock response for now
    return {
        "conversation_id": "conv_123",
        "agent_responses": [
            {
                "agent_name": "Alex",
                "content": f"Hi! I'm Alex, your strategic planning agent. I'd love to help you with: '{message}'. Let me understand what you're looking to accomplish.",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "conversation_state": {
            "ready_for_action": False,
            "lead_agent": "Alex",
            "questions_asked": [],
            "answers_collected": {}
        }
    }

@router.post("/continue/{conversation_id}")
async def continue_conversation(conversation_id: str, message_data: Dict[str, Any]):
    """Continue an existing conversation"""
    
    message = message_data.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Mock response for now
    return {
        "conversation_id": conversation_id,
        "agent_responses": [
            {
                "agent_name": "Alex",
                "content": f"Thanks for that information: '{message}'. Let me help you move forward with this.",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "conversation_state": {
            "ready_for_action": False,
            "lead_agent": "Alex",
            "questions_asked": ["timeline"],
            "answers_collected": {"last_message": message}
        }
    }

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    
    return {
        "conversation_id": conversation_id,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "message_count": 2,
        "lead_agent": "Alex"
    }

@router.post("/message", response_model=ConversationResponse)
async def send_message(request: ConversationRequest):
    """Send a message to the conversational agents"""
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info("Received conversation request", 
                   conversation_id=conversation_id,
                   user_id=request.user_id,
                   message_length=len(request.message))
        
        # Process message through conversation manager
        response = await conversation_manager.handle_user_message(
            message=request.message,
            user_id=request.user_id,
            conversation_id=conversation_id,
            context=request.context or {}
        )
        
        logger.info("Generated conversation response", 
                   conversation_id=conversation_id,
                   agent_count=len(response.agent_responses))
        
        return response
        
    except Exception as e:
        logger.error("Error processing conversation request", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.post("/quick-response", response_model=ConversationResponse)
async def handle_quick_response(request: QuickResponseRequest):
    """Handle quick response button clicks"""
    
    try:
        logger.info("Received quick response", 
                   conversation_id=request.conversation_id,
                   option_id=request.option_id)
        
        response = await conversation_manager.handle_quick_response(
            option_id=request.option_id,
            value=request.value,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        return response
        
    except Exception as e:
        logger.error("Error processing quick response", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing quick response: {str(e)}")

@router.get("/history/{conversation_id}")
async def get_conversation_history(conversation_id: str, user_id: str):
    """Get conversation history"""
    
    try:
        history = await conversation_manager.get_conversation_history(conversation_id, user_id)
        return {"conversation_id": conversation_id, "messages": history}
        
    except Exception as e:
        logger.error("Error getting conversation history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

@router.get("/status/{conversation_id}")
async def get_conversation_status(conversation_id: str):
    """Get conversation status"""
    
    try:
        status = await conversation_manager.get_conversation_status(conversation_id)
        return {"conversation_id": conversation_id, "status": status}
        
    except Exception as e:
        logger.error("Error getting conversation status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

# WebSocket endpoint for real-time conversation
@router.websocket("/ws/{conversation_id}")
async def websocket_conversation(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time conversation"""
    
    await websocket.accept()
    logger.info("WebSocket connection established", conversation_id=conversation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message
            response = await conversation_manager.handle_user_message(
                message=data.get("message", ""),
                user_id=data.get("user_id", "anonymous"),
                conversation_id=conversation_id,
                context=data.get("context", {})
            )
            
            # Send response back to client
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed", conversation_id=conversation_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), conversation_id=conversation_id)
        await websocket.close() 