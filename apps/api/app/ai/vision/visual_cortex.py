"""Persistent Visual Recall Cortex & Ambient Memory System for Jenna AI.

Maintains an indexed timeline of all user screen activities, applications,
videos, texts, and interactions across time in an embedded SQLite database.
Enables Zero-Input perception where Jenna ALREADY knows everything the user has done.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
import time
from typing import Any

logger = logging.getLogger("jenna.visual_cortex")

DB_PATH = Path(
    os.getenv(
        "JENNA_VISUAL_CORTEX_DB",
        "/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/data/visual_recall.db",
    )
)


class VisualRecallCortex:
    """Manages long-term visual event timeline and ambient screen memory."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create visual timeline tables and indexes."""
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS visual_timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    iso_time TEXT NOT NULL,
                    package_name TEXT,
                    app_name TEXT,
                    window_title TEXT,
                    is_floating BOOLEAN DEFAULT 0,
                    visual_summary TEXT,
                    extracted_text TEXT,
                    action_detected TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timeline_ts ON visual_timeline(timestamp DESC);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timeline_pkg ON visual_timeline(package_name);"
            )
            conn.commit()

    def record_screen_event(
        self,
        package_name: str | None,
        app_name: str | None,
        window_title: str | None,
        visual_summary: str,
        extracted_text: list[str] | str | None = None,
        is_floating: bool = False,
        action_detected: str | None = None,
    ) -> int:
        """Insert a newly observed screen visual state into the memory timeline."""
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        text_str = ""
        if isinstance(extracted_text, list):
            text_str = "\n".join(extracted_text)
        elif isinstance(extracted_text, str):
            text_str = extracted_text

        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO visual_timeline (
                    timestamp, iso_time, package_name, app_name, window_title,
                    is_floating, visual_summary, extracted_text, action_detected
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_ts,
                    now_iso,
                    package_name,
                    app_name or (package_name.split(".")[-1].capitalize() if package_name else "Unknown"),
                    window_title,
                    1 if is_floating else 0,
                    visual_summary,
                    text_str,
                    action_detected,
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    def get_recent_timeline(self, limit: int = 10, minutes: int = 60) -> list[dict[str, Any]]:
        """Retrieve recent chronological screen activities within the past N minutes."""
        min_ts = time.time() - (minutes * 60)
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, iso_time, package_name, app_name,
                       window_title, is_floating, visual_summary, extracted_text, action_detected
                FROM visual_timeline
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (min_ts, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_ambient_context_prompt(self, max_events: int = 6) -> str:
        """Format the recent visual history into an immediate ambient memory prompt snippet."""
        events = self.get_recent_timeline(limit=max_events, minutes=45)
        if not events:
            return ""

        lines = [
            "<persistent_visual_recall_cortex>",
            "[ZERO-INPUT AMBIENT SCREEN MEMORY - Jenna's Living Eyes]:",
            "The following chronological timeline shows what the user was actively seeing and doing on their phone screen:",
        ]

        for ev in reversed(events):
            t_str = ev.get("iso_time", "")[11:19]  # HH:MM:SS
            app = ev.get("app_name") or "Unknown"
            floating_str = " (Vivo Small Window)" if ev.get("is_floating") else ""
            summary = ev.get("visual_summary") or ""
            # Truncate summary cleanly
            if len(summary) > 200:
                summary = summary[:197] + "..."
            lines.append(f"- [{t_str}] App: {app}{floating_str} | Visual Event: {summary}")

        lines.extend([
            "[CRITICAL INSTRUCTION: You already know this history from your continuous background vision. "
            "Never ask the user what they were doing or watching. You possess continuous, zero-input recall.]",
            "</persistent_visual_recall_cortex>",
        ])
        return "\n".join(lines)


# Global singleton
visual_recall_cortex = VisualRecallCortex()
