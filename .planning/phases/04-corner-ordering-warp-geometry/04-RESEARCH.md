# Phase 4: Corner Ordering, Warp & Geometry - Research

**Researched:** 2026-05-31 [VERIFIED: user environment context]
**Domain:** OpenCV quadrilateral geometry, deterministic corner ordering, perspective warping, and pixel pose fields [VERIFIED: .planning/ROADMAP.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
**Confidence:** MEDIUM - OpenCV/NumPy APIs are high confidence; the classifier crop-orientation contract is medium confidence because Phase 5 is not specified yet [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; VERIFIED: .planning/ROADMAP.md]

## User Constraints

No Phase 4 `CONTEXT.md` exists, so there are no additional locked decisions, discretion notes, or deferred ideas from `/gsd-discuss-phase`. [VERIFIED: `gsd-tools.cjs init phase-op 4` returned `has_context=false`]

### Locked Decisions

- Phase 4 goal is: each candidate yields consistently ordered corners, a canonical face warp, and pixel pose geometry. [VERIFIED: .planning/ROADMAP.md]
- Phase 4 depends on Phase 3. [VERIFIED: .planning/ROADMAP.md]
- Phase 4 must address GEO-03, GEO-04, and GEO-05. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Phase 4 consumes unordered square candidates from Phase 3 and produces ordered geometry plus warped face crops. [VERIFIED: user prompt; VERIFIED: .planning/phases/03-preprocess-contour-detection/03-RESEARCH.md]
- Corners must be output in top-left, top-right, bottom-right, bottom-left order regardless of block rotation in the frame. [VERIFIED: .planning/ROADMAP.md]
- The warp must be canonical 128x128 or 160x160 and suitable for classification. [VERIFIED: .planning/REQUIREMENTS.md]
- `center_px` equals the mean of ordered corners, and `angle_deg` is derived from the top-edge vector `TR - TL`. [VERIFIED: .planning/ROADMAP.md]
- v1 forbids ArUco and AprilTag markers on blocks. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md]

### Claude's Discretion

