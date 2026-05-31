---
phase: 11
slug: edge-impulse-eim-deployment-for-pi-5-inference-load-model-ru
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-31
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` → `testpaths = ["tests"]` |
| **Quick run command** | `PYTHONPATH=backend:src pytest tests/test_eim_model.py tests/test_vision_mock.py tests/test_edge_impulse_runner.py -q` |
| **Full suite command** | `PYTHONPATH=backend:src pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run task `<automated>` command
- **After every plan wave:** Run quick run command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 0 | EI-11-01 | T-11-01 / — | Model binaries gitignored | grep | `grep -q 'backend/models/\*.eim' .gitignore` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 0 | EI-11-01 | — | Env vars documented | grep | `grep -q 'VISION_MOCK_MODE=' .env.example` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 0 | EI-11-02 | T-11-02 / — | Missing model reported, no crash in mock | unit | `pytest tests/test_eim_model.py -q` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | EI-11-03 | — | Lazy EI import; singleton init | unit | `pytest tests/test_edge_impulse_runner.py -q` | ❌ W1 | ⬜ pending |
| 11-02-02 | 02 | 1 | EI-11-04 | — | Mock stable block without EI | unit | `pytest tests/test_vision_mock.py -q` | ❌ W1 | ⬜ pending |
| 11-03-01 | 03 | 2 | EI-11-05 | — | Health exposes EI fields | integration | `pytest tests/test_api_health.py::test_health_ei_fields -x` | ❌ W2 | ⬜ pending |
| 11-03-02 | 03 | 2 | EI-11-05 | — | Loop uses vision mock path | integration | `pytest tests/test_api_detection.py::test_detection_with_vision_mock -x` | ❌ W2 | ⬜ pending |
| 11-04-01 | 04 | 3 | EI-11-06 | — | README deployment section | grep | `grep -q 'EI_MODEL_PATH' README.md` | ❌ W3 | ⬜ pending |
| 11-04-02 | 04 | 3 | EI-11-07 | — | Arch validation sign-off | manual | Record `uname -m` + `getconf LONG_BIT` in this file | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/models/.gitkeep` — directory placeholder
- [ ] `tests/test_eim_model.py` — model path validation tests
- [ ] `.gitignore` — `backend/models/*.eim`
- [ ] `backend/requirements.txt` — `edge_impulse_linux>=1.2.0`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live EI inference on Pi 5 | EI-11-03 | aarch64 `.eim` + hardware | Copy model, `chmod +x`, `VISION_MOCK_MODE=false`, start detection, verify WS telemetry |
| Arch bit width | EI-11-07 | Target-specific | On Pi: `uname -m` → `aarch64`; `getconf LONG_BIT` → `64` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---

## Arch Validation Record (EI-11-07)

Fill during execution on target hardware:

```
uname -m: arm64
getconf LONG_BIT: 64
chmod +x backend/models/block_detector.eim: applied (2026-05-31)
PYTHONPATH=backend:src pytest tests/ -q: 82 passed (2026-05-31)
```
