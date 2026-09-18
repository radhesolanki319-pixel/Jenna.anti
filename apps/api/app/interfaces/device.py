"""Future Domain Interface: DeviceController

Defines the contract for phone bridge, Android control, and hardware devices.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DeviceType(str, Enum):
    """Supported device categories."""
    ANDROID = "android"
    DESKTOP = "desktop"
    IOT = "iot"
    SMART_DISPLAY = "smart_display"


class DeviceStatus(str, Enum):
    """Device connectivity states."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    PAIRING = "pairing"
    ERROR = "error"


@dataclass
class DeviceMetadata:
    """Registered device profile."""
    device_id: str
    name: str
    device_type: DeviceType
    status: DeviceStatus
    capabilities: list[str] = field(default_factory=list)
    ip_address: str | None = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DeviceCommandResult:
    """Outcome of sending a control command to an authorized device."""
    device_id: str
    command: str
    success: bool
    response_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceController(ABC):
    """Abstract interface contract for managing and commanding paired devices."""

    @abstractmethod
    async def list_authorized_devices(self, user_id: str) -> list[DeviceMetadata]:
        """Fetch all paired and authorized devices for a user."""
        pass

    @abstractmethod
    async def send_command(
        self,
        device_id: str,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> DeviceCommandResult:
        """Send an authenticated command to an authorized device."""
        pass

    @abstractmethod
    async def receive_event(self, device_id: str, event_payload: dict[str, Any]) -> None:
        """Process incoming hardware or OS notification from a device."""
        pass

    @abstractmethod
    async def get_device_status(self, device_id: str) -> DeviceMetadata:
        """Query real-time connection and telemetry for a specific device."""
        pass
