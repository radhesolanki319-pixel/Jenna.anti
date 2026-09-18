"""Staged Canary Deployment and Rollback Manager.

Implements Part 8 Phase 2:
- Staged canary rollouts (5% -> 25% -> 100%)
- Automated rollback threshold monitoring
- Invariant: Jenna MUST NOT autonomously deploy herself to production
"""

from datetime import datetime, timezone
import uuid

from app.ai.improvement.types import (
    CanaryDeploymentRecord,
    ImprovementProposal,
    ProposalStatus,
    RollbackRecord,
)
from app.core.errors import ForbiddenError, ValidationError
from app.core.logging import logger
from app.events import DomainEvent, DomainEventType, domain_dispatcher


class CanaryManager:
    """Controls canary staging, threshold health evaluation, and rollbacks."""

    def __init__(self) -> None:
        # Active deployments: proposal_id -> CanaryDeploymentRecord
        self._deployments: dict[str, CanaryDeploymentRecord] = {}
        # Rollback history: rollback_id -> RollbackRecord
        self._rollbacks: dict[str, RollbackRecord] = {}

    def deploy_canary(
        self,
        proposal: ImprovementProposal,
        traffic_pct: int = 5,
        approved_by_user: str | None = None,
    ) -> CanaryDeploymentRecord:
        """Deploy proposal to canary pool with explicit human authorization check."""
        # 1. Hard Invariant: Production/canary changes require explicit human approval
        if not approved_by_user and not proposal.approved_by:
            raise ForbiddenError(
                "Autonomous self-deployment forbidden. Explicit human administrator approval is required."
            )

        if proposal.status not in (ProposalStatus.TESTS_PASSED, ProposalStatus.APPROVED):
            raise ValidationError(
                f"Cannot deploy proposal in status '{proposal.status.value}'. Must be TESTS_PASSED or APPROVED."
            )

        record = CanaryDeploymentRecord(
            proposal_id=proposal.proposal_id,
            traffic_percentage=traffic_pct,
            current_error_rate=0.00,
            is_healthy=True,
        )

        proposal.status = ProposalStatus.DEPLOYED_CANARY
        proposal.approved_by = approved_by_user or proposal.approved_by
        proposal.updated_at = datetime.now(timezone.utc)
        self._deployments[proposal.proposal_id] = record

        logger.info(
            f"Deployed proposal '{proposal.proposal_id}' to canary ({traffic_pct}% traffic)",
            extra={"proposal_id": proposal.proposal_id, "approved_by": proposal.approved_by},
        )

        event_uid = None
        if proposal.approved_by:
            try:
                event_uid = uuid.UUID(str(proposal.approved_by))
            except (ValueError, TypeError, AttributeError):
                event_uid = None

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.AI_REQUEST,
                aggregate_id=proposal.proposal_id,
                user_id=event_uid,
                payload={"action": "canary_deployed", "traffic_pct": traffic_pct},
            )
        )


        return record

    def record_canary_telemetry(
        self,
        proposal: ImprovementProposal,
        observed_error_rate: float,
    ) -> tuple[bool, RollbackRecord | None]:
        """Record canary metrics and execute automatic rollback if threshold exceeded."""
        record = self._deployments.get(proposal.proposal_id)
        if not record:
            return True, None

        record.current_error_rate = observed_error_rate

        # Check rollback threshold (e.g. 2% error rate)
        if observed_error_rate > record.error_rate_threshold:
            record.is_healthy = False
            rollback = self.execute_rollback(
                proposal=proposal,
                reason=f"Canary error rate {round(observed_error_rate * 100, 2)}% exceeded threshold {round(record.error_rate_threshold * 100, 2)}%.",
                triggered_by="automated_threshold_monitor",
            )
            return False, rollback

        return True, None

    def execute_rollback(
        self,
        proposal: ImprovementProposal,
        reason: str,
        triggered_by: str = "human_operator",
    ) -> RollbackRecord:
        """Instantly revert proposal changes back to baseline version."""
        rollback = RollbackRecord(
            proposal_id=proposal.proposal_id,
            reason=reason,
            previous_version=proposal.baseline_version,
            rolled_back_at=datetime.now(timezone.utc),
        )

        proposal.status = ProposalStatus.ROLLED_BACK
        proposal.updated_at = datetime.now(timezone.utc)
        self._rollbacks[rollback.rollback_id] = rollback

        if proposal.proposal_id in self._deployments:
            del self._deployments[proposal.proposal_id]

        logger.warning(
            f"Rollback executed for proposal '{proposal.proposal_id}': {reason}",
            extra={"proposal_id": proposal.proposal_id, "reason": reason},
        )

        return rollback

    def promote_to_production(
        self,
        proposal: ImprovementProposal,
        approved_by_user: str,
    ) -> ImprovementProposal:
        """Promote a healthy canary to full 100% production after explicit signoff."""
        if proposal.status != ProposalStatus.DEPLOYED_CANARY:
            raise ValidationError("Only active canary deployments can be promoted to production.")

        proposal.status = ProposalStatus.DEPLOYED_PROD
        proposal.approved_by = approved_by_user
        proposal.updated_at = datetime.now(timezone.utc)

        if proposal.proposal_id in self._deployments:
            self._deployments[proposal.proposal_id].traffic_percentage = 100

        logger.info(
            f"Proposal '{proposal.proposal_id}' promoted to full 100% production by {approved_by_user}"
        )

        return proposal


canary_manager = CanaryManager()
