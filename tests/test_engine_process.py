"""Tests for WebcamEngine.process_frame and apply_hot_config without real hardware."""

from pathlib import Path

import numpy as np

from block_detected.core.domain import FrameResult
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine


class _FakeCap:
    def __init__(self, ok: bool = True, frame=None) -> None:
        self._ok = ok
        self._frame = frame if frame is not None else np.zeros((8, 8, 3), dtype=np.uint8)

    def read(self):
        if not self._ok:
            return False, None
        return True, self._frame


class _FakeDetector:
    def __init__(self, name: str = "fake.pt", *, raise_on_predict: bool = False) -> None:
        self._name = name
        self._raise_on_predict = raise_on_predict
        self.closed = False

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float):
        if self._raise_on_predict:
            raise RuntimeError("inference failed")
        return FrameResult(detections=[], raw=None)

    def close(self) -> None:
        self.closed = True


def _engine_with_cap(*, cap_ok: bool = True, raise_on_predict: bool = False) -> WebcamEngine:
    config = AppConfig.defaults()
    config.stability.enabled = True
    detector = _FakeDetector(raise_on_predict=raise_on_predict)
    engine = WebcamEngine(config, [Path("fake.pt")], detector)
    engine._cap = _FakeCap(ok=cap_ok)
    return engine


def test_process_frame_returns_processed_frame_with_stats():
    engine = _engine_with_cap()

    result = engine.process_frame()

    assert result is not None
    assert result.status.detection_count == 0
    assert result.status.stats.inference_ms > 0


def test_process_frame_returns_none_on_read_failure():
    engine = _engine_with_cap(cap_ok=False)

    assert engine.process_frame() is None


def test_process_frame_returns_none_on_inference_exception():
    engine = _engine_with_cap(raise_on_predict=True)

    assert engine.process_frame() is None


def test_apply_hot_config_updates_stability_without_touching_cap():
    config = AppConfig.defaults()
    config.stability.enabled = False
    engine = WebcamEngine(config, [], _FakeDetector())
    cap = _FakeCap()
    engine._cap = cap

    updated = AppConfig.defaults()
    updated.stability.enabled = True
    engine.apply_hot_config(updated)

    assert engine.config.stability.enabled is True
    assert engine._cap is cap
