import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger, request_id_ctx_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that injects request ID into context, headers, and logs request lifecycle."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine request ID (respect existing X-Request-ID or generate new UUID4)
        incoming_id = request.headers.get("X-Request-ID")
        req_id = incoming_id if incoming_id and incoming_id.strip() else str(uuid.uuid4())

        # Set context variable for structured logging
        token = request_id_ctx_var.set(req_id)
        start_time = time.perf_counter()

        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "http_method": request.method,
                "http_path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id

            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Request failed: {request.method} {request.url.path} ({duration_ms}ms)",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_ctx_var.reset(token)
