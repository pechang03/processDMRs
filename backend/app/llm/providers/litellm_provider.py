import os
import litellm
from typing import Any, Dict, List, Optional, Union
from ..mcp import MCPProvider, MCPError, MCPResponse, MCPMessage

class LiteLLMProvider(MCPProvider):
    """
    A unified provider implementation using LiteLLM to support multiple LLM backends
    including OpenAI and Ollama.
    """
    
    def __init__(self, provider_type: str, config: Dict[str, Any]):
        """
        Initialize the LiteLLM provider with configuration
        
        Args:
            provider_type: The type of provider ("openai" or "ollama")
            config: Provider configuration including api_key, base_url, etc.
        """
        super().__init__(provider_type, config)
        self.model = config.get("model")
        
        # Configure provider-specific settings
        if provider_type == "openai":
            litellm.api_key = config.get("api_key")
        elif provider_type == "ollama":
            os.environ["OLLAMA_API_BASE"] = config.get("base_url", "http://localhost:11434")
        
    async def generate(self, prompt: str, **kwargs) -> MCPResponse:
        """Generate completion from prompt"""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return MCPResponse(
                text=response.choices[0].message.content,
                raw_response=response
            )
            
        except Exception as e:
            raise MCPError(f"LiteLLM generation failed: {str(e)}")
            
    async def chat(self, messages: List[MCPMessage], **kwargs) -> MCPResponse:
        """Generate chat completion from message history"""
        try:
            # Convert MCPMessages to LiteLLM format
            litellm_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await litellm.acompletion(
                model=self.model,
                messages=litellm_messages,
                **kwargs
            )
            
            return MCPResponse(
                text=response.choices[0].message.content,
                raw_response=response
            )
            
        except Exception as e:
            raise MCPError(f"LiteLLM chat failed: {str(e)}")
            
    async def _initialize(self) -> None:
        """Verify connection and model availability"""
        try:
            # Test connection with a minimal prompt
            await self.generate("test", max_tokens=1)
        except Exception as e:
            raise MCPError(f"Failed to initialize LiteLLM provider: {str(e)}")

