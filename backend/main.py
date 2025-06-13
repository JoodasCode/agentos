from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
import os

from app.core.config import settings
from app.core.logging import get_logger
from app.core.agentscope_config import initialize_agentscope, validate_openai_connection
from app.services.conversation_manager import ConversationManager
from app.api.routes import health, conversation, automation

logger = get_logger(__name__)

# Global conversation manager
conversation_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global conversation_manager
    
    # Startup
    logger.info("Starting Agent OS V2...")
    
    # Initialize AgentScope
    if initialize_agentscope():
        logger.info("AgentScope initialized successfully")
    else:
        logger.warning("AgentScope initialization failed - using fallback mode")
    
    # Validate OpenAI connection
    if validate_openai_connection():
        logger.info("OpenAI API connection validated")
    else:
        logger.warning("OpenAI API validation failed - check API key")
    
    # Initialize conversation manager
    conversation_manager = ConversationManager()
    logger.info("Conversation manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent OS V2...")

# Create FastAPI app
app = FastAPI(
    title="Agent OS V2 - Multi-Agent Platform",
    description="Conversational AI agents with Trigger.dev automation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - confirms this is OUR server, not AgentScope's"""
    return {
        "message": "🤖 Agent OS V2 - Multi-Agent Platform",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "Agent OS V2 Backend (NOT AgentScope)",
        "agents": ["Alex (Strategy)", "Dana (Creative)", "Riley (Data)", "Jamie (Operations)"],
        "features": [
            "Conversational AI agents",
            "Trigger.dev automation",
            "Real-time chat",
            "Product Hunt launch automation"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Agent OS V2",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }

@app.post("/chat/start")
async def start_conversation(data: Dict[str, Any]):
    """Start a new conversation with agents"""
    global conversation_manager
    
    message = data.get("message", "")
    user_id = data.get("user_id", "default_user")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    if not conversation_manager:
        raise HTTPException(status_code=500, detail="Conversation manager not initialized")
    
    try:
        # Generate new conversation ID
        conversation_id = f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Use real conversation manager
        response = await conversation_manager.handle_user_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return {
            "conversation_id": response.conversation_id,
            "agent_responses": [
                {
                    "agent_name": resp.agent_name,
                    "content": resp.content,
                    "timestamp": resp.timestamp.isoformat(),
                    "agent_type": "lead"
                }
                for resp in response.agent_responses
            ],
            "conversation_state": {
                "ready_for_action": response.conversation_state.ready_for_action,
                "lead_agent": response.conversation_state.lead_agent,
                "questions_asked": response.conversation_state.questions_asked,
                "answers_collected": response.conversation_state.answers_collected
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in start_conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/continue/{conversation_id}")
async def continue_conversation(conversation_id: str, data: Dict[str, Any]):
    """Continue an existing conversation"""
    global conversation_manager
    
    message = data.get("message", "")
    user_id = data.get("user_id", "default_user")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    if not conversation_manager:
        raise HTTPException(status_code=500, detail="Conversation manager not initialized")
    
    try:
        # Use real conversation manager
        response = await conversation_manager.handle_user_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return {
            "conversation_id": response.conversation_id,
            "agent_responses": [
                {
                    "agent_name": resp.agent_name,
                    "content": resp.content,
                    "timestamp": resp.timestamp.isoformat(),
                    "agent_type": "followup"
                }
                for resp in response.agent_responses
            ],
            "conversation_state": {
                "ready_for_action": response.conversation_state.ready_for_action,
                "lead_agent": response.conversation_state.lead_agent,
                "questions_asked": response.conversation_state.questions_asked,
                "answers_collected": response.conversation_state.answers_collected
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in continue_conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/automation/capabilities")
async def get_automation_capabilities():
    """Get available automation capabilities"""
    return {
        "success": True,
        "capabilities": {
            "product_hunt_launch": {
                "name": "Product Hunt Launch Automation",
                "description": "Complete Product Hunt launch workflow",
                "timeline_options": ["same-day", "1-week", "2-weeks", "1-month", "custom"],
                "status": "available"
            },
            "content_generation": {
                "name": "Marketing Content Generation",
                "description": "Generate marketing content across platforms",
                "tone_options": ["professional", "casual", "technical", "playful", "authoritative"],
                "status": "available"
            },
            "analytics_tracking": {
                "name": "Analytics & Performance Monitoring",
                "description": "Set up comprehensive analytics tracking",
                "metric_options": ["signups", "revenue", "traffic", "social_engagement"],
                "status": "available"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/automation/execute")
async def execute_automation(data: Dict[str, Any]):
    """Execute automation workflow"""
    job_type = data.get("job_type", "")
    parameters = data.get("parameters", {})
    
    if not job_type:
        raise HTTPException(status_code=400, detail="job_type is required")
    
    # Mock job execution (will be real Trigger.dev integration)
    job_id = f"job_{job_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "success": True,
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "estimated_completion": "2-5 minutes",
        "parameters": parameters,
        "timestamp": datetime.utcnow().isoformat()
    }

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(conversation.router, prefix="/api/v1", tags=["conversation"])
app.include_router(automation.router, prefix="/api/v1", tags=["automation"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 