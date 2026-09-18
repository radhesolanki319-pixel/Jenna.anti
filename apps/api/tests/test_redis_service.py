import uuid
import pytest
from app.services.redis_service import redis_service


@pytest.mark.asyncio
async def test_redis_service_operations():
    """Test get, set, delete and health check against active Redis."""
    test_key = f"jenna:test:{uuid.uuid4().hex}"
    test_value = "phase2_redis_verified"

    # Set
    success = await redis_service.set(test_key, test_value, ttl=60)
    assert success is True

    # Get
    val = await redis_service.get(test_key)
    assert val == test_value

    # Delete
    deleted = await redis_service.delete(test_key)
    assert deleted is True

    # Confirm deleted
    val_after = await redis_service.get(test_key)
    assert val_after is None


@pytest.mark.asyncio
async def test_redis_health_check():
    """Test Redis connectivity health check returns healthy status."""
    status = await redis_service.health_check()
    assert status.name == "redis"
    assert status.status == "healthy"
