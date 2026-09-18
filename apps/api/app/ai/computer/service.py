"""Computer Control Service coordinating pairing, validation, loop dispatch, and kill-switches.

Implements Part 7 Phase 1 & Phase 2:
- Authorized pairing lifecycle
- Observe -> Plan -> Check -> Execute -> Verify loop dispatch
- Emergency stop kill-switch across devices
- Scoped permissions and audit trails
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.ai.computer.command_validator import command_validator
from app.ai.computer.controller import computer_controller
from app.ai.computer.loop_orchestrator import control_loop
from app.ai.computer.types import (
    CommandExecuteRequest,
    CommandStatus,
    ComputerCommand,
    ComputerExecutionResult,
    ComputerStepProgress,
    PairedComputer,
    PairingRequest,
    PairingResponse,
)
from app.core.errors import ForbiddenError, NotFoundError
from app.models.users import User


class ComputerControlService:
    """Orchestrates computer pairing, command validation, safety loops, and emergency stops."""

    def __init__(self) -> None:
        self.controller = computer_controller
        self.loop = control_loop
        # In-memory command history: command_id -> ComputerCommand
        self._commands: dict[str, ComputerCommand] = {}

    def initiate_pairing(self, user: User, request: PairingRequest) -> PairingResponse:
        """Begin pairing workflow for a computer device."""
        return self.controller.initiate_pairing(user_id=str(user.id), request=request)

    def complete_pairing(self, user: User, device_id: str, code: str) -> PairedComputer:
        """Confirm pairing code and authorize device."""
        return self.controller.complete_pairing(
            user_id=str(user.id),
            device_id=device_id,
            entered_code=code,
        )

    def list_computers(self, user: User) -> list[PairedComputer]:
        """List all paired computers owned by user."""
        return self.controller.list_computers(user_id=str(user.id))

    def get_computer(self, user: User, device_id: str) -> PairedComputer:
        """Fetch computer by device ID ensuring strict user isolation."""
        return self.controller.get_computer(device_id=device_id, user_id=str(user.id))

    def revoke_computer(self, user: User, device_id: str) -> bool:
        """Revoke authorization of a paired computer."""
        return self.controller.revoke_computer(device_id=device_id, user_id=str(user.id))

    async def execute_command(
        self,
        user: User,
        request: CommandExecuteRequest,
    ) -> tuple[ComputerExecutionResult, list[ComputerStepProgress]]:
        """Dispatch a validated instruction through the Observe-Plan-Check-Execute-Verify loop."""
        device = self.get_computer(user, request.device_id)

        command = ComputerCommand(
            command_id=str(uuid.uuid4()),
            device_id=device.device_id,
            user_id=str(user.id),
            action_type=request.action_type,
            parameters=request.parameters,
            confirmed=request.confirmed,
            status=CommandStatus.QUEUED,
        )

        self._commands[command.command_id] = command
        result, steps = await self.loop.run_cycle(command=command, device=device)
        return result, steps

    def trigger_emergency_stop(self, user: User) -> datetime:
        """Emergency stop kill-switch across all user devices."""
        return self.controller.trigger_emergency_stop(user_id=str(user.id))

    def clear_emergency_stop(self, user: User) -> None:
        """Reset emergency stop status."""
        self.controller.clear_emergency_stop(user_id=str(user.id))

    def is_emergency_stopped(self, user: User) -> bool:
        """Check if user has an active emergency stop."""
        return self.controller.is_emergency_stopped(user_id=str(user.id))


computer_service = ComputerControlService()
