from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from . import config

FrameShape = Tuple[int, int]


@dataclass
class ROIBox:
    x: int
    y: int
    w: int
    h: int
    mask: np.ndarray
    area: int
    block_mode: int = 3

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


def extract_cluster_roi(
    edges: np.ndarray,
    frame_shape: FrameShape,
    *,
    block_mode: int | None = None,
    pallet_frac: float | None = None,
) -> Optional[ROIBox]:
    """Isolate block-cluster silhouette; trim right for 3-block mode."""
    h, w = frame_shape
    mode = config.BLOCK_MODE if block_mode is None else block_mode
    pallet = config.ROI_PALLET_FRAC if pallet_frac is None else pallet_frac

    work = edges.copy()
    pallet_y = int(h * pallet)
    work[pallet_y:, :] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    merged = cv2.morphologyEx(work, cv2.MORPH_CLOSE, kernel, iterations=2)
    merged = cv2.dilate(merged, kernel, iterations=2)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(merged)
    best_idx = -1
    best_score = 0.0
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        if area < 800:
            continue
        cy = y + bh / 2.0
        if cy > h * 0.88:
            continue
        centrality = 1.0 - abs((x + bw / 2.0) - w / 2.0) / (w / 2.0)
        upper_bonus = 1.0 - (cy / h)
        score = area * (0.5 + 0.3 * centrality + 0.2 * upper_bonus)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx < 0:
        return None

    comp_mask = (labels == best_idx).astype(np.uint8) * 255
    x, y, bw, bh, area = stats[best_idx]

    pad = max(12, int(min(bw, bh) * 0.04))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(w, x + bw + pad)
    y1 = min(h, y + bh + pad)

    if mode == 3:
        full_w = x1 - x0
        trim = int(full_w * config.ROI_RIGHT_TRIM_FRAC)
        x1 = max(x0 + int(full_w * 0.45), x1 - trim)

    roi_mask = np.zeros((h, w), dtype=np.uint8)
    roi_mask[y0:y1, x0:x1] = 255
    roi_mask = cv2.bitwise_and(roi_mask, comp_mask)
    roi_mask = cv2.dilate(roi_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), 1)

    return ROIBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0, mask=roi_mask, area=int(area), block_mode=mode)


def roi_from_bbox(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    frame_shape: FrameShape,
    *,
    block_mode: int | None = None,
    pad_frac: float | None = None,
) -> ROIBox:
    """Build ROIBox from YOLO xyxy; rectangular mask with optional 3-block right trim."""
    h, w = frame_shape
    mode = config.BLOCK_MODE if block_mode is None else block_mode
    pad = config.YOLO_PAD_FRAC if pad_frac is None else pad_frac

    xa, xb = min(x1, x2), max(x1, x2)
    ya, yb = min(y1, y2), max(y1, y2)
    bw, bh = xb - xa, yb - ya
    pad_x = int(bw * pad)
    pad_y = int(bh * pad)
    x0 = max(0, xa - pad_x)
    y0 = max(0, ya - pad_y)
    x1c = min(w, xb + pad_x)
    y1c = min(h, yb + pad_y)

    if mode == 3:
        full_w = x1c - x0
        trim = int(full_w * config.ROI_RIGHT_TRIM_FRAC)
        x1c = max(x0 + int(full_w * 0.45), x1c - trim)

    roi_mask = np.zeros((h, w), dtype=np.uint8)
    roi_mask[y0:y1c, x0:x1c] = 255
    area = int(np.count_nonzero(roi_mask))

    return ROIBox(x=x0, y=y0, w=x1c - x0, h=y1c - y0, mask=roi_mask, area=area, block_mode=mode)
