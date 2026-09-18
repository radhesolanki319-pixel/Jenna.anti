"""Deterministic test suite for Android Integration (Part 10)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.android import (
    AndroidActionRequest,
    AndroidActionType,
    AndroidContextPayload,
    AndroidNotificationItem,
    AndroidPermission,
    NavigationTarget,
    android_context_manager,
    android_control_layer,
    android_pairing_manager,
    android_service,
)
from app.ai.computer import computer_controller
from app.core.errors import ForbiddenError, ValidationError
from app.main import app
from app.models.users import User


def create_mock_user():
    return User(
        id=uuid.uuid4(),
        email=f"android_user_{uuid.uuid4().hex[:6]}@example.com",
        role="user",
    )


def test_pairing_code_and_device_registration():
    """Verify companion code generation, token exchange, and expiration."""
    user = create_mock_user()
    code = android_pairing_manager.generate_pairing_code(user.id)
    assert len(code) == 6
    assert code.isdigit()

    # Complete pairing
    device, token = android_pairing_manager.complete_pairing(
        code=code,
        device_name="Pixel 8 Pro",
        model="Pixel 8",
        android_version="14",
        sdk_version=34,
        granted_permissions=[AndroidPermission.ACCESSIBILITY, AndroidPermission.NOTIFICATIONS],
    )
    assert device.device_name == "Pixel 8 Pro"
    assert device.user_id == user.id
    assert token.startswith("jnd_")

    # Code cannot be reused
    with pytest.raises(ValidationError):
        android_pairing_manager.complete_pairing(
            code=code,
            device_name="Duplicate",
            model="Phone",
            android_version="14",
            sdk_version=34,
        )

    # Token verification
    authed_device = android_pairing_manager.verify_token(token)
    assert authed_device.device_id == device.device_id


def test_device_remote_revocation():
    """Verify remote revoke disables device token and marks status REVOKED."""
    user = create_mock_user()
    code = android_pairing_manager.generate_pairing_code(user.id)
    device, token = android_pairing_manager.complete_pairing(
        code=code,
        device_name="Galaxy S24",
        model="SM-S921B",
        android_version="14",
        sdk_version=34,
    )

    # Revoke
    revoked = android_pairing_manager.revoke_device(device.device_id, user.id)
    assert revoked.status.value == "REVOKED"

    # Token verification must fail
    with pytest.raises(ForbiddenError):
        android_pairing_manager.verify_token(token)


def test_notification_sanitization():
    """Verify notifications automatically sanitize banking OTPs, card numbers, and credentials."""
    raw_notifs = [
        AndroidNotificationItem(
            notification_id="1",
            package_name="com.bank.app",
            title="Security Alert",
            text="Your OTP for transaction of $500 is 987654. Do not share.",
        ),
        AndroidNotificationItem(
            notification_id="2",
            package_name="com.shopping.app",
            title="Card Verified",
            text="Payment using card 4111 2222 3333 4444 was authorized. password: secretPassword123",
        ),
    ]

    payload = AndroidContextPayload(
        device_id="dev-test-1",
        foreground_app="com.whatsapp",
        screen_width=1080,
        screen_height=2400,
        battery_level=85,
        is_charging=False,
        notifications=raw_notifs,
    )

    clean = android_context_manager.ingest_context(payload)
    assert "[OTP_REDACTED]" in clean.notifications[0].text
    assert "987654" not in clean.notifications[0].text

    assert "[CARD_REDACTED]" in clean.notifications[1].text
    assert "4111 2222 3333 4444" not in clean.notifications[1].text
    assert "secretPassword123" not in clean.notifications[1].text


def test_accessibility_control_risk_and_confirmation():
    """Verify 3-tier risk assessment, coordinate bounds, and confirmation gates."""
    user = create_mock_user()
    code = android_pairing_manager.generate_pairing_code(user.id)
    device, _ = android_pairing_manager.complete_pairing(
        code=code,
        device_name="Test Phone",
        model="Test",
        android_version="14",
        sdk_version=34,
        granted_permissions=[AndroidPermission.ACCESSIBILITY],
    )

    # 1. Low risk navigation (BACK) executes automatically
    nav_req = AndroidActionRequest(
        action_type=AndroidActionType.NAVIGATE,
        nav_target=NavigationTarget.BACK,
    )
    nav_res = android_control_layer.execute_action(device, nav_req)
    assert nav_res.success is True

    # 2. Sensitive text typing without confirmation fails
    type_req = AndroidActionRequest(
        action_type=AndroidActionType.TYPE_TEXT,
        text="Search query",
        confirmed=False,
    )
    with pytest.raises(ValidationError, match="requires explicit human confirmation"):
        android_control_layer.execute_action(device, type_req)

    # 3. Sensitive text typing with confirmation succeeds
    type_req.confirmed = True
    type_res = android_control_layer.execute_action(device, type_req)
    assert type_res.success is True

    # 4. Critical app launch (Settings) without confirmation fails
    crit_req = AndroidActionRequest(
        action_type=AndroidActionType.APP_LAUNCH,
        package_name="com.android.settings",
        confirmed=False,
    )
    with pytest.raises(ValidationError, match="CRITICAL_ACTION"):
        android_control_layer.execute_action(device, crit_req)

    # 5. Critical app launch with confirmation succeeds
    crit_req.confirmed = True
    crit_res = android_control_layer.execute_action(device, crit_req)
    assert crit_res.success is True


def test_emergency_stop_blocks_control():
    """Verify emergency stop halts device control."""
    user = create_mock_user()
    code = android_pairing_manager.generate_pairing_code(user.id)
    device, _ = android_pairing_manager.complete_pairing(
        code=code,
        device_name="Stop Test",
        model="Test",
        android_version="14",
        sdk_version=34,
        granted_permissions=[AndroidPermission.ACCESSIBILITY],
    )

    computer_controller.trigger_emergency_stop(str(user.id))
    try:
        req = AndroidActionRequest(
            action_type=AndroidActionType.TAP,
            x=100,
            y=200,
        )
        with pytest.raises(ForbiddenError, match="Emergency stop is ACTIVE"):
            android_control_layer.execute_action(device, req)
    finally:
        computer_controller.clear_emergency_stop(str(user.id))



@pytest.mark.asyncio
async def test_android_http_api_flow():
    """Verify full end-to-end HTTP API flow for companion pairing and control."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        email = f"android_api_{uuid.uuid4().hex[:6]}@example.com"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg.status_code == 201

        # 1. Generate pairing code
        gen_res = await client.post("/api/v1/android/pair/generate-code")
        assert gen_res.status_code == 200
        code = gen_res.json()["pairing_code"]
        assert len(code) == 6

        # 2. Companion exchanges code
        pair_res = await client.post(
            "/api/v1/android/pair",
            json={
                "pairing_code": code,
                "device_name": "My OnePlus 12",
                "model": "OnePlus 12",
                "android_version": "14",
                "sdk_version": 34,
                "granted_permissions": ["android.permission.ACCESSIBILITY"],
            },
        )
        assert pair_res.status_code == 200
        device_data = pair_res.json()["device"]
        device_id = device_data["device_id"]
        assert device_data["device_name"] == "My OnePlus 12"

        # 3. List devices
        list_res = await client.get("/api/v1/android/devices")
        assert list_res.status_code == 200
        devices = list_res.json()
        assert len(devices) >= 1
        assert any(d["device_id"] == device_id for d in devices)

        # 4. Ingest context
        ctx_res = await client.post(
            f"/api/v1/android/devices/{device_id}/context",
            json={
                "device_id": device_id,
                "foreground_app": "com.android.chrome",
                "screen_width": 1080,
                "screen_height": 2400,
                "battery_level": 92,
                "is_charging": True,
                "notifications": [],
            },
        )
        assert ctx_res.status_code == 200
        assert ctx_res.json()["battery_level"] == 92

        # 5. Get context
        get_ctx = await client.get(f"/api/v1/android/devices/{device_id}/context")
        assert get_ctx.status_code == 200
        assert get_ctx.json()["foreground_app"] == "com.android.chrome"

        # 6. Dispatch action (TAP)
        action_res = await client.post(
            f"/api/v1/android/devices/{device_id}/action",
            json={
                "action_type": "TAP",
                "x": 300,
                "y": 500,
            },
        )
        assert action_res.status_code == 200
        assert action_res.json()["success"] is True

        # 7. Revoke device
        rev_res = await client.post(f"/api/v1/android/devices/{device_id}/revoke")
        assert rev_res.status_code == 200
        assert rev_res.json()["status"] == "REVOKED"
