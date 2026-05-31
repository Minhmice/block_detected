"""Health endpoint tests."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_health_returns_200() -> None:
    os.environ.setdefault("MOCK_CAMERA", "true")
    from app.main import app

    client = TestClient(app)
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "mockCamera" in data
    assert data["status"] == "ok"


def test_loop_idle_when_not_mock(monkeypatch) -> None:
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    monkeypatch.setenv("MOCK_CAMERA", "false")
    monkeypatch.setenv("DETECTION_MODE", "live")
    camera_runtime.set_mock(False)

    import importlib

    import app.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["mockCamera"] is False
    assert data["detectionRunning"] is False


def test_health_ei_fields(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_CAMERA", "true")
    monkeypatch.setenv("VISION_MOCK_MODE", "true")

    import importlib

    import app.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "visionMockMode" in data
    assert data["visionMockMode"] is True
    assert "eiModelPath" in data
    assert "eiModelLoaded" in data
    assert data["eiModelLoaded"] is False
    assert "eiModelExecutable" in data
