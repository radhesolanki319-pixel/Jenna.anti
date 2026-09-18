import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from app.main import app
from app.schemas.health import ServiceStatus


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test comprehensive health endpoint returns status of all services."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy", "degraded")
    assert data["service"] == "jenna-api"
    assert "version" in data
    assert "services" in data
    assert isinstance(data["services"], list)
    service_names = [s["name"] for s in data["services"]]
    assert "postgresql" in service_names
    assert "redis" in service_names


@pytest.mark.asyncio
async def test_liveness_endpoint():
    """Test liveness probe returns 200 and ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "jenna-api"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_endpoint_healthy():
    """Test readiness probe returns 200 when all dependencies are ready."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ready"] is True
    assert len(data["dependencies"]) >= 2


@pytest.mark.asyncio
async def test_readiness_endpoint_unhealthy_returns_503():
    """Test readiness probe returns 503 when a critical dependency fails."""
    transport = ASGITransport(app=app)
    unhealthy_db = ServiceStatus(name="postgresql", status="unhealthy", detail="Connection timeout")

    with patch("app.services.health_service.health_service.check_database_health", return_value=unhealthy_db):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["ready"] is False
