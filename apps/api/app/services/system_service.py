import time
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.system import SystemInfoResponse
from app.services.health_service import HealthService, health_service as default_health_service


class SystemService:
    """Service providing runtime metadata, uptime, and system configuration information."""

    def __init__(self, health_svc: HealthService = default_health_service):
        self.health_service = health_svc
        self._start_time = time.time()

    async def get_system_info(self) -> SystemInfoResponse:
        """Collect platform information and dependency status."""
        uptime = round(time.time() - self._start_time, 2)
        db_status = await self.health_service.check_database_health()
        redis_status = await self.health_service.check_redis_health()

        return SystemInfoResponse(
            service=settings.service_name,
            name=settings.app_name,
            version=settings.app_version,
            phase="Phase 2 — Backend Core + Database",
            environment=settings.app_env,
            status="running",
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=uptime,
            dependencies={
                "postgresql": db_status.status,
                "redis": redis_status.status,
            },
        )


system_service = SystemService()
