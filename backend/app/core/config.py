from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agent OS V2"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-4o-mini"
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    
    # Trigger.dev
    TRIGGER_DEV_API_URL: str = "https://api.trigger.dev"
    TRIGGER_DEV_API_KEY: Optional[str] = None
    TRIGGER_DEV_PROJECT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Create global settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate that required settings are present"""
    required_for_production = [
        "OPENAI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY",
        "SECRET_KEY"
    ]
    
    if settings.ENVIRONMENT == "production":
        missing = [key for key in required_for_production if not getattr(settings, key)]
        if missing:
            raise ValueError(f"Missing required environment variables for production: {missing}")

# Validate on import
if settings.ENVIRONMENT == "production":
    validate_settings() 