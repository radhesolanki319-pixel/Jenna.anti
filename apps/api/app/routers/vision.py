"""Vision & Multimodal Visual Inspection API Router.

Exposes endpoints for image and screen analysis, media safety checks, and camera status.
"""

import base64
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.ai.vision import (
    AnalyzeImageRequest,
    AnalyzeScreenRequest,
    CameraContext,
    VisionAnalysisResult,
    VisionPrivacySettings,
    vision_service,
)
from app.ai.vision.live_screen import live_screen_service
from app.core.errors import ValidationError
from app.models.users import User
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/vision", tags=["Vision & Multimodal"])


@router.get("/camera-status", response_model=CameraContext)
async def get_camera_status(
    current_user: User = Depends(get_current_user),
) -> CameraContext:
    """Check camera availability status (strictly prevents silent activation)."""
    return await vision_service.get_camera_context(current_user)


@router.get("/settings", response_model=VisionPrivacySettings)
async def get_vision_settings(
    current_user: User = Depends(get_current_user),
) -> VisionPrivacySettings:
    """Retrieve vision privacy settings for current user."""
    return vision_service.get_privacy_settings(str(current_user.id))


@router.put("/settings", response_model=VisionPrivacySettings)
async def update_vision_settings(
    settings_in: VisionPrivacySettings,
    current_user: User = Depends(get_current_user),
) -> VisionPrivacySettings:
    """Update vision privacy preferences."""
    return vision_service.update_privacy_settings(str(current_user.id), settings_in)


@router.post("/analyze", response_model=VisionAnalysisResult)
async def analyze_image_json(
    request: AnalyzeImageRequest,
    current_user: User = Depends(get_current_user),
) -> VisionAnalysisResult:
    """Analyze base64-encoded image for scene elements and OCR."""
    try:
        raw_bytes = base64.b64decode(request.image_base64)
    except Exception as err:
        raise ValidationError(f"Malformed base64 image data: {err}")

    return await vision_service.analyze_image(
        image_bytes=raw_bytes,
        user=current_user,
        mime_type=request.mime_type,
        prompt=request.prompt,
        detect_elements=request.detect_elements,
    )


@router.post("/analyze-file", response_model=VisionAnalysisResult)
async def analyze_image_file(
    file: UploadFile = File(...),
    prompt: str | None = Form(None),
    detect_elements: bool = Form(True),
    current_user: User = Depends(get_current_user),
) -> VisionAnalysisResult:
    """Analyze multipart/form-data uploaded image file."""
    content = await file.read()
    if not content:
        raise ValidationError("Uploaded image file is empty.")

    mime_type = file.content_type or "image/jpeg"
    return await vision_service.analyze_image(
        image_bytes=content,
        user=current_user,
        mime_type=mime_type,
        prompt=prompt,
        detect_elements=detect_elements,
    )


@router.post("/screen", response_model=VisionAnalysisResult)
async def analyze_screen_capture(
    request: AnalyzeScreenRequest,
    current_user: User = Depends(get_current_user),
) -> VisionAnalysisResult:
    """Analyze desktop or device screen capture for UI controls and OCR text."""
    try:
        raw_bytes = base64.b64decode(request.screen_base64)
    except Exception as err:
        raise ValidationError(f"Malformed base64 screenshot data: {err}")

    return await vision_service.analyze_screen(
        screen_bytes=raw_bytes,
        user=current_user,
        mime_type=request.mime_type,
        detect_ui_elements=request.detect_ui_elements,
    )


class LiveInspectRequest(BaseModel):
    prompt: str | None = None


@router.get("/live-screen")
async def get_live_screen() -> Response:
    """Stream or return the current live device screen as a PNG image."""
    data = await live_screen_service.capture_screen_bytes(force_refresh=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not capture live screen from Android device over ADB.",
        )
    return Response(content=data, media_type="image/png")


@router.post("/live-inspect")
async def live_inspect_screen(
    request: LiveInspectRequest | None = None,
) -> dict:
    """Capture live Android screen, analyze active window and UI controls via Gemini Vision."""
    prompt = request.prompt if request else ""
    return await live_screen_service.inspect_live_screen(user_question=prompt or "")


@router.get("/timeline")
async def get_visual_timeline(limit: int = 20, minutes: int = 60) -> list[dict]:
    """Retrieve chronological visual memory timeline of observed user activities."""
    from app.ai.vision.visual_cortex import visual_recall_cortex
    return visual_recall_cortex.get_recent_timeline(limit=limit, minutes=minutes)


class AnnotateScreenRequest(BaseModel):
    target: str | None = None
    box_norm: list[int] | None = None
    label: str | None = None
    duration_ms: int = 1500
    auto_draw: bool = True


