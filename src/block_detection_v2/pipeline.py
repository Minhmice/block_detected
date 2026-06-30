from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from . import config
from .edges import LineSegment, detect_edges
from .fit import fit_hexagon_from_lines
from .models import HexagonDetection
from .polygon import find_hexagons
from .roi import ROIBox, extract_cluster_roi, roi_from_bbox
from .score import score_candidate
from .yolo_detector import YoloBlockDetector

_yolo_detector: YoloBlockDetector | None = None


def _reset_yolo_detector() -> None:
    global _yolo_detector
    _yolo_detector = None


def _default_yolo() -> YoloBlockDetector:
    global _yolo_detector
    if _yolo_detector is None:
        _yolo_detector = YoloBlockDetector(
            model_path=config.YOLO_MODEL_PATH,
            conf=config.YOLO_CONF,
            iou=config.YOLO_IOU,
            device=config.YOLO_DEVICE,
        )
    return _yolo_detector


def _roi_lines(lines: List[LineSegment], roi: ROIBox) -> List[LineSegment]:
    out: List[LineSegment] = []
    h, w = roi.mask.shape[:2]
    for p1, p2 in lines:
        mx, my = int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2)
        if 0 <= my < h and 0 <= mx < w and roi.mask[my, mx]:
            out.append((p1, p2))
    return out


def _detect_hex_in_roi(
    color: np.ndarray,
    gray: np.ndarray,
    roi: ROIBox,
    edges: np.ndarray,
    lines: List[LineSegment],
) -> Tuple[Optional[HexagonDetection], dict]:
    """Fit + score hex inside one ROI; coordinates stay in full-frame space."""
    shape = color.shape[:2]
    masked = cv2.bitwise_and(edges, roi.mask)
    filtered = _roi_lines(lines, roi)
    points = fit_hexagon_from_lines(filtered or lines, roi, shape, edges=masked)
    if points is None:
        return None, {
            "stage": "fit",
            "lines": len(lines),
            "roi_lines": len(filtered),
            "roi_area": roi.area,
        }

    score = score_candidate(points, masked, roi, strict_topology=True)
    meta = {
        "stage": "ok",
        "lines": len(lines),
        "roi_lines": len(filtered),
        "roi_area": roi.area,
        "score": score,
    }
    if score < config.DETECTION_SCORE_MIN:
        return None, {**meta, "stage": "low_score"}

    det = HexagonDetection(points=points, contour_area=float(roi.area), score=score)
    return det, meta


def _detect_edge_roi(
    color: np.ndarray,
    gray: np.ndarray,
    edges: np.ndarray,
    lines: List[LineSegment],
) -> Tuple[List[HexagonDetection], dict]:
    shape = color.shape[:2]
    roi = extract_cluster_roi(edges, shape, block_mode=config.BLOCK_MODE)
    if roi is None:
        if config.USE_CONTOUR_FALLBACK:
            return find_hexagons(edges, shape), {"stage": "fallback", "lines": len(lines)}
        return [], {"stage": "roi", "lines": len(lines)}

    det, meta = _detect_hex_in_roi(color, gray, roi, edges, lines)
    meta = {**meta, "stage": "edge_roi" if meta.get("stage") != "ok" else "edge_roi"}
    if det is None:
        if config.USE_CONTOUR_FALLBACK and meta.get("stage") == "fit":
            return find_hexagons(edges, shape), {"stage": "fallback", "lines": len(lines)}
        return [], meta

    return [det], meta


def detect_raw_hexagons(
    color: np.ndarray,
    gray: np.ndarray,
    *,
    yolo_detector: YoloBlockDetector | None = None,
) -> Tuple[List[HexagonDetection], dict]:
    """YOLO-first ROI → fit → score; edge-CC fallback when YOLO misses."""
    edges, lines = detect_edges(gray)
    shape = color.shape[:2]

    if config.USE_YOLO_ROI:
        detector = yolo_detector if yolo_detector is not None else _default_yolo()
        boxes = detector.detect(color)
        if boxes:
            dets: List[HexagonDetection] = []
            best_meta: dict = {"stage": "yolo_roi", "lines": len(lines), "yolo_count": len(boxes)}
            yolo_boxes_meta = []
            for box in boxes[: config.MAX_BLOCKS]:
                roi = roi_from_bbox(box.x1, box.y1, box.x2, box.y2, shape)
                det, meta = _detect_hex_in_roi(color, gray, roi, edges, lines)
                yolo_boxes_meta.append(
                    {"xyxy": list(box.as_xyxy()), "confidence": box.confidence, "class_name": box.class_name}
                )
                if det is not None:
                    dets.append(det)
                    best_meta = {
                        **meta,
                        "stage": "yolo_roi",
                        "yolo_conf": box.confidence,
                        "yolo_count": len(boxes),
                        "yolo_accepted": len(dets),
                    }
            best_meta["yolo_boxes"] = yolo_boxes_meta
            if dets:
                best_meta["score"] = max(d.score for d in dets)
                return dets, best_meta
            return [], {**best_meta, "stage": "yolo_roi", "score": 0.0}

    return _detect_edge_roi(color, gray, edges, lines)


def reset_pipeline_cache() -> None:
    """Test helper — clear lazy YOLO singleton."""
    _reset_yolo_detector()
