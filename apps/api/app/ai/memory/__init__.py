"""Intelligent Memory subsystem package."""

from app.ai.memory.deduplication import (
    ComparisonRelation,
    DeduplicationResult,
    MemoryDeduplicator,
)
from app.ai.memory.extractor import MemoryExtractor
from app.ai.memory.lifecycle import (
    LifecycleAction,
    MemoryLifecycleManager,
    RetentionRecommendation,
)
from app.ai.memory.policy import (
    ImportanceLevel,
    MemoryPolicy,
    PolicyDecision,
)
from app.ai.memory.privacy import (
    PrivacyCheckResult,
    PrivacyFilter,
)
from app.ai.memory.relevance import (
    DEFAULT_WEIGHTS,
    RelevanceScorer,
    ScoringWeights,
)
from app.ai.memory.working_memory import (
    WorkingMemoryManager,
    working_memory_manager,
)

__all__ = [
    "ComparisonRelation",
    "DeduplicationResult",
    "MemoryDeduplicator",
    "MemoryExtractor",
    "LifecycleAction",
    "MemoryLifecycleManager",
    "RetentionRecommendation",
    "ImportanceLevel",
    "MemoryPolicy",
    "PolicyDecision",
    "PrivacyCheckResult",
    "PrivacyFilter",
    "DEFAULT_WEIGHTS",
    "RelevanceScorer",
    "ScoringWeights",
    "WorkingMemoryManager",
    "working_memory_manager",
]
