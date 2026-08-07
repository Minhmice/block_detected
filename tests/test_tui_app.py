"""Tests for Textual/Rich TUI state and render helpers."""

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("rich")
pytest.importorskip("textual")

from block_detected.tui import app
from block_detected.core.domain import Detection, InferenceStats, RuntimeStatus
from block_detected.config.schema import AppConfig


def _status(count: int = 0) -> RuntimeStatus:
    return RuntimeStatus(
        confidence=0.42,
        model_name="train-3.pt",
        camera_index=2,
        stability_enabled=True,
        detection_count=count,
        stats=InferenceStats(
            fps=12.5,
            frame_read_ms=1.2,
            inference_ms=40.0,
            render_ms=3.4,
        ),
    )


def _detections(count: int = 2) -> list[Detection]:
    detections = [
        Detection(box=(1, 2, 30, 40), class_id=0, class_name="block", confidence=0.91),
        Detection(box=(5, 6, 70, 80), class_id=2, class_name="red_block", confidence=0.82),
    ]
    for index in range(2, count):
        detections.append(
            Detection(
                box=(index, index + 1, index + 20, index + 30),
                class_id=index,
                class_name=f"block_{index}",
                confidence=0.5 + index / 100,
            )
        )
    return detections[:count]


def test_tui_app_import_smoke():
    assert callable(app.main)
    assert callable(app.run_textual)


def test_console_script_target_matches_tui_main():
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["block-detected-tui"] == "block_detected.tui.app:main"


def test_pyproject_tui_extra_uses_textual_and_rich_not_curses():
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    core_deps = "\n".join(data["project"]["dependencies"])
    tui_deps = "\n".join(data["project"]["optional-dependencies"]["tui"])

    assert "opencv-python-headless" in core_deps
    assert "PySide6" not in core_deps
    assert "textual" in tui_deps
    assert "rich" in tui_deps
    assert "windows-curses" not in tui_deps


def test_config_from_args_applies_camera_and_conf_overrides(monkeypatch):
    base = AppConfig.defaults()
    monkeypatch.setattr(app, "load_config", lambda _path: base)

    config = app.config_from_args(
        app.CliArgs(
            config=Path("custom.toml"),
            camera_index=3,
            conf=0.55,
        )
    )

    assert config.camera.index == 3
    assert config.inference.default_conf == 0.55


def test_parse_args_accepts_config_camera_and_conf():
    args = app.parse_args(["--config", "pi.toml", "--camera-index", "1", "--conf", "0.33"])

    assert args.config == Path("pi.toml")
    assert args.camera_index == 1
    assert args.conf == 0.33


def test_app_state_maps_runtime_status_and_detections():
    config = AppConfig.defaults()
    runtime = app.TuiRuntime(config)
    runtime.running = True
    runtime.latest_status = _status(2)
    runtime.latest_detections = _detections(2)
    runtime.last_action = "Switched model"

    state = app.app_state_from_runtime(runtime, ("12:00:00 Switched model",))

    assert state.runtime == "RUNNING"
    assert state.model == "train-3.pt"
    assert state.camera == 2
    assert state.confidence == 0.42
    assert state.stability is True
    assert state.fps == 12.5
    assert state.latency_total == 44.6
    assert state.action == "Switched model"
    assert state.detections == tuple(_detections(2))
    assert state.logs == ("12:00:00 Switched model",)


def test_style_helpers_return_expected_styles():
    assert app.style_status("RUNNING") == "bold green"
    assert app.style_status("STOPPED") == "bold yellow"
    assert app.style_status("ERROR") == "bold red"
    assert app.style_fps(20.0) == "bold green"
    assert app.style_fps(10.0) == "bold yellow"
    assert app.style_fps(9.9) == "bold red"
    assert app.style_confidence(0.05) == "bold red"
    assert app.style_confidence(0.42) == "bold bright_cyan"
    assert app.style_confidence(0.8) == "bold yellow"


def test_render_header_contains_dashboard_summary():
    state = app.AppState(
        runtime="RUNNING",
        model="train-3.pt",
        camera=1,
        camera_label="USB index 1",
        confidence=0.42,
        stability=True,
        fps=21.5,
        latency_read=1.0,
        latency_infer=2.0,
        latency_render=3.0,
        action="",
    )

    assert "Block Detection" in app.render_header(state).plain
    assert "RUNNING" in app.render_header(state).plain
    assert "train-3.pt" in app.render_header(state).plain
    assert "latency 6.0ms" in app.render_header(state).plain


