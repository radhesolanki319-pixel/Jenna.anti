"""Relevance scoring engine for ranking memories during semantic retrieval."""

from datetime import datetime, timezone
import math
from typing import NamedTuple


class ScoringWeights(NamedTuple):
    similarity: float = 0.5
    importance: float = 0.2
    recency: float = 0.2
    confidence: float = 0.1


DEFAULT_WEIGHTS = ScoringWeights()


class RelevanceScorer:
    """Computes multidimensional relevance scores combining semantic similarity,

    explicit importance, temporal recency decay, and extraction confidence.
    """

    @staticmethod
    def calculate_recency(
        timestamp: datetime,
        reference_time: datetime | None = None,
        half_life_days: float = 7.0,
    ) -> float:
        """Calculate exponential recency score in [0.0, 1.0] with configurable half-life."""
        ref = reference_time or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        delta_seconds = max(0.0, (ref - timestamp).total_seconds())
        delta_days = delta_seconds / 86400.0
        # Exponential decay: 2^(-delta_days / half_life)
        return math.pow(0.5, delta_days / half_life_days)

    @classmethod
    def compute_score(
        cls,
        similarity: float,
        importance: float,
        confidence: float,
        timestamp: datetime,
        weights: ScoringWeights = DEFAULT_WEIGHTS,
        reference_time: datetime | None = None,
    ) -> tuple[float, dict[str, float]]:
        """Compute compound score and individual factor breakdown."""
        sim = max(0.0, min(1.0, float(similarity)))
        imp = max(0.0, min(1.0, float(importance)))
        conf = max(0.0, min(1.0, float(confidence)))
        rec = cls.calculate_recency(timestamp, reference_time)

        total_weight = weights.similarity + weights.importance + weights.recency + weights.confidence
        if total_weight <= 0:
            total_weight = 1.0

        raw_score = (
            (weights.similarity * sim)
            + (weights.importance * imp)
            + (weights.recency * rec)
            + (weights.confidence * conf)
        ) / total_weight

        compound_score = max(0.0, min(1.0, raw_score))

        breakdown = {
            "similarity": sim,
            "importance": imp,
            "recency": rec,
            "confidence": conf,
            "compound_score": compound_score,
        }

        return compound_score, breakdown
