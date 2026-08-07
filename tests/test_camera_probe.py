"""Tests for camera probe helpers."""

from block_detected.io.camera.probe import format_camera_display, format_probe_report
from block_detected.io.camera.probe import CameraProbeResult


def test_format_camera_display_usb_mac():
    label = format_camera_display(1, "usb")
    assert label == "USB index 1"


def test_format_camera_display_usb_linux():
    label = format_camera_display(2, "usb")
    if __import__("sys").platform.startswith("linux"):
        assert label == "USB /dev/video2"
    else:
        assert "USB" in label


def test_format_probe_report_lists_working():
    results = [
        CameraProbeResult(index=0, opened=True, reads_frames=True, width=640, height=480),
        CameraProbeResult(index=1, opened=False, reads_frames=False),
    ]
    report = format_probe_report(results)
    assert "Working indices: 0" in report
    assert "640x480" in report
