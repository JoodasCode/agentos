from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

try:
    from app.core.config import get_settings
    from app.core.logging import setup_logging
    
    # Setup logging
    setup_logging()
    
    # Get settings
    settings = get_settings()
    
    print("✅ Core imports successful")
    
except ImportError as e:
    print(f"❌ Core import error: {e}")
    # Fallback for basic functionality
    settings = None

# Import routers individually with error handling
health = None
conversation = None
automation = None
api_keys = None
integrations = None

try:
    from app.api.routes import health
    print("✅ Health router imported")
except Exception as e:
    print(f"❌ Health router import failed: {e}")

try:
    from app.api.routes import conversation
    print("✅ Conversation router imported")
except Exception as e:
    print(f"❌ Conversation router import failed: {e}")

try:
    from app.api.routes import automation
    print("✅ Automation router imported")
except Exception as e:
    print(f"❌ Automation router import failed: {e}")

try:
    from app.api.routes import api_keys
    print("✅ API keys router imported")
except Exception as e:
    print(f"❌ API keys router import failed: {e}")

try:
    from app.api.routes import integrations
    print("✅ Integrations router imported")
except Exception as e:
    print(f"❌ Integrations router import failed: {e}")

# Create FastAPI app
app = FastAPI(
    title="Agent OS V2 - Conversational Multi-Agent System",
    description="A conversational AI system with personality-driven agents that engage in natural dialogue before coordinated action execution.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers (only if imports worked)
if health:
    try:
        print("🔧 Including health router...")
        app.include_router(health.router, prefix="/api/health", tags=["health"])
        print("✅ Health router included")
    except Exception as e:
        print(f"❌ Error including health router: {e}")

if conversation:
    try:
        print("🔧 Including conversation router...")
        app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
        print("✅ Conversation router included")
    except Exception as e:
        print(f"❌ Error including conversation router: {e}")

if automation:
    try:
        print("🔧 Including automation router...")
        app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
        print("✅ Automation router included")
    except Exception as e:
        print(f"❌ Error including automation router: {e}")

if api_keys:
    try:
        print("🔧 Including api_keys router...")
        app.include_router(api_keys.router, prefix="/api/keys", tags=["api-keys"])
        print("✅ API keys router included")
    except Exception as e:
        print(f"❌ Error including api_keys router: {e}")

if integrations:
    try:
        print("🔧 Including integrations router...")
        app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
        print("✅ Integrations router included")
    except Exception as e:
        print(f"❌ Error including integrations router: {e}")

print(f"🎯 Final router status: health={bool(health)}, conversation={bool(conversation)}, automation={bool(automation)}, api_keys={bool(api_keys)}, integrations={bool(integrations)}")

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Agent OS V2 - Conversational Multi-Agent System",
        "version": "2.0.0",
        "status": "running",
        "agents": ["Alex (Strategy)", "Dana (Creative)", "Riley (Data)", "Jamie (Operations)"],
        "docs": "/docs",
        "features": [
            "Natural conversation with AI agents",
            "Proactive questioning and follow-ups",
            "Trigger.dev automation integration",
            "Real-time WebSocket communication",
            "Product Hunt launch automation",
            "Secure API key management",
            "Agent-specific service integrations"
        ]
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 