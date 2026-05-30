# Phase 10: Real Camera Capture on Dev Machine — Research

**Researched:** 2026-05-31
**Domain:** OpenCV VideoCapture platform backends (macOS AVFoundation vs Linux V4L2), CameraSettings extension, env/config wiring for no-mock USB capture
**Confidence:** HIGH (root cause verified by direct `cv2.VideoCapture` probe on dev machine; OpenCV build info inspected)

---

## Summary

Phase 10 fixes one root cause: `UsbVideoCaptureFrameSource.start()` hardcodes `cv2.CAP_V4L2` as the OpenCV VideoCapture backend on both device path and index code paths (lines 171 and 173 of `camera.py`). V4L2 is a Linux kernel subsystem; the macOS OpenCV build **does not include it**. A direct runtime probe confirms:

- `cv2.VideoCapture(0, cv2.CAP_V4L2)` → `isOpened() = False` on macOS [VERIFIED: direct probe 2026-05-31]
- `cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)` → `isOpened() = True` on macOS [VERIFIED: direct probe 2026-05-31]
- `cv2.VideoCapture(0, cv2.CAP_ANY)` → `isOpened() = True` on macOS [VERIFIED: direct probe 2026-05-31]

The fix is a platform-aware backend selector added to `UsbVideoCaptureFrameSource`, controlled by a new `cv_backend: str = "auto"` field on `CameraSettings`. With `"auto"`, the selector maps: `darwin` → `CAP_AVFOUNDATION`, `linux` → `CAP_V4L2`, other → `CAP_ANY`. The config JSON can lock to an explicit value (`"avfoundation"`, `"v4l2"`, `"any"`) when auto-detection is insufficient.

The second concern is the existing `main.py` lifespan: the detection loop only auto-starts when `MOCK_CAMERA=true`. With mock off, the operator must call `POST /api/detection/start` — this is **correct behavior** (Phase 9 already has this flow) and requires no change. The Phase 9 console START button triggers this.

**Primary recommendation:** Extend `CameraSettings` with `cv_backend: str = "auto"`, implement `_select_cv_backend()` in `UsbVideoCaptureFrameSource`, add `config/camera.usb.mac.json` as a dev-ready profile, and document the macOS TCC camera permission prompt. No changes to `main.py` or the detection loop are needed.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAM-10-01 | Live USB/built-in capture at 640×480 without mock | Fix `CAP_V4L2` hardcode → platform-aware backend; `cv_backend="auto"` resolves correct backend per `sys.platform` |
| CAM-10-02 | Platform-aware VideoCapture backend | New `cv_backend: str = "auto"` field on `CameraSettings`; `_select_cv_backend()` maps darwin/linux/other to OpenCV constant |
| CAM-10-03 | Console MJPEG+WS after explicit start when mock off | Phase 9 loop already correct (no auto-start without mock); requires `MOCK_CAMERA=` unset + `CAMERA_CONFIG=config/camera.usb.mac.json`; `POST /api/detection/start` triggers capture |
| CAM-10-04 | camera_smoke.py validates live capture | Script already exists at `scripts/camera_smoke.py`; needs `config/camera.usb.mac.json` with `active_profile: "usb"` and `cv_backend: "avfoundation"` to run without args change |
</phase_requirements>

---

## Root Cause Analysis (verified)

### CAP_V4L2 on macOS — Confirmed Broken

```
# OpenCV 4.13.0 on macOS (darwin 25.5.0, dev machine 2026-05-31)
cv2.VideoCapture(0, cv2.CAP_V4L2)        → isOpened() = False   ❌
cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION) → isOpened() = True    ✅
cv2.VideoCapture(0, cv2.CAP_ANY)          → isOpened() = True    ✅
```

[VERIFIED: direct probe on dev machine 2026-05-31]

**Why the constant is defined but non-functional:** OpenCV defines all backend IDs in shared headers (for cross-platform code compatibility), but only compiles supported backends per platform. On macOS, `CAP_V4L2 = 200` exists as a compile-time constant, but specifying it as `apiPreference` to `VideoCapture()` causes OpenCV to fail backend initialization and return a closed capture object.

