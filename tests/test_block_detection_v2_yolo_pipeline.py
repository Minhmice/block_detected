from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import pytest

from block_detection_v2 import config
from block_detection_v2.pipeline import detect_raw_hexagons, reset_pipeline_cache
from block_detection_v2.preprocessing import preprocess
from block_detection_v2.yolo_detector import YoloBlockBox, YoloBlockDetector

_DATASET = Path(__file__).resolve().parents[1] / "src" / "block_detection_v2" / "block_dataset"
_MODEL = Path(config.YOLO_MODEL_PATH)


class _EmptyYolo:
    def detect(self, frame) -> List[YoloBlockBox]:
        return []


def _load(name: str):
    frame = cv2.imread(str(_DATASET / name))
    assert frame is not None
    return preprocess(frame)


@pytest.mark.skipif(not _MODEL.is_file(), reason="YOLO model missing")
def test_yolo_pipeline_dt50():
    reset_pipeline_cache()
    color, gray = _load("dt50.jpg")
    dets, meta = detect_raw_hexagons(color, gray)
    assert meta["stage"] in ("yolo_roi", "edge_roi")
    if meta["stage"] == "yolo_roi":
        assert meta.get("yolo_count", 0) >= 1


def test_yolo_fallback(monkeypatch):
    monkeypatch.setattr(config, "USE_YOLO_ROI", True)
    color, gray = _load("dt50.jpg")
    dets, meta = detect_raw_hexagons(color, gray, yolo_detector=_EmptyYolo())
    assert meta["stage"] == "edge_roi"


def test_yolo_disabled(monkeypatch):
    monkeypatch.setattr(config, "USE_YOLO_ROI", False)
    reset_pipeline_cache()
    color, gray = _load("dt50.jpg")
    dets, meta = detect_raw_hexagons(color, gray)
    assert meta["stage"] in ("edge_roi", "roi", "fit", "low_score", "ok", "fallback")
