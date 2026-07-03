"""Unit tests for hex_detector geometry."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hex_detector.config import HexDetectorConfig
from hex_detector.geometry import (
  is_convex_polygon,
  line_intersection,
  parallelism_score,
  points_from_lines,
  polygon_area,
  should_use_rectangle_mode,
  validate_hex_points,
)
from hex_detector.models import HexPoints, LineSegment


def _hex_lines() -> tuple[LineSegment, ...]:
  """Synthetic lines forming a convex hex."""
  af = LineSegment(50, 10, 50, 180, group="vertical")
  be = LineSegment(110, 10, 110, 180, group="vertical")
  cd = LineSegment(140, 10, 140, 180, group="vertical")
  ab = LineSegment(10, 50, 130, 50, group="front_horizontal")
  fe = LineSegment(10, 150, 130, 150, group="front_horizontal")
  bc = LineSegment(95, 46, 150, 64, group="right_diagonal")
  ed = LineSegment(95, 150, 150, 150, group="right_diagonal")
  return af, be, cd, ab, fe, bc, ed


def test_line_intersection_finds_corner() -> None:
  h = LineSegment(0, 10, 100, 10)
  v = LineSegment(50, 0, 50, 100)
  pt = line_intersection(h, v)
  assert pt is not None
  assert pt[0] == pytest.approx(50.0)
  assert pt[1] == pytest.approx(10.0)


def test_parallel_lines_no_intersection() -> None:
  a = LineSegment(0, 0, 10, 0)
  b = LineSegment(0, 5, 10, 5)
  assert line_intersection(a, b) is None


def test_convex_hex_polygon() -> None:
  pts = points_from_lines(*_hex_lines())
  assert pts is not None
  poly = [pts.A, pts.B, pts.C, pts.D, pts.E, pts.F]
  assert all(p is not None for p in poly)
  assert is_convex_polygon(poly)  # type: ignore[arg-type]


def test_validate_x_ordering_and_front_area() -> None:
  pts = points_from_lines(*_hex_lines())
  assert pts is not None
  cfg = HexDetectorConfig(min_front_area_ratio=0.01, min_right_width_ratio=0.01)
  ok, reason = validate_hex_points(pts, 200, 200, cfg)
  assert ok, reason
  assert pts.A and pts.B and pts.C
  assert pts.A[0] < pts.B[0] < pts.C[0]


def test_parallelism_score_high_for_regular_hex() -> None:
  pts = points_from_lines(*_hex_lines())
  assert pts is not None
  score = parallelism_score(pts, HexDetectorConfig())
  assert score > 0.7


def test_rectangle_mode_when_right_narrow() -> None:
  pts = HexPoints(
    A=(10, 10),
    B=(90, 10),
    C=(95, 20),
    D=(95, 100),
    E=(90, 100),
    F=(10, 100),
  )
  cfg = HexDetectorConfig(rectangle_mode_right_width_ratio=0.15)
  assert should_use_rectangle_mode(pts, 200, cfg)


def test_polygon_area_positive() -> None:
  square = [(0, 0), (10, 0), (10, 10), (0, 10)]
  assert polygon_area(square) == pytest.approx(100.0)
