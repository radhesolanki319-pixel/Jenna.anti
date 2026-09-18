"""Approvals and Permission Policies API Router.

Consolidates human-in-the-loop confirmation queues across agent tasks,
self-improvement proposals, device authorizations, and explains active permission policies.
"""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.improvement import self_improvement_service
from app.core.database import get_db
from app.core.permissions import Permission
from app.interfaces.permissions import AuthorizationDecision
from app.models.tasks import AgentTaskStatus
from app.models.users import User
from app.repositories.agent_task_repo import AgentTaskRepository
from app.repositories.audit_repo import AuditEventRepository
from app.routers.agents import AgentTaskResponse
from app.routers.audit import AuditEventResponse
from app.services.agent_runner_service import agent_runner_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/approvals", tags=["Approvals & Permissions"])


class ApprovalDecisionRequest(BaseModel):
    """Payload for approving or rejecting a pending sensitive action."""

    item_type: str = Field(..., description="'task' or 'proposal'")
    item_id: str = Field(..., description="UUID of task or proposal ID")
    decision: str = Field(..., description="'approve' or 'reject'")
    reason: str | None = Field(default=None, description="Optional explanation for decision")


class PendingApprovalsResponse(BaseModel):
    """Pending actions awaiting human sign-off."""

    tasks: list[AgentTaskResponse]
    proposals: list[dict[str, Any]]
    total_pending: int


class PermissionPolicyTier(BaseModel):
    tier: str
    description: str
    requires_confirmation: bool


class PermissionPoliciesResponse(BaseModel):
    """System 3-tier permission model specifications."""

    tiers: list[PermissionPolicyTier]
    decision_outcomes: list[str]
    governance_invariants: list[str]


@router.get("/pending", response_model=PendingApprovalsResponse, summary="Get pending approval queue")
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PendingApprovalsResponse:
    """Fetch all pending confirmation requests requiring human sign-off."""
    task_repo = AgentTaskRepository(db)
    waiting_tasks = await task_repo.list_user_tasks(
        user_id=current_user.id,
        status=AgentTaskStatus.WAITING.value,
        limit=50,
    )
    # Filter to those strictly requiring confirmation
    pending_tasks = [t for t in waiting_tasks if t.requires_confirmation]

    # Improvement proposals awaiting approval
    proposals = self_improvement_service.list_proposals()
    pending_proposals = [
        p.model_dump() for p in proposals if p.status.value == "VALIDATED"
    ]

    return PendingApprovalsResponse(
        tasks=[AgentTaskResponse.model_validate(t) for t in pending_tasks],
        proposals=pending_proposals,
        total_pending=len(pending_tasks) + len(pending_proposals),
    )


@router.post("/decide", summary="Submit approval or rejection decision")
async def submit_approval_decision(
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute human approval or rejection for a pending task or proposal."""
    approved = payload.decision.lower() == "approve"

    if payload.item_type == "task":
        task_uuid = uuid.UUID(payload.item_id)
        task = await agent_runner_service.confirm_task_action(
            db=db,
            task_id=task_uuid,
            user_id=current_user.id,
            confirmed=approved,
            reason=payload.reason,
        )
        return {
            "status": "success",
            "item_type": "task",
            "item_id": str(task.id),
            "result_status": task.status,
            "confirmed": approved,
        }

    if payload.item_type == "proposal":
        if approved:
            prop = self_improvement_service.approve_proposal(payload.item_id, current_user)
        else:
            prop = self_improvement_service.rollback(payload.item_id, current_user, reason=payload.reason or "Rejected by user")
        return {
            "status": "success",
            "item_type": "proposal",
            "item_id": prop.id,
            "result_status": prop.status.value,
            "confirmed": approved,
        }

    return {"status": "error", "message": f"Unsupported item_type '{payload.item_type}'"}


@router.get("/history", response_model=list[AuditEventResponse], summary="Approval decision history")
async def get_approval_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditEventResponse]:
    """Retrieve audit history of human approval / rejection decisions."""
    audit_repo = AuditEventRepository(db)
    events = await audit_repo.list_filtered(
        user_id=current_user.id,
        event_type="agent_confirmation_response",
        limit=limit,
    )
    return [AuditEventResponse.model_validate(e) for e in events]


@router.get("/policies", response_model=PermissionPoliciesResponse, summary="Get permission policy matrix")
async def get_permission_policies(
    current_user: User = Depends(get_current_user),
) -> PermissionPoliciesResponse:
    """Returns active 3-tier permission governance structure."""
    return PermissionPoliciesResponse(
        tiers=[
            PermissionPolicyTier(
                tier=Permission.READ.value,
                description="Read-only observation, querying, and non-state-mutating operations.",
                requires_confirmation=False,
            ),
            PermissionPolicyTier(
                tier=Permission.LOW_RISK_ACTION.value,
                description="Safe bounded mutations such as creating conversation notes, sandbox executions, or local caching.",
                requires_confirmation=False,
            ),
            PermissionPolicyTier(
                tier=Permission.SENSITIVE_ACTION.value,
                description="Actions affecting external state, filesystem writes, API calls, or device inputs.",
                requires_confirmation=True,
            ),
            PermissionPolicyTier(
                tier=Permission.CRITICAL_ACTION.value,
                description="Irreversible actions: production deployments, credential revocations, file deletions, or system changes.",
                requires_confirmation=True,
            ),
        ],
        decision_outcomes=[
            AuthorizationDecision.ALLOWED.value,
            AuthorizationDecision.DENIED.value,
            AuthorizationDecision.REQUIRES_CONFIRMATION.value,
        ],
        governance_invariants=[
            "System/security rules strictly outrank user instructions.",
            "Jenna cannot autonomously grant herself elevated permissions or deploy code to production.",
            "Credentials, passwords, and private API keys are strictly NO-STORE and never returned in logs.",
            "Emergency kill-switch immediately halts any active or waiting operation.",
        ],
    )
