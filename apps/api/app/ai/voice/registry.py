"""Voice Provider & Profile Registry.

Manages active STT/TTS providers and supported female Jenna voice profiles.
"""

from typing import Any
from app.ai.voice.base import BaseVoiceProvider
from app.ai.voice.gemini_voice_provider import GeminiVoiceProvider
from app.ai.voice.mock_provider import MockVoiceProvider
from app.ai.voice.types import VoiceProfile


JENNA_DEFAULT_VOICES: list[VoiceProfile] = [
    VoiceProfile(
        voice_id="jenna-female-natural",
        name="Jenna Natural (Bilingual)",
        language="hi-IN",
        gender="female",
        style="warm_conversational",
        pitch=1.0,
        speed=1.0,
    ),
    VoiceProfile(
        voice_id="jenna-female-hindi",
        name="Jenna Hindi Native",
        language="hi-IN",
        gender="female",
        style="warm_expressive",
        pitch=1.05,
        speed=0.95,
    ),
    VoiceProfile(
        voice_id="jenna-female-english",
        name="Jenna English Global",
        language="en-US",
        gender="female",
        style="clear_professional",
        pitch=1.0,
        speed=1.0,
    ),
    VoiceProfile(
        voice_id="jenna-female-calm",
        name="Jenna Calm & Gentle",
        language="en-IN",
        gender="female",
        style="gentle_supportive",
        pitch=0.98,
        speed=0.9,
    ),
]


class VoiceRegistry:
    """Registry coordinating voice providers and voice profiles."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseVoiceProvider] = {}
        self._voices: dict[str, VoiceProfile] = {v.voice_id: v for v in JENNA_DEFAULT_VOICES}
        self._default_provider_name: str = "gemini"

        # Register default providers
        self.register_provider("mock", MockVoiceProvider())
        self.register_provider("gemini", GeminiVoiceProvider())

    def register_provider(self, name: str, provider: BaseVoiceProvider) -> None:
        """Register a voice provider."""
        self._providers[name] = provider

    def get_provider(self, name: str | None = None) -> BaseVoiceProvider:
        """Get active voice provider with safe fallback."""
        key = name or self._default_provider_name
        if key in self._providers:
            return self._providers[key]
        return self._providers.get("mock", MockVoiceProvider())

    def list_voices(self) -> list[VoiceProfile]:
        """Return all supported Jenna female voice profiles."""
        return list(self._voices.values())

    def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Fetch voice profile by id."""
        return self._voices.get(voice_id)


voice_registry = VoiceRegistry()
