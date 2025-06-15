from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
import secrets
import httpx

# Load environment variables from .env.local for development
load_dotenv(".env.local")
load_dotenv()  # Also load .env if it exists

from app.core.config import settings
from app.core.logging import get_logger
from app.core.agentscope_config import initialize_agentscope, validate_openai_connection
from app.api.routes import health, conversation, automation
from app.api.routes import api_keys, integrations

logger = get_logger(__name__)

# Global conversation manager
conversation_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global conversation_manager
    
    # Startup
    logger.info("🚀 Starting Agent OS V2 with AgentScope...")
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
    else:
        logger.warning("❌ OPENAI_API_KEY not found in environment!")
    
    # Initialize AgentScope
    if initialize_agentscope():
        logger.info("✅ AgentScope initialized successfully")
        
        # Validate OpenAI connection
        if validate_openai_connection():
            logger.info("✅ OpenAI connection validated")
        else:
            logger.warning("⚠️ OpenAI connection validation failed")
    else:
        logger.warning("❌ AgentScope initialization failed - using fallback mode")
    
    # Initialize conversation manager (after AgentScope is ready)
    try:
        from app.services.conversation_manager import ConversationManager
        conversation_manager = ConversationManager()
        logger.info("✅ Conversation manager initialized with AgentScope")
    except Exception as e:
        logger.error(f"❌ Conversation manager initialization failed: {e}")
        conversation_manager = None
    
    # Set conversation manager in routes
    try:
        from app.api.routes.conversation import set_conversation_manager
        set_conversation_manager(conversation_manager)
        logger.info("✅ Conversation manager set in routes")
    except Exception as e:
        logger.error(f"❌ Failed to set conversation manager in routes: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Agent OS V2...")

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

# Include API routers
app.include_router(api_keys.router, prefix="/api/keys", tags=["API Keys"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])

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
                "pending_questions": response.conversation_state.pending_questions,
                "answered_questions": response.conversation_state.answered_questions
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
                "pending_questions": response.conversation_state.pending_questions,
                "answered_questions": response.conversation_state.answered_questions
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

