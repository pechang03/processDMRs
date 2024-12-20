"""
Model Context Protocol (MCP) implementation for managing different LLM providers and configurations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Supported LLM provider types"""
    OPENAI = "openai"
    OLLAMA = "ollama" 
    ANTHROPIC = "anthropic"

@dataclass
class MCPConfig:
    """Configuration for MCP provider"""
    provider: ProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = 4096
    max_tokens: int = 1000
    temperature: float = 0.7
    extra_params: Dict[str, Any] = None

class MCPProvider(ABC):
    """Abstract base class for MCP providers"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize provider-specific client/settings"""
        pass
        
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        pass
        
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion from message history"""
        pass

class MCPManager:
    """Manager class for MCP functionality"""
    
    def __init__(self):
        self._providers: Dict[ProviderType, MCPProvider] = {}
        self._active_config: Optional[MCPConfig] = None
        self._active_provider: Optional[MCPProvider] = None
        
    def configure(self, config: MCPConfig) -> None:
        """Configure and initialize a provider"""
        if config.provider not in self._providers:
            provider_class = self._get_provider_class(config.provider)
            self._providers[config.provider] = provider_class(config)
        self._active_config = config
        self._active_provider = self._providers[config.provider]
        
    def _get_provider_class(self, provider: ProviderType) -> type:
        """Get the appropriate provider class based on type"""
        # Import providers lazily to avoid circular imports
        if provider == ProviderType.OPENAI:
            from .providers.openai import OpenAIProvider
            return OpenAIProvider
        elif provider == ProviderType.OLLAMA:
            from .providers.ollama import OllamaProvider
            return OllamaProvider
        elif provider == ProviderType.ANTHROPIC:
            from .providers.anthropic import AnthropicProvider
            return AnthropicProvider
        else:
            raise ValueError(f"Unsupported provider type: {provider}")
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion using active provider"""
        if not self._active_provider:
            raise RuntimeError("No active provider configured")
        return await self._active_provider.generate(prompt, **kwargs)
        
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using active provider"""
        if not self._active_provider:
            raise RuntimeError("No active provider configured")
        return await self._active_provider.chat(messages, **kwargs)

# Global MCP manager instance
mcp_manager = MCPManager()

