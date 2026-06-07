"""FastAPI TestClient coverage for the web API (no camera hardware)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from block_detected.apps.web.server import create_app
from block_detected.core.domain import InferenceStats, RuntimeStatus
from block_detected.runtime.logging_setup import setup_logging


@pytest.fixture
def mock_service():
    service = MagicMock()
    service.is_running = False
    service.last_error = None
    service.get_status.return_value = None
    service.get_latest_jpeg.return_value = None
    service.start.return_value = (True, None)
    return service


@pytest.fixture
def client(mock_service):
    app = create_app()
    app.state.engine_service = mock_service
    with TestClient(app) as test_client:
        yield test_client, mock_service


def test_health_returns_ok(client):
    test_client, _ = client
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_telemetry_json_shape(client):
    test_client, mock_service = client
    mock_service.is_running = True
    mock_service.get_status.return_value = RuntimeStatus(
        stats=InferenceStats(fps=25.0, frame_read_ms=4.0, inference_ms=8.0, render_ms=1.5),
        detection_count=2,
    )

    response = test_client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["fps"] == 25.0
    assert data["latency_ms"] == 12.0
    assert data["render_ms"] == 1.5
    assert data["running"] is True
    assert "fps" in data and "latency_ms" in data and "render_ms" in data


def test_telemetry_idle(client):
    test_client, mock_service = client
    mock_service.is_running = False
    mock_service.get_status.return_value = None

    response = test_client.get("/api/telemetry")
    data = response.json()
    assert data["fps"] == 0.0
    assert data["latency_ms"] == 0.0
    assert data["render_ms"] == 0.0
    assert data["running"] is False


def test_logs_tail(client):
    test_client, _ = client
    setup_logging()
    logging.getLogger("test_web_api").info("web api log line")

    response = test_client.get("/api/logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    assert "count" in data
    assert data["count"] <= 10
    assert any("web api log line" in line for line in data["lines"])


def test_control_start_stop(client):
    test_client, mock_service = client
    mock_service.is_running = False

    start = test_client.post("/api/start")
    assert start.status_code == 200
    assert start.json()["ok"] is True
    mock_service.start.assert_called_once()

    stop = test_client.post("/api/stop")
    assert stop.status_code == 200
    assert stop.json()["ok"] is True
    mock_service.stop.assert_called_once()


def test_control_start_already_running(client):
    test_client, mock_service = client
    mock_service.is_running = True

    response = test_client.post("/api/start")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "message": "already running"}
    mock_service.start.assert_not_called()


def test_stream_route_registered(client):
    test_client, _ = client
    schema = test_client.get("/openapi.json")
    assert schema.status_code == 200
    paths = schema.json().get("paths", {})
    assert "/stream" in paths
    get_op = paths["/stream"].get("get", {})
    assert "multipart" in str(get_op.get("responses", {})).lower() or get_op


def test_camera_next_requires_running(client):
    test_client, mock_service = client
    mock_service.is_running = False

    response = test_client.post("/api/camera/next")
    assert response.status_code == 409
    data = response.json()
    assert data["ok"] is False
    assert "not running" in (data.get("message") or "").lower()


def test_engine_state(client):
    test_client, mock_service = client
    mock_service.is_running = True
    mock_service.get_status.return_value = RuntimeStatus(model_name="yolo.pt", camera_index=1)

    response = test_client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is True
    assert data["model_name"] == "yolo.pt"
    assert data["camera_index"] == 1
