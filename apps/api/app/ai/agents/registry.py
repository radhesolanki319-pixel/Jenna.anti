"""Agent Registry for managing available specialized agents in Jenna AI."""

from typing import Any
from app.ai.agents.base import BaseAgent
from app.ai.agents.specialized import (
    AnalysisAgent,
    AutonomousSystemAgent,
    CodingAgent,
    DocumentSynthesisAgent,
    EnterpriseDevOpsAgent,
    FrontierMathAgent,
    GeneralTaskAgent,
    ResearchAgent,
    Spatial3DAgent,
    WritingAgent,
)
from app.ai.agents.types import AgentType
from app.core.permissions import PermissionAction


class AgentRegistry:
    """Registry maintaining active agent definitions and permission requirements."""

    def __init__(self, include_astra: bool = False) -> None:
        self._agents: dict[AgentType, BaseAgent] = {}
        self._register_default_agents()
        if include_astra:
            self.register_astra_agents()

    def _register_default_agents(self) -> None:
        """Register the core standard specialized agents."""
        self.register(ResearchAgent())
        self.register(CodingAgent())
        self.register(AnalysisAgent())
        self.register(WritingAgent())
        self.register(GeneralTaskAgent())

    def register_astra_agents(self) -> None:
        """Register GPT-6 Astra domain specialists."""
        self.register(Spatial3DAgent())
        self.register(EnterpriseDevOpsAgent())
        self.register(DocumentSynthesisAgent())
        self.register(FrontierMathAgent())
        self.register(AutonomousSystemAgent())


    def register(self, agent: BaseAgent) -> None:
        """Register or overwrite an agent instance."""
        self._agents[agent.agent_type] = agent

    def get(self, agent_type: Any) -> BaseAgent | None:
        """Retrieve an agent by its AgentType or string name/value."""
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type.upper())
            except (ValueError, KeyError):
                for a in self._agents.values():
                    if a.name.lower() == agent_type.lower() or a.agent_type.value.lower() == agent_type.lower():
                        return a
        return self._agents.get(agent_type)

    def list_agents(self) -> list[BaseAgent]:
        """Return all registered agent instances."""
        return list(self._agents.values())

    def list_agent_dicts(self) -> list[dict[str, Any]]:
        """Return human-readable metadata for all registered agents."""
        return [agent.to_dict() for agent in self._agents.values()]

    def get_required_permission(self, agent_type: AgentType) -> PermissionAction:
        """Fetch required permission tier for an agent type."""
        agent = self.get(agent_type)
        if agent:
            return agent.required_permission
        return PermissionAction.READ


# Global singleton registry instance
agent_registry = AgentRegistry(include_astra=True)

