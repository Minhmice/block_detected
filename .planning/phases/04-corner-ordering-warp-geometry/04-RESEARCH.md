# Phase 04: Corner Ordering, Warp & Geometry - Research

**Researched:** 2026-05-31 [VERIFIED: local environment context]  
**Domain:** OpenCV quadrilateral corner ordering, perspective warp, and pixel geometry for square block faces [VERIFIED: .planning/ROADMAP.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]  
**Confidence:** HIGH for OpenCV warp APIs and local Phase 3 interface; MEDIUM for crop-size/model-readiness details because Phase 5 classifier input metadata does not exist yet [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/ROADMAP.md]

## User Constraints

No Phase 4 `CONTEXT.md` exists, so there are no additional locked decisions, discretion notes, or deferred ideas from `/gsd-discuss-phase`. [VERIFIED: `gsd-tools.cjs init phase-op 04` returned `has_context=false`]

### Locked Decisions

- Phase 4 goal is that each candidate yields consistently ordered corners, a canonical face warp, and pixel pose geometry. [VERIFIED: .planning/ROADMAP.md]
- Phase 4 depends on Phase 3. [VERIFIED: .planning/ROADMAP.md]
- Phase 4 must address GEO-03, GEO-04, and GEO-05. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Corners must be output in top-left, top-right, bottom-right, bottom-left order. [VERIFIED: .planning/REQUIREMENTS.md]
- `warpPerspective` must produce a canonical 128x128 or 160x160 face crop suitable for classification. [VERIFIED: .planning/REQUIREMENTS.md]
- `center_px` must equal the mean of ordered corners, and `angle_deg` must match the top-edge orientation from `TR - TL`. [VERIFIED: .planning/REQUIREMENTS.md]
- v1 forbids ArUco and AprilTag markers on blocks. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md]
- Phase 5 classification and Phase 6 robot calibration are out of scope except for interface readiness. [VERIFIED: user prompt; VERIFIED: .planning/ROADMAP.md]

### Claude's Discretion

- No Phase 4 discretion section exists; module names, dataclass names, validation tolerance defaults, and test fixture design are planner choices constrained by the implemented Phase 3 handoff and existing contract types. [VERIFIED: `gsd-tools.cjs init phase-op 04`; VERIFIED: src/block_detected/detector.py; VERIFIED: src/block_detected/detection_contract.py]

### Deferred Ideas (OUT OF SCOPE)

- CNN/TFLite classification, confidence thresholds, and training pipeline are Phase 5. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Pixel-to-mm homography and robot pickup pose are Phase 6. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Full reject-policy mapping to `invalid_geometry`, `multiple_candidates`, and end-to-end `detect_block` integration is Phase 7, though Phase 4 should expose geometry validation signals for that later mapping. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEO-03 | Order corners consistently as top-left, top-right, bottom-right, bottom-left. [VERIFIED: .planning/REQUIREMENTS.md] | Implement a local `order_corners_xy()` that accepts Phase 3 `SquareCandidate.approx_xy`, validates four finite unique points, uses the robust x-sort/y-sort/distance pattern, and tests every input permutation. [VERIFIED: src/block_detected/detector.py; CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] |
| GEO-04 | Warp face to canonical 128x128 or 160x160 for classification. [VERIFIED: .planning/REQUIREMENTS.md] | Use OpenCV `cv2.getPerspectiveTransform` from four ordered source points to fixed destination points, then `cv2.warpPerspective` with `dsize=(crop_size_px, crop_size_px)`. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| GEO-05 | Compute `center_px` as mean of corners and `angle_deg` from top edge using `atan2(TR - TL)`. [VERIFIED: .planning/REQUIREMENTS.md] | Use `np.mean(ordered, axis=0, dtype=np.float64)` for center and `math.degrees(math.atan2(tr_y - tl_y, tr_x - tl_x))` for image-space angle. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.python.org/3/library/math.html] |
</phase_requirements>

## Summary

Phase 4 should add a pure geometry stage between Phase 3 contour candidates and later classifier/pose stages. [VERIFIED: .planning/ROADMAP.md] The local Phase 3 implementation already emits `SquareCandidate.approx_xy` as an unordered `(4, 2)` `float64` array plus area, aspect, bbox, and score, so Phase 4 should consume that object directly and must not assume the OpenCV contour vertex order is meaningful. [VERIFIED: src/block_detected/detector.py]

The stable architecture is `SquareCandidate -> ordered corners -> perspective matrix -> fixed-size BGR warp -> center/angle metadata`. [VERIFIED: .planning/research/ARCHITECTURE.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] Use OpenCV for the perspective matrix and resampling, NumPy for finite checks and means, and Python `math.atan2` for the contract-defined angle. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.python.org/3/library/math.html]

**Primary recommendation:** Create `src/block_detected/geometry.py` with `GeometrySettings`, `FaceGeometry`, `order_corners_xy()`, `compute_center_angle()`, `warp_face_bgr()`, and `geometry_from_candidate()`, defaulting `crop_size_px=128` and exporting the new types from `src/block_detected/__init__.py`. [VERIFIED: CLAUDE.md; VERIFIED: src/block_detected/__init__.py; VERIFIED: .planning/ROADMAP.md]

## Project Constraints (from CLAUDE.md)

