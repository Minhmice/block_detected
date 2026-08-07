from __future__ import annotations

from pathlib import Path

import cv2

from block_detection_v2 import config
from block_detection_v2.edges import detect_edges
from block_detection_v2.pipeline import detect_raw_hexagons
from block_detection_v2.preprocessing import preprocess
from block_detection_v2.roi import ROIBox, extract_cluster_roi
from block_detection_v2.score import score_candidate

_DATASET = Path(__file__).resolve().parents[1] / "block_dataset"


def _load(name: str):
    frame = cv2.imread(str(_DATASET / name))
    assert frame is not None
    return frame


def test_score_dt50_above_threshold():
    color, gray = preprocess(_load("dt50.jpg"))
    dets, meta = detect_raw_hexagons(color, gray)
    assert dets
    assert meta["score"] >= config.DETECTION_SCORE_MIN


def test_label_contour_scores_below_threshold():
    import numpy as np
    from block_detection_v2.models import Point2D

    color, gray = preprocess(_load("dt50.jpg"))
    edges, _ = detect_edges(gray)
    dets, meta = detect_raw_hexagons(color, gray)
    assert dets and meta["score"] >= config.DETECTION_SCORE_MIN

    tiny = {
        "A": Point2D(10, 10),
        "B": Point2D(20, 10),
        "C": Point2D(30, 12),
        "D": Point2D(30, 20),
        "E": Point2D(20, 22),
        "F": Point2D(10, 20),
    }
    roi = ROIBox(0, 0, 500, 400, np.ones((400, 500), dtype=np.uint8) * 255, 200000, 3)
    assert score_candidate(tiny, edges, roi) == 0.0


def test_hard_reject_small_area():
    import numpy as np
    from block_detection_v2.models import Point2D

    pts = {k: Point2D(100 + i * 5, 100 + i * 3) for i, k in enumerate("ABCDEF")}
    roi = ROIBox(0, 0, 200, 200, np.ones((200, 200), dtype=np.uint8) * 255, 40000, 3)
    edges = np.zeros((200, 200), dtype=np.uint8)
    assert score_candidate(pts, edges, roi) == 0.0


def test_hard_reject_low_area_ratio():
    import numpy as np
    from block_detection_v2.models import Point2D

    pts = {
        "A": Point2D(10, 10),
        "B": Point2D(30, 10),
        "C": Point2D(50, 12),
        "D": Point2D(50, 40),
        "E": Point2D(30, 42),
        "F": Point2D(10, 40),
    }
    roi = ROIBox(0, 0, 500, 400, np.ones((400, 500), dtype=np.uint8) * 255, 200000, 3)
    edges = np.zeros((400, 500), dtype=np.uint8)
    assert score_candidate(pts, edges, roi) == 0.0
