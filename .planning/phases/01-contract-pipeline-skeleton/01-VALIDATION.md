---
phase: 01
slug: contract-pipeline-skeleton
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-31
---

# Phase 01 - Validation Strategy

Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Python stdlib `unittest` |
| Config file | none |
| Quick run command | `python3 -m unittest tests/test_pipeline.py -v` |
| Full suite command | `python3 -m unittest discover -v` |
| Estimated runtime | ~5 seconds |

## Sampling Rate

- After every task commit: Run `python3 -m unittest tests/test_pipeline.py -v`
- After every plan wave: Run `python3 -m unittest discover -v`
- Before `/gsd-verify-work`: Full suite must be green
- Max feedback latency: 10 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | CONT-01 | T-01-01 | `detect_block(frame)` returns validated `DetectionResult` without throwing on ordinary unsupported input | unit | `python3 -m unittest tests/test_pipeline.py -v` | no, W0 | pending |
| 01-01-02 | 01 | 0 | CONT-02 | T-01-02 | synthetic success path populates identity, confidence, center, ordered corners, and angle | unit | `python3 -m unittest tests/test_pipeline.py -v` | no, W0 | pending |
| 01-01-03 | 01 | 0 | CONT-03 | T-01-03 | rejected frames use `debug.rejection_reason` and no candidate geometry | unit | `python3 -m unittest tests/test_pipeline.py -v` | no, W0 | pending |
| 01-01-04 | 01 | 1 | CONT-01 | T-01-01 | package import path and root compatibility shim both return the same contract objects | unit | `python3 -m unittest discover -v` | no, W0 | pending |

## Wave 0 Requirements

- [ ] `tests/__init__.py` - keeps tests importable under stdlib discovery.
- [ ] `tests/test_pipeline.py` - covers CONT-01, CONT-02, and CONT-03.
- [ ] `tests/test_detection_contract.py` - locks contract sample serialization and identity mismatch behavior before import-path changes.
- [ ] No third-party framework install is required for Phase 01.

## Manual-Only Verifications

All Phase 01 behaviors have automated verification. No camera hardware is required.

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-31