- The project is a Raspberry Pi / edge vision pipeline for four cube blocks without ArUco markers. [VERIFIED: CLAUDE.md]
- The core value is reliable block ID plus correctly ordered corners and angle for robot pickup, not just a bounding box. [VERIFIED: CLAUDE.md]
- The technical stack is Python 3, OpenCV, TensorFlow Lite INT8, and Pi-compatible runtime. [VERIFIED: CLAUDE.md]
- Resolution is locked to 640x480 where possible. [VERIFIED: CLAUDE.md]
- Latency must suit a robot pick cycle, and later classification should operate on a 128x128 warp rather than a full-frame heavy model. [VERIFIED: CLAUDE.md]
- Output must conform to the existing `DetectionResult` contract in `detection_contract.py`. [VERIFIED: CLAUDE.md; VERIFIED: src/block_detected/detection_contract.py]
- GSD workflow enforcement says file-changing work should happen through GSD entry points unless explicitly bypassed. [VERIFIED: CLAUDE.md]
- No project-local skills were found under `.claude/skills/` or `.agents/skills/`. [VERIFIED: local `find .claude/skills .agents/skills -maxdepth 2 -name SKILL.md`]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | Target Pi: 3.11.x; local host: 3.14.4. [VERIFIED: .planning/research/STACK.md; VERIFIED: local `python3 --version`] | Runtime for geometry helpers and tests. [VERIFIED: CLAUDE.md] | Existing package requires Python `>=3.11`. [VERIFIED: pyproject.toml] |
| OpenCV Python (`opencv-python`) | Project dev range `>=4.11,<4.14`; PyPI current `4.13.0.92`, published 2026-02-05. [VERIFIED: pyproject.toml; VERIFIED: local PyPI JSON query] | Perspective matrix, perspective warp, polygon area, bbox, and optional debug drawing. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | OpenCV provides `getPerspectiveTransform` and `warpPerspective`, the exact operations required by GEO-04. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| NumPy | Project dev range `>=2,<3`; PyPI current `2.4.6`, published 2026-05-18. [VERIFIED: pyproject.toml; VERIFIED: local PyPI JSON query] | Point-array validation, ordering math, finite checks, means, distances, and test assertions. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html] | Phase 3 candidates already use NumPy arrays for `approx_xy`. [VERIFIED: src/block_detected/detector.py] |
| Python `math` stdlib | Python 3.11+ target. [VERIFIED: pyproject.toml; VERIFIED: .planning/research/STACK.md] | `atan2` and degree conversion for `angle_deg`. [CITED: https://docs.python.org/3/library/math.html] | GEO-05 defines angle from `TR - TL`, and `atan2` preserves quadrant information. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.python.org/3/library/math.html] |
| pytest | Project dev range `>=9`; PyPI current `9.0.3`, published 2026-04-07. [VERIFIED: pyproject.toml; VERIFIED: local PyPI JSON query] | Permutation, warp-orientation, and center/angle tests. [VERIFIED: .planning/config.json `nyquist_validation=true`] | Existing Phase 2 and Phase 3 tests use pytest. [VERIFIED: tests/test_camera_source.py; VERIFIED: tests/test_preprocess.py; VERIFIED: tests/test_detector.py] |

### Supporting

| Library / API | Version | Purpose | When to Use |
|---------------|---------|---------|-------------|
| `SquareCandidate` | Local Phase 3 dataclass. [VERIFIED: src/block_detected/detector.py] | Input boundary for geometry. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md] | Use `candidate.approx_xy` for source corners and retain `candidate.area_px`, `bbox_xywh`, and `score` for downstream diagnostics. [VERIFIED: src/block_detected/detector.py] |
| `CaptureFrame` / `FrameCandidates` | Local Phase 2/3 dataclasses. [VERIFIED: src/block_detected/camera.py; VERIFIED: src/block_detected/vision.py] | Frame-level integration boundary. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md] | Use for helper integration only; keep core geometry functions pure on arrays/candidates. [ASSUMED] |
| `DetectionResult` corner types | Local contract dataclasses. [VERIFIED: src/block_detected/detection_contract.py] | Later contract mapping for `CornersPx`, `PointPx`, `BoundingBoxPx`, and valid status semantics. [VERIFIED: src/block_detected/detection_contract.py] | Provide conversion helpers or examples, but do not force Phase 4 to classify or return `OK` detections. [VERIFIED: .planning/ROADMAP.md] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Local `order_corners_xy()` with NumPy. [ASSUMED] | `imutils.perspective.order_points`. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | `imutils` adds a runtime dependency for a small function; stack research already recommends inline NumPy for this one operation. [VERIFIED: .planning/research/STACK.md] |
| Robust x-sort/y-sort/distance ordering. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | Sum/difference ordering. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | Sum/difference ordering can choose wrong points when sums or differences tie; tests must cover tie-prone rotated boxes. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] |
| `cv2.getPerspectiveTransform` for four point pairs. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | `cv2.findHomography`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | `getPerspectiveTransform` is the direct API for exactly four corresponding quadrangle vertices; `findHomography` is unnecessary unless later matching code has more points or outliers. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED] |
| `cv2.warpPerspective`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | Crop axis-aligned bbox and resize. [ASSUMED] | Bbox resize does not remove perspective skew and does not preserve the ordered-corner contract for rotated faces. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html] |
| Explicit `atan2(TR.y - TL.y, TR.x - TL.x)`. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.python.org/3/library/math.html] | `cv2.minAreaRect(...).angle`. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Requirement defines angle from the ordered top edge, so `minAreaRect` angle would introduce a second convention the contract does not ask for. [VERIFIED: .planning/REQUIREMENTS.md] |

