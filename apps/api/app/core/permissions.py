from enum import Enum
from typing import Set

from fastapi import Depends

from app.core.errors import ForbiddenError


class Permission(str, Enum):
    """Conceptual platform permissions for Jenna AI."""
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"
    DEVICE_CONTROL = "DEVICE_CONTROL"
    SENSITIVE_ACTION = "SENSITIVE_ACTION"
    LOW_RISK_ACTION = "LOW_RISK_ACTION"
    CRITICAL_ACTION = "CRITICAL_ACTION"


# Compatibility alias
PermissionAction = Permission


class Role(str, Enum):
    """User roles defining baseline permission bundles."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    Role.ADMIN.value: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE,
        Permission.NETWORK,
        Permission.DEVICE_CONTROL,
        Permission.SENSITIVE_ACTION,
        Permission.LOW_RISK_ACTION,
        Permission.CRITICAL_ACTION,
    },
    Role.USER.value: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE,
        Permission.NETWORK,
        Permission.LOW_RISK_ACTION,
    },
    Role.READONLY.value: {
        Permission.READ,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a given role possesses the required permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms


def require_permission(required: Permission):
    """FastAPI dependency factory enforcing a specific permission on the authenticated user."""
    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import get_db
    from app.models.users import User
    from app.repositories.audit_repo import AuditEventRepository
    from app.services.auth_service import get_current_user

    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not has_permission(current_user.role, required):
            audit_repo = AuditEventRepository(db)
            request_id = getattr(request.state, "request_id", None)
            await audit_repo.log_event(
                event_type="authz",
                action="authorization_failure",
                success=False,
                user_id=current_user.id,
                request_id=request_id,
                metadata={
                    "required_permission": required.value,
                    "user_role": current_user.role,
                    "path": request.url.path,
                },
            )
            await db.commit()
            raise ForbiddenError(
                message=f"Access denied. Missing required permission: {required.value}",
                details={"required_permission": required.value, "user_role": current_user.role},
            )
        return current_user

    return permission_checker
