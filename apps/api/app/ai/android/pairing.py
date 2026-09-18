"""Android Secure Companion Pairing and Token Lifecycle Manager."""

import hashlib
import hmac
import secrets
import time
import uuid
from datetime import datetime, timezone
from app.ai.android.types import AndroidDevice, AndroidDeviceStatus, AndroidPermission
from app.core.errors import ForbiddenError, NotFoundError, ValidationError

PAIRING_CODE_TTL_SECONDS = 300  # 5 minutes


class PairingSession:
    def __init__(self, code: str, user_id: uuid.UUID):
        self.code = code
        self.user_id = user_id
        self.created_at = time.time()
        self.expires_at = self.created_at + PAIRING_CODE_TTL_SECONDS

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class AndroidPairingManager:
    """Manages pairing codes, device cryptographic tokens, and ownership binding."""

    def __init__(self):
        # code -> PairingSession
        self._pending_codes: dict[str, PairingSession] = {}
        # device_id -> AndroidDevice
        self._devices: dict[str, AndroidDevice] = {}
        # raw_token -> device_id
        self._token_map: dict[str, str] = {}

    def generate_pairing_code(self, user_id: uuid.UUID) -> str:
        """Create a cryptographically secure 6-digit pairing code."""
        # Purge expired
        now = time.time()
        self._pending_codes = {k: v for k, v in self._pending_codes.items() if v.expires_at > now}

        code = f"{secrets.randbelow(900000) + 100000}"
        self._pending_codes[code] = PairingSession(code, user_id)
        return code

    def complete_pairing(
        self,
        code: str,
        device_name: str,
        model: str,
        android_version: str,
        sdk_version: int,
        granted_permissions: list[AndroidPermission] | None = None,
    ) -> tuple[AndroidDevice, str]:
        """Verify pairing code and register companion device with secure token."""
        session = self._pending_codes.pop(code, None)
        if not session or session.is_expired():
            raise ValidationError("Invalid or expired pairing code.")

        device_id = f"android-{uuid.uuid4().hex[:12]}"
        raw_token = f"jnd_{secrets.token_urlsafe(32)}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        device = AndroidDevice(
            device_id=device_id,
            user_id=session.user_id,
            device_name=device_name,
            model=model,
            android_version=android_version,
            sdk_version=sdk_version,
            status=AndroidDeviceStatus.ONLINE,
            token_hash=token_hash,
            granted_permissions=granted_permissions or [AndroidPermission.ACCESSIBILITY],
        )

        self._devices[device_id] = device
        self._token_map[raw_token] = device_id
        return device, raw_token

    def verify_token(self, raw_token: str) -> AndroidDevice:
        """Authenticate companion request using bearer token."""
        device_id = self._token_map.get(raw_token)
        if not device_id:
            raise ForbiddenError("Invalid companion device token.")

        device = self._devices.get(device_id)
        if not device or device.status == AndroidDeviceStatus.REVOKED:
            raise ForbiddenError("Device has been revoked or removed.")

        device.last_heartbeat = datetime.now(timezone.utc)
        return device

    def list_user_devices(self, user_id: uuid.UUID) -> list[AndroidDevice]:
        """List all paired devices belonging to the user."""
        return [d for d in self._devices.values() if d.user_id == user_id]

    def get_device(self, device_id: str, user_id: uuid.UUID) -> AndroidDevice:
        """Fetch device ensuring user ownership."""
        device = self._devices.get(device_id)
        if not device or device.user_id != user_id:
            raise NotFoundError(f"Android device '{device_id}' not found.")
        return device

    def revoke_device(self, device_id: str, user_id: uuid.UUID) -> AndroidDevice:
        """Instantly revoke companion credentials and access."""
        device = self.get_device(device_id, user_id)
        device.status = AndroidDeviceStatus.REVOKED

        # Remove tokens
        for token, dev_id in list(self._token_map.items()):
            if dev_id == device_id:
                del self._token_map[token]

        return device


# Global singleton instance
android_pairing_manager = AndroidPairingManager()
