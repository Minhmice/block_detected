# Phase 3: Preprocess & Contour Detection - Research

**Researched:** 2026-05-31
**Domain:** OpenCV binary/edge preprocessing and square-quad contour filtering on 640×480 BGR frames
**Confidence:** HIGH

<user_constraints>
## User Constraints

No phase `CONTEXT.md` exists. Locked decisions come from PROJECT.md, ROADMAP.md, and project-level research.

### Locked Decisions

- Pipeline order: **Contour → Warp → CNN → Pose** (this phase covers preprocess + contour only).
- Input: `CaptureFrame.image_bgr` at **640×480** from Phase 2 `FrameSource`.
- No ArUco; square face from **classical contours**, not YOLO bbox.
- Phase 3 requirements: **GEO-01** (preprocess chain), **GEO-02** (square candidates).
- Corner ordering, warp, classification, pose → **Phase 4+** (out of scope here).

### Claude's Discretion

- Adaptive threshold vs Canny default (recommend dual-mode config).
- `SquareCandidate` internal type vs reusing contract corners (use internal type until Phase 4).
- Debug artifact names under `debug_frames/{run_id}/preprocess/` and `.../contours/`.

### Deferred Ideas (OUT OF SCOPE)

- GEO-03 corner order, GEO-04 warp, GEO-05 center/angle (Phase 4).
- REJ-* reject policy integration (Phase 7).
- CNN / TFLite (Phase 5).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEO-01 | BGR→gray, blur, adaptive threshold or Canny, morphology open/close | `preprocess.py` with `PreprocessSettings` dataclass; expose `preprocess_bgr(image_bgr) -> PreprocessResult` returning gray, binary/edge map, and debug dict |
| GEO-02 | `findContours` + `approxPolyDP`; filter 4-vertex convex quads; area min/max; aspect ~1:1 | `detector.py` with `find_square_candidates(binary_or_edges, settings) -> list[SquareCandidate]`; rank by area + squareness score |
</phase_requirements>

## Summary

Phase 3 adds the **vision front-end** that turns a normalized BGR frame into zero or more **square-face quad candidates** ready for Phase 4 geometry. Split into two modules: `preprocess.py` (GEO-01) and `detector.py` (GEO-02). Do not wire full `DetectionResult` yet — return structured candidates with raw contour points in image space.

**Primary recommendation:** Implement configurable preprocess (default: Gaussian blur → adaptive threshold → close/open morphology), then `RETR_EXTERNAL` + `CHAIN_APPROX_SIMPLE` contours, `approxPolyDP` to 4 points, filter by area fraction of frame, aspect ratio, convexity, and minimum corner angle. Persist intermediate debug images via existing `DebugFrameWriter` pattern.

## Project Constraints (from prior phases)

- OpenCV + NumPy already in dev dependencies (`pyproject.toml` `[dev]`).
- `CaptureFrame` from `block_detected.camera` is the only upstream input.
- `detect_block` in `pipeline.py` remains a stub until later phases; Phase 3 may add optional `detect_square_candidates(frame)` helper or internal pipeline hook without breaking contract tests.
- Locked camera exposure (Phase 2) reduces but does not eliminate threshold tuning needs.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| OpenCV (`cv2`) | 4.11–4.13 (pinned in dev extra) | `cvtColor`, `GaussianBlur`, `adaptiveThreshold`, `Canny`, `morphologyEx`, `findContours`, `approxPolyDP`, `contourArea`, `isContourConvex` | De facto API for document/scanner-style square detection |
| NumPy | 2.x | Array ops on 640×480 frames | Required by OpenCV Python bindings |
| Python dataclasses | stdlib | `PreprocessSettings`, `DetectorSettings`, `SquareCandidate` | Matches project contract style |

### Supporting

| Tool | Purpose | When |
|------|---------|------|
| pytest | Unit tests on synthetic binary images | Always — synthetic white square on black, rotated rectangles, noise |
| `DebugFrameWriter` | Save `*_preprocess.png`, `*_contours.png` overlays | Field tuning; use `frame_id` from `CaptureFrame` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Adaptive threshold | Canny only | Canny better for sharp edges; adaptive better for uneven lighting — **use config flag** |
| `RETR_EXTERNAL` | `RETR_TREE` | External avoids nested table edges dominating; tree needed only if holes matter |
| Custom Hough lines | Contour quads | Hough does not give ordered corners; stick to contours per project architecture |

