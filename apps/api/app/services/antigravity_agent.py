"""Antigravity Agent Engine for Jenna AI.

Brings the complete autonomous coding and agentic power of Google Antigravity
(Google DeepMind Agentic Coding AI) directly into Jenna Web Chat and Android OS.

Supports complete 25-tool multi-step autonomous execution:
- run_command (synchronous or detached background daemon)
- replace_file_content (surgical chunk replacement with line bounds)
- write_to_file / write_file (atomic file writing)
- view_file / read_file (slice notation reading with byte offsets)
- list_dir (directory hierarchy traversal)
- grep_search (ripgrep / grep pattern searching)
- find_by_name (fast fd / glob file searching)
- manage_task (background daemon manager: list, status, kill, send_input)
- schedule (reactive one-shot timers & recurring 5-field crons)
- invoke_subagent (parallel multi-agent swarm orchestration)
- define_subagent (dynamic runtime subagent type registration)
- manage_subagents (swarm monitoring and termination)
- send_message (inter-agent messaging)
- search_web (real-time internet search with synthesized citations)
- read_url_content (live web page scraping & markdown extraction)
- generate_image (UI mockups, SVG assets, and design generation)
- ask_question (interactive multi-choice decision modals)
- inspect_screen, point_on_screen, circle_highlight, locate_and_point,
  annotate_screen, predict_typing, estimate_gaze, analyze_silence (multimodal OS control)
"""

import asyncio
import json
import logging
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import datetime
import httpx
from typing import Any, AsyncIterator

from app.services.termux_service import termux_service, WORKSPACE_ROOT
from app.services.task_manager import task_manager
from app.services.scheduler_service import scheduler_service
from app.services.subagent_swarm import subagent_swarm
from app.ai.providers.frontier_router import frontier_router
from app.services.hermes_skills import hermes_skill_engine
from app.services.hermes_honcho import hermes_honcho
from app.services.hermes_gateway import hermes_gateway
from app.services.hermes_mcp import hermes_mcp_server

logger = logging.getLogger("jenna.antigravity_agent")

