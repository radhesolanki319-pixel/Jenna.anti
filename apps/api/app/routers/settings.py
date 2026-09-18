"""Settings API Router: User-specific and system configurations."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User
from app.schemas.personality import PersonalitySettings, PersonalitySettingsResponse
from app.services.auth_service import get_current_user
from app.services.personality_service import PersonalityService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_personality_service(db: AsyncSession = Depends(get_db)) -> PersonalityService:
    """Dependency injector for PersonalityService."""
    return PersonalityService(session=db)


@router.get(
    "/personality",
    response_model=PersonalitySettingsResponse,
    summary="Get persona configuration",
    description="Returns active personality, tone, verbosity, and language preferences for the current user.",
)
async def get_personality_settings(
    current_user: User = Depends(get_current_user),
    service: PersonalityService = Depends(get_personality_service),
) -> PersonalitySettingsResponse:
    settings = await service.get_settings(user_id=current_user.id)
    return PersonalitySettingsResponse(settings=settings, user_id=str(current_user.id))


@router.put(
    "/personality",
    response_model=PersonalitySettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update persona configuration",
    description="Updates personality, tone, verbosity, and language preferences for the current user.",
)
async def update_personality_settings(
    payload: PersonalitySettings,
    current_user: User = Depends(get_current_user),
    service: PersonalityService = Depends(get_personality_service),
) -> PersonalitySettingsResponse:
    updated = await service.update_settings(settings=payload, user_id=current_user.id)
    return PersonalitySettingsResponse(settings=updated, user_id=str(current_user.id))
