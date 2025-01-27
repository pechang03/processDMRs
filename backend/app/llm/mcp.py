"""
Model Context Protocol (MCP) implementation using LiteLLM for unified LLM provider access.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
from litellm import completion, completion_cost

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Supported LLM model types via LiteLLM"""
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE = "claude-2"
    LLAMA2 = "ollama/llama2"
    CODELLAMA = "ollama/codellama"

@dataclass
class MCPConfig:
    """Configuration for LiteLLM provider"""
    model: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = 4096
    max_tokens: int = 1000
    temperature: float = 0.7
    extra_params: Optional[Dict[str, Any]] = None

class MCPManager:
    """Manager class for MCP functionality"""

        def __init__(self):
            self._active_config: Optional[MCPConfig] = None
            
        def configure(self, config: MCPConfig) -> None:
            """Configure the LiteLLM settings"""
            self._active_config = config
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion using LiteLLM"""
        if not self._active_config:
            raise RuntimeError("No configuration set")
            
        try:
            response = await completion(
                model=self._active_config.model.value,
                messages=[{"role": "user", "content": prompt}],
                api_key=self._active_config.api_key,
                api_base=self._active_config.base_url,
                max_tokens=kwargs.get("max_tokens", self._active_config.max_tokens),
                temperature=kwargs.get("temperature", self._active_config.temperature),
                **self._active_config.extra_params or {}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM generation error: {str(e)}")
            raise
            
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using LiteLLM"""
        if not self._active_config:
            raise RuntimeError("No configuration set")
            
        try:
            response = await completion(
                model=self._active_config.model.value,
                messages=messages,
                api_key=self._active_config.api_key,
                api_base=self._active_config.base_url,
                max_tokens=kwargs.get("max_tokens", self._active_config.max_tokens),
                temperature=kwargs.get("temperature", self._active_config.temperature),
                **self._active_config.extra_params or {}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM chat error: {str(e)}")
            raise

# Global MCP manager instance
mcp_manager = MCPManager()

