"""ROI extraction and edge preprocessing."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from .config import HexDetectorConfig
from .models import BBox

UInt8Array = NDArray[np.uint8]


def pad_bbox(bbox: BBox, ratio: float, frame_w: int, frame_h: int) -> BBox:
  return bbox.pad(ratio).clamp(frame_w, frame_h)


def crop_roi(
  frame: UInt8Array,
  bbox: BBox,
  crop_bottom_ratio: float,
) -> tuple[UInt8Array, BBox]:
  """Crop ROI and optionally remove bottom pallet band. Returns empty array if invalid."""
  x1, y1, x2, y2 = bbox.as_int_tuple()
  if x2 <= x1 or y2 <= y1:
    return np.empty((0, 0, 3), dtype=np.uint8), bbox

  roi = frame[y1:y2, x1:x2].copy()
  if roi.size == 0:
    return roi, bbox

  h = roi.shape[0]
  crop_rows = int(h * crop_bottom_ratio)
  if crop_rows > 0 and crop_rows < h:
    roi = roi[: h - crop_rows, :]

  effective = BBox(
    x1=float(x1),
    y1=float(y1),
    x2=float(x2),
    y2=float(y1 + roi.shape[0]),
  )
  return roi, effective


def preprocess_edges(roi: UInt8Array, cfg: HexDetectorConfig) -> UInt8Array:
  """Gray → CLAHE → GaussianBlur → Canny → morphology close."""
  if roi.size == 0:
    return np.empty((0, 0), dtype=np.uint8)

  gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
  clahe = cv2.createCLAHE(
    clipLimit=cfg.clahe_clip_limit,
    tileGridSize=cfg.clahe_tile_grid_size,
  )
  enhanced = clahe.apply(gray)
  blurred = cv2.GaussianBlur(enhanced, cfg.gaussian_kernel, cfg.gaussian_sigma)
  edges = cv2.Canny(blurred, cfg.canny_low, cfg.canny_high)
  k = cv2.getStructuringElement(cv2.MORPH_RECT, (cfg.morph_kernel_size, cfg.morph_kernel_size))
  closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, k, iterations=cfg.morph_iterations)
  return closed
