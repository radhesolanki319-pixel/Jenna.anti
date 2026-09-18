import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request payload."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    """User login request payload."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user response schema. NEVER contains password hashes or secrets."""
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    """Public session metadata schema."""
    id: uuid.UUID
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Successful authentication response."""
    status: str = "ok"
    message: str
    user: UserResponse


class CurrentUserResponse(BaseModel):
    """Current authenticated user profile with active session and permissions."""
    user: UserResponse
    session: SessionResponse | None = None
    permissions: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Generic message response."""
    status: str = "ok"
    message: str
