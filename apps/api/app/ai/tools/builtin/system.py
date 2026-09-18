"""Safe non-sensitive system telemetry tool."""

import os
import platform
import sys
import time
from typing import Any

from app.ai.tools.types import (
    ToolCategory,
    ToolDefinitionSchema,
)
from app.core.permissions import Permission

_START_TIME = time.time()


def get_system_telemetry() -> dict[str, Any]:
    """Retrieve runtime telemetry without disclosing sensitive credentials or paths."""
    uptime_seconds = round(time.time() - _START_TIME, 1)

    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count() or 1,
        "uptime_seconds": uptime_seconds,
        "status": "healthy",
    }


SYSTEM_INFO_TOOL = ToolDefinitionSchema(
    name="system_info",
    description="Retrieve non-sensitive platform status, architecture, Python version, and uptime.",
    category=ToolCategory.SYSTEM,
    parameters=[],
    requires_permission=Permission.READ,
    is_sensitive=False,
    timeout_seconds=5.0,
)
