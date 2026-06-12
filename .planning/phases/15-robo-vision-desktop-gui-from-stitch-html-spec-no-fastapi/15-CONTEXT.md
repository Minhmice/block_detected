# Phase 15 — Robo-Vision desktop GUI (no FastAPI)

## Goal

Replace browser/FastAPI path with **native PySide6** shell matching `example_ui/stitch_block_pickup_vision_console/code.html` and screenshot (ROBO-VISION OS v2.4).

## Decisions

- **Remove** `apps/web/`, `runtime/api/`, `block-detected-web`, `[web]` extra — user does not want HTTP stack in project.
- **Keep** `example_ui/` as design reference only (HTML + DESIGN.md + BACKEND_GAP_ANALYSIS.md).
- **Wire now:** Start/Stop, NEXT CAMERA/MODEL, confidence, stability, camera/model TOML, FPS/latency/render, system log, primary detect summary.
- **Placeholder (disabled):** Contours/Corners/Warped Face, PRE-PROCESSING sliders, NMS IoU (YOLO), KINEMATICS panel — per gap analysis / future phases.

## Reference files

- `example_ui/stitch_block_pickup_vision_console/code.html`
- `example_ui/stitch_block_pickup_vision_console/DESIGN.md`
- `src/block_detected/apps/gui/robo_window.py`
- `src/block_detected/apps/gui/theme.py`