@router.post("/annotate")
async def annotate_screen_endpoint(request: AnnotateScreenRequest) -> dict:
    """Visually annotate, highlight, or draw bounding boxes on live phone display."""
    from app.ai.vision.annotation_service import annotation_service
    if request.box_norm and len(request.box_norm) == 4:
        draw_info = annotation_service.draw_bounding_box(
            request.box_norm,
            label=request.label or "",
            duration_ms=request.duration_ms,
        )
        return {"success": True, **draw_info}

    target = request.target or "screen center"
    return await annotation_service.detect_and_annotate(
        target_description=target,
        auto_draw=request.auto_draw,
        duration_ms=request.duration_ms,
    )


class TypingPredictionRequest(BaseModel):
    current_input: str = ""
    auto_clipboard: bool = False


@router.post("/typing-prediction")
async def typing_prediction_endpoint(request: TypingPredictionRequest) -> dict:
    """Predict next text input, message replies, or commands based on screen context."""
    from app.ai.vision.typing_prediction_service import typing_prediction_service
    return await typing_prediction_service.predict_next_input(
        current_input=request.current_input,
        auto_clipboard=request.auto_clipboard,
    )


@router.get("/gaze-tracking")
async def gaze_tracking_endpoint(camera: bool = False) -> dict:
    """Estimate user visual attention & gaze zone (via heuristics or front camera)."""
    from app.ai.vision.gaze_tracking_service import gaze_tracking_service
    return await gaze_tracking_service.get_gaze_state(use_camera=camera)


# ---------------------------------------------------------------------------
# Screen Narrator Endpoints
# ---------------------------------------------------------------------------

class NarrateStartRequest(BaseModel):
    interval_sec: float = 10.0


@router.post("/narrate")
async def narrate_screen_once() -> dict:
    """Capture live screen, narrate via Gemini Vision, speak aloud via TTS.

    Returns: {text, spoken, skipped, error, timestamp}
    """
    from app.ai.vision.screen_narrator_service import screen_narrator_service
    return await screen_narrator_service.narrate_once()


@router.post("/narrate/start")
async def start_screen_narration(request: NarrateStartRequest | None = None) -> dict:
    """Start automatic screen narration loop at specified interval.

    Returns: {status, interval_sec, message}
    """
    from app.ai.vision.screen_narrator_service import screen_narrator_service
    interval = (request.interval_sec if request else None) or 10.0
    return await screen_narrator_service.start_auto_narration(interval_sec=interval)


@router.post("/narrate/stop")
async def stop_screen_narration() -> dict:
    """Stop the automatic screen narration loop.

    Returns: {status, message}
    """
    from app.ai.vision.screen_narrator_service import screen_narrator_service
    return await screen_narrator_service.stop_auto_narration()


# ---------------------------------------------------------------------------
# Clipboard Intelligence Endpoint
# ---------------------------------------------------------------------------

class ClipboardEnhanceRequest(BaseModel):
    auto_copy_back: bool = True


@router.post("/clipboard-enhance")
async def clipboard_enhance_endpoint(
    request: ClipboardEnhanceRequest | None = None,
) -> dict:
    """Read clipboard, enhance content with Gemini, optionally write back.

    Body: {auto_copy_back: bool}
    Returns: {original, enhanced, content_type, copied_back, toast_shown, error, timestamp}
    """
    from app.ai.clipboard_intelligence_service import clipboard_intelligence_service
    auto_copy = request.auto_copy_back if request is not None else True
    return await clipboard_intelligence_service.enhance_clipboard(auto_copy_back=auto_copy)
# ── Error Detective Endpoints ─────────────────────────────────────────────────

class ErrorWatchRequest(BaseModel):
    interval_sec: float = 5.0


@router.get("/error-scan")
async def error_scan_endpoint() -> dict:
    """Scan the live screen once for errors, crashes, ANR dialogs, tracebacks, etc.

    Returns: {has_error, error_type, error_message, suggested_fix, severity, timestamp}
    """
    from app.ai.vision.error_detective_service import error_detective_service  # lazy
    return await error_detective_service.scan_for_errors()


@router.post("/error-watch/start")
async def error_watch_start(request: ErrorWatchRequest | None = None) -> dict:
    """Start continuous background error watching at the specified interval.

    Automatically shows a toast + vibrates for high/critical severity errors.
    """
    from app.ai.vision.error_detective_service import error_detective_service  # lazy
    interval = request.interval_sec if request else 5.0
    started = error_detective_service.start_watching(interval_sec=interval)
    if started:
        return {
            "success": True,
            "message": f"Error watch started (interval={interval}s).",
            "is_watching": error_detective_service.is_watching,
        }
    return {
        "success": False,
        "message": "Error watch is already running.",
        "is_watching": error_detective_service.is_watching,
    }


@router.post("/error-watch/stop")
async def error_watch_stop() -> dict:
    """Stop the continuous error watching background task."""
    from app.ai.vision.error_detective_service import error_detective_service  # lazy
    stopped = error_detective_service.stop_watching()
    return {
        "success": stopped,
        "message": "Error watch stopped." if stopped else "Error watch was not running.",
        "is_watching": error_detective_service.is_watching,
    }