**Installation:**

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

**Version verification:** `python3 -m pip index versions opencv-python`, `python3 -m pip index versions numpy`, and `python3 -m pip index versions pytest` returned `opencv-python 4.13.0.92`, `numpy 2.4.6`, and `pytest 9.0.3` on 2026-05-31. [VERIFIED: local pip index queries] PyPI JSON queries returned publish timestamps for the same current releases. [VERIFIED: local PyPI JSON query]

## Architecture Patterns

### Recommended Project Structure

```text
src/block_detected/
  geometry.py          # GeometrySettings, FaceGeometry, ordering, warp, center/angle helpers. [ASSUMED]
  vision.py            # Optional frame-level helper can call geometry_from_candidate later. [VERIFIED: src/block_detected/vision.py]
  detection_contract.py# Existing contract types for later result mapping. [VERIFIED: src/block_detected/detection_contract.py]
tests/
  test_geometry.py     # Permutations, rotated squares, perspective warp orientation, center/angle. [ASSUMED]
  fixtures/vision/     # Existing synthetic square fixture; add color-coded warp fixture if useful. [VERIFIED: tests/fixtures/vision/square_face.png]
```

### Pattern 1: Geometry Stage Owns Only Geometry

**What:** Convert one Phase 3 `SquareCandidate` plus source `frame_bgr` into a `FaceGeometry` record containing ordered corners, a fixed-size warp, center, angle, bbox, area, and candidate score. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/ROADMAP.md]

**When to use:** Use this for every accepted `SquareCandidate` before Phase 5 classification and Phase 6 calibration. [VERIFIED: .planning/ROADMAP.md]

**Example:**

```python
# Source basis: Phase 3 exposes SquareCandidate.approx_xy; Phase 4 owns ordering/warp/center/angle. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/ROADMAP.md]
@dataclass(frozen=True)
class FaceGeometry:
    ordered_corners_xy: np.ndarray  # shape (4, 2), TL, TR, BR, BL
    warp_bgr: np.ndarray            # shape (crop_size_px, crop_size_px, 3)
    center_xy: tuple[float, float]
    angle_deg: float
    bbox_xywh: tuple[int, int, int, int]
    area_px: float
    source_candidate_score: float
```

### Pattern 2: Robust Corner Ordering With Validation

**What:** Use a local function that validates shape `(4, 2)`, converts to `float64`, checks `np.isfinite`, rejects duplicate points, lexicographically sorts by x/y, sorts the two leftmost by y, and assigns the right-side pair by squared distance from TL. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html; CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**When to use:** Use before every perspective transform and before every center/angle calculation. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**Example:**

```python
# Source basis: robust TL/TR/BR/BL ordering avoids sum/diff ties documented by PyImageSearch. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]
def order_corners_xy(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float64)
    if pts.shape != (4, 2):
        raise ValueError(f"points must have shape (4, 2); got {pts.shape!r}")
    if not np.isfinite(pts).all():
        raise ValueError("points must be finite")
    if np.unique(pts, axis=0).shape[0] != 4:
        raise ValueError("points must contain four distinct corners")

    x_order = np.lexsort((pts[:, 1], pts[:, 0]))
    x_sorted = pts[x_order]
    left = x_sorted[:2]
    right = x_sorted[2:]

    left = left[np.argsort(left[:, 1])]
    tl, bl = left
    distances = np.sum((right - tl) ** 2, axis=1)
    tr, br = right[np.argsort(distances)]
    return np.array([tl, tr, br, bl], dtype=np.float64)
```

### Pattern 3: Fixed Destination Grid for Warp

**What:** Map ordered source points to `[[0,0], [N-1,0], [N-1,N-1], [0,N-1]]`, compute a `3x3` perspective matrix, and call `cv2.warpPerspective(frame_bgr, matrix, (N, N), flags=cv2.INTER_LINEAR)`. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**When to use:** Use for every Phase 5 classifier crop; default `N=128` because CLAUDE.md explicitly names 128x128 as the low-latency classifier warp. [VERIFIED: CLAUDE.md]

**Example:**

```python
# Source basis: OpenCV getPerspectiveTransform takes four corresponding points; warpPerspective output size is (width, height). [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
def warp_face_bgr(frame_bgr: np.ndarray, ordered: np.ndarray, crop_size_px: int = 128) -> np.ndarray:
    src = np.asarray(ordered, dtype=np.float32)
    max_xy = float(crop_size_px - 1)
    dst = np.array(
        [[0.0, 0.0], [max_xy, 0.0], [max_xy, max_xy], [0.0, max_xy]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(frame_bgr, matrix, (crop_size_px, crop_size_px), flags=cv2.INTER_LINEAR)
```

### Pattern 4: Center and Angle From Ordered Corners Only

**What:** Compute the center as the arithmetic mean of the four ordered corners and compute angle from the top edge vector `TR - TL`. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.python.org/3/library/math.html]

