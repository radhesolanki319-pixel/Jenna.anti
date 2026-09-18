"""Voice Activity Detection (VAD), turn boundary detection, and interruption engine.

Implements Part 6 Phase 1:
- Turn detection where supported
- Interruption / stop speaking logic
- Clear recording and speaking state transitions
"""

import math
from app.ai.voice.types import TurnDetectionResult, VoiceTurnState


class VoiceTurnDetector:
    """Evaluates audio chunks to compute voice activity, turn completion, and interruptions."""

    def __init__(
        self,
        energy_threshold: float = 0.015,
        silence_timeout_ms: float = 600.0,
        min_speech_duration_ms: float = 200.0,
    ) -> None:
        self.energy_threshold = energy_threshold
        self.silence_timeout_ms = silence_timeout_ms
        self.min_speech_duration_ms = min_speech_duration_ms

    def calculate_rms(self, pcm_data: bytes) -> float:
        """Calculate Root Mean Square (RMS) audio energy of 16-bit PCM bytes."""
        if not pcm_data or len(pcm_data) < 2:
            return 0.0

        # Sample count for 16-bit signed little-endian PCM
        count = len(pcm_data) // 2
        sum_squares = 0.0

        for i in range(0, count * 2, 2):
            sample = int.from_bytes(pcm_data[i : i + 2], byteorder="little", signed=True)
            normalized = sample / 32768.0
            sum_squares += normalized * normalized

        mean_square = sum_squares / max(1, count)
        return math.sqrt(mean_square)

    def analyze_chunk(
        self,
        chunk: bytes,
        current_state: VoiceTurnState,
        accumulated_silence_ms: float = 0.0,
        chunk_duration_ms: float = 100.0,
    ) -> TurnDetectionResult:
        """Analyze an incoming audio segment."""
        rms = self.calculate_rms(chunk)
        is_speech = rms >= self.energy_threshold

        # Speech probability estimation based on threshold margin
        speech_prob = min(1.0, rms / max(0.001, self.energy_threshold * 2.0))

        if is_speech:
            new_silence_ms = 0.0
        else:
            new_silence_ms = accumulated_silence_ms + chunk_duration_ms

        # Turn completion: user was speaking, and has now been silent longer than threshold
        is_turn_complete = (
            current_state == VoiceTurnState.LISTENING
            and not is_speech
            and new_silence_ms >= self.silence_timeout_ms
        )

        # Interruption: Jenna is actively speaking, but incoming audio contains confident user speech
        should_interrupt = (
            current_state == VoiceTurnState.SPEAKING
            and is_speech
            and speech_prob > 0.5
        )

        return TurnDetectionResult(
            is_speech=is_speech,
            speech_probability=speech_prob,
            silence_duration_ms=new_silence_ms,
            is_turn_complete=is_turn_complete,
            should_interrupt=should_interrupt,
        )
