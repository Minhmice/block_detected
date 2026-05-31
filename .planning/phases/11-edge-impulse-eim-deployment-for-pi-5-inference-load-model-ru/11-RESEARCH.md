# Phase 11: Edge Impulse .eim Deployment — Research

**Researched:** 2026-05-31
**Domain:** Edge Impulse Linux Python SDK (`edge_impulse_linux`), `.eim` executable deployment on aarch64 Pi 5, FastAPI detection loop integration
**Confidence:** HIGH (official Edge Impulse docs + existing backend architecture verified in codebase)

---

## Summary

Phase 11 adds Edge Impulse Linux AARCH64 inference to the existing FastAPI console. The exported model `models/minhmice-project-1-linux-aarch64-v1-impulse-#2.eim` deploys to `backend/models/block_detector.eim` (gitignored). The Python SDK `edge_impulse_linux` wraps the `.eim` as a subprocess via `ImageImpulseRunner`.

**Primary recommendation:** Create `backend/app/services/edge_impulse_runner.py` with a singleton runner initialized once at app startup; branch `DetectionLoopService._run_loop()` on `VISION_MOCK_MODE` to either call the mock vision service or `detect_block_with_ei()` which runs the existing contour/geometry pipeline and replaces stub/TFLite classification with EI on the warped 128×128 RGB crop. Extend `/health` with `visionMockMode`, `eiModelLoaded`, and `eiModelPath`.

**Platform note:** The exported `.eim` is **linux-aarch64 only**. Dev Mac (x86_64/arm64 without matching EIM) must use `VISION_MOCK_MODE=true`. Pi 5 Bookworm 64-bit is the target for live EI inference.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EI-11-01 | Model at `backend/models/block_detector.eim`, gitignored, env `EI_MODEL_PATH` | Copy from repo `models/*.eim`; `.gitignore` rule; `.env.example` vars |
| EI-11-02 | `edge_impulse_linux` dep + system packages + startup executable check | PyPI `edge-impulse-linux`; apt packages documented; `os.access(X_OK)` + chmod guidance |
| EI-11-03 | `edge_impulse_runner.py` — load once, `classify_frame(BGR) → DetectionResult` | `ImageImpulseRunner.init()` once; BGR→RGB; map `result.classification` labels to block 1–4 |
| EI-11-04 | `VISION_MOCK_MODE=true` skips EI, stable fake detections | Separate `vision_mock.py`; env read in factory; no import of `edge_impulse_linux` when mock |
| EI-11-05 | Wire into health, start/stop, MJPEG, WebSocket loop | Extend `DetectionLoopService._run_loop`; `/health` fields; existing routes unchanged |
| EI-11-06 | `make dev` / README for model placement, deps, chmod, `/health` | `make dev` already exists; add README section + `.env.example` |
| EI-11-07 | Validation: `uname -m`, `getconf LONG_BIT`, chmod, backend tests | Record in `11-VALIDATION.md` sign-off; pytest with mocked runner |
</phase_requirements>

---

## Edge Impulse Linux Python SDK

### Installation

```bash
pip install edge_impulse_linux
# System deps (Pi / Debian):
sudo apt-get install -y libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
```

