"""Silence Intelligence & Turn-Taking Engine for Jenna AI Voice.

Distinguishes between:
1. Thinking / hesitation pauses (e.g. "Wait, umm...", 1-2s breathing pauses).
2. Intentional turn completion (natural question or finished thought).
3. Ambient background room silence.

Prevents awkward premature interruptions and ensures instant response when the user finishes speaking.
"""

import logging
import math
import re
from typing import Any

logger = logging.getLogger("jenna.voice.silence_intelligence")

HESITATION_WORDS = {
    "umm", "um", "uh", "uhh", "er", "ah", "hmm",
    "matlab", "arre", "waise", "aur", "ya", "toh", "ki", "par",
    "so", "like", "wait", "actually", "basically", "and", "then", "but", "or",
}

TRAILING_CONJUNCTIONS = {
    "aur", "ya", "ki", "lekin", "par", "magar", "kyunki", "jab", "agar",
    "and", "or", "but", "if", "because", "so", "that", "which", "where",
    "to", "for", "with", "in", "on", "at",
}


class SilenceIntelligenceService:
    """Intelligent voice activity & conversational pause analyzer."""

    def __init__(
        self,
        base_silence_threshold_ms: float = 650.0,
        hesitation_extended_ms: float = 2200.0,
        energy_threshold: float = 0.015,
    ) -> None:
        self.base_silence_threshold_ms = base_silence_threshold_ms
        self.hesitation_extended_ms = hesitation_extended_ms
        self.energy_threshold = energy_threshold

    def calculate_pcm_rms(self, pcm_data: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy of 16-bit PCM bytes."""
        if not pcm_data or len(pcm_data) < 2:
            return 0.0
        count = len(pcm_data) // 2
        sum_sq = 0.0
        for i in range(0, count * 2, 2):
            sample = int.from_bytes(pcm_data[i : i + 2], byteorder="little", signed=True)
            norm = sample / 32768.0
            sum_sq += norm * norm
        return math.sqrt(sum_sq / max(1, count))

    def analyze_silence(
        self,
        transcript: str,
        silence_duration_ms: float,
        pcm_energy: float = 0.0,
    ) -> dict[str, Any]:
        """Classify current pause into HOLD_TURN, SPEAK_NOW, or IDLE_LISTEN."""
        clean_text = transcript.strip().lower()

        if not clean_text:
            return {
                "decision": "IDLE_LISTEN",
                "is_hesitation": False,
                "can_respond": False,
                "remaining_wait_ms": max(0.0, self.base_silence_threshold_ms - silence_duration_ms),
                "reason": "No speech detected in buffer.",
            }

        words = re.findall(r"\b[a-zA-Z\u0900-\u097F]+\b", clean_text)
        last_word = words[-1] if words else ""

        # Check 1: Trailing hesitation words or conjunctions
        is_hesitation = (
            last_word in HESITATION_WORDS
            or last_word in TRAILING_CONJUNCTIONS
            or clean_text.endswith("...")
            or clean_text.endswith(",")
        )

        # Check 2: Trailing complete punctuation
        is_complete_punctuation = (
            clean_text.endswith("?")
            or clean_text.endswith("!")
            or clean_text.endswith(".")
        )

        # Determine required silence duration
        if is_hesitation:
            required_silence_ms = self.hesitation_extended_ms
        elif is_complete_punctuation or len(words) >= 4:
            required_silence_ms = self.base_silence_threshold_ms
        else:
            required_silence_ms = self.base_silence_threshold_ms * 1.2

        can_respond = silence_duration_ms >= required_silence_ms
        decision = "SPEAK_NOW" if can_respond else "HOLD_TURN"

        if is_hesitation and not can_respond:
            reason = f"User paused on hesitation word '{last_word}'. Holding turn to avoid interruption."
        elif can_respond:
            reason = f"Thought completed with {silence_duration_ms:.0f}ms silence. Ready to respond."
        else:
            reason = f"Listening... accumulated {silence_duration_ms:.0f}ms / {required_silence_ms:.0f}ms silence."

        return {
            "decision": decision,
            "can_respond": can_respond,
            "is_hesitation": is_hesitation,
            "last_word": last_word,
            "silence_duration_ms": silence_duration_ms,
            "required_silence_ms": required_silence_ms,
            "remaining_wait_ms": max(0.0, required_silence_ms - silence_duration_ms),
            "reason": reason,
        }


silence_intelligence_service = SilenceIntelligenceService()