- No Phase 4 discretion section exists; module naming, dataclass naming, geometry validation thresholds, and deterministic tie-breaks are planner choices constrained by existing project code and OpenCV APIs. [VERIFIED: `gsd-tools.cjs init phase-op 4`; VERIFIED: src/block_detected/detector.py; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
- Use 128x128 as the default canonical warp because CLAUDE.md says later classification should operate on a 128x128 warp. [VERIFIED: CLAUDE.md]

### Deferred Ideas (OUT OF SCOPE)

- CNN/TFLite classification is Phase 5. [VERIFIED: .planning/ROADMAP.md]
- Calibration and pixel-to-robot pickup pose are Phase 6. [VERIFIED: .planning/ROADMAP.md]
- Full reject integration and mapping geometry failures to `DetectionStatus.INVALID_GEOMETRY` are Phase 7, although Phase 4 should expose enough validation metadata for that later mapping. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Multi-block scene graphs and temporal filtering are v2 runtime requirements, not Phase 4 work. [VERIFIED: .planning/REQUIREMENTS.md]

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEO-03 | Order corners consistently: top-left, top-right, bottom-right, bottom-left. [VERIFIED: .planning/REQUIREMENTS.md] | Use a pure-NumPy deterministic ordering helper that validates a `(4, 2)` finite point array, sorts vertices around the centroid, then rotates the cyclic order to the image-space top edge. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html; CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] |
| GEO-04 | `warpPerspective` face to canonical 128x128 or 160x160 for classification. [VERIFIED: .planning/REQUIREMENTS.md] | Use `cv2.getPerspectiveTransform` with four ordered source points and fixed destination points, then `cv2.warpPerspective(frame_bgr, M, (128, 128), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; VERIFIED: CLAUDE.md] |
| GEO-05 | Compute `center_px` as mean of corners and `angle_deg` from top edge. [VERIFIED: .planning/REQUIREMENTS.md] | Use `np.mean(ordered, axis=0, dtype=np.float64)` for center and `np.degrees(np.arctan2(tr_y - tl_y, tr_x - tl_x))` for angle. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] |

</phase_requirements>

## Summary

Phase 4 should add a small deterministic `src/block_detected/geometry.py` layer that consumes Phase 3 `SquareCandidate.approx_xy` points and the original 640x480 BGR frame, then returns `FaceGeometry` containing ordered corners, `CornersPx`, `center_px`, `angle_deg`, `face_area_px`, `bbox_xywh`, a 128x128 BGR face crop, and the 3x3 perspective matrix. [VERIFIED: src/block_detected/detector.py; VERIFIED: src/block_detected/detection_contract.py; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

The core implementation should use NumPy for point ordering and scalar geometry, and OpenCV for homography and image warping. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] Do not use `cv2.minAreaRect(...)[2]` as `angle_deg`, because OpenCV documents that `minAreaRect` angles are constrained to `[-90, 0)` and the measured edge changes as the rectangle rotates. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] Do not use the old sum/difference corner-ordering method as the only ordering rule, because duplicate sums or differences can produce incorrect point assignment. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**Primary recommendation:** Use fixed 128x128 BGR warps, center by float64 mean, angle from the ordered top edge, and a robust in-repo corner-ordering helper with rotation/permutation tests before any integration into `detect_block`. [VERIFIED: CLAUDE.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

## Project Constraints (from CLAUDE.md)

- The project is a Raspberry Pi / edge vision pipeline that detects four cube blocks without ArUco markers. [VERIFIED: CLAUDE.md]
- The core value is reliable block ID plus correctly ordered corners and angle for robot pickup, not only a bounding box. [VERIFIED: CLAUDE.md]
- The technical stack is Python 3, OpenCV, TensorFlow Lite INT8, and Pi-compatible runtime. [VERIFIED: CLAUDE.md]
- Resolution is 640x480 locked where possible. [VERIFIED: CLAUDE.md]
- Latency must suit a robot pick cycle, and later classification should operate on a 128x128 warp rather than a full-frame heavy model. [VERIFIED: CLAUDE.md]
- Output must conform to the existing `DetectionResult` contract in `detection_contract.py`. [VERIFIED: CLAUDE.md; VERIFIED: src/block_detected/detection_contract.py]
- GSD workflow enforcement says file-changing work should happen through GSD entry points unless explicitly bypassed. [VERIFIED: CLAUDE.md]
- No project-local skills were found under `.claude/skills/` or `.agents/skills/`. [VERIFIED: local `find .claude/skills .agents/skills -maxdepth 2 -name SKILL.md`]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | Project requires `>=3.11`; local host is 3.14.4; target Pi stack is 3.11.x. [VERIFIED: pyproject.toml; VERIFIED: local `python3 --version`; VERIFIED: .planning/research/STACK.md] | Runtime for geometry dataclasses, tests, and integration. [VERIFIED: CLAUDE.md] | Existing package and prior phases are Python modules. [VERIFIED: src/block_detected/detection_contract.py; VERIFIED: src/block_detected/camera.py] |
| OpenCV Python (`opencv-python`) | Latest PyPI: 4.13.0.92, first upload 2026-02-05; project dev extra allows `>=4.11,<4.14`. [VERIFIED: `python3 -m pip index versions opencv-python`; VERIFIED: PyPI JSON probe; VERIFIED: pyproject.toml] | `getPerspectiveTransform`, `warpPerspective`, `contourArea`, and optional debug drawing. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | OpenCV provides the homography and warp APIs required by GEO-04. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| NumPy | Latest PyPI: 2.4.6, first upload 2026-05-18; project dev extra allows `>=2,<3`. [VERIFIED: `python3 -m pip index versions numpy`; VERIFIED: PyPI JSON probe; VERIFIED: pyproject.toml] | Point arrays, centroid/mean, angle math, synthetic fixtures, and array assertions. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | Phase 3 `SquareCandidate.approx_xy` is already a NumPy array in the current worktree. [VERIFIED: src/block_detected/detector.py] |
| pytest | Latest PyPI: 9.0.3, first upload 2026-04-07; project dev extra requires `>=9`. [VERIFIED: `python3 -m pip index versions pytest`; VERIFIED: PyPI JSON probe; VERIFIED: pyproject.toml] | Parametrized permutation/rotation tests and crop-shape tests. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html] | Existing Phase 2/3 tests use pytest-style assertions and fixtures. [VERIFIED: tests/test_camera_source.py; VERIFIED: tests/test_detector.py] |
| Existing contract dataclasses | In-repo `PointPx`, `CornersPx`, `BoundingBoxPx`. [VERIFIED: src/block_detected/detection_contract.py] | Convert geometry output into contract-ready pixel objects. [VERIFIED: src/block_detected/detection_contract.py] | The public `DetectionResult` contract already validates geometry fields. [VERIFIED: src/block_detected/detection_contract.py] |

### Supporting

| Library / API | Version | Purpose | When to Use |
|---------------|---------|---------|-------------|
| `cv2.getPerspectiveTransform` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | Calculate a 3x3 perspective matrix from four source/destination point pairs. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | Use for every accepted square candidate after ordering corners. [VERIFIED: GEO-04 in .planning/REQUIREMENTS.md] |
| `cv2.warpPerspective` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | Produce the canonical face crop from the 3x3 matrix and output `dsize`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | Use with `(128, 128)` default `dsize` for classifier input. [VERIFIED: CLAUDE.md] |
| `np.mean` | NumPy 2.4 API docs. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] | Compute `center_px` from the four ordered points. [VERIFIED: GEO-05 in .planning/REQUIREMENTS.md] | Use `dtype=np.float64` to avoid avoidable float32 accumulation drift. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] |
| `np.arctan2` + `np.degrees` | NumPy 2.4 API docs. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | Compute `angle_deg` from the top-edge vector while preserving quadrant. [VERIFIED: GEO-05 in .planning/REQUIREMENTS.md] | Use on `TR - TL`; return a signed image-space angle in degrees. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] |
| `cv2.contourArea` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Recompute or validate `face_area_px` from ordered points if Phase 3 area is absent. [VERIFIED: src/block_detected/detector.py] | Prefer carrying Phase 3 `SquareCandidate.area_px`, with recomputation only as a consistency check. [VERIFIED: src/block_detected/detector.py; ASSUMED] |
| `cv2.boxPoints` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Inspect rotated-rectangle vertices only when deriving debug overlays from `minAreaRect`. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Do not use it as the primary Phase 4 input because Phase 3 already exposes `SquareCandidate.approx_xy`. [VERIFIED: src/block_detected/detector.py] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-repo NumPy ordering helper. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | `imutils.perspective.order_points`; latest PyPI is 0.5.4. [VERIFIED: `python3 -m pip index versions imutils`] | `imutils` is an extra dependency for one small function; use an in-repo helper with project-specific tie-break tests. [ASSUMED] |
| `cv2.getPerspectiveTransform`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | `cv2.findHomography`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | `findHomography` is useful for many point correspondences or robust estimation; Phase 4 has exactly four ordered corners, so `getPerspectiveTransform` is the direct API. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; VERIFIED: GEO-04 in .planning/REQUIREMENTS.md] |
| Top-edge `atan2(TR - TL)`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | `cv2.minAreaRect(...)[2]`. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | `minAreaRect` angle switches edges and is constrained to `[-90, 0)`, so it does not match GEO-05's explicit top-edge definition. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; VERIFIED: GEO-05 in .planning/REQUIREMENTS.md] |
| Fixed 128x128 warp. [VERIFIED: CLAUDE.md] | Dynamic `maxWidth`/`maxHeight` from side lengths. [CITED: https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/] | Dynamic sizes are useful for document scanning; Phase 5 needs a stable classifier tensor shape, so Phase 4 should output fixed-size crops. [VERIFIED: CLAUDE.md; VERIFIED: .planning/ROADMAP.md] |

**Installation:**

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

**Version verification:** PyPI and local probes on 2026-05-31 returned `opencv-python 4.13.0.92` uploaded 2026-02-05, `numpy 2.4.6` uploaded 2026-05-18, and `pytest 9.0.3` uploaded 2026-04-07. [VERIFIED: `python3 -m pip index versions ...`; VERIFIED: PyPI JSON probe] The local Python 3.14.4 environment currently cannot import `cv2`, `numpy`, or `pytest`. [VERIFIED: local import probes]

## Architecture Patterns

### Recommended Project Structure

```text
src/block_detected/
  geometry.py        # GeometrySettings, FaceGeometry, order_corners_tl_tr_br_bl(), warp_candidate_face().
  detector.py        # Phase 3 SquareCandidate source object already present in current worktree.
  vision.py          # Later integration can compose candidates -> geometry -> classifier.
