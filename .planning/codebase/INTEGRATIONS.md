# External Integrations

**Analysis Date:** 2026-06-02

## APIs & External Services

**Object detection / ML:**
- Ultralytics YOLO — Local inference only in this project
  - SDK/Client: `ultralytics` Python package
  - Auth: Not applicable — loads local `.pt` weights from `models/`
  - Remote capability: Ultralytics library can download pretrained weights via HTTP when passed a model name string (e.g. `yolo26n.pt`); project scripts use explicit filesystem paths under `models/` and do not invoke remote download in normal operation

**HTTP (transitive, unused by project scripts):**
- `requests` — Pulled in by `ultralytics`; not imported directly in `run_yolo_webcam.py` or `batch_detect_square.py`

**Other external APIs:**
- Not detected — No REST clients, GraphQL, gRPC, or third-party SaaS integrations in application code

## Data Storage

**Databases:**
- None — No SQL, NoSQL, or embedded database usage

**File Storage:**
- Local filesystem only
  - **Input models:** `models/*.pt` (`.pt`, `.onnx`, `.engine` gitignored per `.gitignore`)
  - **Batch input:** `images/` — `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp` (see `batch_detect_square.py` `image_exts`)
  - **Batch output:** `images_out/` — annotated images written by `cv2.imwrite()`; directory auto-created
  - **Training artifacts (ignored, not used by inference scripts):** `runs/`, `wandb/` listed in `.gitignore` — typical Ultralytics/W&B training outputs; no training script in repo

**Caching:**
- Ultralytics cache files (`*.cache`) gitignored
- No application-level cache layer

## Authentication & Identity

**Auth Provider:**
- None — Standalone CLI/desktop scripts with no user accounts or API keys

## Monitoring & Observability

**Error Tracking:**
- None — No Sentry, Rollbar, or similar

**Logs:**
- stdout/stderr via `print()` with prefixed tags: `[INFO]`, `[WARN]`, `[ERROR]`
- Log files gitignored (`*.log`) but not written by current scripts
- No structured logging framework (no `logging` module usage)

## CI/CD & Deployment

**Hosting:**
- Not configured — Local execution on developer machine

**CI Pipeline:**
- None — No `.github/workflows/`, GitLab CI, or other pipeline configs

## Environment Configuration

**Required env vars:**
- None — Scripts do not read `os.environ` or load dotenv files

**Secrets location:**
- `.env` / `.env.*` excluded by `.gitignore` but no secrets consumed by current code
- No credential files referenced in Python source

## Hardware Integrations

**Webcam:**
- OpenCV `cv2.VideoCapture(index)` in `run_yolo_webcam.py`
  - Default index `0`; cycles `0`–`5` via `c` key or `CAMERA_INDEX` / `MAX_CAMERA_INDEX` constants
  - Resolution set via `CAP_PROP_FRAME_WIDTH` / `CAP_PROP_FRAME_HEIGHT` (default 1280×720)
  - No network/IP camera URLs — local device indices only

**GPU (optional):**
- PyTorch CUDA backend when compatible `torch` is installed (README guidance only; not configured in code)
- Device selection delegated to Ultralytics/PyTorch defaults (`model()` / `model.predict()` with no explicit `device=` argument)

## Webhooks & Callbacks

**Incoming:**
- None — No HTTP server or event listeners

**Outgoing:**
- None — No webhook posts or callback URLs in application code
- Potential indirect HTTP only through Ultralytics if using remote model names (not used by default paths in this repo)

## Third-Party Tooling (referenced but not integrated in code)

**Weights & Biases (`wandb/`):**
- Directory name in `.gitignore` suggests optional use during model training elsewhere
- No `import wandb` or W&B API calls in project Python files

**Ultralytics Hub / Docs:**
- README links to https://docs.ultralytics.com/ for framework documentation only

---

*Integration audit: 2026-06-02*
