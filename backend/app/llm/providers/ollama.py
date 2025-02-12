import json
from typing import Any, Dict, List, Optional
import aiohttp
from ...llm.mcp import MCPProvider, ProviderException

class OllamaProvider(MCPProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def _initialize(self) -> None:
        """Initialize the aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _close(self) -> None:
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a completion using Ollama's /api/generate endpoint"""
        await self._initialize()

        # Prepare the request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderException(
                        f"Ollama API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                return {
                    "text": data.get("response", ""),
                    "model": model,
                    "provider": "ollama",
                    "raw": data
                }

        except aiohttp.ClientError as e:
            raise ProviderException(f"Failed to connect to Ollama: {str(e)}")
        except json.JSONDecodeError:
            raise ProviderException("Invalid JSON response from Ollama")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion using Ollama's /api/chat endpoint"""
        await self._initialize()

        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderException(
                        f"Ollama API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                return {
                    "text": data.get("message", {}).get("content", ""),
                    "model": model,
                    "provider": "ollama",
                    "raw": data
                }

        except aiohttp.ClientError as e:
            raise ProviderException(f"Failed to connect to Ollama: {str(e)}")
        except json.JSONDecodeError:
            raise ProviderException("Invalid JSON response from Ollama")

