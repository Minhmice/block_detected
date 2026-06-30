# Phase 15: block_detection_v2 classical CV module — Context

**Gathered:** 2026-06-29
**Status:** Ready for planning
**Source:** Milestone v2.0 spec + implemented scaffold

<domain>
## Phase Boundary

Deliver isolated `src/block_detection_v2/` — OpenCV + NumPy only, no v1 imports, no YOLO. Full pipeline: preprocess → edges → 6-point hexagon → geometry (faces, yaw, homography splits) → EMA tracker → overlay + per-frame dict. Runnable via `python -m block_detection_v2.main`.
</domain>

<decisions>
## Implementation Decisions

### Isolation (D-01)
- Package lives only under `src/block_detection_v2/`
- Zero imports from `block_detected`, `view`, `stream`, or repo root modules

### Stack (D-02)
- OpenCV + NumPy only in v2
- YOLO deferred — `TODO` comment in `main.py` for future ROI only

### Module layout (D-03)
- One responsibility per file: `config`, `camera`, `preprocessing`, `edges`, `polygon`, `geometry`, `tracker`, `renderer`, `models`, `main`
- No DI, factories, or heavy abstractions

### Hexagon labeling (D-04)
- A top_left, B top_mid, C top_right, D bottom_right, E bottom_mid, F bottom_left
- front = A-B-E-F, right = B-C-D-E

### Output (D-05)
- Per-frame dict: `detected`, `points`, `center`, `front_width`, `right_width`, `yaw_deg`

### Claude's Discretion
- Exact Canny/Hough defaults in `config.py`
- Polygon epsilon sweep ratios
</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — ISO-*, PIP-*, POL-* for phase 15
- `.planning/ROADMAP.md` — Phase 15 success criteria
- `src/block_detection_v2/` — implementation target (brownfield scaffold exists)
</canonical_refs>

---

*Phase: 15-block-detection-v2-classical-cv-module*
