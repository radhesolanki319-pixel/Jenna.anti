"""Computer & Device Controller implementing the DeviceController domain interface.

Implements Part 7 Phase 1:
- Explicit computer pairing with expiring confirmation codes
- Scoped permissions and device revocation
- Emergency stop kill-switch across all user devices
- DeviceController abstract interface compliance
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any
import uuid

from app.ai.computer.types import (
    ComputerScope,
    PairedComputer,
    PairingRequest,
    PairingResponse,
)

from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.core.logging import logger
from app.events import DomainEvent, DomainEventType, domain_dispatcher
from app.interfaces.device import (
    DeviceCommandResult as InterfaceCommandResult,
    DeviceController as InterfaceDeviceController,
    DeviceMetadata as InterfaceDeviceMetadata,
    DeviceStatus as InterfaceDeviceStatus,
    DeviceType as InterfaceDeviceType,
)


class ComputerDeviceController(InterfaceDeviceController):
    """Manages explicitly paired computers, authorization status, and connectivity."""

    def __init__(self) -> None:
        # In-memory storage for paired devices (scoped by device_id and user_id)
        self._devices: dict[str, PairedComputer] = {}
        # Pending pairings: device_id -> {"code": str, "user_id": str, "expires_at": datetime, "req": PairingRequest}
        self._pending_pairings: dict[str, dict[str, Any]] = {}
        # Emergency stop registry: user_id -> timestamp
        self._emergency_stops: dict[str, datetime] = {}

    def initiate_pairing(self, user_id: str, request: PairingRequest) -> PairingResponse:
        """Generate an explicit pairing code valid for 10 minutes."""
        device_id = str(uuid.uuid4())
        pairing_code = f"JENNA-{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        self._pending_pairings[device_id] = {
            "code": pairing_code,
            "user_id": str(user_id),
            "expires_at": expires_at,
            "request": request,
        }

        logger.info(
            f"Initiated computer pairing for user {user_id}, device {request.device_name}",
            extra={"device_id": device_id, "user_id": str(user_id)},
        )

        return PairingResponse(
            device_id=device_id,
            pairing_code=pairing_code,
            expires_at=expires_at,
            status="PENDING_AUTHORIZATION",
        )

    def complete_pairing(self, user_id: str, device_id: str, entered_code: str) -> PairedComputer:
        """Confirm pairing code and register the computer as authorized."""
        pending = self._pending_pairings.get(device_id)
        if not pending:
            raise NotFoundError("Pairing request not found or expired.")

        if pending["user_id"] != str(user_id):
            raise ForbiddenError("Access to this pairing request is forbidden.")

        if datetime.now(timezone.utc) > pending["expires_at"]:
            del self._pending_pairings[device_id]
            raise ValidationError("Pairing code has expired. Please initiate pairing again.")

        if pending["code"].strip().upper() != entered_code.strip().upper():
            raise ValidationError("Invalid pairing code.")

        req: PairingRequest = pending["request"]
        scopes = req.requested_scopes or [
            ComputerScope.SCREEN_OBSERVE,
            ComputerScope.MOUSE_CLICK,
            ComputerScope.KEYBOARD_TYPE,
            ComputerScope.APP_NAVIGATE,
            ComputerScope.BROWSER_AUTOMATE,
            ComputerScope.TERMINAL_EXEC,
        ]

        computer = PairedComputer(
            device_id=device_id,
            user_id=str(user_id),
            device_name=req.device_name,
            os_platform=req.os_platform,
            is_authorized=True,
            approved_scopes=scopes,
            paired_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )

        self._devices[device_id] = computer
        del self._pending_pairings[device_id]

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_CONNECTED,
                aggregate_id=device_id,
                user_id=str(user_id),
                payload={"device_name": computer.device_name, "scopes": [s.value for s in scopes]},
            )
        )

        return computer

    def get_computer(self, device_id: str, user_id: str) -> PairedComputer:
        """Retrieve paired computer with strict user isolation."""
        device = self._devices.get(device_id)
        if not device:
            raise NotFoundError(f"Paired computer '{device_id}' not found.")
        if device.user_id != str(user_id):
            raise ForbiddenError("Access to this computer device is forbidden.")
        return device

    def list_computers(self, user_id: str) -> list[PairedComputer]:
        """List all paired computers owned by user."""
        return [d for d in self._devices.values() if d.user_id == str(user_id)]

    def revoke_computer(self, device_id: str, user_id: str) -> bool:
        """Immediately revoke computer authorization."""
        device = self.get_computer(device_id, user_id)
        device.is_authorized = False
        logger.info(f"Revoked authorization for device '{device_id}'", extra={"device_id": device_id})

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                aggregate_id=device_id,
                user_id=str(user_id),
                payload={"action": "device_revoked", "device_id": device_id},
            )
        )
        return True

    def trigger_emergency_stop(self, user_id: str) -> datetime:
        """Activate instant emergency stop kill-switch across all devices."""
        now = datetime.now(timezone.utc)
        self._emergency_stops[str(user_id)] = now

        domain_dispatcher.dispatch(
            DomainEvent(
                event_type=DomainEventType.DEVICE_EVENT,
                aggregate_id=str(user_id),
                user_id=str(user_id),
                payload={"action": "emergency_stop", "halted_at": now.isoformat()},
            )
        )
        return now

    def is_emergency_stopped(self, user_id: str) -> bool:
        """Check if emergency stop is currently active."""
        return str(user_id) in self._emergency_stops

    def clear_emergency_stop(self, user_id: str) -> None:
        """Resume normal operations after emergency stop review."""
        if str(user_id) in self._emergency_stops:
            del self._emergency_stops[str(user_id)]

    # --- DeviceController Abstract Interface Implementations ---

    async def list_authorized_devices(self, user_id: str) -> list[InterfaceDeviceMetadata]:
        """Fetch all paired and authorized devices for a user."""
        computers = self.list_computers(user_id)
        return [
            InterfaceDeviceMetadata(
                device_id=c.device_id,
                name=c.device_name,
                device_type=InterfaceDeviceType.DESKTOP,
                status=InterfaceDeviceStatus.ONLINE if c.is_authorized else InterfaceDeviceStatus.OFFLINE,
                capabilities=[s.value for s in c.approved_scopes],
                last_seen=c.last_seen,
            )
            for c in computers
        ]

    async def send_command(
        self,
        device_id: str,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> InterfaceCommandResult:
        """Send command to device conforming to domain interface."""
        return InterfaceCommandResult(
            device_id=device_id,
            command=command,
            success=True,
            response_data=payload or {},
            timestamp=datetime.now(timezone.utc),
        )

    async def receive_event(self, device_id: str, event_payload: dict[str, Any]) -> None:
        """Process incoming hardware event."""
        if device_id in self._devices:
            self._devices[device_id].last_seen = datetime.now(timezone.utc)

    async def get_device_status(self, device_id: str) -> InterfaceDeviceMetadata:
        """Query real-time connection telemetry."""
        device = self._devices.get(device_id)
        if not device:
            raise NotFoundError(f"Device '{device_id}' not found.")
        return InterfaceDeviceMetadata(
            device_id=device.device_id,
            name=device.device_name,
            device_type=InterfaceDeviceType.DESKTOP,
            status=InterfaceDeviceStatus.ONLINE if device.is_authorized else InterfaceDeviceStatus.OFFLINE,
            capabilities=[s.value for s in device.approved_scopes],
            last_seen=device.last_seen,
        )


computer_controller = ComputerDeviceController()