tests/
  test_geometry.py   # permutation, rotation, center, angle, warp-shape, and crop-orientation tests.
```

This structure matches the existing package layout and keeps Phase 4 geometry separate from Phase 5 classification and Phase 7 final reject mapping. [VERIFIED: src/block_detected/detector.py; VERIFIED: src/block_detected/vision.py; VERIFIED: .planning/ROADMAP.md]

### Pattern 1: Geometry Output Object Between Candidate and DetectionResult

**What:** Create a `FaceGeometry` dataclass that carries ordered corner arrays, contract-ready `CornersPx`, center, angle, bbox, area, warp image, and perspective matrix. [VERIFIED: src/block_detected/detection_contract.py; ASSUMED]

**When to use:** Use for each Phase 3 `SquareCandidate` before classification so Phase 5 receives a canonical crop and Phase 7 can later build `DetectionResult` statuses. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/ROADMAP.md]

**Example:**

```python
# Source basis: Phase 3 SquareCandidate plus existing detection contract dataclasses.
# [VERIFIED: src/block_detected/detector.py; VERIFIED: src/block_detected/detection_contract.py]
from dataclasses import dataclass
import numpy as np

from .detection_contract import BoundingBoxPx, CornersPx, PointPx


@dataclass(frozen=True)
class GeometrySettings:
    warp_size_px: int = 128
    min_side_px: float = 10.0


@dataclass(frozen=True)
class FaceGeometry:
    ordered_xy: np.ndarray
    corners_px: CornersPx
    center_px: PointPx
    angle_deg: float
    bbox_px: BoundingBoxPx
    face_area_px: float
    warp_bgr: np.ndarray
    perspective_matrix: np.ndarray
```

### Pattern 2: Sort Around Centroid, Then Rotate to Top Edge

**What:** Convert unordered vertices to a cyclic polygon by sorting by `atan2(y - cy, x - cx)`, then rotate the cyclic order so the first edge is the topmost image-space edge with a deterministic leftmost tie-break. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html; ASSUMED]

**When to use:** Use for every Phase 3 `SquareCandidate.approx_xy`, because OpenCV contour approximation does not guarantee TL/TR/BR/BL order for this project contract. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source basis: NumPy mean and arctan2 APIs; PyImageSearch documents duplicate
# failures in the older sum/difference ordering shortcut.
# [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html]
# [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html]
# [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]
import numpy as np


def order_corners_tl_tr_br_bl(points_xy: np.ndarray) -> np.ndarray:
    pts = np.asarray(points_xy, dtype=np.float64)
    if pts.shape != (4, 2):
        raise ValueError(f"points_xy must have shape (4, 2); got {pts.shape!r}")
    if not np.isfinite(pts).all():
        raise ValueError("points_xy must contain only finite values")
    if np.unique(np.round(pts, decimals=6), axis=0).shape[0] != 4:
        raise ValueError("points_xy must contain four distinct points")

    center = np.mean(pts, axis=0, dtype=np.float64)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    cyclic = pts[np.argsort(angles)]

    starts = cyclic
    ends = np.roll(cyclic, -1, axis=0)
    midpoints = (starts + ends) / 2.0
    top_edge_index = int(np.lexsort((midpoints[:, 0], midpoints[:, 1]))[0])
    ordered = np.roll(cyclic, -top_edge_index, axis=0)
    return ordered.astype(np.float32)
```