OpenCV build info (macOS dev machine):
```
Video I/O:
  FFMPEG:       YES
  GStreamer:    NO
  AVFoundation: YES     ← macOS native camera API
```

[VERIFIED: `cv2.getBuildInformation()` on dev machine 2026-05-31]

### Exact lines to fix in `camera.py`

```170:174:src/block_detected/camera.py
    def start(self) -> None:
        index = self._settings.camera_index
        if self._settings.device_path:
            cap = cv2.VideoCapture(self._settings.device_path, cv2.CAP_V4L2)  # ← broken on macOS
        else:
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)  # ← broken on macOS
```

Both calls must use `self._select_cv_backend()` instead of the hardcoded constant.

---

## Standard Stack

### Core (no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| OpenCV (`opencv-python`) | 4.13.0 (installed) | `VideoCapture` with `CAP_AVFOUNDATION` on macOS | Already in project; 4.13 includes all needed platform backends [VERIFIED: installed] |
| `sys` / `platform` (stdlib) | 3.11+ | `sys.platform` check for backend selection | No new dep; cleanest platform discriminator |
| NumPy | ≥2,<3 | Frame buffers (unchanged) | Existing constraint |

### No New Dependencies Required

All platform backends (`CAP_V4L2`, `CAP_AVFOUNDATION`, `CAP_ANY`) are part of the installed OpenCV package — selecting the right one is pure Python logic. [VERIFIED: constants present in cv2 module on dev machine]

---

## Architecture Patterns

### Pattern 1: Platform-Aware Backend Selector

**What:** A helper method on `UsbVideoCaptureFrameSource` that maps platform → `cv2.CAP_*` constant, with explicit override from `CameraSettings.cv_backend`.

**When to use:** Always — called in `start()` instead of hardcoded `cv2.CAP_V4L2`.

**Example:**
```python
# Source: verified cv2 backend probe on dev machine 2026-05-31
import sys

_CV_BACKEND_MAP: dict[str, int] = {
    "v4l2":         cv2.CAP_V4L2,           # 200 — Linux only
    "avfoundation": cv2.CAP_AVFOUNDATION,   # 1200 — macOS
    "dshow":        cv2.CAP_DSHOW,          # 700 — Windows
    "any":          cv2.CAP_ANY,            # 0 — auto
}

def _select_cv_backend(cv_backend: str) -> int:
    """Return cv2 VideoCapture apiPreference for current platform."""
    if cv_backend and cv_backend != "auto":
        key = cv_backend.lower()
        if key not in _CV_BACKEND_MAP:
            raise ValueError(f"unknown cv_backend: {cv_backend!r}")
        return _CV_BACKEND_MAP[key]
    # auto-detect from platform
    p = sys.platform
    if p == "darwin":
        return cv2.CAP_AVFOUNDATION
    if p.startswith("linux"):
        return cv2.CAP_V4L2
    return cv2.CAP_ANY
```

### Pattern 2: CameraSettings Extension

**What:** Add `cv_backend: str = "auto"` to `CameraSettings` dataclass; propagate through `load_camera_settings()` and `_profile_to_settings()`.

**When to use:** Whenever the `usb` backend profile is active.

**Example:**
```python
@dataclass
class CameraSettings:
    backend: str = "image_sequence"
    # ... existing fields ...
    cv_backend: str = "auto"   # "auto" | "v4l2" | "avfoundation" | "dshow" | "any"
```

In `load_camera_settings()`, the JSON key `"cv_backend"` from the profile is passed through `merged.get("cv_backend", "auto")`. No special handling needed — the existing generic merge already propagates arbitrary profile keys.

In `frame_source_factory._profile_to_settings()`, the existing `filtered = {k: v for k, v in merged.items() if not str(k).startswith("_")}` already passes all non-comment keys to `CameraSettings(**filtered)` — adding `cv_backend` to the dataclass is sufficient.

### Pattern 3: Dev USB Config Profile

**What:** A `config/camera.usb.mac.json` (plus a Linux variant) that makes `CAMERA_CONFIG=config/camera.usb.mac.json` the complete dev setup. The `camera.example.json` is unchanged (stays `image_sequence` for mock mode).

