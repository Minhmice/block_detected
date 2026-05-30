# Phase 3: Preprocess & Contour Detection - Research

**Researched:** 2026-05-31 [VERIFIED: local environment context]
**Domain:** OpenCV preprocessing, binary mask generation, contour extraction, and square-face candidate filtering [VERIFIED: .planning/ROADMAP.md; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
**Confidence:** HIGH for OpenCV API usage and project constraints; MEDIUM for initial numeric thresholds because no reference images exist in the repo yet [VERIFIED: repo image fixture scan; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]

## User Constraints

No phase `CONTEXT.md` exists for Phase 3, so there are no additional locked decisions, discretion notes, or deferred ideas from `/gsd-discuss-phase`. [VERIFIED: `gsd-tools.cjs init phase-op 3` returned `has_context=false`]

### Locked Decisions

- Phase 3 goal is to produce filtered square-face contour candidates ready for geometry. [VERIFIED: .planning/ROADMAP.md]
- Phase 3 depends on Phase 2. [VERIFIED: .planning/ROADMAP.md]
- Phase 3 must address GEO-01 and GEO-02. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]
- Downstream frame input should be treated as normalized 640x480 BGR with monotonic `frame_id`, because the prompt says Phase 2 research contract is authoritative even though Phase 2 plans are not fully verified. [VERIFIED: user prompt; VERIFIED: .planning/phases/02-camera-capture/02-RESEARCH.md]
- v1 forbids ArUco and AprilTag markers on blocks. [VERIFIED: .planning/PROJECT.md; VERIFIED: .planning/REQUIREMENTS.md]
- Phase 4 owns corner ordering, perspective warp, center, and angle calculations, so Phase 3 should not finalize TL/TR/BR/BL ordering or `DetectionResult` geometry. [VERIFIED: .planning/ROADMAP.md]

### Claude's Discretion

- No Phase 3 discretion section exists; module split, config field names, default threshold mode, and initial filter constants are planner choices constrained by OpenCV best practice and existing project contracts. [VERIFIED: `gsd-tools.cjs init phase-op 3`; VERIFIED: .planning/ROADMAP.md]

### Deferred Ideas (OUT OF SCOPE)

- Corner ordering, `warpPerspective`, center, and `angle_deg` are Phase 4. [VERIFIED: .planning/ROADMAP.md]
- TFLite classification is Phase 5. [VERIFIED: .planning/ROADMAP.md]
- Pose calibration is Phase 6. [VERIFIED: .planning/ROADMAP.md]
- Full reject integration for no detection, invalid geometry, overlapping candidates, and low classifier confidence is Phase 7, though Phase 3 should expose enough candidate metadata for those later decisions. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/REQUIREMENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEO-01 | Preprocess chain: BGR to gray, light blur, adaptive threshold or Canny, morphology open/close. [VERIFIED: .planning/REQUIREMENTS.md] | Use `cv.cvtColor(..., cv.COLOR_BGR2GRAY)`, `cv.GaussianBlur`, `cv.adaptiveThreshold` or `cv.Canny`, then `cv.morphologyEx` with `MORPH_OPEN` and `MORPH_CLOSE`. [CITED: https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html; CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html; CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html] |
| GEO-02 | Find square-face candidates via contours plus `approxPolyDP`: 4 vertices, convex, area min/max, aspect approximately 1:1. [VERIFIED: .planning/REQUIREMENTS.md] | Use `cv.findContours(..., cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)`, `cv.contourArea`, `cv.arcLength`, `cv.approxPolyDP`, `cv.isContourConvex`, `cv.boundingRect`, and optionally `cv.minAreaRect` for rotation-tolerant aspect scoring. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; CITED: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html] |
</phase_requirements>

## Summary

Phase 3 should create a deterministic OpenCV geometry front-end that accepts a Phase 2 `CaptureFrame` or raw 640x480 BGR array and returns ranked `ContourCandidate` records, not final detections. [VERIFIED: .planning/ROADMAP.md; VERIFIED: .planning/phases/02-camera-capture/02-RESEARCH.md] The preprocessing output must be an 8-bit single-channel binary/edge mask because OpenCV documents `findContours` as finding contours in a binary image. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html]

The standard contour pipeline is still appropriate for this controlled v1 problem because the visible square face is the geometry primitive the robot needs, and later phases handle corner ordering, warping, classification, and reject integration. [VERIFIED: .planning/PROJECT.md; VERIFIED: .planning/ROADMAP.md] Numeric thresholds should be configuration values and test fixture expectations, not hidden constants, because lighting, block size in pixels, glare, and pallet contrast are project variables that are not represented by repo fixtures yet. [VERIFIED: repo image fixture scan; ASSUMED]

**Primary recommendation:** Implement `src/block_detected/preprocess.py` for mask generation, `src/block_detected/contours.py` for candidate extraction/filtering, and `src/block_detected/debug_overlay.py` for visual diagnostics; add synthetic-image tests first, then at least one real reference image test when capture fixtures exist. [VERIFIED: existing `src/block_detected` package layout; VERIFIED: .planning/ROADMAP.md; ASSUMED]

