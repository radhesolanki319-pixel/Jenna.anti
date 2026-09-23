#!/usr/bin/env python3
# =============================================================================
# Jenna AI — Proactive Intelligence Daemon v2
# Acts without being asked. Monitors device health & sends smart alerts.
# =============================================================================

import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import shutil

# ---------------------------------------------------------------------------
# Paths & Logging
# ---------------------------------------------------------------------------
BASE_DIR   = Path("/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna")
LOG_DIR    = BASE_DIR / "logs"
LOG_FILE   = LOG_DIR / "proactive_v2.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("jenna.proactive")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BRIDGE_BASE  = "http://localhost:8000"
NOTIF_URL    = f"{BRIDGE_BASE}/device/bridge/exec"
CHAT_URL     = f"{BRIDGE_BASE}/api/v1/antigravity/chat"

BATTERY_LOW_PCT   = 20      # %
BATTERY_TEMP_HIGH = 45.0    # °C
STORAGE_LOW_GB    = 5.0     # GB free

MAIN_LOOP_SEC     = 60      # check every 60 s
BATTERY_CHECK_SEC = 300     # 5 min cadence for battery
STORAGE_CHECK_SEC = 600     # 10 min cadence for storage
APP_CHECK_SEC     = 120     # 2 min cadence for app crash check

IMPORTANT_APPS = [
    "com.whatsapp",
    "com.termux",
    "com.google.android.googlequicksearchbox",
]

# Greeting schedule (hour in IST, 24h)
MORNING_HOUR = 8
NIGHT_HOUR   = 23

# ---------------------------------------------------------------------------
# State — prevent duplicate alerts within a cooldown window
# ---------------------------------------------------------------------------
class AlertState:
    def __init__(self):
        self._last: dict[str, float] = {}

    def should_fire(self, key: str, cooldown_sec: int = 1800) -> bool:
        now = asyncio.get_event_loop().time()
        last = self._last.get(key, 0)
        if now - last >= cooldown_sec:
            self._last[key] = now
            return True
        return False

state = AlertState()

# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no aiohttp dependency required)
# ---------------------------------------------------------------------------
async def _curl_post(url: str, payload: dict) -> bool:
    """Fire a POST request using curl subprocess (no extra deps needed)."""
    data = json.dumps(payload)
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-d", data,
        "--max-time", "10",
        "--connect-timeout", "5",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return proc.returncode == 0
    except Exception as exc:
        log.warning("curl POST failed (%s): %s", url, exc)
        return False


async def send_notification(title: str, content: str) -> bool:
    """Send a device notification via the God-Mode bridge."""
    payload = {
        "action": "notif.send",
        "params": {"title": title, "content": content},
    }
    ok = await _curl_post(NOTIF_URL, payload)
    log.info("NOTIF [%s] → %s | sent=%s", title, content[:80], ok)
    return ok


async def send_whatsapp_alert(prompt: str) -> bool:
    """Trigger Jenna to send a WhatsApp message to Boss via the chat API."""
    payload = {"prompt": f"SYSTEM_PROACTIVE: {prompt}"}
    ok = await _curl_post(CHAT_URL, payload)
    log.info("WHATSAPP ALERT → %s | sent=%s", prompt[:80], ok)
    return ok


async def alert(key: str, title: str, notif_body: str, wa_prompt: str,
                cooldown: int = 1800):
    """Unified alert: notification + WhatsApp, with cooldown de-dup."""
    if not state.should_fire(key, cooldown):
        log.debug("Alert '%s' suppressed (cooldown active)", key)
        return
    await asyncio.gather(
        send_notification(title, notif_body),
        send_whatsapp_alert(wa_prompt),
    )

# ---------------------------------------------------------------------------
# ADB helpers
# ---------------------------------------------------------------------------
ADB_DEVICE = os.getenv("ADB_DEVICE", "127.0.0.1:5555")

