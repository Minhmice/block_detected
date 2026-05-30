"""Classifier tests (stub backend)."""

from __future__ import annotations

import numpy as np

from block_detected.classifier import ClassifierSettings, StubFaceClassifier, classify_face
from block_detected.detection_contract import BlockID


def test_stub_classifier_returns_block_and_confidence() -> None:
    warp = np.zeros((128, 128, 3), dtype=np.uint8)
    warp[:, :, 2] = 200  # red channel dominant → block_01
    result = classify_face(warp, ClassifierSettings(backend="stub"))
    assert result.block_id == BlockID.BLOCK_01
    assert result.confidence >= 0.55


def test_stub_classifier_via_instance() -> None:
    warp = np.zeros((128, 128, 3), dtype=np.uint8)
    warp[:, :, 1] = 180
    result = StubFaceClassifier().classify(warp)
    assert result.block_id == BlockID.BLOCK_02
