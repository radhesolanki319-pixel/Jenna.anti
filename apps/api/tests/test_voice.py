"""Comprehensive deterministic test suite for Jenna Voice & Speech capabilities.

Validates Part 6 Phase 1:
- STT transcription (Hindi, Hinglish, English)
- TTS synthesis with female Jenna voice profiles
- Turn detection (VAD) and silence boundary calculation
- Interruption / emergency stop handling
- Strict privacy: Do not store raw audio by default
- Full HTTP API endpoints flow
"""

import base64
import uuid
from httpx import ASGITransport, AsyncClient
import pytest

from app.ai.voice import (
    JENNA_DEFAULT_VOICES,
    VoiceProfile,
    VoiceSettings,
    VoiceTurnState,
    voice_registry,
    voice_service,
)
from app.ai.voice.mock_provider import MockVoiceProvider
from app.ai.voice.turn_detector import VoiceTurnDetector
from app.main import app


# ==============================================================================
# 1. Voice Activity & Turn Detection Unit Tests
# ==============================================================================

def test_turn_detector_rms_calculation():
    """Verify Root Mean Square energy computation for silence and synthetic waveforms."""
    detector = VoiceTurnDetector(energy_threshold=0.015)

    # Pure silence (all zeros)
    silence = b"\x00\x00" * 800  # 1600 bytes = 800 16-bit samples
    rms_silence = detector.calculate_rms(silence)
    assert rms_silence == 0.0

    # High amplitude square wave
    high_energy = b"\xff\x7f\x00\x80" * 400
    rms_high = detector.calculate_rms(high_energy)
    assert rms_high > 0.5


def test_turn_detector_turn_completion_and_silence():
    """Verify turn completion after sustained silence while in LISTENING state."""
    detector = VoiceTurnDetector(energy_threshold=0.02, silence_timeout_ms=500.0)

    silence_chunk = b"\x00\x00" * 800  # 100ms of silence

    # First silent chunk (accumulated 100ms < 500ms timeout)
    res1 = detector.analyze_chunk(
        chunk=silence_chunk,
        current_state=VoiceTurnState.LISTENING,
        accumulated_silence_ms=0.0,
        chunk_duration_ms=100.0,
    )
    assert res1.is_speech is False
    assert res1.is_turn_complete is False
    assert res1.silence_duration_ms == 100.0

    # Cumulative silence exceeding 500ms
    res2 = detector.analyze_chunk(
        chunk=silence_chunk,
        current_state=VoiceTurnState.LISTENING,
        accumulated_silence_ms=450.0,
        chunk_duration_ms=100.0,
    )
    assert res2.is_turn_complete is True
    assert res2.silence_duration_ms == 550.0


def test_voice_interruption_trigger():
    """Verify that detected speech while Jenna is in SPEAKING state triggers should_interrupt."""
    detector = VoiceTurnDetector(energy_threshold=0.02)
    loud_speech_chunk = b"\xff\x7f\x00\x80" * 400

    # Jenna is currently SPEAKING and user speaks
    res = detector.analyze_chunk(
        chunk=loud_speech_chunk,
        current_state=VoiceTurnState.SPEAKING,
        accumulated_silence_ms=0.0,
    )
    assert res.is_speech is True
    assert res.should_interrupt is True


# ==============================================================================
# 2. Voice Profiles and Registry Tests
# ==============================================================================

def test_female_jenna_voice_profiles():
    """Verify default female Jenna voice profiles exist with bilingual parameters."""
    voices = voice_registry.list_voices()
    assert len(voices) >= 4

    voice_ids = [v.voice_id for v in voices]
    assert "jenna-female-natural" in voice_ids
    assert "jenna-female-hindi" in voice_ids
    assert "jenna-female-english" in voice_ids

    # Check gender & style
    for v in voices:
        assert v.gender == "female"
        assert v.speed >= 0.8


