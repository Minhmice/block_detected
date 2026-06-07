# Phase 3: Runtime engine, typed config, and detector abstraction for GUI prep - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous — discuss skipped)

<domain>
## Phase Boundary

Deliver `WebcamEngine` runtime loop (read → infer → render → metrics), typed `AppConfig` dataclasses with TOML load/save, `DetectorBackend` protocol + YOLO loader, and hot-reload vs restart key classification. No GUI code in this phase — GUI consumes engine only.

</domain>

<decisions>
## Implementation Decisions

### Architecture
- `runtime/` owns engine, config schema/store, metrics, state, detector loader
- `core/` holds domain types and `DetectorBackend` protocol — no OpenCV/YOLO imports
- `detection/` implements YOLO backend; engine depends on protocol, not Ultralytics directly in UI layer

### Config
- Defaults in `AppConfig.defaults()`; optional `block_detected.toml` at repo root
- `RESTART_CAMERA_KEYS` / `RESTART_DETECTOR_KEYS` classify hot vs restart keys

### Claude's Discretion
Retroactive closure: code largely exists — plans should verify, fill gaps, add tests, update ROADMAP goals/success criteria.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/block_detected/runtime/engine.py` — WebcamEngine
- `src/block_detected/runtime/config_schema.py` — AppConfig dataclasses
- `src/block_detected/runtime/config_store.py` — TOML load/save
- `src/block_detected/runtime/detector_loader.py`, `runtime/metrics.py`, `runtime/state.py`
- `src/block_detected/core/protocols.py`, `core/domain.py`
- `src/block_detected/detection/yolo/backend.py`

### Established Patterns
- Layered dependency rules in AGENTS.md
- pytest for pure modules under `tests/`

### Integration Points
- Phase 4 GUI will call `WebcamEngine` only — no duplicate YOLO/camera logic

</code_context>

<specifics>
## Specific Ideas

Retroactive phase closure — verify existing implementation meets success criteria before advancing to Phase 4.

</specifics>

<deferred>
## Deferred Ideas

Web API / Stitch console — Phase 7+

</deferred>
