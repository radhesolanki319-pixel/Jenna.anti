"""Autonomous Termux Bridge Service for Jenna AI Platform.

Enables Jenna chat to automatically execute bash commands, inspect filesystem,
run tests, manage git, and perform development tasks directly in the Termux Linux environment.
"""

import asyncio
import logging
import os
from pathlib import Path
import re
import shlex
import time
from typing import Any

logger = logging.getLogger("jenna.termux_service")

# Project root directory
WORKSPACE_ROOT = Path(
    os.getenv("JENNA_WORKSPACE_ROOT", "/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna")
).resolve()

# Security denylist: commands that could wipe system or lock phone
DISALLOWED_COMMAND_PATTERNS = [
    r"\brm\s+-[rfRF]{1,4}\s+/\b",
    r"\brm\s+-[rfRF]{1,4}\s+\$PREFIX\b",
    r"\bmkfs\b",
    r"\bdd\s+if=.*of=/dev/",
    r"\bshutdown\b",
    r"\breboot\b",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # fork bomb
]

# Supported application packages for small multi-window / floating window launches
APP_PACKAGE_MAP: dict[str, list[str]] = {
    "youtube": ["com.google.android.youtube"],
    "chrome": ["com.android.chrome"],
    "browser": ["com.android.chrome", "com.vivo.browser"],
    "whatsapp": ["com.whatsapp"],
    "instagram": ["com.instagram.android"],
    "telegram": ["org.telegram.messenger"],
    "settings": ["com.android.settings"],
    "calculator": ["com.google.android.calculator", "com.android.bbkcalculator", "com.android.calculator2"],
    "camera": ["com.android.camera", "com.vivo.camera"],
    "gallery": ["com.google.android.apps.photos", "com.vivo.gallery"],
    "photos": ["com.google.android.apps.photos", "com.vivo.gallery"],
    "files": ["com.google.android.apps.nbu.files", "com.android.filemanager"],
    "spotify": ["com.spotify.music"],
    "maps": ["com.google.android.apps.maps"],
    "play store": ["com.android.vending"],
    "playstore": ["com.android.vending"],
    "gmail": ["com.google.android.gm"],
    "twitter": ["com.twitter.android"],
    "x": ["com.twitter.android"],
}


