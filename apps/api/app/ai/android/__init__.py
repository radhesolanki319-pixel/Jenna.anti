"""Android Integration Package (Part 10)."""

from app.ai.android.context_manager import AndroidContextManager, android_context_manager
from app.ai.android.control_layer import AndroidControlLayer, android_control_layer
from app.ai.android.pairing import AndroidPairingManager, android_pairing_manager
from app.ai.android.service import AndroidService, android_service
from app.ai.android.types import (
    AndroidActionRequest,
    AndroidActionResult,
    AndroidActionType,
    AndroidContextPayload,
    AndroidDevice,
    AndroidDeviceStatus,
    AndroidNotificationItem,
    AndroidPermission,
    NavigationTarget,
)

__all__ = [
    "AndroidActionRequest",
    "AndroidActionResult",
    "AndroidActionType",
    "AndroidContextManager",
    "AndroidContextPayload",
    "AndroidControlLayer",
    "AndroidDevice",
    "AndroidDeviceStatus",
    "AndroidNotificationItem",
    "AndroidPairingManager",
    "AndroidPermission",
    "AndroidService",
    "NavigationTarget",
    "android_context_manager",
    "android_control_layer",
    "android_pairing_manager",
    "android_service",
]
