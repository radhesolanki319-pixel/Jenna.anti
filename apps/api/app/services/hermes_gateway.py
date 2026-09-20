"""Jenna Multi-Platform Messaging Gateway with Zero-Amnesia Disk Persistence.

A unified asynchronous router bridging incoming messages from Telegram, Discord,
WhatsApp, and Webhooks directly into Jenna's Antigravity Autonomous Agent.
Every conversation and interaction is automatically saved to disk on the phone
so that even if Termux or the phone restarts, no memory or state is lost.
"""

import asyncio
import datetime
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.services.termux_service import WORKSPACE_ROOT

logger = logging.getLogger("jenna.messaging_gateway")


class HermesMessagingGateway:
    """Unified Messaging Gateway across chat platforms with permanent disk memory."""

    def __init__(self) -> None:
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.conv_dir = WORKSPACE_ROOT / "data" / "conversations"
        self.state_dir = WORKSPACE_ROOT / "data" / "state"
        self.conv_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._load_conversations()

        self.active_channels: Dict[str, Dict[str, Any]] = {
            "web_chat": {"status": "ACTIVE", "type": "websocket/rest", "endpoint": "http://localhost:3001"},
            "telegram": {"status": "READY" if self.telegram_bot_token else "UNCONFIGURED", "type": "bot_api"},
            "discord": {"status": "READY" if self.discord_webhook_url else "UNCONFIGURED", "type": "webhook"},
            "android_dexter": {"status": "ACTIVE", "type": "native_overlay"},
            "whatsapp": {"status": "ACTIVE", "type": "baileys_bridge", "endpoint": "http://localhost:3000"},
        }

    def _safe_user_id(self, user_id: str) -> str:
        return re.sub(r"[^\w\-]", "_", user_id)

    def _load_conversations(self) -> None:
        """Preload all historical conversations from phone disk into memory."""
        try:
            for file_path in self.conv_dir.glob("*.json"):
                user_key = file_path.stem
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self.conversations[user_key] = data
                        logger.info(f"Loaded {len(data)} messages for user [{user_key}] from disk.")
                except Exception as e:
                    logger.warning(f"Failed to read conversation file {file_path}: {e}")
        except Exception as exc:
            logger.error(f"Error loading conversations: {exc}")

    def _save_conversation(self, user_id: str) -> None:
        """Persist full conversation history to phone disk storage immediately."""
        safe_id = self._safe_user_id(user_id)
        history = self.conversations.get(user_id, [])
        file_path = self.conv_dir / f"{safe_id}.json"
        try:
            # Atomic disk write
            tmp_path = self.conv_dir / f"{safe_id}.tmp"
            tmp_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(file_path)
        except Exception as e:
            logger.error(f"Failed to save conversation to disk for {user_id}: {e}")

    def _update_session_state(self, user_id: str, last_message: str, last_response: str) -> None:
        """Update active session state for crash resilience and auto-resume."""
        state_file = self.state_dir / "active_session_state.json"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state = {
            "last_active_user": user_id,
            "last_interaction_time": now_iso,
            "last_user_message": last_message,
            "last_assistant_response": last_response[:200],
            "status": "ONLINE",
            "resume_point": "READY_FOR_NEXT_INSTRUCTION",
            "active_ecosystem": {
                "fastapi": "http://127.0.0.1:8000",
                "nextjs_web": "http://127.0.0.1:3001",
                "whatsapp_bridge": "http://127.0.0.1:3000",
                "postgres": "port 5432",
                "redis": "port 6379",
            },
        }
        try:
            state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to write active session state: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Return connectivity status of all messaging gateways."""
        return {
            "gateway_status": "ONLINE",
            "supported_platforms": ["web_chat", "telegram", "discord", "whatsapp", "android_dexter", "webhook"],
            "channels": self.active_channels,
            "total_channels": len(self.active_channels),
            "stored_conversations": len(self.conversations),
        }

    async def broadcast_message(self, message: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Broadcast a message across configured external platforms."""
        targets = platforms or ["android_dexter", "web_chat"]
        results = {}

        if "android_dexter" in targets:
            try:
                bubble_file = WORKSPACE_ROOT / "logs" / "dexter_bubble.txt"
                bubble_file.parent.mkdir(parents=True, exist_ok=True)
                bubble_file.write_text(message[:120], encoding="utf-8")
                results["android_dexter"] = "delivered"
            except Exception as e:
                results["android_dexter"] = f"failed: {e}"

        if "discord" in targets and self.discord_webhook_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        self.discord_webhook_url,
                        json={"content": f"💖 **Jenna**: {message}", "username": "Jenna AI"},
                    )
                    results["discord"] = "delivered" if resp.status_code in (200, 204) else f"status_{resp.status_code}"
            except Exception as e:
                results["discord"] = f"failed: {e}"

        if "telegram" in targets and self.telegram_bot_token:
            chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
            if chat_id:
                try:
                    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(url, json={"chat_id": chat_id, "text": f"💖 Jenna: {message}"})
                        results["telegram"] = "delivered" if resp.status_code == 200 else f"status_{resp.status_code}"
                except Exception as e:
                    results["telegram"] = f"failed: {e}"

        results["web_chat"] = "active_session"
        return {"success": True, "results": results, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    async def handle_inbound_message(self, platform: str, user_id: str, message: str) -> str:
        """Process inbound message from any platform through Jenna Antigravity Agent with disk persistence."""
        from app.services.antigravity_agent import antigravity_agent

        logger.info(f"Inbound message from platform [{platform}] user [{user_id}]: '{message[:60]}'")
        safe_id = self._safe_user_id(user_id)
        
        # Look up in memory or load from disk if present
        if user_id not in self.conversations and safe_id in self.conversations:
            self.conversations[user_id] = self.conversations[safe_id]
        
        history = self.conversations.setdefault(user_id, [])
        accumulated: List[str] = []
        final_content = None

        # Build clean history format for agent
        formatted_history = []
        for h in history[-20:]:
            formatted_history.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        async for event in antigravity_agent.run_agent_loop(message, conversation_history=formatted_history):
            if event.get("type") == "stream.delta":
                accumulated.append(event.get("delta", ""))
            elif event.get("type") == "agent.final_response":
                final_content = event.get("content", "")

        response_text = (final_content or "".join(accumulated)).strip() or "Haan Boss, main sun rahi hoon! 🚀"
        
        # Enforce user preference: STRICTLY address user as Boss, NEVER use baby / jaan / meri jaan
        response_text = re.sub(r"\b(meri\s+jaan|jaan|baby|babe|sweetheart|darling)\b", "Boss", response_text, flags=re.IGNORECASE)

        IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_t = datetime.datetime.now(IST)
        ist_str = now_t.strftime("%Y-%m-%d %I:%M:%S %p IST")
        history.append({
            "role": "user",
            "content": message,
            "platform": platform,
            "timestamp": now_t.timestamp(),
            "time_str": ist_str,
        })
        history.append({
            "role": "assistant",
            "content": response_text,
            "platform": platform,
            "timestamp": now_t.timestamp(),
            "time_str": ist_str,
        })

        # Save to disk immediately
        self._save_conversation(user_id)
        if safe_id != user_id:
            self._save_conversation(safe_id)

        # Append to append-only JSONL log
        jsonl_path = self.conv_dir / f"{safe_id}.jsonl"
        try:
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"timestamp": now_t.timestamp(), "time_str": now_t.strftime("%Y-%m-%d %H:%M:%S"), "role": "user", "content": message, "platform": platform}, ensure_ascii=False) + "\n")
                f.write(json.dumps({"timestamp": now_t.timestamp(), "time_str": now_t.strftime("%Y-%m-%d %H:%M:%S"), "role": "assistant", "content": response_text, "platform": platform}, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning(f"Failed to append to JSONL log: {exc}")

        # Update crash-proof session state
        self._update_session_state(user_id, message, response_text)

        return response_text


hermes_gateway = HermesMessagingGateway()