**When to use:** Dev machine real-camera sessions; `camera_smoke.py` for CAM-10-04 validation.

```json
// config/camera.usb.mac.json
{
  "_comment": "USB camera on macOS dev — cv_backend=avfoundation required",
  "active_profile": "usb",
  "defaults": {
    "width": 640,
    "height": 480,
    "warmup_frames": 5,
    "lock_exposure": false,
    "lock_white_balance": false
  },
  "profiles": {
    "usb": {
      "_comment": "Built-in FaceTime / USB UVC via AVFoundation on macOS",
      "backend": "usb",
      "camera_index": 0,
      "cv_backend": "avfoundation"
    }
  },
  "debug": {
    "enabled": false,
    "directory": "debug_frames",
    "every_n_frames": 1,
    "max_files": 200,
    "run_id": null
  }
}
```

For Raspberry Pi (Linux), the existing `camera.example.json` `"usb"` profile already works once `cv_backend` defaults to `"auto"` (auto → `CAP_V4L2` on linux).

### Pattern 4: Startup Sequence with Real Camera (no mock)

**What:** Documented env + API call sequence for `MOCK_CAMERA=false` on dev Mac.

```
# Terminal — start backend with real USB camera
MOCK_CAMERA=        # unset or empty string
CAMERA_CONFIG=config/camera.usb.mac.json
uvicorn app.main:app --reload --port 8000 --workers 1

# Backend starts; detection loop is NOT auto-started (correct — mock=false path)
# lifespan: if is_mock_mode(): await detection_loop.start()  ← skipped

# Operator opens console → clicks START
POST /api/detection/start
# → detection_loop.start() → _run_loop()
# → create_frame_source_from_env() → UsbVideoCaptureFrameSource(settings)
# → source.start() → _select_cv_backend("avfoundation") → CAP_AVFOUNDATION
# → cap.isOpened() = True ✅
# → MJPEG at /video/stream shows live feed
# → WS /ws/detection broadcasts telemetry
```

**No change to `main.py`** — the existing lifespan condition is correct. [VERIFIED: `main.py` lines 32-34]

### Anti-Patterns to Avoid

- **Hardcode `cv2.CAP_ANY` as the only fix:** Works on both platforms but loses V4L2 device enumeration controls on Linux (e.g., `v4l2-ctl` integration). Use explicit platform mapping with `"auto"` default.
- **Modify `camera.example.json`:** That file is the mock-mode reference. Dev machine USB config belongs in a separate file.
- **Auto-start detection loop when `MOCK_CAMERA=false`:** Opens camera on backend boot; Pi deploy has one camera, should be operator-triggered. Keep existing lifespan logic.
- **Request camera permission before explaining to user:** macOS TCC silently fails if the terminal/IDE does not have camera access. Document the one-time permission prompt.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Platform detection | OS name string parsing | `sys.platform` (stdlib) | Single canonical discriminator; `"darwin"`, `"linux"`, `"win32"` are stable |
| Backend constant lookup | Hardcoded `if/elif` chains everywhere | `_CV_BACKEND_MAP` dict in `camera.py` + one `_select_cv_backend()` call | Single point of truth; easy to extend for Windows |
| USB config for dev | Modifying example.json | Separate `camera.usb.mac.json` | Example stays clean for mock/CI; new file is version-controlled |
| Camera permission check | OS TCC API | Document manual grant + `AVCaptureDevice` error message | TCC is user-level; Python can't pre-check reliably |

---

## Common Pitfalls

### Pitfall 1: V4L2 Constant Defined but Backend Not Compiled
**What goes wrong:** `cv2.CAP_V4L2` is accessible as a Python int (200) on macOS, so `hasattr(cv2, 'CAP_V4L2')` returns True. Developers assume it works.
**Why it happens:** OpenCV defines all backend IDs in shared headers. Only the backend *implementation* is conditionally compiled.
**How to avoid:** Always probe with `cap.isOpened()` before trusting the constant. Use `cv2.getBuildInformation()` to confirm which backends are compiled.
**Warning signs:** `cap.isOpened()` returns `False`; no OpenCV error raised; `RuntimeError("failed to open USB camera")` from `UsbVideoCaptureFrameSource`.
[VERIFIED: observed on dev machine 2026-05-31]

