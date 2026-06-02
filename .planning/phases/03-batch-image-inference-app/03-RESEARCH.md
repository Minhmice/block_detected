# Phase 3 Research: Batch Image Inference

**Analysis Date:** 2026-06-02  
**Status:** Reused from Phase 2 expansion table — no new research pass.

## Source

- `.planning/phases/02-cv-layered-folder-structure-for-scalable-expansion/02-RESEARCH.md` — expansion roadmap row: `apps/batch/` + `io/images/`
- `AGENTS.md` — batch app location, square annotator path, dependency rules
- Git history: `batch_detect_square.py` — argparse flags and `draw_square_box` geometry

## Implementation anchors

| Concern | Module |
|---------|--------|
| Image listing | `io/images/iter_image_paths` |
| Model load | `detection/yolo/loader.py` |
| Box parse | `detection/boxes.py` |
| Square draw | `vision/drawing/square.py` (new) |
| Orchestration | `apps/batch/app.py` |
| CLI | `block-detected-batch` in pyproject.toml |

## Legacy parity

- Flags: `--model`, `--input`, `--output`, `--conf`, `--show`
- Square box: center on detection, side = max(width, height), clamp to frame
- Default paths: `models/train-3.pt`, `images/`, `images_out/`

---

*Planning reference for Phase 3 — batch image inference app*
