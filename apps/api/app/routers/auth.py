from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Permission, ROLE_PERMISSIONS, require_permission
from app.core.security import SESSION_COOKIE_NAME, get_cookie_settings
from app.models.sessions import Session
from app.models.users import User
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionResponse,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    extract_token_from_request,
    get_current_user_and_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register a new platform user. The first registered user is automatically designated as admin.",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Create account, establish session, and set HttpOnly session cookie."""
    auth_service = AuthService(db)
    user, _, raw_token = await auth_service.register(payload, request=request)

    # Set secure HttpOnly cookie
    cookie_opts = get_cookie_settings()
    response.set_cookie(value=raw_token, **cookie_opts)

    return AuthResponse(
        status="ok",
        message="Registration successful",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate credentials and set HttpOnly session cookie.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate email/password and establish new session."""
    auth_service = AuthService(db)
    user, _, raw_token = await auth_service.login(payload, request=request)

    # Set secure HttpOnly cookie
    cookie_opts = get_cookie_settings()
    response.set_cookie(value=raw_token, **cookie_opts)

    return AuthResponse(
        status="ok",
        message="Login successful",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Revoke the current server-side session and clear the HttpOnly cookie.",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke session in database and delete client cookie."""
    token = extract_token_from_request(request)
    if token:
        auth_service = AuthService(db)
        await auth_service.logout(token, request=request)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return MessageResponse(status="ok", message="Successfully logged out")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current user profile",
    description="Fetch the authenticated user's profile, active session info, and platform permissions.",
)
async def get_me(
    user_and_session: tuple[User, Session] = Depends(get_current_user_and_session),
) -> CurrentUserResponse:
    """Return authenticated user profile and permissions."""
    user, session = user_and_session
    perms = [p.value for p in ROLE_PERMISSIONS.get(user.role, set())]
    perms.sort()

    return CurrentUserResponse(
        user=UserResponse.model_validate(user),
        session=SessionResponse.model_validate(session),
        permissions=perms,
    )


@router.post(
    "/cleanup-sessions",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Cleanup expired sessions",
    description="Administrative maintenance endpoint to purge expired sessions from the database.",
)
async def cleanup_sessions(
    _current_user: User = Depends(require_permission(Permission.SENSITIVE_ACTION)),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete all expired sessions."""
    auth_service = AuthService(db)
    deleted_count = await auth_service.cleanup_expired_sessions()
    return MessageResponse(
        status="ok",
        message=f"Cleaned up {deleted_count} expired session(s)",
    )
