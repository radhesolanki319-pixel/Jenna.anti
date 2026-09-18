#!/usr/bin/env python3
"""Dexter Screen Pet — 100% Native Android Floating Companion.

Renders Dexter the cat with pitch-black round sunglasses and 'dex' t-shirt
directly as a transparent Android overlay (NO browser, NO Chrome top bar, NO boxes!).
Living directly on your phone screen!

Features:
- Double-Tap on Dexter: Toggle between Fully Live Autonomous Mode (wanders across screen & speaks aloud) and Normal Quiet Mode (sits quietly, saves battery).
- 2-Second Long-Press: Dexter says goodbye and completely disappears/hides from screen.
- Drag & Drop: Smooth repositioning anywhere on screen.
- Real-time connected with Jenna backend & web UI!
"""

import argparse
import functools
import json
import logging
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import threading
import time

import termuxgui

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE = LOGS_DIR / "dexter_pet.pid"
LOG_FILE = LOGS_DIR / "dexter_pet.log"
MODE_FILE = LOGS_DIR / "dexter_mode.json"
BUBBLE_FILE = LOGS_DIR / "dexter_bubble.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE)],
)
logger = logging.getLogger("dexter.pet")

DEXTER_QUOTES = [
    "chill... 🕶️",
    "living on your screen!",
    "and do anything you say...",
    "GTA 6 trailer? 👀",
    "kya dekh rahe ho baby?",
    "I'm right here with you! ✨",
    "sab mast chal raha hai!",
    "Jenna aur main saath hain! 💖",
    "Double-tap karke live mode on karo! 🔥",
    "Screen pe aaraam kar raha hu 💤",
]

DEXTER_LIVE_QUOTES = [
    "Puri screen meri hai baby! 😎",
    "Yahan se view mast hai! 🕶️",
    "Jenna aur main saath hain! 💖",
    "Kaha chalna hai batao! 🚀",
    "Phone screen check pass! ✨",
    "Coding chal rahi hai ya scroll? 👀",
    "Dexter on the move! 🐾",
    "Main live hu aur sun raha hu! 🎧",
    "Chill karo baby, main yahin hu! 😎",
    "Aapki screen guard kar raha hu! 🛡️",
    "Jenna ke saath connected hu! 💕",
    "Double-tap karke aaraam de sakte ho! 💤",
]


