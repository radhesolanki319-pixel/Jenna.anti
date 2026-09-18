"""Mock Voice Provider for deterministic tests and offline execution.

Provides predictable STT transcriptions and synthetic audio headers.
"""

from datetime import datetime, timezone
import struct
from app.ai.voice.base import BaseVoiceProvider
from app.ai.voice.types import AudioTranscription, VoiceProfile


class MockVoiceProvider(BaseVoiceProvider):
    """Deterministic voice provider for tests and fallback."""

    @property
    def provider_name(self) -> str:
        return "mock_voice_provider"

    @property
    def supported_languages(self) -> list[str]:
        return ["hi-IN", "en-IN", "en-US", "hi", "en"]

    async def speech_to_text(
        self,
        audio_data: bytes,
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> AudioTranscription:
        """Simulate transcribing speech based on length or mocked markers."""
        if not audio_data or len(audio_data) == 0:
            return AudioTranscription(
                text="",
                language=language or "en",
                confidence=0.0,
                duration_seconds=0.0,
            )

        # Check for mock trigger strings encoded in data
        data_preview = audio_data[:100]
        if b"HINDI" in data_preview or language in ("hi", "hi-IN"):
            text = "नमस्ते Jenna, आप कैसी हैं?"
            lang = "hi-IN"
        elif b"HINGLISH" in data_preview:
            text = "Hey Jenna, aaj ka schedule kya hai?"
            lang = "hi-IN"
        else:
            text = "Hello Jenna, how can you help me today?"
            lang = "en-US"

        duration = max(0.5, round(len(audio_data) / 16000.0, 2))

        return AudioTranscription(
            text=text,
            language=lang,
            confidence=0.98,
            duration_seconds=duration,
            timestamp=datetime.now(timezone.utc),
        )

    async def text_to_speech(
        self,
        text: str,
        voice_profile: VoiceProfile | None = None,
        output_format: str = "audio/mp3",
    ) -> bytes:
        """Return a valid mock audio buffer (simulating 44.1kHz stereo silence/tone header)."""
        # Create a tiny valid WAV/PCM header
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = max(100, len(text.encode("utf-8")) * 10)

        # Minimal standard WAV header (44 bytes)
        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,  # PCM
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )
        audio_body = b"\x00" * data_size
        return wav_header + audio_body
