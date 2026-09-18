"""Future Domain Interface: PermissionService

Defines the contract for extensible authorization decisions (ALLOWED, DENIED, REQUIRES_CONFIRMATION)
and sensitive-action approval policies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.permissions import Permission


class AuthorizationDecision(str, Enum):
    """Result of evaluating whether an action is permitted."""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"


@dataclass
class PermissionEvaluationResult:
    """Detailed evaluation result returned by the permission service."""
    decision: AuthorizationDecision
    reason: str
    required_permission: Permission
    confirmation_prompt: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PermissionService(ABC):
    """Abstract interface contract for extensible permission enforcement."""

    @abstractmethod
    def evaluate_action(
        self,
        role: str,
        required_permission: Permission,
        is_sensitive: bool = False,
        context: dict[str, Any] | None = None,
    ) -> PermissionEvaluationResult:
        """Evaluate if an action is permitted, denied, or requires explicit confirmation."""
        pass

    @abstractmethod
    async def request_confirmation(
        self,
        user_id: str,
        action: str,
        details: dict[str, Any],
    ) -> bool:
        """Prompt user for interactive confirmation before proceeding with sensitive execution."""
        pass

    @abstractmethod
    def grant_temporary_permission(
        self,
        user_id: str,
        permission: Permission,
        duration_seconds: int = 300,
    ) -> bool:
        """Grant a time-bounded permission window to execute a specific capability."""
        pass

    @abstractmethod
    def revoke_temporary_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Revoke a temporary permission prior to expiry."""
        pass
