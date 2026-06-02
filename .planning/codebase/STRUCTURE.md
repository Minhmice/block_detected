# Codebase Structure

**Analysis Date:** 2026-06-02

## Directory Layout

```
block_detected/
├── run_yolo_webcam.py      # Webcam realtime inference + OpenCV UI
├── batch_detect_square.py  # Batch still-image inference + square boxes
├── requirements.txt        # ultralytics, opencv-python pins
├── README.md               # Setup, usage, troubleshooting (Vietnamese + English commands)
├── .gitignore              # venv, outputs, model weights, caches
├── models/                 # YOLO weights (.pt) — gitignored except .gitkeep
│   └── .gitkeep
├── images/                 # Default batch input (sample/generated PNGs may be committed)
├── images_out/             # Batch output (created at runtime; gitignored)
├── venv/                   # Local virtualenv (may exist; prefer .venv per README)
├── node_modules/           # Orphan npm bins if present — not used by Python scripts
└── .planning/
    └── codebase/           # GSD architecture/stack docs (this file)
```

## Directory Purposes

**Repository root (`block_detected/`):**
- Purpose: All runnable application code and project docs
- Contains: Two Python entry scripts, `requirements.txt`, `README.md`
- Key files: `run_yolo_webcam.py`, `batch_detect_square.py`

**`models/`:**
- Purpose: Store Ultralytics `.pt` weight files
- Contains: `*.pt` (e.g. `train-3.pt` default); `.gitkeep` preserves empty dir in git
- Key files: `models/train-3.pt` (expected at runtime; not committed per `.gitignore`)

**`images/`:**
- Purpose: Default input folder for batch detection
- Contains: Raster images (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`)
- Key files: Any images placed by user; repo may include sample PNGs

**`images_out/`:**
- Purpose: Annotated images written by `batch_detect_square.py`
- Contains: Output files mirroring input basenames
- Key files: Created on first batch run; listed in `.gitignore`

**`venv/` or `.venv/`:**
- Purpose: Python virtual environment (local only)
- Contains: `pip`-installed `ultralytics`, `torch`, `opencv-python`, etc.
- Key files: Not part of application architecture; gitignored

**`.planning/codebase/`:**
- Purpose: GSD-generated reference docs for planners/executors
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md`, and other focus-area docs
- Key files: Written by `/gsd-map-codebase`

## Key File Locations

**Entry Points:**
- `run_yolo_webcam.py`: Webcam realtime detection and interactive controls
- `batch_detect_square.py`: Directory batch processing with CLI arguments

**Configuration:**
- `run_yolo_webcam.py` (lines 8–23): `CAMERA_INDEX`, resolution, confidence bounds, overlay depth, eval conf, UI button metrics — edit file to change defaults
- `batch_detect_square.py` (`parse_args()`): CLI defaults for model, input, output, confidence, preview flag
- `requirements.txt`: Dependency versions (`ultralytics>=8.4.0`, `opencv-python>=4.8.0`)
- `.gitignore`: Ignores `images_out/`, `models/*.pt`, `venv/`, Ultralytics `runs/`, caches

**Core Logic:**
- `run_yolo_webcam.py`: `discover_model_paths`, `extract_boxes`, overlay/eval drawing, `open_camera`, `main` loop
- `batch_detect_square.py`: `draw_square_box`, `clamp`, `main` image loop

**Documentation:**
- `README.md`: Install steps, directory overview, keyboard/CLI reference, common errors

**Testing:**
- Not detected — no `tests/`, `test_*.py`, or pytest config

## Naming Conventions

**Files:**
- Snake_case script names at repo root: `run_yolo_webcam.py`, `batch_detect_square.py`
- Model weights: descriptive names with hyphens/versions, e.g. `train-3.pt`, `yolo26n.pt`
- Input images: arbitrary basename; extension must be in batch whitelist

**Functions:**
- Snake_case: `discover_model_paths`, `draw_square_box`, `parse_args`
- Private-by-convention nested handlers: `switch_model` inside `main` (webcam)

**Variables / constants:**
- Module-level config: `UPPER_SNAKE_CASE` (`BASE_DIR`, `MODELS_DIR`, `CAMERA_WIDTH`, `EVAL_CONF`)
- Locals: `snake_case` (`model_index`, `box_history`, `image_paths`)

**Directories:**
- Lowercase, short nouns: `models`, `images`, `images_out`
- No Python package namespace (no `block_detected/` import package)

## Where to Add New Code

**New inference mode (e.g. video file, RTSP stream):**
- Primary code: New top-level script at repository root, e.g. `run_yolo_video.py`, following the same `BASE_DIR` + `YOLO` + OpenCV pattern as `run_yolo_webcam.py`
- Reuse patterns from: `open_camera` / frame loop in `run_yolo_webcam.py`; path validation from `batch_detect_square.py`

**Shared detection or drawing utilities (if refactoring):**
- Implementation: New module e.g. `detection_utils.py` at root (project has no `src/` yet)
- Import from entry scripts: `from detection_utils import extract_boxes, draw_square_box`
- Until refactor exists, duplicate helpers stay inline per script — current convention

**New CLI batch option:**
- Primary code: `parse_args()` and `main()` in `batch_detect_square.py`
- Defaults: Anchor paths with `BASE_DIR / "models" / ...` like existing `--model` default

**New default model or camera setting:**
- Webcam: Edit constants at top of `run_yolo_webcam.py` (`DEFAULT_MODEL_NAME`, `CAMERA_INDEX`, etc.)
- Batch: Change `parser.add_argument("--model", default=...)` in `batch_detect_square.py`

**Tests:**
- Location: Not established — add `tests/test_batch_detect_square.py` or `tests/` package if introducing pytest; mirror script names
- Run: Would require adding `pytest` to `requirements.txt` (not present today)

**Training / export pipelines:**
- Not in repo — Ultralytics training would produce new `.pt` files into `models/` manually or via external notebooks/CLI

## Special Directories

**`models/`:**
- Purpose: Weight storage only; no training code in repo
- Generated: Weights come from external training or downloads
- Committed: Only `.gitkeep`; `*.pt` gitignored

**`images_out/`:**
- Purpose: Batch script output
- Generated: Yes — `output_dir.mkdir(parents=True, exist_ok=True)` in `batch_detect_square.py`
- Committed: No (`.gitignore`)

**`runs/`, `wandb/`:**
- Purpose: Potential Ultralytics training/logging outputs (not created by current scripts)
- Generated: If user runs training elsewhere
- Committed: No (`.gitignore`)

**`node_modules/`:**
- Purpose: Not referenced by Python project; safe to ignore for architecture work
- Generated: If npm tooling was run in this folder
- Committed: Typically no (not listed in provided `.gitignore` but unrelated to detection app)

**`.env`:**
- Not used by application code — `.gitignore` lists `.env` for safety if added later

## Import and Dependency Graph

```
run_yolo_webcam.py
  ├── stdlib: sys, collections.deque, pathlib.Path
  ├── cv2
  └── ultralytics.YOLO

batch_detect_square.py
  ├── stdlib: argparse, pathlib.Path
  ├── cv2
  └── ultralytics.YOLO
```

No cross-imports between the two scripts. Both depend only on third-party stacks declared in `requirements.txt` (Ultralytics pulls PyTorch transitively).

---

*Structure analysis: 2026-06-02*
