"""Computer Control & Device Management API Router.

Exposes endpoints for device pairing, scoped authorization, command loops, and emergency stops.
"""

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.ai.computer import (
    CommandExecuteRequest,
    ComputerExecutionResult,
    ComputerStepProgress,
    PairedComputer,
    PairingRequest,
    PairingResponse,
    computer_service,
)
from app.models.users import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/devices", tags=["Computer & Device Control"])


class ConfirmPairingPayload(BaseModel):
    device_id: str
    pairing_code: str


class CommandExecutionResponse(BaseModel):
    result: ComputerExecutionResult
    steps: list[ComputerStepProgress]


class EmergencyStopStatus(BaseModel):
    is_emergency_stopped: bool


@router.get("", response_model=list[PairedComputer])
async def list_paired_devices(
    current_user: User = Depends(get_current_user),
) -> list[PairedComputer]:
    """List all authorized and paired computers for the current user."""
    return computer_service.list_computers(current_user)


@router.post("/pair/initiate", response_model=PairingResponse)
async def initiate_device_pairing(
    request: PairingRequest,
    current_user: User = Depends(get_current_user),
) -> PairingResponse:
    """Initiate an explicit computer pairing request and generate an authorization code."""
    return computer_service.initiate_pairing(current_user, request)


@router.post("/pair/confirm", response_model=PairedComputer)
async def confirm_device_pairing(
    payload: ConfirmPairingPayload,
    current_user: User = Depends(get_current_user),
) -> PairedComputer:
    """Confirm the pairing code and authorize the computer device."""
    return computer_service.complete_pairing(
        user=current_user,
        device_id=payload.device_id,
        code=payload.pairing_code,
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_paired_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Immediately revoke computer authorization."""
    computer_service.revoke_computer(current_user, device_id)


@router.post("/execute", response_model=CommandExecutionResponse)
async def execute_computer_command(
    request: CommandExecuteRequest,
    current_user: User = Depends(get_current_user),
) -> CommandExecutionResponse:
    """Run an action through the Observe -> Plan -> Check -> Execute -> Verify loop."""
    result, steps = await computer_service.execute_command(current_user, request)
    return CommandExecutionResponse(result=result, steps=steps)


@router.post("/emergency-stop")
async def trigger_emergency_stop(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Emergency kill-switch: immediately halt all active actions on all devices."""
    stopped_at = computer_service.trigger_emergency_stop(current_user)
    return {
        "status": "EMERGENCY_STOPPED",
        "halted_at": stopped_at.isoformat(),
        "message": "All computer execution loops have been halted immediately.",
    }


@router.post("/emergency-stop/clear")
async def clear_emergency_stop(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Clear emergency stop and resume normal operations."""
    computer_service.clear_emergency_stop(current_user)
    return {
        "status": "ACTIVE",
        "message": "Emergency stop has been lifted. Operations resumed.",
    }


@router.get("/emergency-stop/status", response_model=EmergencyStopStatus)
async def get_emergency_stop_status(
    current_user: User = Depends(get_current_user),
) -> EmergencyStopStatus:
    """Check if emergency stop is currently active."""
    is_stopped = computer_service.is_emergency_stopped(current_user)
    return EmergencyStopStatus(is_emergency_stopped=is_stopped)
