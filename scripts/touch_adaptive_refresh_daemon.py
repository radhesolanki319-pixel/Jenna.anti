"""Jenna Dynamic Touch-Adaptive 144Hz / 60Hz Refresh Rate Daemon.

iQOO Neo 10 (Snapdragon 8 Gen 4 / SM8750 "sun" / Android 15)
- Touch Down (finger on screen): Instantly locks display to 144.0 Hz.
- Finger Lifted (screen idle): Immediately drops display to 60.0 Hz after kinetic debounce.
Result: 100% silky 144Hz flagship feel during touch, 60Hz power saving when idle.
"""

import asyncio
import logging
import os
from pathlib import Path
import re
import sys
import time

WORKSPACE = Path("/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna")
LOG_FILE = WORKSPACE / "logs" / "touch_refresh.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("jenna.touch_refresh")

DEBOUNCE_DELAY = 0.4  # Seconds after finger lift before dropping to 60Hz (allows kinetic fling)


class TouchAdaptiveRefreshGovernor:
    """Dynamically scales refresh rate between 144Hz (touch) and 60Hz (idle)."""

    def __init__(self) -> None:
        self.current_rate = 60.0
        self.last_touch_time = 0.0
        self.is_finger_down = False
        self.serial = "emulator-5554"
        self.ts_device = "/dev/input/event5"

    async def detect_device(self):
        """Find connected ADB device and touchscreen event node."""
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
                self.serial = parts[0]
                break

        # Check getevent devices
        p2 = await asyncio.create_subprocess_exec(
            "adb", "-s", self.serial, "shell", "getevent -S",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out2, _ = await p2.communicate()
        text = out2.decode("utf-8", errors="ignore")
        
        # Match device node for vivo_ts or touchscreen
        dev_match = re.search(r"add device \d+: (/dev/input/event\d+)\s+name:\s+\"(vivo_ts|touchscreen|fts_ts)\"", text, re.I)
        if dev_match:
            self.ts_device = dev_match.group(1)
        
        logger.info(f"Connected to {self.serial} | Touchscreen: {self.ts_device}")

    async def apply_rate(self, target_rate: float):
        """Apply refresh rate via ADB settings."""
        if self.current_rate == target_rate:
            return

        self.current_rate = target_rate
        rate_str = f"{target_rate:.1f}"
        
        # When 144Hz, lock min & peak to 144.0
        # When 60Hz, drop min & peak to 60.0
        cmd = f"settings put system min_refresh_rate {rate_str} ; settings put system peak_refresh_rate {rate_str} ; settings put system user_refresh_rate {rate_str}"
        await asyncio.create_subprocess_exec(
            "adb", "-s", self.serial, "shell", cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        logger.info(f"⚡ Display Refresh Rate changed -> {rate_str} Hz")

    async def idle_checker(self):
        """Monitors when touch stops and smoothly drops to 60Hz."""
        while True:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            if not self.is_finger_down and self.current_rate > 60.0:
                if (now - self.last_touch_time) >= DEBOUNCE_DELAY:
                    await self.apply_rate(60.0)

    async def run(self):
        await self.detect_device()
        # Start at 60Hz idle
        await self.apply_rate(60.0)
        asyncio.create_task(self.idle_checker())

        logger.info(f"Listening to touchscreen events on {self.ts_device}...")

        while True:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", self.serial, "shell", f"getevent -l {self.ts_device}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break

                    decoded = line.decode("utf-8", errors="ignore").strip()
                    
                    # Touch DOWN detection
                    if "BTN_TOUCH            DOWN" in decoded or ("ABS_MT_TRACKING_ID" in decoded and "ffffffff" not in decoded):
                        self.is_finger_down = True
                        self.last_touch_time = time.monotonic()
                        if self.current_rate < 144.0:
                            await self.apply_rate(144.0)

                    # Touch UP detection
                    elif "BTN_TOUCH            UP" in decoded or "ABS_MT_TRACKING_ID   ffffffff" in decoded:
                        self.is_finger_down = False
                        self.last_touch_time = time.monotonic()

                    # Finger moving on screen
                    elif self.is_finger_down:
                        self.last_touch_time = time.monotonic()

            except Exception as e:
                logger.warning(f"Event stream error: {e}")
            finally:
                try:
                    proc.kill()
                except Exception:
                    pass
                await asyncio.sleep(1.0)


if __name__ == "__main__":
    governor = TouchAdaptiveRefreshGovernor()
    asyncio.run(governor.run())
