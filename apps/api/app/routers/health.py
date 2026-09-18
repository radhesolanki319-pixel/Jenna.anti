from fastapi import APIRouter, Response, status

from app.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.services.health_service import health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Comprehensive health check",
    description="Returns detailed status across all subsystems and external dependencies.",
)
async def get_health() -> HealthResponse:
    """Check overall service and dependency health."""
    return await health_service.get_health()


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Returns 200 if the API process is alive and able to accept traffic.",
)
async def get_liveness() -> LivenessResponse:
    """Liveness probe for process uptime."""
    return health_service.get_liveness()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_200_OK: {"model": ReadinessResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse},
    },
    summary="Readiness probe",
    description="Returns 200 only if all critical dependencies (PostgreSQL, Redis) are operational.",
)
async def get_readiness(response: Response) -> ReadinessResponse:
    """Readiness probe checking PostgreSQL and Redis dependencies."""
    is_ready, data = await health_service.get_readiness()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return data
