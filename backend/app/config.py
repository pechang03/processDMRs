import os
from pathlib import Path
from typing import Union, Dict, Any
from dotenv import load_dotenv

def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    current = Path(__file__).resolve().parent
    while current.name != 'processDMR' and current != current.parent:
        current = current.parent
    return current

# Base directory configuration
BASE_DIR = get_project_root()
env_path = BASE_DIR / "processDMR.env"
load_dotenv(env_path)

class AppConfig:
    """Base configuration class with get() method for backward compatibility.
    
    This class provides both class-based configuration and integration with Flask's app.config.
    The get() method will first check app.config if available, then fall back to class attributes.
    """
    @classmethod
    def get(cls, key: str = None) -> Union[Any, Dict[str, Any]]:
        # First try to get from Flask app.config if it exists
        from flask import current_app
        try:
            if key is None:
                return {k: v for k, v in current_app.config.items() 
                    if not k.startswith('_')}
            return current_app.config.get(key, getattr(cls, key, None))
        except RuntimeError:
            # If not in Flask context, fall back to class attributes
            if key is None:
                return {k: v for k, v in cls.__dict__.items() 
                    if not k.startswith('_')}
            return getattr(cls, key, None)

# Prompt Management Configuration
class PromptConfig(AppConfig):
    PROMPTS_DIR = os.getenv("PROMPTS_DIR", str(BASE_DIR / "prompts"))
    SCHEMAS_DIR = os.getenv("SCHEMAS_DIR", str(BASE_DIR / "prompts" / "schemas"))
    DEFAULT_SCHEMA = "prompt.xsd"

# LLM Configuration
class LLMConfig(AppConfig):
    # Provider Settings
    AVAILABLE_PROVIDERS = ["openai", "ollama"]
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "ollama")
    
    # Default model configurations
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama2")
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
    
    # Provider URLs
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AZURE_API_KEY = os.getenv("AZURE_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Provider Settings
    PROVIDER_TIMEOUT = int(os.getenv("PROVIDER_TIMEOUT", "30"))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))
    
    # Azure Specific Settings
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2023-05-15")
    AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "")
    AZURE_RESOURCE_NAME = os.getenv("AZURE_RESOURCE_NAME", "")
    
    # Provider-specific model listings
    OPENAI_MODELS = ["gpt-4", "gpt-3.5-turbo"]
    OLLAMA_MODELS = ["llama2", "codellama", "mistral", "neural-chat", "stablelm", "dolphin-phi"]
    
    # Model Settings
    MODEL_CONFIG = {
        # OpenAI Models
        "gpt-4": {
            "provider": "openai",
            "max_tokens": 8000,
            "supports_functions": True
        },
        "gpt-3.5-turbo": {
            "provider": "openai",
            "max_tokens": 4000,
            "supports_functions": True
        },
        # Ollama Models
        "llama2": {
            "provider": "ollama",
            "max_tokens": 4096,
            "supports_functions": False
        },
        "codellama": {
            "provider": "ollama",
            "max_tokens": 4096,
            "supports_functions": False
        },
        "mistral": {
            "provider": "ollama",
            "max_tokens": 4096,
            "supports_functions": False
        },
        "neural-chat": {
            "provider": "ollama",
            "max_tokens": 4096,
            "supports_functions": False
        },
        "stablelm": {
            "provider": "ollama",
            "max_tokens": 4096,
            "supports_functions": False
        },
        "dolphin-phi": {
            "provider": "ollama",
            "max_tokens": 2048,
            "supports_functions": False
        }
    }

# API Configuration
class APIConfig(AppConfig):
    # Environment
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
    
    # CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "100 per minute"
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

# Database Configuration
class DatabaseConfig(AppConfig):
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "dmr_analysis.db"))
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Create config instances
prompt_config = PromptConfig()
llm_config = LLMConfig()
api_config = APIConfig()
db_config = DatabaseConfig()

def load_config(app):
    """Load all configuration into Flask app.config.
    
    This function should be called during app initialization to ensure
    all configuration is available via app.config.
    
    Args:
        app: Flask application instance
    """
    # Load configurations from each config class
    for config_class in [PromptConfig, LLMConfig, APIConfig, DatabaseConfig]:
        config_dict = {k: v for k, v in config_class.__dict__.items() 
                    if not k.startswith('_')}
        app.config.update(config_dict)
    
    # Ensure required paths exist
    app.config['BASE_DIR'] = BASE_DIR
    app.config['PROMPTS_DIR'] = Path(app.config['PROMPTS_DIR'])
    app.config['SCHEMAS_DIR'] = Path(app.config['SCHEMAS_DIR'])
    app.config['DB_PATH'] = Path(app.config['DB_PATH'])
    
    return app
