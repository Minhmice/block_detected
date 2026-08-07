from __future__ import annotations

from pathlib import Path

import cv2
import pytest

from block_detection_v2 import config
from block_detection_v2.yolo_detector import YoloBlockDetector

_DATASET = Path(__file__).resolve().parents[1] / "block_dataset"
_MODEL = Path(config.YOLO_MODEL_PATH)


pytestmark = pytest.mark.skipif(not _MODEL.is_file(), reason="YOLO model missing")


def test_model_path_exists():
    assert _MODEL.is_file()


def test_detect_dt50_returns_boxes():
    frame = cv2.imread(str(_DATASET / "dt50.jpg"))
    assert frame is not None
    boxes = YoloBlockDetector().detect(frame)
    assert len(boxes) >= 1
    assert boxes[0].confidence > 0.5


def test_box_xyxy_ordering():
    frame = cv2.imread(str(_DATASET / "dt50.jpg"))
    boxes = YoloBlockDetector().detect(frame)
    assert boxes
    for i in range(len(boxes) - 1):
        assert boxes[i].confidence >= boxes[i + 1].confidence
    b = boxes[0]
    assert b.x1 < b.x2
    assert b.y1 < b.y2


def test_crop_non_empty():
    frame = cv2.imread(str(_DATASET / "dt50.jpg"))
    det = YoloBlockDetector()
    boxes = det.detect(frame)
    crop = det.crop(frame, boxes[0])
    assert crop.size > 0
