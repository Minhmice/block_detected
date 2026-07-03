"""Regression tests for the relational outer-boundary refactor.

Covers the 8 mandated scenarios:
  1. 2-block front -> seam between blocks must NOT be chosen as BE
  2. front + right         -> hex (side right)
  3. front + left          -> mirrored hex (side left)
  4. straight-on           -> rectangle
  5. strong pallet line    -> filtered out (not selected)
  6. text/logo noise edges -> topology not broken
  7. bbox offset/padding   -> same A-F (in ROI-relative terms)
  8. dt28/dt51/dt79-like   -> real-image smoke (no crash, valid structure)
"""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hex_detector.config import HexDetectorConfig
from hex_detector.detector import HexDetector, _CropAttemptResult, _roi_hex_to_frame
from hex_detector.lines import filter_lines
from hex_detector.models import (
    BBox,
    DetectionResult,
    HexPoints,
    LineGroups,
    LineSegment,
    ScoreBreakdown,
    YoloDetection,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _mock_edges(roi: np.ndarray, _cfg: HexDetectorConfig) -> np.ndarray:
    h, w = roi.shape[:2]
    return np.full((h, w), 255, dtype=np.uint8)


def _mock_no_lines(*_a):
    return []


def _cfg(**kw) -> HexDetectorConfig:
    base = dict(
        block_crop_bottom_ratios=(0.0,),
        max_crop_ratio_attempts=1,
        enable_mirrored_pass=False,
    )
    base.update(kw)
    return HexDetectorConfig(**base)


def _setup(stack: ExitStack, groups: LineGroups) -> None:
    stack.enter_context(patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines))
    stack.enter_context(patch("hex_detector.detector.merge_line_groups", return_value=groups))
    stack.enter_context(patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges))


def _run(detector: HexDetector, groups: LineGroups, bbox: BBox, track_id: int = 1) -> DetectionResult:
    with ExitStack() as stack:
        _setup(stack, groups)
        results = detector.detect_frame(
            np.zeros((300, 500, 3), dtype=np.uint8),
            [YoloDetection(track_id, bbox, 0.9)],
        )
    assert len(results) == 1
    return results[0]


# ---------------------------------------------------------------------------
# 1. Two-block front: seam must not be chosen as BE
# ---------------------------------------------------------------------------

def test_two_block_front_seam_not_chosen_as_be() -> None:
    # Verticals: 20 (true AF), 110 (INTERNAL SEAM), 180 (true BE).
    groups = LineGroups(
        vertical=[
            LineSegment(20, 20, 20, 180, group="vertical"),
            LineSegment(110, 20, 110, 180, group="vertical"),
            LineSegment(180, 20, 180, 180, group="vertical"),
        ],
        front_horizontal=[
            LineSegment(20, 20, 180, 20, group="front_horizontal"),
            LineSegment(20, 180, 180, 180, group="front_horizontal"),
        ],
        right_diagonal=[],
    )
    detector = HexDetector(_cfg(max_front_candidates=100))
    res = _run(detector, groups, BBox(0, 0, 200, 200))

    assert res.mode == "rectangle"
    b = res.points["B"]
    a = res.points["A"]
    assert a is not None and b is not None
    # BE must sit at the OUTER right boundary (~180), NOT on the seam (~110).
    assert b[0] == pytest.approx(180, abs=6), f"BE landed on seam: {b}"
    assert a[0] == pytest.approx(20, abs=6)


# ---------------------------------------------------------------------------
# 2. front + right -> hex
# ---------------------------------------------------------------------------