### Pitfall 2: macOS TCC Camera Permission Denied
**What goes wrong:** First run of `VideoCapture(0, cv2.CAP_AVFOUNDATION)` returns `isOpened() = False` even though camera exists and backend is correct.
**Why it happens:** macOS Transparency, Consent, and Control (TCC) denies camera access to processes that haven't been granted permission. Terminal, Python, or the calling app must have "Camera" access in System Preferences → Privacy & Security.
**How to avoid:** Run `camera_smoke.py` once directly from Terminal before starting the backend — macOS will show the permission prompt. Check System Preferences if prompt doesn't appear (may be pre-denied). [ASSUMED: standard macOS TCC behavior, not directly verified in this session — but well-documented Apple behavior]
**Warning signs:** `isOpened() = False` on macOS with `CAP_AVFOUNDATION` even after fixing V4L2.

### Pitfall 3: warmup_frames Blocks Loop Start
**What goes wrong:** With a real camera, `warmup_frames=5` drains 5 frames before the loop is ready. This is synchronous in `start()` and blocks the asyncio event loop (called via `asyncio.to_thread` in `_run_loop` — but `source.start()` itself is not).
**Why it happens:** `_run_loop` calls `self._frame_source.start()` directly (not via `asyncio.to_thread`). For real cameras, warmup can take 100–300ms per frame.
**How to avoid:** Call `source.start()` inside `asyncio.to_thread(source.start)` in `_run_loop`, or reduce `warmup_frames` to 0–3 in the USB config. For Phase 10, document it as a known limitation; the 5-frame default is already set to 5 in `CameraSettings`.
**Warning signs:** API call to `POST /api/detection/start` returns slowly; first frame appears with delay.

### Pitfall 4: lock_exposure / lock_white_balance on macOS
**What goes wrong:** `_apply_usb_manual_controls()` calls `cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)` and `cap.set(cv2.CAP_PROP_AUTO_WB, 0)`. On macOS AVFoundation, these `cap.set()` calls return `False` (unsupported) but don't raise.
**Why it happens:** AVFoundation camera controls use macOS-native APIs, not V4L2 property IDs. OpenCV's AVFoundation backend exposes only a subset of `CAP_PROP_*`.
**How to avoid:** The existing code already handles this gracefully — failed `cap.set()` calls append to `settings_unsupported` in metadata. For dev Mac, set `lock_exposure: false` and `lock_white_balance: false` in `camera.usb.mac.json` to skip the attempt.
**Warning signs:** `settings_unsupported` list is non-empty in frame metadata — this is expected and non-fatal on macOS.

### Pitfall 5: Multiple `camera_index` Values on macOS
**What goes wrong:** macOS built-in FaceTime camera may not be index 0 if other devices are connected; USB camera might be index 1 or 2.
**Why it happens:** AVFoundation enumerates cameras in non-deterministic order (USB vs. built-in). [ASSUMED: common macOS camera enumeration behavior]
**How to avoid:** Expose `camera_index: 0` in config; document that users can try `1`, `2`, etc. or use `device_path` for explicit UVC device (e.g., `device_path: ""` + index, or use `v4l2-ctl` on Linux). The `camera_smoke.py` script can iterate indices to find the right one.
**Warning signs:** `isOpened() = True` but frames are from wrong camera, or `isOpened() = False` at index 0 despite camera being present.

---

## Code Examples

### Minimal Fix: Platform-Aware start() in UsbVideoCaptureFrameSource

