# Phase 17: ROI-fit-score detection pipeline — Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 11
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/block_detection_v2/roi.py` | service | transform | `.planning/spikes/shared/block_spike_lib.py` | exact (spike port) |
| `src/block_detection_v2/fit.py` | service | transform | `.planning/spikes/shared/block_spike_lib.py` | exact (spike port) |
| `src/block_detection_v2/score.py` | service | transform | `.planning/spikes/shared/block_spike_lib.py` + `polygon.py` | exact (spike port) |
| `src/block_detection_v2/benchmark.py` | utility | batch | `.planning/spikes/004-dataset-benchmark/run.py` | exact (spike port) |
| `src/block_detection_v2/main.py` | controller | streaming | `block_spike_lib.process_image()` + current `main.py` | exact |
| `src/block_detection_v2/config.py` | config | — | `src/block_detection_v2/config.py` | exact |
| `src/block_detection_v2/models.py` | model | — | `models.py` + `block_spike_lib.ROIBox` | exact |
| `src/block_detection_v2/polygon.py` | service (fallback) | transform | current `polygon.py` (demote, don't delete) | exact |
| `src/block_detection_v2/edges.py` | service | transform | current `edges.py` (unchanged) | exact |
| `tests/test_block_detection_v2_*.py` | test | batch | `tests/conftest.py` + `tests/test_boxes.py` | role-match |
| `src/block_detection_v2/polygon.py` `_detection_score` | — | — | replace caller only; scoring moves to `score.py` | partial |

## Pattern Assignments

### `src/block_detection_v2/roi.py` (service, transform)

**Analog:** `.planning/spikes/shared/block_spike_lib.py` (primary); module shell from `src/block_detection_v2/edges.py`

**Imports pattern** (`edges.py` lines 1-8):
```python
from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from . import config
```

**ROIBox dataclass** (`block_spike_lib.py` lines 30-41) — move to `models.py` or re-export from `roi.py`:
```python
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
```

**Core ROI extraction** (`block_spike_lib.py` lines 124-196) — port verbatim logic; replace magic numbers with `config`:
```python
def extract_cluster_roi(
    edges: np.ndarray,
    frame_shape: Tuple[int, int],
    *,
    block_mode: int = 3,
    pallet_frac: float = 0.78,
    log: Optional[ForensicLog] = None,
) -> Optional[ROIBox]:
    """Isolate block-cluster silhouette; trim right for 3-block mode."""
    h, w = frame_shape
    work = edges.copy()
    pallet_y = int(h * pallet_frac)
    work[pallet_y:, :] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    merged = cv2.morphologyEx(work, cv2.MORPH_CLOSE, kernel, iterations=2)
    merged = cv2.dilate(merged, kernel, iterations=2)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(merged)
    # ... best component scoring by area × centrality × upper_bonus ...

    if block_mode == 3:
        full_w = x1 - x0
        trim = int(full_w * 0.22)  # → config.ROI_RIGHT_TRIM_FRAC
        x1 = max(x0 + int(full_w * 0.45), x1 - trim)

    roi_mask = np.zeros((h, w), dtype=np.uint8)
    roi_mask[y0:y1, x0:x1] = 255
    roi_mask = cv2.bitwise_and(roi_mask, comp_mask)
    return ROIBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0, mask=roi_mask, area=int(area), block_mode=block_mode)
```

**Config wiring** — read defaults from `config.BLOCK_MODE`, `config.ROI_PALLET_FRAC`, `config.ROI_RIGHT_TRIM_FRAC` instead of literals.

**Error handling** — return `None` on failure (no exceptions); optional log hook can be dropped in production or gated behind `config.DEBUG_*`.

---

### `src/block_detection_v2/fit.py` (service, transform)

**Analog:** `.planning/spikes/shared/block_spike_lib.py` lines 198-366

**Imports pattern** (`block_spike_lib.py` lines 1-14, adapted):
```python
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from . import config
from .models import Point2D
from .roi import ROIBox

Point = Tuple[float, float]
LineSegment = Tuple[Point, Point]
LABELS = "ABCDEF"
```

**Line utilities** (`block_spike_lib.py` lines 104-114, 198-260) — private helpers at module top:
```python
def _line_angle(p1: Point, p2: Point) -> float:
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0

def _merge_lines_by_angle(lines: List[LineSegment], angle_tol: float = 12.0, min_len: float = 25.0) -> List[LineSegment]:
    # bucket by angle, merge endpoints to bounding segment
    ...

def _dominant_angles(lines: List[LineSegment], bins: int = 18) -> List[float]:
    # length-weighted histogram peaks — NOT fixed 0°/35°/90° families
    ...
