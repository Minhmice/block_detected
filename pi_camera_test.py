#!/usr/bin/env python3
"""Pi Camera GStreamer + V4L2 diagnostic tool — live preview in terminal.

Usage:
    python pi_camera_test.py
    python pi_camera_test.py --width 1280 --height 720
    python pi_camera_test.py --v4l2-start 0 --v4l2-end 10

Keys:
    ← →      prev/next source
    g        add GStreamer pipeline (custom resolution prompt)
    r        re-scan V4L2 cameras
    q        quit
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

DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_V4L2_START = 0
DEFAULT_V4L2_END = 10

# Brute-force a set of common resolutions the Pi camera supports.
RESOLUTIONS: list[tuple[int, int]] = [
    (640, 480),
    (1280, 720),
    (1920, 1080),
    (2592, 1944),
    (320, 240),
    (800, 600),
    (1024, 768),
    (1640, 1232),
]

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
class Source:
    """A camera source — either GStreamer pipeline or V4L2 index."""

    label: str      # human-readable name, e.g. "GStreamer 1280x720"
    kind: str       # "gst" or "v4l2"
    width: int
    height: int
    index: int = -1             # only for v4l2
    pipeline: str | None = None  # only for gst
    opened: bool = False

    @property
    def detail(self) -> str:
        if self.kind == "gst":
            return f"GStreamer {self.width}x{self.height}"
        return f"V4L2 /dev/video{self.index} {self.width}x{self.height}"

    def __hash__(self) -> int:
        return hash((self.kind, self.index, self.pipeline))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Source):
            return NotImplemented
        return self.kind == other.kind and self.index == other.index and self.pipeline == other.pipeline


# ── helpers ─────────────────────────────────────────────────────────────

def _gst_pipeline(width: int, height: int) -> str:
    """Build a ``libcamerasrc`` GStreamer pipeline string."""
    return (
        f"libcamerasrc ! "
        f"video/x-raw,width={width},height={height},framerate=30/1 ! "
        "videoconvert ! appsink"
    )


def gst_sources() -> list[Source]:
    """Return one GStreamer source per common resolution."""
    sources: list[Source] = []
    for w, h in RESOLUTIONS:
        sources.append(Source(
            label=f"GST {w}x{h}",
            kind="gst",
            width=w,
            height=h,
            pipeline=_gst_pipeline(w, h),
        ))
    return sources


def v4l2_sources(start: int, end: int) -> list[Source]:
    """Scan V4L2 indices [start, end] and return working cameras."""
    sources: list[Source] = []
    for idx in range(start, end + 1):
        dev = f"/dev/video{idx}"
        if not Path(dev).exists():
            continue
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            continue
        # Warm-up reads
        for _ in range(4):
            cap.read()
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            continue
        h, w = frame.shape[:2]
        sources.append(Source(
            label=f"V4L2 /dev/video{idx}",
            kind="v4l2",
            index=idx,
            width=w,
            height=h,
            opened=True,
        ))
    return sources


def all_sources(v4l2_start: int, v4l2_end: int) -> list[Source]:
    """Gather GStreamer + V4L2 sources. GStreamer first, then USB."""
    return gst_sources() + v4l2_sources(v4l2_start, v4l2_end)


def open_source(src: Source) -> cv2.VideoCapture | None:
    """Try to open *src* and return the capture, or None."""
    if src.kind == "gst" and src.pipeline:
        try:
            cap = cv2.VideoCapture(src.pipeline, cv2.CAP_GSTREAMER)
        except Exception:
            return None
    elif src.kind == "v4l2":
        cap = cv2.VideoCapture(src.index, cv2.CAP_V4L2)
    else:
        return None
    if not cap.isOpened():
        cap.release()
        return None
    # Warm-up
    for _ in range(4):
        cap.read()
    return cap


# ── widgets ─────────────────────────────────────────────────────────────

class CameraViewer(Static):
    """Renders the current camera frame or placeholder."""

    current_label = reactive("")

    def render(self) -> str:
        if not self.current_label:
            return "[dim]No source selected. Press ← → to browse, r to re-scan.[/]"
        return f"[bold]📷 {self.current_label}[/]"


# ── app ─────────────────────────────────────────────────────────────────

class PiCamTestApp(App[None]):
    """Textual TUI — GStreamer + V4L2 camera sources with ASCII live preview."""

    CSS = CSS
    BINDINGS = [
        ("left", "prev_src", "Prev source"),
        ("right", "next_src", "Next source"),
        ("r", "rescan", "Re-scan V4L2"),
        ("q", "quit", "Quit"),
    ]

    sources = reactive(list[Source], recompose=True)
    current_src = reactive(Source | None, init=False)

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        v4l2_start: int = DEFAULT_V4L2_START,
        v4l2_end: int = DEFAULT_V4L2_END,
    ):
        super().__init__()
        self._default_w = width
        self._default_h = height
        self._v4l2_start = v4l2_start
        self._v4l2_end = v4l2_end
        self._cap: cv2.VideoCapture | None = None

    def on_mount(self) -> None:
        self.scan()

    def scan(self) -> None:
        self._close_camera()
        self.sources = all_sources(self._v4l2_start, self._v4l2_end)
        # Skip to first GStreamer source that opens
        for i, s in enumerate(self.sources):
            cap = open_source(s)
            if cap is not None:
                self._cap = cap
                s.opened = True
                self.current_src = s
                return
        self.current_src = Source(label="none", kind="gst", width=0, height=0) if not self.sources else self.sources[0]

    def _open_current(self) -> None:
        self._close_camera()
        if self.current_src is None:
            return
        cap = open_source(self.current_src)
        if cap is not None:
            self._cap = cap
            self.current_src.opened = True
        else:
            self.current_src.opened = False

    def _close_camera(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _nav_source(self, direction: int) -> None:
        if not self.sources:
            return
        indices = list(range(len(self.sources)))
        try:
            pos = indices.index(self._current_index())
        except (ValueError, IndexError):
            pos = 0
        new_pos = (pos + direction) % len(indices)
        self.current_src = self.sources[new_pos]
        self._open_current()

    def _current_index(self) -> int:
        if self.current_src is None:
            return 0
        for i, s in enumerate(self.sources):
            if s == self.current_src:
                return i
        return 0

    def action_prev_src(self) -> None:
        self._nav_source(-1)

    def action_next_src(self) -> None:
        self._nav_source(1)

    def action_rescan(self) -> None:
        self.scan()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="info-bar"):
            with Horizontal():
                yield Static("", id="label-source")
                yield Static("", id="label-kind")
                yield Static("", id="label-status")
                yield Static("", id="label-res")
        with Container(id="viewer"):
            yield CameraViewer(id="viewer-placeholder")
        yield Static(id="controls")
        yield Footer()

    def watch_current_src(self, src: Source | None) -> None:
        viewer = self.query_one("#viewer-placeholder", CameraViewer)
        label_src = self.query_one("#label-source", Static)
        label_kind = self.query_one("#label-kind", Static)
        label_status = self.query_one("#label-status", Static)
        label_res = self.query_one("#label-res", Static)

        if src is None or src.width == 0:
            viewer.current_label = "none"
            label_src.update("Source: —")
            label_kind.update("Kind: —")
            label_status.update("Status: —")
            label_res.update("Resolution: —")
        else:
            viewer.current_label = src.label
            label_src.update(f"Source: {src.label}")
            label_kind.update(f"Kind: {src.kind.upper()}")
            status = "OPEN" if src.opened else "NO SIG"
            cls = "cam-ok" if src.opened else "cam-fail"
            label_status.update(f"Status: [{cls}]{status}[/]")
            label_res.update(f"Resolution: {src.detail if src.opened else '—'}")

        ctrl = self.query_one("#controls", Static)
        ctrl.update("[dim]← → prev/next  │  r re-scan V4L2  │  q quit[/]")

    # ── frame loop ──────────────────────────────────────────────────

    def on_compose(self) -> None:
        self.set_interval(1 / 15, self._poll_frame)

    def _poll_frame(self) -> None:
        if self._cap is None or not self._cap.isOpened():
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return

        h, w = frame.shape[:2]
        cols, rows = 60, 20
        box_w, box_h = max(1, w // cols), max(1, h // rows)

        lines: list[str] = []
        for r in range(rows):
            row_chars: list[str] = []
            for c in range(cols):
                y, x = r * box_h + box_h // 2, c * box_w + box_w // 2
                if y < h and x < w:
                    b, g, r_val = frame[y, x]
                    lum = int(0.299 * r_val + 0.587 * g + 0.114 * b)
                    row_chars.append(_brightness_char(lum))
                else:
                    row_chars.append(" ")
            lines.append("".join(row_chars))

        viewer = self.query_one("#viewer-placeholder", CameraViewer)
        viewer.update("\n".join(lines))

    def on_unmount(self) -> None:
        self._close_camera()


def _brightness_char(val: int) -> str:
    chars = " .:-=+*#%@"
    return chars[min(val * len(chars) // 256, len(chars) - 1)]


# ── entry ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = ArgumentParser(description="Pi Camera GStreamer + V4L2 TUI test tool")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                        help=f"GStreamer width (default: {DEFAULT_WIDTH})")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT,
                        help=f"GStreamer height (default: {DEFAULT_HEIGHT})")
    parser.add_argument("--v4l2-start", type=int, default=DEFAULT_V4L2_START,
                        help=f"First V4L2 index to scan (default: {DEFAULT_V4L2_START})")
    parser.add_argument("--v4l2-end", type=int, default=DEFAULT_V4L2_END,
                        help=f"Last V4L2 index to scan (default: {DEFAULT_V4L2_END})")
    args = parser.parse_args()

    app = PiCamTestApp(
        width=args.width,
        height=args.height,
        v4l2_start=args.v4l2_start,
        v4l2_end=args.v4l2_end,
    )
    app.run()


if __name__ == "__main__":
    main()
