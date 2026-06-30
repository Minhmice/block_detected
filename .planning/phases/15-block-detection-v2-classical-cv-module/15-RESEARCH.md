# Phase 15 Research — block_detection_v2 classical CV module

**Researched:** 2026-06-29

## Stack

- OpenCV 4.8+: `VideoCapture`, Canny, `findContours`, `approxPolyDP`, `getPerspectiveTransform`, `polylines`
- NumPy for point math only
- No Ultralytics / torch in this phase

## Pipeline pattern

1. Grayscale + CLAHE + Gaussian blur stabilizes lighting
2. Canny + morph close → external contours
3. `approxPolyDP` with multiple epsilon ratios to hit 6 vertices
4. Order top/bottom row by y-midline; validate convexity, face areas, no self-intersection
5. Homography per face → horizontal split lines back-projected to source
6. Per-point EMA with jump reject + 4-frame hold on loss

## Integration

- **None with v1** — run with `PYTHONPATH=src python -m block_detection_v2.main`
- `pyproject.toml` unchanged; package not wired into `block-detected` entry points

## Pitfalls

- `approxPolyDP` often returns 4 verts — need epsilon ratio sweep
- B (top_mid) can have smaller y than A/C — do not require monotonic y within top row
- Arrow keys need `waitKeyEx` on macOS

## Validation Architecture

- Synthetic hexagon image: assert `detected=True`
- `py_compile` all modules
- Grep: no `block_detected` imports inside `block_detection_v2/`
