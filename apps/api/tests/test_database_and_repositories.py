import uuid
from datetime import datetime, timedelta, timezone
import pytest

from app.core.database import AsyncSessionLocal
from app.repositories.user_repo import UserRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.audit_repo import AuditEventRepository
from app.repositories.settings_repo import SystemSettingsRepository


@pytest.mark.asyncio
async def test_user_repository_crud():
    """Test User creation, retrieval, and timestamps."""
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)

        # Create user
        user = await repo.create_user()
        await session.commit()

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.created_at is not None
        assert user.updated_at is not None

        # Fetch user
        fetched = await repo.get_user(user.id)
        assert fetched is not None
        assert fetched.id == user.id

        # Clean up
        await repo.delete(fetched)
        await session.commit()

        # Confirm deletion
        deleted = await repo.get_user(user.id)
        assert deleted is None


@pytest.mark.asyncio
async def test_session_repository_crud():
    """Test Session creation, user association, and expired cleanup."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        session_repo = SessionRepository(session)

        user = await user_repo.create_user()
        await session.commit()

        # Create active and expired session
        now = datetime.now(timezone.utc)
        active_exp = now + timedelta(hours=2)
        expired_exp = now - timedelta(hours=1)

        s1 = await session_repo.create_session(user.id, expires_at=active_exp)
        s2 = await session_repo.create_session(user.id, expires_at=expired_exp)
        await session.commit()

        assert s1.id is not None
        assert s2.id is not None

        # List by user
        user_sessions = await session_repo.list_by_user(user.id)
        assert len(user_sessions) >= 2

        # Delete expired
        deleted_count = await session_repo.delete_expired(now)
        await session.commit()
        assert deleted_count >= 1

        # Clean up user (cascades sessions)
        user_to_del = await user_repo.get_user(user.id)
        if user_to_del:
            await user_repo.delete(user_to_del)
            await session.commit()


@pytest.mark.asyncio
async def test_audit_event_repository():
    """Test recording and querying structured audit events."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        audit_repo = AuditEventRepository(session)

        user = await user_repo.create_user()
        await session.commit()

        event = await audit_repo.log_event(
            event_type="auth_test",
            action="key_rotation",
            success=True,
            user_id=user.id,
            request_id="req-test-12345",
            metadata={"source": "pytest", "role": "admin"},
        )
        await session.commit()

        assert event.id is not None
        assert event.event_type == "auth_test"
        assert event.success is True
        assert event.metadata_json["source"] == "pytest"

        # List recent
        recent = await audit_repo.list_recent(limit=10)
        assert len(recent) >= 1

        # List by user
        by_user = await audit_repo.list_by_user(user.id)
        assert len(by_user) >= 1
        assert by_user[0].id == event.id

        # Clean up
        user_to_del = await user_repo.get_user(user.id)
        if user_to_del:
            await user_repo.delete(user_to_del)
            await session.commit()


@pytest.mark.asyncio
async def test_system_settings_repository():
    """Test SystemSetting creation, retrieval, and value updates."""
    async with AsyncSessionLocal() as session:
        repo = SystemSettingsRepository(session)
        test_key = f"test.setting.{uuid.uuid4().hex[:8]}"

        # Set initial value
        s1 = await repo.set_value(test_key, {"maintenance": False, "timeout": 30})
        await session.commit()

        assert s1.key == test_key
        assert s1.value["maintenance"] is False

        # Retrieve
        fetched = await repo.get_by_key(test_key)
        assert fetched is not None
        assert fetched.value["timeout"] == 30

        # Update value
        s2 = await repo.set_value(test_key, {"maintenance": True, "timeout": 60})
        await session.commit()

        assert s2.value["maintenance"] is True

        # Clean up
        await repo.delete(s2)
        await session.commit()
