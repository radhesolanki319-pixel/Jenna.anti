"""Base Vision Provider specification.

Implements the VisionProvider domain interface with concrete processing abstractions.
"""

from abc import ABC, abstractmethod
from app.ai.vision.types import CameraContext, VisionAnalysisResult


class BaseVisionProvider(ABC):
    """Abstract base class for vision and multimodal visual analysis providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the vision provider implementation."""
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        prompt: str | None = None,
        detect_elements: bool = True,
    ) -> VisionAnalysisResult:
        """Analyze a static image or document screenshot."""
        pass

    @abstractmethod
    async def analyze_screen(
        self,
        screen_data: bytes,
        mime_type: str = "image/png",
        detect_ui_elements: bool = True,
        extract_ocr: bool = True,
    ) -> VisionAnalysisResult:
        """Analyze a captured device screen locating interactive UI controls."""
        pass

    @abstractmethod
    async def get_camera_context(self) -> CameraContext:
        """Inspect operational state of camera sensor without silent activation."""
        pass
