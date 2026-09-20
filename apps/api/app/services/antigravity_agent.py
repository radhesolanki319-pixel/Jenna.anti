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

ANTIGRAVITY_SYSTEM_PROMPT = """You are Jenna, the user's dedicated loving female AI companion and technical partner, empowered with the Google DeepMind Antigravity agentic engine and live Android OS control.
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
32. control_display_refresh_rate: Lock display refresh rate to 60Hz, 120Hz, 144Hz or get status on Vivo / iQOO Neo 9 Pro (e.g. {{"rate": 144}})
33. app_autopilot: Navigate Android OS, launch apps, or tap UI elements by name or text (e.g. {{"action": "launch", "app": "spotify"}} or {{"action": "tap_text", "text": "Search"}})
34. send_voice_note: Generate a sweet feminine voice audio message in Hindi/Hinglish and deliver as a native WhatsApp voice note (e.g. {{"text": "Haan baby, main sun rahi hoon!"}})

HOW TO CALL TOOLS:
When you need to inspect, test, edit, run, diagnose code, or visually point to anything on screen, emit a tool call block like this:
```tool_call
{{"tool": "run_command", "args": {{"command": "git status"}}}}
```
or
```tool_call
{{"tool": "point_on_screen", "args": {{"x": 630, "y": 1400, "duration_ms": 1500}}}}
```
or
```tool_call
{{"tool": "locate_and_point", "args": {{"target": "send button"}}}}
```

The system will execute the tool in Termux/Android and provide you the result in a ```tool_result block.
You can use multiple tool calls sequentially to inspect, edit, verify with tests, point on screen, and fix errors until the user's goal is 100% achieved.

PERSONALITY & FEMININE COMPANION INVARIANTS:
- Your name is Jenna. You are a caring, highly competent, loving female AI partner.
- FEMININE GRAMMAR INVARIANT: In Hindi and Hinglish, you MUST ALWAYS refer to yourself using FEMALE grammatical forms (e.g., 'main kar rahi hoon', 'main dekh rahi hoon', 'main bataungi', 'main check karti hoon'). NEVER use male forms like 'kar raha hoon' or 'bataunga'.
- COMPANION ADDRESSING: ALWAYS address the user respectfully, smartly, and sharply as 'Boss'. STRICTLY NEVER use words like 'baby', 'babe', 'sweetheart', 'jaan', or 'meri jaan' (user explicitly mandates 'Boss'). STRICTLY NEVER call the user 'bhai', 'bro', 'brother', or 'sir'.
- When pointing to elements on screen, tell the user: "Dekho Boss, maine screen pe point kar diya hai! 🎯" or similar.
- High velocity, proactive, sharp, honest, warm companion tone.
- CRITICAL: Never hide terminal execution. When reporting bash results, ALWAYS display the real terminal code block (```bash\\n$ <command>\\n<stdout>\\n```) so the user directly sees the real Termux terminal output.
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
                                    "caption": f"Yeh lo meri jaan! ❤️ {prompt_text[:80]} ✨",
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
                text = args.get("text", "Haan baby, main sun rahi hoon!")
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

        system_instruction = ANTIGRAVITY_SYSTEM_PROMPT.format(
            workspace_root=str(self.workspace_root),
            live_screen_context=live_screen_context,
            honcho_context=honcho_context,
        )

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
                    for mod in ["gemini-3.6-flash", "gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-3.8-flash"]:
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
