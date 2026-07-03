import json
import time

from starlette.testclient import TestClient

from pi_monitor.api.app import create_app
from pi_monitor.core.config import AppConfig


def test_hub_to_dashboard_fanout():
    config = AppConfig()
    app = create_app(config, simulate=False)
    client = TestClient(app)

    with client.websocket_connect("/ws/dashboard") as dash_ws:
        initial = json.loads(dash_ws.receive_text())
        assert "stale" in initial

        with client.websocket_connect("/ws/hub") as hub_ws:
            payload = {
                "v": 1,
                "seq": 42,
                "ts_hub_ms": int(time.time() * 1000),
                "robot_state": "RUNNING",
                "driver_hub_connected": True,
                "heartbeat": True,
                "loop_time_ms": 10,
                "battery_v": 12.0,
            }
            hub_ws.send_text(json.dumps(payload))
            msg = json.loads(dash_ws.receive_text())
            assert msg["frame"]["seq"] == 42
            assert msg["stale"] is False

        status = client.get("/api/status")
        assert status.status_code == 200
        assert status.json()["last_seq"] == 42
