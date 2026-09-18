from fastapi import APIRouter

from app.schemas.system import SystemInfoResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="System information & telemetry",
    description="Returns platform runtime metadata, uptime, and observed dependency health.",
)
async def get_system_info() -> SystemInfoResponse:
    """Retrieve system diagnostics and metadata."""
    return await system_service.get_system_info()