### Pattern 3: Fixed Destination Quad for Classifier Crops

**What:** Map ordered points to `[[0,0], [127,0], [127,127], [0,127]]` by default and call `cv2.warpPerspective` with output `dsize=(128, 128)`. [VERIFIED: CLAUDE.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**When to use:** Use for Phase 4 output so Phase 5 sees a stable BGR crop shape independent of object distance and perspective. [VERIFIED: .planning/ROADMAP.md; VERIFIED: CLAUDE.md]

**Example:**

```python
# Source basis: OpenCV getPerspectiveTransform calculates a 3x3 transform
# from four corresponding source/destination points; warpPerspective applies it.
# [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
import cv2
import numpy as np


def warp_ordered_face(frame_bgr: np.ndarray, ordered_xy: np.ndarray, size_px: int = 128):
    dst = np.array(
        [
            [0.0, 0.0],
            [size_px - 1.0, 0.0],
            [size_px - 1.0, size_px - 1.0],
            [0.0, size_px - 1.0],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(ordered_xy.astype(np.float32), dst)
    crop = cv2.warpPerspective(
        frame_bgr,
        matrix,
        (size_px, size_px),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return crop, matrix
```

### Pattern 4: Compute Contract Geometry From Ordered Points

**What:** Compute center with `np.mean`, angle with `atan2(TR - TL)`, bbox from min/max ordered coordinates, and `CornersPx` in the public contract's field order. [VERIFIED: src/block_detected/detection_contract.py; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html]

**When to use:** Use after ordering and before classification so downstream phases can reuse identical geometry. [VERIFIED: .planning/ROADMAP.md]

**Example:**

```python
# Source basis: GEO-05 requires mean center and top-edge angle.
# [VERIFIED: .planning/REQUIREMENTS.md]
from .detection_contract import BoundingBoxPx, CornersPx, PointPx


def geometry_scalars(ordered_xy: np.ndarray):
    tl, tr, br, bl = ordered_xy.astype(np.float64)
    center_x, center_y = np.mean(ordered_xy, axis=0, dtype=np.float64)
    angle_deg = float(np.degrees(np.arctan2(tr[1] - tl[1], tr[0] - tl[0])))
    min_x, min_y = np.min(ordered_xy, axis=0)
    max_x, max_y = np.max(ordered_xy, axis=0)
    return {
        "center_px": PointPx(float(center_x), float(center_y)),
        "corners_px": CornersPx(
            top_left=PointPx(float(tl[0]), float(tl[1])),
            top_right=PointPx(float(tr[0]), float(tr[1])),
            bottom_right=PointPx(float(br[0]), float(br[1])),
            bottom_left=PointPx(float(bl[0]), float(bl[1])),
        ),
        "angle_deg": angle_deg,
        "bbox_px": BoundingBoxPx(
            x=float(min_x),
            y=float(min_y),
            width=float(max_x - min_x),
            height=float(max_y - min_y),
        ),
    }
```

### Anti-Patterns to Avoid

- **Using `minAreaRect.angle` as project angle:** It does not satisfy GEO-05 because OpenCV's documented angle range and edge switching are different from `atan2(TR - TL)`. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; VERIFIED: .planning/REQUIREMENTS.md]
- **Ordering only by min/max `x + y` and `x - y`:** Duplicate sums/differences can assign the wrong points. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]
- **Making crop size dynamic in Phase 4:** Dynamic crops make Phase 5 model input inconsistent. [VERIFIED: CLAUDE.md; VERIFIED: .planning/ROADMAP.md]
- **Returning a `DetectionResult` from geometry:** Classification and final rejection status are later phases. [VERIFIED: .planning/ROADMAP.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Perspective matrix solving | Custom homography linear solver. [ASSUMED] | `cv2.getPerspectiveTransform`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | OpenCV already calculates the 3x3 transform from four point pairs and handles the solver path. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| Pixel resampling for the face crop | Manual bilinear interpolation loops. [ASSUMED] | `cv2.warpPerspective`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | OpenCV implements image warping, interpolation flags, and border modes for this exact operation. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| Angle quadrant handling | `atan(dy / dx)` or slope conditionals. [ASSUMED] | `np.arctan2(dy, dx)`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | `arctan2` chooses the correct quadrant and returns signed radians. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] |
| Center calculation | Manual average with integer truncation. [ASSUMED] | `np.mean(..., dtype=np.float64)`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] | The requirement says mean of corners, and NumPy provides controlled accumulator dtype. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] |
| Contract geometry serialization | New ad hoc dictionaries for corners. [ASSUMED] | Existing `PointPx`, `CornersPx`, and `BoundingBoxPx`. [VERIFIED: src/block_detected/detection_contract.py] | The public contract already validates field types and ordering. [VERIFIED: src/block_detected/detection_contract.py] |
| Dependency for one ordering helper | Adding `imutils` only for `order_points`. [VERIFIED: `python3 -m pip index versions imutils`] | Small in-repo NumPy helper with tests. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html; ASSUMED] | The project needs exact tie-breaking and no extra runtime package for one function. [ASSUMED] |

**Key insight:** The only custom algorithm Phase 4 should own is deterministic ordering semantics; homography, warp interpolation, center, and angle primitives should come from OpenCV/NumPy and be covered by tests. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html; ASSUMED]

