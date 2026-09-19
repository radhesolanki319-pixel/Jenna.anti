#!/usr/bin/env python3
"""
Jenna AI Companion — Real WhatsApp Gateway Daemon
Connects Real Jenna (Antigravity Agent + Live Vision + Companion Soul)
directly to WhatsApp via local Baileys Bridge.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import httpx

# Ensure Jenna API is in python path
WORKSPACE_ROOT = Path(
    os.getenv("JENNA_WORKSPACE_ROOT", "/app" if os.path.exists("/app/apps/api") else "/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna")
).resolve()
API_DIR = WORKSPACE_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(API_DIR / ".env")
except ImportError:
    pass

from app.services.hermes_gateway import hermes_gateway

LOGS_DIR = WORKSPACE_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "whatsapp_jenna_daemon.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("jenna.whatsapp_daemon")

BRIDGE_URL = "http://127.0.0.1:3000"
HEADERS = {"Host": "127.0.0.1"}


async def ensure_bridge_healthy(client: httpx.AsyncClient) -> bool:
    """Check if WhatsApp bridge is healthy and connected."""
    try:
        resp = await client.get(f"{BRIDGE_URL}/health", headers=HEADERS, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("status") == "connected"
    except Exception:
        pass
    return False


async def send_typing(client: httpx.AsyncClient, chat_id: str):
    """Send typing indicator to WhatsApp chat."""
    try:
        await client.post(f"{BRIDGE_URL}/typing", json={"chatId": chat_id}, headers=HEADERS, timeout=5.0)
    except Exception as e:
        logger.debug(f"Failed to send typing: {e}")


async def send_reply(client: httpx.AsyncClient, chat_id: str, message: str):
    """Send message to WhatsApp chat via bridge."""
    try:
        resp = await client.post(
            f"{BRIDGE_URL}/send",
            json={"chatId": chat_id, "message": message},
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code == 200:
            logger.info(f"Successfully sent Jenna reply to WhatsApp chat [{chat_id}]")
        else:
            logger.warning(f"Bridge /send returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending reply to bridge: {e}")


async def process_message(client: httpx.AsyncClient, msg_data: dict):
    """Process a single incoming WhatsApp message through Real Jenna."""
    chat_id = msg_data.get("chatId")
    sender_id = msg_data.get("senderId", chat_id)
    text = (msg_data.get("body") or "").strip()

    if not text or not chat_id:
        return

    logger.info(f"Incoming WhatsApp message from [{sender_id}]: '{text}'")

    # 1. Send typing indicator immediately
    await send_typing(client, chat_id)

    # 2. Invoke Real Jenna Antigravity Agent
    try:
        reply = await hermes_gateway.handle_inbound_message("whatsapp", sender_id, text)
        logger.info(f"Generated Jenna reply for [{sender_id}]: '{reply[:120]}'")
    except Exception as e:
        logger.error(f"Error generating Jenna reply: {e}", exc_info=True)
        reply = "Arey Boss, ek chhota sa technical error aa gaya, par main theek kar rahi hoon! Ek baar dobara boliye na Boss? 💻✨"

    # 3. Send Jenna's reply to WhatsApp (resolve @lid to user's phone chat)
    target_chat = chat_id
    if target_chat.endswith("@lid"):
        target_chat = "917610543733@s.whatsapp.net"
    await send_reply(client, target_chat, reply)


async def main_loop():
    """Main continuous daemon loop."""
    logger.info("Starting Jenna Real WhatsApp Daemon...")

    async with httpx.AsyncClient(timeout=45.0) as client:
        # Wait for bridge to be connected
        while True:
            if await ensure_bridge_healthy(client):
                logger.info("WhatsApp bridge is connected and ready! Listening for messages...")
                break
            logger.warning("WhatsApp bridge not ready or disconnected, waiting 5 seconds...")
            await asyncio.sleep(5)

        # Polling loop
        while True:
            try:
                resp = await client.get(f"{BRIDGE_URL}/messages", headers=HEADERS, timeout=30.0)
                if resp.status_code == 200:
                    messages = resp.json()
                    if isinstance(messages, list) and messages:
                        for msg in messages:
                            await process_message(client, msg)
                    else:
                        await asyncio.sleep(1.0)
                elif resp.status_code == 503:
                    logger.warning("Bridge reported 503 (disconnected). Waiting...")
                    await asyncio.sleep(5)
            except httpx.TimeoutException:
                pass
            except httpx.ConnectError:
                logger.warning("Could not connect to WhatsApp bridge. Retrying in 3s...")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")
                await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Jenna WhatsApp daemon stopped by user.")