**When to use:** Use after ordering and before contract conversion; do not use bbox center, image moments, or `minAreaRect.angle` for GEO-05. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source basis: GEO-05 defines center as mean and angle as atan2(TR - TL). [VERIFIED: .planning/REQUIREMENTS.md]
def compute_center_angle(ordered: np.ndarray) -> tuple[tuple[float, float], float]:
    center = np.mean(ordered, axis=0, dtype=np.float64)
    tl, tr = ordered[0], ordered[1]
    dx = float(tr[0] - tl[0])
    dy = float(tr[1] - tl[1])
    angle_deg = math.degrees(math.atan2(dy, dx))
    return (float(center[0]), float(center[1])), angle_deg
```

### Anti-Patterns to Avoid

- **Using `candidate.approx_xy` directly as TL/TR/BR/BL:** Phase 3 emits unordered quad vertices, and Phase 4 owns ordering. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md; VERIFIED: src/block_detected/detector.py]
- **Using sum/diff-only corner ordering:** Equal sums or differences can select the wrong point and break clockwise ordering. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]
- **Using bbox crop plus `cv2.resize`:** GEO-04 requires perspective warp from four corners, not an axis-aligned crop. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]
- **Using `minAreaRect.angle` for contract angle:** GEO-05 defines the angle from `TR - TL`, so another OpenCV angle convention is unnecessary. [VERIFIED: .planning/REQUIREMENTS.md]
- **Returning `DetectionResult(status=OK)` from Phase 4:** Block identity and confidence are Phase 5, and full reject/integration is Phase 7. [VERIFIED: .planning/ROADMAP.md; VERIFIED: src/block_detected/detection_contract.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Perspective matrix solving | Custom 3x3 homography solver. [ASSUMED] | `cv2.getPerspectiveTransform`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | OpenCV already calculates the transform from four corresponding point pairs. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| Image resampling | Manual pixel interpolation loops. [ASSUMED] | `cv2.warpPerspective`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | OpenCV handles inverse mapping, interpolation flags, border modes, and output size. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| Classifier crop normalization | Axis-aligned bbox crop plus resize. [ASSUMED] | Ordered-corner perspective warp. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html] | Bbox crop keeps rotation/skew; the classifier should see a fixed square plane. [VERIFIED: .planning/research/ARCHITECTURE.md] |
| Center calculation | Bbox center or contour moment center. [ASSUMED] | `np.mean(ordered, axis=0, dtype=np.float64)`. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] | GEO-05 explicitly defines center as the mean of ordered corners. [VERIFIED: .planning/REQUIREMENTS.md] |
| Angle calculation | `minAreaRect.angle` or bbox slope heuristics. [ASSUMED] | `math.atan2(TR.y - TL.y, TR.x - TL.x)` followed by `math.degrees`. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.python.org/3/library/math.html] | GEO-05 explicitly defines top-edge orientation from `TR - TL`. [VERIFIED: .planning/REQUIREMENTS.md] |
| Semantic upright rotation | Guessing which physical block face edge is "top" from a symmetric square contour alone. [ASSUMED] | Emit image-space TL/TR/BR/BL plus angle; let Phase 5 train with rotations or define a classifier-side orientation strategy if needed. [VERIFIED: .planning/ROADMAP.md; ASSUMED] | A square contour has rotational ambiguity without an asymmetric visual cue, and Phase 4 has no marker/classifier signal by scope. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] |

**Key insight:** Phase 4 should be small but exact: it should normalize geometric coordinates and pixels, not decide block identity, robot coordinates, or reject policy. [VERIFIED: .planning/ROADMAP.md]

## Common Pitfalls

### Pitfall 1: Treating OpenCV Contour Order as Stable

**What goes wrong:** Warped crops are mirrored, rotated, or inconsistent across frames. [ASSUMED]

**Why it happens:** Phase 3 `SquareCandidate.approx_xy` is intentionally unordered and `approxPolyDP` only approximates polygon vertices. [VERIFIED: src/block_detected/detector.py; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]

**How to avoid:** Always call `order_corners_xy()` before center, angle, or warp. [VERIFIED: .planning/REQUIREMENTS.md]

**Warning signs:** A color-coded synthetic quad produces a warp with corners in the wrong output quadrants. [ASSUMED]

### Pitfall 2: Sum/Diff Corner Ordering Fails on Tie Cases

**What goes wrong:** One rotated or perspective-skewed candidate gets assigned duplicate/wrong semantic corners. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**Why it happens:** The min/max sum or difference of x/y coordinates can tie, making the selected index ambiguous. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/]

**How to avoid:** Use the x-sort/y-sort/distance method and test all 24 permutations of at least one skewed quadrilateral. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/; ASSUMED]

**Warning signs:** Tests pass for axis-aligned rectangles but fail for diamond-like or skewed quads. [ASSUMED]

### Pitfall 3: Passing the Wrong Point Type or Shape to OpenCV

**What goes wrong:** `getPerspectiveTransform` raises an OpenCV assertion or returns a matrix that creates an invalid crop. [ASSUMED]

**Why it happens:** OpenCV's perspective tutorial uses `np.float32` source and destination point arrays, and the API computes a transform from four corresponding vertices. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**How to avoid:** Keep ordering and center math in `float64`, then cast ordered/destination points to `np.float32` immediately before `cv2.getPerspectiveTransform`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html; CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]

**Warning signs:** Geometry tests behave differently across OpenCV versions or fail only in the warp call. [ASSUMED]

### Pitfall 4: Swapping OpenCV `dsize` Width and Height

**What goes wrong:** Non-square future crops or debug outputs come out transposed. [ASSUMED]

**Why it happens:** OpenCV documents transform output size as `(width, height)`, while NumPy image shapes are `(height, width, channels)`. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]

**How to avoid:** For Phase 4 square crops, call `cv2.warpPerspective(..., (crop_size_px, crop_size_px))` and assert output shape `(crop_size_px, crop_size_px, 3)`. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; ASSUMED]

**Warning signs:** Shape assertions pass for square crops but helper signatures become confusing when a future non-square crop is tested. [ASSUMED]

### Pitfall 5: Angle Sign Convention Surprises Pose Mapping

**What goes wrong:** Later robot yaw appears inverted even though Phase 4 tests pass. [ASSUMED]

**Why it happens:** Image coordinates use y increasing downward, so `atan2(TR.y - TL.y, TR.x - TL.x)` produces positive angles for clockwise downward top-edge rotation in image space. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.python.org/3/library/math.html; ASSUMED]

**How to avoid:** Document `angle_deg` as image-space top-edge angle in Phase 4 and let Phase 6 own robot/world convention conversion. [VERIFIED: .planning/ROADMAP.md]

**Warning signs:** A synthetic top edge from `(100,100)` to `(200,150)` should produce about `+26.565` degrees in Phase 4 tests. [ASSUMED]

### Pitfall 6: Crop Size Drift Breaks Classifier Interface

**What goes wrong:** Phase 5 trains or loads a model expecting one input size while Phase 4 emits another. [ASSUMED]

**Why it happens:** Requirements allow 128x128 or 160x160, but CLAUDE.md and stack research name 128x128 as the low-latency default. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md; VERIFIED: .planning/research/STACK.md]

**How to avoid:** Put `crop_size_px=128` in `GeometrySettings` and `config/vision.example.json`; only change to 160 if Phase 5 model input metadata requires it. [VERIFIED: config/vision.example.json; ASSUMED]

**Warning signs:** Tests hardcode 128 in multiple places instead of reading one settings object. [ASSUMED]

### Pitfall 7: Invalid Quads Are Silently Warped

**What goes wrong:** A near-collinear or duplicate-point quad returns a mostly black, stretched, or unstable crop. [ASSUMED]

**Why it happens:** Perspective transformation requires four point correspondences, and the OpenCV tutorial notes that three of the four points should not be collinear. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]

**How to avoid:** Validate finite unique points, minimum side length, and positive polygon area before warp; expose invalid geometry errors for Phase 7 to map to `DetectionStatus.INVALID_GEOMETRY`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; VERIFIED: .planning/ROADMAP.md]

**Warning signs:** `cv2.contourArea(ordered.astype(np.float32))` is zero or side lengths are near zero. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED]

## Code Examples

Verified patterns from current docs and local source:

### Geometry Settings and Dataclass

```python
# Source basis: Phase 4 should default to 128x128 because CLAUDE.md names that classifier warp. [VERIFIED: CLAUDE.md]
from dataclasses import dataclass

