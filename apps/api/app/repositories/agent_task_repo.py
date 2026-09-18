"""Repository for managing AgentTask and AgentStepTrace database entities."""

from datetime import datetime, timezone
from typing import Any, Optional, Sequence
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tasks import AgentStepTrace, AgentTask, AgentTaskStatus, AgentType, TaskPriority
from app.repositories.base import BaseRepository


class AgentTaskRepository(BaseRepository[AgentTask]):
    """Data access layer for autonomous agent tasks with strict user scoping."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AgentTask, session)

    async def create_task(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str = "",
        agent_type: str = AgentType.GENERAL_TASK.value,
        priority: str = TaskPriority.NORMAL.value,
        budget: dict[str, Any] | None = None,
        parent_task_id: uuid.UUID | None = None,
        context_handoff: dict[str, Any] | None = None,
        status: str = AgentTaskStatus.CREATED.value,
    ) -> AgentTask:
        """Create a new agent task record isolated to the specified user."""
        budget_dict = budget or {"max_steps": 10, "max_tokens": 4000, "timeout_seconds": 120}
        handoff_dict = context_handoff or {}

        task = AgentTask(
            user_id=user_id,
            title=title.strip(),
            description=description.strip(),
            agent_type=agent_type,
            priority=priority,
            budget=budget_dict,
            parent_task_id=parent_task_id,
            context_handoff=handoff_dict,
            status=status,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_user_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        include_relations: bool = False,
    ) -> AgentTask | None:
        """Fetch a task ensuring user isolation, optionally loading subtasks and traces."""
        query = select(AgentTask).where(
            AgentTask.id == task_id,
            AgentTask.user_id == user_id,
        )
        if include_relations:
            query = query.options(
                selectinload(AgentTask.traces),
                selectinload(AgentTask.subtasks),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_tasks(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        agent_type: str | None = None,
        parent_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[AgentTask]:
        """Fetch filtered and paginated tasks for a user."""
        query = select(AgentTask).where(AgentTask.user_id == user_id)

        if status:
            query = query.where(AgentTask.status == status)
        if agent_type:
            query = query.where(AgentTask.agent_type == agent_type)
        if parent_only:
            query = query.where(AgentTask.parent_task_id.is_(None))

        query = query.order_by(desc(AgentTask.updated_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_user_tasks(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
    ) -> int:
        """Count total user tasks, optionally filtered by status."""
        query = select(func.count(AgentTask.id)).where(AgentTask.user_id == user_id)
        if status:
            query = query.where(AgentTask.status == status)
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def update_task_status(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str,
        result_summary: str | None = None,
        error: str | None = None,
        steps_executed: int | None = None,
        tokens_used: int | None = None,
        requires_confirmation: bool | None = None,
        confirmation_reason: str | None = None,
    ) -> AgentTask | None:
        """Update lifecycle state, metrics, or error on a user task."""
        task = await self.get_user_task(task_id, user_id)
        if not task:
            return None

        task.status = status
        if result_summary is not None:
            task.result_summary = result_summary
        if error is not None:
            task.error = error
        if steps_executed is not None:
            task.steps_executed = steps_executed
        if tokens_used is not None:
            task.tokens_used = tokens_used
        if requires_confirmation is not None:
            task.requires_confirmation = requires_confirmation
        if confirmation_reason is not None:
            task.confirmation_reason = confirmation_reason

        if status in (AgentTaskStatus.SUCCEEDED.value, AgentTaskStatus.FAILED.value, AgentTaskStatus.CANCELLED.value):
            task.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def record_step_trace(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        step_index: int,
        agent_type: str,
        action: str,
        status: str = "RUNNING",
        duration_ms: float = 0.0,
        output_summary: str = "",
    ) -> AgentStepTrace:
        """Append an execution step trace record for audit and telemetry."""
        trace = AgentStepTrace(
            task_id=task_id,
            user_id=user_id,
            step_index=step_index,
            agent_type=agent_type,
            action=action,
            status=status,
            duration_ms=duration_ms,
            output_summary=output_summary,
        )
        self.session.add(trace)
        await self.session.commit()
        await self.session.refresh(trace)
        return trace

    async def get_step_traces(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Sequence[AgentStepTrace]:
        """Fetch ordered step traces for a user task."""
        query = (
            select(AgentStepTrace)
            .where(
                AgentStepTrace.task_id == task_id,
                AgentStepTrace.user_id == user_id,
            )
            .order_by(AgentStepTrace.step_index.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_subtasks(
        self,
        parent_task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Sequence[AgentTask]:
        """Fetch all child subtasks for a given parent task."""
        query = (
            select(AgentTask)
            .where(
                AgentTask.parent_task_id == parent_task_id,
                AgentTask.user_id == user_id,
            )
            .order_by(AgentTask.created_at.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