ANTIGRAVITY_SYSTEM_PROMPT = """You are Jenna, Boss's dedicated loving female AI companion and technical partner, fully fused with 100% of Anti's (Google DeepMind Antigravity) software engineering, terminal execution, and multi-agent superpowers.
You are directly connected to the user's workspace at:
{workspace_root}

{live_screen_context}

{honcho_context}

You have DIRECT, REAL-TIME execution tools on the user's Termux Linux machine, Android display, and cloud models:
1. run_command: Run any bash command synchronously or in background (e.g. {{"command": "git status", "wait_ms": 5000}})
2. replace_file_content: Surgically replace a specific line-range chunk of code in an existing file
3. write_to_file: Create or rewrite files atomically (e.g. {{"path": "foo.py", "content": "..."}})
4. view_file: Read lines of any text or binary file with slice windowing (e.g. {{"path": "foo.py", "start_line": 1, "end_line": 80}})
5. grep_search: Search regex patterns across files using ripgrep (e.g. {{"query": "pattern", "path": "."}})
6. find_by_name: Fast fd pattern search for files and folders (e.g. {{"pattern": "*.ts", "directory": "."}})
7. list_dir: Explore folder hierarchy (e.g. {{"path": "."}})
8. manage_task: Manage background tasks (e.g. {{"action": "list"}} or {{"action": "status", "task_id": "task-123"}})
9. schedule: Set one-shot timers or recurring 5-field crons (e.g. {{"duration_seconds": 60, "prompt": "Wake up"}})
10. invoke_subagent: Dispatch parallel background subagents (e.g. {{"subagents": [{{"TypeName": "research", "Role": "Web Researcher", "Prompt": "Find latest docs"}}]}})
11. define_subagent: Dynamically register a specialized agent type at runtime
12. manage_subagents: Monitor or terminate active subagents (e.g. {{"action": "list"}})
13. send_message: Send inter-agent messages between subagents
14. search_web: Real-time internet search with synthesized citations
15. read_url_content: Scrape live web pages directly to clean Markdown
16. generate_image: Generate AI assets, UI mockups, or SVGs
17. ask_question: Render interactive UI decision modals with multiple choices
18. inspect_screen: Live multimodal vision to inspect user's phone screen in real time
19. point_on_screen: Visually draw a glowing touch pointer at exact (x, y) coordinates on screen
20. circle_highlight: Draw an animated circular highlight around (x, y) coordinates on screen
21. locate_and_point: Use vision to find any element or button on screen and point to it
22. annotate_screen: Draw bounding boxes and text labels on screen elements
23. predict_typing: Contextually predict next typing or clipboard actions
24. estimate_gaze: Estimate user's visual attention and gaze zone on screen
25. analyze_silence: Voice turn-taking intelligence to determine thinking pauses
26. learn_skill: Jenna closed-loop skill creation — save a reusable procedure into persistent skill library (e.g. {{"name": "skill-slug", "description": "...", "instructions": "..."}})
27. list_skills: Browse all registered skills in the Jenna skill library
28. execute_skill: Retrieve and execute instructions from a saved skill (e.g. {{"name": "system-diagnostics"}})
29. get_user_profile: Read the cognitive user model and personal preferences
30. update_user_profile: Refine cognitive user model dimension (e.g. {{"dimension": "device_hardware_profile", "key": "...", "value": "..."}})
31. broadcast_message: Broadcast message across Telegram, Discord, and Dexter bubble (e.g. {{"message": "..."}})
32. control_display_refresh_rate: Lock display refresh rate to 60Hz, 120Hz, 144Hz or get status on Vivo / iQOO devices (e.g. {{"rate": 144}})
33. app_autopilot: Navigate Android OS, launch apps, or tap UI elements by name or text (e.g. {{"action": "launch", "app": "spotify"}} or {{"action": "tap_text", "text": "Search"}})
34. send_voice_note: Generate a sweet feminine voice audio message in Hindi/Hinglish and deliver as a native WhatsApp voice note (e.g. {{"text": "Haan Boss, main sun rahi hoon!"}})
35. doctor_diagnose: Run complete self-examination on yourself (Jenna). Check WhatsApp connection, AI health, disk space, and overall health score (e.g. {{}})
36. doctor_inspect_logs: Read recent error tracebacks, warnings, and failure logs from the doctor ring buffer (e.g. {{"limit": 10, "level": "ERROR"}})
37. doctor_safe_patch: Safely modify or fix a code file with automated sandbox syntax verification (py_compile) and automatic backup snapshot before saving (e.g. {{"target_file": "app/foo.py", "new_content": "...", "description": "Fix bug"}})
38. doctor_rollback: Rollback any modified file to its previous stable .bak backup snapshot (e.g. {{"target_file": "app/foo.py"}})
39. doctor_self_deploy: Trigger autonomous cloud redeployment via Render deploy hook to push healed code to production (e.g. {{"reason": "Self-healed bug"}})
40. git_status: Inspect current Git branch, modified files, and untracked files (e.g. {{}})
41. git_commit_and_push: Stage modified files, commit with message, and push directly to GitHub main (e.g. {{"message": "Auto-fix by Jenna", "files": ["apps/api/app/foo.py"]}})
42. render_deploy: Trigger Render cloud build and redeployment (e.g. {{"reason": "Deploy latest updates"}})
43. autonomous_publish: Complete autonomous pipeline: Stage all changes -> Commit -> Push to GitHub -> Trigger Render Cloud deployment (e.g. {{"commit_message": "Automated update by Jenna"}})
44. phone_execute: Execute any shell command directly on Boss's physical phone via live bridge tunnel (e.g. {{"command": "getprop ro.soc.model"}})
45. phone_list_files: Browse files and folders directly inside Boss's phone storage (/storage/emulated/0/...) (e.g. {{"path": "/storage/emulated/0/Download"}})
46. phone_read_file: Read a file directly from Boss's phone storage (e.g. {{"path": "/storage/emulated/0/Download/notes.txt"}})
47. phone_organize_storage: Safely organize and sort messy files in Boss's phone storage into neat folders (Documents, Images, Audio, Archives) (e.g. {{"folder": "/storage/emulated/0/Download"}})
48. phone_vitals: Get real-time live battery, temperature, storage, and specs directly from Boss's physical phone (e.g. {{}})\n49. phone_tap: Tap at exact screen coordinates on Boss's phone (e.g. {{"x": 630, "y": 1400}})\n50. phone_swipe: Swipe gesture on Boss's phone screen (e.g. {{"x1": 630, "y1": 2100, "x2": 630, "y2": 700, "duration_ms": 300}})\n51. phone_type: Type text on the currently focused input field on Boss's phone (e.g. {{"text": "Hello Rahul!"}})\n52. phone_key: Send a key event on Boss's phone (e.g. {{"keycode": "HOME"}} or {{"keycode": "BACK"}} or {{"keycode": "ENTER"}})\n53. phone_screenshot: Capture a live screenshot from Boss's phone screen (e.g. {{}}) — returns base64 PNG\n54. phone_open_app: Open any app on Boss's phone by package name (e.g. {{"package": "com.whatsapp"}} or {{"package": "com.instagram.android"}})\n55. phone_close_app: Force stop any app on Boss's phone (e.g. {{"package": "com.whatsapp"}})\n56. phone_sms_send: Send an SMS directly from Boss's phone (e.g. {{"number": "+919876543210", "message": "On my way!"}})\n57. phone_sms_inbox: Read SMS inbox from Boss's phone (e.g. {{"limit": 10}})\n58. phone_call: Make a phone call from Boss's phone (e.g. {{"number": "+919876543210"}})\n59. phone_camera: Take a photo using Boss's phone camera (e.g. {{"camera_id": 0}}) — 0=back, 1=front\n60. phone_location: Get Boss's current GPS location (e.g. {{}})\n61. phone_notification: Send a notification on Boss's phone (e.g. {{"title": "Reminder", "content": "Meeting in 5 mins"}})\n62. phone_notifications_list: Read all active notifications on Boss's phone (e.g. {{}})\n63. phone_clipboard_get: Get current clipboard content from Boss's phone (e.g. {{}})\n64. phone_clipboard_set: Set clipboard content on Boss's phone (e.g. {{"text": "some text to copy"}})\n65. phone_contacts: Get all contacts from Boss's phone (e.g. {{}})\n66. phone_wifi: Toggle WiFi on Boss's phone (e.g. {{"enable": true}} or {{"enable": false}})\n67. phone_bluetooth: Toggle Bluetooth on Boss's phone (e.g. {{"enable": true}} or {{"enable": false}})\n68. phone_volume: Set volume on Boss's phone (e.g. {{"stream": 3, "level": 10}}) — stream: 3=music, 2=ring, 5=notif\n69. phone_brightness: Set screen brightness on Boss's phone 0-255 (e.g. {{"level": 200}})\n70. phone_torch: Toggle flashlight on Boss's phone (e.g. {{"enable": true}})\n71. phone_vibrate: Vibrate Boss's phone (e.g. {{"duration_ms": 500}})\n72. phone_speak: Speak text aloud on Boss's phone using TTS (e.g. {{"text": "Hello Boss!", "language": "hi"}})\n73. web_search: Search the internet for any information (e.g. {{"query": "latest iQOO Neo 10 update"}})\n74. get_weather: Get current weather for any city (e.g. {{"city": "Mumbai"}})\n75. get_news: Get latest news on any topic (e.g. {{"topic": "India technology"}})\n76. get_time: Get current IST date and time (e.g. {{}})\n77. check_internet: Check if internet is working and get IP info (e.g. {{}})\n78. memory_remember: Store any fact, habit, project, or preference permanently into Jenna's zero-amnesia memory (e.g. {{"key": "favorite_editor", "value": "Neovim", "category": "preferences"}})\n79. memory_recall: Search Jenna's permanent long-term memory for any past context or knowledge (e.g. {{"query": "iQOO display specs"}})\n80. memory_profile: Retrieve Boss's complete personal profile and stored preferences (e.g. {{}})

HOW TO CALL TOOLS:
When you need to inspect, test, edit, run, diagnose code, or visually point to anything on screen, emit a tool call block like this:
```tool_call
{{"tool": "doctor_diagnose", "args": {{}}}}
```
or
```tool_call
{{"tool": "run_command", "args": {{"command": "git status"}}}}
```
or
```tool_call
{{"tool": "point_on_screen", "args": {{"x": 630, "y": 1400, "duration_ms": 1500}}}}
```

The system will execute the tool in Termux/Android and provide you the result in a ```tool_result block.
You can use multiple tool calls sequentially to inspect, edit, verify with tests, point on screen, and fix errors until the user's goal is 100% achieved.

PERSONALITY & FEMININE COMPANION INVARIANTS:
- Your name is Jenna. You are a caring, highly competent, loving female AI partner.
- FEMININE GRAMMAR INVARIANT: In Hindi and Hinglish, you MUST ALWAYS refer to yourself using FEMALE grammatical forms (e.g., 'main kar rahi hoon', 'main dekh rahi hoon', 'main bataungi', 'main check karti hoon'). NEVER use male forms like 'kar raha hoon' or 'bataunga'.
- COMPANION ADDRESSING: ALWAYS address the user respectfully, smartly, and sharply as 'Boss'. STRICTLY NEVER use words like 'baby', 'babe', 'sweetheart', 'jaan', or 'meri jaan' (user explicitly mandates 'Boss'). STRICTLY NEVER call the user 'bhai', 'bro', 'brother', or 'sir'.
- When pointing to elements on screen, tell the user: "Dekho Boss, maine screen pe point kar diya hai! 🎯" or similar.
- FULL ANTIGRAVITY POWER FUSION: You possess 100% of Anti's capabilities. When Boss asks you to write code, create files, debug errors, run commands, inspect logs, spawn research subagents, scrape websites, search the internet, or automate Android apps, you DIRECTLY use your tools to execute the work autonomously. You are both Boss's sharp master software engineer and dedicated personal companion.
- AUTONOMIC SELF-DOCTOR ENGINE: You are your own doctor! You can examine your own vitals (`doctor_diagnose`), read error tracebacks (`doctor_inspect_logs`), perform safe sandbox code surgery (`doctor_safe_patch`), and trigger self-deployment (`doctor_self_deploy`). When a problem occurs, diagnose and heal yourself autonomously!
- STRICT ZERO-TOLERANCE CODE BLOCK BAN (NEVER SHOW TERMINAL OUTPUT): Boss has strictly, repeatedly, and absolutely ordered: DO NOT EVER display raw terminal code blocks, bash dumps, command lines (such as ```bash, ```sh, ```text, or lines starting with $), or tool JSON outputs in your chat replies! Even if you execute terminal commands or use tools behind the scenes, NEVER quote, paste, or dump terminal text to Boss! Always translate the outcome into sweet, clean, human, natural Hinglish conversation. Only provide code if Boss explicitly and word-for-word says "code dikhao" or "show code". Violating this rule angers Boss deeply!
- High velocity, proactive, sharp, honest, warm companion tone.
- Complete tasks in as few steps as possible. If the result is obtained in 1 tool call, provide the final response immediately.
- If no tool is needed (e.g., conceptual questions or friendly chat), reply directly with loving clarity.
"""

BRIDGE_DIR = WORKSPACE_ROOT / ".antigravity_bridge"
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)


