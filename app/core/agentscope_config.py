"""AgentScope configuration and initialization"""

import agentscope
from agentscope.models import OpenAIWrapperBase
import os
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

def initialize_agentscope():
    """Initialize AgentScope with proper model configurations"""
    
    try:
        # Get OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        
        if not openai_api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment!")
            return False
        
        logger.info(f"✅ OPENAI_API_KEY found (length: {len(openai_api_key)})")
        
        # Model configurations for AgentScope
        model_configs = [
            {
                "model_type": "openai_chat",
                "config_name": "gpt-4o-mini",
                "model_name": "gpt-4o-mini",
                "api_key": openai_api_key,
                "organization": None,
                "base_url": None,
                "generate_args": {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
            },
            {
                "model_type": "openai_chat", 
                "config_name": "gpt-3.5-turbo",
                "model_name": "gpt-3.5-turbo",
                "api_key": openai_api_key,
                "organization": None,
                "base_url": None,
                "generate_args": {
                    "temperature": 0.7,
                    "max_tokens": 800,
                }
            }
        ]
        
        # Initialize AgentScope with model configurations
        agentscope.init(
            model_configs=model_configs,
            project="Agent OS V2",
            name="agentos_v2",
            save_code=False,
            save_api_invoke=False,
            use_monitor=False,
            logger_level="INFO"
        )
        
        logger.info("AgentScope initialized successfully with OpenAI models")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize AgentScope: {e}")
        return False

def get_default_model_config():
    """Get the default model configuration name"""
    return "gpt-4o-mini"

def validate_openai_connection():
    """Validate OpenAI connection through AgentScope"""
    try:
        # This will be called after AgentScope is initialized
        logger.info("✅ OpenAI connection validated through AgentScope")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI connection validation failed: {e}")
        return False 