---
phase: 16-relaxed-multi-block-detection-and-image-folder-viewer
plan: 01
subsystem: cv
tags: [dataset, multi-block, image-source, relaxed-detection]
requires: [15-01]
provides:
  - image_source.py for block_dataset navigation
  - Multi-block detection with score threshold
  - Arrow-key image viewer in main loop
affects: []
tech-stack:
  added: []
  patterns: [natural sort dtN.jpg, waitKeyEx arrows, MultiTracker by center]
key-files:
  created:
    - src/block_detection_v2/image_source.py
  modified:
    - src/block_detection_v2/config.py
    - src/block_detection_v2/camera.py
    - src/block_detection_v2/polygon.py
    - src/block_detection_v2/tracker.py
    - src/block_detection_v2/renderer.py
    - src/block_detection_v2/models.py
    - src/block_detection_v2/main.py
key-decisions:
  - "Default source block_dataset/ (108 images) not webcam"
  - "DETECTION_SCORE_MIN ~0.38 for looser matching"
requirements-completed: [V2-IMG-01, V2-IMG-02, V2-MULTI-01, V2-MULTI-02, V2-RELAX-01]
duration: 30min
completed: 2026-06-29
---

# Phase 16 Plan 01 Summary

**Dataset-driven dev loop on `block_dataset/` with relaxed multi-block detection and arrow navigation.**

## Tasks

1. **image_source.py** — `ImageFolder`, natural sort, `open_image_source()` → 108 images, first `dt1.jpg`
2. **Multi-block** — `find_hexagons`, `DETECTION_SCORE_MIN`, `MultiTracker`, `BlockResult.score`
3. **Main loop** — `open_image_source()`, arrow/p/n keys, `blocks[]` in frame output, colored multi-render

## Verification

- `open_image_source().count() == 108`: pass
- Multi-block synthetic → 2 blocks: pass
- `camera.py` has no `ImageFolder`: pass

## Deviations

None.
