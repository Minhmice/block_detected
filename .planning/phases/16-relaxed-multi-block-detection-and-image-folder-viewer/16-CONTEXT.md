# Phase 16: Relaxed multi-block + image folder viewer — Context

**Gathered:** 2026-06-29
**Status:** Ready for planning
**Source:** User iteration on phase 15 scaffold

<domain>
## Phase Boundary

Extend `block_detection_v2` for dataset-driven dev: relaxed detection score, multiple hexagons per frame, dedicated `image_source.py` reading `block_dataset/`, arrow-key navigation. `main.py` defaults to images not camera.
</domain>

<decisions>
## Implementation Decisions

### Image source (D-01)
- Separate `image_source.py` — not mixed into `camera.py`
- Default folder: `src/block_detection_v2/block_dataset/`
- Natural sort `dt1.jpg` … `dt108.jpg`

### Navigation (D-02)
- Left arrow / `p` = previous image
- Right arrow / `n` / space = next image
- ESC quit; overlay shows `[index/total] filename`

### Multi-block (D-03)
- `find_hexagons()` returns up to `MAX_BLOCKS` non-overlapping detections
- `MultiTracker` matches by center distance
- Renderer cycles colors per block; output includes `blocks[]` array

### Relaxed detection (D-04)
- `DETECTION_SCORE_MIN` + lower `MIN_CONTOUR_AREA` / higher `CONVEXITY_TOLERANCE`
- Score blends convexity, face area ratio, row separation

### Claude's Discretion
- Exact threshold values in `config.py`
</decisions>

<canonical_refs>
## Canonical References

- `src/block_detection_v2/image_source.py`
- `src/block_detection_v2/block_dataset/` (108 jpg)
- Phase 15 module files as base
</canonical_refs>

---

*Phase: 16-relaxed-multi-block-detection-and-image-folder-viewer*
