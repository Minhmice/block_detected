"""WebSocket telemetry tests."""

from __future__ import annotations

import os
import time

from fastapi.testclient import TestClient


def test_ws_telemetry_after_start() -> None:
    os.environ.setdefault("MOCK_CAMERA", "true")
    from app.main import app

    client = TestClient(app)
    with client:
        time.sleep(2.0)
        with client.websocket_connect("/ws/detection") as ws:
            deadline = time.time() + 10.0
            payload = None
            while time.time() < deadline:
                payload = ws.receive_json()
                if "fps" in payload:
                    break
            assert payload is not None
            assert "fps" in payload
