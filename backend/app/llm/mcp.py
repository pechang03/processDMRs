"""
Model Context Protocol (MCP) implementation using LiteLLM for unified LLM provider access
with support for specialized AI agents.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol
import logging
from litellm import completion, completion_cost

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Different specialized roles for AI agents"""
    RESEARCHER = auto()
    SEARCH = auto()
    SQL = auto()
    BIOINFORMATICS = auto()
    GENERAL = auto()

class ModelTier(Enum):
    """Model capability tiers with associated features"""
    WEAK = "weak"     # Basic tasks, fast responses
    MAIN = "main"     # Core processing, balanced capabilities  
    SEARCH = "search" # Research and analysis focused

class ModelCapability(Enum):
    """Specific capabilities of different model tiers"""
    CODE = "code"
    RESEARCH = "research"
    SEARCH = "search"
    SQL = "sql"
    BIO = "bio"

model_tier_capabilities = {
    ModelTier.WEAK: [ModelCapability.CODE],
    ModelTier.MAIN: [ModelCapability.CODE, ModelCapability.SQL, ModelCapability.BIO],
    ModelTier.SEARCH: [ModelCapability.SEARCH, ModelCapability.RESEARCH]
}

model_tier_mappings = {
    ModelTier.WEAK: "ollama/mistral",
    ModelTier.MAIN: "ollama/llama2",
    ModelTier.SEARCH: "ollama/nous-hermes"
}

@dataclass
class MCPConfig:
    """Configuration for LiteLLM provider"""
    model_tier: ModelTier
    capabilities: List[ModelCapability]
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = 4096
    max_tokens: int = 1000
    temperature: float = 0.7
    extra_params: Optional[Dict[str, Any]] = None

class Agent(ABC):
    """Base class for specialized AI agents"""
    
    def __init__(self, config: MCPConfig, role: AgentRole):
        self.config = config
        self.role = role
        self.context: List[Dict[str, str]] = []
    
    @abstractmethod
    async def process(self, input_data: Any) -> str:
        """Process input data according to agent's specialization"""
        pass
        
    async def _generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Internal method to generate responses using LiteLLM"""
        try:
            response = await completion(
                model=model_tier_mappings[self.config.model_tier],
                messages=messages,
                api_key=self.config.api_key,
                api_base=self.config.base_url,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                **self.config.extra_params or {}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Agent generation error: {str(e)}")
            raise

class ResearchAgent(Agent):
    """Specialized agent for research and analysis tasks"""
    def __init__(self, config: MCPConfig):
        super().__init__(config, AgentRole.RESEARCHER)
        
    async def process(self, input_data: Any) -> str:
        # Add research-specific processing logic
        return await self._generate(self.context + [{"role": "user", "content": str(input_data)}])

class SearchAgent(Agent):
    """Specialized agent for internet search and context gathering"""
    def __init__(self, config: MCPConfig):
        super().__init__(config, AgentRole.SEARCH)
        
    async def process(self, input_data: Any) -> str:
        # Add search-specific processing logic
        return await self._generate(self.context + [{"role": "user", "content": str(input_data)}])

class SQLAgent(Agent):
    """Specialized agent for database operations"""
    def __init__(self, config: MCPConfig):
        super().__init__(config, AgentRole.SQL)
        
    async def process(self, input_data: Any) -> str:
        # Add SQL-specific processing logic
        return await self._generate(self.context + [{"role": "user", "content": str(input_data)}])

class BioInformaticsAgent(Agent):
    """Specialized agent for bioinformatics analysis"""
    def __init__(self, config: MCPConfig):
        super().__init__(config, AgentRole.BIOINFORMATICS)
        
    async def process(self, input_data: Any) -> str:
        # Add bioinformatics-specific processing logic
        return await self._generate(self.context + [{"role": "user", "content": str(input_data)}])

class MCPManager:
    """Manager class for MCP functionality"""

        def __init__(self):
            self._active_config: Optional[MCPConfig] = None
            self._agents: Dict[AgentRole, Agent] = {}
            
        def configure(self, config: MCPConfig) -> None:
            """Configure the LiteLLM settings and initialize agents"""
            self._active_config = config
            
            # Initialize specialized agents
            # Map agents to appropriate model tiers
            researcher_config = MCPConfig(
                model_tier=ModelTier.MAIN,
                capabilities=[ModelCapability.RESEARCH]
            )
            search_config = MCPConfig(
                model_tier=ModelTier.SEARCH,
                capabilities=[ModelCapability.SEARCH]
            )
            sql_config = MCPConfig(
                model_tier=ModelTier.MAIN,
                capabilities=[ModelCapability.SQL]
            )
            bio_config = MCPConfig(
                model_tier=ModelTier.MAIN,
                capabilities=[ModelCapability.BIO]
            )

            self._agents = {
                AgentRole.RESEARCHER: ResearchAgent(researcher_config),
                AgentRole.SEARCH: SearchAgent(search_config),
                AgentRole.SQL: SQLAgent(sql_config),
                AgentRole.BIOINFORMATICS: BioInformaticsAgent(bio_config)
            }

        def get_agent(self, role: AgentRole) -> Agent:
            """Get an agent for a specific role"""
            if not self._active_config:
                raise RuntimeError("No configuration set")
            return self._agents.get(role) or self._agents[AgentRole.GENERAL]
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion using LiteLLM"""
        if not self._active_config:
            raise RuntimeError("No configuration set")
            
        try:
            response = await completion(
                model=model_tier_mappings[self._active_config.model_tier],
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
                model=model_tier_mappings[self._active_config.model_tier],
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

