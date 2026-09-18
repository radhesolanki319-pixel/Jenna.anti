"""Controlled Self-Improvement and Evaluation types, schemas, and governance rules.

Conforms to Part 8 Phase 1 & Phase 2 specifications:
- Observe -> Evaluate -> Propose -> Sandbox -> Test -> Verify -> Approval -> Deploy -> Monitor -> Rollback
- Strict governance: Jenna MUST NOT autonomously rewrite or deploy herself
- Production changes require explicit human approval
- Security rules and permission boundaries cannot be weakened
- Sandboxed execution isolated from production runtime
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    """Lifecycle stages of a self-improvement proposal."""
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    SANDBOX_TESTING = "SANDBOX_TESTING"
    TESTS_PASSED = "TESTS_PASSED"
    TESTS_FAILED = "TESTS_FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    DEPLOYED_CANARY = "DEPLOYED_CANARY"
    DEPLOYED_PROD = "DEPLOYED_PROD"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"


class ImprovementCategory(str, Enum):
    """Target optimization categories for the AI platform."""
    PROMPT_OPTIMIZATION = "PROMPT_OPTIMIZATION"
    MEMORY_RELEVANCE = "MEMORY_RELEVANCE"
    TOOL_EFFICIENCY = "TOOL_EFFICIENCY"
    ROUTING_ACCURACY = "ROUTING_ACCURACY"
    COST_REDUCTION = "COST_REDUCTION"


class BenchmarkTestCase(BaseModel):
    """Benchmark test item for deterministic regression verification."""
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_prompt: str
    expected_contains: list[str] = Field(default_factory=list)
    forbidden_contains: list[str] = Field(default_factory=list)
    max_latency_ms: float = 3000.0


class ImprovementProposal(BaseModel):
    """Structured proposal containing proposed parameter or prompt enhancements."""
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=3, max_length=150)
    category: ImprovementCategory
    rationale: str
    proposed_changes: dict[str, Any] = Field(default_factory=dict)
    baseline_version: str = "v1.0"
    target_version: str = "v1.1-canary"
    status: ProposalStatus = ProposalStatus.PROPOSED
    requires_human_approval: bool = True  # Strict invariant: Never auto-deploy
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SandboxEvaluationResult(BaseModel):
    """Results from testing candidate improvements inside isolated sandbox."""
    eval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    baseline_latency_ms: float = 0.0
    candidate_latency_ms: float = 0.0
    quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    regression_detected: bool = False
    security_check_passed: bool = True
    summary: str = ""
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CanaryDeploymentRecord(BaseModel):
    """Telemetry tracking staged rollout."""
    deployment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    traffic_percentage: int = Field(default=5, ge=1, le=100)
    error_rate_threshold: float = 0.02  # 2% error threshold triggers automatic rollback
    current_error_rate: float = 0.00
    is_healthy: bool = True
    deployed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RollbackRecord(BaseModel):
    """Audit log of an emergency or quality rollback."""
    rollback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    reason: str
    previous_version: str
    rolled_back_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
