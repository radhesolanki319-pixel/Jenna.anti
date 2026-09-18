"""Agent Runtime Foundation types, schemas, and lifecycle enums.

Conforms to Part 4 Phase 1 specifications:
- Agent Registry
- AgentRunner
- Task model & lifecycle: CREATED, QUEUED, RUNNING, WAITING, SUCCEEDED, FAILED, CANCELLED
- Context handoff contracts
- Budgets and boundaries
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, Field


from app.models.tasks import AgentTaskStatus, AgentType


class AgentBudget(BaseModel):
    """Execution boundaries and limits for an agent run."""
    max_steps: int = Field(default=10, ge=1, le=50, description="Maximum planning/execution steps permitted.")
    max_tokens: int = Field(default=4000, ge=100, le=32000, description="Cumulative token limit across all steps.")
    timeout_seconds: float = Field(default=60.0, ge=5.0, le=600.0, description="Universal execution timeout.")
    max_cost_cents: float = Field(default=50.0, ge=0.0, description="Maximum allowable spending cap in cents.")


class TaskStep(BaseModel):
    """Individual decomposed step within an agent execution plan."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int
    description: str
    agent_type: AgentType
    status: AgentTaskStatus = AgentTaskStatus.CREATED
    input_context: dict[str, Any] = Field(default_factory=dict)
    output_summary: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentHandoff(BaseModel):
    """Structured contract for handing off execution context between agents."""
    handoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: AgentType
    to_agent: AgentType
    reason: str
    context_summary: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


class AgentContext(BaseModel):
    """Runtime context provided to agents during execution."""
    task_id: str
    user_id: str
    initial_goal: str
    memory_context: str | None = None
    working_memory: dict[str, Any] = Field(default_factory=dict)
    step_history: list[TaskStep] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


class TaskResult(BaseModel):
    """Aggregated final outcome of an agent task execution."""
    task_id: str
    status: AgentTaskStatus
    summary: str
    output: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    total_steps: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    error: str | None = None


class AgentTask(BaseModel):
    """Durable representation of a user-initiated agent task."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    agent_type: AgentType = AgentType.GENERAL_TASK
    status: AgentTaskStatus = AgentTaskStatus.CREATED
    budget: AgentBudget = Field(default_factory=AgentBudget)
    steps: list[TaskStep] = Field(default_factory=list)
    result: TaskResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateTaskRequest(BaseModel):
    """Request payload to create and initiate an agent task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    agent_type: AgentType = AgentType.GENERAL_TASK
    budget: AgentBudget | None = None
