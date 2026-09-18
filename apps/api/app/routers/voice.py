"""Voice & Audio API Router.

Exposes endpoints for STT transcription, TTS synthesis, turn management, and interruption.
"""

import base64
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.ai.voice import (
    AudioTranscription,
    InterruptionRequest,
    InterruptionResponse,
    SynthesizeRequest,
    TranscribeRequest,
    VoiceProfile,
    VoiceSettings,
    voice_registry,
    voice_service,
)
from app.core.errors import ValidationError
from app.models.users import User
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/voice", tags=["Voice & Audio"])


@router.get("/voices", response_model=list[VoiceProfile])
async def list_available_voices(
    current_user: User = Depends(get_current_user),
) -> list[VoiceProfile]:
    """Retrieve all available Jenna female voice profiles."""
    return voice_registry.list_voices()


@router.get("/settings", response_model=VoiceSettings)
async def get_voice_settings(
    current_user: User = Depends(get_current_user),
) -> VoiceSettings:
    """Retrieve voice and audio preferences for the current authenticated user."""
    return voice_service.get_user_settings(str(current_user.id))


@router.put("/settings", response_model=VoiceSettings)
async def update_voice_settings(
    settings_in: VoiceSettings,
    current_user: User = Depends(get_current_user),
) -> VoiceSettings:
    """Update current user voice preferences."""
    return voice_service.update_user_settings(str(current_user.id), settings_in)


@router.post("/transcribe", response_model=AudioTranscription)
async def transcribe_audio_json(
    request: TranscribeRequest,
    current_user: User = Depends(get_current_user),
) -> AudioTranscription:
    """Transcribe base64-encoded audio speech utterance."""
    try:
        raw_bytes = base64.b64decode(request.audio_base64)
    except Exception as err:
        raise ValidationError(f"Malformed base64 audio payload: {err}")

    return await voice_service.transcribe(
        audio_data=raw_bytes,
        user_id=str(current_user.id),
        mime_type=request.mime_type,
        language=request.language,
    )


@router.post("/transcribe-file", response_model=AudioTranscription)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    current_user: User = Depends(get_current_user),
) -> AudioTranscription:
    """Transcribe multipart/form-data audio file."""
    content = await file.read()
    if not content:
        raise ValidationError("Uploaded audio file is empty.")

    mime_type = file.content_type or "audio/webm"
    return await voice_service.transcribe(
        audio_data=content,
        user_id=str(current_user.id),
        mime_type=mime_type,
        language=language,
    )


@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Synthesize text into speech audio bytes using Jenna voice profile."""
    voice_id = request.voice_profile.voice_id if request.voice_profile else None
    audio_bytes, profile = await voice_service.synthesize(
        text=request.text,
        user_id=str(current_user.id),
        voice_id=voice_id,
        output_format=request.output_format,
    )

    return Response(
        content=audio_bytes,
        media_type=request.output_format,
        headers={
            "X-Jenna-Voice-ID": profile.voice_id,
            "X-Jenna-Voice-Language": profile.language,
        },
    )


@router.post("/interrupt", response_model=InterruptionResponse)
async def interrupt_speech(
    request: InterruptionRequest,
    current_user: User = Depends(get_current_user),
) -> InterruptionResponse:
    """Emergency stop or user-initiated interruption of currently speaking Jenna."""
    return voice_service.trigger_interruption(
        conversation_id=request.conversation_id,
        user_id=str(current_user.id),
        reason=request.reason,
    )


class SilenceAnalysisRequest(BaseModel):
    transcript: str = ""
    silence_duration_ms: float = 650.0
    pcm_energy: float = 0.0


@router.post("/silence-analysis")
async def silence_analysis_endpoint(request: SilenceAnalysisRequest) -> dict:
    """Classify pauses into thinking hesitation (HOLD_TURN) vs complete turn (SPEAK_NOW)."""
    from app.ai.voice.silence_intelligence import silence_intelligence_service
    return silence_intelligence_service.analyze_silence(
        transcript=request.transcript,
        silence_duration_ms=request.silence_duration_ms,
        pcm_energy=request.pcm_energy,
    )