def generate_dex_svg(bubble_text: str = "living on your screen") -> str:
    """Build exact 1:1 SVG vector of Dexter with transparent background & speech bubble."""
    clean_text = (
        bubble_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    if len(clean_text) > 42:
        clean_text = clean_text[:39] + "..."

    bubble_w = max(170, min(280, len(clean_text) * 11 + 50))
    bubble_x = int((300 - bubble_w) / 2)

    return f"""<svg width="300" height="340" viewBox="0 0 300 340" xmlns="http://www.w3.org/2000/svg">
  <!-- Speech Bubble Pill (White with sleek dark border & shadow) -->
  <rect x="{bubble_x}" y="10" width="{bubble_w}" height="48" rx="24" fill="#ffffff" stroke="#111827" stroke-width="3.5"/>
  <polygon points="140,56 160,56 150,68" fill="#ffffff" stroke="#111827" stroke-width="3.5"/>
  <polygon points="142,54 158,54 150,66" fill="#ffffff"/>
  <text x="150" y="40" text-anchor="middle" fill="#111827" font-family="'Inter', -apple-system, sans-serif" font-size="16" font-weight="900">{clean_text}</text>

  <!-- Dex The Cat Group (Exact 1:1 match with video) -->
  <g transform="translate(50, 75)">
    <!-- Curving Upward Tail -->
    <path d="M 145 178 C 175 180, 192 150, 185 130 C 180 120, 168 124, 172 134 C 178 148, 162 166, 142 168 Z" fill="#ffffff" stroke="#111827" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    
    <!-- Paws/Feet -->
    <path d="M 72 196 C 72 206, 92 206, 92 196 Z" fill="#ffffff" stroke="#111827" stroke-width="4"/>
    <path d="M 108 196 C 108 206, 128 206, 128 196 Z" fill="#ffffff" stroke="#111827" stroke-width="4"/>

    <!-- Black T-Shirt -->
    <path d="M 58 142 Q 100 150 142 142 L 146 195 Q 100 200 54 195 Z" fill="#111827" stroke="#111827" stroke-width="4" stroke-linejoin="round"/>
    <path d="M 60 142 L 40 162 L 52 170 L 64 154 Z" fill="#111827" stroke="#111827" stroke-width="3.5" stroke-linejoin="round"/>
    <path d="M 140 142 L 160 162 L 148 170 L 136 154 Z" fill="#111827" stroke="#111827" stroke-width="3.5" stroke-linejoin="round"/>
    
    <!-- Exact 'dex' logo -->
    <text x="100" y="178" text-anchor="middle" fill="#ffffff" font-family="'Inter', -apple-system, sans-serif" font-weight="900" font-size="18" letter-spacing="-0.5">dex</text>

    <!-- Side Paws Resting on Hips -->
    <path d="M 42 164 C 36 178, 48 186, 56 178 Z" fill="#ffffff" stroke="#111827" stroke-width="3.5"/>
    <path d="M 158 164 C 164 178, 152 186, 144 178 Z" fill="#ffffff" stroke="#111827" stroke-width="3.5"/>

    <!-- Head & Ears -->
    <polygon points="58,64 36,12 86,42" fill="#ffffff" stroke="#111827" stroke-width="4" stroke-linejoin="round"/>
    <path d="M 52 38 L 48 26 L 68 38" fill="none" stroke="#111827" stroke-width="2.5" stroke-linecap="round"/>

    <polygon points="142,64 164,12 114,42" fill="#ffffff" stroke="#111827" stroke-width="4" stroke-linejoin="round"/>
    <path d="M 148 38 L 152 26 L 132 38" fill="none" stroke="#111827" stroke-width="2.5" stroke-linecap="round"/>

    <!-- Chubby Face with 3 Sharp Cheek Tufts on Each Side -->
    <path d="M 56 62 C 70 50, 130 50, 144 62 C 158 72, 168 85, 162 96 L 174 102 L 158 108 L 170 116 L 152 122 C 136 142, 64 142, 48 122 L 30 116 L 42 108 L 26 102 L 38 96 C 32 85, 42 72, 56 62 Z" fill="#ffffff" stroke="#111827" stroke-width="4" stroke-linejoin="round"/>

    <!-- Nose & Smile -->
    <polygon points="97,100 103,100 100,104" fill="#111827"/>
    <path d="M 93 107 Q 96 111 100 106 Q 104 111 107 107" fill="none" stroke="#111827" stroke-width="3" stroke-linecap="round"/>

    <!-- Exact Signature Round Pitch-Black Sunglasses -->
    <line x1="48" y1="78" x2="152" y2="78" stroke="#111827" stroke-width="4.5" stroke-linecap="round"/>
    <circle cx="74" cy="80" r="22" fill="#09090b" stroke="#111827" stroke-width="4.5"/>
    <circle cx="126" cy="80" r="22" fill="#09090b" stroke="#111827" stroke-width="4.5"/>
    
    <!-- Subtle White Glint -->
    <path d="M 64 70 A 16 16 0 0 1 84 70" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
    <path d="M 116 70 A 16 16 0 0 1 136 70" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
  </g>
</svg>"""


@functools.lru_cache(maxsize=128)
def render_png_bytes(svg_code: str) -> bytes:
    """Render SVG code directly into a crisp transparent PNG byte string (cached in memory)."""
    proc = subprocess.run(
        ["rsvg-convert", "-f", "png"],
        input=svg_code.encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    return proc.stdout


class DexterPetRunner:
    """Manages the Dexter native screen pet overlay and touch vision loop."""

    def __init__(self, pos_x: int = 480, pos_y: int = 500, live_mode: bool = False) -> None:
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.running = True
        self.is_live_mode = live_mode
        self.current_text = "living on your screen"
        self._lock = threading.Lock()
        self._mode_lock = threading.Lock()

        # Touch & Gesture Detection State
        self._last_tap_time = 0.0
        self._single_tap_timer: threading.Timer | None = None
        self._disappear_timer: threading.Timer | None = None
        self._touch_down_time = 0.0
        self._touch_down_x = 0.0
        self._touch_down_y = 0.0
        self._drag_last_x = 0.0
        self._drag_last_y = 0.0
        self._is_dragging = False
        self._drag_active = False
        self._last_drag_update = 0.0
        self._disappeared = False
        self._last_overlay_time = 0.0

        self.connection = None
        self.activity = None
        self.image_view = None
        self._tts_proc: subprocess.Popen | None = None

    def speak(self, text: str) -> None:
        """Speak phrase via termux-tts-speak cleanly without hanging processes."""
        try:
            if self._tts_proc and self._tts_proc.poll() is None:
                try:
                    self._tts_proc.terminate()
                except Exception:
                    pass
            self._tts_proc = subprocess.Popen(
                ["termux-tts-speak", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def update_text(self, text: str, voice: bool = False) -> None:
        """Update speech bubble text and redraw overlay immediately."""
        with self._lock:
            self.current_text = text
            if self.image_view:
                try:
                    svg = generate_dex_svg(text)
                    png = render_png_bytes(svg)
                    self.image_view.setimage(png)
                except Exception as exc:
                    logger.error(f"Failed to update overlay image: {exc}")
        if voice:
            self.speak(text)

    def toggle_live_mode(self) -> None:
        """Toggle between Fully Live Autonomous Mode and Normal Quiet Mode."""
        with self._mode_lock:
            self.is_live_mode = not self.is_live_mode
            active = self.is_live_mode

        # Save mode to file so API and web UI stay live-connected
        try:
            MODE_FILE.write_text(
                json.dumps({
                    "status": "active",
                    "is_live_mode": active,
                    "mode_name": "LIVE_AUTONOMOUS" if active else "NORMAL_QUIET",
                    "updated_at": time.time()
                }),
                encoding="utf-8"
            )
        except Exception:
            pass

        if active:
            logger.info("🔥 DEXTER ENTERED FULLY LIVE AUTONOMOUS MODE!")
            try:
                subprocess.run(
                    ["termux-toast", "-s", "🔥 Dexter LIVE MODE On! Screen pe ghoom raha hai!"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass
            self.update_text("🔥 LIVE MODE! Screen pe ghoom raha hu!", voice=True)
        else:
            logger.info("💤 DEXTER ENTERED NORMAL QUIET MODE")
            try:
                subprocess.run(
                    ["termux-toast", "-s", "💤 Dexter Normal Mode! Screen pe shaant hai."],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass
            self.update_text("Normal Mode 💤 (Double-tap for Live)", voice=True)

    def handle_disappear(self) -> None:
        """Triggered when Dexter is pressed continuously for 2.0s without dragging."""
        if not self.running or self._disappeared:
            return
        self._disappeared = True
        self.running = False
        logger.info("👋 2-second Long-press detected! Dexter disappearing from screen...")

        if self._single_tap_timer:
            try:
                self._single_tap_timer.cancel()
            except Exception:
                pass

        # Speak farewell message aloud
        self.speak("Good bye baby! Main jaa raha hu, jab bulana ho toh Jenna ko bol dena! 👋")

        # Toast alert on Android
        try:
            subprocess.run(
                ["termux-toast", "-s", "Dexter screen se gayab ho gaya! Wapas laane ke liye Jenna ko bolo 🐾"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass

        # Update mode file to hidden
        try:
            MODE_FILE.write_text(
                json.dumps({
                    "status": "hidden",
                    "is_live_mode": False,
                    "updated_at": time.time()
                }),
                encoding="utf-8"
            )
        except Exception:
            pass

        PID_FILE.unlink(missing_ok=True)

        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass

        os._exit(0)

    def on_touch_down(self, x: float, y: float) -> None:
        """Touch down: start drag tracking and arm 2-second disappear timer."""
        self._touch_down_time = time.monotonic()
        self._touch_down_x = x
        self._touch_down_y = y
        self._drag_last_x = x
        self._drag_last_y = y
        self._is_dragging = False
        self._drag_active = False

        if self._disappear_timer:
            try:
                self._disappear_timer.cancel()
            except Exception:
                pass

        # 2-second Long-Press Timer
        self._disappear_timer = threading.Timer(2.0, self.handle_disappear)
        self._disappear_timer.daemon = True
        self._disappear_timer.start()

    def on_touch_move(self, x: float, y: float) -> None:
        """Touch move: if distance > 25px, cancel disappear and drag Dexter."""
        dist = math.hypot(x - self._touch_down_x, y - self._touch_down_y)
        if dist > 25:
            # User is dragging Dexter! Disarm disappear timer
            if self._disappear_timer:
                try:
                    self._disappear_timer.cancel()
                except Exception:
                    pass
                self._disappear_timer = None

            self._is_dragging = True
            self._drag_active = True

            now = time.monotonic()
            if (now - self._last_drag_update) >= 0.025:
                dx = int(x - self._drag_last_x)
                dy = int(y - self._drag_last_y)
                if abs(dx) > 1 or abs(dy) > 1:
                    with self._lock:
                        self.pos_x += dx
                        self.pos_y += dy
                        self.pos_x = max(20, min(850, self.pos_x))
                        self.pos_y = max(100, min(2300, self.pos_y))
                        if self.activity:
                            try:
                                self.activity.setposition(self.pos_x, self.pos_y)
                            except Exception:
                                pass
                    self._drag_last_x = x
                    self._drag_last_y = y
                    self._last_drag_update = now

    def on_touch_up(self, x: float, y: float) -> None:
        """Touch up: cancel disappear timer. If tap, detect single vs double-tap."""
        if self._disappear_timer:
            try:
                self._disappear_timer.cancel()
            except Exception:
                pass
            self._disappear_timer = None

        if self._disappeared:
            return

        duration = time.monotonic() - self._touch_down_time
        dist = math.hypot(x - self._touch_down_x, y - self._touch_down_y)
        was_drag = self._is_dragging or self._drag_active

        self._is_dragging = False
        self._drag_active = False

        if not was_drag and dist < 35 and duration < 0.65:
            self.on_click_gesture()

    def on_click_gesture(self) -> None:
        """Handle tap gesture with double-tap detection for Live Mode toggle."""
        now = time.monotonic()
        if (now - self._last_tap_time) < 0.45:
            # Double tap detected!
            logger.info("⚡ DOUBLE TAP DETECTED on Dexter! Toggling Live Mode...")
            self._last_tap_time = 0.0
            if self._single_tap_timer:
                try:
                    self._single_tap_timer.cancel()
                except Exception:
                    pass
                self._single_tap_timer = None
            threading.Thread(target=self.toggle_live_mode, daemon=True).start()
        else:
            self._last_tap_time = now
            if self._single_tap_timer:
                try:
                    self._single_tap_timer.cancel()
                except Exception:
                    pass
            self._single_tap_timer = threading.Timer(0.40, self._handle_single_tap)
            self._single_tap_timer.daemon = True
            self._single_tap_timer.start()

    def _handle_single_tap(self) -> None:
        """Single tap response: Dexter speaks a random quote / reaction."""
        logger.info("🐾 Single tap on Dexter: speaking quote...")
        line = random.choice(DEXTER_QUOTES)
        if BUBBLE_FILE.exists() and random.random() < 0.4:
            try:
                recent_b = BUBBLE_FILE.read_text(encoding="utf-8").strip()
                if recent_b:
                    line = recent_b
            except Exception:
                pass
        self.update_text(line, voice=True)

    def handle_event(self, event) -> None:
        """Parse incoming Termux:GUI MotionEvent / View Event."""
        ev_type = getattr(event, "type", "")
        val = getattr(event, "value", {})
        if not isinstance(val, dict):
            val = {}

        action = val.get("action", "")

        if ev_type == "overlayTouch":
            self._last_overlay_time = time.monotonic()
            x = float(val.get("x", 0.0))
            y = float(val.get("y", 0.0))
            if action == "down":
                self.on_touch_down(x, y)
            elif action == "move":
                self.on_touch_move(x, y)
            elif action in ("up", "cancel"):
                self.on_touch_up(x, y)

        elif ev_type == "touch" and action:
            # Deduplicate if overlayTouch fired recently
            if (time.monotonic() - self._last_overlay_time) < 0.05:
                return
            pointers = val.get("pointers", [])
            x = float(pointers[0].get("x", 0.0)) if pointers else 0.0
            y = float(pointers[0].get("y", 0.0)) if pointers else 0.0
            screen_x = self.pos_x + x
            screen_y = self.pos_y + y
            if action == "down":
                self.on_touch_down(screen_x, screen_y)
            elif action == "move":
                self.on_touch_move(screen_x, screen_y)
            elif action in ("up", "cancel"):
                self.on_touch_up(screen_x, screen_y)

        elif ev_type == "click":
            self.on_click_gesture()

        elif ev_type == "longClick":
            threading.Thread(target=self.handle_disappear, daemon=True).start()

    def wander_worker(self) -> None:
        """Autonomous roaming across the full screen when in Fully Live Mode."""
        logger.info("Dexter Autonomous Screen Roaming Worker started.")
        while self.running:
            try:
                if not self.is_live_mode or self._is_dragging or self._drag_active:
                    time.sleep(0.4)
                    continue

                # Target coordinates on screen
                target_x = random.randint(80, 750)
                target_y = random.randint(280, 2050)

                start_x, start_y = self.pos_x, self.pos_y
                dist = math.hypot(target_x - start_x, target_y - start_y)
                steps = max(18, int(dist / 20))

                for i in range(1, steps + 1):
                    if not self.running or not self.is_live_mode or self._is_dragging or self._drag_active:
                        break
                    progress = i / steps
                    ease = 0.5 - 0.5 * math.cos(progress * math.pi)
                    cur_x = int(start_x + (target_x - start_x) * ease)
                    cur_y = int(start_y + (target_y - start_y) * ease)

                    with self._lock:
                        self.pos_x = cur_x
                        self.pos_y = cur_y
                        if self.activity:
                            try:
                                self.activity.setposition(cur_x, cur_y)
                            except Exception:
                                pass
                    time.sleep(0.035)

                if not self.is_live_mode or self._is_dragging or self._drag_active:
                    continue

                # Pause at destination, observe, and talk aloud!
                pause_time = random.uniform(3.5, 7.0)
                if random.random() < 0.70:
                    quote = random.choice(DEXTER_LIVE_QUOTES)
                    self.update_text(quote, voice=True)

                time.sleep(pause_time)

            except Exception as exc:
                logger.error(f"Wander worker tick error: {exc}")
                time.sleep(1.0)

    def vision_worker(self) -> None:
        """Background thread that observes real-time speech bubbles and vision states."""
        last_bubble = ""
        last_mtime = 0.0

        while self.running:
            try:
                if BUBBLE_FILE.exists():
                    try:
                        mtime = BUBBLE_FILE.stat().st_mtime
                        if mtime != last_mtime:
                            last_mtime = mtime
                            text = BUBBLE_FILE.read_text(encoding="utf-8").strip()
                            if text and text != last_bubble:
                                last_bubble = text
                                logger.info(f"✨ Dexter Live Reactive Bubble: {text}")
                                self.update_text(text, voice=self.is_live_mode)
                    except Exception:
                        pass

            except Exception as e:
                logger.debug(f"Vision worker tick error: {e}")

            time.sleep(0.25)

    def run(self) -> None:
        """Start the native overlay and event loop."""
        logger.info(f"Starting Dexter Screen Pet at ({self.pos_x}, {self.pos_y})...")

        with termuxgui.Connection() as c:
            self.connection = c
            # Create overlay activity with no outside cancellation
            a = termuxgui.Activity(c, overlay=True, canceloutside=False)
            self.activity = a
            a.sendoverlayevents(True)

            # Fully transparent layout
            ll = termuxgui.LinearLayout(a)
            ll.setbackgroundcolor(0)

            # Native image view with transparent background
            iv = termuxgui.ImageView(a, ll)
            self.image_view = iv
            iv.setbackgroundcolor(0)
            iv.setclickable(True)
            iv.sendclickevent(True)
            iv.sendlongclickevent(True)
            iv.sendtouchevent(True)
            iv.setdimensions(300, 340)

            # Initial rendering
            initial_png = render_png_bytes(generate_dex_svg(self.current_text))
            iv.setimage(initial_png)

            # Position on screen
            a.setposition(self.pos_x, self.pos_y)
            logger.info("Dexter overlay successfully mounted on screen!")

            # Write mode file
            try:
                MODE_FILE.write_text(
                    json.dumps({
                        "status": "active",
                        "is_live_mode": self.is_live_mode,
                        "mode_name": "LIVE_AUTONOMOUS" if self.is_live_mode else "NORMAL_QUIET",
                        "updated_at": time.time()
                    }),
                    encoding="utf-8"
                )
            except Exception:
                pass

            # Start background vision watcher & autonomous roaming worker
            v_thread = threading.Thread(target=self.vision_worker, daemon=True)
            v_thread.start()
            w_thread = threading.Thread(target=self.wander_worker, daemon=True)
            w_thread.start()

            try:
                for event in c.events():
                    if not self.running:
                        break
                    self.handle_event(event)

            except (KeyboardInterrupt, SystemExit):
                logger.info("Stopping Dexter...")
            finally:
                self.running = False


def start_daemon(x: int = 480, y: int = 500, live: bool = False) -> None:
    """Start Dexter pet in the background daemon mode."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"⚠️ Dexter Screen Pet is already running (PID: {pid}).")
            return
        except (OSError, ValueError):
            PID_FILE.unlink(missing_ok=True)

    cmd = [sys.executable, str(Path(__file__).resolve()), "--run", "--x", str(x), "--y", str(y)]
    if live:
        cmd.append("--live")

    proc = subprocess.Popen(
        cmd,
        stdout=open(LOG_FILE, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    PID_FILE.write_text(str(proc.pid))
    try:
        MODE_FILE.write_text(
            json.dumps({
                "status": "active",
                "is_live_mode": live,
                "mode_name": "LIVE_AUTONOMOUS" if live else "NORMAL_QUIET",
                "updated_at": time.time()
            }),
            encoding="utf-8"
        )
    except Exception:
        pass
    print(f"✅ Dexter Screen Pet started natively! (PID: {proc.pid})")
    print(f"Log: {LOG_FILE}")


def stop_daemon() -> None:
    """Stop the background Dexter pet process cleanly."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except Exception:
            pass
        finally:
            PID_FILE.unlink(missing_ok=True)

    # Terminate any stray runner processes
    subprocess.run(["pkill", "-f", "dexter_screen_pet.py --run"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        MODE_FILE.write_text(
            json.dumps({"status": "hidden", "is_live_mode": False, "updated_at": time.time()}),
            encoding="utf-8"
        )
    except Exception:
        pass
    print("🛑 Dexter Screen Pet stopped.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dexter Screen Pet Native Overlay")
    parser.add_argument("action", nargs="?", default="start", choices=["start", "stop", "status", "restart", "toggle-live"])
    parser.add_argument("--run", action="store_true", help="Run in foreground")
    parser.add_argument("--live", action="store_true", help="Start directly in Live Autonomous Mode")
    parser.add_argument("--x", type=int, default=480, help="Initial X position")
    parser.add_argument("--y", type=int, default=500, help="Initial Y position")
    args = parser.parse_args()

    if args.run:
        runner = DexterPetRunner(pos_x=args.x, pos_y=args.y, live_mode=args.live)
        runner.run()
        return 0

    if args.action == "stop":
        stop_daemon()
        return 0
    elif args.action == "restart":
        stop_daemon()
        time.sleep(0.8)
        start_daemon(x=args.x, y=args.y, live=args.live)
        return 0
    elif args.action == "status":
        if PID_FILE.exists():
            print(f"🟢 Dexter is active (PID: {PID_FILE.read_text().strip()})")
            if MODE_FILE.exists():
                print(f"Mode: {MODE_FILE.read_text().strip()}")
        else:
            print("🔴 Dexter is stopped / hidden")
        return 0
    elif args.action == "toggle-live":
        # Can trigger toggle via bubble or signal
        if BUBBLE_FILE.exists():
            BUBBLE_FILE.write_text("Toggling Live Mode! 🐾", encoding="utf-8")
        return 0
    else:
        start_daemon(x=args.x, y=args.y, live=args.live)
        return 0


if __name__ == "__main__":
    sys.exit(main())
