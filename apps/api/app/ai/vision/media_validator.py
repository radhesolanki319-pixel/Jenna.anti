"""Media safety and payload validator.

Implements Part 6 Phase 2:
- Media validation (format, size limits, header magic bytes)
- Corrupted and oversized payload filtering
- Rejection of unsafe or unrecognized formats
"""

from app.ai.vision.types import MediaValidationResult

ALLOWED_IMAGE_MIMES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


class MediaValidator:
    """Validates raw image buffers before ingestion and multimodal routing."""

    @staticmethod
    def validate(image_data: bytes, declared_mime: str = "image/jpeg") -> MediaValidationResult:
        """Verify image data format, size limits, and magic byte integrity."""
        size = len(image_data)
        if size == 0:
            return MediaValidationResult(
                is_valid=False,
                error_message="Image buffer is empty (0 bytes).",
            )

        if size > MAX_IMAGE_SIZE_BYTES:
            return MediaValidationResult(
                is_valid=False,
                size_bytes=size,
                error_message=f"Image size {size} exceeds maximum allowable limit ({MAX_IMAGE_SIZE_BYTES} bytes).",
            )

        norm_mime = declared_mime.lower().strip()
        if norm_mime not in ALLOWED_IMAGE_MIMES:
            return MediaValidationResult(
                is_valid=False,
                size_bytes=size,
                error_message=f"Unsupported image MIME type: '{declared_mime}'. Allowed formats: image/jpeg, image/png, image/webp.",
            )

        # Magic bytes verification
        expected_magics = ALLOWED_IMAGE_MIMES[norm_mime]
        has_valid_magic = any(image_data.startswith(magic) for magic in expected_magics)

        if not has_valid_magic:
            # Check if webp specifically
            if norm_mime == "image/webp" and len(image_data) >= 12 and image_data[8:12] == b"WEBP":
                has_valid_magic = True

        if not has_valid_magic:
            return MediaValidationResult(
                is_valid=False,
                size_bytes=size,
                error_message=f"Image header magic bytes do not match declared MIME type '{declared_mime}'.",
            )

        return MediaValidationResult(
            is_valid=True,
            format=norm_mime,
            size_bytes=size,
        )


media_validator = MediaValidator()
