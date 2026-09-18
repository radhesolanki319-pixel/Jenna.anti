"""Response Quality Validation and Sanity Engine."""

import re
from typing import Tuple


class ResponseValidator:
    """Validates generated LLM responses for quality, completeness, and non-repetition."""

    @staticmethod
    def validate(text: str) -> Tuple[bool, str | None]:
        """Verify that the response is coherent, non-empty, and free of degenerate repetition loops.

        Returns:
            (True, None) if valid.
            (False, error_reason) if invalid.
        """
        if not text or not text.strip():
            return False, "Response is empty or whitespace only."

        clean = text.strip()

        # 1. Minimum sanity length
        if len(clean) < 2:
            return False, "Response is too short to be meaningful."

        # 2. Check for excessive sentence repetition (e.g. model gets stuck in a loop)
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", clean) if len(s.strip()) > 8]
        if len(sentences) >= 4:
            counts: dict[str, int] = {}
            for s in sentences:
                counts[s] = counts.get(s, 0) + 1
                if counts[s] >= 4:
                    return False, f"Degenerate repetition detected: sentence repeated {counts[s]} times."

        # 3. Check for n-gram token loop (e.g. 'the same the same the same...')
        words = clean.lower().split()
        if len(words) >= 12:
            # Check 3-gram repetitions
            trigrams = [tuple(words[i : i + 3]) for i in range(len(words) - 2)]
            tri_counts: dict[tuple, int] = {}
            for tg in trigrams:
                tri_counts[tg] = tri_counts.get(tg, 0) + 1
                if tri_counts[tg] >= 6:
                    return False, "Degenerate n-gram repetition loop detected."

        return True, None

    @staticmethod
    def sanitize(text: str) -> str:
        """Clean leading/trailing noise, redundant consecutive blank lines, or artifacts."""
        if not text:
            return ""
        # Collapse > 2 consecutive newlines into 2
        clean = re.sub(r"\n{3,}", "\n\n", text)
        return clean.strip()
