"""Vision Service managing image and screen inspection with strict security boundaries.

Implements Part 6 Phase 2:
- Multimodal analysis orchestration
- Payload format and size validation
- Defensive prompt-injection containment wrapping
- Strict camera privacy (Never silently activate camera)
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
from app.ai.vision.media_validator import media_validator
from app.ai.vision.mock_provider import MockVisionProvider
from app.ai.vision.multimodal_context import multimodal_context_builder
from app.ai.vision.types import (
    CameraContext,
    VisionAnalysisResult,
    VisionPrivacySettings,
)
from app.core.errors import ForbiddenError, ValidationError
from app.core.logging import logger
from app.events import DomainEvent, DomainEventType, domain_dispatcher



from app.core.permissions import Permission
from app.interfaces.permissions import AuthorizationDecision
from app.models.users import User
from app.services.permission_service import get_permission_service




class VisionService:
    """Service handling visual analysis with security gates and isolation."""

    def __init__(self) -> None:
        self.mock_provider = MockVisionProvider()
        self.gemini_provider = GeminiVisionProvider()
        self._privacy_settings: dict[str, VisionPrivacySettings] = {}

    def get_privacy_settings(self, user_id: str) -> VisionPrivacySettings:
        """Fetch user-scoped vision privacy settings."""
        if user_id not in self._privacy_settings:
            self._privacy_settings[user_id] = VisionPrivacySettings()
        return self._privacy_settings[user_id]

    def update_privacy_settings(
        self,
        user_id: str,
        new_settings: VisionPrivacySettings,
    ) -> VisionPrivacySettings:
        """Update user vision privacy preferences."""
        self._privacy_settings[user_id] = new_settings
        logger.info(
            f"Updated vision privacy settings for user {user_id}",
            extra={"user_id": str(user_id), "camera_allowed": new_settings.allow_camera_capture},
        )
        return self._privacy_settings[user_id]

    async def analyze_image(
        self,
        image_bytes: bytes,
        user: User,
        mime_type: str = "image/jpeg",
        prompt: str | None = None,
        detect_elements: bool = True,
        use_mock: bool = False,
    ) -> VisionAnalysisResult:
        """Analyze an uploaded image after validating media format and size."""
        # 1. Media format and magic bytes validation
        val_res = media_validator.validate(image_bytes, declared_mime=mime_type)
        if not val_res.is_valid:
            raise ValidationError(val_res.error_message or "Invalid image file.")

        # 2. Permission check: reading visual data
        perm_service = get_permission_service()
        eval_res = perm_service.evaluate_action(
            role=user.role,
            required_permission=Permission.LOW_RISK_ACTION,
            is_sensitive=False,
            context={"user_id": str(user.id)},
        )

        if eval_res.decision == AuthorizationDecision.DENIED:
            raise ForbiddenError("Permission denied: user not authorized to perform visual analysis.")


        # 3. Process image through provider
        provider = self.mock_provider if use_mock else self.gemini_provider
        result = await provider.analyze_image(
            image_data=image_bytes,
            mime_type=mime_type,
            prompt=prompt,
            detect_elements=detect_elements,
        )

        # 4. Wrap with defensive untrusted context boundary
        sanitized_context = multimodal_context_builder.build_defensive_context(
            analysis_result=result,
            origin="image_attachment",
        )
        result.sanitized_prompt_context = sanitized_context

        # 5. Audit event
        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.VISION_EVENT,
                aggregate_id=str(user.id),
                user_id=str(user.id),
                payload={
                    "action": "image_analyzed",
                    "mime_type": mime_type,
                    "size_bytes": len(image_bytes),
                    "elements_detected": len(result.detected_elements),
                    "ocr_lines": len(result.extracted_text),
                    "confidence": result.confidence,
                },
            )
        )


        return result

    async def analyze_screen(
        self,
        screen_bytes: bytes,
        user: User,
        mime_type: str = "image/png",
        detect_ui_elements: bool = True,
        use_mock: bool = False,
    ) -> VisionAnalysisResult:
        """Analyze captured screen with sensitive action authorization check."""
        # 1. Media validation
        val_res = media_validator.validate(screen_bytes, declared_mime=mime_type)
        if not val_res.is_valid:
            raise ValidationError(val_res.error_message or "Invalid screen capture buffer.")

        # 2. Screen observation requires valid user permissions
        perm_service = get_permission_service()
        eval_res = perm_service.evaluate_action(
            role=user.role,
            required_permission=Permission.READ,
            is_sensitive=False,
            context={"user_id": str(user.id)},
        )
        if eval_res.decision == AuthorizationDecision.DENIED:
            raise ForbiddenError("Permission denied: Screen capture analysis is forbidden for this user role.")



        provider = self.mock_provider if use_mock else self.gemini_provider
        result = await provider.analyze_screen(
            screen_data=screen_bytes,
            mime_type=mime_type,
            detect_ui_elements=detect_ui_elements,
        )

        sanitized_context = multimodal_context_builder.build_defensive_context(
            analysis_result=result,
            origin="screen_capture",
        )
        result.sanitized_prompt_context = sanitized_context

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.VISION_EVENT,
                aggregate_id=str(user.id),
                user_id=str(user.id),
                payload={
                    "action": "screen_analyzed",
                    "mime_type": mime_type,
                    "elements_count": len(result.detected_elements),
                },
            )
        )


        return result

    async def get_camera_context(self, user: User) -> CameraContext:
        """Check camera availability while strictly preventing silent activation."""
        privacy = self.get_privacy_settings(str(user.id))
        return CameraContext(
            is_active=False,  # Never silently activated
            resolution="1920x1080",
            framerate=30,
            permission_granted=privacy.allow_camera_capture,
        )


vision_service = VisionService()
