"""Agents API Router: Specialized agent registry, task creation, execution, and step telemetry."""

import logging
from typing import Any, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.orchestrator import agent_orchestrator
from app.ai.agents.registry import agent_registry
from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.tasks import AgentTaskStatus, AgentType
from app.models.users import User
from app.repositories.agent_task_repo import AgentTaskRepository
from app.schemas.agents import (
    AgentConfirmationRequest,
    AgentDecompositionPlan,
    AgentStepTraceResponse,
    AgentTaskCreate,
    AgentTaskDetailResponse,
    AgentTaskResponse,
)
from app.services.agent_runner_service import agent_runner_service
from app.services.auth_service import get_current_user

logger = logging.getLogger("jenna.agents_router")

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "/registry",
    summary="List available specialized agents",
    description="Returns registry specifications, capabilities, budgets, and permissions for all registered agents.",
)
async def list_agent_registry(
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List all registered agent personas."""
    return [agent.to_dict() for agent in agent_registry.list_agents()]


@router.post(
    "/decompose",
    response_model=AgentDecompositionPlan,
    summary="Preview task decomposition plan",
    description="Analyzes a complex objective and previews subtask assignments without storing records.",
)
async def preview_decomposition(
    payload: AgentTaskCreate,
    current_user: User = Depends(get_current_user),
) -> AgentDecompositionPlan:
    """Preview decomposition of a complex task."""
    return agent_orchestrator.decompose_task(payload.title, payload.description)


@router.post(
    "/tasks",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent task",
    description="Initializes a new autonomous agent task, with optional multi-agent planner decomposition.",
)
async def create_agent_task(
    payload: AgentTaskCreate,
    auto_decompose: bool = Query(default=False, description="Whether to automatically decompose into specialized subtasks"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskResponse:
    """Create a task owned by the authenticated user."""
    task = await agent_runner_service.create_task(
        db=db,
        user_id=current_user.id,
        data=payload,
        auto_decompose=auto_decompose,
    )
    return AgentTaskResponse.model_validate(task)


@router.get(
    "/tasks",
    response_model=list[AgentTaskResponse],
    summary="List agent tasks",
    description="Fetch filtered list of tasks isolated to the authenticated user.",
)
async def list_agent_tasks(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (QUEUED, RUNNING, SUCCEEDED, etc.)"),
    agent_type: Optional[str] = Query(default=None, description="Filter by agent type (RESEARCH, CODING, etc.)"),
    parent_only: bool = Query(default=False, description="Return only top-level root tasks"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentTaskResponse]:
    """List user tasks with optional filters."""
    repo = AgentTaskRepository(db)
    tasks = await repo.list_user_tasks(
        user_id=current_user.id,
        status=status_filter,
        agent_type=agent_type,
        parent_only=parent_only,
        limit=limit,
        offset=offset,
    )
    return [AgentTaskResponse.model_validate(t) for t in tasks]


@router.get(
    "/tasks/{task_id}",
    response_model=AgentTaskDetailResponse,
    summary="Get task details and step traces",
    description="Fetch a specific task including subtasks and execution telemetry traces.",
)
async def get_agent_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskDetailResponse:
    """Get full task details and execution history."""
    repo = AgentTaskRepository(db)
    task = await repo.get_user_task(task_id, current_user.id, include_relations=True)
    if not task:
        raise NotFoundError(f"Agent task '{task_id}' not found")

    traces = await repo.get_step_traces(task_id, current_user.id)
    subtasks = await repo.get_subtasks(task_id, current_user.id)

    response_data = AgentTaskResponse.model_validate(task).model_dump()
    response_data["traces"] = [AgentStepTraceResponse.model_validate(tr) for tr in traces]
    response_data["subtasks"] = [AgentTaskResponse.model_validate(sub) for sub in subtasks]
    response_data["subtask_count"] = len(subtasks)

    return AgentTaskDetailResponse(**response_data)


@router.post(
    "/tasks/{task_id}/execute",
    response_model=AgentTaskResponse,
    summary="Execute agent task pipeline",
    description="Triggers execution loop for a task and its decomposed subtasks.",
)
async def execute_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskResponse:
    """Execute a task and its subtasks."""
    task = await agent_runner_service.execute_task_pipeline(db, task_id, current_user.id)
    return AgentTaskResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/confirm",
    response_model=AgentTaskResponse,
    summary="Confirm or deny sensitive action",
    description="Human-in-the-loop approval or rejection for a task awaiting confirmation.",
)
async def confirm_task_action(
    task_id: uuid.UUID,
    payload: AgentConfirmationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskResponse:
    """Submit approval decision for a sensitive agent step."""
    task = await agent_runner_service.confirm_task_action(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        confirmed=payload.confirmed,
        reason=payload.reason,
    )
    return AgentTaskResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=AgentTaskResponse,
    summary="Cancel / emergency stop task",
    description="Halts execution of a running or waiting agent task.",
)
async def cancel_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskResponse:
    """Halt an agent task immediately."""
    task = await agent_runner_service.cancel_task(db, task_id, current_user.id)
    return AgentTaskResponse.model_validate(task)
