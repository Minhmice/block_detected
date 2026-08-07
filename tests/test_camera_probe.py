"""Tests for camera probe helpers."""

from block_detected.io.camera import probe
from block_detected.io.camera.probe import CameraProbeResult, format_camera_display, format_probe_report


def test_format_camera_display_usb_mac(monkeypatch):
    monkeypatch.setattr(probe.sys, "platform", "darwin")
    assert format_camera_display(1, "usb") == "USB index 1"


def test_format_camera_display_usb_linux(monkeypatch):
    monkeypatch.setattr(probe.sys, "platform", "linux")
    assert format_camera_display(2, "usb") == "USB /dev/video2"


def test_format_probe_report_lists_working():
    results = [
        CameraProbeResult(index=0, opened=True, reads_frames=True, width=640, height=480),
        CameraProbeResult(index=1, opened=False, reads_frames=False),
    ]
    report = format_probe_report(results)
    assert "Working indices: 0" in report
    assert "640x480" in report