def _adb(args: list[str]) -> str:
    """Run an adb command and return stdout (empty string on error)."""
    try:
        result = subprocess.run(
            ["adb", "-s", ADB_DEVICE, "shell"] + args,
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_battery_level() -> int | None:
    raw = _adb(["dumpsys battery | grep level"])
    if not raw:
        # Try termux-battery-status
        try:
            r = subprocess.run(
                ["termux-battery-status"],
                capture_output=True, text=True, timeout=8,
            )
            data = json.loads(r.stdout)
            return int(data.get("percentage", -1))
        except Exception:
            return None
    m = re.search(r"level:\s*(\d+)", raw)
    return int(m.group(1)) if m else None


def get_battery_temp() -> float | None:
    raw = _adb(["dumpsys battery | grep temperature"])
    if not raw:
        try:
            r = subprocess.run(
                ["termux-battery-status"],
                capture_output=True, text=True, timeout=8,
            )
            data = json.loads(r.stdout)
            temp = data.get("temperature")
            if temp is not None:
                return float(temp)
        except Exception:
            return None
        return None
    m = re.search(r"temperature:\s*(\d+)", raw)
    if m:
        raw_val = int(m.group(1))
        # Android reports in tenths of a degree
        return raw_val / 10.0 if raw_val > 100 else float(raw_val)
    return None


def get_free_storage_gb() -> float | None:
    try:
        usage = shutil.disk_usage("/storage/emulated/0")
        return usage.free / (1024 ** 3)
    except Exception:
        try:
            usage = shutil.disk_usage("/data")
            return usage.free / (1024 ** 3)
        except Exception:
            return None


def is_app_running(package: str) -> bool:
    raw = _adb(["pidof", package])
    return bool(raw and raw.strip().isdigit() or (raw and raw.strip()))


# ---------------------------------------------------------------------------
# Monitor tasks
# ---------------------------------------------------------------------------
_tick: dict[str, int] = {}   # task_name → seconds since last run

def _due(key: str, interval: int, elapsed: int) -> bool:
    """True if enough seconds have elapsed for this key."""
    acc = _tick.get(key, interval)  # first run immediately
    acc += elapsed
    if acc >= interval:
        _tick[key] = 0
        return True
    _tick[key] = acc
    return False


async def check_battery(elapsed: int):
    if not _due("battery", BATTERY_CHECK_SEC, elapsed):
        return

    level = get_battery_level()
    temp  = get_battery_temp()

    log.info("Battery level=%s%% temp=%s°C", level, temp)

    if level is not None and level < BATTERY_LOW_PCT:
        await alert(
            key="battery_low",
            title="⚡ Jenna — Battery Alert",
            notif_body=f"Battery sirf {level}% bachi hai! Charger lagao abhi!",
            wa_prompt=f"battery low at {level}%, send boss an urgent WhatsApp alert in Hinglish to charge the phone now",
            cooldown=1800,
        )

    if temp is not None and temp > BATTERY_TEMP_HIGH:
        await alert(
            key="battery_temp",
            title="🌡️ Jenna — Overheating!",
            notif_body=f"Phone garam ho raha hai! Battery temp: {temp:.1f}°C — thoda rest do!",
            wa_prompt=f"phone is overheating at {temp:.1f}°C, send boss a WhatsApp alert in Hinglish to put the phone down and let it cool",
            cooldown=900,
        )


async def check_storage(elapsed: int):
    if not _due("storage", STORAGE_CHECK_SEC, elapsed):
        return

    free_gb = get_free_storage_gb()
    log.info("Storage free=%.2f GB", free_gb if free_gb is not None else -1)

    if free_gb is not None and free_gb < STORAGE_LOW_GB:
        await alert(
            key="storage_low",
            title="💾 Jenna — Storage Full!",
            notif_body=f"Sirf {free_gb:.1f} GB storage bacha hai! Kuch files delete karo.",
            wa_prompt=f"storage is critically low at {free_gb:.1f} GB free, send boss a WhatsApp alert in Hinglish to clean up storage",
            cooldown=3600,
        )


async def check_app_crashes(elapsed: int):
    if not _due("app_crash", APP_CHECK_SEC, elapsed):
        return

    # Check ANR / crash logs via logcat (non-blocking, last 5 lines)
    try:
        raw = _adb(["logcat -d -t 20 *:E 2>/dev/null | grep -iE 'ANR|CRASH|FATAL' | tail -5"])
    except Exception:
        raw = ""

    if raw:
        snippet = raw[:200].replace("\n", " | ")
        log.warning("App crash/ANR detected: %s", snippet)
        await alert(
            key="app_crash",
            title="💥 Jenna — App Crashed!",
            notif_body=f"Koi app crash hua! Details: {snippet[:100]}",
            wa_prompt=f"detected app crash or ANR on the device: {snippet[:150]}. Send boss a WhatsApp alert in Hinglish",
            cooldown=1200,
        )

    # Additionally check important apps
    for pkg in IMPORTANT_APPS:
        running = is_app_running(pkg)
        if not running:
            log.info("App not running: %s", pkg)
            # Only alert if it *was* running before (we track via state)
            key = f"app_down_{pkg}"
            if state.should_fire(key, cooldown_sec=3600):
                short = pkg.split(".")[-1]
                await alert(
                    key=f"alert_{pkg}",
                    title=f"📴 Jenna — {short} Down",
                    notif_body=f"{pkg} chal nahi raha. Restart karna chahiye?",
                    wa_prompt=f"important app {pkg} is not running on device. Send boss a brief WhatsApp in Hinglish",
                    cooldown=3600,
                )


# ---------------------------------------------------------------------------
# Time-based greetings
# ---------------------------------------------------------------------------
_greeted_morning = False
_greeted_night   = False

async def check_time_greetings():
    global _greeted_morning, _greeted_night
    # Use local IST time (TZ must be set; falls back gracefully)
    now = datetime.now()
    hour = now.hour

    if hour == MORNING_HOUR and not _greeted_morning:
        _greeted_morning = True
        _greeted_night   = False   # reset for tonight
        log.info("Sending Good Morning greeting 🌅")
        await asyncio.gather(
            send_notification(
                "☀️ Jenna — Good Morning!",
                "Good morning boss! 🌅 Uthiye, ek naya din shuru hua hai. Aaj bhi rocking rahenge! ✨",
            ),
            send_whatsapp_alert(
                "send boss a warm good morning message in Hinglish with motivational energy, mention the date and wish them a productive day"
            ),
        )

    elif hour == NIGHT_HOUR and not _greeted_night:
        _greeted_night   = True
        _greeted_morning = False   # reset for tomorrow
        log.info("Sending Good Night greeting 🌙")
        await asyncio.gather(
            send_notification(
                "🌙 Jenna — Good Night!",
                "Good night boss! 🌙 Aaj ka din bohot acha tha. Kal phir milenge. Sweet dreams! 💫",
            ),
            send_whatsapp_alert(
                "send boss a warm good night message in Hinglish, recap that it was a great day and wish sweet dreams"
            ),
        )

    elif hour not in (MORNING_HOUR, NIGHT_HOUR):
        # Reset flags outside the greeting hours so next day triggers work
        if hour > MORNING_HOUR and hour < NIGHT_HOUR:
            pass  # morning flag stays True until night
        if hour < MORNING_HOUR:
            _greeted_morning = False
            _greeted_night   = False


# ---------------------------------------------------------------------------
# Main daemon loop
# ---------------------------------------------------------------------------
_shutdown = asyncio.Event()

def _handle_signal(sig, frame):
    log.info("Received signal %s — shutting down gracefully…", sig)
    _shutdown.set()

async def main():
    log.info("=" * 60)
    log.info("Jenna Proactive Intelligence Daemon v2 starting up…")
    log.info("PID: %d", os.getpid())
    log.info("Monitors: battery every %ds, storage every %ds, loop every %ds",
             BATTERY_CHECK_SEC, STORAGE_CHECK_SEC, MAIN_LOOP_SEC)
    log.info("=" * 60)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT,  _handle_signal)

    elapsed = MAIN_LOOP_SEC  # start with full elapsed so first run fires immediately

    while not _shutdown.is_set():
        try:
            await asyncio.gather(
                check_battery(elapsed),
                check_storage(elapsed),
                check_app_crashes(elapsed),
                check_time_greetings(),
            )
        except Exception as exc:
            log.error("Unhandled error in main loop: %s", exc, exc_info=True)

        try:
            await asyncio.wait_for(
                asyncio.shield(_shutdown.wait()),
                timeout=MAIN_LOOP_SEC,
            )
        except asyncio.TimeoutError:
            pass  # normal — just the loop cadence

        elapsed = MAIN_LOOP_SEC

    log.info("Jenna Proactive Daemon stopped cleanly. Bye! 👋")


if __name__ == "__main__":
    asyncio.run(main())
