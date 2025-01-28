"""Configuration management for LLM providers."""
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Create config from environment variables."""
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_model=os.getenv('OPENAI_MODEL', cls.openai_model),
            ollama_base_url=os.getenv('OLLAMA_BASE_URL', cls.ollama_base_url),
            ollama_model=os.getenv('OLLAMA_MODEL', cls.ollama_model),
        )
    
    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.openai_api_key)
    
    def get_ollama_api_url(self, endpoint: str) -> str:
        """Get full Ollama API URL for endpoint."""
        return urljoin(self.ollama_base_url, endpoint)

# Global config instance
config = LLMConfig.from_env()

