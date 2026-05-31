"""Detection control API tests."""

from __future__ import annotations

from unittest import mock

import numpy as np
from fastapi.testclient import TestClient


def test_start_with_mocked_usb_source(monkeypatch) -> None:
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    monkeypatch.setenv("MOCK_CAMERA", "false")
    monkeypatch.setenv("DETECTION_MODE", "live")
    camera_runtime.set_mock(False)
    camera_runtime.set_camera_index(0)

    fake_source = mock.Mock()
    fake_source.start = mock.Mock()
    fake_source.stop = mock.Mock()
    fake_frame = mock.Mock()
    fake_frame.image_bgr = np.zeros((480, 640, 3), dtype=np.uint8)
    fake_source.read = mock.Mock(return_value=fake_frame)

    import importlib

    import app.main as main_module
    import app.services.detection_loop as loop_module

    importlib.reload(loop_module)
    importlib.reload(main_module)

    with mock.patch.object(
        loop_module,
        "create_frame_source_from_env",
        return_value=fake_source,
    ):
        client = TestClient(main_module.app)
        with client:
            start = client.post("/api/detection/start")
            assert start.status_code == 200
            assert start.json()["started"] is True

            health = client.get("/health")
            assert health.json()["detectionRunning"] is True

            stop = client.post("/api/detection/stop")
            assert stop.status_code == 200


def test_detection_with_vision_mock(monkeypatch) -> None:
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    monkeypatch.setenv("MOCK_CAMERA", "true")
    monkeypatch.setenv("DETECTION_MODE", "mock")
    monkeypatch.setenv("VISION_MOCK_MODE", "true")
    camera_runtime.set_mock(True)

    import importlib
    import time

    import app.main as main_module
    import app.services.detection_loop as loop_module

    importlib.reload(loop_module)
    importlib.reload(main_module)

    client = TestClient(main_module.app)
    with client:
        start = client.post("/api/detection/start")
        assert start.status_code == 200
        deadline = time.time() + 3.0
        telemetry = {}
        while time.time() < deadline:
            telemetry = main_module.app.state.detection_loop.latest_telemetry()
            if telemetry.get("detection", {}).get("blockId") == 2:
                break
            time.sleep(0.05)
        assert telemetry.get("valid") is True
        assert telemetry.get("detection", {}).get("blockId") == 2
        client.post("/api/detection/stop")


def test_apply_params_coerces_even_blur_kernel(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_CAMERA", "true")
    monkeypatch.setenv("VISION_MOCK_MODE", "true")

    import importlib

    import app.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)
    with client:
        response = client.post(
            "/api/detection/params",
            json={"blurKernel": 4},
        )
        assert response.status_code == 200
        blur = main_module.app.state.detection_loop._settings.vision.preprocess.blur_kernel
        assert blur == (5, 5)