## Common Pitfalls

### Pitfall 1: Sum/Difference Ordering Fails on Symmetric or Near-Symmetric Points

**What goes wrong:** Two vertices can share the same `x + y` or `x - y` value, causing `argmin`/`argmax` to select duplicate or wrong roles. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**Why it happens:** The shortcut assumes unique extrema for sums and differences, which is not guaranteed for rotated squares. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**How to avoid:** Sort cyclically around the centroid, choose a top-edge tie-break, and test all permutations of each synthetic quadrilateral. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html; CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html; ASSUMED]

**Warning signs:** A diamond-like 45-degree square produces mirrored or 90-degree-shifted crops. [ASSUMED]

### Pitfall 2: `minAreaRect` Angle Does Not Match Project Angle

**What goes wrong:** `angle_deg` jumps by roughly 90 degrees or changes sign unexpectedly as the block rotates. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED]

**Why it happens:** OpenCV documents `minAreaRect` angle in `[-90, 0)` and says the measured edge changes as the object rotates. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]

**How to avoid:** Always compute `angle_deg` from the ordered top edge using `atan2(TR.y - TL.y, TR.x - TL.x)`. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html]

**Warning signs:** Angle tests pass for unrotated squares but fail around 45, 90, or 135 degrees. [ASSUMED]

### Pitfall 3: Destination Point Order Mirrors the Classifier Crop

**What goes wrong:** `warpPerspective` returns a crop with the face flipped or rotated even though the output shape is correct. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED]

**Why it happens:** `getPerspectiveTransform` maps corresponding source and destination quadrangle vertices by index, so a mismatched source/destination order changes the homography. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**How to avoid:** Keep source and destination arrays in the same TL, TR, BR, BL order and use asymmetric synthetic fixtures to verify orientation. [CITED: https://docs.opencv.org/4.x/de/dd4/samples_2cpp_2warpPerspective_demo_8cpp-example.html; ASSUMED]

**Warning signs:** A synthetic crop with colored quadrants places top-left content in another corner. [ASSUMED]

### Pitfall 4: Dynamic Crop Sizes Break Phase 5

**What goes wrong:** The classifier receives variable tensor shapes or implicit resizing that changes training/inference semantics. [VERIFIED: CLAUDE.md; ASSUMED]

**Why it happens:** Document-scanner examples often compute `maxWidth` and `maxHeight` from side lengths, which is useful for documents but not for a fixed-size CNN input. [CITED: https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/; VERIFIED: CLAUDE.md]

**How to avoid:** Use `GeometrySettings.warp_size_px=128` and include the setting in metadata/tests. [VERIFIED: CLAUDE.md; ASSUMED]

**Warning signs:** Tests assert only "crop exists" and not `crop.shape == (128, 128, 3)`. [ASSUMED]

### Pitfall 5: Degenerate Quads Produce Bad or Unstable Warps

**What goes wrong:** Duplicate points, near-zero side lengths, or nearly collinear vertices produce singular or visually meaningless transforms. [ASSUMED]

**Why it happens:** `getPerspectiveTransform` expects four corresponding quadrangle vertices; degenerate source geometry does not define a useful quadrangle. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED]

**How to avoid:** Validate shape `(4, 2)`, finite values, four distinct points, minimum side length, non-trivial polygon area, and in-frame coordinates before warping. [VERIFIED: src/block_detected/detector.py; ASSUMED]

**Warning signs:** Warp contains mostly border pixels, `perspective_matrix` has non-finite values, or side-length checks approach zero. [ASSUMED]

### Pitfall 6: Square Symmetry Cannot Reveal Semantic Upright Orientation

**What goes wrong:** Geometry produces a deterministic crop, but the physical face's semantic "upright" orientation may still be off by a multiple of 90 degrees. [ASSUMED]

**Why it happens:** A square quadrilateral has four rotationally equivalent geometric corner assignments unless the face texture, class model, or another cue defines semantic top. [ASSUMED]

**How to avoid:** Phase 4 should document image-space ordering semantics; Phase 5 should either train with rotation augmentation or explicitly consume `angle_deg`/orientation metadata. [VERIFIED: .planning/ROADMAP.md; ASSUMED]

**Warning signs:** Classification accuracy varies by 90-degree block rotations even when geometry tests pass. [ASSUMED]

### Pitfall 7: Width/Height Argument Order Is Easy to Hide for Square Crops

**What goes wrong:** Future non-square debug crops get transposed because OpenCV `dsize` is `(width, height)`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**Why it happens:** NumPy image shapes are `(height, width, channels)`, while OpenCV warp `dsize` is a `Size(width, height)`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED]

**How to avoid:** Name variables `warp_width_px` and `warp_height_px` if non-square support is added; for Phase 4 keep a single `warp_size_px`. [ASSUMED]

**Warning signs:** Tests pass only because 128x128 is square. [ASSUMED]

## Code Examples

Verified patterns from official sources and current project files:

### End-to-End Candidate Geometry

