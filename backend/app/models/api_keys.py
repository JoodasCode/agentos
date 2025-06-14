from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class SupportedService(str, Enum):
    """Supported external services"""
    OPENAI = "openai"
    FAL_AI = "fal_ai"
    NOTION = "notion"
    SLACK = "slack"
    GITHUB = "github"
    GOOGLE_CALENDAR = "google_calendar"
    RESEND = "resend"
    SUPABASE = "supabase"
    DEEPGRAM = "deepgram"
    SENTRY = "sentry"

class ServiceCapability(BaseModel):
    """What an agent can do with a service"""
    service: SupportedService
    capabilities: List[str]
    required_scopes: List[str] = []
    setup_url: str
    instructions: str

class APIKeyRequest(BaseModel):
    """Request for API key from user"""
    agent_name: str
    service: SupportedService
    reason: str
    capabilities_unlocked: List[str]
    setup_instructions: str
    is_required: bool = True

class APIKeySubmission(BaseModel):
    """User submitting an API key"""
    service: SupportedService
    api_key: str = Field(..., min_length=1)
    session_id: str
    user_id: Optional[str] = None

class UserAPIKeys(BaseModel):
    """User's API keys for session"""
    session_id: str
    keys: Dict[SupportedService, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class AgentCapabilities(BaseModel):
    """What an agent can do based on available keys"""
    agent_name: str
    available_actions: List[str]
    missing_keys: List[SupportedService]
    setup_suggestions: List[APIKeyRequest]

# Service configurations
SERVICE_CONFIGS = {
    SupportedService.FAL_AI: ServiceCapability(
        service=SupportedService.FAL_AI,
        capabilities=["AI image generation", "Image-to-image transformation", "Style transfer"],
        setup_url="https://fal.ai/dashboard",
        instructions="1. Go to fal.ai/dashboard\n2. Sign up or log in\n3. Navigate to API Keys\n4. Create a new key\n5. Copy and paste it here"
    ),
    SupportedService.OPENAI: ServiceCapability(
        service=SupportedService.OPENAI,
        capabilities=["Text generation", "DALL-E image creation", "Code generation", "Analysis"],
        setup_url="https://platform.openai.com/api-keys",
        instructions="1. Go to platform.openai.com\n2. Sign in to your account\n3. Navigate to API Keys\n4. Create new secret key\n5. Copy and paste it here"
    ),
    SupportedService.NOTION: ServiceCapability(
        service=SupportedService.NOTION,
        capabilities=["Database operations", "Page creation", "Content management", "Project tracking"],
        required_scopes=["read", "write"],
        setup_url="https://www.notion.so/my-integrations",
        instructions="1. Go to notion.so/my-integrations\n2. Create new integration\n3. Give it a name and workspace\n4. Copy the Internal Integration Token\n5. Share relevant pages with your integration"
    ),
    SupportedService.SLACK: ServiceCapability(
        service=SupportedService.SLACK,
        capabilities=["Send messages", "Create channels", "File uploads", "Team notifications"],
        required_scopes=["chat:write", "channels:write", "files:write"],
        setup_url="https://api.slack.com/apps",
        instructions="1. Go to api.slack.com/apps\n2. Create New App\n3. Add Bot Token Scopes: chat:write, channels:write\n4. Install to workspace\n5. Copy Bot User OAuth Token"
    ),
    SupportedService.GITHUB: ServiceCapability(
        service=SupportedService.GITHUB,
        capabilities=["Repository analysis", "Issue management", "Commit tracking", "Project insights"],
        required_scopes=["repo", "read:org"],
        setup_url="https://github.com/settings/tokens",
        instructions="1. Go to github.com/settings/tokens\n2. Generate new token (classic)\n3. Select scopes: repo, read:org\n4. Set expiration as needed\n5. Copy and paste the token"
    ),
    SupportedService.GOOGLE_CALENDAR: ServiceCapability(
        service=SupportedService.GOOGLE_CALENDAR,
        capabilities=["Event creation", "Calendar management", "Meeting scheduling", "Availability checking"],
        required_scopes=["https://www.googleapis.com/auth/calendar"],
        setup_url="https://console.cloud.google.com/apis/credentials",
        instructions="1. Go to Google Cloud Console\n2. Create or select project\n3. Enable Calendar API\n4. Create credentials (API key or OAuth)\n5. Copy and paste the key"
    ),
    SupportedService.RESEND: ServiceCapability(
        service=SupportedService.RESEND,
        capabilities=["Email campaigns", "Transactional emails", "Email templates", "Analytics"],
        setup_url="https://resend.com/api-keys",
        instructions="1. Go to resend.com\n2. Sign up or log in\n3. Navigate to API Keys\n4. Create new API key\n5. Copy and paste it here"
    )
}

# Agent to service mappings
AGENT_SERVICE_MAPPING = {
    "Alex": [
        SupportedService.GITHUB,
        SupportedService.NOTION,
        SupportedService.SUPABASE
    ],
    "Dana": [
        SupportedService.FAL_AI,
        SupportedService.OPENAI,
        SupportedService.RESEND,
        SupportedService.SLACK
    ],
    "Riley": [
        SupportedService.SUPABASE,
        SupportedService.GITHUB,
        SupportedService.DEEPGRAM,
        SupportedService.SENTRY
    ],
    "Jamie": [
        SupportedService.SLACK,
        SupportedService.NOTION,
        SupportedService.RESEND
    ]
} 