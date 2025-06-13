"""AgentScope configuration and initialization"""

import agentscope
from agentscope.models import OpenAIWrapperBase
from app.core.config import settings
from app.core.logging import get_logger
import os

logger = get_logger(__name__)

def initialize_agentscope():
    """Initialize AgentScope with proper model configurations"""
    
    # Model configurations for different LLMs
    model_configs = [
        {
            "config_name": "gpt-4o-mini",
            "model_type": "openai_chat",
            "model_name": "gpt-4o-mini",
            "api_key": settings.OPENAI_API_KEY,
            "organization": None,
            "generate_args": {
                "temperature": 0.7,
                "max_tokens": 1000,
            }
        },
        {
            "config_name": "gpt-4o",
            "model_type": "openai_chat", 
            "model_name": "gpt-4o",
            "api_key": settings.OPENAI_API_KEY,
            "organization": None,
            "generate_args": {
                "temperature": 0.7,
                "max_tokens": 1500,
            }
        },
        {
            "config_name": "gpt-3.5-turbo",
            "model_type": "openai_chat",
            "model_name": "gpt-3.5-turbo",
            "api_key": settings.OPENAI_API_KEY,
            "organization": None,
            "generate_args": {
                "temperature": 0.7,
                "max_tokens": 1000,
            }
        }
    ]
    
    try:
        # Initialize AgentScope with model configurations
        agentscope.init(
            model_configs=model_configs,
            project="Agent OS V2",
            name="conversational_agents",
            save_code=False,
            save_api_invoke=True,
            use_monitor=True,
            logger_level="INFO"
        )
        
        logger.info("AgentScope initialized successfully with OpenAI models")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize AgentScope: {e}")
        return False

def get_default_model_config():
    """Get the default model configuration name"""
    return getattr(settings, 'DEFAULT_MODEL', 'gpt-4o-mini')

def validate_openai_connection():
    """Validate that OpenAI API key is working"""
    
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not found in settings")
        return False
    
    try:
        # Test OpenAI connection with a simple call
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Make a simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        logger.info("OpenAI API connection validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API validation failed: {e}")
        return False 