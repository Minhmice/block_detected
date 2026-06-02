# Technology Stack

**Analysis Date:** 2026-06-02

## Languages

**Primary:**
- Python 3.10+ — All application code; README recommends 3.11+; `requirements.txt` notes testing on 3.13; local `venv` observed on Python 3.14.4

**Secondary:**
- Not applicable — No other languages in project source

## Runtime

**Environment:**
- CPython (local virtual environment)
- README documents `.venv/` on Windows/Linux/macOS; `.gitignore` also ignores `venv/` and `env/`

**Package Manager:**
- pip (via `python -m pip`)
- Lockfile: **missing** — only `requirements.txt` with minimum version pins; no `requirements-lock.txt`, `poetry.lock`, or `Pipfile.lock`

## Frameworks

**Core:**
- Ultralytics YOLO (`ultralytics>=8.4.0`) — Object detection inference via `YOLO` class in `main.py` and `batch_detect_square.py`
- OpenCV (`opencv-python>=4.8.0`) — Webcam capture, image I/O, drawing, GUI windows (`cv2.VideoCapture`, `cv2.imread`/`imwrite`, `cv2.imshow`)

**Testing:**
- Not detected — No pytest, unittest, or other test runner configured

**Build/Dev:**
- Not detected — No `pyproject.toml`, `setup.py`, Makefile, Dockerfile, or CI pipeline
- `node_modules/` exists at project root with `concurrently` binaries but no `package.json`; not part of the Python application stack

## Key Dependencies

**Critical (direct — `requirements.txt`):**
- `ultralytics>=8.4.0` — YOLO model loading, inference (`model()`, `model.predict()`), result plotting (`result.plot()`)
- `opencv-python>=4.8.0` — Camera and image pipeline for both entry scripts

**Critical (transitive — installed with `ultralytics`):**
- `torch>=1.8.0` — Deep learning backend for inference (CPU by default; CUDA optional per README)
- `torchvision>=0.9.0` — Vision utilities used by Ultralytics/PyTorch stack
- `numpy>=1.23.0` — Array/tensor operations underlying detections
- `pillow>=7.1.2` — Image handling within Ultralytics pipeline
- `matplotlib>=3.3.0` — Plotting support in Ultralytics (not used directly by project scripts)
- `pyyaml>=5.3.1` — YAML config parsing in Ultralytics
- `scipy>=1.4.1` — Scientific computing dependency of Ultralytics
- `requests>=2.23.0` — HTTP client (Ultralytics uses for optional remote model/asset downloads; project scripts load local `.pt` files only)
- `psutil>=5.8.0` — System metrics in Ultralytics
- `polars>=0.20.0` — DataFrame operations in Ultralytics
- `ultralytics-thop>=2.0.18` — FLOPs computation in Ultralytics

**Infrastructure:**
- Not applicable — No cloud SDKs, ORMs, or deployment libraries in project code

## Configuration

**Environment:**
- No `.env` file present; `.gitignore` excludes `.env` and `.env.*` (allows `!.env.example`, but no `.env.example` exists)
- All runtime configuration is **in-script constants** or **CLI arguments** — no external config files

**In-script constants (`main.py`):**
- `MODELS_DIR` — `models/` relative to script
- `DEFAULT_MODEL_NAME` — `train-3.pt`
- `CAMERA_INDEX`, `MAX_CAMERA_INDEX`, `CAMERA_WIDTH`, `CAMERA_HEIGHT`
- `CONF_MIN`, `CONF_MAX`, `CONF_STEP`, `EVAL_CONF`, `OVERLAY_HISTORY`
- UI layout: `WINDOW_NAME`, `BUTTON_MARGIN`, `BUTTON_HEIGHT`, `BUTTON_PAD_X`

**CLI arguments (`batch_detect_square.py`):**
- `--model` (default `models/train-3.pt`)
- `--input` (default `images/`)
- `--output` (default `images_out/`)
- `--conf` (default `0.01`)
- `--show` (optional preview window)

**Build:**
- `requirements.txt` — sole dependency manifest
- `.gitignore` — Python caches, venvs, model weights, output dirs, Ultralytics artifacts

## Platform Requirements

**Development:**
- Python 3.10+ with pip
- Webcam hardware for `main.py`
- Local YOLO weights in `models/*.pt` (gitignored; `models/.gitkeep` preserves directory)
- Sample images in `images/` for batch mode (project includes sample PNGs)
- Disk space for PyTorch/Ultralytics install (README notes first install can take several minutes)
- Optional NVIDIA GPU + CUDA-compatible PyTorch for faster inference (README links to https://pytorch.org/get-started/locally/)

**Production:**
- Local/desktop execution only — scripts run as one-off CLI processes
- No server, container, or cloud deployment configuration detected
- Output written to local filesystem (`images_out/` for batch; OpenCV window for webcam)

---

*Stack analysis: 2026-06-02*
