import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger, request_id_ctx_var


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppException):
    """Validation failed on request data."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class NotFoundError(AppException):
    """Requested resource was not found."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppException):
    """Resource already exists or conflicts with current state."""

    def __init__(self, message: str = "Resource conflict", details: dict[str, Any] | None = None):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UnauthorizedError(AppException):
    """Authentication required or credentials invalid."""

    def __init__(self, message: str = "Authentication required", details: dict[str, Any] | None = None):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppException):
    """Insufficient permissions for requested action."""

    def __init__(self, message: str = "Insufficient permissions", details: dict[str, Any] | None = None):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class DependencyError(AppException):
    """Downstream service or dependency failed."""

    def __init__(self, message: str = "Dependency unavailable or failed", details: dict[str, Any] | None = None):
        super().__init__(
            code="DEPENDENCY_ERROR",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class RateLimitError(AppException):
    """Rate limit or quota allocation exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after_seconds: int = 60,
        details: dict[str, Any] | None = None,
    ):
        det = dict(details or {})
        det["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=det,
        )



class InternalError(AppException):
    """Internal server error."""

    def __init__(self, message: str = "Internal server error", details: dict[str, Any] | None = None):
        super().__init__(
            code="INTERNAL_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
    debug_trace: str | None = None,
) -> JSONResponse:
    """Format standard JSON error response."""
    req_id = request_id_ctx_var.get()
    error_payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details or {},
        "request_id": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if debug_trace and not settings.is_production:
        error_payload["debug_trace"] = debug_trace

    return JSONResponse(status_code=status_code, content={"error": error_payload})


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"AppException: {exc.code} - {exc.message}",
            extra={"status_code": exc.status_code, "details": exc.details},
        )
        return create_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = {"errors": exc.errors()}
        logger.warning("Request validation error", extra={"details": details})
        return create_error_response(
            code="VALIDATION_ERROR",
            message="Request input validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            503: "DEPENDENCY_ERROR",
        }
        code = code_map.get(exc.status_code, "INTERNAL_ERROR")
        logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
        return create_error_response(
            code=code,
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_str = traceback.format_exc()
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={"exception_type": type(exc).__name__},
        )
        debug_trace = trace_str if not settings.is_production else None
        return create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected internal server error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            debug_trace=debug_trace,
        )
