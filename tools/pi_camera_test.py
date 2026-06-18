#!/usr/bin/env python3
"""Pi Camera V4L2 diagnostic tool — scans /dev/video indices and live-previews.

Usage:
    python tools/pi_camera_test.py
    python tools/pi_camera_test.py --start 0 --end 35

Keys:
    ← →      prev/next camera index
    r         re-scan available cameras
    q         quit
"""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path

import cv2
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static

# ── constants ──────────────────────────────────────────────────────────

DEFAULT_START = 0
DEFAULT_END = 35
CSS = """
Screen {
    background: #1a1a2e;
}

#info-bar {
    dock: top;
    height: auto;
    padding: 1 2;
    background: #16213e;
    color: #e0e0e0;
    border-bottom: solid #0f3460;
}

#info-bar Static {
    width: 1fr;
    text-align: center;
}

#viewer {
    height: 1fr;
    align: center middle;
}

#viewer-placeholder {
    color: #555;
    content-align: center middle;
    text-style: bold;
}

#controls {
    dock: bottom;
    height: 3;
    padding: 0 2;
    background: #16213e;
    color: #888;
    text-align: center;
    border-top: solid #0f3460;
}

.cam-ok   { color: #00ff88; }
.cam-fail { color: #ff4444; }
.highlight { color: #ffd700; text-style: bold; }
"""


@dataclass
class CamDevice:
    index: int
    label: str
    opened: bool
    width: int = 0
    height: int = 0


# ── helpers ─────────────────────────────────────────────────────────────

def scan_devices(start: int, end: int) -> list[CamDevice]:
    """Scan V4L2 indices [start, end] and return working cameras."""
    devices: list[CamDevice] = []
    # Prefer lower indices (Pi Camera) first, then higher
    for idx in range(start, end + 1):
        dev = f"/dev/video{idx}"
        if not Path(dev).exists():
            continue
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        opened = cap.isOpened()
        w, h = 0, 0
        if opened:
            # Warm-up reads
            for _ in range(4):
                cap.read()
            ok, frame = cap.read()
            if ok and frame is not None:
                h, w = frame.shape[:2]
            else:
                opened = False  # device opens but gives no frame
        cap.release()
        devices.append(CamDevice(index=idx, label=dev, opened=opened, width=w, height=h))
    return sorted(devices, key=lambda d: (not d.opened, d.index))


# ── widgets ─────────────────────────────────────────────────────────────

class CameraViewer(Static):
    """Renders the current camera frame or placeholder."""

    current_index = reactive(-1)

    def render(self) -> str:
        if self.current_index < 0:
            return "[dim]No camera selected. Press ← → to scan.[/]"
        return f"[bold]📷 /dev/video{self.current_index}[/]"


# ── app ─────────────────────────────────────────────────────────────────

