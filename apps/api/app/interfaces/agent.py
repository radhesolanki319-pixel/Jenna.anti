"""Future Domain Interface: AgentRunner

Defines the contract for autonomous goal-driven agents and subagent execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class AgentStatus(str, Enum):
    """Lifecycle states of an autonomous agent run."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentRun:
    """Metadata tracking an agent's execution lifecycle."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    task: str = ""
    user_id: str = ""
    status: AgentStatus = AgentStatus.PENDING
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentTaskResult:
    """Outcome and artifacts produced by an agent run."""
    run_id: str
    status: AgentStatus
    output: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    steps_executed: int = 0
    error: str | None = None


class AgentRunner(ABC):
    """Abstract interface contract for autonomous agent orchestrators."""

    @abstractmethod
    async def create_run(
        self,
        agent_name: str,
        task: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> AgentRun:
        """Initialize and register a new autonomous agent execution."""
        pass

    @abstractmethod
    async def execute_task(self, run_id: str) -> AgentTaskResult:
        """Run the agent through its planning, tool calling, and evaluation loops."""
        pass

    @abstractmethod
    async def get_status(self, run_id: str) -> AgentRun:
        """Fetch live status and metrics for an agent run."""
        pass

    @abstractmethod
    async def cancel_run(self, run_id: str) -> bool:
        """Halt execution of a running agent."""
        pass