```

**ROI seed** (`block_spike_lib.py` lines 262-281):
```python
def _hex_from_roi(roi: ROIBox) -> Dict[str, Point2D]:
    """Seed A–F from ROI box with 3-block isometric proportions."""
    x, y, w, h = roi.x, roi.y, roi.w, roi.h
    inset_x = w * 0.06
    inset_y = h * 0.08
    mid_x = x + w * 0.52
    # A,B,C top row; D,E,F bottom row
    return {"A": Point2D(*a), "B": Point2D(*b), ...}
```

**Refine + snap** (`block_spike_lib.py` lines 284-336, 339-366):
```python
def _snap_point_to_edges(pt: Point, edges: np.ndarray, radius: int = 12) -> Point:
  # search (2*radius+1)² neighborhood for max edge pixel

def fit_hexagon_from_lines(
    lines: List[LineSegment],
    roi: ROIBox,
    frame_shape: Tuple[int, int],
    edges: Optional[np.ndarray] = None,
) -> Optional[Dict[str, Point2D]]:
    seed = _hex_from_roi(roi)
    points = _refine_with_lines(seed, lines, edges or np.zeros(frame_shape, dtype=np.uint8), roi)
    if not validate_topology(points, strict=False):
        points = seed
    if not validate_topology(points, strict=False):
        return None
    return points
```

**Reuse topology from `score.py`** — import `validate_topology` from `score` (or shared `topology.py` if split); spike keeps it in same file.

**Type alignment with `edges.py`** — import `LineSegment` from `edges` to avoid duplicate aliases:
```python
from .edges import LineSegment
```

---

### `src/block_detection_v2/score.py` (service, transform)

**Analog:** `.planning/spikes/shared/block_spike_lib.py` lines 368-423; reject pattern from `polygon.py` lines 129-201

**Imports pattern:**
```python
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np

from . import config
from .models import Point2D
from .roi import ROIBox

LABELS = "ABCDEF"
```

**Topology validation** (`block_spike_lib.py` lines 368-380) — strict E-row at accept time per CONTEXT D-04:
```python
def validate_topology(points: Dict[str, Point2D], *, strict: bool = False) -> bool:
    a, b, c, d, e, f = (points[k].as_tuple() for k in LABELS)
    if not (a[0] < b[0] < c[0] and f[0] < e[0] < d[0]):
        return False
    top_y = (a[1] + b[1] + c[1]) / 3.0
    bot_y = (d[1] + e[1] + f[1]) / 3.0
    if top_y >= bot_y - 15:
        return False
    if strict and e[1] < top_y + (bot_y - top_y) * 0.25:
        return False
    if _polygon_area([a, b, c, d, e, f]) < 2000:
        return False
    return True
```

**Composite score** (`block_spike_lib.py` lines 383-423):
```python
def edge_support(points: Dict[str, Point2D], edges: np.ndarray, sample_step: int = 4) -> float:
    order = ["A", "B", "C", "D", "E", "F", "A"]
    # sample along hex perimeter; 5×5 patch max > 0 counts as hit

def score_candidate(
    points: Dict[str, Point2D],
    edges: np.ndarray,
    roi: ROIBox,
    *,
    strict_topology: bool = True,
) -> float:
    hex_area = _polygon_area([points[k].as_tuple() for k in LABELS])
    area_ratio = min(1.0, hex_area / max(roi.area, 1))
    support = edge_support(points, edges)
    topo = 1.0 if validate_topology(points, strict=strict_topology) else 0.0
    if hex_area < config.SCORE_HEX_AREA_MIN:  # 3500
        return 0.0
    if area_ratio < config.SCORE_AREA_RATIO_MIN:  # 0.12
        return 0.0
    return float(0.35 * area_ratio + 0.45 * support + 0.20 * topo)
```

**Legacy contrast** — old `polygon._detection_score` (lines 129-149) used convex_ratio + face_ratio without ROI; do **not** extend it. Keep `find_hexagons` gated behind optional fallback flag only.

---

### `src/block_detection_v2/main.py` (controller, streaming)

**Analog:** `block_spike_lib.process_image()` lines 458-492; preserve `process_frame` → `MultiTracker` shell from current `main.py` lines 27-50

**Bug to fix** (current `main.py` line 30):
```python
edges, _lines = detect_edges(gray)  # WRONG — discards lines
```

**New pipeline** (RESEARCH + `block_spike_lib.process_image`):
```python
def process_frame(frame, tracker: MultiTracker) -> tuple[List[BlockResult], dict]:
    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=config.BLOCK_MODE)
    if roi is None:
        raw: List[HexagonDetection] = []
    else:
        masked = cv2.bitwise_and(edges, roi.mask)
        roi_lines = [
            seg for seg in lines
            if roi.mask[int((seg[0][1] + seg[1][1]) / 2), int((seg[0][0] + seg[1][0]) / 2)] > 0
        ]
        points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked)
        if points is None:
            raw = []
        else:
            score = score_candidate(points, masked, roi, strict_topology=True)
            if score >= config.DETECTION_SCORE_MIN:
                raw = [HexagonDetection(points=points, contour_area=roi.area, score=score)]
            else:
                raw = []
    stable = tracker.update(raw)
    # ... compute_geometry → BlockResult unchanged ...