```python
# Source basis: Phase 3 SquareCandidate, OpenCV perspective APIs, and existing
# contract dataclasses.
# [VERIFIED: src/block_detected/detector.py]
# [VERIFIED: src/block_detected/detection_contract.py]
# [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
def geometry_from_candidate(frame_bgr, candidate, settings=GeometrySettings()):
    ordered = order_corners_tl_tr_br_bl(candidate.approx_xy)
    crop_bgr, matrix = warp_ordered_face(frame_bgr, ordered, settings.warp_size_px)
    scalars = geometry_scalars(ordered)
    return FaceGeometry(
        ordered_xy=ordered,
        corners_px=scalars["corners_px"],
        center_px=scalars["center_px"],
        angle_deg=scalars["angle_deg"],
        bbox_px=scalars["bbox_px"],
        face_area_px=float(candidate.area_px),
        warp_bgr=crop_bgr,
        perspective_matrix=matrix,
    )
```

### Geometry Test Matrix

```python
# Source basis: pytest parametrize supports multiple argument sets.
# [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html]
import itertools
import numpy as np
import pytest


@pytest.mark.parametrize("angle_deg", [0, 15, 30, 45, 60, 89, 120, 179])
def test_ordering_is_stable_for_all_input_permutations(angle_deg):
    expected = rotated_square_points(center=(320.0, 240.0), side=120.0, angle_deg=angle_deg)
    for permuted in itertools.permutations(expected):
        ordered = order_corners_tl_tr_br_bl(np.array(permuted, dtype=np.float64))
        assert ordered.shape == (4, 2)
        assert np.all(np.isfinite(ordered))
```

### Warp Orientation Fixture

