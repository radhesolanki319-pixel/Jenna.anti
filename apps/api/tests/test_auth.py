import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.permissions import Permission, Role, has_permission
from app.core.security import (
    SESSION_COOKIE_NAME,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.main import app
from app.models.audit_events import AuditEvent
from app.models.sessions import Session
from app.models.users import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService


@pytest.fixture
def unique_email():
    """Generate a unique email for test isolation."""
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """Verify PBKDF2 hashing produces distinct salts and validates correctly."""
    pwd = "MySuperSecretPassword123!"
    hashed1 = hash_password(pwd)
    hashed2 = hash_password(pwd)

    # Different salts must yield different hash strings
    assert hashed1 != hashed2
    assert hashed1.startswith("pbkdf2_sha256$600000$")

    # Correct verification
    assert verify_password(pwd, hashed1) is True
    assert verify_password(pwd, hashed2) is True
    assert verify_password("WrongPassword!", hashed1) is False
    assert verify_password("", hashed1) is False


@pytest.mark.asyncio
async def test_permission_matrix():
    """Verify role permission mappings."""
    assert has_permission("admin", Permission.SENSITIVE_ACTION) is True
    assert has_permission("admin", Permission.DEVICE_CONTROL) is True
    assert has_permission("admin", Permission.READ) is True

    assert has_permission("user", Permission.READ) is True
    assert has_permission("user", Permission.WRITE) is True
    assert has_permission("user", Permission.SENSITIVE_ACTION) is False
    assert has_permission("user", Permission.DEVICE_CONTROL) is False

    assert has_permission("readonly", Permission.READ) is True
    assert has_permission("readonly", Permission.WRITE) is False


@pytest.mark.asyncio
async def test_user_registration_success(unique_email):
    """Test registering a new user sets HttpOnly cookie and does not expose secrets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "SecurePassword123!"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert data["user"]["email"] == unique_email
    assert "role" in data["user"]
    # Ensure sensitive fields are NEVER leaked
    assert "password" not in data
    assert "hashed_password" not in data
    assert "token" not in data
    assert "token_hash" not in data

    # Verify cookie is set
    assert SESSION_COOKIE_NAME in response.cookies
    cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header or "httponly" in cookie_header.lower()


@pytest.mark.asyncio
async def test_duplicate_registration_fails(unique_email):
    """Test duplicate registration returns 409 Conflict."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "SecurePassword123!"},
        )
        assert res1.status_code == 201

        res2 = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "SecurePassword123!"},
        )
        assert res2.status_code == 409
        assert "already exists" in res2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_weak_password_rejected():
    """Test registration password length validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "short_pwd@example.com", "password": "short"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_flow_success_and_failure(unique_email):
    """Test login with valid credentials, invalid password, and nonexistent email."""
    password = "CorrectPassword123!"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register user
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": password},
        )
        assert reg_res.status_code == 201

        # 2. Login with wrong password -> 401 generic error
        fail_res = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "WrongPassword!"},
        )
        assert fail_res.status_code == 401
        assert fail_res.json()["error"]["message"] == "Invalid email or password"

        # 3. Login with nonexistent email -> 401 generic error
        fail_email_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": password},
        )
        assert fail_email_res.status_code == 401
        assert fail_email_res.json()["error"]["message"] == "Invalid email or password"

        # 4. Login with correct password -> 200 OK + cookie
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password},
        )
        assert login_res.status_code == 200
        assert SESSION_COOKIE_NAME in login_res.cookies


@pytest.mark.asyncio
async def test_auth_me_endpoint(unique_email):
    """Test GET /api/v1/auth/me for authenticated and unauthenticated requests."""
    password = "ValidPassword123!"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Unauthenticated request -> 401
        unauth_res = await client.get("/api/v1/auth/me")
        assert unauth_res.status_code == 401

        # Register and retain cookies
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": password},
        )
        assert reg_res.status_code == 201

        # Authenticated /me
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["user"]["email"] == unique_email
        assert "session" in me_data
        assert "permissions" in me_data
        assert isinstance(me_data["permissions"], list)
        assert len(me_data["permissions"]) > 0


@pytest.mark.asyncio
async def test_logout_and_session_revocation(unique_email):
    """Test logging out revokes session and prevents further authenticated requests."""
    password = "ValidPassword123!"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register user
        await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": password},
        )

        # 2. Verify active session
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200

        # 3. Logout
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        assert logout_res.json()["status"] == "ok"

        # 4. Attempt to access /me with cleared session -> 401
        me_after = await client.get("/api/v1/auth/me")
        assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_permission_enforcement_and_rbac():
    """Test require_permission dependency checks against user roles."""
    transport = ASGITransport(app=app)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        # Create a non-admin 'user'
        non_admin_email = f"standard_{uuid.uuid4().hex[:8]}@example.com"
        pwd_hash = hash_password("StandardPass123!")
        user = await user_repo.create_user(email=non_admin_email, hashed_password=pwd_hash, role="user")
        await session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as non-admin
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": non_admin_email, "password": "StandardPass123!"},
        )
        assert login_res.status_code == 200

        # Attempt to access sensitive action endpoint requiring SENSITIVE_ACTION (admin only)
        cleanup_res = await client.post("/api/v1/auth/cleanup-sessions")
        # Must be 403 Forbidden!
        assert cleanup_res.status_code == 403
        assert "Access denied" in cleanup_res.json()["error"]["message"]

        # Verify authorization_failure was recorded in audit log
        audit_res = await session.execute(
            select(AuditEvent).where(
                AuditEvent.event_type == "authz",
                AuditEvent.action == "authorization_failure",
                AuditEvent.user_id == user.id,
            )
        )
        assert audit_res.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_audit_logging_integrity(unique_email):
    """Test that auth actions record audit logs without exposing credentials."""
    transport = ASGITransport(app=app)
    password = "AuditTestPassword123!"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        await client.post("/api/v1/auth/register", json={"email": unique_email, "password": password})
        # Failed login
        await client.post("/api/v1/auth/login", json={"email": unique_email, "password": "wrong"})
        # Successful login
        await client.post("/api/v1/auth/login", json={"email": unique_email, "password": password})
        # Logout
        await client.post("/api/v1/auth/logout")

    async with AsyncSessionLocal() as session:
        query = (
            select(AuditEvent)
            .where(AuditEvent.event_type == "auth")
            .order_by(AuditEvent.created_at.desc())
            .limit(20)
        )
        result = await session.execute(query)
        events = result.scalars().all()

        # Find events matching unique_email
        user_events = [
            e for e in events
            if (e.metadata_json and e.metadata_json.get("email") == unique_email)
            or e.action == "logout"
        ]
        actions = [e.action for e in user_events]
        assert "registration" in actions
        assert "login_failure" in actions
        assert "login_success" in actions
        assert "logout" in actions

        # Verify no secrets in metadata
        for event in events:
            meta_str = str(event.metadata_json)
            assert password not in meta_str
            assert "token_hash" not in meta_str
