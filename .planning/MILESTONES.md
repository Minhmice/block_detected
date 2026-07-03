# Milestones

## v2.0 — Detect Only v4 (Planning: 2026-07-03)

**Status:** Planning complete — 7 phases (3–9), 42 requirements

**Goal:** Modular YOLO inference platform on Raspberry Pi 5 with model/camera discovery, task adapters, threaded pipeline, and FastAPI WebSocket UI.

**Module:** `src/detect_only_v4/` (greenfield)

**Artifacts:** `.planning/research/`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`

**Next:** `/gsd:plan-phase 3`

---

## v1.0 — Hex Detector MVP (Shipped: 2026-07-03)

**Phases completed:** 2 phases, 3 plans

**Delivered:** CPU-only `hex_detector` library with front-first rectangle/hex detection, temporal hold, debug rendering, and interactive dataset debugger.

**Key accomplishments:**

- Front-first rectangle/hex detection with bounded candidates and stable `RejectReason` codes (01-01)
- Guarded temporal hold, score decay, basic/verbose debug rendering (01-02)
- Interactive `scripts/debug_hex_dataset.py` with tiered diagnostics 0–3, per-stage timings, config reload (02-01)

**Stats:** Timeline 2026-06-30 → 2026-07-01; +2,726 / -208 LOC in hex_detector + scripts + tests; 32+ tests passing.

**Archived:** `.planning/milestones/v1.0-ROADMAP.md`, `.planning/milestones/v1.0-REQUIREMENTS.md`

---

## Legacy — Block Detected Core (pre-pivot)

YOLO webcam inference, layered CV package, runtime engine, GUI, postprocess, web telemetry API.

Phases 2–7 verified. Phases 8–14 deferred when project pivoted to hex_detector on 2026-06-30.

---

## v2.0 — Classical CV Block Detection (removed)

Planning artifacts for this milestone (spikes, phases 15–18, `docs/BLOCK_DETECTION_V2.md`) were removed on 2026-06-30. No active v2 roadmap.