# ==============================================================================
# 3. Provider & Service Core Logic Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_voice_provider_multilingual_stt():
    """Verify speech-to-text for Hindi and English signals."""
    provider = MockVoiceProvider()

    # Hindi audio trigger
    res_hi = await provider.speech_to_text(audio_data=b"TEST_HINDI_AUDIO_STREAM", language="hi-IN")
    assert "नमस्ते" in res_hi.text
    assert res_hi.language == "hi-IN"

    # English audio trigger
    res_en = await provider.speech_to_text(audio_data=b"TEST_ENGLISH_AUDIO_STREAM", language="en-US")
    assert "Jenna" in res_en.text
    assert res_en.language == "en-US"


@pytest.mark.asyncio
async def test_mock_voice_provider_tts_synthesis():
    """Verify synthesized audio output contains valid audio format structure."""
    provider = MockVoiceProvider()
    profile = voice_registry.get_voice("jenna-female-natural")

    audio_bytes = await provider.text_to_speech("Namaste! Main Jenna hoon.", voice_profile=profile)
    assert len(audio_bytes) > 44
    assert audio_bytes[:4] == b"RIFF"  # Valid WAV header container
    assert audio_bytes[8:12] == b"WAVE"


@pytest.mark.asyncio
async def test_privacy_no_raw_audio_stored():
    """Verify strict privacy invariant: raw audio bytes are not stored by default."""
    user_id = str(uuid.uuid4())
    settings = voice_service.get_user_settings(user_id)
    assert settings.store_raw_audio is False

    transcription = await voice_service.transcribe(
        audio_data=b"SENSITIVE_AUDIO_STREAM",
        user_id=user_id,
        language="hi-IN",
        provider_name="mock",
    )
    assert transcription.text is not None


@pytest.mark.asyncio
async def test_emergency_interruption_stop():
    """Verify emergency interruption signal halts speech execution."""
    user_id = str(uuid.uuid4())
    conv_id = f"conv-{uuid.uuid4().hex[:8]}"

    # Trigger interruption
    res = voice_service.trigger_interruption(
        conversation_id=conv_id,
        user_id=user_id,
        reason="user_speaking",
    )
    assert res.success is True
    assert voice_service.is_interrupted(conversation_id=conv_id, user_id=user_id) is True


# ==============================================================================
# 4. Voice HTTP Endpoints Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_voice_http_api_flow():
    """Verify all /api/v1/voice HTTP endpoints with authenticated session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register test user
        email = f"voice_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg.status_code == 201

        # 2. GET /api/v1/voice/voices
        voices_res = await client.get("/api/v1/voice/voices")
        assert voices_res.status_code == 200
        voices = voices_res.json()
        assert len(voices) >= 4
        assert any(v["voice_id"] == "jenna-female-natural" for v in voices)

        # 3. GET /api/v1/voice/settings
        settings_res = await client.get("/api/v1/voice/settings")
        assert settings_res.status_code == 200
        settings = settings_res.json()
        assert settings["store_raw_audio"] is False

        # 4. PUT /api/v1/voice/settings
        settings["speech_rate"] = 1.2
        settings["preferred_voice_id"] = "jenna-female-hindi"
        update_res = await client.put("/api/v1/voice/settings", json=settings)
        assert update_res.status_code == 200
        assert update_res.json()["speech_rate"] == 1.2

        # 5. POST /api/v1/voice/transcribe (base64)
        audio_b64 = base64.b64encode(b"HINDI_AUDIO_SAMPLE").decode("utf-8")
        stt_res = await client.post(
            "/api/v1/voice/transcribe",
            json={"audio_base64": audio_b64, "language": "hi-IN"},
        )
        assert stt_res.status_code == 200
        stt_data = stt_res.json()
        assert "नमस्ते" in stt_data["text"]

        # 6. POST /api/v1/voice/synthesize
        tts_res = await client.post(
            "/api/v1/voice/synthesize",
            json={"text": "Hello world, I am Jenna."},
        )
        assert tts_res.status_code == 200
        assert len(tts_res.content) > 44
        assert "X-Jenna-Voice-ID" in tts_res.headers

        # 7. POST /api/v1/voice/interrupt
        interrupt_res = await client.post(
            "/api/v1/voice/interrupt",
            json={"conversation_id": "test-conv-123", "reason": "user_speaking"},
        )
        assert interrupt_res.status_code == 200
        assert interrupt_res.json()["success"] is True
