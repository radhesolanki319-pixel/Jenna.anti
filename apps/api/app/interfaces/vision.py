"""Future Domain Interface: VisionProvider

Defines the contract for screen understanding, camera context, and multimodal visual inspection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class BoundingBox:
    """Coordinates of a detected UI or visual element."""
    x: float
    y: float
    width: float
    height: float
    label: str | None = None
    confidence: float = 1.0


@dataclass
class VisionAnalysisResult:
    """Outcome of visual analysis on an image or screenshot."""
    description: str
    detected_elements: list[BoundingBox] = field(default_factory=list)
    extracted_text: list[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CameraContext:
    """Current state and capability of a connected camera sensor."""
    is_active: bool
    resolution: str
    framerate: int = 30
    device_id: str | None = None


class VisionProvider(ABC):
    """Abstract interface contract for visual processing."""

    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes | str,
        prompt: str | None = None,
    ) -> VisionAnalysisResult:
        """Analyze a static image and return structured scene understanding."""
        pass

    @abstractmethod
    async def analyze_screen(
        self,
        screen_capture: bytes | str,
        detect_ui_elements: bool = True,
    ) -> VisionAnalysisResult:
        """Analyze a captured device screen, locating interactive UI components."""
        pass

    @abstractmethod
    async def get_camera_context(self) -> CameraContext:
        """Inspect the current operational status of the camera sensor."""
        pass
