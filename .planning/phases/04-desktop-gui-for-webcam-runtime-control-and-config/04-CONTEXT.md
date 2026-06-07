# Phase 4: Desktop GUI for webcam runtime control and config - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
## Phase Boundary

PySide6 GUI (`apps/gui/app.py`) as primary entry (`python main.py`). GUI delegates to `WebcamEngine` — no duplicate YOLO/camera logic. Controls: start/stop, conf, camera/model switch, config hot-reload, log panel via `get_log_lines()`, frame preview with aspect ratio.

</domain>

<decisions>
## Implementation Decisions

### GUI Architecture
- Lazy PySide6 imports in app.py for test import safety
- QThread worker for frame loop; run generation guards for stale signals
- Worker calls `engine.shutdown(destroy_cv_windows=False)` — never cv2.destroyAllWindows from GUI

### Controls
- Camera group: index, max, width, height spinboxes
- Confidence slider/spin with hot apply
- Model/camera cycle buttons; eval mode toggle

### Claude's Discretion
Retroactive closure — verify existing GUI meets criteria, add tests where feasible, document worker shutdown pattern.

</decisions>

<code_context>
## Existing Code Insights

- `src/block_detected/apps/gui/app.py` — main GUI
- `runtime/engine.py`, `runtime/logging_setup.py` — engine + log buffer
- `main.py` — entry point

</code_context>

<specifics>
Verify GUI hardening patterns from AGENTS.md (worker shutdown, log buffer API).

</specifics>

<deferred>
Stitch web console — Phase 7+

</deferred>
