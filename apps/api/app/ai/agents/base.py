"""Base agent abstraction for specialized agents in Jenna."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import time
from typing import Any

from app.ai.agents.types import (
    AgentBudget,
    AgentContext,
    AgentTaskStatus,
    AgentType,
    TaskStep,
)
from app.ai.types import AIRequest, ChatMessage, TaskType
from app.core.permissions import PermissionAction


class BaseAgent(ABC):
    """Abstract base class representing a specialized autonomous agent."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        description: str,
        required_permission: PermissionAction = PermissionAction.READ,
    ) -> None:
        self._name = name
        self._agent_type = agent_type
        self._description = description
        self._required_permission = required_permission

    @property
    def name(self) -> str:
        return self._name

    @property
    def agent_type(self) -> AgentType:
        return self._agent_type

    @property
    def description(self) -> str:
        return self._description

    @property
    def required_permission(self) -> PermissionAction:
        return self._required_permission

    @property
    def default_budget(self) -> AgentBudget:
        """Default execution limits for this agent."""
        return AgentBudget(max_steps=10, max_tokens=4000, timeout_seconds=120.0)

    @property
    def system_prompt(self) -> str:
        """Baseline system prompt for this agent persona."""
        return self.build_system_instruction(
            AgentContext(task_id="", user_id="", initial_goal="")
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent specification to dictionary."""
        return {
            "name": self._name,
            "agent_type": self._agent_type.value if hasattr(self._agent_type, "value") else str(self._agent_type),
            "description": self._description,
            "required_permission": self._required_permission.value if hasattr(self._required_permission, "value") else str(self._required_permission),
        }

    @abstractmethod
    def build_system_instruction(self, context: AgentContext) -> str:
        """Construct deterministic, secure system prompt for this agent persona."""
        pass

    async def execute_step(
        self,
        step: TaskStep,
        context: AgentContext,
        ai_service: Any,
    ) -> TaskStep:
        """Execute a single step assigned to this agent using the AI service."""
        step.started_at = datetime.now(timezone.utc)
        step.status = AgentTaskStatus.RUNNING

        system_instruction = self.build_system_instruction(context)

        # Defensive context assembly
        history_summary = ""
        if context.step_history:
            history_summary = "\n".join(
                f"- Step {s.step_number} ({s.agent_type.value}): {s.output_summary or s.description}"
                for s in context.step_history[-5:]
                if s.output_summary
            )

        user_content_parts = [
            f"Goal: {context.initial_goal}",
            f"Current Step #{step.step_number}: {step.description}",
        ]
        if history_summary:
            user_content_parts.append(f"Previous Steps Completed:\n{history_summary}")
        if context.memory_context:
            user_content_parts.append(f"\n{context.memory_context}")

        prompt_text = "\n\n".join(user_content_parts)

        ai_request = AIRequest(
            messages=[ChatMessage(role="user", content=prompt_text)],
            system_instruction=system_instruction,
            task_type=TaskType.CHAT if self._agent_type == AgentType.GENERAL_TASK else TaskType.REASONING,
            temperature=0.2,
            max_tokens=1500,
        )

        try:
            ai_response = await ai_service.generate(ai_request)
            step.output_summary = ai_response.text.strip()
            step.status = AgentTaskStatus.SUCCEEDED
            step.error = None
        except Exception as exc:
            step.status = AgentTaskStatus.FAILED
            step.error = str(exc)

        step.completed_at = datetime.now(timezone.utc)
        return step
