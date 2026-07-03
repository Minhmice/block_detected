# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Hex Detector MVP

**Shipped:** 2026-07-03
**Phases:** 2 | **Plans:** 3

### What Was Built

- `src/hex_detector/` — front-first rectangle/hex detection from YOLO bbox with bounded candidate search
- Temporal hold state machine with guarded score decay and typed `ScoreBreakdown` on every result
- Basic/verbose debug rendering (Pi-friendly defaults to winner-only geometry)
- `scripts/debug_hex_dataset.py` — interactive dataset debugger with 4 diagnostic levels, keyboard controls, runtime config reload

### What Worked

- Front-first architecture eliminated the old 7-line combinatorial bottleneck and made rectangle fallback natural
- Greenfield `hex_detector/` module avoided entanglement with legacy `block_detected` code
- Phase 2 debugger stayed observational — instrumentation exposed truth without altering detector decisions
- Deterministic test suite (32+ tests) caught regressions during instrumentation refactors

### What Was Inefficient

- Planning artifacts (ROADMAP, REQUIREMENTS, STATE) drifted during pivot from Block Detected to Hex Detector — required reconciliation at milestone close
- Phase 2 verification needed a re-verification cycle (18/20 → 20/20) after test modifications were initially uncommitted
- Human verification items (Pi 5 profiling, OpenCV keyboard behavior) remain unclosed

### Patterns Established

- Front-first: detect rectangle from 2 vertical + 2 horizontal lines; hex upgrade is additive
- Bounded candidates via config (`max_front_candidates`, `max_right_candidates`)
- Single-advance `hold_age` via `try_hold()` with rollback on guard failure
- Fresh detector instance per dataset image to prevent cross-image state leakage
- Per-stage `perf_counter` timings split into hough/filter/group/merge

### Key Lessons

1. Archive planning artifacts at milestone boundaries — stale ROADMAP entries confuse tooling (`gsd-sdk roadmap.analyze` missed Phase 1 until fixed)
2. Commit test modifications in the same commit as code refactors — uncommitted test changes caused verification gaps
3. Observational debugger instrumentation is a low-risk way to accelerate dataset tuning without touching core detection logic

### Cost Observations

- Timeline: 2 days (2026-06-30 → 2026-07-01)
- LOC: +2,726 / -208 in hex_detector + scripts + tests
- Notable: Two-phase MVP (core + debugger) delivered complete interactive workflow in under 48 hours

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 2 | 3 | Greenfield pivot from Block Detected; front-first CV architecture |

### Cumulative Quality

| Milestone | Tests | Must-haves | Human verification |
|-----------|-------|------------|-------------------|
| v1.0 | 32+ | 20/20 (Phase 2) | 2 items pending (Pi 5, OpenCV GUI) |

### Top Lessons (Verified Across Milestones)

1. Bounded candidate search prevents combinatorial CPU explosion on Pi 5
2. Debugger phases should be strictly observational to preserve detection integrity
