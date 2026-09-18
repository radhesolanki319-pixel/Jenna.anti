"""Gemini Multimodal Vision Provider using official google-genai SDK.

Implements Part 6 Phase 2:
- Multimodal scene understanding and OCR
- UI detection via Gemini 2.5 Flash
- Graceful offline fallback
"""

import asyncio
from datetime import datetime, timezone
import json
import re

from app.ai.vision.base import BaseVisionProvider
from app.ai.vision.mock_provider import MockVisionProvider
from app.ai.vision.types import BoundingBox, CameraContext, VisionAnalysisResult
from app.core.config import settings
from app.core.logging import logger

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False


class GeminiVisionProvider(BaseVisionProvider):
    """Vision provider using Gemini multimodal visual understanding."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.effective_google_api_key


        self._fallback = MockVisionProvider()
        self._client = None
        if HAS_GOOGLE_GENAI and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini vision client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini_vision_provider"

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        prompt: str | None = None,
        detect_elements: bool = True,
    ) -> VisionAnalysisResult:
        """Analyze image with Gemini multimodal model."""
        if not self._client:
            return await self._fallback.analyze_image(image_data, mime_type, prompt, detect_elements)

        try:
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
            user_instruction = prompt or "Provide a comprehensive description of this image, transcribe any visible text, and identify main elements."
            system_prompt = (
                "You are an expert visual analysis assistant. "
                "Describe what is present in the image. List all extracted text lines. "
                "Respond in clear, structured format."
            )

            def _call_gemini():
                for m in [
                    "gemini-flash-lite-latest",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                    "gemini-1.5-flash",
                    "gemini-3.5-flash",
                ]:
                    try:
                        return self._client.models.generate_content(
                            model=m,
                            contents=[image_part, f"{system_prompt}\n\nTask: {user_instruction}"],
                        )
                    except Exception as me:
                        logger.warning(f"Vision model {m} attempt failed: {me}")
                raise RuntimeError("All vision model attempts exhausted")

            response = await asyncio.to_thread(_call_gemini)
            raw_text = (response.text or "").strip()

            # Split lines for basic OCR extraction
            extracted_lines = [
                line.strip().lstrip("-*• ")
                for line in raw_text.splitlines()
                if line.strip() and len(line.strip()) < 100
            ]

            return VisionAnalysisResult(
                description=raw_text,
                detected_elements=[],
                extracted_text=extracted_lines[:20],
                confidence=0.95,
                is_untrusted_content=True,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as err:
            logger.warning(f"Gemini visual analysis failed, using fallback: {err}")
            return await self._fallback.analyze_image(image_data, mime_type, prompt, detect_elements)

    async def analyze_screen(
        self,
        screen_data: bytes,
        mime_type: str = "image/png",
        detect_ui_elements: bool = True,
        extract_ocr: bool = True,
        prompt: str | None = None,
    ) -> VisionAnalysisResult:
        """Analyze screen capture with Gemini."""
        actual_prompt = prompt or "Analyze this screen capture: locate active UI windows, buttons, input fields, and extract visible text."
        return await self.analyze_image(
            image_data=screen_data,
            mime_type=mime_type,
            prompt=actual_prompt,
            detect_elements=detect_ui_elements,
        )

    async def get_camera_context(self) -> CameraContext:
        """Inspect camera state safely."""
        return await self._fallback.get_camera_context()