def test_front_plus_right_becomes_hex() -> None:
    # A genuine hex: front axis-aligned (40..160), side slanted out to CD at x=250.
    # The slanted side top (BC) means a full-width rectangle top would NOT be
    # supported by edges, so hex must win on edge support.
    groups = LineGroups(
        vertical=[
            LineSegment(40, 50, 40, 150, group="vertical"),    # AF
            LineSegment(160, 50, 160, 150, group="vertical"),  # BE
            LineSegment(250, 75, 250, 150, group="vertical"),  # CD (outer)
        ],
        front_horizontal=[
            LineSegment(40, 50, 160, 50, group="front_horizontal"),    # AB
            LineSegment(40, 150, 160, 150, group="front_horizontal"),  # FE
        ],
        right_diagonal=[
            LineSegment(160, 50, 250, 75, group="right_diagonal"),     # BC (recedes down-right, ~15deg)
            LineSegment(160, 150, 250, 150, group="right_diagonal"),   # ED (flat bottom)
        ],
    )

    def edges_from_groups(roi: np.ndarray, _cfg: HexDetectorConfig) -> np.ndarray:
        h, w = roi.shape[:2]
        canvas = np.zeros((h, w), dtype=np.uint8)
        for ln in groups.all_lines():
            cv2.line(canvas, (int(ln.x1), int(ln.y1)), (int(ln.x2), int(ln.y2)), 255, 2)
        return canvas

    detector = HexDetector(_cfg(max_front_candidates=100))
    with ExitStack() as stack:
        stack.enter_context(patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines))
        stack.enter_context(patch("hex_detector.detector.merge_line_groups", return_value=groups))
        stack.enter_context(patch("hex_detector.detector.preprocess_edges", side_effect=edges_from_groups))
        results = detector.detect_frame(
            np.zeros((300, 300, 3), dtype=np.uint8),
            [YoloDetection(1, BBox(0, 0, 300, 300), 0.9)],
        )
    assert len(results) == 1
    res = results[0]
    assert res.mode == "hex", res.reject_reason
    assert res.side == "right"
    for k in ("A", "B", "C", "D", "E", "F"):
        assert res.points[k] is not None


# ---------------------------------------------------------------------------
# 3. front + left -> mirrored hex (side left) — selection + un-flip logic
# ---------------------------------------------------------------------------

def _attempt(mirrored: bool, mode: str, score: float) -> _CropAttemptResult:
    bbox = BBox(0, 0, 200, 200)
    if mode == "hex":
        pts = HexPoints(A=(20, 20), B=(100, 20), C=(160, 30), D=(160, 170), E=(100, 180), F=(20, 180))
    else:
        pts = HexPoints(A=(20, 20), B=(180, 20), C=None, D=None, E=(180, 180), F=(20, 180))
    res = DetectionResult(
        track_id=1, mode=mode, points=pts.filled_for_mode(mode), score=score,
        roi_bbox=bbox.to_dict(), status="detected",
        score_breakdown=ScoreBreakdown(1.0, 1.0, 1.0, 1.0, 0.5, score),
    )
    return _CropAttemptResult(
        crop_ratio=0.0, result=res, raw_roi_points=pts, effective_bbox=bbox, mirrored=mirrored,
    )


def test_left_face_selected_as_mirrored_hex(monkeypatch) -> None:
    detector = HexDetector(_cfg(enable_mirrored_pass=True))

    def fake(self, **kw):
        return _attempt(kw["mirrored"], "hex" if kw["mirrored"] else "rectangle",
                        0.85 if kw["mirrored"] else 0.60)

    monkeypatch.setattr(HexDetector, "_detect_roi_for_crop", fake)
    res = detector.detect_roi(np.zeros((300, 300, 3), np.uint8), 1, BBox(0, 0, 200, 200), 300, 300)
    assert res.mode == "hex"
    assert res.side == "left"


def test_mirror_unflip_coordinates() -> None:
    pts = HexPoints(A=(10.0, 10.0), B=(90.0, 10.0), C=None, D=None, E=(90.0, 90.0), F=(10.0, 90.0))
    out = _roi_hex_to_frame(pts, BBox(0, 0, 100, 100), mirrored=True, roi_w=100)
    assert out.A == pytest.approx((90.0, 10.0))
    assert out.B == pytest.approx((10.0, 10.0))


# ---------------------------------------------------------------------------
# 4. straight-on view -> rectangle
# ---------------------------------------------------------------------------

def test_straight_on_view_is_rectangle() -> None:
    groups = LineGroups(
        vertical=[
            LineSegment(40, 20, 40, 180, group="vertical"),
            LineSegment(160, 20, 160, 180, group="vertical"),
        ],
        front_horizontal=[
            LineSegment(40, 20, 160, 20, group="front_horizontal"),
            LineSegment(40, 180, 160, 180, group="front_horizontal"),
        ],
        right_diagonal=[],
    )
    res = _run(HexDetector(_cfg()), groups, BBox(0, 0, 400, 400))
    assert res.mode == "rectangle"
    assert res.points["C"] is None and res.points["D"] is None


# ---------------------------------------------------------------------------
# 5. Strong pallet line filtered out
# ---------------------------------------------------------------------------

