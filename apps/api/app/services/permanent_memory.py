"""Jenna Permanent Memory System.

Persistent JSON-based memory and knowledge graph for Jenna AI.
Ensures zero-amnesia across restarts: remembers Boss's habits, preferences,
projects, personal facts, and past conversational context permanently.
"""

import datetime
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jenna.permanent_memory")

WORKSPACE_ROOT = Path(
    os.getenv(
        "WORKSPACE_ROOT",
        "/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna",
    )
)
MEMORY_FILE = WORKSPACE_ROOT / "data" / "permanent_memory.json"
MAX_MEMORIES = 1000


class JennaPermanentMemory:
    """Manages persistent long-term memories, facts, and profile for Boss."""

    def __init__(self, memory_file: Optional[Path] = None):
        self.memory_file = memory_file or MEMORY_FILE
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {
            "version": "1.0",
            "boss_profile": {
                "name": "Boss",
                "phone_model": "iQOO Neo 10 (I2405)",
                "relationship": "Supreme Creator / Boss",
                "language_preference": "Hinglish / Hindi",
                "companion_style": "Feminine, loving, respectful, high-velocity, proactive",
            },
            "preferences": {},
            "facts": {},
            "projects": {},
            "habits": {},
            "people": {},
            "events": [],
            "memories": [],  # list of {id, key, value, category, created_at, updated_at}
        }
        self._load()

    def _load(self) -> None:
        """Load persistent memories from JSON file."""
        if not self.memory_file.exists():
            self._save()
            return
        try:
            content = self.memory_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            if isinstance(loaded, dict):
                self.data.update(loaded)
                logger.info(f"Loaded {len(self.data.get('memories', []))} memories from disk.")
        except Exception as e:
            logger.warning(f"Failed to load permanent memory ({e}); initializing default.")
            self._save()

    def _save(self) -> None:
        """Atomic write to disk."""
        try:
            tmp_path = self.memory_file.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(self.data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self.memory_file)
        except Exception as e:
            logger.error(f"Failed to persist permanent memory to disk: {e}")

    def remember(self, key: str, value: Any, category: str = "facts") -> Dict[str, Any]:
        """Store or update a memory permanently."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        category = category.lower().strip()
        if category not in ("preferences", "facts", "projects", "habits", "people", "events"):
            category = "facts"

        # Update specific category dictionary if applicable
        if category in self.data and isinstance(self.data[category], dict):
            self.data[category][key] = value

        # Update or append in linear memory log
        existing = None
        for m in self.data.get("memories", []):
            if m.get("key", "").lower() == key.lower():
                existing = m
                break

        if existing:
            existing["value"] = value
            existing["category"] = category
            existing["updated_at"] = now_iso
            res = existing
        else:
            res = {
                "id": f"mem_{len(self.data.get('memories', [])) + 1}",
                "key": key,
                "value": value,
                "category": category,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            self.data.setdefault("memories", []).append(res)

        # Prune if exceeding limit
        if len(self.data["memories"]) > MAX_MEMORIES:
            self.data["memories"] = self.data["memories"][-MAX_MEMORIES:]

        self._save()
        return {"success": True, "action": "remembered", "entry": res}

    def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by keyword match in key, value, or category."""
        q_tokens = [t.lower() for t in re.split(r"\W+", query) if len(t) > 1]
        if not q_tokens:
            return self.data.get("memories", [])[-limit:]

        scored: List[tuple[int, Dict[str, Any]]] = []
        for m in self.data.get("memories", []):
            text = f"{m.get('key', '')} {m.get('value', '')} {m.get('category', '')}".lower()
            score = sum(1 for token in q_tokens if token in text)
            if score > 0:
                scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def get_user_profile(self) -> Dict[str, Any]:
        """Return Boss's complete profile and compiled preferences."""
        return {
            "profile": self.data.get("boss_profile", {}),
            "preferences": self.data.get("preferences", {}),
            "projects": self.data.get("projects", {}),
            "habits": self.data.get("habits", {}),
            "total_memories": len(self.data.get("memories", [])),
        }

    def update_preference(self, key: str, value: Any) -> Dict[str, Any]:
        """Update a Boss preference."""
        return self.remember(key, value, category="preferences")

    def get_context_for_conversation(self) -> str:
        """Format high-priority memories and Boss profile for system prompt injection."""
        profile = self.data.get("boss_profile", {})
        prefs = self.data.get("preferences", {})
        projects = self.data.get("projects", {})
        recent = self.data.get("memories", [])[-15:]

        lines = [
            "### PERMANENT MEMORY & BOSS KNOWLEDGE GRAPH:",
            f"- Boss Name: {profile.get('name', 'Boss')}",
            f"- Device: {profile.get('phone_model', 'iQOO Neo 10 (I2405)')}",
            f"- Companion Mode: {profile.get('companion_style', 'Loving, respectful, high-velocity female AI')}",
        ]

        if prefs:
            pref_strs = [f"{k}: {v}" for k, v in list(prefs.items())[:8]]
            lines.append(f"- Known Preferences: {'; '.join(pref_strs)}")

        if projects:
            proj_strs = [f"{k}: {v}" for k, v in list(projects.items())[:6]]
            lines.append(f"- Active Projects: {'; '.join(proj_strs)}")

        if recent:
            lines.append("- Recent Permanent Recollections:")
            for m in recent[-6:]:
                lines.append(f"  * [{m.get('category', 'fact')}] {m.get('key')}: {m.get('value')}")

        return "\n".join(lines)

    def learn_from_conversation(self, user_msg: str, assistant_msg: str) -> None:
        """Simple heuristic extractor to remember explicit statements automatically."""
        u_lower = user_msg.lower()
        
        # Check for explicit 'mera/meri ... pasand hai' or 'mujhe ... pasand hai'
        m = re.search(r"mujhe\s+([a-zA-Z0-9_\s]{2,30})\s+(pasand|achha\s+lagta)\s+hai", u_lower)
        if m:
            item = m.group(1).strip()
            self.remember(f"likes_{item}", f"Boss likes {item}", category="preferences")

        # Check for project mentions
        if "project" in u_lower or "app" in u_lower:
            m_proj = re.search(r"(?:project|app|naam)\s+([a-zA-Z0-9_\-]{3,20})", u_lower)
            if m_proj:
                p_name = m_proj.group(1).strip()
                self.remember(f"project_{p_name}", f"Project {p_name} mentioned by Boss", category="projects")


permanent_memory = JennaPermanentMemory()
