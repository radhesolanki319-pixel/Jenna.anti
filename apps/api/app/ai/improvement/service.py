"""Self-Improvement Service coordinating proposals, sandbox evaluations, canary deployments, and rollbacks.

Implements Part 8 Phase 1 & Phase 2:
- Complete observe -> evaluate -> propose -> sandbox -> test -> verify -> approval -> deploy -> monitor -> rollback loop
- Strict human approval requirement for production deployment
- Safety and regression containment
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.ai.improvement.canary_manager import canary_manager
from app.ai.improvement.sandbox import improvement_sandbox
from app.ai.improvement.types import (
    CanaryDeploymentRecord,
    ImprovementCategory,
    ImprovementProposal,
    ProposalStatus,
    RollbackRecord,
    SandboxEvaluationResult,
)
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.users import User


class SelfImprovementService:
    """Service managing platform self-improvement proposals and governance."""

    def __init__(self) -> None:
        self.sandbox = improvement_sandbox
        self.canary = canary_manager
        # In-memory proposal storage: proposal_id -> ImprovementProposal
        self._proposals: dict[str, ImprovementProposal] = {}
        # Evaluation history: eval_id -> SandboxEvaluationResult
        self._evaluations: dict[str, SandboxEvaluationResult] = {}

        # Seed initial baseline proposals
        self._seed_default_proposals()

    def _seed_default_proposals(self) -> None:
        """Seed default proposals for initial demonstration."""
        p1 = ImprovementProposal(
            proposal_id="prop-prompt-opt-101",
            title="Optimize Jenna Hindi-English bilingual transition markers",
            category=ImprovementCategory.PROMPT_OPTIMIZATION,
            rationale="Reduce code-switching latency and improve Hinglish phrasing naturalness.",
            proposed_changes={"temperature": 0.65, "tone_naturalness_boost": True},
            status=ProposalStatus.TESTS_PASSED,
        )
        self._proposals[p1.proposal_id] = p1

    def list_proposals(self) -> list[ImprovementProposal]:
        """List all current improvement proposals."""
        return list(self._proposals.values())

    def get_proposal(self, proposal_id: str) -> ImprovementProposal:
        """Fetch proposal by ID."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise NotFoundError(f"Improvement proposal '{proposal_id}' not found.")
        return proposal

    def create_proposal(
        self,
        title: str,
        category: ImprovementCategory,
        rationale: str,
        proposed_changes: dict[str, Any],
    ) -> ImprovementProposal:
        """Create a new self-improvement proposal."""
        proposal = ImprovementProposal(
            title=title,
            category=category,
            rationale=rationale,
            proposed_changes=proposed_changes,
            status=ProposalStatus.PROPOSED,
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def run_sandbox_evaluation(self, proposal_id: str) -> SandboxEvaluationResult:
        """Execute candidate proposal inside isolated regression test sandbox."""
        proposal = self.get_proposal(proposal_id)
        proposal.status = ProposalStatus.SANDBOX_TESTING

        eval_result = self.sandbox.evaluate_proposal(proposal)
        self._evaluations[eval_result.eval_id] = eval_result

        if eval_result.regression_detected or not eval_result.security_check_passed:
            proposal.status = ProposalStatus.TESTS_FAILED
        else:
            proposal.status = ProposalStatus.TESTS_PASSED

        proposal.updated_at = datetime.now(timezone.utc)
        return eval_result

    def approve_proposal(self, proposal_id: str, admin_user: User) -> ImprovementProposal:
        """Explicit human signoff required by Part 8 governance rules."""
        proposal = self.get_proposal(proposal_id)
        if proposal.status != ProposalStatus.TESTS_PASSED:
            raise ValidationError("Cannot approve proposal that has not passed sandbox tests.")

        proposal.status = ProposalStatus.APPROVED
        proposal.approved_by = str(admin_user.id)
        proposal.updated_at = datetime.now(timezone.utc)
        return proposal

    def deploy_canary(
        self,
        proposal_id: str,
        admin_user: User,
        traffic_pct: int = 5,
    ) -> CanaryDeploymentRecord:
        """Deploy approved candidate into staged canary."""
        proposal = self.get_proposal(proposal_id)
        return self.canary.deploy_canary(
            proposal=proposal,
            traffic_pct=traffic_pct,
            approved_by_user=str(admin_user.id),
        )

    def promote_production(self, proposal_id: str, admin_user: User) -> ImprovementProposal:
        """Promote healthy canary to 100% full production deployment."""
        proposal = self.get_proposal(proposal_id)
        return self.canary.promote_to_production(proposal=proposal, approved_by_user=str(admin_user.id))

    def rollback(
        self,
        proposal_id: str,
        admin_user: User,
        reason: str = "Operator requested rollback",
    ) -> RollbackRecord:
        """Instantly revert canary or production changes back to baseline."""
        proposal = self.get_proposal(proposal_id)
        return self.canary.execute_rollback(
            proposal=proposal,
            reason=reason,
            triggered_by=str(admin_user.id),
        )


self_improvement_service = SelfImprovementService()
