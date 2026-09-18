"""Memory deduplication, comparison, and conflict resolution."""

import enum
import re
from typing import NamedTuple, Sequence
import uuid
from app.models.memory import Memory, MemoryType


class ComparisonRelation(str, enum.Enum):
    """Categorization of comparison between candidate and existing memory."""

    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    RELATED = "RELATED"
    GENUINELY_NEW = "GENUINELY_NEW"


class DeduplicationResult(NamedTuple):
    """Outcome of deduplication evaluation."""

    relation: ComparisonRelation
    matched_memory_id: uuid.UUID | None
    similarity_score: float
    recommended_action: str  # "STORE", "SUPERSEDE", "UPDATE", "IGNORE"
    reason: str


class MemoryDeduplicator:
    """Detects duplicates, contradictions/conflicts, and related memories."""

    # Common contradictory pairs for quick conflict detection
    CONTRADICTORY_PAIRS = [
        ({"dark", "dark mode"}, {"light", "light mode"}),
        ({"concise", "short", "brief"}, {"detailed", "verbose", "comprehensive"}),
        ({"mac", "macos"}, {"windows", "linux"}),
        ({"morning"}, {"evening", "night"}),
        ({"vegetarian", "vegan"}, {"meat", "non-vegetarian", "omnivore"}),
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalize text by lowercasing, stripping punctuation, and compressing spaces."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def compute_lexical_similarity(cls, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity over word tokens."""
        tokens1 = set(cls.normalize_text(text1).split())
        tokens2 = set(cls.normalize_text(text2).split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    @classmethod
    def detect_attribute_conflict(cls, text1: str, text2: str) -> bool:
        """Check whether two texts contain conflicting attribute values."""
        norm1 = cls.normalize_text(text1)
        norm2 = cls.normalize_text(text2)

        for set_a, set_b in cls.CONTRADICTORY_PAIRS:
            in_a_1 = any(term in norm1 for term in set_a)
            in_b_1 = any(term in norm1 for term in set_b)
            in_a_2 = any(term in norm2 for term in set_a)
            in_b_2 = any(term in norm2 for term in set_b)

            if (in_a_1 and in_b_2) or (in_b_1 and in_a_2):
                return True

        return False

    @classmethod
    def compare_with_existing(
        cls,
        candidate_content: str,
        candidate_type: str,
        existing_memories: Sequence[Memory],
        semantic_similarities: dict[uuid.UUID, float] | None = None,
    ) -> DeduplicationResult:
        """Compare a candidate against existing active memories.

        Determines whether it is DUPLICATE, CONFLICT, RELATED, or GENUINELY_NEW.
        """
        if not existing_memories:
            return DeduplicationResult(
                relation=ComparisonRelation.GENUINELY_NEW,
                matched_memory_id=None,
                similarity_score=0.0,
                recommended_action="STORE",
                reason="No existing memories found for comparison.",
            )

        best_score = 0.0
        best_match: Memory | None = None
        best_relation = ComparisonRelation.GENUINELY_NEW
        best_reason = "Unique information."

        norm_candidate = cls.normalize_text(candidate_content)

        for mem in existing_memories:
            norm_existing = cls.normalize_text(mem.content)

            # Exact text match
            if norm_candidate == norm_existing:
                return DeduplicationResult(
                    relation=ComparisonRelation.DUPLICATE,
                    matched_memory_id=mem.id,
                    similarity_score=1.0,
                    recommended_action="IGNORE",
                    reason="Exact duplicate of existing active memory.",
                )

            # Lexical similarity
            lexical_sim = cls.compute_lexical_similarity(candidate_content, mem.content)

            # Semantic similarity if provided by vector search
            sem_sim = 0.0
            if semantic_similarities and mem.id in semantic_similarities:
                sem_sim = semantic_similarities[mem.id]

            # Combined similarity estimate
            effective_sim = max(lexical_sim, sem_sim)

            # 1. High similarity (> 0.85) -> DUPLICATE
            if effective_sim > 0.85 and mem.memory_type == candidate_type:
                return DeduplicationResult(
                    relation=ComparisonRelation.DUPLICATE,
                    matched_memory_id=mem.id,
                    similarity_score=effective_sim,
                    recommended_action="IGNORE",
                    reason=f"Substantially duplicate ({effective_sim:.2f} similarity) to existing memory.",
                )

            # 2. Check for Contradiction / Conflict
            is_conflict = cls.detect_attribute_conflict(candidate_content, mem.content)
            if is_conflict and (effective_sim > 0.3 or mem.memory_type == candidate_type):
                return DeduplicationResult(
                    relation=ComparisonRelation.CONFLICT,
                    matched_memory_id=mem.id,
                    similarity_score=effective_sim,
                    recommended_action="SUPERSEDE",
                    reason="Conflicting preference detected with existing memory; recommending supersession.",
                )

            # 3. Track best related memory
            if effective_sim > best_score:
                best_score = effective_sim
                best_match = mem

        # Evaluate best match
        if best_match and best_score >= 0.50:
            return DeduplicationResult(
                relation=ComparisonRelation.RELATED,
                matched_memory_id=best_match.id,
                similarity_score=best_score,
                recommended_action="STORE",
                reason=f"Related to existing memory '{best_match.id}' ({best_score:.2f} similarity).",
            )

        return DeduplicationResult(
            relation=ComparisonRelation.GENUINELY_NEW,
            matched_memory_id=None,
            similarity_score=best_score,
            recommended_action="STORE",
            reason=best_reason,
        )
