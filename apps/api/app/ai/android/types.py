"""Type definitions and domain contracts for Android Integration (Part 10)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AndroidDeviceStatus(str, Enum):
    """Device lifecycle states."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    REVOKED = "REVOKED"
    PAIRING = "PAIRING"


class AndroidPermission(str, Enum):
    """OS permissions reported by the companion app."""
    ACCESSIBILITY = "android.permission.ACCESSIBILITY"
    NOTIFICATIONS = "android.permission.BIND_NOTIFICATION_LISTENER"
    SCREEN_CAPTURE = "android.permission.SCREEN_CAPTURE"
    CAMERA = "android.permission.CAMERA"
    AUDIO_RECORD = "android.permission.RECORD_AUDIO"


class AndroidActionType(str, Enum):
    """Supported accessibility and device control actions."""
    TAP = "TAP"
    SWIPE = "SWIPE"
    TYPE_TEXT = "TYPE_TEXT"
    PRESS_KEY = "PRESS_KEY"
    APP_LAUNCH = "APP_LAUNCH"
    NAVIGATE = "NAVIGATE"  # BACK, HOME, RECENTS


class NavigationTarget(str, Enum):
    """System navigation gestures."""
    BACK = "BACK"
    HOME = "HOME"
    RECENTS = "RECENTS"
    NOTIFICATIONS = "NOTIFICATIONS"
    QUICK_SETTINGS = "QUICK_SETTINGS"


class AndroidDevice(BaseModel):
    """Registered Android companion device."""
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: uuid.UUID
    device_name: str
    model: str
    android_version: str
    sdk_version: int
    status: AndroidDeviceStatus = AndroidDeviceStatus.ONLINE
    token_hash: str
    granted_permissions: list[AndroidPermission] = Field(default_factory=list)
    paired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class AndroidNotificationItem(BaseModel):
    """Sanitized notification ingested from device."""
    notification_id: str
    package_name: str
    title: str
    text: str
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_clearable: bool = True


class AndroidContextPayload(BaseModel):
    """Live OS telemetry and screen context from companion."""
    device_id: str
    foreground_app: str
    screen_width: int
    screen_height: int
    battery_level: int = Field(ge=0, le=100)
    is_charging: bool
    network_type: str = "WIFI"
    notifications: list[AndroidNotificationItem] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AndroidActionRequest(BaseModel):
    """Command dispatched to paired device accessibility service."""
    action_type: AndroidActionType
    x: int | None = None
    y: int | None = None
    x2: int | None = None
    y2: int | None = None
    text: str | None = None
    nav_target: NavigationTarget | None = None
    package_name: str | None = None
    confirmed: bool = False
    reason: str | None = None


class AndroidActionResult(BaseModel):
    """Result returned after device action execution and verification."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: AndroidActionType
    success: bool
    verification_state: str
    message: str
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
