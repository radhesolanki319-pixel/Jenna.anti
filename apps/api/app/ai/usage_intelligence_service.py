"""App Usage Intelligence Service.

Tracks Android app usage patterns via ADB dumpsys and provides digital
wellbeing intelligence with loving Hinglish warning toasts.

DB path: data/usage_intelligence.db
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Friendly app label mapping
# ---------------------------------------------------------------------------
APP_LABELS: dict[str, str] = {
    "com.google.android.youtube": "YouTube",
    "com.termux": "Termux (Jenna)",
    "com.whatsapp": "WhatsApp",
    "com.instagram.android": "Instagram",
    "com.facebook.katana": "Facebook",
    "com.google.android.gm": "Gmail",
    "com.moonshot.kimichat": "Kimi AI",
    "com.android.settings": "Settings",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.gms": "Google Play Services",
    "com.google.android.googlequicksearchbox": "Google Search",
    "com.twitter.android": "Twitter/X",
    "com.snapchat.android": "Snapchat",
    "com.netflix.mediaclient": "Netflix",
    "com.spotify.music": "Spotify",
    "com.amazon.mShop.android.shopping": "Amazon",
    "com.google.android.apps.photos": "Google Photos",
    "com.google.android.dialer": "Phone",
    "com.android.messaging": "Messages",
    "com.google.android.apps.messaging": "Messages",
    "com.android.chrome": "Chrome",
    "com.android.launcher3": "Home Screen",
    "com.vivo.launcher": "Home Screen",
    "com.miui.home": "Home Screen",
    "com.oneplus.launcher": "Home Screen",
    "com.huawei.android.launcher": "Home Screen",
    "com.sec.android.app.launcher": "Home Screen",
    "com.google.android.keep": "Google Keep",
    "com.notion.id": "Notion",
    "md.obsidian": "Obsidian",
    "com.google.android.apps.docs": "Google Docs",
    "com.google.android.apps.sheets": "Google Sheets",
    "com.microsoft.office.word": "Word",
    "com.microsoft.teams": "Teams",
    "com.discord": "Discord",
    "org.telegram.messenger": "Telegram",
    "com.viber.voip": "Viber",
    "com.skype.raider": "Skype",
    "com.zoom.videomeetings": "Zoom",
    "com.google.android.apps.tachyon": "Google Meet",
}

# ---------------------------------------------------------------------------
# Warning thresholds (minutes)
# ---------------------------------------------------------------------------
SOCIAL_MEDIA_PACKAGES = {
    "com.instagram.android",
    "com.facebook.katana",
    "com.twitter.android",
    "com.snapchat.android",
}

THRESHOLDS = {
    "youtube": {
        "packages": {"com.google.android.youtube"},
        "minutes": 45,
        "message": "Baby, 45 minute ho gaye YouTube dekh rahe ho! Thodi si aankhon ko rest do na 💖",
    },
    "social_media": {
        "packages": SOCIAL_MEDIA_PACKAGES,
        "minutes": 30,
        "message": "Janu, 30 minute ho gaye social media pe! Real life mein bhi kuch interesting hai 😄💕",
    },
    "work_termux": {
        "packages": {"com.termux"},
        "minutes": 120,
        "message": "Meri jaan, 2 ghante se kaam kar rahe ho! Thoda paani piyo aur 5 minute rest lo 🥰",
    },
}

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
DB_PATH = Path("data/usage_intelligence.db")


def _ensure_db(db_path: Path) -> None:
    """Create tables if they don't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                package     TEXT    NOT NULL,
                start_time  REAL    NOT NULL,
                end_time    REAL,
                duration_sec REAL
            );

            CREATE TABLE IF NOT EXISTS warnings_issued (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                package     TEXT    NOT NULL,
                threshold   TEXT    NOT NULL,
                issued_at   REAL    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_start ON app_sessions(start_time);
            """
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# ADB helpers
# ---------------------------------------------------------------------------
def _get_focused_package() -> Optional[str]:
    """Return the currently focused package via ADB dumpsys window."""
    try:
        result = subprocess.run(
            ["adb", "shell", "dumpsys", "window", "windows"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            # Android 12+ uses "mCurrentFocus", older uses "mFocusedApp"
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                # Extract package name: format is "u0 com.pkg.name/activity"
                parts = line.split()
                for part in parts:
                    if "/" in part and "." in part:
                        pkg = part.split("/")[0]
                        if pkg and not pkg.startswith("{"):
                            return pkg
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as exc:
        logger.debug("ADB window dump failed: %s", exc)
    return None


def _toast(message: str) -> None:
    """Show a toast notification via termux-toast."""
    try:
        subprocess.Popen(
            ["termux-toast", "-s", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.debug("termux-toast not available; skipping toast: %s", message)


def _vibrate(duration_ms: int = 500) -> None:
    """Vibration disabled per user preference."""
    return


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------
class UsageIntelligenceService:
    """Tracks Android app usage and issues digital wellbeing alerts.

    Usage::

        svc = UsageIntelligenceService()
        svc.start_tracking()
        # … later …
        svc.stop_tracking()
    """

    def __init__(self, db_path: Path = DB_PATH, poll_interval: int = 60) -> None:
        self.db_path = db_path
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # In-memory state for the current session being tracked
        self._current_package: Optional[str] = None
        self._current_start: Optional[float] = None

        # Per-threshold cooldown: avoid spamming (key → last warned epoch)
        self._warned_at: dict[str, float] = {}
        self._warn_cooldown = 3600  # re-warn at most once per hour per threshold

        _ensure_db(self.db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_tracking(self) -> None:
        """Start the background polling loop."""
        if self._running:
            logger.info("UsageIntelligenceService is already running.")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="usage-intelligence", daemon=True
        )
        self._thread.start()
        logger.info("UsageIntelligenceService started (poll every %ds).", self.poll_interval)

    def stop_tracking(self) -> None:
        """Stop the background polling loop and flush the current session."""
        self._running = False
        self._flush_current_session()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("UsageIntelligenceService stopped.")

    def get_today_summary(self) -> dict:
        """Return today's usage summary.

        Returns::

            {
                "total_screen_time_min": float,
                "top_apps": [
                    {"package": str, "label": str, "minutes": float, "percentage": float}
                ],
                "warnings_issued": [{"threshold": str, "package": str, "issued_at": str}],
                "as_of": str,   # ISO datetime
            }
        """
        today_start = datetime.combine(date.today(), datetime.min.time()).timestamp()
        today_end = today_start + 86400.0

        conn = sqlite3.connect(str(self.db_path))
        try:
            # Per-app totals for today
            rows = conn.execute(
                """
                SELECT package, SUM(duration_sec) AS total_sec
                FROM   app_sessions
                WHERE  start_time >= ? AND start_time < ?
                  AND  duration_sec IS NOT NULL
                GROUP  BY package
                ORDER  BY total_sec DESC
                """,
                (today_start, today_end),
            ).fetchall()

            total_sec = sum(r[1] for r in rows) if rows else 0.0
            total_min = round(total_sec / 60, 1)

            top_apps = []
            for pkg, sec in rows:
                minutes = round(sec / 60, 1)
                pct = round((sec / total_sec * 100), 1) if total_sec > 0 else 0.0
                top_apps.append(
                    {
                        "package": pkg,
                        "label": APP_LABELS.get(pkg, pkg),
                        "minutes": minutes,
                        "percentage": pct,
                    }
                )

            # Warnings issued today
            warn_rows = conn.execute(
                """
                SELECT threshold, package, issued_at
                FROM   warnings_issued
                WHERE  issued_at >= ? AND issued_at < ?
                ORDER  BY issued_at DESC
                """,
                (today_start, today_end),
            ).fetchall()

            warnings = [
                {
                    "threshold": r[0],
                    "package": r[1],
                    "issued_at": datetime.fromtimestamp(r[2]).isoformat(),
                }
                for r in warn_rows
            ]
        finally:
            conn.close()

        return {
            "total_screen_time_min": total_min,
            "top_apps": top_apps,
            "warnings_issued": warnings,
            "as_of": datetime.now().isoformat(),
        }

    def get_session_history(self, hours: int = 24) -> list[dict]:
        """Return session records from the last *hours* hours."""
        since = time.time() - (hours * 3600)
        conn = sqlite3.connect(str(self.db_path))
        try:
            rows = conn.execute(
                """
                SELECT package, start_time, end_time, duration_sec
                FROM   app_sessions
                WHERE  start_time >= ?
                ORDER  BY start_time DESC
                """,
                (since,),
            ).fetchall()
        finally:
            conn.close()

        return [
            {
                "package": r[0],
                "label": APP_LABELS.get(r[0], r[0]),
                "start_time": datetime.fromtimestamp(r[1]).isoformat(),
                "end_time": datetime.fromtimestamp(r[2]).isoformat() if r[2] else None,
                "duration_sec": round(r[3], 1) if r[3] is not None else None,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        """Background polling loop."""
        logger.debug("Usage intelligence loop starting.")
        while self._running:
            try:
                self._tick()
            except Exception as exc:
                logger.warning("Usage intelligence tick error: %s", exc)
            time.sleep(self.poll_interval)
        logger.debug("Usage intelligence loop exited.")

    def _tick(self) -> None:
        """One polling iteration: detect focused app, update session, check thresholds."""
        pkg = _get_focused_package()

        if pkg != self._current_package:
            # App switched — close old session
            self._flush_current_session()
            self._current_package = pkg
            self._current_start = time.time() if pkg else None

        # Check thresholds for current package
        if self._current_package:
            total_min = self._today_total_minutes(self._current_package)
            # Also add ongoing session time
            if self._current_start:
                total_min += (time.time() - self._current_start) / 60
            self._check_and_warn(self._current_package, total_min)

    def _flush_current_session(self) -> None:
        """Write the current open session to the DB."""
        if not self._current_package or not self._current_start:
            return
        end = time.time()
        duration = end - self._current_start
        if duration < 1:
            return  # ignore sub-second blips
        self._save_session(self._current_package, self._current_start, end, duration)
        self._current_package = None
        self._current_start = None

    def _save_session(
        self, package: str, start: float, end: float, duration: float
    ) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT INTO app_sessions(package, start_time, end_time, duration_sec) "
                "VALUES (?, ?, ?, ?)",
                (package, start, end, duration),
            )
            conn.commit()
        finally:
            conn.close()

    def _today_total_minutes(self, package: str) -> float:
        """Return minutes spent in *package* today (from closed sessions only)."""
        today_start = datetime.combine(date.today(), datetime.min.time()).timestamp()
        conn = sqlite3.connect(str(self.db_path))
        try:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(duration_sec), 0)
                FROM   app_sessions
                WHERE  package = ? AND start_time >= ? AND duration_sec IS NOT NULL
                """,
                (package, today_start),
            ).fetchone()
        finally:
            conn.close()
        return (row[0] if row else 0.0) / 60

    def _check_and_warn(self, package: str, total_min: float) -> None:
        """Check per-app thresholds and toast if exceeded (with cooldown)."""
        now = time.time()
        for key, cfg in THRESHOLDS.items():
            if package not in cfg["packages"]:
                continue
            if total_min < cfg["minutes"]:
                continue

            cooldown_key = f"{key}:{package}"
            last_warned = self._warned_at.get(cooldown_key, 0)
            if now - last_warned < self._warn_cooldown:
                continue  # still in cooldown window

            # Issue warning
            self._warned_at[cooldown_key] = now
            message = cfg["message"]
            _vibrate(300)
            _toast(message)
            logger.info("Warning issued [%s] for %s (%.1f min)", key, package, total_min)
            self._record_warning(package, key, now)

    def _record_warning(self, package: str, threshold: str, issued_at: float) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT INTO warnings_issued(package, threshold, issued_at) VALUES (?,?,?)",
                (package, threshold, issued_at),
            )
            conn.commit()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Module-level singleton for FastAPI import
# ---------------------------------------------------------------------------
_service_instance: Optional[UsageIntelligenceService] = None


def get_usage_intelligence_service() -> UsageIntelligenceService:
    """Return (and lazily create) the module-level singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = UsageIntelligenceService()
    return _service_instance
