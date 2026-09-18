"""Voice Service coordinating STT, TTS, Turn Detection, and User Voice Preferences.

Implements Part 6 Phase 1:
- Provider-agnostic STT and TTS orchestration
- User-isolated voice settings
- Real-time turn detection and interruption dispatch
- Strict privacy: Never stores raw audio bytes by default
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.ai.voice.registry import voice_registry
from app.ai.voice.turn_detector import VoiceTurnDetector
from app.ai.voice.types import (
    AudioTranscription,
    InterruptionResponse,
    TurnDetectionResult,
    VoiceProfile,
    VoiceSettings,
    VoiceTurnState,
)
from app.core.logging import logger
from app.events import DomainEvent, DomainEventType, domain_dispatcher





class VoiceService:
    """Service handling audio processing, synthesis, turn transitions, and voice preferences."""

    def __init__(self) -> None:
        self.turn_detector = VoiceTurnDetector()
        # In-memory store for user voice settings (scoped by user_id)
        self._user_settings: dict[str, VoiceSettings] = {}
        # Active interruption tracker (conversation_id -> timestamp)
        self._active_interruptions: dict[str, datetime] = {}

    def get_user_settings(self, user_id: str) -> VoiceSettings:
        """Fetch voice settings for a user with sensible defaults."""
        if user_id not in self._user_settings:
            self._user_settings[user_id] = VoiceSettings()
        return self._user_settings[user_id]

    def update_user_settings(self, user_id: str, new_settings: VoiceSettings) -> VoiceSettings:
        """Update and persist user voice settings."""
        self._user_settings[user_id] = new_settings
        logger.info(
            f"Updated voice settings for user {user_id}",
            extra={"user_id": str(user_id), "voice_id": new_settings.preferred_voice_id},
        )
        return self._user_settings[user_id]

    async def transcribe(
        self,
        audio_data: bytes,
        user_id: str,
        mime_type: str = "audio/webm",
        language: str | None = None,
        provider_name: str | None = None,
    ) -> AudioTranscription:
        """Transcribe speech audio without retaining raw audio data."""
        provider = voice_registry.get_provider(provider_name)
        user_settings = self.get_user_settings(user_id)
        target_lang = language or user_settings.preferred_language

        transcription = await provider.speech_to_text(
            audio_data=audio_data,
            mime_type=mime_type,
            language=target_lang,
        )

        # Audit event without raw audio buffer
        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.VOICE_EVENT,
                aggregate_id=str(user_id),
                user_id=str(user_id),
                payload={
                    "action": "transcription",
                    "char_length": len(transcription.text),
                    "confidence": transcription.confidence,
                    "language": transcription.language,
                    "duration_seconds": transcription.duration_seconds,
                    "raw_audio_stored": user_settings.store_raw_audio,
                },
            )
        )


        return transcription

    async def synthesize(
        self,
        text: str,
        user_id: str,
        voice_id: str | None = None,
        output_format: str = "audio/mp3",
        provider_name: str | None = None,
    ) -> tuple[bytes, VoiceProfile]:
        """Synthesize text using selected female Jenna voice profile."""
        user_settings = self.get_user_settings(user_id)
        active_voice_id = voice_id or user_settings.preferred_voice_id

        profile = voice_registry.get_voice(active_voice_id) or voice_registry.list_voices()[0]
        # Apply user speed modifier
        effective_profile = profile.model_copy(
            update={"speed": profile.speed * user_settings.speech_rate}
        )

        provider = voice_registry.get_provider(provider_name)
        audio_bytes = await provider.text_to_speech(
            text=text,
            voice_profile=effective_profile,
            output_format=output_format,
        )

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.VOICE_EVENT,
                aggregate_id=str(user_id),
                user_id=str(user_id),
                payload={
                    "action": "synthesis",
                    "text_length": len(text),
                    "voice_id": effective_profile.voice_id,
                    "audio_bytes_length": len(audio_bytes),
                    "format": output_format,
                },
            )
        )

        return audio_bytes, effective_profile

    def detect_turn_boundary(
        self,
        audio_chunk: bytes,
        current_state: VoiceTurnState,
        accumulated_silence_ms: float = 0.0,
    ) -> TurnDetectionResult:
        """Evaluate real-time speech boundary and potential interruption."""
        return self.turn_detector.analyze_chunk(
            chunk=audio_chunk,
            current_state=current_state,
            accumulated_silence_ms=accumulated_silence_ms,
        )

    def trigger_interruption(
        self,
        conversation_id: str | None,
        user_id: str,
        reason: str = "user_speaking",
    ) -> InterruptionResponse:
        """Trigger immediate emergency stop / interruption for speaking Jenna."""
        now = datetime.now(timezone.utc)
        conv_key = conversation_id or str(user_id)
        self._active_interruptions[conv_key] = now

        logger.info(
            f"Voice interruption triggered for conversation '{conv_key}': {reason}",
            extra={"conversation_id": conv_key, "user_id": str(user_id), "reason": reason},
        )

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.VOICE_EVENT,
                aggregate_id=conv_key,
                user_id=str(user_id),
                payload={"action": "interruption", "conversation_id": conv_key, "reason": reason},
            )
        )


        return InterruptionResponse(
            success=True,
            interrupted_at=now,
            message=f"Voice output successfully halted ({reason}).",
        )

    def is_interrupted(self, conversation_id: str | None, user_id: str) -> bool:
        """Check if an interruption signal was recently received."""
        conv_key = conversation_id or str(user_id)
        return conv_key in self._active_interruptions


voice_service = VoiceService()
