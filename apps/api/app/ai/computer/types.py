"""Computer Control types, schemas, and safety boundaries.

Conforms to Part 7 Phase 1 & Phase 2 specifications:
- Authorized PC pairing and device metadata
- Scoped permissions and allowlists
- Action risk levels: SAFE, SENSITIVE, CRITICAL
- Observe -> Plan -> Permission Check -> Execute -> Observe -> Verify -> Report loop
- Emergency stop & cancellation guarantees
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, Field


class ComputerScope(str, Enum):
    """Granular permissions granted to a paired computer device."""
    SCREEN_OBSERVE = "SCREEN_OBSERVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    KEYBOARD_TYPE = "KEYBOARD_TYPE"
    APP_NAVIGATE = "APP_NAVIGATE"
    BROWSER_AUTOMATE = "BROWSER_AUTOMATE"
    TERMINAL_EXEC = "TERMINAL_EXEC"


class ComputerActionType(str, Enum):
    """Executable actions on a paired computer."""
    OBSERVE = "OBSERVE"
    CLICK = "CLICK"
    TYPE = "TYPE"
    KEY_PRESS = "KEY_PRESS"
    NAVIGATE_APP = "NAVIGATE_APP"
    BROWSER_ACTION = "BROWSER_ACTION"
    TERMINAL_RUN = "TERMINAL_RUN"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class ActionRiskLevel(str, Enum):
    """Risk tier dictating confirmation policy."""
    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class CommandStatus(str, Enum):
    """Lifecycle states of a computer control instruction."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EMERGENCY_STOPPED = "EMERGENCY_STOPPED"


class PairedComputer(BaseModel):
    """Explicitly paired and authorized remote/local computer."""
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_name: str
    os_platform: str = "linux"  # linux, windows, macos, android
    is_authorized: bool = True
    approved_scopes: list[ComputerScope] = Field(
        default_factory=lambda: [
            ComputerScope.SCREEN_OBSERVE,
            ComputerScope.MOUSE_CLICK,
            ComputerScope.KEYBOARD_TYPE,
            ComputerScope.APP_NAVIGATE,
        ]
    )
    ip_address: str | None = None
    paired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComputerCommand(BaseModel):
    """A validated instruction destined for a paired computer."""
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    user_id: str
    action_type: ComputerActionType
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    requires_confirmation: bool = False
    confirmed: bool = False
    status: CommandStatus = CommandStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class ComputerStepProgress(BaseModel):
    """Telemetry emitted during the Observe -> Plan -> Execute -> Verify loop."""
    step_number: int
    stage: str  # OBSERVE, PLAN, PERMISSION_CHECK, EXECUTE, OBSERVE_VERIFY, REPORT
    message: str
    is_terminal: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComputerExecutionResult(BaseModel):
    """Final result of a computer control loop execution."""
    command_id: str
    device_id: str
    success: bool
    action_type: ComputerActionType
    output: dict[str, Any] = Field(default_factory=dict)
    visual_verification_passed: bool = True
    duration_ms: float = 0.0
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PairingRequest(BaseModel):
    """Request to initiate computer pairing."""
    device_name: str = Field(..., min_length=1, max_length=100)
    os_platform: str = Field(default="linux")
    requested_scopes: list[ComputerScope] = Field(default_factory=list)


class PairingResponse(BaseModel):
    """Pairing initialization with pairing token and expiry."""
    device_id: str
    pairing_code: str
    expires_at: datetime
    status: str = "PENDING_AUTHORIZATION"


class CommandExecuteRequest(BaseModel):
    """Request to execute an action on a paired computer."""
    device_id: str
    action_type: ComputerActionType
    parameters: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False  # Set to True when user approves SENSITIVE/CRITICAL action
