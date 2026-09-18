"""Memory lifecycle state management and retention policies."""

from datetime import datetime, timedelta, timezone
import enum
from typing import NamedTuple
from app.models.memory import Memory, MemoryStatus, MemoryType


class LifecycleAction(str, enum.Enum):
    """Actions performed on memory lifecycle."""

    ACTIVATE = "ACTIVATE"
    SUPERSEDE = "SUPERSEDE"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    DELETE = "DELETE"


class RetentionRecommendation(NamedTuple):
    """Outcome of retention evaluation on a memory record."""

    should_retain: bool
    recommended_action: LifecycleAction | None
    reason: str


class MemoryLifecycleManager:
    """Manages memory lifecycle transitions and retention rules.

    Valid lifecycle transitions:
    - CANDIDATE  -> ACTIVE, DELETED
    - ACTIVE     -> SUPERSEDED, ARCHIVED, DELETED
    - SUPERSEDED -> ACTIVE, ARCHIVED, DELETED
    - ARCHIVED   -> ACTIVE, DELETED
    - DELETED    -> (Terminal state; soft-deleted records are never retrieved)
    """

    VALID_TRANSITIONS: dict[str, set[str]] = {
        MemoryStatus.CANDIDATE.value: {
            MemoryStatus.ACTIVE.value,
            MemoryStatus.DELETED.value,
        },
        MemoryStatus.ACTIVE.value: {
            MemoryStatus.SUPERSEDED.value,
            MemoryStatus.ARCHIVED.value,
            MemoryStatus.DELETED.value,
        },
        MemoryStatus.SUPERSEDED.value: {
            MemoryStatus.ACTIVE.value,
            MemoryStatus.ARCHIVED.value,
            MemoryStatus.DELETED.value,
        },
        MemoryStatus.ARCHIVED.value: {
            MemoryStatus.ACTIVE.value,
            MemoryStatus.DELETED.value,
        },
        MemoryStatus.DELETED.value: set(),
    }

    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        """Check if lifecycle transition is legally permitted."""
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def evaluate_retention(
        cls,
        memory: Memory,
        stale_threshold_days: int = 90,
        now: datetime | None = None,
    ) -> RetentionRecommendation:
        """Evaluate retention policy on an existing memory.

        Rules:
        - Already DELETED memories are excluded.
        - High-importance memories (>= 0.70) are NEVER auto-archived.
        - TEMPORARY memories older than 7 days should be ARCHIVED or DELETED.
        - Memories with low importance (< 0.35) unaccessed for stale_threshold_days are candidates for ARCHIVE.
        """
        if memory.status == MemoryStatus.DELETED.value:
            return RetentionRecommendation(
                should_retain=False,
                recommended_action=None,
                reason="Memory is already deleted.",
            )

        current_time = now or datetime.now(timezone.utc)

        # Temporary memory expiration (7 days)
        if memory.memory_type == MemoryType.TEMPORARY.value:
            age = current_time - (memory.created_at or current_time)
            if age > timedelta(days=7):
                return RetentionRecommendation(
                    should_retain=False,
                    recommended_action=LifecycleAction.ARCHIVE,
                    reason="Temporary memory exceeded 7-day retention period.",
                )

        # High importance protection
        if memory.importance >= 0.70:
            return RetentionRecommendation(
                should_retain=True,
                recommended_action=None,
                reason="Protected from archival due to high importance.",
            )

        # Stale memory evaluation
        last_accessed = memory.last_accessed_at or memory.created_at or current_time
        idle_time = current_time - last_accessed

        if idle_time > timedelta(days=stale_threshold_days) and memory.importance < 0.35:
            return RetentionRecommendation(
                should_retain=False,
                recommended_action=LifecycleAction.ARCHIVE,
                reason=f"Memory has low utility (<0.35) and has been unaccessed for {idle_time.days} days.",
            )

        return RetentionRecommendation(
            should_retain=True,
            recommended_action=None,
            reason="Memory remains within active retention bounds.",
        )