## Architecture Patterns

### Module Split

```text
src/block_detected/
  preprocess.py   # GEO-01: BGR → PreprocessResult (gray, mask, metadata)
  detector.py     # GEO-02: mask → list[SquareCandidate]
  pipeline.py     # (Phase 7) orchestration; Phase 3 may add dev-only entry
```

### Pattern 1: Preprocess Pipeline Function

**What:** Pure function `preprocess_bgr(image_bgr, settings) -> PreprocessResult` with no I/O.

**When:** Every frame before contours; enables pytest without camera.

**Parameters (recommended defaults for 640×480):**

| Parameter | Default | Notes |
|-----------|---------|-------|
| `blur_ksize` | 5 | Odd integer; 0 = skip blur |
| `threshold_mode` | `"adaptive"` | `"adaptive"` \| `"canny"` |
| `adaptive_block_size` | 11 | Odd, ≥3 |
| `adaptive_c` | 2 | Subtracted constant |
| `canny_low` / `canny_high` | 50 / 150 | Used when mode=canny |
| `morph_open_ksize` | 3 | Removes speckle |
| `morph_close_ksize` | 5 | Closes gaps in square edges |

### Pattern 2: Square Candidate Detection

**What:** `find_square_candidates(mask, settings) -> list[SquareCandidate]`.

**SquareCandidate fields (internal, not contract):**

```python
@dataclass(frozen=True)
class SquareCandidate:
    contour: np.ndarray          # 4x1x2 or Nx2 polygon
    vertices: tuple[PointPx, ...]  # 4 points, UNORDERED until Phase 4
    area_px: float
    aspect_ratio: float          # max(side)/min(side) from bounding rect
    squareness: float            # area / (bbox width * height), 0-1
    centroid: tuple[float, float]
```

**Filters (GEO-02):**

1. `len(approx) == 4` after `approxPolyDP(epsilon = 0.02 * arcLength)` (tune via config).
2. `cv2.isContourConvex(approx)`.
3. `area_min_px` ≤ `contourArea` ≤ `area_max_px` (defaults: 2%–40% of 640×480).
4. Aspect ratio from `minAreaRect`: ratio of side lengths ≤ `max_aspect` (default 1.25).
5. Optional: reject if corner angles deviate >15° from 90° (Phase 3.5 or Phase 7).

**Ranking:** Sort by `squareness * area_px` descending; Phase 7 picks best one.

### Pattern 3: Debug Overlays

**What:** After detection, draw all quads on copy of BGR; save via debug writer.

```python
overlay = image_bgr.copy()
cv2.drawContours(overlay, [c.contour for c in candidates], -1, (0, 255, 0), 2)
```

### Anti-Patterns

- **Preprocess inside detector** — keeps GEO-01/GEO-02 testable separately.
- **Returning DetectionResult from Phase 3** — premature; no block_id yet.
- **Hard-coded thresholds only** — must be JSON/YAML config for field tuning.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Grayscale conversion | Manual weights | `cv2.cvtColor(..., COLOR_BGR2GRAY)` | Correct BGR order |
| Contour finding | Scan pixels | `cv2.findContours` | Optimized C++ |
| Polygon simplification | Custom RDP | `cv2.approxPolyDP` | Standard epsilon model |
| Convex test | Custom cross products | `cv2.isContourConvex` | Edge cases handled |
| Area | Shoelace by hand | `cv2.contourArea` | Consistent with OpenCV |

## Common Pitfalls

### Pitfall 1: Glare fragments binary mask (GEO-01)

**Signs:** Many tiny contours; missing large square.

**Prevention:** Phase 2 locked exposure; increase `adaptive_block_size` or switch to Canny; save preprocess debug image every N frames.

### Pitfall 2: `approxPolyDP` epsilon too loose/tight (GEO-02)

**Signs:** 5–8 vertex polys or collapsed lines.

**Prevention:** Default `epsilon = 0.02 * arcLength`; expose in config; unit test synthetic square at 0°, 45°.

### Pitfall 3: Table/pallet edges as quads (GEO-02)

**Signs:** Huge candidates; wrong pick in Phase 7.

