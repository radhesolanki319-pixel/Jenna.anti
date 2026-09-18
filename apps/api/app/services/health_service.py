import time
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.core.database import engine as default_engine
from app.core.logging import logger
from app.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    ServiceStatus,
)
from app.services.redis_service import RedisService, redis_service as default_redis_service


class HealthService:
    """Service handling health checks for database, cache, and application runtime."""

    def __init__(
        self,
        engine: AsyncEngine = default_engine,
        redis_svc: RedisService = default_redis_service,
    ):
        self.engine = engine
        self.redis_service = redis_svc
        self.startup_time = time.time()

    async def check_database_health(self) -> ServiceStatus:
        """Check PostgreSQL database connectivity and query execution."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return ServiceStatus(name="postgresql", status="healthy")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ServiceStatus(name="postgresql", status="unhealthy", detail=str(e))

    async def check_redis_health(self) -> ServiceStatus:
        """Check Redis connectivity."""
        return await self.redis_service.health_check()

    async def get_health(self) -> HealthResponse:
        """Evaluate overall health status across all dependencies."""
        db_status = await self.check_database_health()
        redis_status = await self.check_redis_health()

        services = [db_status, redis_status]
        all_healthy = all(s.status == "healthy" for s in services)
        any_healthy = any(s.status == "healthy" for s in services)

        if all_healthy:
            overall = "ok"
        elif any_healthy:
            overall = "degraded"
        else:
            overall = "unhealthy"

        return HealthResponse(
            status=overall,
            service=settings.service_name,
            version=settings.app_version,
            phase="Phase 2 — Backend Core + Database",
            timestamp=datetime.now(timezone.utc).isoformat(),
            services=services,
        )

    def get_liveness(self) -> LivenessResponse:
        """Liveness check indicating whether the HTTP process is running."""
        return LivenessResponse(
            status="ok",
            service=settings.service_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    async def get_readiness(self) -> tuple[bool, ReadinessResponse]:
        """Readiness check indicating whether all critical dependencies are ready."""
        db_status = await self.check_database_health()
        redis_status = await self.check_redis_health()

        dependencies = [db_status, redis_status]
        is_ready = all(dep.status == "healthy" for dep in dependencies)

        response = ReadinessResponse(
            status="ok" if is_ready else "not_ready",
            service=settings.service_name,
            ready=is_ready,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dependencies=dependencies,
        )
        return is_ready, response


health_service = HealthService()
