# Phase 16 Research — multi-block + image folder

**Researched:** 2026-06-29

## Multi-block

- Collect all valid 6-gon candidates per contour set (RETR_EXTERNAL then RETR_LIST)
- Sort by `detection.score`; greedy pick with `MIN_BLOCK_CENTER_DIST` NMS on centers
- `MultiTracker`: greedy nearest-center assignment per frame

## Image folder

- `ImageFolder` class: `open`, `read`, `next_image`, `prev_image`, `current_name`, `count`
- `waitKeyEx` for arrow keys; fallback `waitKey` on older OpenCV builds

## Dataset

- `block_dataset/` — 108 real block photos for manual UAT
- Config `IMAGE_DIR` points to package-relative `block_dataset`

## Validation

- `open_image_source()` returns 108 images
- Navigate dt1 → dt2 with natural sort
- Multi-block synthetic: 2 blocks detected
