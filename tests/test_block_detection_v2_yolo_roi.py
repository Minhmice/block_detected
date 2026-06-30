from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from block_detection_v2 import config
from block_detection_v2.roi import roi_from_bbox
from block_detection_v2.yolo_detector import YoloBlockDetector

_DATASET = Path(__file__).resolve().parents[1] / "src" / "block_detection_v2" / "block_dataset"
_MODEL = Path(config.YOLO_MODEL_PATH)


def test_roi_from_bbox_shape():
    roi = roi_from_bbox(100, 100, 200, 200, (480, 640))
    assert roi.mask.shape == (480, 640)
    assert roi.w > 0 and roi.h > 0


def test_roi_trim_reduces_width():
    raw = roi_from_bbox(50, 50, 250, 250, (480, 640), block_mode=3, pad_frac=0.0)
    full = roi_from_bbox(50, 50, 250, 250, (480, 640), block_mode=1, pad_frac=0.0)
    assert raw.w < full.w


@pytest.mark.skipif(not _MODEL.is_file(), reason="YOLO model missing")
def test_roi_from_yolo_box():
    frame = cv2.imread(str(_DATASET / "dt50.jpg"))
    box = YoloBlockDetector().detect(frame)[0]
    roi = roi_from_bbox(box.x1, box.y1, box.x2, box.y2, frame.shape[:2])
    assert np.count_nonzero(roi.mask) > 0
    assert roi.mask[box.y1 : box.y2, box.x1 : box.x2].max() == 255
