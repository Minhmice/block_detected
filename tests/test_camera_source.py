"""Camera FrameSource tests (CAM-01, CAM-02).

Quick run: python -m pytest tests/test_camera_source.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import cv2
import numpy as np
import pytest

from block_detected.camera import (
    CameraSettings,
    ImageSequenceFrameSource,
    PiCamera2FrameSource,
    UsbVideoCaptureFrameSource,
    _select_cv_backend,
    create_frame_source,
    load_camera_settings,
)


def test_fake_source_returns_640x480_bgr(fixture_image_dir: Path) -> None:
    settings = CameraSettings(backend="image_sequence", image_dir=str(fixture_image_dir))
    source = ImageSequenceFrameSource(settings)
    source.start()
    try:
        frame = source.read()
        assert frame.image_bgr.shape == (480, 640, 3)
        assert frame.image_bgr.dtype == np.uint8
        assert frame.frame_id == "frame_000001"
        frame2 = source.read()
        assert frame2.frame_id == "frame_000002"
    finally:
        source.stop()


def test_backend_selector_darwin(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    assert _select_cv_backend("auto") == cv2.CAP_AVFOUNDATION


def test_backend_selector_linux(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert _select_cv_backend("auto") == cv2.CAP_V4L2


def test_backend_selector_explicit_override(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert _select_cv_backend("avfoundation") == cv2.CAP_AVFOUNDATION


def test_backend_selector_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown cv_backend"):
        _select_cv_backend("bogus")


def test_usb_capture_platform_backend() -> None:
    settings = CameraSettings(backend="usb", camera_index=0, cv_backend="avfoundation")
    source = UsbVideoCaptureFrameSource(settings)
    fake_cap = mock.Mock()
    fake_cap.isOpened.return_value = True
    fake_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    fake_cap.get.return_value = 640.0
    fake_cap.set.return_value = True
    with mock.patch("block_detected.camera.cv2.VideoCapture", return_value=fake_cap) as mock_vc:
        source.start()
        frame = source.read()
        source.stop()
    assert frame.image_bgr.shape == (480, 640, 3)
    assert frame.source == "usb-opencv"
    assert mock_vc.call_args[0][1] == cv2.CAP_AVFOUNDATION


def test_backend_open_failure_is_explicit() -> None:
    settings = CameraSettings(backend="usb", camera_index=0)
    source = UsbVideoCaptureFrameSource(settings)
    fake_cap = mock.Mock()
    fake_cap.isOpened.return_value = False
    with mock.patch("block_detected.camera.cv2.VideoCapture", return_value=fake_cap):
        with pytest.raises(RuntimeError, match="failed to open USB camera"):
            source.start()


def test_manual_control_metadata_records_support() -> None:
    settings = CameraSettings(backend="picamera2", warmup_frames=0)
    source = PiCamera2FrameSource(settings)

    fake_picam = mock.Mock()
    fake_picam.capture_metadata.return_value = {
        "ExposureTime": 10000,
        "AnalogueGain": 1.0,
        "ColourGains": (1.0, 1.0),
    }
    fake_picam.capture_array.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

    source._apply_picamera2_lock(fake_picam)
    source._picam2 = fake_picam
    source._frame_index = 0

    frame = source.read()
    assert frame.source == "picamera2"
    assert "settings_requested" in frame.metadata
    assert "settings_applied" in frame.metadata
    assert "settings_unsupported" in frame.metadata


def test_create_frame_source_dispatch() -> None:
    seq = create_frame_source(CameraSettings(backend="image_sequence", image_dir="."))
    assert isinstance(seq, ImageSequenceFrameSource)


def test_camera_example_json_loads() -> None:
    path = Path(__file__).resolve().parents[1] / "config" / "camera.example.json"
    settings = load_camera_settings(path)
    assert settings.width == 640
    assert settings.height == 480
    assert settings.debug is not None
    data = json.loads(path.read_text())
    assert "profiles" in data
