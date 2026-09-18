"""Service for managing and loading user-specific or system-wide personality configurations."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.personality import SystemInstructionBuilder
from app.repositories.settings_repo import SystemSettingsRepository
from app.schemas.personality import PersonalitySettings


class PersonalityService:
    """Provides personality retrieval, updates, and instruction compilation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings_repo = SystemSettingsRepository(session)

    def _settings_key(self, user_id: uuid.UUID | None) -> str:
        """Derive database setting key for user personality preferences."""
        if user_id:
            return f"personality:{user_id}"
        return "personality:global_default"

    async def get_settings(self, user_id: uuid.UUID | None = None) -> PersonalitySettings:
        """Fetch personality settings for user or return default."""
        key = self._settings_key(user_id)
        record = await self.settings_repo.get_by_key(key)
        if record and isinstance(record.value, dict):
            try:
                return PersonalitySettings.model_validate(record.value)
            except Exception:
                pass
        return PersonalitySettings()

    async def update_settings(
        self,
        settings: PersonalitySettings,
        user_id: uuid.UUID | None = None,
    ) -> PersonalitySettings:
        """Persist updated personality configuration."""
        key = self._settings_key(user_id)
        await self.settings_repo.set_value(key, settings.model_dump())
        return settings

    async def get_instruction_builder(
        self,
        user_id: uuid.UUID | None = None,
    ) -> SystemInstructionBuilder:
        """Construct a configured SystemInstructionBuilder for a user."""
        settings = await self.get_settings(user_id)
        return SystemInstructionBuilder(settings)
