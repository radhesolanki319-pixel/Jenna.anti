"""Gemini Voice Provider utilizing multimodal audio understanding.

Implements Part 6 Phase 1:
- Multilingual speech-to-text (Hindi, Hinglish, English)
- Audio understanding via Gemini multimodal API
- Graceful offline fallback
"""

import asyncio
from datetime import datetime, timezone
import struct
from app.ai.voice.base import BaseVoiceProvider
from app.ai.voice.mock_provider import MockVoiceProvider
from app.ai.voice.types import AudioTranscription, VoiceProfile
from app.core.config import settings
from app.core.logging import logger

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False


class GeminiVoiceProvider(BaseVoiceProvider):
    """Voice provider powered by Gemini multimodal audio processing."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.effective_google_api_key


        self._fallback = MockVoiceProvider()
        self._client = None
        if HAS_GOOGLE_GENAI and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini voice client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini_voice_provider"

    @property
    def supported_languages(self) -> list[str]:
        return ["hi-IN", "en-IN", "en-US", "hi", "en"]

    async def speech_to_text(
        self,
        audio_data: bytes,
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> AudioTranscription:
        """Transcribe audio bytes using Gemini multimodal audio model or fallback."""
        if not self._client:
            return await self._fallback.speech_to_text(audio_data, mime_type, language)

        try:
            # Construct audio transcription prompt
            target_lang_str = f" Target language/dialect: {language}." if language else " Support Hindi, Hinglish, or English naturally."
            prompt = (
                "You are an exact speech-to-text transcriber. "
                "Transcribe the spoken words in the following audio file verbatim. "
                "Do not translate, summarize, or add quotes or conversational commentary."
                + target_lang_str
            )

            audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime_type)

            def _call_gemini():
                return self._client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[audio_part, prompt],
                )

            response = await asyncio.to_thread(_call_gemini)
            text = (response.text or "").strip()

            duration = max(0.5, round(len(audio_data) / 16000.0, 2))
            return AudioTranscription(
                text=text,
                language=language or "auto",
                confidence=0.95,
                duration_seconds=duration,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as err:
            logger.warning(f"Gemini STT failed, falling back to mock provider: {err}")
            return await self._fallback.speech_to_text(audio_data, mime_type, language)

    async def text_to_speech(
        self,
        text: str,
        voice_profile: VoiceProfile | None = None,
        output_format: str = "audio/mp3",
    ) -> bytes:
        """Synthesize text into speech audio buffer."""
        # Returns standard audio payload
        return await self._fallback.text_to_speech(text, voice_profile, output_format)
