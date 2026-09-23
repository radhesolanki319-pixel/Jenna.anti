"""
Jenna AI — Screen Vision Module (God Mode Phase 2)
AI-powered screen understanding using Screenshot + Gemini Vision.
Implements the "See → Think → Act" loop for intelligent screen control.

Flow:
  1. Capture screenshot via ADB
  2. Send to Gemini Vision API for analysis
  3. Get UI elements with coordinates
  4. Execute next action (tap, swipe, type)
  5. Repeat until goal achieved
"""

import asyncio
import base64
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jenna.screen_vision")

# Gemini API config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-2.0-flash-lite")
VISION_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{VISION_MODEL}:generateContent"

# Screen dimensions for coordinate mapping
SCREEN_WIDTH = 1260
SCREEN_HEIGHT = 2800

# Max steps in a single vision-action loop to prevent infinite loops
MAX_VISION_STEPS = 15


async def _capture_screenshot_b64() -> Optional[str]:
    """Capture screenshot and return base64 PNG string."""
    tmp_dev = "/data/local/tmp/jenna_vision_ss.png"
    tmp_local = "/data/data/com.termux/files/home/jenna_vision_ss.png"

    try:
        proc = await asyncio.create_subprocess_shell(
            f"adb -s 127.0.0.1:5555 shell screencap -p {tmp_dev}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=5.0)

        proc2 = await asyncio.create_subprocess_shell(
            f"adb -s 127.0.0.1:5555 pull {tmp_dev} {tmp_local}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc2.communicate(), timeout=5.0)

        if os.path.exists(tmp_local):
            with open(tmp_local, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
    return None


async def _call_gemini_vision(screenshot_b64: str, prompt: str) -> Optional[Dict[str, Any]]:
    """Call Gemini Vision API with screenshot and prompt."""
    try:
        from app.core.config import settings
        api_key = settings.effective_google_api_key or os.getenv("GOOGLE_API_KEY", "")
    except Exception:
        api_key = os.getenv("GOOGLE_API_KEY", "")

    if not api_key:
        logger.error("GOOGLE_API_KEY not set — cannot use Vision")
        return None

    import aiohttp

    url = f"{VISION_API_URL}?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": screenshot_b64,
                    }
                },
                {"text": prompt},
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            # Try to extract JSON from text
                            start = text.find("{")
                            end = text.rfind("}") + 1
                            if start >= 0 and end > start:
                                return json.loads(text[start:end])
                    return {"raw_response": text}
                else:
                    error_text = await resp.text()
                    logger.error(f"Gemini Vision API error {resp.status}: {error_text[:200]}")
                    return None
    except Exception as e:
        logger.error(f"Gemini Vision API call failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  SCREEN ANALYSIS
# ══════════════════════════════════════════════════════════════

ANALYZE_PROMPT = """You are Jenna AI analyzing an Android phone screen (1260x2800 pixels).

Look at this screenshot and identify:
1. What app/screen is currently showing
2. All visible UI elements with their approximate tap coordinates (x, y)
3. Text visible on screen

Respond in JSON format:
{
  "current_app": "app name or screen description",
  "screen_state": "brief description of what's on screen",
  "elements": [
    {"label": "element description", "type": "button|input|text|icon|image|link", "x": 630, "y": 400, "text": "visible text if any"}
  ],
  "scrollable": true/false,
  "keyboard_visible": true/false
}

Be precise with coordinates. The screen is 1260 pixels wide and 2800 pixels tall.
Top-left is (0,0), bottom-right is (1260,2800).
"""


async def analyze_screen() -> Dict[str, Any]:
    """Capture and analyze current screen state."""
    start = time.time()

    screenshot = await _capture_screenshot_b64()
    if not screenshot:
        return {"success": False, "error": "Failed to capture screenshot"}

    result = await _call_gemini_vision(screenshot, ANALYZE_PROMPT)
    if not result:
        return {"success": False, "error": "Vision API call failed"}

    return {
        "success": True,
        "analysis": result,
        "duration_ms": round((time.time() - start) * 1000, 1),
    }


# ══════════════════════════════════════════════════════════════
#  GOAL-DIRECTED VISION LOOP (See → Think → Act)
# ══════════════════════════════════════════════════════════════

GOAL_PROMPT_TEMPLATE = """You are Jenna AI controlling an Android phone screen (1260x2800 pixels).

GOAL: {goal}

PREVIOUS ACTIONS TAKEN:
{action_history}

Look at this screenshot and decide the NEXT action to achieve the goal.

Rules:
- If the goal is already achieved, set "goal_completed" to true
- If you need to tap something, provide exact (x, y) coordinates
- If you need to type, use "type" action
- For navigation, use "key" action with keycode (HOME=3, BACK=4, ENTER=66)
- Be precise with coordinates (screen is 1260x2800)
- Do ONE action at a time

Respond in JSON:
{{
  "screen_description": "what you see on screen",
  "reasoning": "why you chose this action",
  "next_action": {{
    "type": "tap|swipe|type|key|wait|none",
    "params": {{}}
  }},
  "goal_completed": false,
  "goal_progress": "brief progress update"
}}

For tap: {{"type": "tap", "params": {{"x": 630, "y": 400}}}}
For swipe: {{"type": "swipe", "params": {{"x1": 630, "y1": 2100, "x2": 630, "y2": 700}}}}
For type: {{"type": "type", "params": {{"text": "hello"}}}}
For key: {{"type": "key", "params": {{"keycode": "HOME"}}}}
For wait: {{"type": "wait", "params": {{"seconds": 2}}}}
For done: {{"type": "none", "params": {{}}}}
"""


async def _execute_vision_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single action determined by vision."""
    action_type = action.get("type", "none")
    params = action.get("params", {})

    if action_type == "tap":
        proc = await asyncio.create_subprocess_shell(
            f"adb -s 127.0.0.1:5555 shell input tap {params.get('x', 0)} {params.get('y', 0)}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"executed": "tap", "x": params.get("x"), "y": params.get("y"), "success": True}

    elif action_type == "swipe":
        cmd = f"adb -s 127.0.0.1:5555 shell input swipe {params.get('x1', 0)} {params.get('y1', 0)} {params.get('x2', 0)} {params.get('y2', 0)} {params.get('duration_ms', 300)}"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return {"executed": "swipe", "success": True}

    elif action_type == "type":
        text = params.get("text", "")
        safe = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        proc = await asyncio.create_subprocess_shell(
            f'adb -s 127.0.0.1:5555 shell input text "{safe}"',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"executed": "type", "text": text, "success": True}

    elif action_type == "key":
        kc = params.get("keycode", "HOME")
        if not str(kc).isdigit() and not str(kc).startswith("KEYCODE_"):
            kc = f"KEYCODE_{str(kc).upper()}"
        proc = await asyncio.create_subprocess_shell(
            f"adb -s 127.0.0.1:5555 shell input keyevent {kc}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"executed": "key", "keycode": kc, "success": True}

    elif action_type == "wait":
        secs = params.get("seconds", 1)
        await asyncio.sleep(secs)
        return {"executed": "wait", "seconds": secs, "success": True}

    elif action_type == "none":
        return {"executed": "none", "success": True}

    return {"executed": action_type, "success": False, "error": "Unknown action type"}


async def execute_goal(goal: str, max_steps: int = MAX_VISION_STEPS) -> Dict[str, Any]:
    """Execute a goal using the See → Think → Act vision loop.

    This is the core of God Mode intelligence — Jenna looks at the screen,
    thinks about what to do next, does it, then looks again.

    Args:
        goal: Natural language goal (e.g., "Open WhatsApp and send 'hello' to Rahul")
        max_steps: Maximum steps before giving up

    Returns:
        Complete execution log with all steps, screenshots, and results
    """
    start = time.time()
    action_history = []
    steps_log = []

    logger.info(f"🎯 Vision Goal: {goal}")

    for step in range(1, max_steps + 1):
        logger.info(f"👁️ Step {step}/{max_steps}: Capturing screen...")

        # 1. SEE — capture screenshot
        screenshot = await _capture_screenshot_b64()
        if not screenshot:
            steps_log.append({"step": step, "error": "Screenshot capture failed"})
            continue

        # 2. THINK — ask Gemini what to do
        history_str = "\n".join([f"  Step {i+1}: {a}" for i, a in enumerate(action_history)]) or "  (none yet)"
        prompt = GOAL_PROMPT_TEMPLATE.format(goal=goal, action_history=history_str)

        vision_result = await _call_gemini_vision(screenshot, prompt)
        if not vision_result:
            steps_log.append({"step": step, "error": "Vision API failed"})
            await asyncio.sleep(1)
            continue

        next_action = vision_result.get("next_action", {"type": "none", "params": {}})
        goal_completed = vision_result.get("goal_completed", False)
        reasoning = vision_result.get("reasoning", "")
        screen_desc = vision_result.get("screen_description", "")

        logger.info(f"🧠 Step {step}: {screen_desc} → {next_action.get('type', 'none')} ({reasoning})")

        step_info = {
            "step": step,
            "screen": screen_desc,
            "reasoning": reasoning,
            "action": next_action,
            "progress": vision_result.get("goal_progress", ""),
        }

        # 3. CHECK — is goal done?
        if goal_completed:
            step_info["goal_completed"] = True
            steps_log.append(step_info)
            logger.info(f"✅ Goal achieved in {step} steps!")
            break

        # 4. ACT — execute the decided action
        if next_action.get("type", "none") != "none":
            exec_result = await _execute_vision_action(next_action)
            step_info["execution"] = exec_result
            action_history.append(f"{next_action['type']}({json.dumps(next_action.get('params', {}))})")

            # Brief pause for UI to update
            await asyncio.sleep(0.5)

        steps_log.append(step_info)

    total_time = round((time.time() - start) * 1000, 1)
    completed = any(s.get("goal_completed") for s in steps_log)

    return {
        "success": completed,
        "goal": goal,
        "total_steps": len(steps_log),
        "completed": completed,
        "steps": steps_log,
        "duration_ms": total_time,
        "action_history": action_history,
    }


# ══════════════════════════════════════════════════════════════
#  QUICK VISION HELPERS
# ══════════════════════════════════════════════════════════════

async def find_element(description: str) -> Optional[Dict[str, Any]]:
    """Find a specific UI element on screen by description.
    Returns coordinates if found.

    Example: find_element("search icon") → {"x": 1020, "y": 120, "found": True}
    """
    screenshot = await _capture_screenshot_b64()
    if not screenshot:
        return None

    prompt = f"""Look at this Android screenshot (1260x2800 pixels).
Find the UI element that matches: "{description}"

Respond in JSON:
{{
  "found": true/false,
  "x": <center x coordinate>,
  "y": <center y coordinate>,
  "confidence": "high|medium|low",
  "element_description": "what you found"
}}
"""
    result = await _call_gemini_vision(screenshot, prompt)
    return result


async def read_screen_text() -> Optional[Dict[str, Any]]:
    """Read all visible text on screen (OCR-like functionality)."""
    screenshot = await _capture_screenshot_b64()
    if not screenshot:
        return None

    prompt = """Read ALL visible text on this Android screenshot.
Organize by position (top to bottom).

Respond in JSON:
{
  "app_name": "current app if visible",
  "title": "screen title/header",
  "body_text": ["line 1", "line 2", ...],
  "buttons": ["button text 1", "button text 2", ...],
  "notifications": ["notification text if any"],
  "status_bar": "time and status bar info"
}
"""
    return await _call_gemini_vision(screenshot, prompt)
