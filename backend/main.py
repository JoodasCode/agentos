from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any
import os

# Create FastAPI app
app = FastAPI(
    title="Agent OS V2 - Multi-Agent Platform",
    description="Conversational AI agents with Trigger.dev automation",
    version="2.0.0"
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
    message = data.get("message", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Mock intelligent agent response (will be real AgentScope integration)
    agent_response = _get_mock_agent_response(message)
    
    return {
        "conversation_id": f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "agent_responses": [agent_response],
        "conversation_state": {
            "ready_for_action": False,
            "lead_agent": agent_response["agent_name"],
            "questions_asked": [],
            "answers_collected": {}
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat/continue/{conversation_id}")
async def continue_conversation(conversation_id: str, data: Dict[str, Any]):
    """Continue an existing conversation"""
    message = data.get("message", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Mock follow-up response
    agent_response = _get_mock_followup_response(message)
    
    return {
        "conversation_id": conversation_id,
        "agent_responses": [agent_response],
        "conversation_state": {
            "ready_for_action": _should_transition_to_action(message),
            "lead_agent": agent_response["agent_name"],
            "questions_asked": ["timeline", "preferences"],
            "answers_collected": {"last_message": message}
        },
        "timestamp": datetime.utcnow().isoformat()
    }

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

# Helper functions for mock responses
def _get_mock_agent_response(message: str) -> Dict[str, Any]:
    """Generate mock agent response based on message content"""
    message_lower = message.lower()
    
    # Determine lead agent based on content
    if any(word in message_lower for word in ["launch", "strategy", "plan", "timeline"]):
        agent = "Alex"
        content = f"Hi! I'm Alex, your strategic planning agent. I see you want to work on: '{message}'. Let me help you create a solid plan. When are you looking to launch this?"
    elif any(word in message_lower for word in ["content", "copy", "creative", "marketing"]):
        agent = "Dana"
        content = f"Hey there! I'm Dana, your creative content specialist. I love what you're thinking with: '{message}'. What's the tone and vibe you're going for?"
    elif any(word in message_lower for word in ["data", "analytics", "metrics", "track"]):
        agent = "Riley"
        content = f"Hello! I'm Riley, your data analysis expert. Interesting project: '{message}'. What key metrics should we be tracking for success?"
    else:
        agent = "Alex"
        content = f"Hi! I'm Alex from the Agent OS team. I'd love to help you with: '{message}'. Let me understand what you're looking to accomplish."
    
    return {
        "agent_name": agent,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_type": "lead"
    }

def _get_mock_followup_response(message: str) -> Dict[str, Any]:
    """Generate mock follow-up response"""
    return {
        "agent_name": "Alex",
        "content": f"Thanks for that info: '{message}'. Based on what you've shared, I can help set up the automation. Should we proceed with the workflow?",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_type": "followup"
    }

def _should_transition_to_action(message: str) -> bool:
    """Determine if conversation is ready for action"""
    action_keywords = ["yes", "go ahead", "let's do it", "start", "begin", "ready"]
    return any(keyword in message.lower() for keyword in action_keywords)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 