# External Integrations

**Analysis Date:** 2026-06-02

## APIs & External Services

**Cloud / SaaS:**
- None — no HTTP clients, API keys, or third-party SaaS SDKs in `src/`

**ML inference:**
- **Ultralytics YOLO** (local library, not a remote API)
  - SDK: `ultralytics` package
  - Weights: local filesystem `models/*.pt` via `detection/yolo/loader.py`
  - Auth: not applicable

## Data Storage

**Databases:**
- None

**File Storage:**
- **Local filesystem only**
  - Input weights: `models/` (`config/paths.py` → `MODELS_DIR`)
  - Batch input images (planned): `images/` (`IMAGES_DIR`)
  - Batch output (planned): `images_out/` (`IMAGES_OUT_DIR`, gitignored)
  - Ultralytics run artifacts: `runs/`, `wandb/` (gitignored per `.gitignore`)

**Caching:**
- Ultralytics/YOLO may write `*.cache` under project (gitignored)
- No application-level Redis or disk cache module

## Authentication & Identity

**Auth Provider:**
- Not applicable — single-user local desktop app with no login

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- `print("[INFO|WARN|ERROR] ...")` pattern in `apps/webcam/app.py`, `ui/input/handlers.py`
- No `logging` module configuration

## CI/CD & Deployment

**Hosting:**
- None — not deployed as a service

**CI Pipeline:**
- None — no `.github/workflows/` or other CI config detected

## Environment Configuration

**Required env vars:**
- None — all configuration is code constants in `src/block_detected/config/`

**Secrets location:**
- `.env` and `.env.*` are gitignored (`.gitignore`) but no `.env` file exists in repo
- No secrets required for current feature set

## Webhooks & Callbacks

**Incoming:**
- OpenCV UI callbacks only: `cv2.setMouseCallback` → `ui/input/handlers.py` `on_mouse`
- Keyboard via `cv2.waitKeyEx` → `handle_key`

**Outgoing:**
- None

## Hardware Integrations

**Webcam:**
- OpenCV `cv2.VideoCapture(index)` in `io/camera/capture.py`
- Camera index cycling `0..MAX_CAMERA_INDEX` via `switch_camera`

**GPU (optional):**
- PyTorch/CUDA used indirectly through Ultralytics when user installs GPU-enabled PyTorch (documented in `README.md`, not enforced in `pyproject.toml`)

---

*Integration audit: 2026-06-02*
