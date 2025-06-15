from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

try:
    from app.core.config import get_settings
    from app.api.routes import conversation, health, automation, api_keys, integrations
    from app.core.logging import setup_logging
    
    # Setup logging
    setup_logging()
    
    # Get settings
    settings = get_settings()
    
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for basic functionality
    settings = None

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
try:
    print("🔧 Including health router...")
    app.include_router(health.router, prefix="/api/health", tags=["health"])
    print("🔧 Including conversation router...")
    app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
    print("🔧 Including automation router...")
    app.include_router(automation.router, prefix="/api/automation", tags=["automation"])
    print("🔧 Including api_keys router...")
    app.include_router(api_keys.router, prefix="/api/keys", tags=["api-keys"])
    print("🔧 Including integrations router...")
    app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
    print("✅ All routers included successfully!")
except NameError as e:
    print(f"❌ NameError including routers: {e}")
except Exception as e:
    print(f"❌ Error including routers: {e}")
    import traceback
    traceback.print_exc()

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