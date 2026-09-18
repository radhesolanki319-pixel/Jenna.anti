"""Vision & Multimodal visual inspection package."""

from app.ai.vision.media_validator import media_validator, MediaValidator
from app.ai.vision.multimodal_context import multimodal_context_builder, MultimodalContextBuilder
from app.ai.vision.service import vision_service, VisionService
from app.ai.vision.types import (
    AnalyzeImageRequest,
    AnalyzeScreenRequest,
    BoundingBox,
    CameraContext,
    MediaValidationResult,
    VisionAnalysisResult,
    VisionPrivacySettings,
)

__all__ = [
    "vision_service",
    "VisionService",
    "media_validator",
    "MediaValidator",
    "multimodal_context_builder",
    "MultimodalContextBuilder",
    "BoundingBox",
    "VisionAnalysisResult",
    "CameraContext",
    "VisionPrivacySettings",
    "MediaValidationResult",
    "AnalyzeImageRequest",
    "AnalyzeScreenRequest",
]
