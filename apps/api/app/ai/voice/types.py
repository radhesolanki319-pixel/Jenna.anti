"""Voice & Speech type definitions, configuration models, and state contracts.

Conforms to Part 6 Phase 1 specifications:
- Provider-agnostic STT & TTS
- Turn detection (VAD) & interruption handling
- Configurable female Jenna voice profiles (Hindi/Hinglish/English)
- Strict privacy: Do not store raw audio by default
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class VoiceTurnState(str, Enum):
    """Current state of voice interaction loop."""
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"


class VoiceProfile(BaseModel):
    """Identifier and acoustic attributes for female Jenna synthesized speech."""
    voice_id: str = Field(..., description="Unique voice identifier, e.g., 'jenna-female-natural'")
    name: str = Field(..., description="Human-friendly voice label")
    language: str = Field(default="hi-IN", description="Primary locale code (e.g., 'hi-IN', 'en-IN', 'en-US')")
    gender: str = Field(default="female", description="Voice gender")
    style: str = Field(default="warm_conversational", description="Tone and demeanor")
    pitch: float = Field(default=1.0, ge=0.5, le=1.5, description="Pitch modifier")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech rate modifier")


class AudioTranscription(BaseModel):
    """Transcription payload returned by Speech-to-Text providers."""
    text: str = Field(..., description="Transcribed textual utterance")
    language: str = Field(default="hi", description="Detected or requested language code")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Transcription confidence score")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Audio duration in seconds")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceSettings(BaseModel):
    """User-scoped voice interaction and playback preferences."""
    preferred_voice_id: str = Field(default="jenna-female-natural", description="Default selected female voice")
    preferred_language: str = Field(default="hi-IN", description="Default speech recognition language")
    auto_playback: bool = Field(default=True, description="Automatically speak out AI responses")
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Default speech speed")
    input_mode: str = Field(default="vad", description="'vad' for voice activity detection, 'push_to_talk' for manual")
    interruption_enabled: bool = Field(default=True, description="Allow user speech to interrupt active TTS playback")
    store_raw_audio: bool = Field(default=False, description="Privacy toggle: never store raw audio buffers by default")


class TurnDetectionResult(BaseModel):
    """Real-time Voice Activity Detection and turn boundary analysis."""
    is_speech: bool = Field(default=False, description="True if voice activity is detected in chunk")
    speech_probability: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence of human speech presence")
    silence_duration_ms: float = Field(default=0.0, ge=0.0, description="Consecutive silence observed in milliseconds")
    is_turn_complete: bool = Field(default=False, description="True if user finished speaking based on silence threshold")
    should_interrupt: bool = Field(default=False, description="True if user started speaking while Jenna is speaking")


class InterruptionRequest(BaseModel):
    """Client request to interrupt current TTS playback."""
    conversation_id: str | None = None
    reason: str = Field(default="user_speaking", description="Interruption cause: 'user_speaking', 'button_click'")


class InterruptionResponse(BaseModel):
    """Interruption acknowledgment."""
    success: bool
    interrupted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str


class SynthesizeRequest(BaseModel):
    """Request payload for text-to-speech synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text string to synthesize")
    voice_profile: VoiceProfile | None = None
    output_format: str = Field(default="audio/mp3", description="Desired audio MIME type (audio/mp3, audio/wav)")


class TranscribeRequest(BaseModel):
    """Base64 audio transcription request."""
    audio_base64: str = Field(..., description="Base64-encoded audio payload")
    mime_type: str = Field(default="audio/webm", description="Audio MIME type")
    language: str | None = Field(default=None, description="Optional target language hint")