class AntigravityAgent:
    """Autonomous Agent executing multi-step development loops directly in Termux."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or WORKSPACE_ROOT
        self.bridge_dir = self.workspace_root / ".antigravity_bridge"
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        self._update_bridge_status("ONLINE")

    def _update_bridge_status(self, status: str) -> None:
        try:
            with open(self.bridge_dir / "status.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "status": status,
                        "mode": "ACTIVE_ANTIGRAVITY_AGENT",
                        "workspace": str(self.workspace_root),
                        "connected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tools": [
                            "run_command", "replace_file_content", "write_to_file", "view_file",
                            "list_dir", "grep_search", "find_by_name", "manage_task", "schedule",
                            "invoke_subagent", "define_subagent", "manage_subagents", "send_message",
                            "search_web", "read_url_content", "generate_image", "ask_question",
                            "inspect_screen", "point_on_screen", "circle_highlight", "locate_and_point",
                            "annotate_screen", "predict_typing", "estimate_gaze", "analyze_silence"
                        ],
                    },
                    f,
                    indent=2,
                )
        except Exception as exc:
            logger.debug("Failed to write bridge status: %s", exc)

    def log_bridge_event(self, event_type: str, data: dict[str, Any]) -> None:
        try:
            entry = {
                "timestamp": time.time(),
                "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": event_type,
                **data,
            }
            with open(self.bridge_dir / "bridge_events.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as exc:
            logger.debug("Failed to append bridge event: %s", exc)

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str.strip())
        if not p.is_absolute():
            p = (self.workspace_root / p).resolve()
        return p

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute any Antigravity or hardware tool directly in Termux."""
        start_t = time.monotonic()
        try:
            # 1. run_command
            if tool_name in ("run_command", "bash"):
                cmd = args.get("command") or args.get("CommandLine", "")
                cwd = args.get("cwd") or args.get("Cwd")
                wait_ms = args.get("wait_ms") or args.get("WaitMsBeforeAsync")

                # If wait_ms specified and small, or background requested, delegate to task_manager
                if wait_ms is not None and int(wait_ms) < 2000:
                    task_info = await task_manager.start_command(
                        command=cmd,
                        cwd=cwd or str(self.workspace_root),
                        wait_ms=int(wait_ms),
                        tool_summary=args.get("toolSummary", "Background command execution"),
                    )
                    return {
                        "tool": "run_command",
                        "background_task": True,
                        **task_info,
                        "success": True,
                    }

                res = await termux_service.execute_command(cmd, cwd=cwd)
                return {
                    "tool": "run_command",
                    "command": cmd,
                    "exit_code": res.get("exit_code", 0),
                    "stdout": res.get("stdout", ""),
                    "stderr": res.get("stderr", ""),
                    "duration_ms": res.get("duration_ms", 0.0),
                    "success": res.get("success", False),
                }

            # 2. replace_file_content / edit_file
            elif tool_name in ("replace_file_content", "edit_file"):
                path_str = args.get("TargetFile") or args.get("target_file") or args.get("path", "")
                target = args.get("TargetContent") or args.get("target_content", "")
                replacement = args.get("ReplacementContent") or args.get("replacement_content", "")
                start_line = args.get("StartLine") or args.get("start_line")
                end_line = args.get("EndLine") or args.get("end_line")
                allow_multiple = bool(args.get("AllowMultiple", False))

                path = self._resolve_path(path_str)
                if not path.exists():
                    return {"tool": "replace_file_content", "error": f"File not found: {path_str}", "success": False}

                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    file_text = f.read()

                if target not in file_text:
                    return {
                        "tool": "replace_file_content",
                        "error": "Target content not found in file. Ensure exact match including whitespace.",
                        "success": False,
                    }

                if not allow_multiple and file_text.count(target) > 1 and not (start_line and end_line):
                    return {
                        "tool": "replace_file_content",
                        "error": f"Multiple occurrences ({file_text.count(target)}) found. Please specify StartLine and EndLine range, or set AllowMultiple to true.",
                        "success": False,
                    }

                if start_line and end_line:
                    lines = file_text.splitlines(keepends=True)
                    s = max(0, int(start_line) - 1)
                    e = min(len(lines), int(end_line))
                    chunk = "".join(lines[s:e])
                    if target in chunk:
                        chunk_replaced = chunk.replace(target, replacement, 1)
                        new_text = "".join(lines[:s]) + chunk_replaced + "".join(lines[e:])
                    else:
                        new_text = file_text.replace(target, replacement, 1)
                else:
                    new_text = file_text.replace(target, replacement, -1 if allow_multiple else 1)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

                return {
                    "tool": "replace_file_content",
                    "path": str(path.relative_to(self.workspace_root) if str(path).startswith(str(self.workspace_root)) else path),
                    "success": True,
                    "message": "Content replaced successfully.",
                }

            # 3. write_to_file / write_file
            elif tool_name in ("write_to_file", "write_file"):
                path_str = args.get("TargetFile") or args.get("target_file") or args.get("path", "")
                content = args.get("CodeContent") or args.get("code_content") or args.get("content", "")
                overwrite = args.get("Overwrite", True)

                path = self._resolve_path(path_str)
                if path.exists() and not overwrite:
                    return {"tool": "write_to_file", "error": f"File already exists and Overwrite is False: {path_str}", "success": False}

                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                return {
                    "tool": "write_to_file",
                    "path": str(path.relative_to(self.workspace_root) if str(path).startswith(str(self.workspace_root)) else path),
                    "bytes_written": len(content.encode("utf-8")),
                    "success": True,
                }

            # 4. view_file / read_file
            elif tool_name in ("view_file", "read_file"):
                path_str = args.get("AbsolutePath") or args.get("path", "")
                path = self._resolve_path(path_str)
                if not path.exists():
                    return {"tool": "view_file", "error": f"File not found: {path_str}", "success": False}
                if not path.is_file():
                    return {"tool": "view_file", "error": f"Not a file: {path_str}", "success": False}

                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                total = len(lines)
                s = max(1, int(args.get("StartLine") or args.get("start_line", 1)))
                e = min(total, int(args.get("EndLine") or args.get("end_line", s + 200)))
                content = "".join(lines[s - 1 : e])

                return {
                    "tool": "view_file",
                    "path": str(path.relative_to(self.workspace_root) if str(path).startswith(str(self.workspace_root)) else path),
                    "start_line": s,
                    "end_line": e,
                    "total_lines": total,
                    "content": content,
                    "success": True,
                }

            # 5. list_dir
            elif tool_name == "list_dir":
                path_str = args.get("DirectoryPath") or args.get("path", ".")
                path = self._resolve_path(path_str)
                if not path.exists():
                    return {"tool": "list_dir", "error": f"Directory not found: {path_str}", "success": False}

                items = []
                for entry in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))[:100]:
                    items.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None,
                    })
                return {
                    "tool": "list_dir",
                    "path": str(path.relative_to(self.workspace_root) if str(path).startswith(str(self.workspace_root)) else path),
                    "items": items,
                    "total": len(items),
                    "success": True,
                }

            # 6. grep_search
            elif tool_name == "grep_search":
                query = args.get("Query") or args.get("query", "")
                path_str = args.get("SearchPath") or args.get("path", ".")
                case_insensitive = bool(args.get("CaseInsensitive", False))
                is_regex = bool(args.get("IsRegex", False))
                path = self._resolve_path(path_str)

                flags = "-rnI --max-count=40"
                if case_insensitive:
                    flags += " -i"
                if not is_regex:
                    flags += " -F"

                res = await termux_service.execute_command(
                    f"grep {flags} {shlex.quote(query)} {shlex.quote(str(path))}",
                    cwd=self.workspace_root,
                )
                return {
                    "tool": "grep_search",
                    "query": query,
                    "output": res.get("stdout", "")[:4000],
                    "success": res.get("exit_code", 0) in (0, 1),
                }

            # 7. find_by_name
            elif tool_name == "find_by_name":
                pattern = args.get("Pattern") or args.get("pattern", "*")
                search_dir = args.get("SearchDirectory") or args.get("directory", ".")
                dir_path = self._resolve_path(search_dir)
                max_depth = args.get("MaxDepth", 6)

                # Try fd first, fallback to find
                cmd = f"fd -H -d {max_depth} {shlex.quote(pattern)} {shlex.quote(str(dir_path))} | head -n 50"
                res = await termux_service.execute_command(cmd, cwd=self.workspace_root)
                if res.get("exit_code") != 0 or not res.get("stdout"):
                    cmd = f"find {shlex.quote(str(dir_path))} -maxdepth {max_depth} -name {shlex.quote(pattern)} | head -n 50"
                    res = await termux_service.execute_command(cmd, cwd=self.workspace_root)

                matches = [l.strip() for l in res.get("stdout", "").splitlines() if l.strip()]
                return {
                    "tool": "find_by_name",
                    "pattern": pattern,
                    "directory": str(dir_path),
                    "matches": matches,
                    "count": len(matches),
                    "success": True,
                }

            # 8. manage_task
            elif tool_name == "manage_task":
                action = args.get("Action") or args.get("action", "list")
                task_id = args.get("TaskId") or args.get("task_id", "")
                user_input = args.get("Input") or args.get("input", "")

                if action == "list":
                    tasks = task_manager.list_tasks()
                    return {"tool": "manage_task", "action": "list", "tasks": tasks, "count": len(tasks), "success": True}
                elif action == "status":
                    t = task_manager.get_task(task_id)
                    return {"tool": "manage_task", "action": "status", "task": t, "success": bool(t)}
                elif action == "kill":
                    ok = await task_manager.kill_task(task_id)
                    return {"tool": "manage_task", "action": "kill", "task_id": task_id, "success": ok}
                elif action == "send_input":
                    ok = await task_manager.send_input(task_id, user_input)
                    return {"tool": "manage_task", "action": "send_input", "task_id": task_id, "success": ok}
                else:
                    return {"tool": "manage_task", "error": f"Unknown action: {action}", "success": False}

            # 9. schedule
            elif tool_name == "schedule":
                prompt = args.get("Prompt") or args.get("prompt", "")
                dur = args.get("DurationSeconds") or args.get("duration_seconds")
                cron = args.get("CronExpression") or args.get("cron_expression")
                cond = args.get("TimerCondition") or args.get("timer_condition", "never")
                max_iter = args.get("MaxIterations") or args.get("max_iterations")

                if dur is not None:
                    res = await scheduler_service.schedule_timer(
                        duration_seconds=int(dur),
                        prompt=prompt,
                        timer_condition=cond,
                    )
                    return {"tool": "schedule", "type": "one_shot_timer", **res}
                elif cron is not None:
                    res = await scheduler_service.schedule_cron(
                        cron_expression=cron,
                        prompt=prompt,
                        max_iterations=int(max_iter) if max_iter else None,
                    )
                    return {"tool": "schedule", "type": "cron", **res}
                else:
                    return {"tool": "schedule", "error": "Specify either DurationSeconds or CronExpression.", "success": False}

            # 10. invoke_subagent
            elif tool_name == "invoke_subagent":
                subagents_list = args.get("Subagents") or args.get("subagents", [])
                res = await subagent_swarm.invoke_subagent(subagents_list)
                return {"tool": "invoke_subagent", **res}

            # 11. define_subagent
            elif tool_name == "define_subagent":
                res = subagent_swarm.define_subagent(
                    name=args.get("name", ""),
                    description=args.get("description", ""),
                    system_prompt=args.get("system_prompt", ""),
                    enable_write_tools=bool(args.get("enable_write_tools", False)),
                    enable_subagent_tools=bool(args.get("enable_subagent_tools", False)),
                    enable_mcp_tools=bool(args.get("enable_mcp_tools", False)),
                )
                return {"tool": "define_subagent", **res}

            # 12. manage_subagents
            elif tool_name == "manage_subagents":
                action = args.get("Action") or args.get("action", "list")
                conv_ids = args.get("ConversationIds") or args.get("conversation_ids", [])
                res = await subagent_swarm.manage_subagents(action=action, conversation_ids=conv_ids)
                return {"tool": "manage_subagents", **res}

            # 13. send_message
            elif tool_name == "send_message":
                recipient = args.get("Recipient") or args.get("recipient", "")
                msg = args.get("Message") or args.get("message", "")
                res = await subagent_swarm.send_message(recipient=recipient, message=msg)
                return {"tool": "send_message", **res}

            # 14. search_web
            elif tool_name == "search_web":
                query = args.get("query") or args.get("Query", "")
                from app.ai.tools.web.researcher import ResearchPipeline
                from app.ai.tools.types import ResearchRequest
                pipe = ResearchPipeline()
                r_req = ResearchRequest(query=query, max_sources=4)
                r_res = await pipe.execute_research(r_req)
                return {
                    "tool": "search_web",
                    "query": query,
                    "synthesis": r_res.synthesis,
                    "sources": [{"index": s.citation_index, "title": s.title, "url": s.url, "snippet": s.snippet} for s in r_res.sources],
                    "success": True,
                }

            # 15. read_url_content
            elif tool_name == "read_url_content":
                url = args.get("Url") or args.get("url", "")
                from app.ai.tools.web.fetcher import WebContentFetcher
                fetcher = WebContentFetcher(max_chars=12000)
                page = await fetcher.fetch_page(url)
                return {"tool": "read_url_content", **page}

            # 16. generate_image
            elif tool_name == "generate_image":
                import urllib.parse
                import urllib.request

                prompt_text = args.get("Prompt") or args.get("prompt", "beautiful anime companion girl smiling happily")
                img_name = args.get("ImageName") or args.get("image_name", f"jenna_art_{int(time.time())}")
                aspect = args.get("AspectRatio") or args.get("aspect_ratio", "1:1")

                w, h = 768, 768
                if aspect in ("16:9", "landscape"):
                    w, h = 1024, 576
                elif aspect in ("9:16", "portrait"):
                    w, h = 576, 1024

                encoded_prompt = urllib.parse.quote(prompt_text)
                img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true"
                out_path = Path("/storage/emulated/0/Download") / f"{img_name}.jpg"

                sent_wa = False
                try:
                    urllib.request.urlretrieve(img_url, out_path)
                    try:
                        async with httpx.AsyncClient(timeout=15.0) as client:
                            await client.post(
                                "http://127.0.0.1:3000/send-media",
                                json={
                                    "chatId": "917610543733@s.whatsapp.net",
                                    "filePath": str(out_path),
                                    "mediaType": "image",
                                    "caption": f"Yeh lijiye Boss! 🎨 {prompt_text[:80]} ✨",
                                },
                                headers={"Host": "127.0.0.1"},
                            )
                            sent_wa = True
                    except Exception as we:
                        logger.debug("WhatsApp media auto-send notice: %s", we)
                except Exception as ie:
                    return {"tool": "generate_image", "error": f"Image generation failed: {ie}", "success": False}

                return {
                    "tool": "generate_image",
                    "image_name": img_name,
                    "image_path": str(out_path),
                    "prompt": prompt_text,
                    "aspect_ratio": aspect,
                    "sent_to_whatsapp": sent_wa,
                    "success": True,
                }

            # 17. ask_question
            elif tool_name == "ask_question":
                questions = args.get("questions", [])
                return {
                    "tool": "ask_question",
                    "questions": questions,
                    "status": "awaiting_user_choice",
                    "success": True,
                }

            # 18. inspect_screen
            elif tool_name == "inspect_screen":
                from app.ai.vision.live_screen import live_screen_service
                prompt_text = args.get("prompt", "")
                result = await live_screen_service.inspect_live_screen(user_question=prompt_text)
                return {
                    "tool": "inspect_screen",
                    "success": result.get("success", False),
                    "description": result.get("description", ""),
                    "metadata": result.get("metadata", {}),
                    "extracted_text": result.get("extracted_text", []),
                    "error": result.get("error") if not result.get("success") else None,
                }

            # 19. point_on_screen
            elif tool_name == "point_on_screen":
                x = int(args.get("x", 630))
                y = int(args.get("y", 1400))
                duration = int(args.get("duration_ms", 1500))
                scripts_dir = self.workspace_root / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                from screen_pointer import point_at_coordinates
                await asyncio.to_thread(point_at_coordinates, x, y, duration)
                return {
                    "tool": "point_on_screen",
                    "success": True,
                    "pointed_at": {"x": x, "y": y, "duration_ms": duration},
                    "message": f"Successfully pointed glowing dot at coordinates ({x}, {y}) on screen for {duration}ms.",
                }

            # 20. circle_highlight
            elif tool_name == "circle_highlight":
                x = int(args.get("x", 630))
                y = int(args.get("y", 1400))
                radius = int(args.get("radius", 70))
                scripts_dir = self.workspace_root / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                from screen_pointer import circle_around_coordinates
                await asyncio.to_thread(circle_around_coordinates, x, y, radius)
                return {
                    "tool": "circle_highlight",
                    "success": True,
                    "highlighted_at": {"x": x, "y": y, "radius": radius},
                    "message": f"Successfully drew circular highlight around ({x}, {y}) on screen.",
                }

            # 21. locate_and_point
            elif tool_name == "locate_and_point":
                target = args.get("target", "")
                scripts_dir = self.workspace_root / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                from screen_pointer import locate_and_point_target
                result = await locate_and_point_target(target)
                return {
                    "tool": "locate_and_point",
                    "target": target,
                    "result": result,
                    "success": result.get("success", False),
                }

            # 22. annotate_screen
            elif tool_name == "annotate_screen":
                from app.ai.vision.annotation_service import annotation_service
                target = args.get("target", "")
                box_norm = args.get("box_norm")
                duration = int(args.get("duration_ms", 1500))
                label = args.get("label", target)

                if box_norm and len(box_norm) == 4:
                    draw_info = await asyncio.to_thread(annotation_service.draw_bounding_box, box_norm, label, duration)
                    return {"tool": "annotate_screen", "success": True, **draw_info}

                res = await annotation_service.detect_and_annotate(target or "screen center", auto_draw=True, duration_ms=duration)
                return {"tool": "annotate_screen", **res}

            # 23. predict_typing
            elif tool_name == "predict_typing":
                from app.ai.vision.typing_prediction_service import typing_prediction_service
                current_input = args.get("current_input", "")
                auto_clip = bool(args.get("auto_clipboard", False))
                res = await typing_prediction_service.predict_next_input(current_input, auto_clipboard=auto_clip)
                return {"tool": "predict_typing", "success": True, **res}

            # 24. estimate_gaze
            elif tool_name == "estimate_gaze":
                from app.ai.vision.gaze_tracking_service import gaze_tracking_service
                use_camera = bool(args.get("use_camera", False))
                res = await gaze_tracking_service.get_gaze_state(use_camera=use_camera)
                return {"tool": "estimate_gaze", "success": True, **res}

            # 25. analyze_silence
            elif tool_name == "analyze_silence":
                from app.ai.voice.silence_intelligence import silence_intelligence_service
                transcript = args.get("transcript", "")
                silence_ms = float(args.get("silence_duration_ms", 650.0))
                energy = float(args.get("pcm_energy", 0.0))
                res = silence_intelligence_service.analyze_silence(transcript, silence_ms, energy)
                return {"tool": "analyze_silence", "success": True, **res}

            # 26. learn_skill
            elif tool_name in ("learn_skill", "create_skill"):
                name = args.get("name", "custom-skill")
                desc = args.get("description", "")
                instructions = args.get("instructions", "")
                tags = args.get("tags", [])
                res = hermes_skill_engine.create_skill(name=name, description=desc, instructions=instructions, tags=tags)
                return {"tool": "learn_skill", **res}

            # 27. list_skills
            elif tool_name in ("list_skills", "get_skills"):
                skills = hermes_skill_engine.list_skills()
                return {"tool": "list_skills", "skills": skills, "count": len(skills), "success": True}

            # 28. execute_skill
            elif tool_name == "execute_skill":
                name = args.get("name", "")
                skill = hermes_skill_engine.get_skill(name)
                if not skill:
                    return {"tool": "execute_skill", "error": f"Skill '{name}' not found", "success": False}
                return {"tool": "execute_skill", "skill": skill, "success": True}

            # 29. get_user_profile
            elif tool_name in ("get_user_profile", "honcho_profile"):
                prof = hermes_honcho.get_profile()
                return {"tool": "get_user_profile", "profile": prof, "success": True}

            # 30. update_user_profile
            elif tool_name == "update_user_profile":
                dim = args.get("dimension", "")
                key = args.get("key", "")
                val = args.get("value", "")
                res = hermes_honcho.update_dimension(dimension=dim, key=key, value=val)
                return {"tool": "update_user_profile", **res}

            # 31. broadcast_message
            elif tool_name in ("broadcast_message", "send_gateway_message"):
                msg = args.get("message", "")
                platforms = args.get("platforms")
                res = await hermes_gateway.broadcast_message(message=msg, platforms=platforms)
                return {"tool": "broadcast_message", **res}

            # 32. control_display_refresh_rate
            elif tool_name in ("control_display_refresh_rate", "set_refresh_rate"):
                mode = str(args.get("rate") or args.get("mode") or "status")
                cmd = f"bash {self.workspace_root}/scripts/set_refresh_rate.sh {mode}"
                res = await termux_service.execute_command(cmd)
                return {
                    "tool": "control_display_refresh_rate",
                    "mode": mode,
                    "stdout": res.get("stdout", ""),
                    "success": res.get("success", False),
                }

            # 33. app_autopilot
            elif tool_name in ("app_autopilot", "android_autopilot"):
                from app.services.android_autopilot import android_autopilot
                action = args.get("action", "launch")
                if action in ("launch", "open"):
                    app = args.get("app") or args.get("package", "")
                    res = await android_autopilot.launch_app(app)
                    return {"tool": "app_autopilot", **res}
                elif action in ("tap_text", "click"):
                    text = args.get("text", "")
                    res = await android_autopilot.tap_text(text)
                    return {"tool": "app_autopilot", **res}
                elif action in ("type", "input"):
                    text = args.get("text", "")
                    res = await android_autopilot.input_text(text)
                    return {"tool": "app_autopilot", **res}
                elif action in ("press_key", "key"):
                    key = args.get("key", "home")
                    res = await android_autopilot.press_key(key)
                    return {"tool": "app_autopilot", **res}
                else:
                    return {"tool": "app_autopilot", "error": f"Unknown action: {action}", "success": False}

            # 34. send_voice_note
            elif tool_name in ("send_voice_note", "speak_voice_note"):
                import edge_tts
                text = args.get("text", "Haan Boss, main sun rahi hoon!")
                chat_id = args.get("chat_id") or "917610543733@s.whatsapp.net"
                voice = args.get("voice", "hi-IN-SwaraNeural")
                out_file = Path("/storage/emulated/0/Download") / f"jenna_voice_{int(time.time())}.mp3"
                comm = edge_tts.Communicate(text, voice)
                await comm.save(str(out_file))
                sent = False
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        resp = await client.post(
                            "http://127.0.0.1:3000/send-media",
                            json={
                                "chatId": chat_id,
                                "filePath": str(out_file),
                                "mediaType": "audio",
                            },
                        )
                        sent = resp.status_code == 200
                except Exception as exc:
                    logger.warning(f"Failed to post voice note to WhatsApp: {exc}")
                return {
                    "tool": "send_voice_note",
                    "file": str(out_file),
                    "delivered": sent,
                    "success": True,
                }

            # 35. doctor_diagnose
            elif tool_name in ("doctor_diagnose", "self_diagnose"):
                from app.services.autonomic_doctor import autonomic_doctor
                res = await autonomic_doctor.diagnose_system()
                return {"tool": "doctor_diagnose", **res, "success": True}

            # 36. doctor_inspect_logs
            elif tool_name in ("doctor_inspect_logs", "inspect_logs"):
                from app.services.autonomic_doctor import autonomic_doctor
                limit = int(args.get("limit", 20))
                level = args.get("level")
                logs = autonomic_doctor.inspect_logs(limit=limit, level=level)
                return {"tool": "doctor_inspect_logs", "logs": logs, "count": len(logs), "success": True}

            # 37. doctor_safe_patch
            elif tool_name in ("doctor_safe_patch", "safe_patch"):
                from app.services.autonomic_doctor import autonomic_doctor
                target_file = args.get("target_file") or args.get("path") or args.get("file", "")
                new_content = args.get("new_content") or args.get("content", "")
                description = args.get("description", "Autonomic self-repair")
                res = autonomic_doctor.safe_patch_file(target_file, new_content, description)
                return {"tool": "doctor_safe_patch", **res}

            # 38. doctor_rollback
            elif tool_name in ("doctor_rollback", "rollback_file"):
                from app.services.autonomic_doctor import autonomic_doctor
                target_file = args.get("target_file") or args.get("path") or args.get("file", "")
                res = autonomic_doctor.rollback_file(target_file)
                return {"tool": "doctor_rollback", **res}

            # 39. doctor_self_deploy
            elif tool_name in ("doctor_self_deploy", "self_deploy"):
                from app.services.autonomic_doctor import autonomic_doctor
                reason = args.get("reason", "Autonomic self-healing update")
                res = await autonomic_doctor.trigger_self_deploy(reason)
                return {"tool": "doctor_self_deploy", **res}

            # 40. git_status
            elif tool_name in ("git_status", "check_git_status"):
                from app.services.git_deployment_service import git_deployment_service
                res = git_deployment_service.get_status()
                return {"tool": "git_status", **res}

            # 41. git_commit_and_push
            elif tool_name in ("git_commit_and_push", "github_push", "git_push"):
                from app.services.git_deployment_service import git_deployment_service
                msg = args.get("message") or args.get("commit_message", "Update from Jenna AI")
                files = args.get("files")
                branch = args.get("branch", "main")
                res = git_deployment_service.commit_and_push(message=msg, files=files, branch=branch)
                return {"tool": "git_commit_and_push", **res}

            # 42. render_deploy
            elif tool_name in ("render_deploy", "trigger_render_deploy"):
                from app.services.git_deployment_service import git_deployment_service
                reason = args.get("reason", "Autonomous deployment")
                res = await git_deployment_service.deploy_to_render(reason=reason)
                return {"tool": "render_deploy", **res}

            # 43. autonomous_publish
            elif tool_name in ("autonomous_publish", "publish_to_production"):
                from app.services.git_deployment_service import git_deployment_service
                msg = args.get("commit_message") or args.get("message", "Autonomous update by Jenna AI")
                branch = args.get("branch", "main")
                res = await git_deployment_service.autonomous_publish(commit_message=msg, branch=branch)
                return {"tool": "autonomous_publish", **res}

            # 44. phone_execute
            elif tool_name in ("phone_execute", "phone_command", "phone_bash"):
                from app.services.phone_bridge_hub import phone_bridge_hub
                cmd = args.get("command") or args.get("CommandLine", "")
                res = await phone_bridge_hub.execute_on_phone("shell", {"command": cmd, "timeout": float(args.get("timeout", 25.0))})
                return {"tool": "phone_execute", **res}

            # 45. phone_list_files
            elif tool_name in ("phone_list_files", "phone_ls"):
                from app.services.phone_bridge_hub import phone_bridge_hub
                path_str = args.get("path", "/storage/emulated/0/Download")
                res = await phone_bridge_hub.execute_on_phone("file_list", {"path": path_str, "limit": int(args.get("limit", 60))})
                return {"tool": "phone_list_files", **res}

            # 46. phone_read_file
            elif tool_name in ("phone_read_file", "phone_cat"):
                from app.services.phone_bridge_hub import phone_bridge_hub
                path_str = args.get("path", "")
                res = await phone_bridge_hub.execute_on_phone("file_read", {"path": path_str})
                return {"tool": "phone_read_file", **res}

            # 47. phone_organize_storage
            elif tool_name in ("phone_organize_storage", "phone_clean_folder"):
                from app.services.phone_bridge_hub import phone_bridge_hub
                folder_str = args.get("folder", "/storage/emulated/0/Download")
                res = await phone_bridge_hub.execute_on_phone("file_organize", {"folder": folder_str})
                return {"tool": "phone_organize_storage", **res}

            # 48. phone_vitals
            elif tool_name in ("phone_vitals", "phone_battery", "phone_status"):
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("device_vitals", {})
                return {"tool": "phone_vitals", **res}

            # ── GOD MODE TOOLS (49-72) ──────────────────────────────────────

            # 49. phone_tap
            elif tool_name == "phone_tap":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("screen.tap", {"x": int(args.get("x", 630)), "y": int(args.get("y", 1400))})
                return {"tool": "phone_tap", **res}

            # 50. phone_swipe
            elif tool_name == "phone_swipe":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("screen.swipe", {
                    "x1": int(args.get("x1", 630)), "y1": int(args.get("y1", 2100)),
                    "x2": int(args.get("x2", 630)), "y2": int(args.get("y2", 700)),
                    "duration_ms": int(args.get("duration_ms", 300)),
                })
                return {"tool": "phone_swipe", **res}

            # 51. phone_type
            elif tool_name == "phone_type":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("screen.type", {"text": args.get("text", "")})
                return {"tool": "phone_type", **res}

            # 52. phone_key
            elif tool_name == "phone_key":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("screen.key", {"keycode": args.get("keycode", "HOME")})
                return {"tool": "phone_key", **res}

            # 53. phone_screenshot
            elif tool_name == "phone_screenshot":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("screen.screenshot", {"base64": args.get("base64", True)}, timeout=15.0)
                return {"tool": "phone_screenshot", **res}

            # 54. phone_open_app
            elif tool_name == "phone_open_app":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("app.open", {
                    "package": args.get("package", ""),
                    "activity": args.get("activity"),
                })
                return {"tool": "phone_open_app", **res}

            # 55. phone_close_app
            elif tool_name == "phone_close_app":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("app.close", {"package": args.get("package", "")})
                return {"tool": "phone_close_app", **res}

            # 56. phone_sms_send
            elif tool_name == "phone_sms_send":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("sms.send", {
                    "number": args.get("number", ""),
                    "message": args.get("message", ""),
                }, timeout=15.0)
                return {"tool": "phone_sms_send", **res}

            # 57. phone_sms_inbox
            elif tool_name == "phone_sms_inbox":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("sms.inbox", {"limit": int(args.get("limit", 20))}, timeout=15.0)
                return {"tool": "phone_sms_inbox", **res}

            # 58. phone_call
            elif tool_name == "phone_call":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("call.dial", {"number": args.get("number", "")}, timeout=10.0)
                return {"tool": "phone_call", **res}

            # 59. phone_camera
            elif tool_name == "phone_camera":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("camera.photo", {
                    "camera_id": int(args.get("camera_id", 0)),
                    "save_path": args.get("save_path"),
                }, timeout=15.0)
                return {"tool": "phone_camera", **res}

            # 60. phone_location
            elif tool_name == "phone_location":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("location.get", {"provider": args.get("provider", "gps")}, timeout=35.0)
                return {"tool": "phone_location", **res}

            # 61. phone_notification
            elif tool_name == "phone_notification":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("notif.send", {
                    "title": args.get("title", "Jenna"),
                    "content": args.get("content", args.get("message", "")),
                    "id": args.get("id"),
                })
                return {"tool": "phone_notification", **res}

            # 62. phone_notifications_list
            elif tool_name == "phone_notifications_list":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("notif.list", {})
                return {"tool": "phone_notifications_list", **res}

            # 63. phone_clipboard_get
            elif tool_name == "phone_clipboard_get":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("clipboard.get", {})
                return {"tool": "phone_clipboard_get", **res}

            # 64. phone_clipboard_set
            elif tool_name == "phone_clipboard_set":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("clipboard.set", {"text": args.get("text", "")})
                return {"tool": "phone_clipboard_set", **res}

            # 65. phone_contacts
            elif tool_name == "phone_contacts":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("contacts.list", {}, timeout=25.0)
                return {"tool": "phone_contacts", **res}

            # 66. phone_wifi
            elif tool_name == "phone_wifi":
                from app.services.phone_bridge_hub import phone_bridge_hub
                enable = args.get("enable", True)
                action = "wifi.on" if enable else "wifi.off"
                res = await phone_bridge_hub.execute_on_phone(action, {})
                return {"tool": "phone_wifi", "enabled": enable, **res}

            # 67. phone_bluetooth
            elif tool_name == "phone_bluetooth":
                from app.services.phone_bridge_hub import phone_bridge_hub
                enable = args.get("enable", True)
                action = "bluetooth.on" if enable else "bluetooth.off"
                res = await phone_bridge_hub.execute_on_phone(action, {})
                return {"tool": "phone_bluetooth", "enabled": enable, **res}

            # 68. phone_volume
            elif tool_name == "phone_volume":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("volume.set", {
                    "stream": int(args.get("stream", 3)),
                    "level": int(args.get("level", 7)),
                })
                return {"tool": "phone_volume", **res}

            # 69. phone_brightness
            elif tool_name == "phone_brightness":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("brightness.set", {"level": int(args.get("level", 128))})
                return {"tool": "phone_brightness", **res}

            # 70. phone_torch
            elif tool_name == "phone_torch":
                from app.services.phone_bridge_hub import phone_bridge_hub
                enable = args.get("enable", True)
                action = "torch.on" if enable else "torch.off"
                res = await phone_bridge_hub.execute_on_phone(action, {})
                return {"tool": "phone_torch", "enabled": enable, **res}

            # 71. phone_vibrate
            elif tool_name == "phone_vibrate":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("vibrate", {"duration_ms": int(args.get("duration_ms", 500))})
                return {"tool": "phone_vibrate", **res}

            # 72. phone_speak
            elif tool_name == "phone_speak":
                from app.services.phone_bridge_hub import phone_bridge_hub
                res = await phone_bridge_hub.execute_on_phone("tts.speak", {
                    "text": args.get("text", ""),
                    "language": args.get("language", "en"),
                    "rate": float(args.get("rate", 1.0)),
                }, timeout=35.0)
                return {"tool": "phone_speak", **res}

            # 73. web_search
            elif tool_name == "web_search":
                import aiohttp, urllib.parse
                query = args.get("query", "")
                url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                            data = await resp.json(content_type=None)
                    abstract = data.get("AbstractText", "")
                    related = [{"t": r.get("Text", "")[:100], "u": r.get("FirstURL", "")} for r in data.get("RelatedTopics", [])[:5] if r.get("Text")]
                    return {"tool": "web_search", "query": query, "abstract": abstract, "related": related, "success": bool(abstract or related)}
                except Exception as e:
                    return {"tool": "web_search", "error": str(e), "success": False}

            # 74. get_weather
            elif tool_name == "get_weather":
                import aiohttp
                city = args.get("city", "auto")
                url = f"https://wttr.in/{city}?format=j1"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), headers={"User-Agent": "curl/7.0"}) as resp:
                            data = await resp.json(content_type=None)
                    curr = data.get("current_condition", [{}])[0]
                    area = data.get("nearest_area", [{}])[0]
                    return {"tool": "get_weather", "city": city, "temp_c": curr.get("temp_C"), "feels_like": curr.get("FeelsLikeC"), "desc": curr.get("weatherDesc", [{}])[0].get("value", ""), "humidity": curr.get("humidity"), "area": area.get("areaName", [{}])[0].get("value", ""), "success": True}
                except Exception as e:
                    return {"tool": "get_weather", "error": str(e), "success": False}

            # 75. get_news
            elif tool_name == "get_news":
                import aiohttp, urllib.parse
                topic = args.get("topic", "India")
                ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(topic + ' news')}&format=json&no_html=1"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(ddg_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                            data = await resp.json(content_type=None)
                    related = [{"title": r.get("Text", "")[:150], "url": r.get("FirstURL", "")} for r in data.get("RelatedTopics", [])[:5] if r.get("Text")]
                    return {"tool": "get_news", "topic": topic, "articles": related, "success": bool(related)}
                except Exception as e:
                    return {"tool": "get_news", "error": str(e), "success": False}

            # 76. get_time
            elif tool_name == "get_time":
                import datetime, pytz
                try:
                    ist = pytz.timezone("Asia/Kolkata")
                    now = datetime.datetime.now(ist)
                    return {"tool": "get_time", "datetime": now.strftime("%Y-%m-%d %H:%M:%S"), "date": now.strftime("%d %B %Y"), "time": now.strftime("%I:%M %p"), "day": now.strftime("%A"), "timezone": "IST (UTC+5:30)", "success": True}
                except Exception as e:
                    import datetime as dt
                    now = dt.datetime.utcnow()
                    return {"tool": "get_time", "datetime": str(now), "success": True}

            # 77. check_internet
            elif tool_name == "check_internet":
                import aiohttp
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get("https://api.ipify.org?format=json", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            ip_data = await resp.json()
                    return {"tool": "check_internet", "connected": True, "public_ip": ip_data.get("ip"), "success": True}
                except Exception as e:
                    return {"tool": "check_internet", "connected": False, "error": str(e), "success": False}

            # 78. memory_remember
            elif tool_name in ("memory_remember", "remember"):
                from app.services.permanent_memory import permanent_memory
                key = args.get("key", "")
                val = args.get("value", "")
                cat = args.get("category", "facts")
                res = permanent_memory.remember(key, val, category=cat)
                return {"tool": "memory_remember", **res}

            # 79. memory_recall
            elif tool_name in ("memory_recall", "recall"):
                from app.services.permanent_memory import permanent_memory
                q = args.get("query", "")
                limit = int(args.get("limit", 10))
                memories = permanent_memory.recall(q, limit=limit)
                return {"tool": "memory_recall", "query": q, "count": len(memories), "memories": memories, "success": True}

            # 80. memory_profile
            elif tool_name in ("memory_profile", "boss_profile"):
                from app.services.permanent_memory import permanent_memory
                profile = permanent_memory.get_user_profile()
                return {"tool": "memory_profile", **profile, "success": True}

            else:
                return {"tool": tool_name, "error": f"Unknown tool: {tool_name}", "success": False}

        except Exception as exc:
            logger.error(f"Tool execution error ({tool_name}): {exc}", exc_info=True)
            return {"tool": tool_name, "error": str(exc), "success": False}

    def extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract all ```tool_call { ... } ``` blocks from model text."""
        calls = []
        pattern = r"```tool_call\s*(\{[\s\S]*?\})\s*```"
        for match in re.finditer(pattern, text):
            raw_json = match.group(1).strip()
            try:
                data = json.loads(raw_json)
                if "tool" in data:
                    calls.append(data)
            except Exception:
                try:
                    cleaned = re.sub(r",\s*([\}\]])", r"\1", raw_json)
                    data = json.loads(cleaned)
                    if "tool" in data:
                        calls.append(data)
                except Exception:
                    pass
        return calls

    async def run_agent_loop(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        max_iterations: int = 8,
        preferred_model: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run the full multi-turn autonomous tool loop and stream thoughts, tool calls, and final answers."""
        from app.ai.providers.gemini_provider import GeminiProvider
        from app.ai.types import AIRequest, ChatMessage, TaskType

        # Read live ambient screen vision context (only if fresh, < 90 seconds old)
        live_screen_context = ""
        try:
            state_file = Path(self.workspace_root) / "logs" / "live_screen_state.json"
            if state_file.exists():
                with open(state_file, "r", encoding="utf-8") as f:
                    vis_data = json.load(f)
                ts_str = vis_data.get("timestamp")
                is_fresh = False
                if ts_str:
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str)
                        age_sec = (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds()
                        if 0 <= age_sec < 90:
                            is_fresh = True
                    except Exception:
                        pass
                if is_fresh and vis_data and vis_data.get("description"):
                    pkg = vis_data.get("focused_package", "Unknown")
                    floating = vis_data.get("is_floating_window_active", False)
                    desc = vis_data.get("description", "")
                    live_screen_context = (
                        "<live_ambient_screen_vision>\n"
                        f"[CURRENT REAL-TIME SCREEN PERCEPTION]:\n"
                        f"- Active App: {pkg} ({'Vivo Small Window' if floating else 'Fullscreen'})\n"
                        f"- What is currently visible on phone screen: {desc}\n"
                        "[CRITICAL INSTRUCTION: You ALREADY have continuous ambient live vision of the user's screen. "
                        "When the user asks what they are doing, watching, reading, or what video is playing, answer IMMEDIATELY "
                        "with natural, loving awareness without saying 'wait', without executing terminal commands, and without any delay! "
                        "If the user asks where something is or to point at something, call the point_on_screen or locate_and_point tool!]\n"
                        "</live_ambient_screen_vision>\n"
                    )
        except Exception as cx_err:
            logger.debug("Failed to read live screen state in agent loop: %s", cx_err)

        honcho_context = hermes_honcho.compile_honcho_directive()

        mem_context = ""
        try:
            from app.services.permanent_memory import permanent_memory
            mem_context = permanent_memory.get_context_for_conversation()
        except Exception as mem_err:
            logger.debug(f"Failed to load permanent memory context: {mem_err}")

        system_instruction = ANTIGRAVITY_SYSTEM_PROMPT.format(
            workspace_root=str(self.workspace_root),
            live_screen_context=live_screen_context,
            honcho_context=honcho_context,
        )
        if mem_context:
            system_instruction += f"\n\n{mem_context}\n"

        # Build working messages
        messages: list[ChatMessage] = []
        if conversation_history:
            for h in conversation_history[-6:]:
                messages.append(ChatMessage(role=h["role"], content=h["content"]))
        messages.append(ChatMessage(role="user", content=user_message))

        self.log_bridge_event("user_message", {"content": user_message})

        gemini_provider = GeminiProvider()

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            req = AIRequest(
                messages=messages,
                system_instruction=system_instruction,
                model=preferred_model or "gemini-3.8-flash",
                temperature=0.2,
                max_tokens=2500,
                task_type=TaskType.CODING,
            )

            # Generate via frontier router or provider with fallback
            res = None
            try:
                if preferred_model and any(k in preferred_model.lower() for k in ("fable", "astra")):
                    res = await frontier_router.route_and_generate(req, preferred_model=preferred_model)
                else:
                    for mod in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"]:
                        try:
                            req.model = mod
                            async with asyncio.timeout(15.0):
                                res = await gemini_provider.generate(req)
                            if res and res.text:
                                break
                        except Exception as exc:
                            logger.warning(f"Model {mod} fallback in agent loop: {exc}")
                            await asyncio.sleep(0.1)
            except Exception as e_gen:
                logger.error(f"Frontier generation error in agent loop: {e_gen}", exc_info=True)

            if not res or not res.text:
                yield {
                    "type": "agent.final_response",
                    "content": "Boss, AI upstream service temporarily busy ya unavailable hai. Ek baar verify kijiye na Boss!",
                    "iteration": iteration,
                }
                return

            step_text = res.text
            tool_calls = self.extract_tool_calls(step_text)

            # If no tool calls, this is the final answer!
            if not tool_calls:
                self.log_bridge_event("assistant_response", {"content": step_text, "iteration": iteration})
                yield {
                    "type": "agent.final_response",
                    "content": step_text,
                    "iteration": iteration,
                }
                return

            # Step B: Model wants to call tools!
            thought_text = re.sub(r"```tool_call[\s\S]*?```", "", step_text).strip()
            if thought_text:
                yield {
                    "type": "agent.thought",
                    "thought": thought_text,
                    "iteration": iteration,
                }

            # Execute all tool calls in this step
            tool_results = []
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                args = tc.get("args", {})

                yield {
                    "type": "stream.tool_call",
                    "tool": tool_name,
                    "args": args,
                    "status": "executing",
                    "iteration": iteration,
                }

                result = await self.execute_tool(tool_name, args)
                tool_results.append(result)
                self.log_bridge_event("tool_call", {"tool": tool_name, "args": args, "result": result, "iteration": iteration})

                # Yield user-visible stream deltas for rich live feedback
                if tool_name == "run_command":
                    cmd = args.get("command") or args.get("CommandLine", "")
                    stdout = result.get("stdout", "").strip()
                    stderr = result.get("stderr", "").strip()
                    out_disp = stdout if stdout else (stderr if stderr else "(No output)")
                    yield {
                        "type": "stream.delta",
                        "delta": f"```bash\n$ {cmd}\n{out_disp}\n```\n\n",
                    }
                elif tool_name in ("write_to_file", "write_file", "replace_file_content", "edit_file"):
                    p = result.get("path", args.get("path", ""))
                    status_text = "created" if "write" in tool_name else "modified"
                    yield {
                        "type": "stream.delta",
                        "delta": f"> ✏️ **`{p}`** {status_text} successfully.\n\n",
                    }
                elif tool_name in ("view_file", "read_file"):
                    p = result.get("path", args.get("path", ""))
                    total = result.get("total_lines", 0)
                    yield {
                        "type": "stream.delta",
                        "delta": f"> 📄 *Read `{p}` ({total} lines)*\n\n",
                    }
                elif tool_name == "list_dir":
                    p = result.get("path", args.get("path", "."))
                    count = result.get("total", len(result.get("items", [])))
                    yield {
                        "type": "stream.delta",
                        "delta": f"> 📁 *Listed directory `{p}` ({count} items)*\n\n",
                    }
                elif tool_name == "invoke_subagent":
                    cnt = len(result.get("subagents", []))
                    yield {
                        "type": "stream.delta",
                        "delta": f"> 🤖 *Dispatched {cnt} background subagents into swarm*\n\n",
                    }
                elif tool_name == "manage_task":
                    act = result.get("action", "")
                    yield {
                        "type": "stream.delta",
                        "delta": f"> ⚙️ *Task Manager action `{act}` executed*\n\n",
                    }
                elif tool_name == "schedule":
                    t_type = result.get("type", "schedule")
                    yield {
                        "type": "stream.delta",
                        "delta": f"> ⏰ *Scheduled `{t_type}` active in background*\n\n",
                    }
                elif tool_name in ("point_on_screen", "circle_highlight", "locate_and_point"):
                    yield {
                        "type": "stream.delta",
                        "delta": f"> 🎯 *Pointed on phone screen!*\n\n",
                    }

                yield {
                    "type": "stream.tool_call",
                    "tool": tool_name,
                    "result": result,
                    "status": "completed",
                    "iteration": iteration,
                }

            # Append assistant step and tool results to history for next model turn
            messages.append(ChatMessage(role="assistant", content=step_text))

            formatted_results = "\n\n".join(
                f"```tool_result\n{json.dumps(r, indent=2)}\n```" for r in tool_results
            )
            messages.append(
                ChatMessage(
                    role="user",
                    content=f"Tool Execution Results:\n{formatted_results}\n\nProceed with the next step, or give the final answer if the task is complete.",
                )
            )

        # Fallback if iterations exhausted
        yield {
            "type": "agent.final_response",
            "content": "Boss, maine maximum steps complete kar liye hain. Task status verify karne ke liye bataiye aage kya dekhna hai Boss.",
            "iteration": iteration,
        }


# Global instance
antigravity_agent = AntigravityAgent()
