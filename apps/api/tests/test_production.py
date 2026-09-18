"""Tests for Production Hardening, Backup/Restore, and Automated Security Audit (Part 11)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal
from app.core.backup_restore import backup_manager
from app.core.errors import RateLimitError
from app.core.quotas import quota_manager
from app.main import app


def test_quota_and_sliding_window_rate_limiting():
    """Verify rate limits reject burst overages and track daily token quotas."""
    test_user_id = uuid.uuid4()

    # 1. Normal record within bounds
    res1 = quota_manager.record_and_check(test_user_id, estimated_tokens=1000, rpm_limit=5, daily_limit=5000)
    assert res1.allowed is True
    assert res1.current_tokens == 1000
    assert res1.remaining_tokens == 4000

    # 2. Exceed daily quota
    with pytest.raises(RateLimitError, match="Daily token quota exceeded"):
        quota_manager.record_and_check(test_user_id, estimated_tokens=10000, rpm_limit=5, daily_limit=5000)

    # 3. Exceed RPM limit
    fresh_user_id = uuid.uuid4()
    for _ in range(3):
        quota_manager.record_and_check(fresh_user_id, estimated_tokens=10, rpm_limit=3, daily_limit=100000)

    with pytest.raises(RateLimitError, match="rate limit exceeded"):
        quota_manager.record_and_check(fresh_user_id, estimated_tokens=10, rpm_limit=3, daily_limit=100000)


@pytest.mark.asyncio
async def test_backup_and_integrity_verification():
    """Verify database snapshot creation and cryptographic SHA-256 verification."""
    async with AsyncSessionLocal() as db_session:
        manifest = await backup_manager.create_backup(db_session, description="Test snapshot")
        assert manifest.snapshot_id.startswith("backup_")
        assert manifest.checksum_sha256 is not None
        assert len(manifest.checksum_sha256) == 64

        # Verify integrity
        is_valid = backup_manager.verify_backup_integrity(manifest.file_path, manifest.checksum_sha256)
        assert is_valid is True

        # Tampered checksum fails
        is_tampered = backup_manager.verify_backup_integrity(manifest.file_path, "0" * 64)
        assert is_tampered is False

        # List backups
        backups = backup_manager.list_backups()
        assert len(backups) >= 1
        assert any(b["snapshot_id"] == manifest.snapshot_id for b in backups)



@pytest.mark.asyncio
async def test_production_http_endpoints_and_security_audit():
    """Verify production HTTP API endpoints: security audit, quotas, backup."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        email = f"prod_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg.status_code == 201

        # 1. Run automated security audit
        audit_res = await client.get("/api/v1/production/security-audit")
        assert audit_res.status_code == 200
        report = audit_res.json()
        assert report["overall_status"] == "READY_FOR_PRODUCTION"
        assert report["passed_checks"] >= 8
        assert report["failed_checks"] == 0

        # Verify key invariant checks are evaluated
        check_names = [c["check_name"] for c in report["checks"]]
        assert "Zero Plaintext Secrets In Telemetry" in check_names
        assert "Multi-Tenant User Isolation" in check_names
        assert "3-Tier Permission Hierarchy Enforcement" in check_names
        assert "Self-Improvement Human Signoff Invariant" in check_names
        assert "Global Emergency Stop Kill-Switch" in check_names

        # 2. Get quotas status
        quotas_res = await client.get("/api/v1/production/quotas")
        assert quotas_res.status_code == 200
        quotas_data = quotas_res.json()
        assert "daily_limit_tokens" in quotas_data
        assert "remaining_tokens" in quotas_data

        # 3. Create backup snapshot via API
        backup_res = await client.post(
            "/api/v1/production/backup",
            json={"description": "API-triggered backup snapshot"},
        )
        assert backup_res.status_code == 200
        snap = backup_res.json()
        assert "snapshot_id" in snap
        assert "checksum_sha256" in snap

        # 4. List backups
        list_res = await client.get("/api/v1/production/backups")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1
