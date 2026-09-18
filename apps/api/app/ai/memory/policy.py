"""Memory extraction and persistence policies."""

import enum
import re
from typing import NamedTuple
from app.models.memory import MemoryType
from app.schemas.memory import CandidateAction, SensitivityClassification


class ImportanceLevel(str, enum.Enum):
    """Categorized importance levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PolicyDecision(NamedTuple):
    """Result of policy evaluation on candidate memory."""

    action: CandidateAction
    importance_level: ImportanceLevel
    computed_importance: float
    computed_confidence: float
    reason: str


class MemoryPolicy:
    """Configurable policy determining candidate eligibility for persistence.

    Enforces:
    - Rejection of trivial or conversational chatter.
    - Automatic rejection of sensitive credentials.
    - Promotion of explicit user remember requests.
    - Differentiation between durable long-term memories and temporary task notes.
    """

    TRIVIAL_WORDS = {
        "hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon",
        "ok", "okay", "cool", "awesome", "great", "sounds good", "alright", "thanks", "thank you",
        "bye", "see ya", "how are you", "what's up", "how's it going", "yes", "no", "yep", "nope",
        "sure", "definitely", "ok thanks", "thanks ok",
    }

    # Trivial phrases that should NEVER be turned into persistent long-term memories
    TRIVIAL_PATTERNS = [
        re.compile(r"^(?:hello|hi|hey|greetings|good\s+(?:morning|afternoon|evening))\b", re.IGNORECASE),
        re.compile(r"^(?:ok|okay|cool|awesome|great|sounds good|alright|thanks|thank you|bye|see ya)\b", re.IGNORECASE),
        re.compile(r"^(?:how are you|what's up|how's it going|who are you)\??$", re.IGNORECASE),
        re.compile(r"^(?:yes|no|yep|nope|sure|definitely)\.?$", re.IGNORECASE),
    ]

    # Explicit memory triggers indicating user intention to store
    EXPLICIT_TRIGGERS = [
        re.compile(r"\b(?:remember\s+(?:this|that|to)?|don't\s+forget\s+(?:this|that)?|keep\s+in\s+mind)\b", re.IGNORECASE),
        re.compile(r"\b(?:make\s+a\s+note\s+(?:of|that)?|store\s+this|save\s+this)\b", re.IGNORECASE),
        re.compile(r"\b(?:yaad\s+rakhna|isko\s+yaad\s+rakhna|ye\s+yaad\s+rakhna|dhyan\s+rakhna)\b", re.IGNORECASE),
    ]

    @classmethod
    def is_trivial(cls, text: str) -> bool:
        """Check if candidate content is trivial chit-chat."""
        cleaned = re.sub(r"[^\w\s]", "", text.strip().lower()).strip()
        if len(cleaned) < 4:
            return True
        if cleaned in cls.TRIVIAL_WORDS:
            return True
        words = set(cleaned.split())
        trivial_single_words = {"hello", "hi", "hey", "ok", "okay", "cool", "thanks", "bye", "sure", "great", "awesome"}
        if words and words.issubset(trivial_single_words):
            return True
        for pattern in cls.TRIVIAL_PATTERNS:
            if pattern.search(cleaned):
                return True
        return False

    @classmethod
    def has_explicit_trigger(cls, text: str) -> bool:
        """Detect if text contains explicit memory request keywords."""
        for pattern in cls.EXPLICIT_TRIGGERS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def evaluate_candidate(
        cls,
        content: str,
        memory_type: str,
        base_importance: float = 0.5,
        base_confidence: float = 0.8,
        is_explicit: bool = False,
        sensitivity: SensitivityClassification = SensitivityClassification.SAFE,
    ) -> PolicyDecision:
        """Evaluate whether an extracted candidate should be stored, confirmed, or ignored."""
        # 1. Strict Security: sensitive credentials must ALWAYS be ignored
        if sensitivity in (
            SensitivityClassification.SENSITIVE_CREDENTIAL,
            SensitivityClassification.HIGH_RISK,
        ):
            return PolicyDecision(
                action=CandidateAction.IGNORE,
                importance_level=ImportanceLevel.LOW,
                computed_importance=0.0,
                computed_confidence=0.0,
                reason="Rejected: Contains sensitive credentials or security secrets.",
            )

        # 2. Filter trivial small-talk
        if cls.is_trivial(content):
            return PolicyDecision(
                action=CandidateAction.IGNORE,
                importance_level=ImportanceLevel.LOW,
                computed_importance=0.1,
                computed_confidence=0.2,
                reason="Ignored: Trivial conversation or generic greeting.",
            )

        # 3. Calculate adjusted importance & confidence
        importance = base_importance
        confidence = base_confidence

        if is_explicit or cls.has_explicit_trigger(content):
            importance = min(1.0, importance + 0.3)
            confidence = min(1.0, confidence + 0.2)
            reason = "Explicit user request to remember durable information."
        elif memory_type in (MemoryType.PREFERENCE.value, MemoryType.INSTRUCTION.value):
            importance = min(1.0, importance + 0.15)
            reason = f"Identified durable user {memory_type.lower()}."
        elif memory_type == MemoryType.PERSONAL_CONTEXT.value:
            importance = min(1.0, importance + 0.1)
            reason = "Identified durable personal context."
        elif memory_type == MemoryType.TEMPORARY.value:
            importance = max(0.2, importance - 0.2)
            reason = "Identified transient/temporary context."
        else:
            reason = "Identified factual conversation knowledge."

        # Importance classification
        if importance >= 0.70:
            level = ImportanceLevel.HIGH
        elif importance >= 0.40:
            level = ImportanceLevel.MEDIUM
        else:
            level = ImportanceLevel.LOW

        # 4. Determine Suggested Action
        # Very low importance (< 0.25) without explicit user trigger should be ignored
        if importance < 0.25 and not is_explicit:
            return PolicyDecision(
                action=CandidateAction.IGNORE,
                importance_level=level,
                computed_importance=importance,
                computed_confidence=confidence,
                reason="Ignored: Information utility below retention threshold.",
            )

        # Sensitive personal details (e.g. family, medical, address) may require confirmation if configured
        if sensitivity == SensitivityClassification.SENSITIVE_PERSONAL:
            return PolicyDecision(
                action=CandidateAction.CONFIRM,
                importance_level=level,
                computed_importance=importance,
                computed_confidence=confidence,
                reason="Requires confirmation: Sensitive personal context.",
            )

        return PolicyDecision(
            action=CandidateAction.STORE,
            importance_level=level,
            computed_importance=importance,
            computed_confidence=confidence,
            reason=reason,
        )
