---
phase: 03
slug: preprocess-contour-detection
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-31
---

# Phase 03 - Validation Strategy

Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | `pytest` with NumPy/OpenCV synthetic image fixtures |
| Config file | `config/vision.example.json` created in Wave 0 |
| Quick run command | `python -m pytest tests/test_preprocess.py tests/test_detector.py -q` |
| Full suite command | `python -m pytest -q` |
| Estimated runtime | ~20 seconds locally |

## Sampling Rate

- After every task commit: Run `python -m pytest tests/test_preprocess.py tests/test_detector.py -q`
- After every plan wave: Run `python -m pytest -q`
- Before `/gsd-verify-work`: Full suite must be green and one fixture-backed visible-face candidate test must pass
- Max feedback latency: 30 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | GEO-01 | T-03-01 | preprocess rejects invalid input shapes without writing debug files outside configured paths | unit | `python -m pytest tests/test_preprocess.py::test_preprocess_rejects_non_bgr_input -q` | no, W0 | pending |
| 03-01-02 | 01 | 0 | GEO-01 | T-03-02 | adaptive and canny modes both return a single-channel `uint8` mask with BGR source unchanged | unit | `python -m pytest tests/test_preprocess.py -q` | no, W0 | pending |
| 03-02-01 | 02 | 1 | GEO-02 | T-03-03 | contour detector returns only convex 4-vertex candidates within configured area and aspect bounds | unit | `python -m pytest tests/test_detector.py::test_square_candidate_filters_area_aspect_and_convexity -q` | no, W0 | pending |
| 03-02-02 | 02 | 1 | GEO-02 | T-03-04 | empty masks and noise-only masks return `[]` candidates instead of fabricated geometry | unit | `python -m pytest tests/test_detector.py::test_empty_mask_returns_no_candidates -q` | no, W0 | pending |
| 03-03-01 | 03 | 2 | GEO-01, GEO-02 | T-03-05 | frame-level helper preserves `CaptureFrame.frame_id` and finds at least one candidate on a visible square fixture | integration | `python -m pytest tests/test_preprocess.py tests/test_detector.py -q` | no, W0 | pending |

## Wave 0 Requirements

- [ ] `src/block_detected/preprocess.py` - defines `PreprocessSettings`, `PreprocessResult`, and `preprocess_bgr`.
- [ ] `src/block_detected/detector.py` - defines `DetectorSettings`, `SquareCandidate`, and `find_square_candidates`.
- [ ] `tests/test_preprocess.py` - covers GEO-01 adaptive/canny/morphology behavior with synthetic BGR images.
- [ ] `tests/test_detector.py` - covers GEO-02 contour filtering, ranking, empty masks, and rotated squares.
- [ ] `config/vision.example.json` - documents preprocess and detector threshold defaults.

## Manual-Only Verifications

All Phase 03 behaviors have automated synthetic or fixture-backed verification. Physical camera tuning is deferred to Phase 8 evaluation.

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-31
