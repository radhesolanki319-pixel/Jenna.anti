"""Vision & Multimodal type definitions, validation schemas, and security boundaries.

Conforms to Part 6 Phase 2 specifications:
- Image & Screen visual analysis contracts
- UI Bounding box & OCR extraction
- Multimodal context wrapping with untrusted content boundaries
- Strict privacy: Camera permission verification & retention limits
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized coordinates of a detected visual or UI element (0.0 to 1.0)."""
    x: float = Field(..., ge=0.0, le=1.0, description="Top-left X coordinate normalized")
    y: float = Field(..., ge=0.0, le=1.0, description="Top-left Y coordinate normalized")
    width: float = Field(..., ge=0.0, le=1.0, description="Width normalized")
    height: float = Field(..., ge=0.0, le=1.0, description="Height normalized")
    label: str | None = Field(default=None, description="Class or element label (e.g. 'button', 'text', 'icon')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence")


class VisionAnalysisResult(BaseModel):
    """Structured scene and document understanding."""
    description: str = Field(..., description="Natural language description of visual scene")
    detected_elements: list[BoundingBox] = Field(default_factory=list, description="Detected UI elements or objects")
    extracted_text: list[str] = Field(default_factory=list, description="Extracted OCR text lines")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall analysis confidence")
    is_untrusted_content: bool = Field(default=True, description="Always marked untrusted to prevent prompt injections")
    sanitized_prompt_context: str | None = Field(default=None, description="Defensively wrapped context snippet")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CameraContext(BaseModel):
    """Operational status and permission state of a camera sensor."""
    is_active: bool = Field(default=False, description="True if camera is actively capturing")
    resolution: str = Field(default="1920x1080", description="Sensor resolution")
    framerate: int = Field(default=30, description="Sensor framerate")
    device_id: str | None = Field(default=None, description="Hardware device ID")
    permission_granted: bool = Field(default=False, description="Explicit user permission granted")


class VisionPrivacySettings(BaseModel):
    """User-scoped vision and camera privacy controls."""
    allow_camera_capture: bool = Field(default=False, description="Explicit permission for camera capture")
    retention_hours: int = Field(default=0, ge=0, le=720, description="Image retention in hours (0 = immediate purge)")
    mask_pii_in_ocr: bool = Field(default=True, description="Automatically redact detected sensitive credentials")
    never_silent_activate: bool = Field(default=True, description="Strictly prohibit unnotified sensor activation")


class MediaValidationResult(BaseModel):
    """Result of image payload safety and format validation."""
    is_valid: bool
    format: str | None = None
    size_bytes: int = 0
    dimensions: tuple[int, int] | None = None
    error_message: str | None = None


class AnalyzeImageRequest(BaseModel):
    """Request schema for visual inspection of an image."""
    image_base64: str = Field(..., description="Base64-encoded image bytes")
    mime_type: str = Field(default="image/jpeg", description="MIME type: image/jpeg, image/png, or image/webp")
    prompt: str | None = Field(default=None, description="Instruction or question regarding the visual scene")
    detect_elements: bool = Field(default=True, description="Whether to locate UI bounding boxes")


class AnalyzeScreenRequest(BaseModel):
    """Request schema for screen and desktop visual analysis."""
    screen_base64: str = Field(..., description="Base64-encoded screenshot bytes")
    mime_type: str = Field(default="image/png", description="MIME type of screenshot")
    detect_ui_elements: bool = Field(default=True, description="Detect interactive UI buttons and inputs")
    extract_ocr: bool = Field(default=True, description="Extract text from screen")
