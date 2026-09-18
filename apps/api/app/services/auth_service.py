from datetime import datetime, timedelta, timezone
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ConflictError, UnauthorizedError
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models.sessions import Session
from app.models.users import User
from app.repositories.audit_repo import AuditEventRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


def extract_token_from_request(request: Request) -> str | None:
    """Extract raw session token from HttpOnly cookie or Authorization Bearer header."""
    # 1. Cookie check (primary)
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    # 2. Bearer token check (fallback for API / testing clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


class AuthService:
    """Business logic for user registration, authentication, sessions, and authorization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.audit_repo = AuditEventRepository(db)

    async def register(
        self,
        payload: RegisterRequest,
        request: Request | None = None,
    ) -> tuple[User, Session, str]:
        """Register a new user, issue initial session, and log the audit event."""
        # 1. Check if user already exists
        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError("An account with this email already exists")

        # 2. Assign admin to first registered user, regular user thereafter
        user_count = await self.user_repo.count_users()
        role = "admin" if user_count == 0 else "user"

        # 3. Hash password securely (PBKDF2-HMAC-SHA256, 600,000 rounds)
        hashed_pwd = hash_password(payload.password)

        # 4. Persist user
        user = await self.user_repo.create_user(
            email=payload.email,
            hashed_password=hashed_pwd,
            role=role,
        )

        # 5. Issue session
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_DURATION_SECONDS)

        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None
        request_id = getattr(request.state, "request_id", None) if request else None

        session = await self.session_repo.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 6. Audit logging (never log credentials or tokens)
        await self.audit_repo.log_event(
            event_type="auth",
            action="registration",
            success=True,
            user_id=user.id,
            request_id=request_id,
            metadata={"email": user.email, "role": role},
        )

        return user, session, raw_token

    async def login(
        self,
        payload: LoginRequest,
        request: Request | None = None,
    ) -> tuple[User, Session, str]:
        """Authenticate user credentials, issue session, and record audit trail."""
        request_id = getattr(request.state, "request_id", None) if request else None
        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        user = await self.user_repo.get_by_email(payload.email)

        # Constant-time comparison or fail-safe dummy check
        if not user or not verify_password(payload.password, user.hashed_password):
            await self.audit_repo.log_event(
                event_type="auth",
                action="login_failure",
                success=False,
                user_id=user.id if user else None,
                request_id=request_id,
                metadata={"email": payload.email, "reason": "invalid_credentials"},
            )
            await self.db.commit()
            # Use generic message to prevent account enumeration
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            await self.audit_repo.log_event(
                event_type="auth",
                action="login_failure",
                success=False,
                user_id=user.id,
                request_id=request_id,
                metadata={"email": payload.email, "reason": "account_inactive"},
            )
            await self.db.commit()
            raise UnauthorizedError("Account is inactive")

        # Create session
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_DURATION_SECONDS)

        session = await self.session_repo.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.audit_repo.log_event(
            event_type="auth",
            action="login_success",
            success=True,
            user_id=user.id,
            request_id=request_id,
            metadata={"email": user.email, "ip_address": ip_address, "session_id": str(session.id)},
        )

        return user, session, raw_token

    async def logout(
        self,
        token: str,
        request: Request | None = None,
    ) -> bool:
        """Revoke the current session."""
        request_id = getattr(request.state, "request_id", None) if request else None
        token_hash = hash_session_token(token)

        # Attempt to identify the session/user for audit logging
        now = datetime.now(timezone.utc)
        session = await self.session_repo.get_valid_session(token_hash, now)
        user_id = session.user_id if session else None

        revoked = await self.session_repo.revoke_session(token_hash)

        await self.audit_repo.log_event(
            event_type="auth",
            action="logout",
            success=revoked,
            user_id=user_id,
            request_id=request_id,
            metadata={"revoked": revoked},
        )

        return revoked

    async def get_user_from_token(self, token: str) -> tuple[User, Session]:
        """Validate session token and return user and session models."""
        token_hash = hash_session_token(token)
        now = datetime.now(timezone.utc)
        session = await self.session_repo.get_valid_session(token_hash, now)

        if not session or session.is_revoked or session.expires_at <= now:
            raise UnauthorizedError("Invalid or expired session")

        if not session.user or not session.user.is_active:
            raise UnauthorizedError("User account is inactive or disabled")

        return session.user, session

    async def cleanup_expired_sessions(self) -> int:
        """Purge all expired sessions from the database."""
        now = datetime.now(timezone.utc)
        return await self.session_repo.delete_expired(now)


# FastAPI Dependencies
async def get_current_user_and_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> tuple[User, Session]:
    """Dependency validating credentials and returning authenticated (User, Session)."""
    token = extract_token_from_request(request)
    if not token:
        raise UnauthorizedError("Not authenticated")

    service = AuthService(db)
    return await service.get_user_from_token(token)


async def get_current_user(
    user_and_session: tuple[User, Session] = Depends(get_current_user_and_session),
) -> User:
    """Dependency returning authenticated User."""
    return user_and_session[0]
