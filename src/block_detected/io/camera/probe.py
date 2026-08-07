"""Probe local camera indices (USB / built-in) for Mac, Linux, and Pi."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import cv2

from block_detected.io.camera.v4l2 import _open_capture, _video_backend


@dataclass(frozen=True, slots=True)
class CameraProbeResult:
    index: int
    opened: bool
    reads_frames: bool
    width: int = 0
    height: int = 0
    backend: str = ""

    @property
    def label(self) -> str:
        if sys.platform.startswith("linux"):
            device = f"/dev/video{self.index}"
        else:
            device = f"index {self.index}"
        if not self.opened:
            return f"{device} — not available"
        if not self.reads_frames:
            return f"{device} — opens but no frames"
        return f"{device} — {self.width}x{self.height} OK"


def _backend_name() -> str:
    backend = _video_backend()
    names = {
        cv2.CAP_AVFOUNDATION: "AVFoundation",
        cv2.CAP_DSHOW: "DirectShow",
        cv2.CAP_V4L2: "V4L2",
    }
    return names.get(backend, str(backend))


def probe_camera_index(index: int) -> CameraProbeResult:
    backend = _backend_name()
    cap = _open_capture(index)
    if not cap.isOpened():
        return CameraProbeResult(index=index, opened=False, reads_frames=False, backend=backend)

    for _ in range(4):
        cap.read()
    ok, frame = cap.read()
    if not ok or frame is None or frame.size == 0:
        cap.release()
        return CameraProbeResult(index=index, opened=True, reads_frames=False, backend=backend)

    height, width = frame.shape[:2]
    cap.release()
    return CameraProbeResult(
        index=index,
        opened=True,
        reads_frames=True,
        width=width,
        height=height,
        backend=backend,
    )


def probe_cameras(max_index: int = 10) -> list[CameraProbeResult]:
    return [probe_camera_index(index) for index in range(max_index + 1)]


def working_camera_indices(max_index: int = 10) -> list[int]:
    return [r.index for r in probe_cameras(max_index) if r.reads_frames]


def format_camera_display(index: int, source: str) -> str:
    if source == "usb":
        if sys.platform.startswith("linux"):
            return f"USB /dev/video{index}"
        return f"USB index {index}"
    if source in ("libcamera", "rpicam", "gstreamer"):
        return f"CSI ({source})"
    if sys.platform.startswith("linux"):
        return f"/dev/video{index}"
    return f"index {index}"


def format_probe_report(results: list[CameraProbeResult]) -> str:
    lines = [f"OpenCV backend: {_backend_name()}", ""]
    working = [r for r in results if r.reads_frames]
    for result in results:
        marker = " *" if result.reads_frames else ""
        lines.append(f"  {result.label}{marker}")
    lines.append("")
    if working:
        indices = ", ".join(str(r.index) for r in working)
        lines.append(f"Working indices: {indices}")
        lines.append("Set camera.index in block_detected.json or use --camera-index N")
        if len(working) > 1:
            lines.append("Multiple cameras: press C in TUI to switch, or pick the USB index above.")
    else:
        lines.append("No working cameras found. Check USB connection and permissions.")
    return "\n".join(lines)