**Prevention:** `area_max_px` cap; aspect ratio filter; Phase 7 overlap reject — document that Phase 3 may return multiple candidates.

### Pitfall 4: BGR/RGB confusion on preprocess (GEO-01)

**Signs:** Threshold inverted vs expectation.

**Prevention:** Always document input as BGR from `CaptureFrame`; never convert RGB twice.

### Pitfall 5: Contour hierarchy noise (GEO-02)

**Signs:** Inner holes detected as squares.

**Prevention:** `RETR_EXTERNAL` + area filter; ignore contours with area < `area_min_px`.

## Code Examples

### Preprocess (adaptive path)

```python
import cv2 as cv

def preprocess_bgr(image_bgr, settings):
    gray = cv.cvtColor(image_bgr, cv.COLOR_BGR2GRAY)
    if settings.blur_ksize > 1:
        gray = cv.GaussianBlur(gray, (settings.blur_ksize, settings.blur_ksize), 0)
    if settings.threshold_mode == "adaptive":
        mask = cv.adaptiveThreshold(
            gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY,
            settings.adaptive_block_size, settings.adaptive_c,
        )
    else:
        edges = cv.Canny(gray, settings.canny_low, settings.canny_high)
        mask = edges
    k_open = cv.getStructuringElement(cv.MORPH_RECT, (settings.morph_open_ksize,) * 2)
    k_close = cv.getStructuringElement(cv.MORPH_RECT, (settings.morph_close_ksize,) * 2)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, k_open)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, k_close)
    return gray, mask
```

### Contour quad filter

```python
def find_square_candidates(mask, settings):
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    candidates = []
    for cnt in contours:
        peri = cv.arcLength(cnt, True)
        approx = cv.approxPolyDP(cnt, settings.epsilon_ratio * peri, True)
        if len(approx) != 4 or not cv.isContourConvex(approx):
            continue
        area = cv.contourArea(approx)
        if area < settings.area_min_px or area > settings.area_max_px:
            continue
        rect = cv.minAreaRect(approx)
        w, h = rect[1]
        if w == 0 or h == 0:
            continue
        aspect = max(w, h) / min(w, h)
        if aspect > settings.max_aspect_ratio:
            continue
        candidates.append((approx, area, aspect))
    return sorted(candidates, key=lambda x: x[1], reverse=True)
```

## State of the Art

| Approach | Use here? | Notes |
|----------|-----------|-------|
| OpenCV contour + approxPolyDP | **Yes** | Project architecture locked |
| YOLO-OBB | No | No ordered corners for grasp |
| ArUco subpixel | No | Explicit exclusion |
| Deep edge detector | No | Overkill for Phase 3 |

## Open Questions (RESOLVED)

1. **Default threshold mode?** — **RESOLVED:** `adaptive` default; `canny` in config for high-glare labs. Validate on physical test set in Phase 8.

2. **Return multiple candidates?** — **RESOLVED:** Yes — return `list[SquareCandidate]`; Phase 7 selects/rejects. Matches `multiple_candidates` status design.

3. **Wire into `detect_block` now?** — **RESOLVED:** Optional internal function only; keep public `detect_block` stub until Phase 7 integration. Add `preprocess_and_detect_candidates(capture_frame)` for tests.

## Environment Availability

| Dependency | Available | Notes |
|------------|-----------|-------|
| opencv-python | Yes (dev extra) | Already used in Phase 2 tests |
| numpy | Yes | Same |
| pytest | Yes | Same venv |

## Validation Architecture

| Test | Type | Command |
|------|------|---------|
| Synthetic square | unit | `pytest tests/test_preprocess.py tests/test_detector.py -q` |
| Empty mask | unit | Expect `[]` candidates |
| Rotated square 45° | unit | Exactly one candidate within area bounds |
| Real fixture PNG | integration | Use `tests/fixtures/frames/frame.png` — may need painted square |

Suggested `config/vision.example.json` alongside camera config for preprocess/detector thresholds.

## Sources

- OpenCV contours tutorial: https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html
- `approxPolyDP`: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html
- Project `.planning/research/ARCHITECTURE.md`, `PITFALLS.md`
- Phase 2 `CaptureFrame` contract in `src/block_detected/camera.py`

---
*Phase 3 research for: preprocess-contour-detection*
*Researched: 2026-05-31*