class PiCamTestApp(App[None]):
    """Textual TUI that scans V4L2 cameras and shows live preview."""

    CSS = CSS
    BINDINGS = [
        ("left", "prev_cam", "Prev camera"),
        ("right", "next_cam", "Next camera"),
        ("r", "rescan", "Re-scan"),
        ("q", "quit", "Quit"),
    ]

    devices = reactive(list[CamDevice], recompose=True)
    current_idx = reactive(-1)
    fps = reactive(0.0)

    def __init__(self, start: int = DEFAULT_START, end: int = DEFAULT_END):
        super().__init__()
        self._scan_start = start
        self._scan_end = end
        self._cap: cv2.VideoCapture | None = None

    def on_mount(self) -> None:
        self.scan()

    def scan(self) -> None:
        self._close_camera()
        self.devices = scan_devices(self._scan_start, self._scan_end)
        # Find first working camera
        for d in self.devices:
            if d.opened:
                self.current_idx = d.index
                self._open_camera(d.index)
                return
        self.current_idx = -1

    def _open_camera(self, idx: int) -> None:
        self._close_camera()
        self._cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if self._cap.isOpened():
            for _ in range(4):
                self._cap.read()

    def _close_camera(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _nav_camera(self, direction: int) -> None:
        """Move through *all* devices (opened or not)."""
        if not self.devices:
            return
        # Build flat list of indices
        indices = [d.index for d in self.devices]
        try:
            pos = indices.index(self.current_idx)
        except ValueError:
            pos = 0
        new_pos = (pos + direction) % len(indices)
        new_idx = indices[new_pos]
        self._open_camera(new_idx)
        self.current_idx = new_idx

    def action_prev_cam(self) -> None:
        self._nav_camera(-1)

    def action_next_cam(self) -> None:
        self._nav_camera(1)

    def action_rescan(self) -> None:
        self.scan()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="info-bar"):
            with Horizontal():
                yield Static("", id="label-index")
                yield Static("", id="label-device")
                yield Static("", id="label-status")
                yield Static("", id="label-res")
        with Container(id="viewer"):
            yield CameraViewer(id="viewer-placeholder")
        yield Static(id="controls")
        yield Footer()

    def watch_current_idx(self, idx: int) -> None:
        cam = self._find_device(idx)
        viewer = self.query_one("#viewer-placeholder", CameraViewer)
        viewer.current_index = idx

        label_idx = self.query_one("#label-index", Static)
        label_dev = self.query_one("#label-device", Static)
        label_status = self.query_one("#label-status", Static)
        label_res = self.query_one("#label-res", Static)

        if cam:
            label_idx.update(f"Index: [{idx}]")
            label_dev.update(f"Device: {cam.label}")
            status = "OPEN" if cam.opened else "NO SIG"
            cls = "cam-ok" if cam.opened else "cam-fail"
            label_status.update(f"Status: [{cls}]{status}[/]")
            if cam.opened and cam.width:
                label_res.update(f"Resolution: {cam.width}x{cam.height}")
            elif cam.opened:
                label_res.update("Resolution: (warming up...)")
            else:
                label_res.update("Resolution: —")
        else:
            label_idx.update(f"Index: [{idx}]")
            label_dev.update("Device: —")
            label_status.update("Status: —")
            label_res.update("Resolution: —")

        ctrl = self.query_one("#controls", Static)
        ctrl.update(
            "[dim]← → prev/next  │  r re-scan  │  q quit[/]"
        )

    def _find_device(self, idx: int) -> CamDevice | None:
        for d in self.devices:
            if d.index == idx:
                return d
        return None

    # ── frame loop (poll via set_interval) ──────────────────────────

    def on_compose(self) -> None:
        self.set_interval(1 / 15, self._poll_frame)  # 15 fps for TUI

    def _poll_frame(self) -> None:
        if self._cap is None or not self._cap.isOpened():
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return

        # Build ASCII-art preview by sampling a small grid
        h, w = frame.shape[:2]
        cols = 60
        rows = 20
        box_w = max(1, w // cols)
        box_h = max(1, h // rows)

        lines: list[str] = []
        for r in range(rows):
            row_chars: list[str] = []
            for c in range(cols):
                y = r * box_h + box_h // 2
                x = c * box_w + box_w // 2
                if y < h and x < w:
                    b, g, r_val = frame[y, x]  # OpenCV BGR
                    brightness = int(0.299 * r_val + 0.587 * g + 0.114 * b)
                    ch = self._brightness_char(brightness)
                    row_chars.append(ch)
                else:
                    row_chars.append(" ")
            lines.append("".join(row_chars))

        viewer = self.query_one("#viewer-placeholder", CameraViewer)
        viewer.update("\n".join(lines))

    @staticmethod
    def _brightness_char(val: int) -> str:
        chars = " .:-=+*#%@"
        idx = min(val * len(chars) // 256, len(chars) - 1)
        return chars[idx]

    def on_unmount(self) -> None:
        self._close_camera()


# ── entry ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = ArgumentParser(description="Pi Camera V4L2 TUI test tool")
    parser.add_argument("--start", type=int, default=DEFAULT_START,
                        help=f"First /dev/video index to scan (default: {DEFAULT_START})")
    parser.add_argument("--end", type=int, default=DEFAULT_END,
                        help=f"Last /dev/video index to scan (default: {DEFAULT_END})")
    args = parser.parse_args()

    app = PiCamTestApp(start=args.start, end=args.end)
    app.run()


if __name__ == "__main__":
    main()
