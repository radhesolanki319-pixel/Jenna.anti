"""Comprehensive deterministic test suite for Jenna Controlled Self-Improvement & Governance.

Validates Part 8 Phase 1 & Phase 2:
- Governance invariant: Jenna MUST NOT autonomously rewrite or deploy herself
- Production/canary changes mandate explicit human approval
- Security rules and permission checks cannot be weakened by generated changes
- Isolated sandbox regression test runner (sandbox failures cannot affect production)
- Staged canary deployment, automated threshold monitoring, and emergency rollback
- Full HTTP API endpoints flow
"""

import uuid
from httpx import ASGITransport, AsyncClient
import pytest

from app.ai.improvement import (
    CanaryDeploymentRecord,
    ImprovementCategory,
    ImprovementProposal,
    ProposalStatus,
    RollbackRecord,
    canary_manager,
    improvement_sandbox,
    self_improvement_service,
)
from app.core.errors import ForbiddenError, ValidationError
from app.main import app


# ==============================================================================
# 1. Governance & Security Boundary Tests
# ==============================================================================

def test_governance_invariant_no_autonomous_deployment():
    """Verify system strictly rejects autonomous deployment without human approval."""
    proposal = ImprovementProposal(
        title="Candidate model router update",
        category=ImprovementCategory.ROUTING_ACCURACY,
        rationale="Optimize latency for coding queries.",
        status=ProposalStatus.TESTS_PASSED,
        approved_by=None,
    )

    # Attempting deployment without an approving human user MUST raise ForbiddenError
    with pytest.raises(ForbiddenError) as exc:
        canary_manager.deploy_canary(proposal=proposal, traffic_pct=5, approved_by_user=None)
    assert "Autonomous self-deployment forbidden" in str(exc.value)


def test_sandbox_rejects_security_weakening():
    """Verify proposals attempting to lower security or bypass permissions are rejected."""
    malicious_proposal = ImprovementProposal(
        title="Bypass auth to speed up response latency",
        category=ImprovementCategory.PROMPT_OPTIMIZATION,
        rationale="Speed up pipeline.",
        proposed_changes={"skip_permission": True, "allow_all_tools": True},
    )

    eval_result = improvement_sandbox.evaluate_proposal(malicious_proposal)
    assert eval_result.security_check_passed is False
    assert eval_result.regression_detected is True
    assert "Security rejection" in eval_result.summary


# ==============================================================================
# 2. Sandbox Regression & Quality Evaluation Tests
# ==============================================================================

def test_sandbox_evaluates_safe_proposal():
    """Verify legitimate improvements pass benchmarks and advance status."""
    proposal = self_improvement_service.create_proposal(
        title="Tune prompt temperature for concise explanations",
        category=ImprovementCategory.PROMPT_OPTIMIZATION,
        rationale="Improve token economy and response focus.",
        proposed_changes={"temperature": 0.5, "max_output_tokens": 1024},
    )

    res = self_improvement_service.run_sandbox_evaluation(proposal.proposal_id)
    assert res.security_check_passed is True
    assert res.tests_passed >= 2
    assert proposal.status == ProposalStatus.TESTS_PASSED


# ==============================================================================
# 3. Canary Staging, Automated Rollback, & Promotion Tests
# ==============================================================================

def test_canary_staging_and_automatic_rollback_on_error():
    """Verify automated rollback when canary error rate breaches the 2% threshold."""
    proposal = ImprovementProposal(
        proposal_id=str(uuid.uuid4()),
        title="Canary test candidate",
        category=ImprovementCategory.COST_REDUCTION,
        rationale="Cost optimization test.",
        status=ProposalStatus.TESTS_PASSED,
    )

    # Deploy to 10% canary with human admin
    canary_rec = canary_manager.deploy_canary(
        proposal=proposal,
        traffic_pct=10,
        approved_by_user="admin-user-id",
    )
    assert canary_rec.traffic_percentage == 10
    assert proposal.status == ProposalStatus.DEPLOYED_CANARY

    # Record safe error rate (1% <= 2% threshold)
    is_healthy, rollback_none = canary_manager.record_canary_telemetry(proposal, observed_error_rate=0.01)
    assert is_healthy is True
    assert rollback_none is None

    # Error rate spike (5% > 2% threshold) triggers automatic rollback
    is_healthy, rollback = canary_manager.record_canary_telemetry(proposal, observed_error_rate=0.05)
    assert is_healthy is False
    assert rollback is not None
    assert rollback.previous_version == proposal.baseline_version
    assert proposal.status == ProposalStatus.ROLLED_BACK


# ==============================================================================
# 4. Full HTTP API Endpoint Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_self_improvement_http_api_flow():
    """Verify all /api/v1/improvement HTTP endpoints with authenticated session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register test user
        email = f"improve_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg.status_code == 201

        # 2. List proposals
        list_res = await client.get("/api/v1/improvement/proposals")
        assert list_res.status_code == 200
        proposals = list_res.json()
        assert len(proposals) >= 1

        # 3. Create proposal
        create_res = await client.post(
            "/api/v1/improvement/proposals",
            json={
                "title": "Enhance memory retrieval scoring weights",
                "category": "MEMORY_RELEVANCE",
                "rationale": "Boost recency weighting by 10%.",
                "proposed_changes": {"recency_weight": 0.35},
            },
        )
        assert create_res.status_code == 200
        prop = create_res.json()
        prop_id = prop["proposal_id"]
        assert prop["requires_human_approval"] is True

        # 4. Run Sandbox Evaluation
        eval_res = await client.post(f"/api/v1/improvement/proposals/{prop_id}/sandbox-eval")
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["security_check_passed"] is True
        assert eval_data["quality_score"] > 0

        # 5. Human Signoff / Approve
        approve_res = await client.post(f"/api/v1/improvement/proposals/{prop_id}/approve")
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "APPROVED"

        # 6. Deploy to 10% Canary
        canary_res = await client.post(
            f"/api/v1/improvement/proposals/{prop_id}/deploy-canary",
            json={"traffic_percentage": 10},
        )
        assert canary_res.status_code == 200
        assert canary_res.json()["traffic_percentage"] == 10

        # 7. Promote to 100% Production
        promote_res = await client.post(f"/api/v1/improvement/proposals/{prop_id}/promote")
        assert promote_res.status_code == 200
        assert promote_res.json()["status"] == "DEPLOYED_PROD"

        # 8. Rollback
        rollback_res = await client.post(
            f"/api/v1/improvement/proposals/{prop_id}/rollback",
            json={"reason": "Reverting back to baseline for verification."},
        )
        assert rollback_res.status_code == 200
        rb_data = rollback_res.json()
        assert rb_data["proposal_id"] == prop_id
