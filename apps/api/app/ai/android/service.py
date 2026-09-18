"""Android Integration Service Facade."""

import uuid
from typing import Any
from app.ai.android.context_manager import android_context_manager
from app.ai.android.control_layer import android_control_layer
from app.ai.android.pairing import android_pairing_manager
from app.ai.android.types import (
    AndroidActionRequest,
    AndroidActionResult,
    AndroidContextPayload,
    AndroidDevice,
    AndroidPermission,
)
from app.events import DomainEvent, DomainEventType, domain_dispatcher
from app.models.users import User


class AndroidService:
    """Consolidated service managing companion pairing, live context, and accessibility execution."""

    def __init__(self):
        self.pairing_manager = android_pairing_manager
        self.context_manager = android_context_manager
        self.control_layer = android_control_layer

    def generate_pairing_code(self, user: User) -> str:
        """Create a 6-digit one-time code to link an Android companion device."""
        code = self.pairing_manager.generate_pairing_code(user.id)
        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                user_id=user.id,
                payload={"action": "generate_android_pairing_code"},
            )
        )
        return code


    def pair_device(
        self,
        code: str,
        device_name: str,
        model: str,
        android_version: str,
        sdk_version: int,
        granted_permissions: list[AndroidPermission] | None = None,
    ) -> tuple[AndroidDevice, str]:
        """Verify code and link device."""
        device, raw_token = self.pairing_manager.complete_pairing(
            code=code,
            device_name=device_name,
            model=model,
            android_version=android_version,
            sdk_version=sdk_version,
            granted_permissions=granted_permissions,
        )
        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                user_id=device.user_id,
                payload={"action": "pair_android_device", "device_id": device.device_id},
            )
        )
        return device, raw_token

    def list_devices(self, user: User) -> list[AndroidDevice]:
        """Fetch all devices owned by the user."""
        return self.pairing_manager.list_user_devices(user.id)

    def revoke_device(self, device_id: str, user: User) -> AndroidDevice:
        """Revoke device authorization."""
        device = self.pairing_manager.revoke_device(device_id, user.id)
        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                user_id=user.id,
                payload={"action": "revoke_android_device", "device_id": device_id},
            )
        )
        return device

    def ingest_context(self, payload: AndroidContextPayload) -> AndroidContextPayload:
        """Sanitize and record incoming screen & notification context."""
        return self.context_manager.ingest_context(payload)

    def get_context(self, device_id: str, user: User) -> AndroidContextPayload | None:
        """Get latest context for user's device."""
        # Ensure user owns device
        self.pairing_manager.get_device(device_id, user.id)
        return self.context_manager.get_latest_context(device_id)

    def dispatch_action(
        self,
        device_id: str,
        request: AndroidActionRequest,
        user: User,
    ) -> AndroidActionResult:
        """Dispatches authorized accessibility command to the companion device."""
        device = self.pairing_manager.get_device(device_id, user.id)
        result = self.control_layer.execute_action(device, request)

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                user_id=user.id,
                payload={
                    "action": "execute_android_action",
                    "device_id": device_id,
                    "action_type": request.action_type.value,
                    "success": result.success,
                },
            )
        )
        return result


# Global singleton instance
android_service = AndroidService()
