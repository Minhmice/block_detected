"""Frame source factory tests."""

from __future__ import annotations

from unittest import mock

from app.services.camera_runtime import camera_runtime
from app.services.frame_source_factory import create_frame_source_from_env, is_mock_mode


def test_mock_camera_uses_image_sequence(monkeypatch) -> None:
    camera_runtime.reset_for_tests()
    monkeypatch.setenv("MOCK_CAMERA", "true")
    monkeypatch.setenv("CAMERA_CONFIG", "config/camera.example.json")
    assert is_mock_mode()
    source = create_frame_source_from_env()
    source.start()
    try:
        frame = source.read()
        assert frame.image_bgr.shape == (480, 640, 3)
    finally:
        source.stop()


def test_real_mode_uses_usb_profile(monkeypatch) -> None:
    camera_runtime.reset_for_tests()
    monkeypatch.delenv("MOCK_CAMERA", raising=False)
    monkeypatch.setenv("DETECTION_MODE", "live")
    camera_runtime.set_mock(False)
    camera_runtime.set_camera_index(0)
    assert not is_mock_mode()
    captured: list = []

    def _capture_create(settings):
        captured.append(settings)
        fake = mock.Mock()
        fake.start = mock.Mock()
        fake.read = mock.Mock()
        fake.stop = mock.Mock()
        return fake

    with mock.patch(
        "app.services.frame_source_factory.create_frame_source",
        side_effect=_capture_create,
    ):
        create_frame_source_from_env()
    assert len(captured) == 1
    assert captured[0].backend == "usb"
    assert captured[0].cv_backend == "avfoundation"
    assert captured[0].camera_index == 0