```python
# Source: synthesized from cv2 probe results 2026-05-31 and existing camera.py structure
import sys

_CV_BACKEND_MAP: dict[str, int] = {
    "v4l2":         cv2.CAP_V4L2,           # 200 — Linux only (V4L2 kernel module)
    "avfoundation": cv2.CAP_AVFOUNDATION,   # 1200 — macOS native
    "dshow":        cv2.CAP_DSHOW,          # 700 — Windows DirectShow
    "msmf":         cv2.CAP_MSMF,           # 1400 — Windows Media Foundation
    "any":          cv2.CAP_ANY,            # 0 — OpenCV auto-select
}


def _select_cv_backend(cv_backend: str) -> int:
    if cv_backend and cv_backend != "auto":
        key = cv_backend.lower()
        if key not in _CV_BACKEND_MAP:
            raise ValueError(f"unknown cv_backend: {cv_backend!r}; valid: {sorted(_CV_BACKEND_MAP)}")
        return _CV_BACKEND_MAP[key]
    p = sys.platform
    if p == "darwin":
        return cv2.CAP_AVFOUNDATION  # 1200
    if p.startswith("linux"):
        return cv2.CAP_V4L2          # 200
    return cv2.CAP_ANY               # 0 — Windows/other


class UsbVideoCaptureFrameSource:
    def start(self) -> None:
        backend_api = _select_cv_backend(self._settings.cv_backend)
        index = self._settings.camera_index
        if self._settings.device_path:
            cap = cv2.VideoCapture(self._settings.device_path, backend_api)
        else:
            cap = cv2.VideoCapture(index, backend_api)
        if not cap.isOpened():
            raise RuntimeError(
                f"failed to open USB camera index={index} device={self._settings.device_path!r} "
                f"backend={self._settings.cv_backend!r} (resolved api={backend_api})"
            )
        # ... rest unchanged ...
```

### CameraSettings Dataclass Addition

```python
@dataclass
class CameraSettings:
    # ... all existing fields unchanged ...
    cv_backend: str = "auto"
    # Valid: "auto" | "v4l2" | "avfoundation" | "dshow" | "msmf" | "any"
    # "auto" → platform detection: darwin=avfoundation, linux=v4l2, other=any
```

### load_camera_settings() Extension

The existing `load_camera_settings()` in `camera.py` already passes arbitrary JSON keys through `merged.get("cv_backend", "auto")`:

```python
# In load_camera_settings() — add one line alongside existing fields:
settings = CameraSettings(
    # ... existing assignments ...
    cv_backend=str(merged.get("cv_backend", "auto")),
)
```

### Dev Smoke Run (CAM-10-04)

```bash
# After creating config/camera.usb.mac.json with active_profile="usb", cv_backend="avfoundation":
python scripts/camera_smoke.py --config config/camera.usb.mac.json --frames 3
# Expected output:
# { "frame_id": "frame_000001", "shape": [480, 640, 3], "source": "usb-opencv", ... }
# { "frame_id": "frame_000002", ... }
# { "frame_id": "frame_000003", ... }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `CAP_V4L2` hardcoded in both VideoCapture calls | `_select_cv_backend(cv_backend)` with platform auto-detection | Phase 10 | USB capture works on macOS dev without config change |
| No `cv_backend` field in config | `cv_backend: "auto"` \| `"avfoundation"` \| `"v4l2"` in profile JSON | Phase 10 | Explicit override when auto-detect insufficient |
| Mock auto-start only (no USB path documented) | `MOCK_CAMERA=` + `CAMERA_CONFIG=camera.usb.mac.json` + explicit START | Phase 10 | Documented path from Phase 9 console to real camera |

**Deprecated/outdated after Phase 10:**
- `cv2.CAP_V4L2` as a hardcoded argument in `UsbVideoCaptureFrameSource` — use `_select_cv_backend()`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` → `testpaths = ["tests"]` |
| Quick run command | `pytest tests/test_camera_source.py -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAM-10-01 | USB capture returns 640×480 BGR frame | unit (mocked) | `pytest tests/test_camera_source.py::test_usb_capture_platform_backend -x` | ❌ Wave 0 |
| CAM-10-02 | darwin → CAP_AVFOUNDATION; linux → CAP_V4L2 | unit | `pytest tests/test_camera_source.py::test_backend_selector_darwin -x` | ❌ Wave 0 |
| CAM-10-02 | explicit cv_backend override in config | unit | `pytest tests/test_camera_source.py::test_backend_selector_explicit_override -x` | ❌ Wave 0 |
| CAM-10-02 | unknown cv_backend raises ValueError | unit | `pytest tests/test_camera_source.py::test_backend_selector_unknown_raises -x` | ❌ Wave 0 |
| CAM-10-03 | backend does NOT auto-start loop when MOCK_CAMERA unset | integration | `pytest tests/test_api_health.py::test_loop_idle_when_not_mock -x` | ❌ Wave 0 |
| CAM-10-03 | loop starts after POST /api/detection/start (mocked camera) | integration | `pytest tests/test_api_detection.py::test_start_with_mocked_usb_source -x` | ❌ Wave 0 |
| CAM-10-04 | camera_smoke.py runs without error on usb.mac.json (mock cap) | unit | `pytest tests/test_camera_smoke_script.py -x` | ❌ Wave 0 |
| CAM-10-01 | Existing USB backend failure test still passes | regression | `pytest tests/test_camera_source.py::test_backend_open_failure_is_explicit -x` | ✅ exists |
| CAM-10-01 | Existing mock factory test still passes | regression | `pytest tests/test_frame_source_factory.py::test_mock_camera_uses_image_sequence -x` | ✅ exists |

**Hardware-gated tests** (optional, skip in CI without physical camera):

```python
# conftest.py addition
import pytest, cv2

