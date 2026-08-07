from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import numpy as np

from block_detected.config.schema import AppConfig
from block_detected.core.domain import Detection, FrameResult
from block_detected.targeting import check_all_models, main, resolve_imgsz, run_single


class _FakeDetector:
    def __init__(self, name="model.onnx", task="detect", *, fail=False):
        self.model_name = name
        self.task = task
        self.fail = fail
        self.closed = False

    def predict(self, _frame, **_kwargs):
        if self.fail:
            raise RuntimeError("broken model")
        return FrameResult(
            detections=[Detection((20, 20, 40, 40), 0, "block", 0.9)],
            raw=None,
        )

    def close(self):
        self.closed = True


class _FakeCapture:
    def __init__(self):
        self.frame = np.zeros((100, 100, 3), dtype=np.uint8)

    def read(self):
        return True, self.frame.copy()


def _args(**overrides):
    values = {
        "model": "model.onnx",
        "class_filter": None,
        "frames": 1,
        "warmup": 0,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_single_model_outputs_json_and_closes_detector(monkeypatch, tmp_path):
    model = tmp_path / "model.onnx"
    model.write_bytes(b"invalid metadata is allowed by mocked loader")
    detector = _FakeDetector()
    monkeypatch.setattr("block_detected.targeting.load_detector", lambda _path: detector)
    monkeypatch.setattr("block_detected.targeting.resolve_imgsz", lambda _path, requested: requested)
    output = io.StringIO()

    result = run_single(_args(model=str(model)), AppConfig.defaults(), _FakeCapture(), output=output)

    payload = json.loads(output.getvalue())
    assert result == 0
    assert payload["target"]["error_norm"] == [-0.4, -0.4]
    assert detector.closed is True


def test_single_model_rejects_classification(monkeypatch, tmp_path):
    model = tmp_path / "classifier.pt"
    model.write_bytes(b"model")
    detector = _FakeDetector(task="classify")
    monkeypatch.setattr("block_detected.targeting.load_detector", lambda _path: detector)
    output = io.StringIO()

    result = run_single(_args(model=str(model)), AppConfig.defaults(), _FakeCapture(), output=output)

    assert result == 2
    assert json.loads(output.getvalue())["status"] == "unsupported"
    assert detector.closed is True


def test_check_all_continues_after_invalid_model(monkeypatch, tmp_path):
    bad = tmp_path / "a.onnx"
    good = tmp_path / "b.onnx"
    bad.write_bytes(b"bad")
    good.write_bytes(b"good")
    loaded = []

    def load(path):
        detector = _FakeDetector(path.name, fail=path == bad)
        loaded.append(detector)
        return detector

    monkeypatch.setattr("block_detected.targeting.load_detector", load)
    monkeypatch.setattr("block_detected.targeting.resolve_imgsz", lambda _path, requested: requested)
    output = io.StringIO()

    result = check_all_models(
        _args(),
        AppConfig.defaults(),
        np.zeros((100, 100, 3), dtype=np.uint8),
        output=output,
        models_dir=tmp_path,
    )

    records = [json.loads(line) for line in output.getvalue().splitlines()]
    assert result == 1
    assert [record["status"] for record in records] == ["error", "ok"]
    assert all(detector.closed for detector in loaded)


def test_fixed_onnx_input_size_overrides_requested(monkeypatch, tmp_path):
    model = tmp_path / "fixed.onnx"
    model.write_bytes(b"model")

    class Dim:
        def __init__(self, value):
            self.dim_value = value

    graph = type(
        "Graph",
        (),
        {"input": [type("Input", (), {"type": type("T", (), {"tensor_type": type("TT", (), {"shape": type("S", (), {"dim": [Dim(1), Dim(3), Dim(640), Dim(640)]})()})()})()})()]},
    )()
    monkeypatch.setattr("onnx.load", lambda *_args, **_kwargs: type("Model", (), {"graph": graph})())

    assert resolve_imgsz(model, 320) == 640


def test_dynamic_onnx_keeps_requested_size(monkeypatch, tmp_path):
    model = tmp_path / "dynamic.onnx"
    model.write_bytes(b"model")

    class Dim:
        dim_value = 0

    graph = type(
        "Graph",
        (),
        {"input": [type("Input", (), {"type": type("T", (), {"tensor_type": type("TT", (), {"shape": type("S", (), {"dim": [Dim(), Dim(), Dim(), Dim()]})()})()})()})()]},
    )()
    monkeypatch.setattr("onnx.load", lambda *_args, **_kwargs: type("Model", (), {"graph": graph})())

    assert resolve_imgsz(model, 320) == 320


def test_main_releases_camera_after_single_run(monkeypatch, tmp_path):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    detector = _FakeDetector(name=model.name)

    class ReleasableCapture(_FakeCapture):
        released = False

        def release(self):
            self.released = True

    capture = ReleasableCapture()
    monkeypatch.setattr("block_detected.targeting.try_open_camera", lambda *_args: (capture, 0, None))
    monkeypatch.setattr("block_detected.targeting.load_detector", lambda _path: detector)

    result = main(["--model", str(model), "--frames", "1", "--warmup", "0"])

    assert result == 0
    assert capture.released is True
    assert detector.closed is True


def test_main_reports_missing_model_without_crashing(monkeypatch):
    capture = _FakeCapture()
    capture.release = lambda: None
    monkeypatch.setattr("block_detected.targeting.try_open_camera", lambda *_args: (capture, 0, None))

    assert main(["--model", "missing.pt", "--frames", "1", "--warmup", "0"]) == 1