```python
# Source basis: OpenCV warpPerspective applies a perspective transform to an image.
# [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
def test_warp_preserves_synthetic_quadrant_orientation():
    frame, source_corners = asymmetric_face_fixture()
    ordered = order_corners_tl_tr_br_bl(source_corners)
    crop, _ = warp_ordered_face(frame, ordered, size_px=128)

    assert crop.shape == (128, 128, 3)
    assert top_left_marker_score(crop) > top_right_marker_score(crop)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Use sum/difference extrema for all corner ordering. [CITED: https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/] | Use a robust ordering method with duplicate/tie tests. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/; ASSUMED] | PyImageSearch documented the issue in 2016 and current testing should cover it. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | Planner should require permutation and 45-degree tests for GEO-03. [ASSUMED] |
| Use `minAreaRect` angle as object rotation. [ASSUMED] | Use the explicit top-edge vector from ordered corners. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | Project requirement GEO-05 defines the angle source. [VERIFIED: .planning/REQUIREMENTS.md] | Planner should not accept `minAreaRect` angle as sufficient. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| Use dynamic document-scanner crop dimensions. [CITED: https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/] | Use a fixed 128x128 crop for the later classifier. [VERIFIED: CLAUDE.md] | Project stack locked classifier latency and crop size before Phase 4. [VERIFIED: CLAUDE.md] | Phase 5 can train and infer on a stable tensor shape. [ASSUMED] |
| Let geometry directly return final OK/invalid results. [ASSUMED] | Return geometry artifacts now; integrate final reject statuses later. [VERIFIED: .planning/ROADMAP.md] | Roadmap separates Phase 4 geometry from Phase 7 reject integration. [VERIFIED: .planning/ROADMAP.md] | Planner should keep `detect_block` integration limited or behind clear boundaries. [VERIFIED: .planning/ROADMAP.md] |

**Deprecated/outdated:**

- Treating `cv2.findContours`/`approxPolyDP` point order as already contract-ready is unsafe for this phase; Phase 3 exposes `SquareCandidate.approx_xy` but does not order it as TL/TR/BR/BL. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/REQUIREMENTS.md]
- Using `cv2.minAreaRect` angle for `angle_deg` is outdated for this project because GEO-05 explicitly defines top-edge orientation. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
- Adding ArUco/AprilTag markers to solve orientation is forbidden by project constraints. [VERIFIED: CLAUDE.md; VERIFIED: .planning/REQUIREMENTS.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The centroid-angle plus top-edge tie-break ordering semantics are acceptable for project TL/TR/BR/BL. | Architecture Patterns | If the user expects semantic physical face orientation, geometry-only ordering will be insufficient. |
| A2 | 128x128 should be the default warp size. | Standard Stack, Architecture Patterns | If Phase 5 later chooses 160x160, tests and representative training data must be regenerated. |
| A3 | Phase 5 can handle deterministic image-space crops that may be semantically rotated by multiples of 90 degrees. | Common Pitfalls | Classifier accuracy may drop on rotated blocks unless training includes rotation augmentation. |
| A4 | Current worktree Phase 3 `SquareCandidate.approx_xy` is the intended upstream candidate interface. | Summary, Architecture Patterns | If Phase 3 is rewritten before Phase 4 planning, adapter tasks may change. |
| A5 | Recomputing `face_area_px` is optional if Phase 3 candidate area is carried forward. | Standard Stack, Code Examples | If Phase 3 area semantics differ from ordered polygon area, downstream metrics may need one canonical definition. |

## Open Questions

1. **Does Phase 5 require semantic upright face crops?**
   - What we know: Phase 4 must produce consistent geometry and a classifier-suitable crop. [VERIFIED: .planning/ROADMAP.md]
   - What's unclear: Whether block face artwork has a semantic top that the classifier expects. [ASSUMED]
   - Recommendation: Phase 4 should output deterministic image-space crops and `angle_deg`; Phase 5 should train with rotation augmentation unless a semantic orientation cue is added. [ASSUMED]

2. **Should the canonical crop be 128x128 or 160x160?**
   - What we know: Requirements allow either, but CLAUDE.md says classify on 128x128 warp. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md]
   - What's unclear: No Phase 5 model architecture exists yet. [VERIFIED: .planning/ROADMAP.md]
   - Recommendation: Lock Phase 4 default to 128 and keep `GeometrySettings.warp_size_px` configurable. [VERIFIED: CLAUDE.md; ASSUMED]

3. **Where should geometry validation failures become public statuses?**
   - What we know: REJ-03 invalid/skewed quad rejection is Phase 7. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: .planning/ROADMAP.md]
   - What's unclear: Whether Phase 4 should return errors, skip candidates, or attach validation diagnostics. [ASSUMED]
   - Recommendation: Phase 4 should raise/return internal geometry validation errors with reasons; Phase 7 should map them to `DetectionStatus.INVALID_GEOMETRY`. [VERIFIED: .planning/ROADMAP.md; ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All Phase 4 code/tests. [VERIFIED: pyproject.toml] | yes | 3.14.4 local; target Pi stack 3.11.x. [VERIFIED: local `python3 --version`; VERIFIED: .planning/research/STACK.md] | None needed. [ASSUMED] |
| OpenCV Python `cv2` | `getPerspectiveTransform`, `warpPerspective`, image fixtures. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | no locally | Missing import. [VERIFIED: local import probe] | Install project dev extras before automated geometry tests. [VERIFIED: pyproject.toml] |
| NumPy | Ordering, center, angle, tests. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | no locally | Missing import. [VERIFIED: local import probe] | Install project dev extras before automated geometry tests. [VERIFIED: pyproject.toml] |
| pytest | Nyquist validation tests. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html] | no locally | Missing import. [VERIFIED: local import probe] | Existing unittest tests do not cover Phase 4 geometry; install dev extras. [VERIFIED: tests/test_pipeline.py; ASSUMED] |
| Phase 3 candidate module | Upstream `SquareCandidate.approx_xy`. [VERIFIED: src/block_detected/detector.py] | yes in current worktree | Untracked current worktree file. [VERIFIED: `git status --short`] | If Phase 3 code changes, add an adapter to read the final candidate field. [ASSUMED] |
| Synthetic vision fixture | Warp orientation tests. [VERIFIED: tests/fixtures/vision/square_face.png] | yes in current worktree | Static PNG exists in current worktree. [VERIFIED: local `find tests/fixtures/vision`] | Generate asymmetric synthetic fixtures inside tests. [ASSUMED] |

**Missing dependencies with no fallback:**

- `cv2`, `numpy`, and `pytest` are required to run Phase 4 automated tests and are not importable in the current local Python environment. [VERIFIED: local import probes]

**Missing dependencies with fallback:**

- Real captured block-face fixtures are not required for Phase 4 mechanics if asymmetric synthetic fixtures verify ordering and warp orientation, but real fixtures remain useful before Phase 8 evaluation. [VERIFIED: .planning/ROADMAP.md; ASSUMED]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 recommended; missing locally. [VERIFIED: PyPI JSON probe; VERIFIED: local import probe] |
| Config file | `pyproject.toml` has `[tool.pytest.ini_options] testpaths = ["tests"]`. [VERIFIED: pyproject.toml] |
| Quick run command | `python -m pytest tests/test_geometry.py -q` [ASSUMED] |
| Full suite command | `python -m pytest -q` [VERIFIED: pyproject.toml; ASSUMED] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| GEO-03 | Every permutation of each synthetic rotated square orders to deterministic TL, TR, BR, BL. [VERIFIED: .planning/REQUIREMENTS.md] | unit | `python -m pytest tests/test_geometry.py::test_ordering_is_stable_for_all_input_permutations -q` | no, Wave 0 |
| GEO-03 | Degenerate point sets are rejected before warping. [ASSUMED] | unit | `python -m pytest tests/test_geometry.py::test_ordering_rejects_duplicate_or_nonfinite_points -q` | no, Wave 0 |
| GEO-04 | Candidate warp returns `(128, 128, 3)` `uint8` BGR without mutating source frame. [VERIFIED: CLAUDE.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | unit | `python -m pytest tests/test_geometry.py::test_warp_outputs_128x128_bgr_without_mutation -q` | no, Wave 0 |
| GEO-04 | Asymmetric synthetic fixture keeps top-left marker in the crop's top-left region. [ASSUMED] | unit | `python -m pytest tests/test_geometry.py::test_warp_preserves_synthetic_quadrant_orientation -q` | no, Wave 0 |
| GEO-05 | `center_px` equals float64 mean of ordered corners. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] | unit | `python -m pytest tests/test_geometry.py::test_center_is_mean_of_ordered_corners -q` | no, Wave 0 |
| GEO-05 | `angle_deg` equals top-edge `atan2(TR - TL)` for representative rotations. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html] | unit | `python -m pytest tests/test_geometry.py::test_angle_matches_top_edge_orientation -q` | no, Wave 0 |
| GEO-03/GEO-04/GEO-05 | `geometry_from_candidate` consumes current Phase 3 `SquareCandidate` and returns `FaceGeometry`. [VERIFIED: src/block_detected/detector.py] | integration | `python -m pytest tests/test_geometry.py::test_geometry_from_square_candidate -q` | no, Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_geometry.py -q` [ASSUMED]
- **Per wave merge:** `python -m pytest -q` [ASSUMED]
- **Phase gate:** Full suite green with dev extras installed, plus visual inspection or artifact assertion for one asymmetric warp fixture. [VERIFIED: .planning/config.json `nyquist_validation=true`; ASSUMED]

