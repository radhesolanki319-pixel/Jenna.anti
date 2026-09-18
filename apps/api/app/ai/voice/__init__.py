"""Voice and Speech package for Jenna AI Platform."""

from app.ai.voice.registry import voice_registry, JENNA_DEFAULT_VOICES
from app.ai.voice.service import voice_service, VoiceService
from app.ai.voice.types import (
    AudioTranscription,
    InterruptionRequest,
    InterruptionResponse,
    SynthesizeRequest,
    TranscribeRequest,
    TurnDetectionResult,
    VoiceProfile,
    VoiceSettings,
    VoiceTurnState,
)

__all__ = [
    "voice_service",
    "VoiceService",
    "voice_registry",
    "JENNA_DEFAULT_VOICES",
    "AudioTranscription",
    "VoiceProfile",
    "VoiceSettings",
    "VoiceTurnState",
    "TurnDetectionResult",
    "InterruptionRequest",
    "InterruptionResponse",
    "SynthesizeRequest",
    "TranscribeRequest",
]
