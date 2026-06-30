from __future__ import annotations

from pathlib import Path

import cv2

from block_detection_v2 import config
from block_detection_v2.edges import detect_edges
from block_detection_v2.preprocessing import preprocess
from block_detection_v2.roi import extract_cluster_roi

_DATASET = Path(__file__).resolve().parents[1] / "src" / "block_detection_v2" / "block_dataset"


def _load(name: str):
    path = _DATASET / name
    frame = cv2.imread(str(path))
    assert frame is not None, f"missing {path}"
    return frame


def test_extract_cluster_roi_dt50():
    color, gray = preprocess(_load("dt50.jpg"))
    edges, _ = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2])
    assert roi is not None
    assert roi.mask.sum() > 0
    assert roi.area > 800


def test_extract_cluster_roi_dt1():
    color, gray = preprocess(_load("dt1.jpg"))
    edges, _ = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2])
    assert roi is not None
    assert roi.block_mode == config.BLOCK_MODE


def test_three_block_right_trim():
    color, gray = preprocess(_load("dt50.jpg"))
    edges, _ = detect_edges(gray)
    roi3 = extract_cluster_roi(edges, color.shape[:2], block_mode=3)
    roi4 = extract_cluster_roi(edges, color.shape[:2], block_mode=4)
    assert roi3 is not None and roi4 is not None
    assert roi3.w <= roi4.w