def test_app_state_uses_loaded_model_before_first_frame():
    config = AppConfig.defaults()
    config.inference.last_model_name = "rbs-final.pt"
    runtime = app.TuiRuntime(config)
    runtime.running = True

    state = app.app_state_from_runtime(runtime)

    assert state.model == "rbs-final.pt"


def test_render_metrics_includes_model():
    from io import StringIO

    from rich.console import Console

    state = app.AppState(
        runtime="RUNNING",
        model="rbs-final.pt",
        camera=0,
        camera_label="index 0",
        confidence=0.45,
        stability=True,
        fps=18.0,
        latency_read=1.0,
        latency_infer=2.0,
        latency_render=0.5,
        action="",
    )
    metrics = app.render_metrics(state)
    buffer = StringIO()
    Console(file=buffer, width=120, force_terminal=True).print(metrics)
    assert "rbs-final.pt" in buffer.getvalue()
    assert "Model" in buffer.getvalue()

def test_render_detection_table_sorts_limits_and_reports_more():
    detections = tuple(_detections(10))
    table = app.render_detection_table(detections, width=120, limit=8)

    class_cells = table.columns[1]._cells
    conf_cells = table.columns[3]._cells

    assert class_cells[0] == "block"
    assert conf_cells[0] == "0.910"
    assert "+2" in table.columns[0]._cells[-1]
    assert "more" in table.columns[1]._cells[-1]


def test_render_detection_table_hides_bbox_when_narrow():
    wide = app.render_detection_table(tuple(_detections(1)), width=120)
    narrow = app.render_detection_table(tuple(_detections(1)), width=80)

    assert [column.header for column in wide.columns] == ["#", "class", "id", "conf", "bbox"]
    assert [column.header for column in narrow.columns] == ["#", "class", "id", "conf"]


def test_event_buffer_keeps_last_five_and_ignores_duplicate_tail():
    events = app.EventBuffer(limit=5)
    for index in range(7):
        events.append(f"event {index}")
    events.append("event 6")

    snapshot = events.snapshot()

    assert len(snapshot) == 5
    assert snapshot[0].endswith("event 2")
    assert snapshot[-1].endswith("event 6")


def test_detection_tracker_only_reports_transitions():
    tracker = app.DetectionStateTracker()

    assert tracker.update(_status(0)) is None
    assert tracker.update(_status(0)) is None

    detected = tracker.update(_status(1))
    assert detected is not None
    assert detected.label == "CLEAR -> DETECTED"
    assert detected.detection_count == 1
    assert tracker.update(_status(2)) is None

    clear = tracker.update(_status(0))
    assert clear is not None
    assert clear.label == "DETECTED -> CLEAR"


class _FakeEngine:
    created = []

    def __init__(self, *, start_ok: bool = True, frames=None, detections=None) -> None:
        self.start_ok = start_ok
        self.frames = list(frames or [])
        self.detections = list(detections or [])
        self.shutdown_calls = []
        self.switch_model_calls = 0
        self.switch_camera_calls = 0
        self.applied_configs = []
        self.state = SimpleNamespace(confidence=0.42, eval_mode=False)

    @classmethod
    def try_create(cls, _config):
        engine = cls.created.pop(0)
        return engine, None

    def try_start(self):
        if not self.start_ok:
            return False, "start failed"
        return True, None

    def process_frame(self):
        if not self.frames:
            self.last_process_error = "Camera frame read failed."
            return None
        self.last_process_error = None
        return SimpleNamespace(status=self.frames.pop(0), detections=list(self.detections))

    def switch_model(self):
        self.switch_model_calls += 1

    def switch_camera(self):
        self.switch_camera_calls += 1
        return True

    def apply_hot_config(self, config):
        self.applied_configs.append(config)

    def shutdown(self, *, destroy_cv_windows: bool = True):
        self.shutdown_calls.append(destroy_cv_windows)