```

**Optional contour fallback** (CONTEXT D-05 discretion):
```python
if not raw and config.USE_CONTOUR_FALLBACK:
    raw = find_hexagons(edges, color.shape[:2])
```

**Imports to add:**
```python
from .fit import fit_hexagon_from_lines
from .roi import extract_cluster_roi
from .score import score_candidate
```

---

### `src/block_detection_v2/config.py` (config)

**Analog:** current `config.py` — flat module-level constants with `Path` for package dir

**Additions** (RESEARCH lines 38-44):
```python
BLOCK_MODE = 3
ROI_PALLET_FRAC = 0.78
ROI_RIGHT_TRIM_FRAC = 0.22
SCORE_AREA_RATIO_MIN = 0.12
SCORE_HEX_AREA_MIN = 3500
DETECTION_SCORE_MIN = 0.42  # was 0.38

USE_CONTOUR_FALLBACK = False  # optional per CONTEXT D-05 discretion
```

**Pattern** (`config.py` lines 1-11):
```python
from __future__ import annotations

from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
IMAGE_DIR = str(_PKG_DIR / "block_dataset")
```

---

### `src/block_detection_v2/models.py` (model)

**Analog:** current `models.py` + `block_spike_lib.ROIBox`

**Existing dataclass pattern** (`models.py` lines 9-25):
```python
@dataclass
class Point2D:
    x: float
    y: float

    def as_tuple(self) -> Point:
        return (self.x, self.y)

@dataclass
class HexagonDetection:
    points: Dict[str, Point2D]
    contour_area: float
    score: float = 1.0
```

**Add ROIBox** — same fields as spike; `mask` stays `np.ndarray` (import numpy in models or keep ROIBox in `roi.py` and export via `__init__.py`; prefer `models.py` only if numpy already used elsewhere — currently models.py has no numpy, so **keep ROIBox in `roi.py`** to match spike split).

---

### `src/block_detection_v2/benchmark.py` (utility, batch)

**Analog:** `.planning/spikes/004-dataset-benchmark/run.py` (full file); helpers from `block_spike_lib` lines 96-101, 425-456

**Dataset listing** (`block_spike_lib.py` lines 96-101):
```python
def dataset_dir() -> Path:
    return SRC_ROOT / "block_detection_v2" / "block_dataset"

def list_dataset() -> List[Path]:
    return sorted(dataset_dir().glob("dt*.jpg"), key=lambda p: int(p.stem[2:]))
```

**Per-image processing** — call production modules, not spike lib:
```python
def process_image(path: Path) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False, "error": "read_failed"}
    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=config.BLOCK_MODE)
    # ... same pipeline as main.process_frame ...
    return {"file": path.name, "ok": score >= config.DETECTION_SCORE_MIN, "score": score, ...}
```

**Benchmark harness** (`004 run.py` lines 62-94):
```python
def main() -> None:
    out_dir = Path(__file__).resolve().parent / "benchmark_output" / "overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = list_dataset()
    results = [render_overlay(p, out_dir) for p in paths]
    summary = {
        "total": len(results),
        "accepted": len(ok),
        "accept_rate": len(ok) / max(len(results), 1),
        "fail_roi": len(fail_roi),
        "fail_fit": len(fail_fit),
        "low_score": len(low_score),
    }
    report = {"summary": summary, "failures": [...], "results": results}
    # write benchmark.json
```

**Entry point** — `if __name__ == "__main__": main()` or expose via `python -m block_detection_v2.benchmark`.

**Overlay drawing** — port `draw_hexagon` / `draw_roi` from `block_spike_lib.py` lines 425-456 into `benchmark.py` or `renderer.py` debug helpers; benchmark-only is fine.

---

### `src/block_detection_v2/polygon.py` (service fallback, transform)

**Analog:** current file — demote, minimal edits

**Keep public API** (`polygon.py` lines 207-231):
```python
def find_hexagons(edges: np.ndarray, frame_shape: tuple[int, int]) -> List[HexagonDetection]:
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    raw = _collect_candidates(contours)
    # ... NMS by center distance ...
