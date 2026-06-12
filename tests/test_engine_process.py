"""Tests for WebcamEngine.process_frame and apply_hot_config without real hardware."""

from pathlib import Path

import numpy as np

from block_detected.core.domain import Detection, FrameResult
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
    def __init__(
        self,
        name: str = "fake.pt",
        *,
        raise_on_predict: bool = False,
        detections: list[Detection] | None = None,
    ) -> None:
        self._name = name
        self._raise_on_predict = raise_on_predict
        self._detections = detections if detections is not None else []
        self.closed = False

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float, **kwargs):
        if self._raise_on_predict:
            raise RuntimeError("inference failed")
        return FrameResult(detections=list(self._detections), raw=None)

    def close(self) -> None:
        self.closed = True


def _sample_detections() -> list[Detection]:
    return [
        Detection(box=(1, 1, 3, 3), class_id=0, class_name="block", confidence=0.2),
        Detection(box=(2, 2, 6, 6), class_id=0, class_name="block", confidence=0.95),
    ]


def _engine_with_cap(
    *,
    cap_ok: bool = True,
    raise_on_predict: bool = False,
    detections: list[Detection] | None = None,
) -> WebcamEngine:
    config = AppConfig.defaults()
    config.stability.enabled = True
    config.stability.min_confidence = 0.5
    config.stability.reject_edge_boxes = False
    config.stability.temporal_window = 1
    config.stability.required_stable_votes = 1
    detector = _FakeDetector(
        raise_on_predict=raise_on_predict,
        detections=detections if detections is not None else _sample_detections(),
    )
    engine = WebcamEngine(config, [Path("fake.pt")], detector)
    engine._cap = _FakeCap(ok=cap_ok)
    return engine


def test_process_frame_returns_processed_frame_with_stats():
    engine = _engine_with_cap(detections=[])

    result = engine.process_frame()

    assert result is not None
    assert result.status.detection_count == 0
    assert result.status.stats.inference_ms > 0


def test_process_frame_applies_postprocess_min_confidence():
    engine = _engine_with_cap()

    result = engine.process_frame()

    assert result is not None
    assert result.status.detection_count == 1
    assert len(result.detections) == 1
    assert result.detections[0].confidence == 0.95


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


def test_process_frame_sets_primary_detection():
    engine = _engine_with_cap()
    result = engine.process_frame()
    assert result is not None
    assert result.status.primary_detection is not None
    assert result.status.primary_detection.confidence == 0.95


def test_process_frame_populates_sorted_detections_list():
    engine = _engine_with_cap()
    result = engine.process_frame()
    assert result is not None
    assert len(result.status.detections) == 1
    assert result.status.detections[0].confidence == 0.95


def test_apply_hot_config_min_confidence_filters_more_detections():
    engine = _engine_with_cap()
    assert engine.process_frame().status.detection_count == 1

    updated = AppConfig.defaults()
    updated.stability.enabled = True
    updated.stability.min_confidence = 0.99
    updated.stability.reject_edge_boxes = False
    updated.stability.temporal_window = 1
    updated.stability.required_stable_votes = 1
    engine.apply_hot_config(updated)

    result = engine.process_frame()
    assert result is not None
    assert result.status.detection_count == 0