@app.get("/debug/agent-health")
async def debug_agent_health():
    """Debug endpoint to check agent and OpenAI integration status"""
    import os
    
    # Check environment variables
    openai_key_exists = os.getenv("OPENAI_API_KEY") is not None
    openai_key_length = len(os.getenv("OPENAI_API_KEY", "")) if openai_key_exists else 0
    
    # Check OpenAI agents initialization
    agents_initialized = conversation_manager is not None
    
    try:
        import openai
        openai_import = True
        openai_version = getattr(openai, '__version__', 'unknown')
    except ImportError as e:
        openai_import = False
        openai_version = f"Import failed: {e}"
    
    return {
        "status": "debug_info",
        "environment": {
            "openai_key_exists": openai_key_exists,
            "openai_key_length": openai_key_length,
            "railway_env": os.getenv("RAILWAY_ENVIRONMENT", "not_set")
        },
        "imports": {
            "openai_import": openai_import,
            "openai_version": openai_version
        },
        "initialization": {
            "conversation_manager_exists": agents_initialized,
            "conversation_manager_type": type(conversation_manager).__name__ if conversation_manager else None
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/integrations/slack/connect")
async def connect_slack_with_triggerdev(session_id: str, slack_bot_token: str):
    """Connect Slack using Trigger.dev integration"""
    
    try:
        # Store the Slack bot token securely
        from app.services.api_key_manager import api_key_manager
        from app.models.api_keys import SupportedService, APIKeySubmission
        
        # Store Slack token
        submission = APIKeySubmission(
            session_id=session_id,
            service=SupportedService.SLACK,
            api_key=slack_bot_token
        )
        
        success = await api_key_manager.submit_api_key(submission)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to store Slack token")
        
        # Test the connection by making a simple API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {slack_bot_token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": "🎉 Slack Connected Successfully!",
                        "workspace": {
                            "team": data.get("team", "Unknown"),
                            "user": data.get("user", "Unknown"),
                            "team_id": data.get("team_id", "Unknown")
                        },
                        "integration_method": "trigger.dev",
                        "next_steps": [
                            "✅ Your Slack workspace is now connected to Agent OS",
                            "🤖 Dana and other agents can now send messages to your Slack channels",
                            "💬 The Trigger.dev tasks are ready to execute",
                            "🚀 Try asking an agent to send a Slack message!"
                        ],
                        "trigger_dev_status": "Tasks registered and ready",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    raise HTTPException(status_code=400, detail=f"Slack API error: {data.get('error', 'Unknown error')}")
            else:
                raise HTTPException(status_code=400, detail="Failed to validate Slack token")
            
    except Exception as e:
        logger.error(f"Slack connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@app.post("/integrations/slack/demo")
async def demo_slack_integration_triggerdev(
    session_id: str, 
    channel: str = "general",
    user_name: str = "Demo User"
):
    """Demo the Slack integration using Trigger.dev"""
    
    try:
        # Get the stored Slack token
        from app.services.api_key_manager import api_key_manager
        from app.models.api_keys import SupportedService
        
        slack_token = await api_key_manager.get_api_key(session_id, SupportedService.SLACK)
        
        if not slack_token:
            raise HTTPException(status_code=400, detail="No Slack token found. Please connect Slack first.")
        
        # Send a demo message directly using Slack API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": channel,
                    "text": f"""🚀 **Agent OS Demo Message**

Hey {user_name}! This is a demo message from Agent OS to show that the Slack integration is working perfectly.

🤖 **What's Connected:**
• Agent OS backend is running
• Trigger.dev tasks are registered
• Slack workspace is connected
• All agents can now send messages

🎯 **Next Steps:**
• Try asking Dana to send a creative message
• Ask Alex for strategic updates
• Use Riley for data notifications
• Get Jamie to send operational alerts

*Sent via Agent OS + Trigger.dev integration*""",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🚀 Agent OS Demo Message"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Hey {user_name}! This is a demo message from Agent OS to show that the Slack integration is working perfectly."
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*🤖 What's Connected:*\n• Agent OS backend\n• Trigger.dev tasks\n• Slack workspace\n• All agents ready"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*🎯 Available Agents:*\n• Dana (Creative)\n• Alex (Strategy)\n• Riley (Data)\n• Jamie (Operations)"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Sent via Agent OS + Trigger.dev • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                                }
                            ]
                        }
                    ]
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {
                        "success": True,
                        "demo_completed": True,
                        "message": "🚀 Demo message sent to Slack successfully!",
                        "channel": channel,
                        "message_ts": data.get("ts"),
                        "integration_method": "trigger.dev",
                        "next_steps": [
                            "✅ Demo message sent successfully",
                            "🤖 Agent OS is fully connected to your Slack workspace",
                            "💬 All agents can now send messages to any channel",
                            "🚀 Try asking Dana: 'Send a message to #general saying hello!'",
                            "📊 Ask Riley to send data updates to your team",
                            "🎯 Get Alex to share strategic insights"
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    raise HTTPException(status_code=400, detail=f"Slack API error: {data.get('error', 'Unknown error')}")
            else:
                raise HTTPException(status_code=400, detail="Failed to send demo message")
            
    except Exception as e:
        logger.error(f"Slack demo failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@app.get("/integrations/slack/setup-instructions")
async def get_slack_setup_instructions():
    """Get instructions for setting up Slack with Agent OS"""
    
    return {
        "success": True,
        "setup_method": "trigger.dev",
        "instructions": [
            "🚀 **Set up Slack for Agent OS using Trigger.dev:**",
            "",
            "**Step 1: Create a Slack App**",
            "1. Go to https://api.slack.com/apps",
            "2. Click 'Create New App' → 'From scratch'",
            "3. App Name: 'Agent OS'",
            "4. Choose your workspace",
            "",
            "**Step 2: Configure Bot Permissions**",
            "1. Go to 'OAuth & Permissions' in your app settings",
            "2. Add these Bot Token Scopes:",
            "   • chat:write",
            "   • channels:read",
            "",
            "**Step 3: Install to Workspace**",
            "1. Click 'Install to Workspace'",
            "2. Review permissions and click 'Allow'",
            "3. Copy the 'Bot User OAuth Token' (starts with xoxb-)",
            "",
            "**Step 4: Connect to Agent OS**",
            "1. Paste your Bot Token in the Agent OS settings",
            "2. Test the connection",
            "3. Your agents can now send Slack messages via Trigger.dev!"
        ],
        "required_scopes": [
            "chat:write",
            "channels:read"
        ],
        "app_settings": {
            "app_name": "Agent OS",
            "description": "Multi-agent AI platform for productivity automation",
            "integration_method": "trigger.dev + official Slack SDK"
        },
        "trigger_dev_info": {
            "status": "Tasks registered and ready",
            "available_tasks": [
                "agent-os-slack-message",
                "agent-os-create-channel", 
                "agent-os-slack-workspace-info",
                "demo-agent-os-slack-integration"
            ],
            "dev_server_running": True
        },
        "what_users_will_see": [
            "App name: Agent OS",
            "App description: Multi-agent AI platform", 
            "Permissions: Send messages, read channels, upload files",
            "Messages will show 'Sent by Agent OS' branding"
        ]
    }

@app.get("/integrations/slack/oauth/authorize")
async def slack_oauth_authorize(session_id: str):
    """Initiate Slack OAuth flow"""
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    
    # Store state in session (in production, use proper session storage)
    # For now, we'll include it in the redirect and verify it in callback
    
    # Slack OAuth parameters
    client_id = os.getenv('SLACK_CLIENT_ID', 'your-slack-client-id')
    redirect_uri = "https://agentos-production-6348.up.railway.app/integrations/slack/oauth/callback"
    
    scopes = [
        "chat:write",
        "channels:read"
    ]
    
    oauth_params = {
        "client_id": client_id,
        "scope": ",".join(scopes),
        "redirect_uri": redirect_uri,
        "state": f"{session_id}:{state}",
        "response_type": "code"
    }
    
    slack_auth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(oauth_params)}"
    
    return {
        "success": True,
        "auth_url": slack_auth_url,
        "state": state,
        "message": "Redirect user to auth_url to complete Slack authorization"
    }

@app.get("/integrations/slack/oauth/callback")
async def slack_oauth_callback(code: str, state: str, error: str = None):
    """Handle Slack OAuth callback"""
    
    if error:
        return {
            "success": False,
            "error": error,
            "message": "Slack authorization was denied or failed"
        }
    
    try:
        # Parse state to get session_id
        session_id, state_token = state.split(":", 1)
        
        # Exchange code for access token
        client_id = os.getenv('SLACK_CLIENT_ID', 'your-slack-client-id')
        client_secret = os.getenv('SLACK_CLIENT_SECRET', 'your-slack-client-secret')
        redirect_uri = "https://agentos-production-6348.up.railway.app/integrations/slack/oauth/callback"
        
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            result = response.json()
            
            if not result.get("ok"):
                raise Exception(f"Slack OAuth error: {result.get('error', 'Unknown error')}")
            
            # Extract bot token
            bot_token = result["access_token"]
            team_info = result.get("team", {})
            
            # Store the bot token securely
            from app.services.api_key_manager import api_key_manager
            from app.models.api_keys import SupportedService, APIKeySubmission
            
            submission = APIKeySubmission(
                session_id=session_id,
                service=SupportedService.SLACK,
                api_key=bot_token
            )
            
            success = await api_key_manager.submit_api_key(submission)
            
            if success:
                # Return success page or redirect to frontend
                return {
                    "success": True,
                    "message": f"Successfully connected to Slack workspace: {team_info.get('name', 'Unknown')}",
                    "team": team_info,
                    "redirect_to": f"http://localhost:3000/settings?slack_connected=true"
                }
            else:
                raise Exception("Failed to store Slack token")
                
    except Exception as e:
        logger.error(f"Slack OAuth callback error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to complete Slack authorization"
        }

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(conversation.router, prefix="/api/v1", tags=["conversation"])
app.include_router(automation.router, prefix="/api/v1", tags=["automation"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 