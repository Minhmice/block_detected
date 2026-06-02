# Roadmap: Block Detected

## Overview

Layered computer-vision Python package: webcam detection today; tracking and alternate backends later.

## Phases

- [x] **Phase 1: Package foundation** - Initial modular refactor (webcam working)
- [x] **Phase 2: CV layered folder structure** - Scalable folder layout, tests, docs

## Phase Details

### Phase 1: Package foundation
**Goal**: Webcam app runs from installable package with AGENTS.md
**Depends on**: Nothing
**Requirements**: REQ-01, REQ-02
**Success Criteria**:
  1. `python main.py` starts webcam inference
  2. Source under `src/block_detected/` (not one monolithic script)
  3. AGENTS.md maps modules to responsibilities
**Plans**: 1 plan (ad-hoc refactor)

Plans:
- [x] 01-01: Initial package refactor

### Phase 2: CV layered folder structure for scalable expansion
**Goal**: Layered folders (apps/config/core/detection/vision/io/ui), pytest foundation, synced docs
**Depends on**: Phase 1
**Requirements**: REQ-02, REQ-03
**Success Criteria**:
  1. Six layers present under `src/block_detected/` with dependency rules documented
  2. `pytest tests/` passes (pure modules)
  3. AGENTS.md + `.planning/codebase/` reflect current tree
**Plans**: 3 plans

Plans:
- [x] 02-01: Finalize layered tree + expansion stubs
- [x] 02-02: Pytest foundation
- [x] 02-03: Docs sync + verification

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package foundation | 1/1 | Complete | 2026-06-02 |
| 2. CV layered structure | 3/3 | Complete | 2026-06-02 |

### Phase 3: Runtime engine, typed config, and detector abstraction for GUI prep

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 2
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 3 to break down)

### Phase 4: Desktop GUI for webcam runtime control and config

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 3
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 4 to break down)

### Phase 5: GUI and runtime hardening for production UAT

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 4
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 5 to break down)

### Phase 6: Detection post-processing, reject rules, and temporal stability

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 5
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 6 to break down)
