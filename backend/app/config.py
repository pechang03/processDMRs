import os
from pathlib import Path

# Base directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Prompt Management Configuration
class PromptConfig:
    PROMPTS_DIR = os.getenv("PROMPTS_DIR", str(BASE_DIR / "prompts"))
    SCHEMAS_DIR = os.getenv("SCHEMAS_DIR", str(BASE_DIR / "prompts" / "schemas"))
    DEFAULT_SCHEMA = "prompt.xsd"

# LLM Configuration
class LLMConfig:
    # Default model configurations
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    # Provider URLs
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Provider Settings
    PROVIDER_TIMEOUT = int(os.getenv("PROVIDER_TIMEOUT", "30"))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))

# API Configuration
class APIConfig:
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
class DatabaseConfig:
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "dmr_analysis.db"))
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Create config instances
prompt_config = PromptConfig()
llm_config = LLMConfig()
api_config = APIConfig()
db_config = DatabaseConfig()

