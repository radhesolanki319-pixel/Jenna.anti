"""Controlled Self-Improvement and Governance API Router.

Exposes endpoints for proposal creation, sandbox testing, human approval, canary rollout, and rollback.
"""

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.ai.improvement import (
    CanaryDeploymentRecord,
    ImprovementCategory,
    ImprovementProposal,
    RollbackRecord,
    SandboxEvaluationResult,
    self_improvement_service,
)
from app.models.users import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/improvement", tags=["Controlled Self-Improvement"])


class CreateProposalPayload(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    category: ImprovementCategory
    rationale: str
    proposed_changes: dict[str, Any] = Field(default_factory=dict)


class DeployCanaryPayload(BaseModel):
    traffic_percentage: int = Field(default=5, ge=1, le=100)


class RollbackPayload(BaseModel):
    reason: str = Field(default="Manual operator rollback")


@router.get("/proposals", response_model=list[ImprovementProposal])
async def list_proposals(
    current_user: User = Depends(get_current_user),
) -> list[ImprovementProposal]:
    """List all improvement proposals."""
    return self_improvement_service.list_proposals()


@router.post("/proposals", response_model=ImprovementProposal)
async def create_proposal(
    payload: CreateProposalPayload,
    current_user: User = Depends(get_current_user),
) -> ImprovementProposal:
    """Submit a new candidate optimization proposal."""
    return self_improvement_service.create_proposal(
        title=payload.title,
        category=payload.category,
        rationale=payload.rationale,
        proposed_changes=payload.proposed_changes,
    )


@router.get("/proposals/{proposal_id}", response_model=ImprovementProposal)
async def get_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
) -> ImprovementProposal:
    """Fetch details of a single proposal."""
    return self_improvement_service.get_proposal(proposal_id)


@router.post("/proposals/{proposal_id}/sandbox-eval", response_model=SandboxEvaluationResult)
async def run_sandbox_evaluation(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
) -> SandboxEvaluationResult:
    """Run regression tests and safety audits on proposal within isolated sandbox."""
    return self_improvement_service.run_sandbox_evaluation(proposal_id)


@router.post("/proposals/{proposal_id}/approve", response_model=ImprovementProposal)
async def approve_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
) -> ImprovementProposal:
    """Provide explicit human signoff to authorize candidate deployment."""
    return self_improvement_service.approve_proposal(proposal_id, current_user)


@router.post("/proposals/{proposal_id}/deploy-canary", response_model=CanaryDeploymentRecord)
async def deploy_canary(
    proposal_id: str,
    payload: DeployCanaryPayload,
    current_user: User = Depends(get_current_user),
) -> CanaryDeploymentRecord:
    """Deploy approved proposal to staged canary pool."""
    return self_improvement_service.deploy_canary(
        proposal_id=proposal_id,
        admin_user=current_user,
        traffic_pct=payload.traffic_percentage,
    )


@router.post("/proposals/{proposal_id}/promote", response_model=ImprovementProposal)
async def promote_production(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
) -> ImprovementProposal:
    """Promote healthy canary to 100% production."""
    return self_improvement_service.promote_production(proposal_id, current_user)


@router.post("/proposals/{proposal_id}/rollback", response_model=RollbackRecord)
async def rollback_proposal(
    proposal_id: str,
    payload: RollbackPayload,
    current_user: User = Depends(get_current_user),
) -> RollbackRecord:
    """Immediately revert proposal and rollback to baseline version."""
    return self_improvement_service.rollback(proposal_id, current_user, reason=payload.reason)
