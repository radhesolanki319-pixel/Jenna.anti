import pytest
from starlette.testclient import TestClient

from app.main import app


def test_websocket_connect_and_welcome():
    """Test connecting to /api/v1/ws returns connection_established acknowledgement."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws?client_id=test-client-1") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "connection_established"
        assert welcome["client_id"] == "test-client-1"
        assert welcome["service"] == "jenna-api"


def test_websocket_heartbeat():
    """Test ping-pong heartbeat over WebSocket."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws?client_id=heartbeat-client") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "connection_established"

        # Send ping
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()

        assert response["type"] == "pong"
        assert response["client_id"] == "heartbeat-client"
        assert "timestamp" in response


def test_websocket_subscriptions():
    """Test subscription message over WebSocket."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.receive_json()  # welcome

        websocket.send_json({"type": "subscribe", "channels": ["system_health", "telemetry"]})
        res = websocket.receive_json()

        assert res["type"] == "subscribed"
        assert "system_health" in res["channels"]


def test_websocket_unknown_event_handling():
    """Test sending unrecognized event returns structured error."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.receive_json()  # welcome

        websocket.send_json({"type": "invalid_event_xyz"})
        res = websocket.receive_json()

        assert res["type"] == "error"
        assert res["code"] == "UNKNOWN_EVENT"


def test_websocket_extension_point():
    """Test future extension point events (e.g. ai_stream, voice_event)."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.receive_json()  # welcome

        websocket.send_json({"type": "ai_stream", "prompt": "test"})
        res = websocket.receive_json()

        assert res["type"] == "event_acknowledged"
        assert res["event_type"] == "ai_stream"
