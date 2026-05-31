"""Camera config API tests."""

from __future__ import annotations

from unittest import mock

from fastapi.testclient import TestClient


def test_get_camera_config(monkeypatch) -> None:
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    camera_runtime.set_mock(True)
    camera_runtime.set_camera_index(1)

    with mock.patch(
        "app.routes.camera.list_usb_camera_indices",
        return_value=[0, 1],
    ):
        from app.main import app

        client = TestClient(app)
        with client:
            res = client.get("/api/camera/config")
    assert res.status_code == 200
    data = res.json()
    assert data["mockCamera"] is True
    assert data["cameraIndex"] == 1
    assert data["availableIndices"] == [0, 1]


def test_post_camera_config_live(monkeypatch) -> None:
    from app.services.camera_runtime import camera_runtime

    camera_runtime.reset_for_tests()
    camera_runtime.set_mock(True)

    with mock.patch(
        "app.routes.camera.list_usb_camera_indices",
        return_value=[0],
    ):
        import importlib

        import app.main as main_module

        importlib.reload(main_module)
        client = TestClient(main_module.app)
        with client:
            res = client.post(
                "/api/camera/config",
                json={"mockCamera": False, "cameraIndex": 0},
            )
    assert res.status_code == 200
    data = res.json()
    assert data["mockCamera"] is False
    assert data["cameraIndex"] == 0
