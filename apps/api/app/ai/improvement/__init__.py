"""Controlled Self-Improvement and Governance package."""

from app.ai.improvement.canary_manager import canary_manager, CanaryManager
from app.ai.improvement.sandbox import improvement_sandbox, ImprovementSandbox
from app.ai.improvement.service import self_improvement_service, SelfImprovementService
from app.ai.improvement.types import (
    BenchmarkTestCase,
    CanaryDeploymentRecord,
    ImprovementCategory,
    ImprovementProposal,
    ProposalStatus,
    RollbackRecord,
    SandboxEvaluationResult,
)

__all__ = [
    "self_improvement_service",
    "SelfImprovementService",
    "improvement_sandbox",
    "ImprovementSandbox",
    "canary_manager",
    "CanaryManager",
    "BenchmarkTestCase",
    "CanaryDeploymentRecord",
    "ImprovementCategory",
    "ImprovementProposal",
    "ProposalStatus",
    "RollbackRecord",
    "SandboxEvaluationResult",
]
