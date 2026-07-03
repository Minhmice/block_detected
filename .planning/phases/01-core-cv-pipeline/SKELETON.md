# Walking Skeleton — Hex Detector

**Phase:** 1
**Generated:** 2026-06-30

## Capability Proven End-to-End

> A caller can pass a NumPy frame and tracked YOLO bbox to `HexDetector.detect_frame()` and receive a typed rectangle, hex, held, or rejected result that can be rendered as an OpenCV debug overlay.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Python package with OpenCV + NumPy | CPU-only classical CV matches Raspberry Pi 5 constraints |
| Data layer | In-memory `_TrackState` keyed by `track_id` | Temporal state is frame-local runtime data; persistent DB storage is outside this library's scope |
| Auth | Not applicable | The module is a local CV library with no network or user boundary |
| Deployment target | Importable `src/` package exercised by pytest/local Python on Pi-compatible CPU | Proves the complete call path without inventing a web service |
| Directory layout | Focused modules under `src/hex_detector/` | Existing separation of config, models, preprocessing, lines, geometry, tracking, orchestration, and rendering is clear and reusable |

## Stack Touched in Phase 1

- [x] Package API — typed public `detect_frame()` entry point
- [x] Routing equivalent — one real call path delegates to internal `detect_roi()`
- [x] State read/write — real per-track in-memory EMA and last-good hold state
- [x] UI equivalent — real `render_debug()` OpenCV overlay consuming typed results
- [x] Local execution — focused pytest commands exercise the full frame → result → overlay path

> Database, authentication, browser UI, and remote deployment are intentionally marked not applicable: adding them would violate the fixed phase boundary.

## Out of Scope (Deferred to Later Slices)

- Cross-frame tracking policy beyond the guarded three-frame hold window.
- Dataset-level calibration and Raspberry Pi performance benchmarking.
- Integration into the legacy `block_detected` runtime or YOLO tracker.
- Network APIs, persistence, or GUI controls.

## Subsequent Slice Plan

- Phase 2: Temporal tracking refinement across frames.
- Phase 3: Demo and verification against representative frames.