### Wave 0 Gaps

- [ ] `src/block_detected/geometry.py` - covers GEO-03, GEO-04, GEO-05. [ASSUMED]
- [ ] `tests/test_geometry.py` - permutation, rotation, center, angle, warp, and candidate integration tests. [ASSUMED]
- [ ] Install dev extras: `python -m pip install -e ".[dev]"` before running geometry tests. [VERIFIED: pyproject.toml; VERIFIED: local import probes]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Phase 4 has no authentication surface. [VERIFIED: .planning/ROADMAP.md] |
| V3 Session Management | no | Phase 4 has no session state. [VERIFIED: .planning/ROADMAP.md] |
| V4 Access Control | no | Phase 4 has no user authorization boundary. [VERIFIED: .planning/ROADMAP.md] |
| V5 Input Validation | yes | Validate frame shape `(480, 640, 3)`, dtype `uint8`, corner shape `(4, 2)`, finite values, distinct points, side lengths, and warp size. [VERIFIED: src/block_detected/camera.py; VERIFIED: src/block_detected/detector.py; ASSUMED] |
| V6 Cryptography | no | Phase 4 has no cryptographic operation. [VERIFIED: .planning/ROADMAP.md] |

### Known Threat Patterns for OpenCV Geometry

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed frame or candidate array crashes OpenCV. [ASSUMED] | Denial of Service | Validate shape, dtype, finite values, and point count before OpenCV calls. [VERIFIED: src/block_detected/preprocess.py; ASSUMED] |
| Degenerate quadrilateral produces invalid matrix or pathological crop. [ASSUMED] | Denial of Service | Enforce four distinct points, minimum side length, non-trivial area, and in-frame bounds before warp. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED] |
| Debug artifacts expose arbitrary filesystem paths. [ASSUMED] | Information Disclosure / Tampering | Reuse Phase 2 `DebugFrameWriter` fixed directory and allowed-root controls instead of accepting per-candidate paths. [VERIFIED: src/block_detected/debug.py] |

## Sources

### Primary (HIGH confidence)

- https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html - `getPerspectiveTransform`, `warpPerspective`, `dsize`, interpolation, border modes, and in-place limitation. [CITED]
- https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html - `minAreaRect` angle semantics, `boxPoints`, `contourArea`, and convexity caveats. [CITED]
- https://docs.opencv.org/4.x/de/dd4/samples_2cpp_2warpPerspective_demo_8cpp-example.html - OpenCV sample using TL/TR/BR/BL labels and perspective warp. [CITED]
- https://numpy.org/doc/stable/reference/generated/numpy.mean.html - arithmetic mean behavior and dtype control. [CITED]
- https://numpy.org/doc/stable/reference/generated/numpy.arctan2.html - quadrant-aware signed angle. [CITED]
- https://docs.pytest.org/en/stable/how-to/parametrize.html - parametrized test pattern for rotations/permutations. [CITED]
- Local `pyproject.toml` - project dev dependency ranges and pytest config. [VERIFIED]
- Local `src/block_detected/detection_contract.py` - `PointPx`, `CornersPx`, `BoundingBoxPx`, `DetectionResult` validation. [VERIFIED]
- Local `src/block_detected/detector.py` - current Phase 3 `SquareCandidate.approx_xy`, area, bbox, score. [VERIFIED]

### Secondary (MEDIUM confidence)

- https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/ - common four-point transform pattern and dynamic crop example. [CITED]
- https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/ - known failure mode in older sum/difference corner ordering. [CITED]
- `.planning/phases/03-preprocess-contour-detection/03-RESEARCH.md` - upstream candidate assumptions and Phase 3/4 boundary. [VERIFIED]
- `.planning/research/STACK.md` - project stack decisions for OpenCV, NumPy, pytest, and Pi constraints. [VERIFIED]
- Local PyPI and PyPI JSON probes for current package versions and upload timestamps. [VERIFIED]

### Tertiary (LOW confidence)

- The top-edge tie-break for exact diamond-like squares is a project semantic choice and should be confirmed by tests/user expectations if the robot requires a different convention. [ASSUMED]
- Phase 5 rotation augmentation requirement is inferred from square symmetry and the absence of a semantic orientation cue in Phase 4. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - OpenCV, NumPy, pytest versions and APIs were verified against PyPI/local probes and official docs. [VERIFIED: PyPI JSON probe; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html]
- Architecture: MEDIUM - The module boundary matches current worktree Phase 3 code, but those Phase 3 files are untracked and could change before planning. [VERIFIED: `git status --short`; VERIFIED: src/block_detected/detector.py]
- Pitfalls: HIGH for OpenCV `minAreaRect`/warp mechanics and MEDIUM for semantic orientation risks. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED]
- Validation: MEDIUM - Test architecture is clear, but `cv2`, `numpy`, and `pytest` are not currently installed locally. [VERIFIED: local import probes]

**Research date:** 2026-05-31 [VERIFIED: user environment context]
**Valid until:** 2026-06-30 for OpenCV/NumPy API usage; revisit before Phase 5 if the classifier input size or orientation contract changes. [ASSUMED]
