import openai
from typing import Dict, List, Optional, Any
from ...llm.mcp import MCPProvider, MCPRequest, MCPResponse, MCPError

class OpenAIProvider(MCPProvider):
    """OpenAI provider implementation for MCP"""
    
    def _initialize(self):
        """Initialize the OpenAI client with API key from config"""
        try:
            openai.api_key = self.config.get("api_key")
            if not openai.api_key:
                raise MCPError("OpenAI API key not configured")
        except Exception as e:
            raise MCPError(f"Failed to initialize OpenAI provider: {str(e)}")

    async def generate(self, request: MCPRequest) -> MCPResponse:
        """Generate completion using OpenAI's completion API"""
        try:
            response = await openai.Completion.acreate(
                model=request.model or "text-davinci-003",
                prompt=request.prompt,
                max_tokens=request.max_tokens or 1000,
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 1.0,
                frequency_penalty=request.frequency_penalty or 0.0,
                presence_penalty=request.presence_penalty or 0.0,
                stop=request.stop_sequences
            )
            
            return MCPResponse(
                provider="openai",
                model=request.model,
                output=response.choices[0].text,
                raw_response=response
            )
            
        except Exception as e:
            raise MCPError(f"OpenAI generation failed: {str(e)}")

    async def chat(self, messages: List[Dict[str, str]], 
                model: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                **kwargs: Any) -> MCPResponse:
        """Generate chat completion using OpenAI's chat API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=temperature or 0.7,
                max_tokens=max_tokens or 1000,
                **kwargs
            )
            
            return MCPResponse(
                provider="openai",
                model=model,
                output=response.choices[0].message.content,
                raw_response=response
            )
            
        except Exception as e:
            raise MCPError(f"OpenAI chat failed: {str(e)}")

