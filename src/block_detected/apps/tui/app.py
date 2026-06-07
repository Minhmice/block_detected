"""Textual/Rich dashboard TUI for Raspberry Pi detection runtime."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from block_detected.core.domain import Detection, RuntimeStatus
from block_detected.runtime.config_apply import apply_hot_runtime_settings
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import DEFAULT_CONFIG_PATH, load_config, validate_config
from block_detected.runtime.engine import WebcamEngine
from block_detected.runtime.logging_setup import setup_logging

logger = logging.getLogger(__name__)

UI_REFRESH_SECONDS = 0.12
CONFIDENCE_KEY_STEP = 0.01
MAX_DETECTION_ROWS = 8
MAX_EVENT_LOGS = 5


@dataclass(slots=True)
class CliArgs:
    config: Path | None
    camera_index: int | None
    conf: float | None


@dataclass(frozen=True, slots=True)
class AppState:
    runtime: str
    model: str
    camera: int
    confidence: float
    stability: bool
    fps: float
    latency_read: float
    latency_infer: float
    latency_render: float
    action: str
    detections: tuple[Detection, ...] = field(default_factory=tuple)
    logs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    @property
    def latency_total(self) -> float:
        return self.latency_read + self.latency_infer + self.latency_render


@dataclass(slots=True)
class DetectionTransition:
    previous: bool
    current: bool
    detection_count: int

    @property
    def label(self) -> str:
        return "CLEAR -> DETECTED" if self.current else "DETECTED -> CLEAR"


class DetectionStateTracker:
    """Tracks DETECTED/CLEAR transitions without logging every frame."""

    def __init__(self) -> None:
        self._detected: bool | None = None

    def update(self, status: RuntimeStatus) -> DetectionTransition | None:
        detected = status.detection_count > 0
        if self._detected is None:
            self._detected = detected
            return None
        if detected == self._detected:
            return None
        transition = DetectionTransition(
            previous=self._detected,
            current=detected,
            detection_count=status.detection_count,
        )
        self._detected = detected
        return transition

    def reset(self) -> None:
        self._detected = None


class EventBuffer:
    """Small de-duplicating event buffer for the dashboard log panel."""

    def __init__(self, limit: int = MAX_EVENT_LOGS) -> None:
        self.limit = limit
        self._events: list[str] = []

    def append(self, message: str) -> None:
        if not message:
            return
        if self._events and self._events[-1].endswith(f" {message}"):
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._events.append(f"{timestamp} {message}")
        del self._events[:-self.limit]

    def snapshot(self) -> tuple[str, ...]:
        return tuple(self._events)


class TuiRuntime:
    """Owns a WebcamEngine instance for the TUI layer."""

    def __init__(self, config: AppConfig, engine_cls: type[WebcamEngine] = WebcamEngine) -> None:
        self.config = config
        self._engine_cls = engine_cls
        self._engine: WebcamEngine | None = None
        self.latest_status: RuntimeStatus | None = None
        self.latest_detections: list[Detection] = []
        self.last_error: str | None = None
        self.last_action: str | None = None
        self.running = False

    def start(self) -> str | None:
        if self.running:
            return None

        engine, create_error = self._engine_cls.try_create(self.config)
        if engine is None:
            self.last_error = create_error or "Failed to create webcam engine."
            return self.last_error

        started, start_error = engine.try_start()
        if not started:
            engine.shutdown(destroy_cv_windows=False)
            self.last_error = start_error or "Failed to open camera source."
            return self.last_error

        self._engine = engine
        self.latest_status = None
        self.latest_detections = []
        self.last_error = None
        self.last_action = "Runtime started"
        self.running = True
        return None

    def stop(self) -> None:
        engine = self._engine
        if engine is not None:
            engine.shutdown(destroy_cv_windows=False)
        self._engine = None
        self.latest_status = None
        self.latest_detections = []
        self.last_action = "Runtime stopped"
        self.running = False

    def toggle(self) -> str | None:
        if self.running:
            self.stop()
            return None
        return self.start()

    def process_once(self) -> RuntimeStatus | None:
        if self._engine is None:
            return None

        processed = self._engine.process_frame()
        if processed is None:
            self.last_error = "Frame loop ended (camera read failed or inference stopped)."
            self.stop()
            return None

        self.latest_status = processed.status
        self.latest_detections = list(getattr(processed, "detections", []))
        return processed.status

    def switch_model(self) -> bool:
        if self._engine is None:
            self.last_action = "Start runtime before switching model"
            return False
        self._engine.switch_model()
        self.last_action = "Switched model"
        logger.info("TUI switched model")
        return True

    def switch_camera(self) -> bool:
        if self._engine is None:
            self.last_action = "Start runtime before switching camera"
            return False
        switched = self._engine.switch_camera()
        self.last_action = "Switched camera" if switched else "No other camera available"
        logger.info("TUI switch camera result=%s", switched)
        return switched

    def toggle_stability(self) -> bool:
        self.config.stability.enabled = not self.config.stability.enabled
        if self._engine is not None:
            apply_hot_runtime_settings(
                self._engine,
                self.config,
                confidence=self.current_confidence,
                eval_mode=self._engine.state.eval_mode,
            )
        state = "on" if self.config.stability.enabled else "off"
        self.last_action = f"Stability {state}"
        logger.info("TUI stability %s", state)
        return self.config.stability.enabled

    @property
    def current_confidence(self) -> float:
        if self._engine is not None:
            return self._engine.state.confidence
        return self.config.inference.default_conf

    def adjust_confidence(self, delta: float = CONFIDENCE_KEY_STEP) -> float:
        inf = self.config.inference
        next_conf = min(inf.conf_max, max(inf.conf_min, self.current_confidence + delta))
        self.config.inference.default_conf = next_conf
        if self._engine is not None:
            apply_hot_runtime_settings(
                self._engine,
                self.config,
                confidence=next_conf,
                eval_mode=self._engine.state.eval_mode,
            )
        self.last_action = f"Confidence {next_conf:.3f}"
        logger.info("TUI confidence %.3f", next_conf)
        return next_conf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="block-detected-tui",
        description="Run Block Detected in a Textual dashboard.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Path to TOML config file (default: {DEFAULT_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="Override camera.index for this run.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=None,
        help="Override inference.default_conf for this run.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> CliArgs:
    ns = build_parser().parse_args(argv)
    return CliArgs(config=ns.config, camera_index=ns.camera_index, conf=ns.conf)


def config_from_args(args: CliArgs) -> AppConfig:
    config = load_config(args.config)
    if args.camera_index is not None:
        config.camera.index = args.camera_index
    if args.conf is not None:
        config.inference.default_conf = args.conf
    return config


def runtime_label(runtime: TuiRuntime) -> str:
    if runtime.last_error:
        return "ERROR"
    return "RUNNING" if runtime.running else "STOPPED"


def app_state_from_runtime(runtime: TuiRuntime, logs: tuple[str, ...] = ()) -> AppState:
    status = runtime.latest_status
    if status is None:
        return AppState(
            runtime=runtime_label(runtime),
            model="-",
            camera=runtime.config.camera.index,
            confidence=runtime.current_confidence,
            stability=runtime.config.stability.enabled,
            fps=0.0,
            latency_read=0.0,
            latency_infer=0.0,
            latency_render=0.0,
            action=runtime.last_error or runtime.last_action or "",
            detections=tuple(runtime.latest_detections),
            logs=logs,
        )

    stats = status.stats
    return AppState(
        runtime=runtime_label(runtime),
        model=status.model_name or "-",
        camera=status.camera_index,
        confidence=status.confidence,
        stability=status.stability_enabled,
        fps=stats.fps,
        latency_read=stats.frame_read_ms,
        latency_infer=stats.inference_ms,
        latency_render=stats.render_ms,
        action=runtime.last_error or runtime.last_action or "",
        detections=tuple(runtime.latest_detections),
        logs=logs,
    )


def style_status(status: str) -> str:
    if status == "RUNNING":
        return "bold green"
    if status == "ERROR":
        return "bold red"
    return "bold yellow"


def style_fps(fps: float) -> str:
    if fps >= 20:
        return "bold green"
    if fps >= 10:
        return "bold yellow"
    return "bold red"


def style_confidence(confidence: float) -> str:
    if confidence < 0.1:
        return "bold red"
    if confidence > 0.75:
        return "bold yellow"
    return "bold bright_cyan"


def render_header(state: AppState) -> Text:
    header = Text()
    header.append("Block Detection", style="bold bright_cyan")
    header.append("  ")
    header.append(f" {state.runtime} ", style=style_status(state.runtime))
    header.append(f"  cam {state.camera}", style="dim")
    header.append(f"  model {state.model}", style="white")
    header.append("  fps ")
    header.append(f"{state.fps:.1f}", style=style_fps(state.fps))
    header.append(f"  latency {state.latency_total:.1f}ms", style="bright_cyan")
    return header


def _metric_card(label: str, value: str, style: str = "bold white") -> Table:
    card = Table.grid(expand=True)
    card.add_column(ratio=1)
    card.add_row(Text(label, style="dim"))
    card.add_row(Text(value, style=style))
    return card


def render_metrics(state: AppState) -> Group:
    detection_style = "bold bright_cyan" if state.detection_count else "bold white"
    latency = (
        f"read {state.latency_read:.1f}ms  "
        f"infer {state.latency_infer:.1f}ms  "
        f"render {state.latency_render:.1f}ms"
    )
    items = [
        _metric_card("Detection count", str(state.detection_count), detection_style),
        _metric_card("Confidence", f"{state.confidence:.3f}", style_confidence(state.confidence)),
        _metric_card("Stability", "on" if state.stability else "off", "bold green" if state.stability else "dim"),
        _metric_card("FPS", f"{state.fps:.1f}", style_fps(state.fps)),
        _metric_card("Latency", latency, "white"),
    ]
    if state.action:
        items.append(_metric_card("Current action", state.action, "bright_cyan"))
    return Group(*items)


def render_detection_table(
    detections: tuple[Detection, ...],
    *,
    width: int = 120,
    limit: int = MAX_DETECTION_ROWS,
) -> Table:
    hide_bbox = width < 96
    table = Table(
        box=box.SIMPLE,
        expand=True,
        show_edge=False,
        pad_edge=False,
    )
    table.add_column("#", style="dim", no_wrap=True, width=3)
    table.add_column("class", style="white", no_wrap=True)
    table.add_column("id", justify="right", style="dim", no_wrap=True, width=4)
    table.add_column("conf", justify="right", no_wrap=True, width=6)
    if not hide_bbox:
        table.add_column("bbox", style="dim", no_wrap=True)

    sorted_detections = sorted(detections, key=lambda det: det.confidence, reverse=True)
    visible = sorted_detections[:limit]
    for index, detection in enumerate(visible, start=1):
        x1, y1, x2, y2 = detection.box
        row = [
            str(index),
            detection.class_name,
            str(detection.class_id),
            f"{detection.confidence:.3f}",
        ]
        if not hide_bbox:
            row.append(f"[{x1}, {y1}, {x2}, {y2}]")
        table.add_row(*row)

    hidden = len(sorted_detections) - len(visible)
    if hidden > 0:
        table.add_row(f"+{hidden}", "more", "", "", *([] if hide_bbox else [""]))
    if not sorted_detections:
        table.add_row("-", "No detections", "-", "-", *([] if hide_bbox else [""]))
    return table


def render_logs(state: AppState) -> Group:
    if not state.logs:
        return Group(Text("No events yet", style="dim"))
    return Group(*(Text(line, style="white") for line in state.logs[-MAX_EVENT_LOGS:]))


def render_footer() -> Text:
    footer = Text()
    footer.append("S", style="bold bright_cyan")
    footer.append(" start/stop | ")
    footer.append("M", style="bold bright_cyan")
    footer.append(" model | ")
    footer.append("C", style="bold bright_cyan")
    footer.append(" camera | ")
    footer.append("T", style="bold bright_cyan")
    footer.append(" stability | ")
    footer.append("Q", style="bold bright_cyan")
    footer.append(" quit | Esc quit")
    return footer


class BlockDetectedDashboard(App[None]):
    CSS = """
    Screen {
        background: #07111f;
        color: #dce7f3;
    }

    #top-bar {
        height: 3;
        padding: 1 2;
        background: #0b1b2e;
        border-bottom: solid #143653;
    }

    #main {
        height: 1fr;
        min-height: 12;
    }

    .panel {
        border: solid #163a5a;
        background: #0a1626;
        padding: 1 2;
    }

    #left-panel {
        width: 42%;
        min-width: 34;
    }

    #right-panel {
        width: 58%;
        min-width: 40;
    }

    .panel-title {
        height: 1;
        color: #67d7ff;
        text-style: bold;
    }

    #metrics, #detections {
        height: 1fr;
    }

    #log-panel {
        height: 7;
        min-height: 5;
    }

    #footer {
        height: 1;
        padding: 0 2;
        background: #0b1b2e;
        color: #a7b5c4;
    }
    """

    BINDINGS = [
        ("s", "toggle_runtime", "start/stop"),
        ("m", "switch_model", "model"),
        ("c", "switch_camera", "camera"),
        ("t", "toggle_stability", "stability"),
        ("up", "confidence_up", "confidence up"),
        ("down", "confidence_down", "confidence down"),
        ("q", "quit", "quit"),
        ("escape", "quit", "quit"),
    ]

    def __init__(self, config: AppConfig, engine_cls: type[WebcamEngine] = WebcamEngine) -> None:
        super().__init__()
        self.runtime = TuiRuntime(config, engine_cls=engine_cls)
        self.tracker = DetectionStateTracker()
        self.events = EventBuffer()
        self._last_rendered_action: str | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="top-bar")
        with Horizontal(id="main"):
            with Vertical(id="left-panel", classes="panel"):
                yield Static("Live Status", classes="panel-title")
                yield Static(id="metrics")
            with Vertical(id="right-panel", classes="panel"):
                yield Static("Detections", classes="panel-title")
                yield Static(id="detections")
        with Vertical(id="log-panel", classes="panel"):
            yield Static("Event Log", classes="panel-title")
            yield Static(id="logs")
        yield Static(id="footer")

    def on_mount(self) -> None:
        error = self.runtime.start()
        self._record_runtime_action(error or self.runtime.last_action)
        self.set_interval(UI_REFRESH_SECONDS, self._tick)
        self._refresh_ui()

    def on_unmount(self) -> None:
        self.runtime.stop()

    def action_toggle_runtime(self) -> None:
        error = self.runtime.toggle()
        self.tracker.reset()
        self._record_runtime_action(error or self.runtime.last_action)
        self._refresh_ui()

    def action_switch_model(self) -> None:
        self.runtime.switch_model()
        self._record_runtime_action(self.runtime.last_action)
        self._refresh_ui()

    def action_switch_camera(self) -> None:
        self.runtime.switch_camera()
        self._record_runtime_action(self.runtime.last_action)
        self._refresh_ui()

    def action_toggle_stability(self) -> None:
        self.runtime.toggle_stability()
        self._record_runtime_action(self.runtime.last_action)
        self._refresh_ui()

    def action_confidence_up(self) -> None:
        self.runtime.adjust_confidence(CONFIDENCE_KEY_STEP)
        self._record_runtime_action(self.runtime.last_action)
        self._refresh_ui()

    def action_confidence_down(self) -> None:
        self.runtime.adjust_confidence(-CONFIDENCE_KEY_STEP)
        self._record_runtime_action(self.runtime.last_action)
        self._refresh_ui()

    def _tick(self) -> None:
        if self.runtime.running:
            status = self.runtime.process_once()
            if status is None and self.runtime.last_error:
                self._record_runtime_action(self.runtime.last_error)
            elif status is not None:
                transition = self.tracker.update(status)
                if transition is not None:
                    message = f"{transition.label} count={transition.detection_count}"
                    self.events.append(message)
                    logger.info(message)
        self._refresh_ui()

    def _record_runtime_action(self, action: str | None) -> None:
        if not action or action == self._last_rendered_action:
            return
        self._last_rendered_action = action
        self.events.append(action)

    def _refresh_ui(self) -> None:
        state = app_state_from_runtime(self.runtime, self.events.snapshot())
        width = self.size.width if self.size.width else 120
        height = self.size.height if self.size.height else 32
        hide_logs = height < 24

        self.query_one("#top-bar", Static).update(render_header(state))
        self.query_one("#metrics", Static).update(render_metrics(state))
        self.query_one("#detections", Static).update(render_detection_table(state.detections, width=width))
        self.query_one("#logs", Static).update(render_logs(state))
        self.query_one("#footer", Static).update(render_footer())

        log_panel = self.query_one("#log-panel")
        log_panel.styles.display = "none" if hide_logs else "block"


def run_textual(config: AppConfig) -> int:
    result = BlockDetectedDashboard(config).run()
    return result if isinstance(result, int) else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = config_from_args(args)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"[ERROR] Config: {error}")
        return 1

    setup_logging(config.ui.log_level)
    try:
        return run_textual(config)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