## Project Constraints (from CLAUDE.md)

- The project is a Raspberry Pi / edge vision pipeline that detects four cube blocks without ArUco markers. [VERIFIED: CLAUDE.md]
- The core value is reliable block ID plus correctly ordered corners and angle for robot pickup, not just a bounding box. [VERIFIED: CLAUDE.md]
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
| Python | Target Pi: 3.11.x; local host: 3.14.4. [VERIFIED: .planning/research/STACK.md; VERIFIED: local `python3 --version`] | Runtime for candidate extraction modules and tests. [VERIFIED: CLAUDE.md] | Existing package requires Python `>=3.11`. [VERIFIED: pyproject.toml] |
| OpenCV Python (`opencv-python`) | 4.13.0.92 current on PyPI as of 2026-05-31. [VERIFIED: `python3 -m pip index versions opencv-python`] | Grayscale conversion, blur, threshold/Canny, morphology, contours, polygon approximation, and debug drawing. [CITED: https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | OpenCV provides the exact APIs named by GEO-01 and GEO-02. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| NumPy | 2.4.6 current on PyPI as of 2026-05-31. [VERIFIED: `python3 -m pip index versions numpy`] | Array typing, synthetic image fixtures, candidate point arrays, and mask assertions. [VERIFIED: .planning/research/STACK.md; ASSUMED] | OpenCV Python returns and accepts NumPy arrays in the project stack. [VERIFIED: .planning/research/STACK.md] |
| pytest | 9.0.3 current on PyPI as of 2026-05-31. [VERIFIED: `python3 -m pip index versions pytest`] | Fast unit tests for preprocessing, contour filtering, and fixture detection. [VERIFIED: .planning/config.json `nyquist_validation=true`; ASSUMED] | Phase 2 validation already selected pytest for camera/debug modules, so Phase 3 should continue that test runner. [VERIFIED: .planning/phases/02-camera-capture/02-VALIDATION.md] |

### Supporting

| Library / API | Version | Purpose | When to Use |
|---------------|---------|---------|-------------|
| `cv.cvtColor` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html] | Convert normalized BGR frames to grayscale. [VERIFIED: GEO-01 in .planning/REQUIREMENTS.md] | Always first preprocessing step for threshold/Canny modes. [VERIFIED: .planning/REQUIREMENTS.md] |
| `cv.GaussianBlur` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html] | Light noise reduction before thresholding or Canny. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html] | Use odd positive kernels such as `(3, 3)` or `(5, 5)` as config. [CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html] |
| `cv.adaptiveThreshold` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html] | Binary mask generation under uneven lighting. [CITED: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html] | Default Phase 3 threshold mode for block face masks unless reference images prove Canny is better. [ASSUMED] |
| `cv.Canny` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html] | Edge mask generation for visible high-contrast face boundaries. [VERIFIED: GEO-01 in .planning/REQUIREMENTS.md] | Keep as configurable alternative and useful debug comparison. [VERIFIED: .planning/REQUIREMENTS.md; ASSUMED] |
| `cv.morphologyEx` + `cv.getStructuringElement` | OpenCV 4.x API. [CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html; CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html] | Remove small white noise and close small holes or edge breaks. [CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html] | Apply after binary/edge mask generation with configurable kernel and iterations. [ASSUMED] |
| `cv.drawContours`, `cv.polylines`, `cv.putText` | OpenCV 4.x drawing APIs. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html] | Debug overlays for raw contours, accepted candidates, and rejection reasons. [VERIFIED: Phase 3 prompt asks to include debug overlays] | Use for artifact inspection, not as detection logic. [ASSUMED] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `adaptiveThreshold` default [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html] | `Canny` default [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html] | Canny localizes edges but can create broken contours that need closing; adaptive threshold can preserve filled face regions but can merge foreground with shadows or texture. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html; ASSUMED] |
| `RETR_EXTERNAL` [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | `RETR_TREE` [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | External retrieval reduces duplicate inner contours for a single face; tree retrieval is useful only if holes/nested face markings matter for candidate extraction, which Phase 3 does not require. [VERIFIED: GEO-02 in .planning/REQUIREMENTS.md; ASSUMED] |
| `CHAIN_APPROX_SIMPLE` [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | `CHAIN_APPROX_NONE` [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Simple mode compresses rectangle-like contours to endpoints and is enough before `approxPolyDP`; none stores every boundary point and increases work without improving this phase's contract. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED] |
| Axis-aligned `boundingRect` aspect check [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Rotated `minAreaRect` aspect check [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | Axis-aligned aspect is simple but rejects rotated squares too aggressively; use `minAreaRect` aspect for primary filtering and keep `boundingRect` for debug bbox. [ASSUMED; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |

**Installation:**

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install "opencv-python==4.13.0.92" "numpy>=2.0,<3" "pytest==9.0.3"
```

**Version verification:** PyPI index queries returned `opencv-python 4.13.0.92`, `numpy 2.4.6`, and `pytest 9.0.3` on 2026-05-31. [VERIFIED: local `python3 -m pip index versions ...`] The local host currently does not have `cv2`, `numpy`, or `pytest` importable. [VERIFIED: local import probe]

## Architecture Patterns

### Recommended Project Structure

```text
src/block_detected/
  preprocess.py       # PreprocessConfig, PreprocessDebug, preprocess_frame_bgr().
  contours.py         # ContourFilterConfig, ContourCandidate, find_square_candidates().
  debug_overlay.py    # draw_preprocess_debug_overlay() and candidate annotations.
  pipeline.py         # Later integration; Phase 3 can remain callable directly from tests.
tests/
  test_preprocess.py  # synthetic BGR to binary mask checks.
  test_contours.py    # quad/area/aspect/convex filtering checks.
  fixtures/
    reference/        # real captured frames once Phase 2 artifacts exist.
```

### Pattern 1: Typed Config Objects for Tunables

**What:** Put threshold mode, blur kernel, Canny thresholds, adaptive block size/C, morphology kernels, area bounds, aspect tolerance, and approximation epsilon ratio in dataclasses. [ASSUMED]

**When to use:** Use for every preprocessing and contour call so field tuning changes config rather than code. [VERIFIED: Phase 3 success criteria require configured area/aspect bounds; ASSUMED]

**Example:**

```python
# Source basis: OpenCV adaptiveThreshold requires blockSize and C; Canny requires two thresholds; approxPolyDP uses epsilon. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html; CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
from dataclasses import dataclass
from typing import Literal, Tuple


@dataclass(frozen=True)
class PreprocessConfig:
    mode: Literal["adaptive_threshold", "canny"] = "adaptive_threshold"
    blur_kernel: Tuple[int, int] = (5, 5)
    adaptive_block_size: int = 31
    adaptive_c: int = 5
    canny_low: int = 50
    canny_high: int = 150
    morph_kernel: Tuple[int, int] = (3, 3)
    morph_open_iterations: int = 1
    morph_close_iterations: int = 1


@dataclass(frozen=True)
class ContourFilterConfig:
    min_area_px: float = 1_000.0
    max_area_px: float = 80_000.0
    aspect_min: float = 0.75
    aspect_max: float = 1.33
    approx_epsilon_ratio: float = 0.03
```

### Pattern 2: Preprocess Returns Named Intermediate Images

**What:** Return grayscale, blurred image, raw mask, morph-open mask, morph-close/final mask, and metadata rather than only final candidates. [ASSUMED]

**When to use:** Use during Phase 3 and later field tuning because most contour failures are caused by preprocessing, not the contour loop. [ASSUMED]

**Example:**

```python
# Source basis: cvtColor, GaussianBlur, adaptiveThreshold, Canny, morphologyEx are OpenCV's documented primitives for this chain. [CITED: https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html; CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html]
import cv2 as cv


def preprocess_frame_bgr(frame_bgr, config: PreprocessConfig):
    gray = cv.cvtColor(frame_bgr, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, config.blur_kernel, 0)

    if config.mode == "adaptive_threshold":
        raw_mask = cv.adaptiveThreshold(
            blurred,
            255,
            cv.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv.THRESH_BINARY,
            config.adaptive_block_size,
            config.adaptive_c,
        )
    else:
        raw_mask = cv.Canny(blurred, config.canny_low, config.canny_high)

    kernel = cv.getStructuringElement(cv.MORPH_RECT, config.morph_kernel)
    opened = cv.morphologyEx(raw_mask, cv.MORPH_OPEN, kernel, iterations=config.morph_open_iterations)
    final = cv.morphologyEx(opened, cv.MORPH_CLOSE, kernel, iterations=config.morph_close_iterations)
    return {"gray": gray, "blurred": blurred, "raw_mask": raw_mask, "opened": opened, "mask": final}
```

### Pattern 3: Contour Candidate Object With Rejection Metadata

**What:** Store approximated points, contour area, bounding rect, rotated aspect ratio, score, and rejection reason for every contour considered. [ASSUMED]

**When to use:** Use in `find_square_candidates()` so tests can assert why contours were rejected and overlays can label them. [ASSUMED]

**Example:**

```python
# Source basis: OpenCV documents contourArea, arcLength, approxPolyDP, isContourConvex, boundingRect, minAreaRect, RETR_EXTERNAL, and CHAIN_APPROX_SIMPLE. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; CITED: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html]
import cv2 as cv


def find_square_candidates(mask, config: ContourFilterConfig):
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    candidates = []

    for contour in contours:
        area = float(cv.contourArea(contour))
        if area < config.min_area_px or area > config.max_area_px:
            continue

        perimeter = cv.arcLength(contour, True)
        approx = cv.approxPolyDP(contour, config.approx_epsilon_ratio * perimeter, True)
        if len(approx) != 4:
            continue
        if not cv.isContourConvex(approx):
            continue

        (_, _), (width, height), _ = cv.minAreaRect(approx)
        short_side = max(1.0, min(float(width), float(height)))
        long_side = max(float(width), float(height))
        aspect = long_side / short_side
        if not (config.aspect_min <= aspect <= config.aspect_max):
            continue

        x, y, w, h = cv.boundingRect(approx)
        candidates.append({
            "contour": contour,
            "approx": approx.reshape(4, 2),
            "area_px": area,
            "aspect": aspect,
            "bbox_xywh": (x, y, w, h),
        })

    return sorted(candidates, key=lambda item: item["area_px"], reverse=True)
```

### Pattern 4: Debug Overlay Mirrors the Filter Pipeline

**What:** Draw all raw contours lightly, accepted quads strongly, and optional rejection labels on a copy of the BGR frame. [ASSUMED]

**When to use:** Use for Phase 3 reference-image validation and field tuning, not as a production dependency. [VERIFIED: Phase 3 prompt asks to include debug overlays; ASSUMED]

**Example:**

```python
# Source basis: OpenCV drawContours draws contour outlines or filled contours. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html]
import cv2 as cv


def draw_candidates_overlay(frame_bgr, candidates):
    overlay = frame_bgr.copy()
    for candidate in candidates:
        points = candidate["approx"].reshape((-1, 1, 2))
        cv.drawContours(overlay, [points], -1, (0, 255, 0), 2)
        x, y, _, _ = candidate["bbox_xywh"]
        cv.putText(
            overlay,
            f"area={candidate['area_px']:.0f} aspect={candidate['aspect']:.2f}",
            (x, max(0, y - 8)),
            cv.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv.LINE_AA,
        )
    return overlay
```

### Anti-Patterns to Avoid

- **Finalizing corner order in Phase 3:** Phase 4 owns TL/TR/BR/BL ordering and warp, so Phase 3 should emit unordered quad candidates plus enough metadata for Phase 4. [VERIFIED: .planning/ROADMAP.md]
- **Using only axis-aligned width/height for square tests:** A rotated square can have a non-square axis-aligned bounding box, so primary aspect filtering should use `minAreaRect` or side lengths of the approximated quad. [ASSUMED; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
- **Letting threshold constants live inside functions:** Phase 3 must be tunable across lighting and distance, and no real fixture set exists yet. [VERIFIED: repo image fixture scan; ASSUMED]
- **Passing grayscale directly to `findContours`:** The documented contour pipeline expects a binary image; tests should assert masks are `uint8` and contain only `0/255` for threshold mode. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]
- **Depending on candidate index order from OpenCV:** Sort candidates by explicit score such as area or geometry quality before returning. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Grayscale conversion | Manual weighted BGR channel math | `cv.cvtColor(frame, cv.COLOR_BGR2GRAY)` | OpenCV documents channel order and color conversions, including BGR defaults. [CITED: https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html] |
| Noise blur | Custom convolution loops | `cv.GaussianBlur` | OpenCV provides optimized Gaussian filtering with documented kernel constraints. [CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html] |
| Local thresholding | Per-pixel neighborhood threshold loops | `cv.adaptiveThreshold` | OpenCV already implements mean/Gaussian adaptive thresholding and requires 8-bit single-channel input. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html] |
| Edge detection | Sobel plus custom hysteresis | `cv.Canny` | OpenCV implements the full Canny pipeline including smoothing, gradients, non-maximum suppression, and hysteresis thresholds. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html] |
| Morphology | Manual erosion/dilation scans | `cv.morphologyEx` with `MORPH_OPEN` and `MORPH_CLOSE` | Opening and closing are standard erosion/dilation compositions in OpenCV. [CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html] |
| Contour extraction | Flood-fill or boundary tracing loops | `cv.findContours` | OpenCV provides contour retrieval modes and approximation modes. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| Polygon simplification | Custom vertex simplifier | `cv.approxPolyDP` | OpenCV implements Douglas-Peucker approximation with epsilon accuracy. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| Convexity check | Cross-product loops | `cv.isContourConvex` | OpenCV tests contour convexity and documents undefined output for self-intersections. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] |
| Debug contour rendering | Manual raster drawing | `cv.drawContours`, `cv.polylines`, `cv.putText` | OpenCV drawing APIs are documented for contour outlines and labels. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html] |

**Key insight:** The custom code in Phase 3 should orchestrate OpenCV primitives, preserve intermediate artifacts, and apply project-specific filtering; it should not reimplement image processing algorithms. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED]

## Common Pitfalls

### Pitfall 1: Adaptive Threshold Inverts the Object/Background Polarity

**What goes wrong:** The block face becomes black and the background becomes white, so `findContours` returns the table or shadows instead of the face. [ASSUMED]

**Why it happens:** `adaptiveThreshold` supports both `THRESH_BINARY` and `THRESH_BINARY_INV`, and OpenCV computes a local threshold per pixel. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]

**How to avoid:** Make threshold type configurable and include a synthetic test with a bright square on dark background and a dark square on bright background. [ASSUMED]

**Warning signs:** The largest contour is near the image border or has an area close to the full frame area. [ASSUMED]

### Pitfall 2: Invalid Adaptive Block Size

**What goes wrong:** OpenCV raises an error or produces unusable masks when block size is not an odd neighborhood size such as 3, 5, or 7. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]

**Why it happens:** `adaptiveThreshold` defines `blockSize` as the pixel neighborhood size, with examples `3, 5, 7, and so on`. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]

**How to avoid:** Validate config at construction time: `block_size >= 3` and odd. [ASSUMED]

**Warning signs:** Unit tests fail before contours are generated, or masks are almost all black/white. [ASSUMED]

### Pitfall 3: Canny Produces Broken Edge Contours

**What goes wrong:** A visible square face is present, but the contour approximation has more/fewer than four vertices or multiple partial contours. [ASSUMED]

**Why it happens:** Canny uses two hysteresis thresholds and accepts weak edges only when connected to strong edges. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html]

**How to avoid:** Blur before Canny, use a 2:1 to 3:1 high/low threshold ratio as a tuning baseline, and use closing to join small gaps. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html]

**Warning signs:** Overlay shows four line segments that do not form one closed contour. [ASSUMED]

### Pitfall 4: Morphology Erases Small Faces or Merges Nearby Objects

**What goes wrong:** Opening removes a small/distant face, or closing merges the face with nearby table/pallet edges. [ASSUMED]

**Why it happens:** Erosion shrinks foreground regions, dilation grows them, opening is erosion followed by dilation, and closing is dilation followed by erosion. [CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html]

**How to avoid:** Keep kernel and iteration counts small by default, validate on minimum expected face size, and expose config for tuning. [ASSUMED]

**Warning signs:** Candidate count changes dramatically when kernel size moves from 3x3 to 5x5. [ASSUMED]

### Pitfall 5: `approxPolyDP` Epsilon Is Too Aggressive or Too Strict

**What goes wrong:** The real square is approximated as a triangle, pentagon, or detailed noisy polygon. [ASSUMED]

**Why it happens:** OpenCV defines epsilon as the maximum distance between the original curve and approximation, and the contour tutorial warns that wise epsilon selection is needed. [CITED: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]

**How to avoid:** Configure epsilon as a ratio of `arcLength(contour, True)` and start around `0.02-0.04`; test synthetic rounded/noisy squares. [CITED: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html; ASSUMED]

**Warning signs:** One parameter value finds candidates only for perfect synthetic images but fails on captured images. [ASSUMED]

### Pitfall 6: Area Bounds Are Hardcoded for One Camera Distance

**What goes wrong:** Close blocks are rejected as too large, distant blocks are rejected as too small, or noise is accepted as a candidate. [ASSUMED]

**Why it happens:** GEO-02 requires area min/max bounds, but the repo has no real reference image set yet. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: repo image fixture scan]

**How to avoid:** Make min/max area config values, record observed `contourArea` values from reference images, and test both lower and upper bounds. [CITED: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html; ASSUMED]

**Warning signs:** All reference frames fail the same area rejection reason. [ASSUMED]

### Pitfall 7: Axis-Aligned Aspect Rejects Rotated Squares

**What goes wrong:** A square at 45 degrees has a large axis-aligned bounding box and fails a tight width/height ratio. [ASSUMED]

**Why it happens:** `boundingRect` returns an up-right rectangle, while the block can rotate in the image. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; VERIFIED: project requires varied rotation in TEST-01]

**How to avoid:** Use `minAreaRect` side ratio or approximated side lengths for square-likeness, and keep axis-aligned bbox only for debug/contract compatibility later. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; ASSUMED]

**Warning signs:** Synthetic unrotated squares pass but synthetic 30-45 degree squares fail. [ASSUMED]

### Pitfall 8: Self-Intersecting or Duplicate Contour Points Break Convexity Assumptions

**What goes wrong:** Convexity checks return unreliable results for malformed contours. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]

**Why it happens:** OpenCV documents `isContourConvex` output as undefined when the contour is not simple and has self-intersections. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]

**How to avoid:** Run convexity after `approxPolyDP`, require exactly four distinct vertices, and reject zero-length sides before Phase 4. [ASSUMED]

**Warning signs:** Side-length calculations have zeros or repeated points. [ASSUMED]

## Code Examples

Verified patterns from official sources and existing project constraints:

### End-to-End Phase 3 Function Shape

```python
# Source basis: Phase 2 normalized BGR frame contract plus OpenCV preprocessing/contour APIs. [VERIFIED: user prompt; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
def detect_square_face_candidates(frame_bgr, preprocess_config, filter_config):
    preprocess = preprocess_frame_bgr(frame_bgr, preprocess_config)
    candidates = find_square_candidates(preprocess["mask"], filter_config)
    return candidates, preprocess
```

### Config Validation

```python
# Source basis: OpenCV requires odd positive Gaussian kernels and adaptive threshold block sizes such as 3, 5, 7. [CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]
def _require_odd_size(value: int, name: str, minimum: int = 3) -> None:
    if value < minimum or value % 2 == 0:
        raise ValueError(f"{name} must be odd and >= {minimum}; got {value}")
```

### Synthetic Fixture for Reference-Like Square

```python
# Source basis: tests can build OpenCV-compatible BGR uint8 frames before real captured fixtures exist. [ASSUMED]
import cv2 as cv
import numpy as np


def synthetic_square_frame(size=(480, 640), points=None):
    image = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    if points is None:
        points = np.array([[260, 160], [380, 170], [370, 290], [250, 280]], dtype=np.int32)
    cv.fillConvexPoly(image, points, (220, 220, 220))
    return image
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Treat "square detection" as only `threshold -> findContours -> len(approx)==4`. [ASSUMED] | Preserve preprocess intermediates, use configurable threshold/Canny modes, morphology, convexity, area, rotation-tolerant aspect, and debug overlays. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html; ASSUMED] | Current project phase design already separates contour candidates from geometry/classification. [VERIFIED: .planning/ROADMAP.md] | The planner should create modules that expose both accepted candidates and rejection/debug data. [ASSUMED] |
| Use fiducials such as ArUco/AprilTag for reliable square pose. [ASSUMED] | Do not use fiducials on blocks; use natural square-face contours, then warp and classify later. [VERIFIED: .planning/PROJECT.md; VERIFIED: .planning/REQUIREMENTS.md] | Locked by project constraints before Phase 3. [VERIFIED: .planning/PROJECT.md] | Phase 3 needs honest candidate uncertainty and must not pretend contour geometry is final pose. [ASSUMED] |
| Use a heavy detector on full 640x480 frames for all tasks. [ASSUMED] | Use cheap contour candidates first, then classify canonical face warps with a small INT8 model in later phases. [VERIFIED: .planning/research/STACK.md; VERIFIED: .planning/ROADMAP.md] | Project stack research dated 2026-05-31 selected contour + warp + tiny CNN. [VERIFIED: .planning/research/STACK.md] | Phase 3 should stay fast and geometry-focused. [ASSUMED] |
| Rely on template matching as the primary v1 recognition method. [VERIFIED: .planning/PROJECT.md says this is out of scope as primary] | Use contour candidates and later TFLite INT8 CNN classification as v1 default. [VERIFIED: .planning/PROJECT.md; VERIFIED: .planning/research/STACK.md] | Locked in project docs before Phase 3. [VERIFIED: .planning/PROJECT.md] | Phase 3 should not add template-matching scoring. [VERIFIED: .planning/ROADMAP.md] |

**Deprecated/outdated:**

- Relying on `cv.findContours` return signatures from OpenCV 2.x/3.x tutorials is outdated for this project; OpenCV 4 Python uses `contours, hierarchy = cv.findContours(...)`. [CITED: https://docs.opencv.org/4.x/df/d0d/tutorial_find_contours.html]
- Using only `boundingRect` aspect as a square test is fragile for rotated blocks. [ASSUMED; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html]
- Adding ArUco/AprilTag markers to solve pose is out of scope for this project. [VERIFIED: .planning/PROJECT.md; VERIFIED: .planning/REQUIREMENTS.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `adaptive_threshold` should be the default mask mode, with Canny kept as configurable alternative. | Standard Stack | If reference images have weak fill contrast but strong edges, Canny may need to be default. |
| A2 | Initial area/aspect/epsilon constants can start from synthetic tests and be tuned once real fixtures exist. | Summary, Common Pitfalls | Planner may need an earlier task to collect/reference real images before success criterion 3 can be fully automated. |
| A3 | `minAreaRect` aspect is a better primary filter than axis-aligned `boundingRect` aspect for rotated squares. | Architecture Patterns, Pitfalls | If perspective skew dominates, side-length and angle heuristics may need Phase 4 earlier than expected. |
| A4 | Debug overlay output should be produced by a separate helper and not embedded in candidate extraction logic. | Architecture Patterns | If the project wants minimum files, planner may merge helper into `contours.py` while preserving separation of concerns. |

## Open Questions

1. **Where will Phase 3 reference images live?**
   - What we know: No image fixtures were found in the repo. [VERIFIED: local image fixture scan]
   - What's unclear: Whether Phase 2 will create `debug_frames/` examples before Phase 3 execution. [VERIFIED: Phase 2 plans are not fully verified per user prompt]
   - Recommendation: Wave 0 should use synthetic image tests and create `tests/fixtures/reference/README.md`; real captured reference images should be added as soon as Phase 2 artifacts exist. [ASSUMED]

2. **What physical block face size range should area thresholds represent?**
   - What we know: Camera resolution is 640x480 and success criteria require configured min/max area. [VERIFIED: CLAUDE.md; VERIFIED: .planning/ROADMAP.md]
   - What's unclear: Expected pixel area at nearest and farthest working distances. [ASSUMED]
   - Recommendation: Start with broad defaults and require a debug report that logs observed areas from reference images. [ASSUMED]

3. **Should threshold polarity default to `THRESH_BINARY` or `THRESH_BINARY_INV`?**
   - What we know: OpenCV supports both polarity modes. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html]
   - What's unclear: Whether block faces are lighter or darker than the pallet/table under locked lighting. [ASSUMED]
   - Recommendation: Expose polarity config and test both with synthetic fixtures. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All Phase 3 code/tests | yes | 3.14.4 local; target Pi 3.11.x from stack docs [VERIFIED: local probe; VERIFIED: .planning/research/STACK.md] | None needed |
| OpenCV Python `cv2` | GEO-01, GEO-02 implementation | no locally | Missing import [VERIFIED: local import probe] | Add dependency in Wave 0 and skip OpenCV tests until installed |
| NumPy | OpenCV arrays and tests | no locally | Missing import [VERIFIED: local import probe] | Add dependency in Wave 0 |
| pytest | Nyquist validation tests | no locally | Missing import [VERIFIED: local import probe] | Existing unittest can run Phase 1 tests, but Phase 3 should install pytest for image assertions [VERIFIED: tests use unittest; ASSUMED] |
| Reference images | Success criterion 3 | no | No image files found [VERIFIED: local image fixture scan] | Synthetic fixtures for Wave 0; real fixture task before final Phase 3 gate |

**Missing dependencies with no fallback:**

- OpenCV Python and NumPy block automated Phase 3 implementation tests until installed. [VERIFIED: local import probe]

**Missing dependencies with fallback:**

- pytest is missing locally; the repo has unittest tests, but Phase 3 validation should add pytest as planned by Phase 2 validation. [VERIFIED: tests directory; VERIFIED: .planning/phases/02-camera-capture/02-VALIDATION.md]
- Real reference images are missing; synthetic square fixtures can validate algorithm mechanics, but success criterion 3 needs real captured images before phase completion. [VERIFIED: repo image fixture scan; VERIFIED: .planning/ROADMAP.md]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 recommended; missing locally [VERIFIED: `python3 -m pip index versions pytest`; VERIFIED: local import probe] |
| Config file | none yet; Wave 0 should update `pyproject.toml` or add dependency config [VERIFIED: pyproject.toml] |
| Quick run command | `python -m pytest tests/test_preprocess.py tests/test_contours.py -q` [ASSUMED] |
| Full suite command | `python -m pytest -q` [VERIFIED: Phase 2 validation pattern; ASSUMED] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| GEO-01 | BGR frame becomes grayscale, blurred image, binary/edge mask, and morphology outputs with expected shape/dtype. [VERIFIED: .planning/REQUIREMENTS.md] | unit | `python -m pytest tests/test_preprocess.py::test_preprocess_outputs_named_480x640_uint8_images -q` | no, Wave 0 |
| GEO-01 | Adaptive threshold validates odd block size and configurable polarity. [CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html] | unit | `python -m pytest tests/test_preprocess.py::test_adaptive_threshold_config_validation -q` | no, Wave 0 |
| GEO-01 | Canny mode produces an 8-bit mask and closing can bridge small edge gaps in synthetic square fixtures. [CITED: https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html; CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html] | unit | `python -m pytest tests/test_preprocess.py::test_canny_mode_outputs_candidate_mask -q` | no, Wave 0 |
| GEO-02 | Synthetic visible square returns at least one 4-vertex convex candidate within area/aspect bounds. [VERIFIED: .planning/ROADMAP.md] | unit | `python -m pytest tests/test_contours.py::test_synthetic_square_yields_candidate -q` | no, Wave 0 |
| GEO-02 | Non-square rectangle, tiny noise, concave polygon, and oversized contour are rejected with reasons. [VERIFIED: .planning/REQUIREMENTS.md; CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html] | unit | `python -m pytest tests/test_contours.py::test_geometry_filters_reject_bad_contours -q` | no, Wave 0 |
| GEO-02 | Real reference frame with visible block face yields at least one candidate. [VERIFIED: .planning/ROADMAP.md] | regression | `python -m pytest tests/test_contours_reference.py -q` | no, blocked until fixture exists |
| GEO-02 | Debug overlay draws accepted candidate contours without changing source frame. [CITED: https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html] | unit | `python -m pytest tests/test_debug_overlay.py -q` | no, Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_preprocess.py tests/test_contours.py -q` [ASSUMED]
- **Per wave merge:** `python -m pytest -q` [ASSUMED]
- **Phase gate:** Full suite green, plus at least one real reference image test or an explicit blocker if Phase 2 has not produced any reference image. [VERIFIED: Phase 3 success criterion 3; ASSUMED]

### Wave 0 Gaps

- [ ] `pyproject.toml` dependencies or dev extras for `opencv-python`, `numpy`, and `pytest`. [VERIFIED: local imports missing; VERIFIED: pyproject.toml currently has no dependencies]
- [ ] `src/block_detected/preprocess.py` with config validation and named intermediates. [ASSUMED]
- [ ] `src/block_detected/contours.py` with `ContourCandidate` and filtering. [ASSUMED]
- [ ] `src/block_detected/debug_overlay.py` or equivalent overlay helper. [ASSUMED]
- [ ] `tests/test_preprocess.py`, `tests/test_contours.py`, and `tests/test_debug_overlay.py`. [ASSUMED]
- [ ] `tests/fixtures/reference/README.md` documenting required captured frames until real images exist. [VERIFIED: no image fixtures found; ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No authentication surface in Phase 3 image-processing modules. [VERIFIED: .planning/ROADMAP.md] |
| V3 Session Management | no | No sessions in Phase 3. [VERIFIED: .planning/ROADMAP.md] |
| V4 Access Control | no | No user authorization boundary in Phase 3. [VERIFIED: .planning/ROADMAP.md] |
| V5 Input Validation | yes | Validate frame shape `(480, 640, 3)`, dtype `uint8`, config bounds, odd kernels, and candidate numeric fields. [VERIFIED: user prompt; CITED: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html; CITED: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html] |
| V6 Cryptography | no | No crypto in Phase 3. [VERIFIED: .planning/ROADMAP.md] |

### Known Threat Patterns for OpenCV Frame Processing

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed frame object or wrong shape reaches OpenCV and crashes processing. [ASSUMED] | Denial of Service | Reject non-NumPy frames, wrong dtype, wrong channel count, and wrong resolution before `cv.cvtColor`. [VERIFIED: user prompt; ASSUMED] |
| Unbounded debug artifact writes fill disk. [VERIFIED: Phase 2 validation identified debug retention risk] | Denial of Service | Reuse Phase 2 `DebugFrameWriter` retention/sampling controls for overlays. [VERIFIED: .planning/phases/02-camera-capture/02-VALIDATION.md; ASSUMED] |
| Path traversal through debug output names. [ASSUMED] | Tampering | Use Phase 2 frame IDs and fixed output directory; do not accept arbitrary filenames from image content. [VERIFIED: .planning/phases/02-camera-capture/02-VALIDATION.md; ASSUMED] |

## Sources

### Primary (HIGH confidence)

- https://docs.opencv.org/4.x/d8/d01/group__imgproc__color__conversions.html - `cv.cvtColor`, BGR channel convention, color conversion API. [CITED]
- https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html - `cv.GaussianBlur`, `cv.morphologyEx`, `cv.getStructuringElement`, kernel constraints. [CITED]
- https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html - `cv.adaptiveThreshold`, threshold types, adaptive block-size requirements. [CITED]
- https://docs.opencv.org/4.x/da/d5c/tutorial_canny_detector.html - Canny theory, threshold ratio guidance, OpenCV `cv.Canny`. [CITED]
- https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html - opening, closing, erosion, dilation, structuring elements. [CITED]
- https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html - `findContours`, retrieval modes, `CHAIN_APPROX_SIMPLE`, `approxPolyDP`, `arcLength`, `boundingRect`, `minAreaRect`, `isContourConvex`. [CITED]
- https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html - contour area, perimeter, polygon approximation and epsilon guidance. [CITED]
- https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html - `drawContours` and drawing APIs for overlays. [CITED]

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` - project stack decisions for Python, OpenCV, NumPy, pytest, Pi compatibility. [VERIFIED]
- `.planning/phases/02-camera-capture/02-RESEARCH.md` - Phase 2 frame shape/color contract and camera abstraction direction. [VERIFIED]
- `.planning/phases/02-camera-capture/02-VALIDATION.md` - pytest validation pattern and debug artifact retention concerns. [VERIFIED]
- Local PyPI index queries for `opencv-python`, `numpy`, and `pytest` current versions. [VERIFIED]

### Tertiary (LOW confidence)

- Initial numeric defaults for area bounds, aspect ratio tolerance, Canny thresholds, adaptive C, and approximation epsilon are placeholders until measured against real captured fixtures. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - OpenCV APIs and package versions were verified against official docs and PyPI index. [CITED: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html; VERIFIED: local PyPI index queries]
- Architecture: MEDIUM - Module boundaries match the existing package and roadmap, but Phase 2 implementation is not fully verified yet. [VERIFIED: existing `src/block_detected` layout; VERIFIED: user prompt]
- Pitfalls: MEDIUM - OpenCV mechanics are verified, while several field failure modes depend on lighting, block material, and camera distance not represented by fixtures yet. [CITED: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html; VERIFIED: repo image fixture scan]
- Validation: MEDIUM - Nyquist is enabled and commands are clear, but OpenCV/NumPy/pytest are not installed locally and real reference images are missing. [VERIFIED: .planning/config.json; VERIFIED: local import probe; VERIFIED: repo image fixture scan]

**Research date:** 2026-05-31 [VERIFIED: local environment context]
**Valid until:** 2026-06-30 for OpenCV API usage; revisit within 7 days of adding target-Pi dependency pins or real camera fixtures. [ASSUMED]
