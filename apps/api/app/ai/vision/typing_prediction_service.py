"""Typing Prediction & Proactive Text Completion Service.

Predicts what the user wants to type or reply based on current live screen context,
active app, focused input field, and recent conversation history.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
import re
import subprocess
import time
from typing import Any

from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
from app.ai.vision.live_screen import live_screen_service

logger = logging.getLogger("jenna.vision.typing_prediction")


class TypingPredictionService:
    """Provides screen-contextual typing prediction, smart completions, and proactive drafts."""

    def __init__(self, serial: str = "localhost:5555") -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self.provider = GeminiVisionProvider()

    def is_keyboard_visible(self) -> bool:
        """Check if Android virtual keyboard (IME) is actively open."""
        try:
            out = subprocess.check_output(
                ["adb", "-s", self.serial, "shell", "dumpsys input_method"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.5,
            )
            return "mInputShown=true" in out or "mIsInputViewShown=true" in out
        except Exception:
            return False

    async def predict_next_input(
        self,
        current_input: str = "",
        auto_clipboard: bool = False,
    ) -> dict[str, Any]:
        """Generate smart typing predictions based on the live device screen context."""
        meta = await live_screen_service.get_screen_metadata()
        focused_pkg = meta.get("focused_package", "Unknown")
        keyboard_open = self.is_keyboard_visible()

        # Capture screen bytes
        screen_bytes = await live_screen_service.capture_screen_bytes(force_refresh=True)
        if not screen_bytes:
            # Fallback based on package context
            return self._heuristic_fallback(focused_pkg, current_input, keyboard_open)

        prompt = (
            f"You are Jenna's Typing Prediction Engine. "
            f"Current Android package is '{focused_pkg}'. "
            f"Keyboard is open: {keyboard_open}. "
        )
        if current_input:
            prompt += f"The user has partially typed: '{current_input}'. "
        else:
            prompt += "The user has an input field open or is about to type a message/command. "

        prompt += (
            "Analyze the conversation, code, or app content on the screen. "
            "Predict what the user wants to type next. "
            "Return a clean JSON object with this exact schema:\n"
            "{\n"
            "  \"predicted_intent\": \"brief intent description\",\n"
            "  \"top_completion\": \"most likely exact text to type\",\n"
            "  \"alternative_completions\": [\"option 2\", \"option 3\"],\n"
            "  \"category\": \"chat_reply | terminal_command | code_snippet | search_query | note\"\n"
            "}"
        )

        try:
            res = await self.provider.analyze_screen(
                screen_data=screen_bytes,
                mime_type="image/png",
                detect_ui_elements=False,
                prompt=prompt,
            )

            desc = res.description or ""
            # Extract JSON block
            parsed = self._extract_json(desc)
            if not parsed:
                parsed = self._heuristic_fallback(focused_pkg, current_input, keyboard_open)

            parsed["focused_package"] = focused_pkg
            parsed["keyboard_active"] = keyboard_open
            parsed["timestamp"] = datetime.now(timezone.utc).isoformat()

            if auto_clipboard and parsed.get("top_completion"):
                try:
                    subprocess.run(
                        ["termux-clipboard-set", parsed["top_completion"]],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=1.0,
                    )
                    parsed["copied_to_clipboard"] = True
                except Exception:
                    parsed["copied_to_clipboard"] = False

            return parsed

        except Exception as err:
            logger.error(f"Error in typing prediction: {err}")
            return self._heuristic_fallback(focused_pkg, current_input, keyboard_open)

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Extract JSON dictionary from model markdown output."""
        try:
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                import json
                return json.loads(m.group(0))
        except Exception:
            pass
        return None

    def _heuristic_fallback(
        self,
        package: str,
        current_input: str,
        keyboard_open: bool,
    ) -> dict[str, Any]:
        """Deterministic heuristic fallback if offline or vision is unavailable."""
        pkg_lower = package.lower()

        if "termux" in pkg_lower:
            return {
                "predicted_intent": "Terminal command execution",
                "top_completion": "git status" if not current_input else f"{current_input} --help",
                "alternative_completions": [
                    "bash status_jenna.sh",
                    "pytest -v",
                    "ls -la",
                ],
                "category": "terminal_command",
                "focused_package": package,
                "keyboard_active": keyboard_open,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        elif "whatsapp" in pkg_lower or "telegram" in pkg_lower or "kimi" in pkg_lower:
            return {
                "predicted_intent": "Conversational reply",
                "top_completion": "Haan theek hai, main dekh kar batata hoon." if not current_input else f"{current_input} jaldi karo.",
                "alternative_completions": [
                    "Arey nahi, koi baat nahi!",
                    "Abhi free ho kar baat karta hoon.",
                    "Haan zaroor!",
                ],
                "category": "chat_reply",
                "focused_package": package,
                "keyboard_active": keyboard_open,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        elif "youtube" in pkg_lower:
            return {
                "predicted_intent": "Video search",
                "top_completion": "Latest AI news 2026" if not current_input else f"{current_input} tutorial",
                "alternative_completions": [
                    "Hindi lofi songs",
                    "Python programming in Termux",
                    "Tech review",
                ],
                "category": "search_query",
                "focused_package": package,
                "keyboard_active": keyboard_open,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "predicted_intent": "General text input",
                "top_completion": current_input or "Okay",
                "alternative_completions": ["Sure", "Sounds good", "Done"],
                "category": "note",
                "focused_package": package,
                "keyboard_active": keyboard_open,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


typing_prediction_service = TypingPredictionService()
