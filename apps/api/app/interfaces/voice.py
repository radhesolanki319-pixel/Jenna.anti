"""Future Domain Interface: VoiceProvider

Defines the contract for speech-to-text (STT), text-to-speech (TTS), and audio streaming.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator


@dataclass
class AudioTranscription:
    """Result of speech-to-text transcription."""
    text: str
    language: str = "en"
    confidence: float = 1.0
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VoiceProfile:
    """Settings and identifiers for synthesized speech."""
    voice_id: str
    name: str
    language: str = "en-US"
    gender: str = "female"
    style: str = "conversational"


class VoiceProvider(ABC):
    """Abstract interface contract for audio input and speech synthesis."""

    @abstractmethod
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> AudioTranscription:
        """Transcribe an audio buffer to text."""
        pass

    @abstractmethod
    def stream_speech_to_text(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream transcription text incrementally from incoming audio chunks."""
        pass

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        voice_profile: VoiceProfile | None = None,
    ) -> bytes:
        """Synthesize text into complete audio format (e.g. PCM / MP3)."""
        pass

    @abstractmethod
    def stream_text_to_speech(
        self,
        text_stream: AsyncIterator[str],
        voice_profile: VoiceProfile | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized audio chunks in real-time as text tokens arrive."""
        pass
