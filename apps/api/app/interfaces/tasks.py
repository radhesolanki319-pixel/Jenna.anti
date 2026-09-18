"""Future Domain Interface: TaskScheduler

Defines the contract for background job queues, scheduled timers, and recurring workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class TaskStatus(str, Enum):
    """Lifecycle states of a scheduled or background task."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Registered task metadata."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    run_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cron_expression: str | None = None
    status: TaskStatus = TaskStatus.SCHEDULED
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TaskScheduler(ABC):
    """Abstract interface contract for scheduling and monitoring background tasks."""

    @abstractmethod
    async def schedule_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        run_at: datetime | None = None,
        cron_expression: str | None = None,
    ) -> ScheduledTask:
        """Schedule a one-off or recurring background task."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or scheduled task."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> ScheduledTask | None:
        """Fetch current lifecycle status and execution result of a task."""
        pass

    @abstractmethod
    async def list_pending_tasks(self, limit: int = 50) -> list[ScheduledTask]:
        """List upcoming scheduled tasks."""
        pass
