import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

# Context variable for request-scoped correlation ID
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)

SENSITIVE_PATTERNS = re.compile(
    r"(password|token|secret|api_?key|auth|bearer|credential|cookie|session)",
    re.IGNORECASE,
)


def sanitize_data(data: Any, depth: int = 0) -> Any:
    """Recursively mask sensitive values to prevent secret leakage in logs."""
    if depth > 5:
        return "<max_depth_exceeded>"
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if SENSITIVE_PATTERNS.search(str(k)):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_data(v, depth + 1)
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item, depth + 1) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or request_id_ctx_var.get()

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": settings.service_name,
            "request_id": req_id,
            "event": record.getMessage(),
            "logger": record.name,
        }

        # Include extra attributes if provided in record.__dict__
        extra_data = {}
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "request_id"
        }
        for k, v in record.__dict__.items():
            if k not in standard_attrs and not k.startswith("_"):
                extra_data[k] = v

        if extra_data:
            log_entry["metadata"] = sanitize_data(extra_data)

        if record.exc_info and not settings.is_production:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # Remove existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

    # Quieten chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("jenna.core")
