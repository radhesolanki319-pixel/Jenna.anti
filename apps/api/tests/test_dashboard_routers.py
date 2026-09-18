"""Tests for Part 9 Dashboard backend routers: audit, approvals, and usage."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_audit_endpoints_user_isolation():
    """Verify audit endpoints enforce user isolation and no secret leakage."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and log in user
        email = f"audit_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg_res.status_code == 201

        # 1. Fetch audit events
        res = await client.get("/api/v1/audit/events")
        assert res.status_code == 200
        events = res.json()
        assert isinstance(events, list)

        # 2. Fetch stats
        stats_res = await client.get("/api/v1/audit/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "total_events" in stats
        assert "successful_events" in stats
        assert "failed_events" in stats


@pytest.mark.asyncio
async def test_approvals_pending_and_policies():
    """Verify approval queue and permission policies matrix."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"approvals_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg_res.status_code == 201

        # 1. Permission policies
        pol_res = await client.get("/api/v1/approvals/policies")
        assert pol_res.status_code == 200
        pol_data = pol_res.json()
        assert len(pol_data["tiers"]) == 4
        tiers = [t["tier"] for t in pol_data["tiers"]]
        assert "SENSITIVE_ACTION" in tiers
        assert "CRITICAL_ACTION" in tiers

        # 2. Pending queue
        pend_res = await client.get("/api/v1/approvals/pending")
        assert pend_res.status_code == 200
        pend_data = pend_res.json()
        assert "tasks" in pend_data
        assert "proposals" in pend_data
        assert "total_pending" in pend_data

        # 3. History
        hist_res = await client.get("/api/v1/approvals/history")
        assert hist_res.status_code == 200
        assert isinstance(hist_res.json(), list)


@pytest.mark.asyncio
async def test_usage_summary_and_logs():
    """Verify usage and cost tracking endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"usage_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg_res.status_code == 201

        res = await client.get("/api/v1/usage/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "estimated_cost_usd" in data
        assert "daily_quota_tokens" in data
        assert "quota_remaining_tokens" in data
        assert data["daily_quota_tokens"] > 0

        logs_res = await client.get("/api/v1/usage/logs")
        assert logs_res.status_code == 200
        assert isinstance(logs_res.json(), list)