```

**Do not delete** `_order_hexagon`, `_detection_score` — used only when `USE_CONTOUR_FALLBACK=True`. Add module docstring noting legacy path.

---

### `tests/test_block_detection_v2_roi.py` (and fit/score/bench) (test, batch)

**Analog:** `tests/conftest.py` + `tests/test_boxes.py`; spike single-image runs from `001-roi-silhouette/run.py`

**Path setup** (`conftest.py` lines 1-10):
```python
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
```

**Test style** (`test_boxes.py` lines 1-5):
```python
"""Tests for block_detection_v2 ROI extraction."""

from block_detection_v2.roi import extract_cluster_roi
from block_detection_v2.preprocessing import preprocess
from block_detection_v2.edges import detect_edges
```

**ROI unit test pattern** (from spike 001 `run_one`, lines 27-67):
```python
def test_extract_cluster_roi_dt50():
    path = Path("src/block_detection_v2/block_dataset/dt50.jpg")
    frame = cv2.imread(str(path))
    color, gray = preprocess(frame)
    edges, _ = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3)
    assert roi is not None
    assert roi.mask.sum() > 0
    assert roi.area > 800
```

**Score unit test** (from spike 003 — legacy FP rejection):
```python
def test_label_contour_scores_below_threshold():
    # run find_hexagons on edges; assert best score < config.DETECTION_SCORE_MIN
    # OR assert new pipeline score on label-sized hex < 0.42
```

**Benchmark integration** (RESEARCH validation table):
```python
def test_benchmark_accept_rate():
    from block_detection_v2.benchmark import run_benchmark
    summary = run_benchmark(write_overlays=False)
    assert summary["accept_rate"] >= 0.80
```

---

## Shared Patterns

### Module header and imports
**Source:** `src/block_detection_v2/edges.py`, `preprocessing.py`
**Apply to:** `roi.py`, `fit.py`, `score.py`, `benchmark.py`
```python
from __future__ import annotations

from . import config
from .models import Point2D, HexagonDetection
```

### Point2D + ABCDEF dict contract
**Source:** `src/block_detection_v2/models.py` lines 9-25; `tracker.py` lines 24-42
**Apply to:** all detection outputs before `MultiTracker.update`
```python
# Tracker expects Dict[str, Point2D] with keys "ABCDEF"
for key in "ABCDEF":
    dx = raw[key].x - self._ema[key].x
```

### HexagonDetection → BlockResult bridge
**Source:** `src/block_detection_v2/main.py` lines 34-47
**Apply to:** `main.py` only (unchanged downstream)
```python
geo = compute_geometry(det.points)
blocks.append(BlockResult(
    points=det.points,
    center=geo.center,
    front_width=geo.front_width,
    right_width=geo.right_width,
    yaw_deg=geo.yaw_deg,
    score=det.score,
    geometry=geo,
))
```

### Preprocess → edges entry
**Source:** `block_spike_lib.process_image` lines 463-465
**Apply to:** `main.py`, `benchmark.py`, all tests
```python
color, gray = preprocess(frame)
edges, lines = detect_edges(gray)
```

### ROI-masked line filter
**Source:** `block_spike_lib.process_image` lines 469-475
**Apply to:** `main.py`, `benchmark.py`
```python
roi_lines = []
for p1, p2 in lines:
    mx = (p1[0] + p2[0]) / 2.0
    my = (p1[1] + p2[1]) / 2.0
    if roi.mask[int(my), int(mx)] > 0:
        roi_lines.append((p1, p2))
points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked)
```

### Config-driven thresholds (no magic numbers in pipeline)
**Source:** `src/block_detection_v2/config.py`; CONTEXT D-04
**Apply to:** `score.py`, `main.py`, `roi.py`
```python
if score >= config.DETECTION_SCORE_MIN:
    ...
```

### Spike code as canonical implementation
**Source:** `.planning/spikes/shared/block_spike_lib.py`
**Apply to:** `roi.py`, `fit.py`, `score.py` — port functions directly; diff should be mostly import paths + config constants + removal of `ForensicLog` / `sys.path` hacks.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | All planned files have codebase or spike analogs |

**Note:** Skill reference markdown files (`references/roi-silhouette.md`, etc.) are cited in CONTEXT but not present on disk; use `block_spike_lib.py` and spike `run.py` scripts as canonical sources.

---

## Metadata

**Analog search scope:** `src/block_detection_v2/`, `.planning/spikes/shared/`, `.planning/spikes/00*-*/run.py`, `tests/`
**Files scanned:** ~25
**Pattern extraction date:** 2026-06-29

**Integration order (from skill):**
1. `roi.py` + `config.py` constants
2. `fit.py` + wire lines in `main.py`
3. `score.py`
4. `main.py` full pipeline
5. `benchmark.py` + tests

**Unchanged modules (CONTEXT D-05):** `tracker.py`, `renderer.py`, `geometry.py`, `image_source.py`, `preprocessing.py`, `edges.py`