def test_tui_runtime_start_process_and_stop_without_real_camera():
    fake = _FakeEngine(frames=[_status(1)], detections=_detections(2))
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(AppConfig.defaults(), engine_cls=_FakeEngine)

    assert runtime.start() is None
    assert runtime.running is True
    assert runtime.process_once().detection_count == 1
    assert runtime.latest_detections == _detections(2)

    runtime.stop()

    assert runtime.running is False
    assert fake.shutdown_calls == [False]


def test_tui_runtime_returns_error_when_start_fails():
    fake = _FakeEngine(start_ok=False)
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(AppConfig.defaults(), engine_cls=_FakeEngine)

    assert runtime.start() == "start failed"
    assert runtime.running is False
    assert fake.shutdown_calls == [False]


def test_tui_runtime_sets_error_when_frame_loop_ends():
    fake = _FakeEngine(frames=[])
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(AppConfig.defaults(), engine_cls=_FakeEngine)

    assert runtime.start() is None
    assert runtime.process_once() is None

    assert runtime.running is False
    assert "Frame loop ended" in runtime.last_error
    assert fake.shutdown_calls == [False]


def test_tui_runtime_switch_model_and_camera_call_engine_methods():
    fake = _FakeEngine(frames=[_status(0)])
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(AppConfig.defaults(), engine_cls=_FakeEngine)
    assert runtime.start() is None

    assert runtime.switch_model() is True
    assert runtime.switch_camera() is True

    assert fake.switch_model_calls == 1
    assert fake.switch_camera_calls == 1
    assert runtime.last_action == "Switched camera"


def test_tui_runtime_toggle_stability_hot_applies_config():
    config = AppConfig.defaults()
    config.stability.enabled = False
    fake = _FakeEngine(frames=[_status(0)])
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(config, engine_cls=_FakeEngine)
    assert runtime.start() is None

    assert runtime.toggle_stability() is True

    assert config.stability.enabled is True
    assert fake.applied_configs[-1].stability.enabled is True
    assert runtime.last_action == "Stability on"


def test_tui_runtime_adjust_confidence_uses_step_and_clamps():
    config = AppConfig.defaults()
    config.inference.conf_min = 0.0
    config.inference.conf_max = 0.43
    config.inference.default_conf = 0.42
    fake = _FakeEngine(frames=[_status(0)])
    _FakeEngine.created = [fake]
    runtime = app.TuiRuntime(config, engine_cls=_FakeEngine)
    assert runtime.start() is None

    assert runtime.adjust_confidence(app.CONFIDENCE_KEY_STEP) == 0.43
    assert fake.state.confidence == 0.43
    assert runtime.adjust_confidence(app.CONFIDENCE_KEY_STEP) == 0.43
    assert runtime.adjust_confidence(-app.CONFIDENCE_KEY_STEP) == 0.42


class _FakeRuntimeForActions:
    def __init__(self) -> None:
        self.calls = []
        self.last_action = None

    def toggle(self):
        self.calls.append("toggle")
        self.last_action = "Runtime stopped"
        return None

    def switch_model(self):
        self.calls.append("switch_model")
        self.last_action = "Switched model"
        return True

    def switch_camera(self):
        self.calls.append("switch_camera")
        self.last_action = "Switched camera"
        return True

    def toggle_stability(self):
        self.calls.append("toggle_stability")
        self.last_action = "Stability on"
        return True

    def adjust_confidence(self, delta):
        self.calls.append(("adjust_confidence", delta))
        self.last_action = "Confidence 0.430"
        return 0.43


def test_textual_action_handlers_call_runtime_methods(monkeypatch):
    dashboard = app.BlockDetectedDashboard(AppConfig.defaults())
    fake_runtime = _FakeRuntimeForActions()
    dashboard.runtime = fake_runtime
    monkeypatch.setattr(dashboard, "_refresh_ui", lambda: None)

    dashboard.action_toggle_runtime()
    dashboard.action_switch_model()
    dashboard.action_switch_camera()
    dashboard.action_toggle_stability()
    dashboard.action_confidence_up()
    dashboard.action_confidence_down()

    assert fake_runtime.calls == [
        "toggle",
        "switch_model",
        "switch_camera",
        "toggle_stability",
        ("adjust_confidence", app.CONFIDENCE_KEY_STEP),
        ("adjust_confidence", -app.CONFIDENCE_KEY_STEP),
    ]