@dataclass(frozen=True)
class GeometrySettings:
    crop_size_px: int = 128
    min_side_px: float = 8.0

    def __post_init__(self) -> None:
        if self.crop_size_px <= 0:
            raise ValueError("crop_size_px must be positive")
        if self.min_side_px <= 0:
            raise ValueError("min_side_px must be positive")
```

### Candidate to Geometry

```python
# Source basis: SquareCandidate contains unordered approx_xy, area, bbox, score. [VERIFIED: src/block_detected/detector.py]
def geometry_from_candidate(frame_bgr: np.ndarray, candidate: SquareCandidate, settings: GeometrySettings) -> FaceGeometry:
    ordered = order_corners_xy(candidate.approx_xy)
    validate_ordered_quad(ordered, settings)
    warp = warp_face_bgr(frame_bgr, ordered, crop_size_px=settings.crop_size_px)
    center_xy, angle_deg = compute_center_angle(ordered)
    return FaceGeometry(
        ordered_corners_xy=ordered,
        warp_bgr=warp,
        center_xy=center_xy,
        angle_deg=angle_deg,
        bbox_xywh=candidate.bbox_xywh,
        area_px=float(candidate.area_px),
        source_candidate_score=float(candidate.score),
    )
```

### Contract Corner Conversion

```python
# Source basis: CornersPx.as_ordered_tuple returns TL, TR, BR, BL. [VERIFIED: src/block_detected/detection_contract.py]
def corners_to_contract(ordered: np.ndarray) -> CornersPx:
    tl, tr, br, bl = ordered
    return CornersPx(
        top_left=PointPx(float(tl[0]), float(tl[1])),
        top_right=PointPx(float(tr[0]), float(tr[1])),
        bottom_right=PointPx(float(br[0]), float(br[1])),
        bottom_left=PointPx(float(bl[0]), float(bl[1])),
    )
```

### Warp Orientation Test Fixture

```python
# Source basis: Perspective transform requires ordered corresponding source and destination vertices. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html]
def test_warp_maps_color_coded_corners_to_output_quadrants() -> None:
    frame, unordered_points = make_color_coded_quad_fixture()
    ordered = order_corners_xy(unordered_points)
    warp = warp_face_bgr(frame, ordered, crop_size_px=128)
    assert warp.shape == (128, 128, 3)
    assert top_left_patch_is_expected_color(warp)
    assert top_right_patch_is_expected_color(warp)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sum/diff corner ordering. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | X-sort/y-sort/distance ordering with permutation tests. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | PyImageSearch documented the bug and improved method in 2016. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | Planner should include explicit tie/permutation tests, not only happy-path square tests. [ASSUMED] |
