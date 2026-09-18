from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_settings import SystemSetting
from app.repositories.base import BaseRepository


class SystemSettingsRepository(BaseRepository[SystemSetting]):
    """Repository handling SystemSetting database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(SystemSetting, session)

    async def get_by_key(self, key: str) -> SystemSetting | None:
        """Fetch setting by its unique configuration key."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def set_value(self, key: str, value: Any) -> SystemSetting:
        """Create or update a configuration setting."""
        setting = await self.get_by_key(key)
        if setting:
            setting.value = value
            await self.session.flush()
            await self.session.refresh(setting)
            return setting
        return await self.create(key=key, value=value)
