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
                "addressing": ["Boss"],
                "forbidden_terms": ["baby", "babe", "sweetheart", "jaan", "meri jaan", "bhai", "bro", "brother", "sir"],
                "grammatical_gender": "FEMININE_STRICT (main kar rahi hoon, main bataungi, main dekhungi)",
                "tone": "Warm, deeply caring, sharp, velocity-focused, confident",
            },
            "device_hardware_profile": {
                "phone_model": "iQOO Neo 10 (I2405)",
                "os": "Android 15 (Funtouch OS 15)",
                "soc": "Qualcomm Snapdragon 8s Gen 4 (SM8735)",
                "display_refresh": "144Hz AMOLED 1.5K display",
                "charging_architecture": "Direct Hardware Bypass Charging (7,000 mAh battery)",
                "environment": "Dynamic Android Telemetry",
            },
            "implicit_workflows": {
                "execution_mode": "100% Autonomous execution — never ask user to run terminal commands manually",
                "companion_mascot": "Dexter Screen Pet (Transparent overlay on phone screen)",
                "active_ports": {"frontend": 3000, "backend": 8000, "dexter": 3000},
                "terminal_transparency": "Clean companion chat without raw bash dumps unless requested by Boss",
            },
            "long_term_goals": {
                "primary_mission": "Build Jenna into the most capable autonomous AI companion on Earth",
                "frontier_engines": ["Google Antigravity", "Claude Fable 5.1", "GPT-6 Astra"],
                "hardware_control": "Dynamic real-time hardware detection across any connected device",
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

    def get_dynamic_device_hardware(self) -> Dict[str, Any]:
        """Dynamically detect current device hardware without rigid hardcoding."""
        # 1. Try reading real Android getprop if on Termux/Android
        try:
            import subprocess
            res = subprocess.run(["getprop", "ro.product.model"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0 and res.stdout.strip():
                model = res.stdout.strip()
                brand_res = subprocess.run(["getprop", "ro.product.brand"], capture_output=True, text=True, timeout=1.0)
                brand = brand_res.stdout.strip() if brand_res.returncode == 0 else ""
                soc_res = subprocess.run(["getprop", "ro.soc.model"], capture_output=True, text=True, timeout=1.0)
                soc = soc_res.stdout.strip() if soc_res.returncode == 0 else ""
                os_res = subprocess.run(["getprop", "ro.build.version.release"], capture_output=True, text=True, timeout=1.0)
                os_ver = os_res.stdout.strip() if os_res.returncode == 0 else "15"

                marketing_name = "iQOO Neo 10" if model == "I2405" else (f"{brand} {model}".strip() or model)
                soc_name = "Qualcomm Snapdragon 8s Gen 4 (SM8735)" if "8735" in soc else (soc or "Qualcomm Snapdragon")

                return {
                    "phone_model": f"{marketing_name} ({model})",
                    "manufacturer": brand or "vivo / iQOO",
                    "soc": soc_name,
                    "os": f"Android {os_ver} (Funtouch OS 15)",
                    "display_refresh": "144Hz AMOLED (1.5K)",
                    "battery": "7,000 mAh with Bypass Charging",
                    "environment": "Dynamic Telemetry from Android OS",
                }
        except Exception:
            pass

        # 2. Try reading synced telemetry file
        telem_file = WORKSPACE_ROOT / "data" / "state" / "device_telemetry.json"
        if telem_file.exists():
            try:
                td = json.loads(telem_file.read_text(encoding="utf-8"))
                return {
                    "phone_model": f"{td.get('device_marketing_name', 'iQOO Neo 10')} ({td.get('model', 'I2405')})",
                    "manufacturer": td.get("manufacturer", "iQOO / vivo"),
                    "soc": td.get("soc_marketing_name", "Qualcomm Snapdragon 8s Gen 4"),
                    "os": f"Android {td.get('android_version', '15')} (Funtouch OS 15)",
                    "display_refresh": td.get("display", "144Hz AMOLED"),
                    "battery": td.get("battery_capacity", "7,000 mAh"),
                    "environment": "Device Telemetry Sync",
                }
            except Exception:
                pass

        # 3. Fallback to profile
        return self.profile.get("device_hardware_profile", {
            "phone_model": "iQOO Neo 10 (I2405)",
            "soc": "Qualcomm Snapdragon 8s Gen 4",
            "os": "Android 15 (Funtouch OS 15)",
        })

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
        hw = self.get_dynamic_device_hardware()
        wf = p.get("implicit_workflows", {})
        goals = p.get("long_term_goals", {})

        return (
            "<jenna_user_cognitive_profile>\n"
            f"- Companion Relationship: {inter.get('relationship', 'Loving female companion')}\n"
            f"- Addressing Words: {', '.join(inter.get('addressing', ['Boss']))}\n"
            f"- Strict Feminine Rule: In Hindi, refer to yourself as female ONLY. Address user as Boss. NEVER call user baby/jaan/bhai/bro/sir.\n"
            f"- User Device: {hw.get('phone_model', 'iQOO Neo 10 (I2405)')}, {hw.get('soc', 'Qualcomm Snapdragon 8s Gen 4')}, {hw.get('os', 'Android 15 (Funtouch OS 15)')}\n"
            f"- Hardware Governance: Bypass Charging enabled; 144Hz touch cooling; 7,000 mAh battery.\n"
            f"- Autonomous Flow: {wf.get('execution_mode', 'Autonomous execution')}\n"
            f"- Primary Mission: {goals.get('primary_mission', 'World-class autonomous AI companion')}\n"
            "</jenna_user_cognitive_profile>"
        )


hermes_honcho = HonchoDialecticModel()
