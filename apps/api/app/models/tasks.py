"""Agent Task and Step Trace models for autonomous agent orchestration."""

import enum
import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


class AgentTaskStatus(str, enum.Enum):
    """Lifecycle states of an autonomous agent task."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentType(str, enum.Enum):
    """Specialized agent roles registered in Jenna AI."""

    RESEARCH = "RESEARCH"
    CODING = "CODING"
    ANALYSIS = "ANALYSIS"
    WRITING = "WRITING"
    GENERAL_TASK = "GENERAL_TASK"

    # GPT-6 Astra Specialized Domains
    SPATIAL_3D = "SPATIAL_3D"
    ENTERPRISE_DEVOPS = "ENTERPRISE_DEVOPS"
    DOCUMENT_SYNTHESIS = "DOCUMENT_SYNTHESIS"
    FRONTIER_MATH = "FRONTIER_MATH"
    SYSTEM_AUTOMATION = "SYSTEM_AUTOMATION"


class TaskPriority(str, enum.Enum):
    """Priority level of scheduled or queued tasks."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentTask(Base):
    """Represents an autonomous or specialized agent task owned by a user."""

    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    agent_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=AgentType.GENERAL_TASK.value,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AgentTaskStatus.CREATED.value,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TaskPriority.NORMAL.value,
    )
    budget: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    steps_executed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    context_handoff: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    result_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    confirmation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", backref="agent_tasks")
    parent_task = relationship("AgentTask", remote_side=[id], backref="subtasks")
    traces = relationship(
        "AgentStepTrace",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="AgentStepTrace.step_index.asc()",
    )

    __table_args__ = (
        Index("ix_agent_tasks_user_status", "user_id", "status"),
        Index("ix_agent_tasks_user_updated", "user_id", "updated_at"),
    )


class AgentStepTrace(Base):
    """Audit and step-by-step execution telemetry for an agent task."""

    __tablename__ = "agent_step_traces"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="RUNNING",
    )
    duration_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    output_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    task = relationship("AgentTask", back_populates="traces")

    __table_args__ = (
        Index("ix_step_traces_task_index", "task_id", "step_index"),
    )
