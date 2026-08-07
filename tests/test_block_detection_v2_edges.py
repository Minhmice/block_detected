from __future__ import annotations

import cv2
import numpy as np
import pytest

from block_detection_v2 import config
from block_detection_v2.edges import detect_edges


@pytest.mark.parametrize(
    "raw",
    [
        np.array([[[1, 2, 3, 4]], [[5, 6, 7, 8]]], dtype=np.int32),
        np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int32),
    ],
)
def test_detect_edges_accepts_hough_output_layouts(monkeypatch, raw):
    gray = np.zeros((8, 8), dtype=np.uint8)
    edge_map = np.zeros_like(gray)
    monkeypatch.setattr(config, "USE_LSD", False)
    monkeypatch.setattr(cv2, "Canny", lambda *args, **kwargs: edge_map)
    monkeypatch.setattr(cv2, "morphologyEx", lambda image, *args, **kwargs: image)
    monkeypatch.setattr(cv2, "HoughLinesP", lambda *args, **kwargs: raw)

    _, lines = detect_edges(gray)

    assert lines == [((1, 2), (3, 4)), ((5, 6), (7, 8))]


def test_detect_edges_accepts_no_hough_lines(monkeypatch):
    gray = np.zeros((8, 8), dtype=np.uint8)
    edge_map = np.zeros_like(gray)
    monkeypatch.setattr(config, "USE_LSD", False)
    monkeypatch.setattr(cv2, "Canny", lambda *args, **kwargs: edge_map)
    monkeypatch.setattr(cv2, "morphologyEx", lambda image, *args, **kwargs: image)
    monkeypatch.setattr(cv2, "HoughLinesP", lambda *args, **kwargs: None)

    _, lines = detect_edges(gray)

    assert lines == []
