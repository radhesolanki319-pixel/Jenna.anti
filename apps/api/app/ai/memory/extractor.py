"""Candidate memory extraction engine."""

import logging
import re
import uuid
from typing import Sequence
from app.ai.memory.policy import MemoryPolicy
from app.ai.memory.privacy import PrivacyFilter
from app.models.memory import MemorySource, MemoryType
from app.schemas.memory import CandidateAction, MemoryCandidate, SensitivityClassification

logger = logging.getLogger("jenna.memory.extractor")


class MemoryExtractor:
    """Analyzes conversational turns or text to identify candidate long-term memories.

    Separates extraction from persistence.
    """

    # Explicit extraction regexes with capture groups for payload
    EXPLICIT_PATTERNS = [
        (
            re.compile(
                r"\b(?:please\s+)?(?:remember\s+(?:that|this)?|don't\s+forget\s+(?:that)?|make\s+a\s+note\s+that)\s*[:,-]?\s*(.+)",
                re.IGNORECASE,
            ),
            MemorySource.USER_EXPLICIT.value,
        ),
        (
            re.compile(
                r"\b(?:yaad\s+rakhna|ye\s+yaad\s+rakhna|isko\s+yaad\s+rakhna|dhyan\s+rakhna)\s*(?:ki)?\s*[:,-]?\s*(.+)",
                re.IGNORECASE,
            ),
            MemorySource.USER_EXPLICIT.value,
        ),
    ]

    # Preference patterns
    PREFERENCE_PATTERNS = [
        re.compile(r"\b(?:i\s+prefer|i\s+like|i\s+love|i\s+always\s+want|i\s+favour|my\s+preference\s+is)\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:i\s+hate|i\s+dislike|i\s+don't\s+like|i\s+never\s+want)\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:mera\s+preference|mujhe\s+pasand\s+hai|meri\s+pasand\s+hai)\s+(.+)", re.IGNORECASE),
    ]

    # Personal Context patterns
    PERSONAL_PATTERNS = [
        re.compile(r"\b(?:my\s+name\s+is|call\s+me|i\s+am\s+called)\s+([A-Za-z0-9_\-\s]{2,40})", re.IGNORECASE),
        re.compile(r"\b(?:i\s+live\s+in|i'm\s+based\s+in|i\s+am\s+from|my\s+city\s+is)\s+([A-Za-z0-9_\-,\s]{2,60})", re.IGNORECASE),
        re.compile(r"\b(?:i\s+work\s+as|i\s+am\s+a|my\s+job\s+is|my\s+role\s+is)\s+([A-Za-z0-9_\-\s]{2,60})", re.IGNORECASE),
        re.compile(r"\b(?:my\s+(?:dog|cat|pet|wife|husband|daughter|son|partner|friend)'s\s+name\s+is|i\s+have\s+a\s+(?:dog|cat|pet)\s+named)\s+([A-Za-z0-9_\-\s]{2,40})", re.IGNORECASE),
    ]

    # Instruction patterns
    INSTRUCTION_PATTERNS = [
        re.compile(r"\b(?:always\s+(?:respond|answer|reply|write)|never\s+(?:use|say|reply))\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:keep\s+your\s+answers\s+(?:concise|short|detailed|formal|friendly))\b", re.IGNORECASE),
    ]

    @classmethod
    def extract_candidates(
        cls,
        text: str,
        conversation_id: uuid.UUID | None = None,
    ) -> list[MemoryCandidate]:
        """Extract memory candidates from conversational input."""
        candidates: list[MemoryCandidate] = []
        cleaned = text.strip()
        if not cleaned:
            return candidates

        # 1. Check for explicit memory requests first
        for pattern, src in cls.EXPLICIT_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                payload = match.group(1).strip().rstrip(".!?,")
                if payload:
                    candidates.append(
                        cls._build_candidate(
                            raw_content=payload,
                            source=src,
                            is_explicit=True,
                            conversation_id=conversation_id,
                        )
                    )
                # If explicit request found, return immediately or continue
                return candidates

        # 2. Check for preferences
        for pattern in cls.PREFERENCE_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                payload = match.group(0).strip().rstrip(".!?,")
                candidates.append(
                    cls._build_candidate(
                        raw_content=payload,
                        source=MemorySource.USER_CONVERSATION.value,
                        memory_type=MemoryType.PREFERENCE.value,
                        base_importance=0.6,
                        conversation_id=conversation_id,
                    )
                )
                break

        # 3. Check for personal context
        for pattern in cls.PERSONAL_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                payload = match.group(0).strip().rstrip(".!?,")
                candidates.append(
                    cls._build_candidate(
                        raw_content=payload,
                        source=MemorySource.USER_CONVERSATION.value,
                        memory_type=MemoryType.PERSONAL_CONTEXT.value,
                        base_importance=0.65,
                        conversation_id=conversation_id,
                    )
                )
                break

        # 4. Check for system/assistant instructions
        for pattern in cls.INSTRUCTION_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                payload = match.group(0).strip().rstrip(".!?,")
                candidates.append(
                    cls._build_candidate(
                        raw_content=payload,
                        source=MemorySource.USER_CONVERSATION.value,
                        memory_type=MemoryType.INSTRUCTION.value,
                        base_importance=0.7,
                        conversation_id=conversation_id,
                    )
                )
                break

        return candidates

    @classmethod
    def _build_candidate(
        cls,
        raw_content: str,
        source: str,
        memory_type: str | None = None,
        base_importance: float = 0.5,
        base_confidence: float = 0.85,
        is_explicit: bool = False,
        conversation_id: uuid.UUID | None = None,
    ) -> MemoryCandidate:
        """Construct structured candidate with privacy filter and policy evaluation."""
        # 1. Run Privacy Filter
        privacy_result = PrivacyFilter.check_text(raw_content)

        # 2. Infer memory type if not specified
        m_type = memory_type
        if not m_type:
            lower = raw_content.lower()
            if any(k in lower for k in ("prefer", "like", "love", "favorite", "favourite", "want", "pasand")):
                m_type = MemoryType.PREFERENCE.value
            elif any(k in lower for k in ("always", "never", "concise", "detailed", "rule", "instruction")):
                m_type = MemoryType.INSTRUCTION.value
            elif any(k in lower for k in ("name is", "live in", "work as", "my wife", "my son", "my dog")):
                m_type = MemoryType.PERSONAL_CONTEXT.value
            else:
                m_type = MemoryType.FACT.value

        # 3. Evaluate Policy
        decision = MemoryPolicy.evaluate_candidate(
            content=raw_content,
            memory_type=m_type,
            base_importance=base_importance,
            base_confidence=base_confidence,
            is_explicit=is_explicit,
            sensitivity=privacy_result.classification,
        )

        return MemoryCandidate(
            content=raw_content,
            memory_type=m_type,
            importance=decision.computed_importance,
            confidence=decision.computed_confidence,
            reason=decision.reason,
            source=source,
            sensitivity=privacy_result.classification,
            suggested_action=decision.action,
            conversation_id=conversation_id,
        )
