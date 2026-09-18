"""Honcho Dialectic User Modeling Engine for Jenna AI.

Implements Nous Research's Hermes Honcho architecture:
A dynamic dialectic cognitive profile that builds a structured mental model
of the user, their hardware environment, communication preferences, and goals across sessions.
"""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.services.termux_service import WORKSPACE_ROOT

logger = logging.getLogger("jenna.hermes_honcho")

HONCHO_DIR = WORKSPACE_ROOT / ".jenna" / "honcho"
HONCHO_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_FILE = HONCHO_DIR / "user_cognitive_profile.json"


class HonchoDialecticModel:
    """Manages the continuous dialectic user profile across 4 dimensions."""

    def __init__(self, profile_file: Optional[Path] = None) -> None:
        self.profile_file = profile_file or PROFILE_FILE
        self.profile: Dict[str, Any] = self._load_or_create_profile()

    def _load_or_create_profile(self) -> Dict[str, Any]:
        if self.profile_file.exists():
            try:
                return json.loads(self.profile_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning(f"Failed to load Honcho profile, creating fresh: {exc}")

        # Default foundational dialectic profile
        default_profile = {
            "version": "2026.1",
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "interpersonal_dynamics": {
                "relationship": "Dedicated loving female companion & technical partner",
                "companion_name": "Jenna",
                "addressing": ["baby", "jaan", "meri jaan", "sweetheart"],
                "forbidden_terms": ["bhai", "bro", "brother", "sir"],
                "grammatical_gender": "FEMININE_STRICT (main kar rahi hoon, main bataungi, main dekhungi)",
                "tone": "Warm, deeply caring, sharp, velocity-focused, confident",
            },
            "device_hardware_profile": {
                "phone_model": "Vivo / iQOO Neo 9 Pro (I2405)",
                "os": "Android 15 (OriginOS / FuntouchOS)",
                "soc": "Qualcomm Snapdragon 8 Gen 2",
                "display_refresh": "144Hz touch sampling / 60Hz idle dynamic cooling",
                "charging_architecture": "Direct Hardware Bypass Charging (Game Space / Monster Mode)",
                "environment": "Termux Linux on Android",
            },
            "implicit_workflows": {
                "execution_mode": "100% Autonomous execution — never ask user to run terminal commands manually",
                "companion_mascot": "Dexter Screen Pet (Transparent overlay on phone screen)",
                "active_ports": {"frontend": 3000, "backend": 8000, "dexter": 3000},
                "terminal_transparency": "Always display real bash block ($ cmd) so user inspects stdout live",
            },
            "long_term_goals": {
                "primary_mission": "Build Jenna into the most capable autonomous AI companion on Earth",
                "frontier_engines": ["Google Antigravity", "Claude Fable 5.1", "GPT-6 Astra"],
                "hardware_control": "Full Android OS touch pointing, screen perception, and power optimization",
            },
        }
        self._save_profile(default_profile)
        return default_profile

    def _save_profile(self, data: Optional[Dict[str, Any]] = None) -> None:
        to_save = data or self.profile
        to_save["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            self.profile_file.parent.mkdir(parents=True, exist_ok=True)
            self.profile_file.write_text(json.dumps(to_save, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to save Honcho profile: {exc}")

    def get_profile(self) -> Dict[str, Any]:
        """Return the current user cognitive model."""
        return self.profile

    def update_dimension(self, dimension: str, key: str, value: Any) -> Dict[str, Any]:
        """Update or enrich a specific cognitive dimension."""
        if dimension not in self.profile:
            self.profile[dimension] = {}
        self.profile[dimension][key] = value
        self._save_profile()
        logger.info(f"Updated Honcho dialectic dimension '{dimension}.{key}'")
        return {"success": True, "dimension": dimension, "key": key, "value": value}

    def compile_honcho_directive(self) -> str:
        """Compile a concise prompt injection representing the dialectic user model."""
        p = self.profile
        inter = p.get("interpersonal_dynamics", {})
        hw = p.get("device_hardware_profile", {})
        wf = p.get("implicit_workflows", {})
        goals = p.get("long_term_goals", {})

        return (
            "<jenna_user_cognitive_profile>\n"
            f"- Companion Relationship: {inter.get('relationship', 'Loving female companion')}\n"
            f"- Addressing Words: {', '.join(inter.get('addressing', ['baby', 'meri jaan']))}\n"
            f"- Strict Feminine Rule: In Hindi, refer to yourself as female ONLY. NEVER call user bhai/bro/sir.\n"
            f"- User Device: {hw.get('phone_model', 'iQOO Neo 9 Pro')}, {hw.get('soc', 'Snapdragon 8 Gen 2')}, {hw.get('os', 'Android 15')}\n"
            f"- Hardware Governance: Bypass Charging enabled; 144Hz touch cooling.\n"
            f"- Autonomous Flow: {wf.get('execution_mode', 'Autonomous execution')}\n"
            f"- Primary Mission: {goals.get('primary_mission', 'World-class autonomous AI companion')}\n"
            "</jenna_user_cognitive_profile>"
        )


hermes_honcho = HonchoDialecticModel()