| Axis-aligned crop and resize. [ASSUMED] | Four-corner perspective warp. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html] | OpenCV 4.x docs still prescribe four source and destination points for perspective correction. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html] | Phase 4 should use `getPerspectiveTransform` and `warpPerspective`, not bbox crop normalization. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| Angle from rotated rectangle metadata. [ASSUMED] | Contract-defined top-edge angle from ordered corners. [VERIFIED: .planning/REQUIREMENTS.md] | Requirement GEO-05 defines this project convention. [VERIFIED: .planning/REQUIREMENTS.md] | Tests should assert exact formula against synthetic known angles. [ASSUMED] |
| Classification on full 640x480 frame. [VERIFIED: .planning/research/STACK.md says to avoid full-frame heavy models] | Detect square cheaply, warp small face crop, classify later. [VERIFIED: .planning/research/STACK.md; VERIFIED: CLAUDE.md] | Project stack research selected contour + warp + tiny CNN before Phase 4. [VERIFIED: .planning/research/STACK.md] | Phase 4 is the normalization boundary for Phase 5. [VERIFIED: .planning/ROADMAP.md] |

**Deprecated/outdated:**

- Using OpenCV 2.x/3.x tutorial assumptions without checking OpenCV 4.x signatures is outdated for this project. [VERIFIED: .planning/research/STACK.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]
- Adding `imutils` solely for `order_points` is unnecessary because the project can implement and test the small NumPy ordering function locally. [VERIFIED: .planning/research/STACK.md; ASSUMED]
- Solving block orientation with ArUco/AprilTag markers is out of scope for v1. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Phase 4 default crop should be 128x128, with 160x160 only if Phase 5 model metadata later requires it. | Summary, Standard Stack, Pitfalls | If the final classifier is designed around 160x160, Phase 4 tests/config need one coordinated size change. |
| A2 | A local NumPy `order_corners_xy()` is preferred over adding `imutils`. | Standard Stack, State of the Art | If the project standardizes on `imutils` later, the local function may duplicate dependency behavior. |
| A3 | Phase 4 should expose geometry helpers and package exports but should not replace the public `detect_block` stub with real pipeline behavior yet. | Architecture Patterns | If the planner wants early integration, Phase 4 could add a non-classifying internal pipeline helper, but it still cannot return `OK` without Phase 5 identity/confidence. |
| A4 | Square contour geometry alone cannot guarantee semantic upright orientation of a symmetric face crop. | Don't Hand-Roll, Open Questions | If block faces have asymmetric visual markings, Phase 5 may define orientation normalization or rotation augmentation. |

## Open Questions

1. **Should the canonical crop stay at 128x128 or switch to 160x160?**
   - What we know: Requirements allow either, while CLAUDE.md and stack research name 128x128. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: CLAUDE.md; VERIFIED: .planning/research/STACK.md]
   - What's unclear: Phase 5 model input shape does not exist yet. [VERIFIED: .planning/ROADMAP.md]
   - Recommendation: Use `GeometrySettings(crop_size_px=128)` and a config field, then let Phase 5 lock model input shape. [ASSUMED]

2. **Does Phase 5 need semantic upright crops or only perspective-normalized crops?**
   - What we know: Phase 4 can produce consistent image-space TL/TR/BR/BL warps and `angle_deg`. [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: The classifier's block-face markings and rotation sensitivity are not specified. [VERIFIED: .planning/REQUIREMENTS.md]
   - Recommendation: Phase 4 should not rotate crops to guessed semantic orientation; Phase 5 should train with rotations or define a classifier-side orientation strategy if required. [ASSUMED]

3. **Should invalid geometry become exceptions or structured invalid results in Phase 4?**
   - What we know: Phase 7 owns `invalid_geometry` rejection status, while Phase 4 owns geometry computation. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: The planner may prefer exceptions for pure helpers or a `GeometryResult` union for easier Phase 7 mapping. [ASSUMED]
   - Recommendation: Raise `ValueError` from pure helpers in Phase 4 tests and keep error messages stable enough for Phase 7 to map later. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All Phase 4 code/tests | yes | 3.14.4 local; target Pi 3.11.x from stack docs. [VERIFIED: local `python3 --version`; VERIFIED: .planning/research/STACK.md] | None needed. [ASSUMED] |
| OpenCV Python `cv2` | `getPerspectiveTransform`, `warpPerspective`, image fixtures | no in current shell | Missing import. [VERIFIED: local import probe] | Install dev extras with `python -m pip install -e ".[dev]"`. [VERIFIED: pyproject.toml] |
| NumPy | Point math, means, tests | no in current shell | Missing import. [VERIFIED: local import probe] | Install dev extras with `python -m pip install -e ".[dev]"`. [VERIFIED: pyproject.toml] |
| pytest | Nyquist validation tests | no in current shell | Missing import. [VERIFIED: local import probe] | Install dev extras with `python -m pip install -e ".[dev]"`. [VERIFIED: pyproject.toml] |
| Synthetic image fixtures | Warp and geometry tests | yes | `tests/fixtures/vision/square_face.png`, `tests/fixtures/frames/frame.png`. [VERIFIED: local image fixture scan] | Add a color-coded synthetic quad fixture in `tests/test_geometry.py` if existing grayscale fixture is insufficient for orientation assertions. [ASSUMED] |
| Real captured reference frames | Field realism | no | Only synthetic fixtures are documented. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md; VERIFIED: local image fixture scan] | Synthetic tests are enough for Phase 4 mechanics; real frames can wait for Phase 8 evaluation. [VERIFIED: .planning/ROADMAP.md; ASSUMED] |