def _hw_camera_available() -> bool:
    cap = cv2.VideoCapture(0)
    ok = cap.isOpened()
    cap.release()
    return ok

hw_camera = pytest.mark.skipif(
    not _hw_camera_available(),
    reason="no physical camera attached"
)
```

Use `@hw_camera` on any test that requires real `VideoCapture.read()` output. These run locally but are skipped in CI.

### Unit Test Approach (mock VideoCapture)

The existing `test_camera_source.py` test `test_backend_open_failure_is_explicit()` already demonstrates the correct pattern:

```python
# Extending the existing pattern for platform backend selection
import sys
from unittest import mock

def test_backend_selector_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert _select_cv_backend("auto") == cv2.CAP_AVFOUNDATION

def test_backend_selector_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert _select_cv_backend("auto") == cv2.CAP_V4L2

def test_backend_selector_explicit_override(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")  # linux but explicit avfoundation wins
    assert _select_cv_backend("avfoundation") == cv2.CAP_AVFOUNDATION

def test_usb_capture_platform_backend():
    settings = CameraSettings(backend="usb", camera_index=0, cv_backend="auto")
    source = UsbVideoCaptureFrameSource(settings)
    fake_cap = mock.Mock()
    fake_cap.isOpened.return_value = True
    fake_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    fake_cap.get.return_value = 0.0
    fake_cap.set.return_value = True
    with mock.patch("block_detected.camera.cv2.VideoCapture", return_value=fake_cap) as mock_vc:
        source.start()
        frame = source.read()
        source.stop()
    assert frame.image_bgr.shape == (480, 640, 3)
    assert frame.source == "usb-opencv"
    # verify it was called with a non-V4L2 backend on macOS (or the correct one)
    call_args = mock_vc.call_args
    assert call_args is not None
```

### Sampling Rate

- **Per task commit:** `pytest tests/test_camera_source.py -q` (unit coverage of backend selector)
- **Per wave merge:** `pytest tests/ -q` (full suite including existing 50+ tests)
- **Phase gate:** Full pytest green + manual `camera_smoke.py --frames 3` on dev Mac

### Wave 0 Gaps

- [ ] `tests/test_camera_source.py` — add 4 new test functions (backend selector, override, unknown raises, mocked USB read)
- [ ] `tests/test_api_detection.py` — add `test_start_with_mocked_usb_source` (may be new file if not exists)
- [ ] `tests/test_camera_smoke_script.py` — subprocess test for smoke script (optional; can be manual)
- [ ] `tests/conftest.py` — add `hw_camera` pytest mark and `_hw_camera_available()` helper
- [ ] `config/camera.usb.mac.json` — new dev USB config (not a test file but needed for CAM-10-04)
- [ ] `pyproject.toml` — register `hw` pytest marker to avoid `PytestUnknownMarkWarning`

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| OpenCV (`cv2`) | Camera backend switching | ✓ | 4.13.0 | — |
| `cv2.CAP_AVFOUNDATION` | macOS USB capture | ✓ | constant 1200 | `CAP_ANY` |
| `cv2.CAP_V4L2` | Linux/Pi USB capture | ✓ (constant defined) | 200 (backend N/A on macOS) | `CAP_ANY` |
| AVFoundation backend | Real camera on macOS | ✓ | YES in build | — |
| Physical camera (index 0) | CAM-10-04 manual validation | ✓ (FaceTime/built-in) | macOS FaceTime | USB webcam at index 0-2 |
| macOS TCC camera permission | First run | requires manual grant | — | Grant via System Preferences |
| pytest 9.x | Unit tests | ✓ | 9.0.3 | — |

**Missing dependencies with no fallback:**
- None for CI/unit tests (all `VideoCapture` calls are mocked).

**Missing dependencies with fallback (manual validation only):**
- Physical camera: use `hw_camera` pytest mark to skip in CI.
- TCC permission: one-time manual grant before first real capture.

---

## Open Questions

1. **`lock_exposure: false` in `camera.usb.mac.json`?**
   - What we know: `CAP_PROP_AUTO_EXPOSURE` and `CAP_PROP_AUTO_WB` calls return `False` on macOS AVFoundation (non-fatal, logged to `settings_unsupported`).
   - What's unclear: Whether to set `lock_exposure: false` in the new Mac config (to avoid noise in metadata logs) or leave defaults.
   - Recommendation: Set `lock_exposure: false, lock_white_balance: false` in `camera.usb.mac.json` for a clean dev experience. On Pi, retain `true` in the existing profile.

2. **`_select_cv_backend` location: module-level or method?**
   - What we know: Could be a module-level function in `camera.py` (easier to unit test) or a private method on `UsbVideoCaptureFrameSource`.
   - Recommendation: Module-level function `_select_cv_backend(cv_backend: str) -> int` — matches existing `_normalize_bgr`, `_format_frame_id` module-level helper pattern in `camera.py`.

3. **`camera.usb.linux.json` needed?**
   - What we know: On Linux/Pi, `cv_backend="auto"` defaults to `CAP_V4L2`, which is already correct. The existing `camera.example.json` `"usb"` profile works once `cv_backend` defaults to `"auto"`.
   - Recommendation: No separate Linux file needed; document that Linux defaults are correct out of the box.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | macOS TCC permission prompt appears on first AVFoundation `VideoCapture` open | Pitfall 2 | If terminal pre-denied, `isOpened()=False` with no obvious error; requires manual TCC reset |
| A2 | `cv2.CAP_DSHOW` constant is defined on macOS cv2 install | Code Examples `_CV_BACKEND_MAP` | `AttributeError` at import; fix: use `getattr(cv2, 'CAP_DSHOW', 700)` |
| A3 | `sys.platform.startswith("linux")` covers Raspberry Pi OS | Backend selector | Pi uses `linux` prefix — well-documented, HIGH confidence this is correct [ASSUMED: standard] |
| A4 | `_frame_source.start()` called synchronously in `_run_loop` is acceptable for warmup overhead | Pitfall 3 | If warmup is slow (>500ms), API responsiveness degrades; mitigable by reducing warmup_frames |

**If A2 is wrong:** protect with `getattr(cv2, 'CAP_DSHOW', 700)` in `_CV_BACKEND_MAP`.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Local console, no auth in v1 |
| V3 Session Management | no | — |
| V4 Access Control | no | LAN/dev only |
| V5 Input Validation | yes (minor) | `cv_backend` must validate against known values before use — `ValueError` on unknown key handles this |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed `cv_backend` string in config JSON | Tampering | `_select_cv_backend` raises `ValueError` on unknown key; fails fast before `VideoCapture` call |
| Attacker-controlled `CAMERA_CONFIG` env var pointing to external path | Elevation | `load_camera_settings` reads arbitrary path — existing behavior; acceptable for local dev tool |

---

## Project Constraints (from CLAUDE.md)

- No ArUco dependency — not relevant to camera backend; constraint unchanged
- 640×480 resolution locked — `TARGET_WIDTH/HEIGHT` in `camera.py` unchanged
- `UsbVideoCaptureFrameSource` already exists — extend, do not rewrite
- Pi camera: `PiCamera2FrameSource` for CSI — Phase 10 only changes the USB path
- TFLite INT8 on Pi — no change to classifier
- GSD workflow: use `/gsd-execute-phase` for implementation

---

## Sources

### Primary (HIGH confidence)
- Direct runtime probe: `cv2.VideoCapture(0, cv2.CAP_V4L2)` → `isOpened()=False` on macOS OpenCV 4.13.0 [VERIFIED: 2026-05-31]
- Direct runtime probe: `cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)` → `isOpened()=True` on macOS [VERIFIED: 2026-05-31]
- `cv2.getBuildInformation()` → AVFoundation: YES; V4L2: absent from macOS build [VERIFIED: 2026-05-31]
- `src/block_detected/camera.py` — lines 171-173: hardcoded `cv2.CAP_V4L2` [VERIFIED: direct read]
- `backend/app/main.py` — lifespan lines 32-34: mock-only auto-start [VERIFIED: direct read]
- `tests/test_camera_source.py` — existing `mock.patch("block_detected.camera.cv2.VideoCapture")` pattern [VERIFIED: direct read]

### Secondary (MEDIUM confidence)
- [OpenCV VideoCapture docs](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html) — `apiPreference` parameter, backend constants table [CITED]
- [OpenCV VideoCaptureAPIs enum](https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html) — `CAP_V4L2=200`, `CAP_AVFOUNDATION=1200`, `CAP_ANY=0` [CITED]

### Tertiary (LOW confidence)
- macOS TCC behavior for Python/terminal camera access — standard Apple behavior, not directly tested in this session [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- Root cause (CAP_V4L2 on macOS): HIGH — directly verified by probe
- Fix approach (cv_backend field + _select_cv_backend): HIGH — follows existing CameraSettings pattern exactly
- Test strategy: HIGH — follows existing mock.patch pattern in test_camera_source.py
- TCC permission pitfall: MEDIUM — standard macOS behavior, not tested in this session

**Research date:** 2026-05-31
**Valid until:** 2026-08-31 (OpenCV 4.x backend API is stable; platform constants unchanged for years)

---

## RESEARCH COMPLETE

**Phase:** 10 - Real Camera Capture on Dev Machine (no mock — USB/Pi camera live feed)
**Confidence:** HIGH

### Key Findings
- **Root cause confirmed:** `cv2.VideoCapture(0, cv2.CAP_V4L2)` returns `isOpened()=False` on macOS — verified by direct probe. V4L2 is Linux-only; `CAP_AVFOUNDATION` is the correct macOS backend.
- **Minimal fix:** Add `cv_backend: str = "auto"` to `CameraSettings` + one module-level `_select_cv_backend()` function in `camera.py`; replace two hardcoded `cv2.CAP_V4L2` references in `UsbVideoCaptureFrameSource.start()`.
- **No changes to `main.py` or detection loop:** The "explicit START required when mock=false" behavior is already correct for Phase 9 integration.
- **Dev workflow:** `MOCK_CAMERA=` (unset) + `CAMERA_CONFIG=config/camera.usb.mac.json` → POST `/api/detection/start` → live MJPEG + WS telemetry.
- **Test strategy:** Mock `cv2.VideoCapture` using existing `test_camera_source.py` pattern; add `hw_camera` pytest mark for optional hardware tests; gate CI on mocked tests only.

### File Created
`.planning/phases/10-real-camera-capture-on-dev-machine-no-mock-usb-pi-camera-liv/10-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Root Cause | HIGH | Direct VideoCapture probe on dev machine |
| Fix Approach | HIGH | Follows existing CameraSettings + module helper patterns exactly |
| Config/Env Contract | HIGH | Traced through frame_source_factory.py and load_camera_settings() |
| Test Strategy | HIGH | Extends existing mock.patch pattern in test_camera_source.py |
| macOS TCC pitfall | MEDIUM | Standard Apple behavior; not directly probed |

### Ready for Planning
Research complete. Planner can create PLAN.md targeting `camera.py` (2 lines + 1 function + 1 field), `camera.usb.mac.json` (new file), and 4+ new unit tests.