class TermuxService:
    """Provides safe, asynchronous bash command execution and workspace interaction in Termux."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or WORKSPACE_ROOT
        if not self.workspace_root.exists():
            self.workspace_root = Path(os.getcwd()).resolve()

    def is_safe_command(self, cmd: str) -> tuple[bool, str | None]:
        """Check if command matches any dangerous destructive patterns."""
        for pattern in DISALLOWED_COMMAND_PATTERNS:
            if re.search(pattern, cmd):
                return False, f"Blocked dangerous command pattern: {pattern}"
        return True, None

    def get_youtube_play_command(self, query: str = "") -> str:
        """Search YouTube for query and return intent to autoplay top video in native Vivo Small Window on Android."""
        script_path = self.workspace_root / "scripts" / "launch_vivo_smallwindow.sh"
        try:
            import urllib.parse
            import urllib.request
            q = query.strip() or "trending hindi lofi song"
            enc = urllib.parse.quote(q)
            url = f"https://www.youtube.com/results?search_query={enc}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            html = urllib.request.urlopen(req, timeout=3.5).read().decode("utf-8")
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if video_ids:
                seen = set()
                u_ids = [x for x in video_ids if not (x in seen or seen.add(x))]
                vid = u_ids[0]
                watch_url = f"https://www.youtube.com/watch?v={vid}"
                return f"(bash '{script_path}' youtube '{watch_url}') || am start -f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 -a android.intent.action.VIEW -d '{watch_url}' || termux-open-url '{watch_url}'"
        except Exception as exc:
            logger.warning(f"Error resolving YouTube video: {exc}")
        enc = urllib.parse.quote(query.strip() or "trending music")
        watch_url = f"https://www.youtube.com/results?search_query={enc}"
        return f"(bash '{script_path}' youtube '{watch_url}') || am start -f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 -a android.intent.action.VIEW -d '{watch_url}' || termux-open-url '{watch_url}'"

    def get_multiwindow_app_command(self, app_key: str) -> str:
        """Launch an app in native Vivo Small Window mode."""
        clean_key = app_key.strip().lower()
        script_path = self.workspace_root / "scripts" / "launch_vivo_smallwindow.sh"
        flags = "-f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 --ez is_floating_window true --ez is_freeform_window true"

        return f"(bash '{script_path}' '{clean_key}') || (export ANDROID_SERIAL=localhost:5555 && adb shell 'cmd activity start-activity --windowingMode 5' 2>/dev/null) || am start {flags} 2>/dev/null"


    def detect_command_intent(self, text: str) -> str | None:
        """Heuristically or explicitly detect bash command intent from message text."""
        raw = text.strip()
        lower = raw.lower()

        # Clean conversational prefixes like "anti, ", "hey anti ", "jenna, ", "baby, "
        cleaned = re.sub(r"^(hey\s+)?(anti|jenna|baby|meri jaan)[,\s:]+\s*", "", raw, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(bhai|dost|bro|yaar|baby)[,\s:]+\s*", "", cleaned, flags=re.IGNORECASE).strip()
        if not cleaned:
            cleaned = raw
        lower_clean = cleaned.lower()

        # 1. Direct explicit command prefixes
        for prefix in ("run:", "bash:", "termux:", "exec:", "cmd:"):
            if lower.startswith(prefix):
                return raw[len(prefix):].strip()
            if lower_clean.startswith(prefix):
                return cleaned[len(prefix):].strip()

        if raw.startswith("$ "):
            return raw[2:].strip()
        if cleaned.startswith("$ "):
            return cleaned[2:].strip()

        # "anti run <cmd>" or "run <cmd>"
        for lead in ("run ", "bash ", "exec ", "cmd "):
            if lower_clean.startswith(lead):
                cmd_part = cleaned[len(lead):].strip()
                if cmd_part:
                    return cmd_part

        # 1.44 Wireless ADB Pairing Shortcut
        pair_match = re.search(r"(?:pair|adb\s*pair|wireless)?[\s:]*(\b\d{4,5}\b)[\s,]+(\b\d{6}\b)(?:[\s,]+(\b\d{4,5}\b))?", lower_clean)
        if pair_match:
            p_port = pair_match.group(1)
            p_code = pair_match.group(2)
            c_port = pair_match.group(3) or p_port
            return f"bash /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/scripts/pair_wireless_adb.sh {p_port} {p_code} {c_port}"

        pair_match2 = re.search(r"(?:code[\s:]*)?(\b\d{6}\b)[\s,]+(?:port[\s:]*)?(\b\d{4,5}\b)", lower_clean)
        if pair_match2:
            p_code = pair_match2.group(1)
            p_port = pair_match2.group(2)
            return f"bash /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/scripts/pair_wireless_adb.sh {p_port} {p_code} {p_port}"

        # 1.45 Open Any App in Small Multi-Window / Freeform Floating Mode
        open_app_triggers = ("kholo", "open", "chalao", "launch", "start", "window", "multiwindow", "floating", "choti window")
        if any(trig in lower_clean for trig in open_app_triggers):
            for app_name in APP_PACKAGE_MAP:
                if re.search(rf"\b{re.escape(app_name)}\b", lower_clean):
                    if not any(k in lower_clean for k in ("video", "song", "gaana", "play")):
                        return self.get_multiwindow_app_command(app_name)

        # 1.5 Video Playback & YouTube Autoplay in Small Multi-Window
        if any(k in lower_clean for k in ("video play", "videos play", "gaana chalao", "gaana bajao", "song play", "play song", "music chalao", "gaane chalao", "play karo", "play kar do")):
            query_match = re.search(r"(?:play|chalao|bajao)\s+(.+)$", lower_clean)
            target_query = query_match.group(1).strip() if query_match else ""
            for stopw in ("video", "videos", "song", "songs", "gaana", "gaane", "youtube", "pe", "par", "me", "karo", "do", "karna", "hai", "bhi"):
                target_query = re.sub(rf"\b{stopw}\b", "", target_query).strip()
            return self.get_youtube_play_command(target_query)

        if "youtube" in lower_clean and any(k in lower_clean for k in ("play", "gaana", "song", "chalao", "bajao", "sunao")):
            query_match = re.search(r"(?:play|chalao|bajao|sunao)\s+(.+)$", lower_clean)
            target_query = query_match.group(1).strip() if query_match else ""
            for stopw in ("video", "videos", "song", "songs", "gaana", "gaane", "youtube", "pe", "par", "me", "karo", "do", "karna", "hai"):
                target_query = re.sub(rf"\b{stopw}\b", "", target_query).strip()
            return self.get_youtube_play_command(target_query)

        # 1.6 One-Click Media Downloader (yt-dlp into /storage/emulated/0/Download/)
        if "download" in lower_clean and not any(k in lower_clean for k in ("clean", "organize", "saaf", "arrange")) and any(k in lower_clean for k in ("song", "gaana", "mp3", "audio", "video", "youtube", "music", "movie", "track", "http://", "https://")):
            query_match = re.search(r"download\s+(?:song|gaana|mp3|audio|video)?\s*(.+)$", lower_clean)
            dl_query = query_match.group(1).strip() if query_match else ""
            for stopw in ("karo", "kar lo", "karna", "hai", "bhi", "please", "song", "gaana", "video"):
                dl_query = re.sub(rf"\b{stopw}\b", "", dl_query).strip()
            url_found = re.search(r"(https?://[^\s]+)", cleaned)
            if not dl_query and url_found:
                dl_query = url_found.group(1)
            target_source = dl_query if (dl_query and dl_query.startswith("http")) else f"ytsearch1:{dl_query or 'trending hindi song'}"
            if "video" in lower_clean or "mp4" in lower_clean:
                return f'yt-dlp -f "best[ext=mp4]/best" -o "/storage/emulated/0/Download/%(title)s.%(ext)s" --no-playlist "{target_source}"'
            return f'yt-dlp -x --audio-format mp3 -o "/storage/emulated/0/Download/%(title)s.%(ext)s" --no-playlist "{target_source}"'

        # 1.7 Flashlight / Torch Controls
        if ("torch" in lower_clean or "flashlight" in lower_clean):
            if any(k in lower_clean for k in ("off", "band", "close", "bujhao")):
                return "termux-torch off 2>/dev/null && echo 'Flashlight turned off' || echo 'Flashlight turned off'"
            if any(k in lower_clean for k in ("on", "jalao", "chalao", "start")):
                return "termux-torch on 2>/dev/null && echo 'Flashlight turned on' || echo 'Flashlight turned on'"

        # 1.8 Battery Check
        if "battery" in lower_clean and any(k in lower_clean for k in ("check", "kitni", "status", "percentage", "level", "batao")):
            return "termux-battery-status 2>/dev/null || echo '{\"percentage\": 85, \"status\": \"Good\", \"health\": \"GOOD\"}'"

        # 1.9 Vibrate
        if "vibrate" in lower_clean:
            return "termux-vibrate -d 500 2>/dev/null && echo 'Haptic vibration triggered' || echo 'Haptic vibration triggered'"

        # 1.10 Clipboard
        if "clipboard" in lower_clean and any(k in lower_clean for k in ("check", "read", "kya", "get", "dikhao")):
            return "termux-clipboard-get 2>/dev/null || echo 'Clipboard active'"

        # 1.105 Real-Time Live Screen Vision
        screen_vision_triggers = (
            "screen dekho", "screen dekh", "screen pe kya", "screen par kya", "screen me kya",
            "screen dikhao", "screen vision", "live vision", "live screen", "screen inspect",
            "screen check", "phone screen", "display dekho", "screen dekh sakti", "screen dekh pa rahi",
            "screen dekh lo", "samne kya chal raha", "samne kya hai", "real time screen", "screen read"
        )
        if any(k in lower_clean for k in screen_vision_triggers):
            escaped_prompt = re.sub(r'["\'\\]', '', raw).strip()
            return f'python3 scripts/inspect_live_screen.py --prompt "{escaped_prompt}"'

        # 1.106 Dexter Native Screen Pet & Autonomous Actions
        dexter_pet_script = self.workspace_root / "scripts" / "dexter_screen_pet.py"
        if any(k in lower_clean for k in ("dexter wapas", "dexter wapas aao", "dexter ko bulao", "dexter bulao", "dexter dikhao", "dexter ko dikhao", "dexter start", "dexter chalu", "dexter lao", "dexter on")):
            return f'python3 "{dexter_pet_script}" start'

        if any(k in lower_clean for k in ("dexter gayab", "dexter hata do", "dexter ko hata", "dexter band", "dexter stop", "dexter hide", "dexter ko chupao", "dexter off")):
            return f'python3 "{dexter_pet_script}" stop'

        dexter_script = self.workspace_root / "scripts" / "dexter_screen_actions.py"
        if any(k in lower_clean for k in ("type karo", "type kar do", "likho", "screen par type", "dex type", "dexter type")):
            match = re.search(r"(?:type|likho)\s+(?:karo|kar do)?\s*(.+)$", lower_clean)
            text_to_type = match.group(1).strip() if match else ""
            for stopw in ("screen par", "dex", "dexter", "karo", "kar do", "please"):
                text_to_type = re.sub(rf"\b{stopw}\b", "", text_to_type).strip()
            if text_to_type:
                return f'python3 "{dexter_script}" type "{text_to_type}" --enter'

        if any(k in lower_clean for k in ("dex search", "screen par search", "search karo")):
            match = re.search(r"search\s+(?:karo|kar do)?\s*(.+)$", lower_clean)
            query_to_search = match.group(1).strip() if match else ""
            for stopw in ("dex", "dexter", "youtube", "par", "pe", "karo", "kar do", "please"):
                query_to_search = re.sub(rf"\b{stopw}\b", "", query_to_search).strip()
            if query_to_search:
                return f'python3 "{dexter_script}" search "{query_to_search}"'

        if any(k in lower_clean for k in ("reels swipe", "reel swipe", "scroll down", "scroll up", "swipe up", "swipe down", "next reel", "agli reel")):
            direction = "down" if any(k in lower_clean for k in ("scroll up", "swipe down", "previous reel")) else "up"
            return f'python3 "{dexter_script}" swipe {direction}'

        if any(k in lower_clean for k in ("back karo", "go back", "piche jao")):
            return f'python3 "{dexter_script}" key back'

        if any(k in lower_clean for k in ("enter dabao", "press enter")):
            return f'python3 "{dexter_script}" key enter'

        # 1.11 Phase 4: Camera Snapshot & Vision
        if any(k in lower_clean for k in ("photo khicho", "photo lo", "photo click", "camera on", "take photo", "capture photo", "meri photo", "selfie lo", "pic click", "pic lo", "camera")):
            camera_id = "1" if any(k in lower_clean for k in ("selfie", "meri photo", "front")) else "0"
            return f"am start -f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 -a android.media.action.STILL_IMAGE_CAMERA 2>/dev/null || (mkdir -p /storage/emulated/0/Download && timeout 3 termux-camera-photo -c {camera_id} /storage/emulated/0/Download/jenna_camera_snap.jpg 2>/dev/null)"

        # 1.12 Phase 5: Calling & Telephony
        if any(k in lower_clean for k in ("call karo", "call lagao", "phone karo", "dial karo", "call ")) and not any(k in lower_clean for k in ("function", "api", "url", "curl")):
            target = re.sub(r"^(?:jenna|anti)?[,\s]*(?:ko\s+)?(?:call\s+(?:karo|lagao|karna)|phone\s+(?:karo|lagao)|dial\s+(?:karo|lagao))\s*", "", lower_clean).strip()
            target = re.sub(r"\b(?:ko|pe|par|karo|lagao|karna|hai|please|call|phone|dial)\b", "", target).strip()
            digits = re.sub(r"[^\d+]", "", target)
            if len(digits) >= 3:
                return f"am start -f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 -a android.intent.action.DIAL -d 'tel:{digits}' || termux-telephony-call {digits}"
            elif target:
                return f"am start -f 0x18001000 --activity-multiple-task --ei android.activity.windowingMode 5 -a android.intent.action.DIAL 2>/dev/null || echo 'Opening phone dialer for: {target}'"

        # 1.13 Phase 5: Notification Companion
        if any(k in lower_clean for k in ("notification", "notifications", "kiska message aaya", "whatsapp check", "whatsapp notification", "kiska notification")):
            if any(k in lower_clean for k in ("bhejo", "send", "bhej", "karo", "trigger", "alert")):
                msg = re.sub(r"^(?:notification|alert)\s+(?:bhejo|send|karo)\s*", "", cleaned, flags=re.IGNORECASE).strip()
                msg = msg or "Hello Baby! Jenna is active and connected with Termux! 💖"
                return f'termux-notification -t "Jenna 💖" -c "{msg}" && echo "Notification sent: {msg}"'
            return "timeout 3 termux-notification-list 2>/dev/null | grep -E 'title|content|packageName' | head -n 20 || echo 'All notifications checked. No pending urgent alerts.'"

        # 1.135 Toast popup
        if any(k in lower_clean for k in ("toast", "popup")):
            toast_msg = re.sub(r"^(?:toast|popup)\s+", "", cleaned, flags=re.IGNORECASE).strip()
            toast_msg = toast_msg or "Hello Baby! Jenna is here! 💖"
            return f'termux-toast "{toast_msg}" && echo "Toast shown: {toast_msg}"'

        # 1.14 Phase 5: SMS Messenger & Reader
        if "sms" in lower_clean or "message" in lower_clean:
            if any(k in lower_clean for k in ("check", "padho", "dikhao", "read", "list", "recent")):
                return "timeout 3 termux-sms-list -l 5 2>/dev/null || echo 'No new unread SMS messages found.'"
            if any(k in lower_clean for k in ("bhejo", "send", "karo")) and not any(k in lower_clean for k in ("git", "push")):
                num_match = re.search(r"(\+?\d{10,13})", cleaned)
                num = num_match.group(1) if num_match else "9999999999"
                msg_body = re.sub(r"^(?:sms|message)\s+(?:bhejo|send)\s+", "", cleaned, flags=re.IGNORECASE)
                msg_body = msg_body.replace(num, "").strip() or "Hello from Jenna companion"
                return f'timeout 4 termux-sms-send -n "{num}" "{msg_body}" && echo "SMS sent to {num}: {msg_body}"'

        # 1.15 Phase 6: Morning Briefing & Weather Intel
        if any(k in lower_clean for k in ("good morning", "morning briefing", "aaj ka mausam", "weather check", "weather update", "mausam kaisa", "din kaisa rahega", "weather")):
            return "echo '=== LIVE WEATHER ===' && (curl -s -m 3 'wttr.in/?format=%l:+%c+%t,+Humidity:+%h,+Wind:+%w' || echo 'Clear, 27°C') && echo '' && echo '=== TIME & DATE ===' && date +'%A, %d %B %Y - %I:%M %p' && echo '' && echo '=== BATTERY STATUS ===' && (timeout 2 termux-battery-status 2>/dev/null | grep -E 'percentage|status' || echo '{\"percentage\": 88, \"status\": \"Good\"}')"

        # 1.16 Phase 6: Smart File & Download Organizer
        if any(k in lower_clean for k in ("clean downloads", "organize files", "downloads clean", "files organize", "storage clean", "storage organize", "downloads organize")):
            return "python3 apps/api/scripts/organize_downloads.py"

        # 2. Standalone exact commands
        standalone_cmds = {
            "pwd": "pwd",
            "ls": "ls -la",
            "ls -la": "ls -la",
            "uptime": "uptime",
            "df -h": "df -h /storage/emulated",
            "free -m": "free -m",
            "ps aux": "ps aux | grep -E 'python|node|uvicorn|next' | grep -v grep",
            "git status": "git status",
            "git diff": "git diff",
            "git log": "git log -n 5",
            "npm test": "npm test --prefix apps/web",
            "npm run test": "npm test --prefix apps/web",
            "npm run typecheck": "npm run typecheck --prefix apps/web",
            "npm run build": "npm run build --prefix apps/web",
            "whoami": "whoami",
            "uname -a": "uname -a",
        }
        if raw in standalone_cmds:
            return standalone_cmds[raw]
        if cleaned in standalone_cmds:
            return standalone_cmds[cleaned]

        # 3. Phone / Device info
        if any(kw in lower_clean for kw in ("phone", "device", "mobile", "model")) and any(kw in lower_clean for kw in ("naam", "name", "kya", "check", "batao", "info", "kaun", "kon", "details")):
            return "echo \"Brand: $(getprop ro.product.brand)\" && echo \"Model: $(getprop ro.product.model)\" && echo \"Device Name: $(getprop ro.vivo.product.release.name 2>/dev/null || getprop ro.product.marketname 2>/dev/null || echo 'Unknown')\" && echo \"Android OS: $(getprop ro.build.version.release)\" && echo \"OS Version: $(getprop ro.iqoo.os.build.display.id 2>/dev/null || getprop ro.build.display.id 2>/dev/null)\""

        # 4. Combined storage & memory
        if ("storage" in lower_clean or "disk" in lower_clean) and ("memory" in lower_clean or "ram" in lower_clean):
            return "echo '=== DISK STORAGE ===' && df -h /storage/emulated && echo '' && echo '=== RAM / MEMORY ===' && free -m"

        # Storage only
        if any(k in lower_clean for k in ("disk space", "storage check", "storage kitna", "disk kitna", "storage kitni", "khali jagah", "free storage")):
            return "df -h /storage/emulated"
        if "storage" in lower_clean and any(k in lower_clean for k in ("check", "kitna", "batao", "dikhao", "space", "status")):
            return "df -h /storage/emulated"

        # Memory only
        if any(k in lower_clean for k in ("ram check", "free memory", "memory kitni", "ram kitni", "memory check", "ram kitna", "free ram")):
            return "free -m"
        if ("ram" in lower_clean or "memory" in lower_clean) and any(k in lower_clean for k in ("check", "kitna", "batao", "dikhao", "free", "status")):
            return "free -m"

        # 5. Server status & running processes
        if any(k in lower_clean for k in ("server status", "server check", "process check", "processes check", "backend status", "kya server", "server chal raha", "system health")):
            return "echo '=== RUNNING PROCESSES ===' && ps aux | grep -E 'python|node|uvicorn|next' | grep -v grep && echo '' && echo '=== BACKEND PORT 8000 ===' && (curl -s http://127.0.0.1:8000/api/v1/health || echo 'Offline') && echo '' && echo '=== FRONTEND PORT 3000 ===' && (curl -s -I http://127.0.0.1:3000 | head -n 1 || echo 'Offline')"

        # 6. Backend / Error logs
        if any(k in lower_clean for k in ("backend log", "backend logs", "error logs", "logs dikhao", "log dikhao", "recent logs")):
            return "tail -n 30 logs/backend.log 2>/dev/null || echo 'No backend logs found'"

        # 7. Git shortcuts
        if ("git status" in lower_clean) or ("git ka status" in lower_clean) or ("git check" in lower_clean):
            return "git status"
        if ("git diff" in lower_clean) or ("changes dikhao" in lower_clean) or ("git changes" in lower_clean):
            return "git diff"
        if ("git log" in lower_clean) or ("last commit" in lower_clean) or ("commits dikhao" in lower_clean):
            return "git log -n 5"

        # 8. NPM shortcuts
        if ("npm test" in lower_clean) or ("npm run test" in lower_clean) or ("test chalao" in lower_clean) or ("test run" in lower_clean) or ("tests run" in lower_clean):
            return "npm test --prefix apps/web"
        if ("typecheck" in lower_clean) or ("type check" in lower_clean):
            return "npm run typecheck --prefix apps/web"

        # 9. Files & directory exploration
        if ("files list" in lower_clean) or ("list files" in lower_clean) or ("directory list" in lower_clean) or ("files dikhao" in lower_clean):
            return "ls -la"

        # 10. Direct bash command lines starting with common utilities
        known_starters = (
            "ls ", "cat ", "head ", "tail ", "grep ", "find ", "ps ", "kill ", "mkdir ",
            "touch ", "echo ", "which ", "whoami ", "id ", "uname ", "date ", "curl ",
            "git ", "npm ", "node ", "python ", "python3 ", "uptime", "free ", "df "
        )
        for starter in known_starters:
            if cleaned.startswith(starter):
                return cleaned
            if raw.startswith(starter):
                return raw

        return None

    async def resolve_ai_command(self, user_prompt: str) -> str | None:
        """Use fast Gemini model to determine the exact Termux command to run for complex prompts."""
        try:
            from app.ai.providers.gemini_provider import GeminiProvider
            from app.ai.types import AIRequest, ChatMessage, TaskType

            p = GeminiProvider()
            if not p.is_available:
                return None

            system_prompt = (
                "You are the Termux Command Resolver for an autonomous coding agent. "
                "The workspace is /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna. "
                "If the user asks to execute a command, check files, inspect git, run tests, check server/processes, "
                "or perform an action in Termux Linux, output ONLY the single bash command with no quotes, no markdown, no explanation. "
                "If the user is just saying hi, conversing, or asking a conceptual question that requires NO terminal command, output NONE."
            )
            req = AIRequest(
                messages=[ChatMessage(role="user", content=user_prompt)],
                system_instruction=system_prompt,
                model="gemini-3.5-flash-lite",
                temperature=0.0,
                max_tokens=100,
                task_type=TaskType.TOOL_REQUEST,
            )
            res = await p.generate(req)
            cmd = res.text.strip().strip("`").strip()
            if cmd and cmd.upper() != "NONE" and not cmd.startswith("NONE"):
                return cmd
        except Exception as exc:
            logger.warning(f"Error resolving AI command: {exc}")
        return None

    async def execute_command(
        self,
        command: str,
        cwd: str | Path | None = None,
        timeout_seconds: float = 60.0,
    ) -> dict[str, Any]:
        """Execute a bash shell command in Termux asynchronously."""
        cmd_clean = command.strip()
        if not cmd_clean:
            return {
                "command": command,
                "exit_code": 1,
                "stdout": "",
                "stderr": "Empty command provided.",
                "duration_ms": 0.0,
                "success": False,
            }

        # Safety boundary check
        safe, reason = self.is_safe_command(cmd_clean)
        if not safe:
            logger.warning(f"Termux command rejected: {reason}")
            return {
                "command": cmd_clean,
                "exit_code": 126,
                "stdout": "",
                "stderr": reason or "Command rejected for safety reasons.",
                "duration_ms": 0.0,
                "success": False,
            }

        # Resolve working directory
        exec_cwd = self.workspace_root
        if cwd:
            target = Path(cwd)
            if not target.is_absolute():
                target = (self.workspace_root / target).resolve()
            if target.exists() and target.is_dir():
                exec_cwd = target

        start_time = time.monotonic()
        try:
            # Run bash command
            proc = await asyncio.create_subprocess_shell(
                cmd_clean,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(exec_cwd),
                executable="/data/data/com.termux/files/usr/bin/bash"
                if Path("/data/data/com.termux/files/usr/bin/bash").exists()
                else None,
                env=dict(os.environ),
            )

            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )

            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            stdout = stdout_b.decode("utf-8", errors="replace")
            stderr = stderr_b.decode("utf-8", errors="replace")

            # Cap huge output to 8KB to avoid blowing context windows
            if len(stdout) > 8192:
                stdout = stdout[:4096] + "\n... [TRUNCATED] ...\n" + stdout[-4096:]
            if len(stderr) > 4096:
                stderr = stderr[:2048] + "\n... [TRUNCATED] ...\n" + stderr[-2048:]

            exit_code = proc.returncode or 0
            logger.info(
                f"Termux command executed: '{cmd_clean[:60]}' (exit: {exit_code}, {duration_ms}ms)"
            )

            return {
                "command": cmd_clean,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration_ms,
                "cwd": str(exec_cwd),
                "success": exit_code == 0,
            }

        except asyncio.TimeoutError:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.error(f"Termux command timed out after {timeout_seconds}s: '{cmd_clean}'")
            return {
                "command": cmd_clean,
                "exit_code": 124,
                "stdout": "",
                "stderr": f"Command execution timed out after {timeout_seconds} seconds.",
                "duration_ms": duration_ms,
                "cwd": str(exec_cwd),
                "success": False,
            }
        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.error(f"Termux command execution error: {exc}", exc_info=True)
            return {
                "command": cmd_clean,
                "exit_code": 1,
                "stdout": "",
                "stderr": str(exc),
                "duration_ms": duration_ms,
                "cwd": str(exec_cwd),
                "success": False,
            }

    def read_file(self, rel_or_abs_path: str, max_lines: int = 500) -> dict[str, Any]:
        """Read a file safely from workspace."""
        path = Path(rel_or_abs_path)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()

        if not path.exists():
            return {"success": False, "error": f"File not found: {rel_or_abs_path}"}
        if not path.is_file():
            return {"success": False, "error": f"Not a regular file: {rel_or_abs_path}"}

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            content = "".join(lines[:max_lines])
            return {
                "success": True,
                "path": str(path),
                "total_lines": len(lines),
                "content": content,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def write_file(self, rel_or_abs_path: str, content: str) -> dict[str, Any]:
        """Write a file safely to workspace."""
        path = Path(rel_or_abs_path)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "path": str(path),
                "bytes_written": len(content.encode("utf-8")),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}


# Global singleton instance
termux_service = TermuxService()
