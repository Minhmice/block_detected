---
phase: 17
slug: roi-fit-score-detection-pipeline
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-29
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` optional-dependencies dev |
| **Quick run command** | `PYTHONPATH=src pytest tests/test_block_detection_v2_<module>.py -x -q` |
| **Full suite command** | `PYTHONPATH=src pytest tests/test_block_detection_v2_*.py -q` |
| **Estimated runtime** | ~15 seconds (benchmark ~5–10s) |

---

## Sampling Rate

- **After every task commit:** Run plan-specific quick pytest from task `<verify><automated>`
- **After every plan wave:** Run cumulative phase tests through current wave
- **Before `/gsd-verify-work`:** Full `tests/test_block_detection_v2_*.py` green + `python -m block_detection_v2.benchmark` accept_rate ≥ 0.80
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 17-01-01 | 01 | 1 | SPIKE-ROI-01 | unit RED | `pytest tests/test_block_detection_v2_roi.py -x` grep fail | ⬜ pending |
| 17-01-02 | 01 | 1 | SPIKE-ROI-01/02 | unit | `pytest tests/test_block_detection_v2_roi.py -q` | ⬜ pending |
| 17-02-01 | 02 | 2 | SPIKE-FIT-01 | unit RED | `pytest tests/test_block_detection_v2_fit.py -x` grep fail | ⬜ pending |
| 17-02-02 | 02 | 2 | SPIKE-FIT-01 | unit | `pytest tests/test_block_detection_v2_fit.py -q` | ⬜ pending |
| 17-02-03 | 02 | 2 | SPIKE-FIT-02 | integration | `python -c process_frame dt50` | ⬜ pending |
| 17-03-01 | 03 | 3 | SPIKE-SCORE-01 | unit RED | `pytest tests/test_block_detection_v2_score.py -x` grep fail | ⬜ pending |
| 17-03-02 | 03 | 3 | SPIKE-SCORE-01/02 | unit | `pytest tests/test_block_detection_v2_score.py -q` | ⬜ pending |
| 17-03-03 | 03 | 3 | SPIKE-SCORE-* | integration | `process_frame dt50 score>=0.42` | ⬜ pending |
| 17-04-01 | 04 | 4 | SPIKE-BENCH-01 | integration RED | `pytest tests/test_block_detection_v2_benchmark.py -x` grep fail | ⬜ pending |
| 17-04-02 | 04 | 4 | SPIKE-BENCH-01 | integration | `python -m block_detection_v2.benchmark` accept_rate≥0.80 | ⬜ pending |
| 17-04-03 | 04 | 4 | SPIKE-BENCH-01 | suite | `pytest tests/test_block_detection_v2_*.py -q` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers phase requirements:
- [x] pytest in `pyproject.toml` dev extras
- [x] `src/block_detection_v2/block_dataset/` dt1–dt108
- [x] Spike baseline in `.planning/spikes/004-dataset-benchmark/output/benchmark.json`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual overlay QA | SPIKE-BENCH-01 | Human judges hex alignment | Open `benchmark_output/overlays/dt50_bench.jpg`, confirm hex on cluster not label |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