def test_pallet_line_filtered_out() -> None:
    cfg = HexDetectorConfig()
    roi_w = roi_h = 200
    pallet = LineSegment(40, 150, 160, 150, group="unknown")   # horizontal, low band
    block_vert = LineSegment(100, 40, 100, 160, group="unknown")
    kept = filter_lines([pallet, block_vert], roi_w, roi_h, cfg)
    kept_mids = [ln.midpoint() for ln in kept]
    assert (100.0, 100.0) in [(round(m[0]), round(m[1])) for m in kept_mids]
    assert all(abs(m[1] - 150) > 1 for m in kept_mids), "pallet line was not filtered"


# ---------------------------------------------------------------------------
# 6. Text/logo noise must not break topology
# ---------------------------------------------------------------------------

def test_text_noise_does_not_break_topology() -> None:
    groups = LineGroups(
        vertical=[
            LineSegment(20, 20, 20, 180, group="vertical"),
            LineSegment(110, 20, 110, 180, group="vertical"),   # seam-ish noise
            LineSegment(180, 20, 180, 180, group="vertical"),
        ],
        front_horizontal=[
            LineSegment(20, 20, 180, 20, group="front_horizontal"),
            LineSegment(20, 180, 180, 180, group="front_horizontal"),
            LineSegment(60, 95, 120, 95, group="front_horizontal"),   # logo text stroke
            LineSegment(70, 110, 130, 110, group="front_horizontal"),  # logo text stroke
        ],
        right_diagonal=[
            LineSegment(80, 60, 120, 75, group="right_diagonal"),   # single stray diagonal
        ],
    )
    res = _run(HexDetector(_cfg(max_front_candidates=100)), groups, BBox(0, 0, 200, 200))
    assert res.mode == "rectangle"   # single diagonal cannot form a valid hex
    a, b = res.points["A"], res.points["B"]
    assert a is not None and b is not None
    assert a[0] == pytest.approx(20, abs=6)
    assert b[0] == pytest.approx(180, abs=6)


# ---------------------------------------------------------------------------
# 7. bbox offset/padding -> same ROI-relative A-F
# ---------------------------------------------------------------------------

def test_bbox_offset_yields_same_relative_points() -> None:
    groups = LineGroups(
        vertical=[
            LineSegment(20, 20, 20, 180, group="vertical"),
            LineSegment(180, 20, 180, 180, group="vertical"),
        ],
        front_horizontal=[
            LineSegment(20, 20, 180, 20, group="front_horizontal"),
            LineSegment(20, 180, 180, 180, group="front_horizontal"),
        ],
        right_diagonal=[],
    )
    # padding must be 0 so bbox maps 1:1 to ROI for a clean comparison
    cfg = _cfg(bbox_padding_ratio=0.0)
    res_a = _run(HexDetector(cfg), groups, BBox(0, 0, 200, 200), track_id=1)
    res_b = _run(HexDetector(cfg), groups, BBox(50, 30, 250, 230), track_id=2)

    for k in ("A", "B", "E", "F"):
        pa, pb = res_a.points[k], res_b.points[k]
        assert pa is not None and pb is not None
        assert pb[0] - 50 == pytest.approx(pa[0], abs=3), f"{k}.x offset mismatch"
        assert pb[1] - 30 == pytest.approx(pa[1], abs=3), f"{k}.y offset mismatch"


# ---------------------------------------------------------------------------
# 8. dt-like real-image smoke tests (no YOLO — feed full frame as one bbox)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["dt28.jpg", "dt51.jpg", "dt79.jpg"])
def test_dtlike_real_image_smoke(name: str) -> None:
    cv2 = pytest.importorskip("cv2")
    img_path = ROOT / "block_dataset" / name
    if not img_path.exists():
        pytest.skip(f"{name} not present")
    frame = cv2.imread(str(img_path))
    if frame is None:
        pytest.skip(f"cannot read {name}")
    h, w = frame.shape[:2]
    detector = HexDetector(HexDetectorConfig(enable_mirrored_pass=True))
    results = detector.detect_frame(frame, [YoloDetection(1, BBox(0, 0, float(w), float(h)), 0.9)])
    # Contract: never crash, always structurally valid.
    for r in results:
        assert set(r.points.keys()) == {"A", "B", "C", "D", "E", "F"}
        assert r.mode in ("hex", "rectangle", "not_detected")
        assert r.side in ("left", "right")
