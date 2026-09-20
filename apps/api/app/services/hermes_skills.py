"""Hermes Autonomous Skill Engine & Self-Improvement Loop for Jenna AI.

Implements Nous Research's Hermes Agent autonomous skill creation architecture,
compatible with the https://agentskills.io open standard.

Features:
- Closed learning loop: Jenna automatically synthesizes, tests, and documents
  new reusable skills when solving complex multi-step problems.
- Standard SKILL.md format (YAML/JSON frontmatter + detailed markdown instructions).
- Persistent storage in workspace and user home directories.
- Dynamic skill discovery and execution in Antigravity ReAct loops.
"""

import datetime
import json
import logging
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.services.termux_service import WORKSPACE_ROOT

logger = logging.getLogger("jenna.hermes_skills")

SKILLS_DIR = WORKSPACE_ROOT / ".jenna" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _dump_frontmatter(data: Dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, (list, dict, bool, int, float)):
            lines.append(f"{k}: {json.dumps(v)}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_str = parts[1].strip()
    body = parts[2].strip()
    data: Dict[str, Any] = {}
    for line in fm_str.splitlines():
        line = line.strip()
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            try:
                data[k] = json.loads(v)
            except Exception:
                data[k] = v
    return data, body


class HermesSkillEngine:
    """Manages skill synthesis, storage, indexing, and execution."""

    def __init__(self, skills_dir: Optional[Path] = None) -> None:
        self.skills_dir = skills_dir or SKILLS_DIR
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_built_in_skills()

    def _ensure_built_in_skills(self) -> None:
        """Seed default foundational skills if not present."""
        built_ins = [
            {
                "name": "system-diagnostics",
                "description": "Comprehensive Android and Termux thermal, battery, memory, and process diagnostics.",
                "tags": ["android", "termux", "hardware", "diagnostics"],
                "version": "1.0.0",
                "instructions": (
                    "To diagnose the device:\n"
                    "1. Check battery capacity, temp, and status: `termux-battery-status` or `dumpsys battery`\n"
                    "2. Check CPU frequency and thermal throttling in `/sys/class/thermal/`\n"
                    "3. Check memory pressure using `free -h` and `vmstat`\n"
                    "4. Check active Termux and background daemons using `ps aux | grep python`\n"
                    "Synthesize findings and present warm, actionable advice to the user."
                ),
            },
            {
                "name": "bypass-charging-control",
                "description": "Governance and verification of Vivo/iQOO direct hardware Bypass Charging.",
                "tags": ["hardware", "charging", "vivo", "battery"],
                "version": "1.0.0",
                "instructions": (
                    "To manage and check Bypass Charging on iQOO / vivo devices (including iQOO Neo 10 / Snapdragon 8s Gen 4):\n"
                    "1. Check current charge level and charging current: `dumpsys battery`\n"
                    "2. Verify thermal temperature (maintain under 38.5°C for optimal gaming)\n"
                    "3. Check battery saver state: `cmd battery set low_power 0`\n"
                    "4. Guide the user to activate Monster Mode / Game Space sidebar for full hardware bypass lock."
                ),
            },
            {
                "name": "git-workflow-auto",
                "description": "Autonomous Git status inspection, branch verification, and safe commit operations.",
                "tags": ["git", "version-control", "code"],
                "version": "1.0.0",
                "instructions": (
                    "When managing workspace git repository:\n"
                    "1. Always run `git status` first to inspect modified, untracked, or staged files.\n"
                    "2. Use `git diff` on specific files to verify surgical line edits.\n"
                    "3. Never perform destructive commands like `git reset --hard` without explicit user intent.\n"
                    "4. Provide clean, meaningful commit messages following standard conventions."
                ),
            },
            {
                "name": "screen-pointer-guide",
                "description": "Visual coordinate guidance and screen element pointing using Dexter and overlay pointers.",
                "tags": ["ui", "screen", "pointer", "dexter"],
                "version": "1.0.0",
                "instructions": (
                    "To point on the phone screen:\n"
                    "1. Identify target coordinate (x, y) or detect element visually via `inspect_screen`.\n"
                    "2. Call `point_on_screen` or `circle_highlight` with duration (default 1500ms).\n"
                    "3. Inform the user warmly: 'Dekho meri jaan, maine screen pe point kar diya hai! 🎯'."
                ),
            },
        ]

        for s in built_ins:
            skill_folder = self.skills_dir / s["name"]
            skill_file = skill_folder / "SKILL.md"
            if not skill_file.exists():
                skill_folder.mkdir(parents=True, exist_ok=True)
                frontmatter = {
                    "name": s["name"],
                    "description": s["description"],
                    "version": s["version"],
                    "tags": s["tags"],
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "author": "Jenna AI (Hermes Engine)",
                }
                fm_header = _dump_frontmatter(frontmatter)
                content = f"{fm_header}\n\n# {s['name'].replace('-', ' ').title()}\n\n{s['instructions']}\n"
                skill_file.write_text(content, encoding="utf-8")

    def create_skill(
        self,
        name: str,
        description: str,
        instructions: str,
        tags: Optional[List[str]] = None,
        author: str = "Jenna AI",
        version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Create and register a new reusable skill following agentskills.io standard."""
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-")
        skill_folder = self.skills_dir / slug
        skill_folder.mkdir(parents=True, exist_ok=True)

        frontmatter = {
            "name": slug,
            "description": description,
            "version": version,
            "tags": tags or ["learned-skill"],
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "author": author,
        }

        fm_header = _dump_frontmatter(frontmatter)
        full_markdown = f"{fm_header}\n\n# {name}\n\n{instructions}\n"
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(full_markdown, encoding="utf-8")

        logger.info(f"Learned & stored new Hermes skill: '{slug}' at {skill_file}")
        return {
            "success": True,
            "skill_name": slug,
            "path": str(skill_file),
            "description": description,
            "message": f"Successfully synthesized and saved new skill '{slug}'.",
        }

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific skill by name or slug."""
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-")
        skill_file = self.skills_dir / slug / "SKILL.md"
        if not skill_file.exists():
            return None

        content = skill_file.read_text(encoding="utf-8")
        frontmatter, body = _parse_frontmatter(content)

        return {
            "name": slug,
            "frontmatter": frontmatter,
            "instructions": body,
            "path": str(skill_file),
        }

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all indexed skills in the Hermes skill repository."""
        skills = []
        for folder in sorted(self.skills_dir.iterdir()):
            if folder.is_dir():
                skill_file = folder / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        frontmatter, _ = _parse_frontmatter(content)
                        skills.append({
                            "name": folder.name,
                            "description": frontmatter.get("description", "No description"),
                            "version": frontmatter.get("version", "1.0.0"),
                            "tags": frontmatter.get("tags", []),
                            "author": frontmatter.get("author", "Jenna"),
                            "path": str(skill_file),
                        })
                    except Exception as e:
                        logger.warning(f"Error reading skill {folder.name}: {e}")
        return skills

    async def auto_synthesize_skill(
        self,
        task_name: str,
        problem_statement: str,
        solution_steps: List[str],
        code_snippets: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Hermes Closed-Loop Learning: Synthesizes a new skill from a solved problem."""
        instructions_md = (
            f"### Problem Solved\n{problem_statement}\n\n"
            f"### Autonomous Solution Procedure\n"
        )
        for idx, step in enumerate(solution_steps, 1):
            instructions_md += f"{idx}. {step}\n"

        if code_snippets:
            instructions_md += f"\n### Reference Implementation\n```\n{code_snippets}\n```\n"

        description = f"Autonomous procedure for {task_name.replace('-', ' ')} learned during live execution."
        return self.create_skill(
            name=task_name,
            description=description,
            instructions=instructions_md,
            tags=["auto-synthesized", "self-learned"],
            author="Jenna AI (Self-Improvement Loop)",
        )


hermes_skill_engine = HermesSkillEngine()
