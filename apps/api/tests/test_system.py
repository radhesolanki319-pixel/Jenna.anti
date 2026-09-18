import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_system_info_endpoint():
    """Test system info endpoint returns environment, metadata, and observed dependencies."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/info")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "jenna-api"
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0
    assert "dependencies" in data
    assert "postgresql" in data["dependencies"]
    assert "redis" in data["dependencies"]
