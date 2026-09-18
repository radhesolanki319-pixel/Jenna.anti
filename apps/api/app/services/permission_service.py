"""Permission service implementing the 3-tier authorization decision model:
- ALLOWED
- DENIED
- REQUIRES_CONFIRMATION

Provides sensitive-action confirmation policies and temporary permission grants.
"""

import time
from typing import Any

from app.core.permissions import Permission, Role, has_permission
from app.interfaces.permissions import (
    AuthorizationDecision,
    PermissionEvaluationResult,
    PermissionService,
)


class DefaultPermissionService(PermissionService):
    """Concrete permission service implementation enforcing role-based capabilities,
    confirmation challenges for high-risk operations, and temporary grants.
    """

    def __init__(self) -> None:
        # Map: user_id -> {permission: expiry_timestamp}
        self._temporary_grants: dict[str, dict[Permission, float]] = {}

    def evaluate_action(
        self,
        role: str,
        required_permission: Permission,
        is_sensitive: bool = False,
        context: dict[str, Any] | None = None,
    ) -> PermissionEvaluationResult:
        """Evaluate if an action is allowed, denied, or requires explicit interactive confirmation."""
        ctx = context or {}
        user_id = ctx.get("user_id")

        # 1. Check temporary grants if user_id is provided
        if user_id and str(user_id) in self._temporary_grants:
            user_grants = self._temporary_grants[str(user_id)]
            expiry = user_grants.get(required_permission)
            if expiry and expiry > time.time():
                return PermissionEvaluationResult(
                    decision=AuthorizationDecision.ALLOWED,
                    reason=f"Action permitted via active temporary grant (expires in {int(expiry - time.time())}s).",
                    required_permission=required_permission,
                )

        # 2. Check base role permission
        if not has_permission(role, required_permission):
            return PermissionEvaluationResult(
                decision=AuthorizationDecision.DENIED,
                reason=f"Role '{role}' lacks required permission '{required_permission.value}'.",
                required_permission=required_permission,
            )

        # 3. Check for sensitive action requiring explicit interactive confirmation
        requires_confirm = is_sensitive or required_permission == Permission.SENSITIVE_ACTION
        if requires_confirm:
            confirmed = ctx.get("confirmed", False)
            if not confirmed:
                action_name = ctx.get("action_name", "sensitive operation")
                return PermissionEvaluationResult(
                    decision=AuthorizationDecision.REQUIRES_CONFIRMATION,
                    reason=f"Action '{action_name}' is sensitive and requires explicit confirmation.",
                    required_permission=required_permission,
                    confirmation_prompt=f"Confirm execution of sensitive action '{action_name}'?",
                )

        # 4. Standard permission granted
        return PermissionEvaluationResult(
            decision=AuthorizationDecision.ALLOWED,
            reason=f"Role '{role}' is authorized for permission '{required_permission.value}'.",
            required_permission=required_permission,
        )

    async def request_confirmation(
        self,
        user_id: str,
        action: str,
        details: dict[str, Any],
    ) -> bool:
        """Prompt user for interactive confirmation before proceeding.

        Foundation implementation: Returns False unless pre-confirmed in details.
        Future phases will link this to WebSocket notifications and mobile push confirmations.
        """
        return bool(details.get("user_confirmed", False))

    def grant_temporary_permission(
        self,
        user_id: str,
        permission: Permission,
        duration_seconds: int = 300,
    ) -> bool:
        """Grant a time-bounded permission window to execute a capability."""
        uid = str(user_id)
        if uid not in self._temporary_grants:
            self._temporary_grants[uid] = {}
        self._temporary_grants[uid][permission] = time.time() + duration_seconds
        return True

    def revoke_temporary_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Revoke a temporary permission prior to expiry."""
        uid = str(user_id)
        if uid in self._temporary_grants and permission in self._temporary_grants[uid]:
            del self._temporary_grants[uid][permission]
            return True
        return False


_default_permission_service: PermissionService | None = None


def get_permission_service() -> PermissionService:
    """Singleton getter for the platform permission service."""
    global _default_permission_service
    if _default_permission_service is None:
        _default_permission_service = DefaultPermissionService()
    return _default_permission_service
