"""Command validator, sandboxing policy, and risk assessment for PC Control.

Implements Part 7 Phase 1 & Phase 2:
- Command allowlists and strict denylists
- Coordinate and payload bounds validation
- Scoped authorization verification
- 3-tier risk assessment (SAFE, SENSITIVE, CRITICAL)
- Rejection of unrestricted shell execution
"""

import re
from typing import Any

from app.ai.computer.types import (
    ActionRiskLevel,
    ComputerActionType,
    ComputerScope,
    PairedComputer,
)
from app.core.errors import ForbiddenError, ValidationError

# Permitted terminal command prefixes
SAFE_TERMINAL_COMMANDS = {
    "ls", "dir", "pwd", "date", "uptime", "whoami", "echo",
    "git status", "git diff", "git log", "git branch",
    "python --version", "node -v", "npm -v", "cat", "grep",
}

# Strict destructive / forbidden command patterns
FORBIDDEN_COMMAND_PATTERNS = [
    r"\brm\s+(-[rfRF]+\s+|--recursive\s+)?/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpasswd\b",
    r"\bchmod\s+[0-7]*777\b",
    r"\bcurl\s+.*\|\s*(sh|bash)\b",
    r"\bwget\s+.*\|\s*(sh|bash)\b",
    r"\bformat\s+[c-zC-Z]:\b",
    r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\b",
]

# Sensitive action triggers (deletion, purchasing, credential modification)
CRITICAL_ACTION_PATTERNS = [
    r"\bdelete\b",
    r"\bpurchase\b",
    r"\bbuy\s+now\b",
    r"\bpay\b",
    r"\btransfer\b",
    r"\bpassword\b",
    r"\bapi[_-]?key\b",
]


class CommandValidator:
    """Validates parameters, checks scopes, and classifies risk levels."""

    @staticmethod
    def assess_risk(action_type: ComputerActionType, parameters: dict[str, Any]) -> ActionRiskLevel:
        """Determine risk level of requested computer action."""
        if action_type == ComputerActionType.EMERGENCY_STOP:
            return ActionRiskLevel.SAFE

        if action_type == ComputerActionType.OBSERVE:
            return ActionRiskLevel.SAFE

        if action_type in (ComputerActionType.CLICK, ComputerActionType.TYPE, ComputerActionType.KEY_PRESS):
            text = str(parameters.get("text", "")).lower()
            for pattern in CRITICAL_ACTION_PATTERNS:
                if re.search(pattern, text):
                    return ActionRiskLevel.CRITICAL
            return ActionRiskLevel.SAFE

        if action_type == ComputerActionType.TERMINAL_RUN:
            command = str(parameters.get("command", "")).strip().lower()
            # Any non-trivial terminal execution is at least SENSITIVE
            for pattern in CRITICAL_ACTION_PATTERNS:
                if re.search(pattern, command):
                    return ActionRiskLevel.CRITICAL
            return ActionRiskLevel.SENSITIVE

        if action_type in (ComputerActionType.NAVIGATE_APP, ComputerActionType.BROWSER_ACTION):
            url_or_app = str(parameters.get("url", "") or parameters.get("app_name", "")).lower()
            if any(k in url_or_app for k in ("bank", "checkout", "settings/password")):
                return ActionRiskLevel.CRITICAL
            return ActionRiskLevel.SENSITIVE

        return ActionRiskLevel.SENSITIVE

    @classmethod
    def validate_command(
        cls,
        action_type: ComputerActionType,
        parameters: dict[str, Any],
        device: PairedComputer,
    ) -> None:
        """Validate command parameters and enforce device authorization scopes."""
        # 1. Device Authorization
        if not device.is_authorized:
            raise ForbiddenError(f"Device '{device.device_id}' is not authorized for computer control.")

        # 2. Scope verification
        required_scope_map = {
            ComputerActionType.OBSERVE: ComputerScope.SCREEN_OBSERVE,
            ComputerActionType.CLICK: ComputerScope.MOUSE_CLICK,
            ComputerActionType.TYPE: ComputerScope.KEYBOARD_TYPE,
            ComputerActionType.KEY_PRESS: ComputerScope.KEYBOARD_TYPE,
            ComputerActionType.NAVIGATE_APP: ComputerScope.APP_NAVIGATE,
            ComputerActionType.BROWSER_ACTION: ComputerScope.BROWSER_AUTOMATE,
            ComputerActionType.TERMINAL_RUN: ComputerScope.TERMINAL_EXEC,
            ComputerActionType.EMERGENCY_STOP: None,
        }

        req_scope = required_scope_map.get(action_type)
        if req_scope and req_scope not in device.approved_scopes:
            raise ForbiddenError(
                f"Device '{device.device_name}' lacks the required '{req_scope.value}' scope."
            )

        # 3. Parameter bounds checking
        if action_type == ComputerActionType.CLICK:
            x = parameters.get("x")
            y = parameters.get("y")
            if x is None or y is None or not (0 <= float(x) <= 3840) or not (0 <= float(y) <= 2160):
                raise ValidationError("Click coordinates out of valid range (0 <= x <= 3840, 0 <= y <= 2160).")

        # 4. Terminal Command Allowlist & Denylist
        if action_type == ComputerActionType.TERMINAL_RUN:
            command = str(parameters.get("command", "")).strip()
            if not command:
                raise ValidationError("Terminal command cannot be empty.")

            # Denylist check
            for pattern in FORBIDDEN_COMMAND_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    raise ForbiddenError(f"Command '{command}' is blocked by security policy (destructive command).")

            # Check prefix allowlist
            cmd_base = command.split()[0].lower()
            is_allowed_prefix = any(command.lower().startswith(allowed) for allowed in SAFE_TERMINAL_COMMANDS) or cmd_base in SAFE_TERMINAL_COMMANDS
            if not is_allowed_prefix:
                raise ForbiddenError(
                    f"Command '{command}' is not on the approved terminal execution allowlist."
                )


command_validator = CommandValidator()
