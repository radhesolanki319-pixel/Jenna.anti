"""Android Integration API Router (Part 10).

Exposes companion pairing, live context ingestion, remote revoke,
and authorized accessibility device control.
"""

from typing import Any
from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel, Field

from app.ai.android import (
    AndroidActionRequest,
    AndroidActionResult,
    AndroidContextPayload,
    AndroidDevice,
    AndroidPermission,
    android_service,
)
from app.models.users import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/android", tags=["Android Companion Integration"])


class PairingCodeResponse(BaseModel):
    pairing_code: str
    expires_in_seconds: int = 300


class PairCompanionRequest(BaseModel):
    pairing_code: str
    device_name: str = Field(..., min_length=2, max_length=64)
    model: str = Field(default="Android Device")
    android_version: str = Field(default="14")
    sdk_version: int = Field(default=34)
    granted_permissions: list[AndroidPermission] = Field(default_factory=list)


class PairCompanionResponse(BaseModel):
    device: AndroidDevice
    device_token: str


@router.post("/pair/generate-code", response_model=PairingCodeResponse, summary="Generate Android pairing code")
async def generate_android_pairing_code(
    current_user: User = Depends(get_current_user),
) -> PairingCodeResponse:
    """Generate a short-lived 6-digit pairing code to link an Android companion device."""
    code = android_service.generate_pairing_code(current_user)
    return PairingCodeResponse(pairing_code=code, expires_in_seconds=300)


@router.post("/pair", response_model=PairCompanionResponse, summary="Pair companion device")
async def pair_companion_device(
    payload: PairCompanionRequest,
) -> PairCompanionResponse:
    """Exchange pairing code for a secure companion bearer token."""
    device, raw_token = android_service.pair_device(
        code=payload.pairing_code,
        device_name=payload.device_name,
        model=payload.model,
        android_version=payload.android_version,
        sdk_version=payload.sdk_version,
        granted_permissions=payload.granted_permissions,
    )
    return PairCompanionResponse(device=device, device_token=raw_token)


@router.get("/devices", response_model=list[AndroidDevice], summary="List paired Android devices")
async def list_android_devices(
    current_user: User = Depends(get_current_user),
) -> list[AndroidDevice]:
    """List all paired Android devices owned by the authenticated user."""
    return android_service.list_devices(current_user)


@router.post("/devices/{device_id}/revoke", response_model=AndroidDevice, summary="Revoke Android device")
async def revoke_android_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
) -> AndroidDevice:
    """Instantly revoke companion credentials and access."""
    return android_service.revoke_device(device_id, current_user)


@router.post("/devices/{device_id}/context", response_model=AndroidContextPayload, summary="Ingest companion context")
async def ingest_companion_context(
    device_id: str,
    payload: AndroidContextPayload,
) -> AndroidContextPayload:
    """Ingest live OS telemetry, foreground app, and sanitized notifications from companion."""
    payload.device_id = device_id
    return android_service.ingest_context(payload)


@router.get("/devices/{device_id}/context", response_model=AndroidContextPayload | None, summary="Get latest companion context")
async def get_companion_context(
    device_id: str,
    current_user: User = Depends(get_current_user),
) -> AndroidContextPayload | None:
    """Retrieve most recent sanitized context for a paired device."""
    return android_service.get_context(device_id, current_user)


@router.post("/devices/{device_id}/action", response_model=AndroidActionResult, summary="Dispatch accessibility action")
async def dispatch_android_action(
    device_id: str,
    payload: AndroidActionRequest,
    current_user: User = Depends(get_current_user),
) -> AndroidActionResult:
    """Execute authorized accessibility action (tap, swipe, type, navigation, app launch)."""
    return android_service.dispatch_action(
        device_id=device_id,
        request=payload,
        user=current_user,
    )
