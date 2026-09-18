"""Pydantic schemas for autonomous agent tasks, execution traces, and orchestration."""

from datetime import datetime
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field

from app.models.tasks import AgentTaskStatus, AgentType, TaskPriority


class AgentBudgetSchema(BaseModel):
    """Execution bounds and resource budgets for an agent."""
    max_steps: int = Field(default=10, ge=1, le=50, description="Maximum execution steps allowed")
    max_tokens: int = Field(default=4000, ge=100, le=32000, description="Maximum LLM tokens allocated")
    timeout_seconds: int = Field(default=120, ge=5, le=600, description="Total timeout in seconds")


class ContextHandoffSchema(BaseModel):
    """Structured data contract passed between agents during task execution."""
    source_agent: str = Field(description="Name or type of the agent originating this handoff")
    task_summary: str = Field(description="Clean high-level outcome summary without raw chain of thought")
    artifacts: list[dict[str, Any]] = Field(default_factory=list, description="Structured deliverables or data items")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution environment or tracking details")


class AgentTaskCreate(BaseModel):
    """Schema for initializing a new autonomous agent task."""
    title: str = Field(..., min_length=1, max_length=255, description="Brief descriptive title")
    description: str = Field(default="", description="Detailed task requirements and instructions")
    agent_type: AgentType = Field(default=AgentType.GENERAL_TASK, description="Assigned agent specialty")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Execution priority")
    parent_task_id: Optional[uuid.UUID] = Field(default=None, description="Parent task if this is a decomposed subtask")
    budget: Optional[AgentBudgetSchema] = Field(default_factory=AgentBudgetSchema, description="Execution limits")
    context_handoff: Optional[dict[str, Any]] = Field(default_factory=dict, description="Input context from previous tasks")


class AgentTaskUpdate(BaseModel):
    """Schema for patching task status or results."""
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    status: Optional[AgentTaskStatus] = None
    priority: Optional[TaskPriority] = None
    result_summary: Optional[str] = None
    error: Optional[str] = None
    requires_confirmation: Optional[bool] = None
    confirmation_reason: Optional[str] = None


class AgentStepTraceResponse(BaseModel):
    """Telemetry record for a single step executed by an agent."""
    id: uuid.UUID
    task_id: uuid.UUID
    step_index: int
    agent_type: str
    action: str
    status: str
    duration_ms: float
    output_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentTaskResponse(BaseModel):
    """Public representation of an agent task."""
    id: uuid.UUID
    user_id: uuid.UUID
    parent_task_id: Optional[uuid.UUID] = None
    agent_type: str
    title: str
    description: str
    status: str
    priority: str
    budget: dict[str, Any]
    steps_executed: int
    tokens_used: int
    context_handoff: dict[str, Any]
    result_summary: Optional[str] = None
    error: Optional[str] = None
    requires_confirmation: bool
    confirmation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    subtask_count: int = 0

    model_config = {"from_attributes": True}


class AgentTaskDetailResponse(AgentTaskResponse):
    """Extended representation with child subtasks and step execution traces."""
    traces: list[AgentStepTraceResponse] = []
    subtasks: list[AgentTaskResponse] = []


class AgentConfirmationRequest(BaseModel):
    """User response to a sensitive-action confirmation prompt."""
    confirmed: bool = Field(..., description="Whether the user approved the sensitive step")
    reason: Optional[str] = Field(default=None, description="Optional explanation or feedback from user")


class AgentDecompositionSubtask(BaseModel):
    """A decomposed step proposed by the planner."""
    title: str
    description: str
    agent_type: AgentType
    order: int


class AgentDecompositionPlan(BaseModel):
    """Structured plan decomposing a complex goal into specialized subtasks."""
    original_task: str
    strategy: str
    subtasks: list[AgentDecompositionSubtask]
