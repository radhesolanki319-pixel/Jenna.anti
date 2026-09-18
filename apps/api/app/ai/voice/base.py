"""Base Voice Provider abstract specification.

Implements the VoiceProvider domain interface with concrete default behaviors.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from app.ai.voice.types import AudioTranscription, VoiceProfile


class BaseVoiceProvider(ABC):
    """Abstract base class for all speech-to-text and text-to-speech providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the voice provider implementation."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        """List of supported language/locale codes (e.g. ['hi-IN', 'en-IN', 'en-US'])."""
        pass

    @abstractmethod
    async def speech_to_text(
        self,
        audio_data: bytes,
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> AudioTranscription:
        """Transcribe an audio buffer to text."""
        pass

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        voice_profile: VoiceProfile | None = None,
        output_format: str = "audio/mp3",
    ) -> bytes:
        """Synthesize text into complete audio format."""
        pass

    async def stream_speech_to_text(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream transcription text incrementally from incoming audio chunks."""
        # Default fallback accumulates and processes
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        full_audio = b"".join(chunks)
        result = await self.speech_to_text(full_audio, language=language)
        yield result.text

    async def stream_text_to_speech(
        self,
        text_stream: AsyncIterator[str],
        voice_profile: VoiceProfile | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized audio chunks in real-time as text tokens arrive."""
        full_text = ""
        async for chunk in text_stream:
            full_text += chunk
        audio_bytes = await self.text_to_speech(full_text, voice_profile=voice_profile)
        yield audio_bytes