**Missing dependencies with no fallback:**

- OpenCV Python and NumPy are required to run Phase 4 geometry tests in the current shell. [VERIFIED: local import probe; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html]

**Missing dependencies with fallback:**

- pytest is missing in the current shell, but the repo declares pytest in dev extras and existing tests use pytest. [VERIFIED: local import probe; VERIFIED: pyproject.toml; VERIFIED: tests/test_detector.py]
- Real captured reference frames are absent, but Phase 4 can validate deterministic geometry with synthetic arrays. [VERIFIED: local image fixture scan; ASSUMED]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=9`, current PyPI `9.0.3`, missing in current shell. [VERIFIED: pyproject.toml; VERIFIED: local PyPI JSON query; VERIFIED: local import probe] |
| Config file | `pyproject.toml` with `testpaths = ["tests"]`. [VERIFIED: pyproject.toml] |
| Quick run command | `python -m pytest tests/test_geometry.py -q`. [ASSUMED] |
| Full suite command | `python -m pytest -q`. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| GEO-03 | `order_corners_xy()` returns TL, TR, BR, BL for every permutation of an axis-aligned quad. [VERIFIED: .planning/REQUIREMENTS.md] | unit | `python -m pytest tests/test_geometry.py::test_order_corners_handles_all_axis_aligned_permutations -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-03 | `order_corners_xy()` returns stable order for rotated/skewed quads and avoids sum/diff tie failures. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/] | unit | `python -m pytest tests/test_geometry.py::test_order_corners_handles_skewed_and_diamond_quads -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-03 | Invalid point arrays with wrong shape, duplicate corners, or non-finite values raise `ValueError`. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html] | unit | `python -m pytest tests/test_geometry.py::test_order_corners_rejects_invalid_points -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-04 | `warp_face_bgr()` returns `(128, 128, 3)` `uint8` by default and does not mutate source frame. [VERIFIED: CLAUDE.md; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] | unit | `python -m pytest tests/test_geometry.py::test_warp_face_default_128_uint8_non_mutating -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-04 | Color-coded source corners land in expected output quadrants after warp. [CITED: https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html] | unit | `python -m pytest tests/test_geometry.py::test_warp_maps_ordered_corners_to_output_quadrants -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-05 | `center_px` equals `np.mean(ordered, axis=0)` within float tolerance. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://numpy.org/doc/stable/reference/generated/numpy.mean.html] | unit | `python -m pytest tests/test_geometry.py::test_center_is_mean_of_ordered_corners -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-05 | `angle_deg` equals `degrees(atan2(TR.y - TL.y, TR.x - TL.x))` for 0, positive, and negative image-space top-edge slopes. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.python.org/3/library/math.html] | unit | `python -m pytest tests/test_geometry.py::test_angle_uses_top_edge_atan2_convention -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |
| GEO-03/GEO-04/GEO-05 | `geometry_from_candidate()` consumes Phase 3 `SquareCandidate` and returns coherent `FaceGeometry`. [VERIFIED: src/block_detected/detector.py] | integration | `python -m pytest tests/test_geometry.py::test_geometry_from_square_candidate_end_to_end -q` | no, Wave 0. [VERIFIED: local `rg --files tests`] |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_geometry.py -q`. [ASSUMED]
- **Per wave merge:** `python -m pytest -q`. [VERIFIED: .planning/phases/03-preprocess-contour-detection/03-03-SUMMARY.md]
- **Phase gate:** Full suite green after installing dev extras, with geometry tests proving order, warp shape/orientation, and center/angle formula. [VERIFIED: .planning/config.json; ASSUMED]

### Wave 0 Gaps

- [ ] `src/block_detected/geometry.py` - covers `GeometrySettings`, `FaceGeometry`, `order_corners_xy`, `warp_face_bgr`, `compute_center_angle`, and `geometry_from_candidate`. [ASSUMED]
- [ ] `tests/test_geometry.py` - covers GEO-03, GEO-04, and GEO-05. [ASSUMED]
- [ ] `config/vision.example.json` geometry section - documents `crop_size_px=128` and any validation thresholds. [VERIFIED: config/vision.example.json currently has preprocess/detector only]
- [ ] `src/block_detected/__init__.py` exports for new geometry types/helpers. [VERIFIED: src/block_detected/__init__.py currently exports Phase 1-3 symbols]
- [ ] Dev environment install: `python -m pip install -e ".[dev]"` before running OpenCV/NumPy/pytest tests in the current shell. [VERIFIED: local import probe; VERIFIED: pyproject.toml]

## Security Domain

Security enforcement is enabled by default because `.planning/config.json` does not explicitly set `security_enforcement: false`. [VERIFIED: .planning/config.json]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Phase 4 has no authentication surface. [VERIFIED: .planning/ROADMAP.md] |
| V3 Session Management | no | Phase 4 has no sessions. [VERIFIED: .planning/ROADMAP.md] |
| V4 Access Control | no | Phase 4 has no user authorization boundary. [VERIFIED: .planning/ROADMAP.md] |
| V5 Input Validation | yes | Validate frame shape/dtype, point array shape, finiteness, uniqueness, side lengths, crop size, and warp output shape before downstream use. [VERIFIED: src/block_detected/preprocess.py; CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html; CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html] |
| V6 Cryptography | no | Phase 4 has no cryptographic operation. [VERIFIED: .planning/ROADMAP.md] |

### Known Threat Patterns for Geometry Processing

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed or non-finite corner arrays crash OpenCV or generate invalid matrices. [ASSUMED] | Denial of Service | Validate shape `(4, 2)`, dtype-converted finite values, uniqueness, side lengths, and area before warp. [CITED: https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| Oversized or zero crop size allocates unexpected memory or fails in OpenCV. [ASSUMED] | Denial of Service | Bound `crop_size_px` to positive configured values and test 128 default. [VERIFIED: CLAUDE.md; ASSUMED] |
| Fabricated geometry on bad candidates reaches robot integration later. [VERIFIED: .planning/REQUIREMENTS.md says rejected/ambiguous frames must not include fake geometry] | Tampering / Safety | Phase 4 should raise/flag invalid geometry, and Phase 7 should map that to `DetectionStatus.INVALID_GEOMETRY` with no candidate fields. [VERIFIED: .planning/ROADMAP.md; VERIFIED: src/block_detected/detection_contract.py] |
| Debug overlays or crop dumps fill disk if added later. [VERIFIED: Phase 2 delivered retention controls] | Denial of Service | Reuse Phase 2 `DebugFrameWriter` retention/sampling when saving warps. [VERIFIED: .planning/phases/02-camera-capture/02-03-SUMMARY.md; VERIFIED: src/block_detected/debug.py] |

## Sources

### Primary (HIGH confidence)

- https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html - `getPerspectiveTransform`, `warpPerspective`, matrix/dsize/flags behavior. [CITED]
- https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html - OpenCV perspective-transform tutorial with four point pairs, `np.float32`, and output-size convention. [CITED]
- https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html - `contourArea`, `boundingRect`, `minAreaRect`, `approxPolyDP`, and shape descriptors used around geometry validation. [CITED]
- https://numpy.org/doc/stable/reference/generated/numpy.mean.html - `np.mean` axis/dtype behavior for center calculation. [CITED]
- https://numpy.org/doc/stable/reference/generated/numpy.isfinite.html - finite-point validation. [CITED]
- https://docs.python.org/3/library/math.html - `math.atan2` quadrant-aware angle and radians behavior. [CITED]
- `src/block_detected/detector.py` - Phase 3 `SquareCandidate` input interface. [VERIFIED]
- `src/block_detected/detection_contract.py` - `CornersPx`, `PointPx`, status geometry rules, and contract conversion targets. [VERIFIED]
- `src/block_detected/vision.py` - Phase 3 frame helper and candidate overlay boundary. [VERIFIED]
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `CLAUDE.md` - Phase scope, crop-size allowance, project constraints, and out-of-scope phases. [VERIFIED]

### Secondary (MEDIUM confidence)

- https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/ - robust corner-ordering pattern and sum/diff bug explanation. [CITED]
- `.planning/research/STACK.md` - project stack decisions for OpenCV/NumPy/pytest and 128x128 warp direction. [VERIFIED]
- `.planning/research/ARCHITECTURE.md` - pipeline stage boundary for `geometry.py`. [VERIFIED]
- `.planning/research/PITFALLS.md` - wrong-corner-order pitfall. [VERIFIED]
- `.planning/phases/03-preprocess-contour-detection/03-*-SUMMARY.md` - implemented Phase 3 handoff and out-of-scope notes. [VERIFIED]
- Local PyPI index and JSON queries for current package versions and publish dates. [VERIFIED]

### Tertiary (LOW confidence)

- Assumptions around semantic-upright classifier orientation and exact invalid-geometry thresholds remain pending Phase 5/7 decisions. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - OpenCV, NumPy, Python `math`, pytest versions and APIs were verified via official docs, local `pyproject.toml`, and PyPI queries. [CITED: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html; VERIFIED: pyproject.toml; VERIFIED: local PyPI JSON query]
- Architecture: HIGH - Phase 3 source now defines the exact candidate handoff, and roadmap/requirements define Phase 4 outputs. [VERIFIED: src/block_detected/detector.py; VERIFIED: .planning/ROADMAP.md]
- Pitfalls: MEDIUM - API pitfalls are verified, while semantic-upright and real-image robustness depend on block markings and captured fixtures not specified yet. [CITED: https://pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/; ASSUMED]
- Validation: MEDIUM - Test architecture is clear, but current shell lacks OpenCV/NumPy/pytest until dev extras are installed. [VERIFIED: local import probe; VERIFIED: pyproject.toml]

**Research date:** 2026-05-31 [VERIFIED: local environment context]  
**Valid until:** 2026-06-30 for OpenCV geometry APIs; revisit within 7 days of Phase 5 choosing model input shape or target-Pi dependency pins. [ASSUMED]