Package: [edge-impulse-linux on PyPI](https://pypi.org/project/edge-impulse-linux/) (v1.2.2 as of 2026-01).

### Model file requirements

1. Download or copy `.eim` for target arch (`runner-linux-aarch64` for Pi 5)
2. **Must be executable:** `chmod +x backend/models/block_detector.eim`
3. SDK spawns `.eim` as subprocess — non-executable file fails at `runner.init()`

[Source: Edge Impulse Linux Python SDK docs](https://docs.edgeimpulse.com/tools/libraries/sdks/inference/linux/python)

### Inference API (image classification)

```python
from edge_impulse_linux.image import ImageImpulseRunner
import cv2

runner = ImageImpulseRunner("backend/models/block_detector.eim")
model_info = runner.init()  # call ONCE

# OpenCV BGR → RGB for get_features_from_image
rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
features, cropped = runner.get_features_from_image(rgb)
res = runner.classify(features)

# res["result"]["classification"] → dict label → probability (0..1)
# res["timing"] → inference timing metadata
```

[Source: edgeimpulse/linux-sdk-python examples/image/classify-image.py, ShawnHymel Pi live inference sample]

### Label → block_id mapping

Edge Impulse project labels may be `"block_01"`, `"1"`, `"class0"`, etc. Map via configurable dict in runner:

```python
_LABEL_TO_BLOCK_ID = {
    "block_01": 1, "block_02": 2, "block_03": 3, "block_04": 4,
    "1": 1, "2": 2, "3": 3, "4": 4,
}
```

Take argmax of classification dict; if below threshold → `DetectionStatus.LOW_CONFIDENCE`.

---

## Integration Architecture

### Current backend flow (unchanged camera/MJPEG/WS shell)

```
DetectionLoopService._run_loop()
  → create_frame_source_from_env().read()
  → detect_block(frame, settings)          # stub classifier today
  → build_telemetry_from_contract(result)
  → ws.broadcast_json + latest_jpeg
```

### Proposed Phase 11 flow

```
DetectionLoopService._run_loop()
  → frame = read()
  → if is_vision_mock_mode():
        result, scores = vision_mock.detect(frame)
    else:
        result, scores = ei_runner.detect_from_frame(frame, settings)
  → build_telemetry_from_contract(result, classifier_scores=scores)
```

### `detect_from_frame` strategy (geometry + EI classification)

Reuse existing pipeline geometry; replace classifier step:

1. `find_square_candidates_from_frame()` → pick best candidate (same as `detect_block`)
2. `geometry_from_candidate()` → corners, warp 128×128 BGR
3. EI classify on **warped RGB crop** (matches training crop semantics)
4. `pixel_to_pickup_pose()` if calibration loaded
5. Assemble `DetectionResult` with `validate_detection_result()`

Alternative if EI impulse is full-frame object detection: pass full BGR→RGB frame. **Default plan:** warped crop (consistent with Phase 5 TFLite path).

### Singleton runner lifecycle

| Event | Action |
|-------|--------|
| App lifespan startup | `validate_eim_model(path)` — exists + executable |
| First non-mock detection start | `EdgeImpulseRunnerService.ensure_initialized()` |
| App shutdown | `runner.close()` if SDK supports it |
| Mock mode | Skip runner entirely |

Place validation in `backend/app/services/eim_model.py` (pure pathlib/os — no EI import). Runner in `edge_impulse_runner.py`.

---

## Existing Code Insertion Points

| File | Change |
|------|--------|
| `backend/requirements.txt` | Add `edge_impulse_linux>=1.2.0` (optional extra or conditional — use direct dep; mock mode tests skip import) |
| `backend/app/services/detection_loop.py` | Branch inference path; pass `classifier_scores` to wire_builder |
| `backend/app/routes/health.py` | Add EI status fields to `SystemStatusWire` |
| `backend/app/schemas/wire.py` | Extend `SystemStatusWire` |
| `backend/app/main.py` | Call `validate_eim_model()` in lifespan (warn, don't crash on dev Mac) |
| `.env.example` | `EI_MODEL_PATH`, `VISION_MOCK_MODE` |
| `.gitignore` | `backend/models/*.eim` |
| `README.md` | EI deployment section |

**No frontend changes required** — wire format unchanged; `/health` gains optional new camelCase fields.

---

## Mock Vision Service

`backend/app/services/vision_mock.py`:

- `is_vision_mock_mode()` — reads `VISION_MOCK_MODE` env (`true`/`1`/`yes`)
- `detect_from_frame(frame) -> tuple[DetectionResult, dict[str, float]]` — returns stable block 2 detection at frame center with fixed corners (640×480), confidence 0.92, status OK
- Uses `SAMPLE_SUCCESS_BLOCK_1` pattern from `detection_contract.py` as template but block_id=2 for visual distinction from pipeline stub

When `VISION_MOCK_MODE=true`, backend starts even without `.eim` present.

---

## Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| aarch64 `.eim` on x86 dev Mac | Default `VISION_MOCK_MODE=true` in `.env.example`; document Pi-only live EI |
| Forgot `chmod +x` | Startup check + README + `/health` `eiModelExecutable: false` |
| BGR passed to EI | Always `cv2.cvtColor(..., COLOR_BGR2RGB)` before `get_features_from_image` |
| Runner init per frame | Singleton on `EdgeImpulseRunnerService`; test asserts `init` called once |
| `edge_impulse_linux` import breaks CI | Lazy import inside runner; mock mode never imports package |
| Label mismatch | Log unknown labels; return `no_detection` with debug reason |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pyproject.toml` → `testpaths = ["tests"]` |
| Quick run command | `PYTHONPATH=backend:src pytest tests/test_eim_model.py tests/test_vision_mock.py tests/test_edge_impulse_runner.py -q` |
| Full suite command | `PYTHONPATH=backend:src pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EI-11-01 | `.gitignore` ignores `backend/models/*.eim` | unit | `grep -q 'backend/models/\*.eim' .gitignore` | ❌ Wave 0 |
| EI-11-01 | `.env.example` has `EI_MODEL_PATH` | unit | `grep -q 'EI_MODEL_PATH=' .env.example` | ❌ Wave 0 |
| EI-11-02 | Model validator detects missing file | unit | `pytest tests/test_eim_model.py::test_validate_missing_model -x` | ❌ Wave 0 |
| EI-11-02 | Model validator detects non-executable | unit | `pytest tests/test_eim_model.py::test_validate_not_executable -x` | ❌ Wave 0 |
| EI-11-03 | Runner maps classification to block_id | unit (mocked) | `pytest tests/test_edge_impulse_runner.py::test_map_classification_to_block -x` | ❌ Wave 1 |
| EI-11-04 | Mock mode returns stable detection | unit | `pytest tests/test_vision_mock.py::test_mock_stable_block -x` | ❌ Wave 1 |
| EI-11-05 | `/health` exposes visionMockMode + eiModelLoaded | integration | `pytest tests/test_api_health.py::test_health_ei_fields -x` | ❌ Wave 2 |
| EI-11-05 | Loop uses mock when VISION_MOCK_MODE=true | integration | `pytest tests/test_api_detection.py::test_detection_with_vision_mock -x` | ❌ Wave 2 |
| EI-11-06 | README contains chmod + model path | docs | `grep -q 'chmod +x backend/models/block_detector.eim' README.md` | ❌ Wave 3 |
| EI-11-07 | Arch validation recorded | manual | Human runs `uname -m` + `getconf LONG_BIT` on Pi; sign 11-VALIDATION.md | manual |

### Hardware-gated (Pi 5 only)

```python
pi_aarch64 = pytest.mark.skipif(
    not (platform.machine() == "aarch64" and Path(os.getenv("EI_MODEL_PATH", "")).exists()),
    reason="Pi aarch64 EIM not available",
)
```

Use `@pi_aarch64` for optional live EI smoke test — not required for CI green.

---

## RESEARCH COMPLETE
