# Phase 2: Dataset Hex Debugger MVP - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-01
**Phase:** 2-Dataset Hex Debugger MVP
**Areas discussed:** Debug instrumentation source, Output persistence, Per-image error handling, Runtime config reload

---

## Debug instrumentation source

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal detector instrumentation | Expose the actual pipeline's missing debug artifacts and timing without changing detection | ✓ |
| Replay pipeline in script | Rerun preprocessing, Hough, grouping, and scoring outside detector | |

**User's choice:** Instrument the detector.
**Notes:** Replaying in the script can diverge from the selected result and approximately doubles CPU cost. Instrumentation must remain observational.

---

## Output persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Automatic light + manual full | Save lightweight JSON for every image; J saves full snapshot plus overlay/edge | ✓ |
| Manual only | Save debug artifacts only when J/S/E is pressed | |

**User's choice:** Automatic lightweight JSON plus manual full snapshot.
**Notes:** Full snapshots may contain sanitized detailed payloads; lightweight JSON must stay compact.

---

## Per-image error handling

| Option | Description | Selected |
|--------|-------------|----------|
| Traceback and continue | Log full traceback, mark image failed, preserve interactive navigation | ✓ |
| Fail fast | Stop the whole dataset session on the first image/runtime error | |

**User's choice:** Continue after per-image failures.
**Notes:** Model, import, and initial config initialization failures remain fatal.

---

## Runtime config reload

| Option | Description | Selected |
|--------|-------------|----------|
| JSON reload + detector rebuild | Reread debug_config.json and create a new configured HexDetector on R | ✓ |
| Python import reload | Reload config.py using importlib | |

**User's choice:** JSON reload and detector rebuild.
**Notes:** This is the lowest-state-risk path for rapid fine-tuning; do not use importlib.

---

## the agent's Discretion

- Exact documented location/bootstrap behavior for `debug_config.json`.
- JSON-safe serialization details for debug-only objects.
- OpenCV window sizing/colors and bounded top-candidate summary shape.

## Deferred Ideas

None.
