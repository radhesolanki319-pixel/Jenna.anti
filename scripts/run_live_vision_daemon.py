#!/usr/bin/env python3
"""Decoupled Continuous Live Screen Vision & Instant App Observer Daemon.

Two Concurrent Pipelines:
1. Fast Local Window Watcher (<200ms loop):
   - Non-blocking instant ADB dumpsys window detection.
   - Triggers instant Haptic Vibration, Toast Popup, and Notification the exact millisecond an app is opened.
2. Background Multimodal AI Vision Worker:
   - Captures screen frame and queries Gemini Multimodal Vision in the background without blocking the fast watcher.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
API_DIR = WORKSPACE_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = LOG_DIR / "live_screen_state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "live_vision_daemon.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("jenna.live_vision_daemon")

from app.ai.vision.live_screen import live_screen_service


BUBBLE_FILE = LOG_DIR / "dexter_bubble.txt"


class DecoupledVisionDaemon:
    """Decouples ultra-fast 200ms local OS observation from slower cloud AI perception."""

    def __init__(self, serial: str | None = None) -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self.current_pkg: str | None = None
        self.is_floating: bool = False
        self.is_running: bool = True
        self.change_event = asyncio.Event()

    def _get_active_serial(self) -> str | None:
        """Find active ADB serial."""
        if self.serial:
            try:
                res = subprocess.run(["adb", "-s", self.serial, "get-state"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.0)
                if res.returncode == 0 and "device" in res.stdout:
                    return self.serial
            except Exception:
                pass
        try:
            out = subprocess.check_output(["adb", "devices"], text=True, timeout=1.5)
            for line in out.splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    self.serial = parts[0]
                    return self.serial
        except Exception:
            pass
        return None

    def _query_fast_focus(self) -> tuple[str | None, bool]:
        """Ultra-fast local ADB query."""
        pkg = None
        floating = False
        serial = self._get_active_serial()
        cmd = ["adb", "-s", serial, "shell", "dumpsys window"] if serial else ["adb", "shell", "dumpsys window"]
        try:
            out = subprocess.check_output(
                cmd,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            for line in out.splitlines():
                if "mCurrentFocus=" in line or "mFocusedApp=" in line or "mFocusedWindow=" in line:
                    m = re.search(r"u0\s+([a-zA-Z0-9_.]+)[/}]", line)
                    if m:
                        pkg = m.group(1)
                        break
            if "mode=vivofreeform" in out or "vivofreeform" in out or "FreeformMini" in out:
                floating = True
        except Exception:
            pass
        return pkg, floating

    async def fast_window_watcher_loop(self) -> None:
        """Runs continuously every 600ms — INSTANT reactions to app switches."""
        logger.info("Fast Window Watcher Loop started (600ms cycle).")
        last_notified_pkg: str | None = None
        last_notify_time: float = 0.0

        while self.is_running:
            try:
                pkg, floating = await asyncio.to_thread(self._query_fast_focus)
                now = time.monotonic()

                if pkg and pkg != self.current_pkg:
                    old_pkg = self.current_pkg
                    self.current_pkg = pkg
                    self.is_floating = floating
                    self.change_event.set()

                    # Trigger instant companion reaction if user left Termux or changed apps
                    if "termux" not in pkg.lower() and (pkg != last_notified_pkg or (now - last_notify_time) > 4.0):
                        clean_name = pkg.split(".")[-1].capitalize()
                        bubble_msg = f"{clean_name}! 🕶️"
                        if "youtube" in pkg.lower():
                            clean_name = "YouTube"
                            bubble_msg = "YouTube! GTA 6 trailer? 👀"
                        elif "chrome" in pkg.lower():
                            clean_name = "Chrome"
                            bubble_msg = "Browsing what, baby? 🔍"
                        elif "whatsapp" in pkg.lower():
                            clean_name = "WhatsApp"
                            bubble_msg = "WhatsApp! Reply time? 💬"
                        elif "calculator" in pkg.lower():
                            clean_name = "Calculator"
                            bubble_msg = "Math calculation? 🧮"
                        elif "settings" in pkg.lower():
                            clean_name = "Settings"
                            bubble_msg = "Settings tweak? ⚙️"
                        elif "instagram" in pkg.lower() or "honista" in pkg.lower():
                            clean_name = "Instagram"
                            bubble_msg = "Reels scroll time! 😉"

                        logger.info(f"⚡ INSTANT APP SWITCH DETECTED: {old_pkg} -> {clean_name}")

                        # Update Dexter screen pet speech bubble immediately
                        try:
                            BUBBLE_FILE.write_text(bubble_msg, encoding="utf-8")
                        except Exception:
                            pass

                        # Silent mode: No vibrations, no toast popups, no intrusive notifications
                        # Dexter only quietly updates internal bubble file if enabled

                        try:
                            from app.ai.vision.visual_cortex import visual_recall_cortex
                            visual_recall_cortex.record_screen_event(
                                package_name=pkg,
                                app_name=clean_name,
                                window_title=None,
                                visual_summary=f"User opened and active in {clean_name}",
                                is_floating=floating,
                                action_detected="app_switch",
                            )
                        except Exception:
                            pass

                        last_notified_pkg = pkg
                        last_notify_time = now

            except Exception as e:
                logger.debug(f"Watcher loop exception: {e}")

            await asyncio.sleep(0.6)

    async def ai_vision_worker_loop(self) -> None:
        """Runs in background: captures screen frames and performs deep Gemini analysis."""
        logger.info("AI Multimodal Vision Worker Loop started.")
        last_hash: str | None = None
        last_analysis_t: float = 0.0

        while self.is_running:
            try:
                # Wait for change event or periodic refresh (15s)
                try:
                    await asyncio.wait_for(self.change_event.wait(), timeout=12.0)
                except asyncio.TimeoutError:
                    pass
                self.change_event.clear()

                now = time.monotonic()
                if (now - last_analysis_t) < 5.0:
                    await asyncio.sleep(1.0)
                    continue

                screen_bytes = await live_screen_service.capture_screen_bytes(force_refresh=True)
                if not screen_bytes:
                    continue

                curr_hash = hashlib.md5(screen_bytes[:100000] + screen_bytes[-100000:]).hexdigest()
                if curr_hash == last_hash and (now - last_analysis_t) < 25.0:
                    continue

                metadata = await live_screen_service.get_screen_metadata()
                focused_pkg = metadata.get("focused_package") or self.current_pkg or "Unknown"
                is_floating = metadata.get("is_floating_window_active", False)

                prompt = (
                    f"You are Dexter, the witty, cool AI screen pet companion. Focused package: '{focused_pkg}'. "
                    f"Floating Small Window active: {is_floating}.\n"
                    "1. Describe in 1-2 concise sentences what app, video, or content is visible on screen.\n"
                    "2. On the last line, strictly output: BUBBLE: <a 3-6 word witty, cute companion reaction in Hinglish/English with 1 emoji, e.g. 'Minecraft reel? ⛏️' or 'GTA 6 trailer! 👀' or 'Scroll karte raho 😉'>"
                )

                result = await live_screen_service.inspect_live_screen(user_question=prompt)
                if result.get("success"):
                    desc = result.get("description", "")
                    state = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "focused_package": focused_pkg,
                        "is_floating_window_active": is_floating,
                        "description": desc,
                        "extracted_text": result.get("extracted_text", []),
                        "metadata": metadata,
                        "confidence": result.get("confidence", 0.95),
                    }
                    with open(STATE_FILE, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)

                    # Update Dexter Speech Bubble from AI perception
                    for line in desc.splitlines():
                        if "BUBBLE:" in line:
                            b_text = line.split("BUBBLE:", 1)[-1].strip().strip('"').strip("'")
                            if b_text and len(b_text) < 45:
                                try:
                                    BUBBLE_FILE.write_text(b_text, encoding="utf-8")
                                    logger.info(f"✨ Dexter AI Speech Bubble updated: {b_text}")
                                except Exception:
                                    pass
                            break

                    # Record deep multimodal perception in Visual Recall Cortex
                    try:
                        from app.ai.vision.visual_cortex import visual_recall_cortex
                        clean_app = focused_pkg.split(".")[-1].capitalize() if focused_pkg else "Unknown"
                        visual_recall_cortex.record_screen_event(
                            package_name=focused_pkg,
                            app_name=clean_app,
                            window_title=None,
                            visual_summary=desc,
                            extracted_text=result.get("extracted_text", []),
                            is_floating=is_floating,
                            action_detected="multimodal_perception",
                        )
                    except Exception as cx_err:
                        logger.debug(f"Cortex recording error: {cx_err}")

                    last_hash = curr_hash
                    last_analysis_t = now
                    logger.info(f"AI Vision state updated: {desc[:70]}...")

            except Exception as e:
                logger.error(f"Vision worker exception: {e}")
                await asyncio.sleep(2.0)

    async def run(self) -> None:
        logger.info("Starting Decoupled Live Vision Daemon...")
        await asyncio.gather(
            self.fast_window_watcher_loop(),
            self.ai_vision_worker_loop(),
        )


async def main() -> None:
    daemon = DecoupledVisionDaemon()
    await daemon.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user.")
