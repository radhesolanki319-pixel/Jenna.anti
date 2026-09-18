import pytest
from httpx import AsyncClient, ASGITransport

from app.core.errors import NotFoundError, ValidationError, ConflictError, DependencyError
from app.main import app


@pytest.mark.asyncio
async def test_request_id_generated():
    """Verify that an X-Request-ID header is automatically generated if none provided."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health/live")

    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) > 10


@pytest.mark.asyncio
async def test_custom_request_id_preserved():
    """Verify that client-supplied X-Request-ID is preserved across request/response."""
    transport = ASGITransport(app=app)
    custom_id = "client-req-999-abc"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health/live", headers={"X-Request-ID": custom_id})

    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
async def test_404_structured_error_response():
    """Verify that 404 errors return standard structured JSON format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/non_existent_route")

    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "NOT_FOUND"
    assert "message" in error
    assert "request_id" in error
    assert "timestamp" in error


def test_exception_classes():
    """Verify custom exception status codes and codes."""
    not_found = NotFoundError("Missing item")
    assert not_found.code == "NOT_FOUND"
    assert not_found.status_code == 404

    val_err = ValidationError("Bad input")
    assert val_err.code == "VALIDATION_ERROR"
    assert val_err.status_code == 422

    conflict = ConflictError("Already exists")
    assert conflict.code == "CONFLICT"
    assert conflict.status_code == 409

    dep_err = DependencyError("DB unreachable")
    assert dep_err.code == "DEPENDENCY_ERROR"
    assert dep_err.status_code == 503
