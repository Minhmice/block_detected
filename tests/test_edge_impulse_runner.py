"""Tests for Edge Impulse runner service."""

from __future__ import annotations

import sys
from unittest import mock

import cv2
import numpy as np
import pytest

from app.services.edge_impulse_runner import (
    EdgeImpulseRunnerService,
    _map_ei_classification,
)
from block_detected.detection_contract import BlockID, DetectionStatus
from block_detected.pipeline import PipelineSettings


def _square_frame() -> np.ndarray:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (235, 235, 235), -1)
    return frame


def _mock_ei_modules(fake_runner: mock.Mock) -> dict[str, mock.Mock]:
    image_mod = mock.MagicMock()
    image_mod.ImageImpulseRunner = mock.Mock(return_value=fake_runner)
    pkg = mock.MagicMock()
    return {
        "edge_impulse_linux": pkg,
        "edge_impulse_linux.image": image_mod,
    }


def test_map_classification_to_block() -> None:
    block_id, confidence, scores, reject = _map_ei_classification(
        {"block_02": 0.88, "block_01": 0.12},
        min_confidence=0.5,
    )
    assert block_id == BlockID.BLOCK_02
    assert confidence == pytest.approx(0.88, rel=1e-3)
    assert reject is None
    assert scores["block_02"] == pytest.approx(0.88, rel=1e-3)


def test_runner_init_once(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = tmp_path / "model.eim"
    model.write_text("fake", encoding="utf-8")
    model.chmod(0o755)
    monkeypatch.setenv("EI_MODEL_PATH", str(model))

    fake_runner = mock.Mock()
    fake_runner.init = mock.Mock(return_value={})
    fake_runner.get_features_from_image = mock.Mock(
        return_value=(np.zeros(10, dtype=np.float32), None)
    )
    fake_runner.classify = mock.Mock(
        return_value={"result": {"classification": {"block_02": 0.9, "block_01": 0.1}}}
    )

    modules = _mock_ei_modules(fake_runner)
    with mock.patch.dict(sys.modules, modules):
        service = EdgeImpulseRunnerService()
        service.ensure_initialized()
        service.ensure_initialized()
        service.detect_from_frame(_square_frame(), PipelineSettings())

    modules["edge_impulse_linux.image"].ImageImpulseRunner.assert_called_once()
    assert fake_runner.init.call_count == 1


def test_no_candidate_returns_no_detection(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = tmp_path / "model.eim"
    model.write_text("fake", encoding="utf-8")
    model.chmod(0o755)
    monkeypatch.setenv("EI_MODEL_PATH", str(model))

    fake_runner = mock.Mock()
    fake_runner.init = mock.Mock(return_value={})

    modules = _mock_ei_modules(fake_runner)
    with mock.patch.dict(sys.modules, modules):
        service = EdgeImpulseRunnerService()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        result, _ = service.detect_from_frame(blank, PipelineSettings())

    assert result.status == DetectionStatus.NO_DETECTION
    fake_runner.classify.assert_not_called()
