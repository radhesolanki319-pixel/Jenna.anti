import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.core.config import settings

# Use NullPool in testing environments to prevent connection leakage across event loops
is_testing = (
    settings.app_env.lower() in ("test", "testing")
    or "pytest" in sys.modules
    or bool(os.environ.get("PYTEST_CURRENT_TEST"))
)

engine_kwargs: dict = {
    "echo": False,
    "pool_pre_ping": True,
}

if is_testing or "sqlite" in settings.database_url:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
