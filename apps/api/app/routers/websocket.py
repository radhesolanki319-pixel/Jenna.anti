from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import logger
from app.websocket.manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str | None = Query(default=None, description="Optional client identifier"),
    token: str | None = Query(default=None, description="Authentication token placeholder for Phase 3"),
):
    """Realtime WebSocket endpoint supporting heartbeats, events, and future streaming."""
    conn_id = await ws_manager.connect(websocket, client_id=client_id, token=token)

    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(conn_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(conn_id)
        logger.info(f"WebSocket client disconnected cleanly: {conn_id}")
    except Exception as e:
        ws_manager.disconnect(conn_id)
        logger.warning(f"WebSocket error for client {conn_id}: {e}")
