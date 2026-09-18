"""Jenna Android OS Auto-Pilot Engine.

Provides deep OS navigation, app control, and UI element interaction
using ADB and UIAutomator dumps on Android 15 (Vivo / iQOO Neo 9 Pro).
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("jenna.android_autopilot")

COMMON_APPS = {
    "youtube": "com.google.android.youtube",
    "spotify": "com.spotify.music",
    "chrome": "com.android.chrome",
    "whatsapp": "com.whatsapp",
    "settings": "com.android.settings",
    "camera": "com.android.camera",
    "clock": "com.google.android.deskclock",
    "calculator": "com.google.android.calculator",
    "files": "com.google.android.documentsui",
    "telegram": "org.telegram.messenger",
    "jenna": "ai.jenna.app",
    "playstore": "com.android.vending",
}


class AndroidAutopilot:
    """Autonomous OS navigation and UI manipulation."""

    def __init__(self) -> None:
        self._serial: Optional[str] = None

    async def get_serial(self) -> str:
        if self._serial:
            return self._serial
        proc = await asyncio.create_subprocess_exec(
            "adb", "devices",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().splitlines()
        for line in lines[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                self._serial = parts[0]
                return self._serial
        return "127.0.0.1:5555"

    async def run_adb(self, *args: str) -> Tuple[int, str, str]:
        serial = await self.get_serial()
        cmd = ["adb", "-s", serial] + list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def launch_app(self, target: str) -> Dict[str, Any]:
        """Launch an installed application by common name or package id."""
        target_lower = target.lower().strip()
        pkg = COMMON_APPS.get(target_lower, target.strip())

        code, out, err = await self.run_adb("shell", f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
        if code == 0:
            return {"success": True, "action": "launch_app", "package": pkg, "message": f"Successfully launched {target}"}
        
        # Fallback to direct am start
        code2, out2, err2 = await self.run_adb("shell", f"am start {pkg}")
        return {
            "success": code2 == 0,
            "action": "launch_app",
            "package": pkg,
            "stdout": out2 or out,
            "stderr": err2 or err,
        }

    async def dump_ui(self) -> Optional[str]:
        """Dump UIAutomator XML hierarchy from active screen."""
        await self.run_adb("shell", "uiautomator dump /data/local/tmp/uidump.xml")
        code, out, _ = await self.run_adb("shell", "cat /data/local/tmp/uidump.xml")
        return out if code == 0 and "<hierarchy" in out else None

    async def find_element_by_text(self, text: str) -> Optional[Tuple[int, int]]:
        """Scan active screen UI hierarchy for text match and return center (x, y)."""
        xml_content = await self.dump_ui()
        if not xml_content:
            return None

        try:
            root = ET.fromstring(xml_content)
            target = text.lower()
            for elem in root.iter("node"):
                elem_text = (elem.get("text") or "").lower()
                elem_desc = (elem.get("content-desc") or "").lower()
                if target in elem_text or target in elem_desc:
                    bounds = elem.get("bounds", "")
                    # bounds format: [x1,y1][x2,y2]
                    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
                        return ((x1 + x2) // 2, (y1 + y2) // 2)
        except Exception as e:
            logger.warning(f"Failed to parse UI XML: {e}")
        return None

    async def tap_text(self, text: str) -> Dict[str, Any]:
        """Find an element by text or content description and tap it."""
        coords = await self.find_element_by_text(text)
        if not coords:
            return {"success": False, "error": f"Element matching '{text}' not found on active screen"}
        
        x, y = coords
        code, _, _ = await self.run_adb("shell", f"input tap {x} {y}")
        return {"success": code == 0, "action": "tap_text", "text": text, "x": x, "y": y}

    async def input_text(self, text: str) -> Dict[str, Any]:
        """Type text into active focused input box."""
        escaped = re.sub(r'([ "&\'<>()|;])', r'\\\1', text)
        code, _, _ = await self.run_adb("shell", f"input text '{escaped}'")
        return {"success": code == 0, "action": "input_text", "text": text}

    async def press_key(self, key_name: str) -> Dict[str, Any]:
        """Press an Android hardware key (home, back, enter, volume_up, etc.)."""
        keymap = {
            "home": "KEYCODE_HOME",
            "back": "KEYCODE_BACK",
            "enter": "KEYCODE_ENTER",
            "menu": "KEYCODE_MENU",
            "app_switch": "KEYCODE_APP_SWITCH",
            "power": "KEYCODE_POWER",
            "volume_up": "KEYCODE_VOLUME_UP",
            "volume_down": "KEYCODE_VOLUME_DOWN",
        }
        key_code = keymap.get(key_name.lower(), key_name)
        code, _, _ = await self.run_adb("shell", f"input keyevent {key_code}")
        return {"success": code == 0, "action": "press_key", "key": key_code}


android_autopilot = AndroidAutopilot()
