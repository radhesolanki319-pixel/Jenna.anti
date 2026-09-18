import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling User database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def create_user(
        self,
        email: str | None = None,
        hashed_password: str | None = None,
        role: str = "admin",
    ) -> User:
        """Create and persist a new user record."""
        target_email = email.strip().lower() if email else f"user_{uuid.uuid4().hex[:8]}@example.com"
        target_pwd = hashed_password or "dummy_unusable_hash"
        return await self.create(
            email=target_email,
            hashed_password=target_pwd,
            role=role,
            is_active=True,
        )

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """Fetch user by ID."""
        return await self.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by case-insensitive email."""
        query = select(User).where(func.lower(User.email) == email.strip().lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_users(self) -> int:
        """Return total number of registered users."""
        query = select(func.count(User.id))
        result = await self.session.execute(query)
        return result.scalar_one() or 0
