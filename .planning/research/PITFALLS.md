# Pitfalls Research

**Domain:** Contour-based square detection + TFLite on Pi
**Researched:** 2026-05-31
**Confidence:** HIGH

## Critical Pitfalls

### 1. Wrong corner order → flipped warp

**Warning signs:** Classifier confident but wrong block; face appears mirrored in debug warp.

**Prevention:** Unit test `order_corners` on synthetic rotations; visualize warped crop in dataset script.

**Phase:** Phase 4 (Geometry & Warp)

### 2. Adaptive threshold breaks under glare

**Warning signs:** Contours fragment or merge; missing blocks at noon / LED glare.

**Prevention:** Lock exposure; try Canny vs adaptive per environment; save preprocess debug images.

**Phase:** Phase 3 (Preprocess & Contours)

### 3. Similar block colors confuse CNN

**Warning signs:** Block 2 ↔ 3 swaps under shadow.

**Prevention:** Augment training (brightness, hue jitter); collect hard negatives; per-class threshold tuning.

**Phase:** Phase 5 (Classifier)

### 4. Homography drift after camera bump

**Warning signs:** mm pose bias increases over days.

**Prevention:** Version calibration file; startup sanity check on known table point; document recal procedure.

**Phase:** Phase 6 (Pose & Calibration)

### 5. Multiple contours → wrong pick

**Warning signs:** Pallet edge detected as square; two blocks → unstable ID.

**Prevention:** Area/aspect filters; overlap IoU check; `multiple_candidates` status.

**Phase:** Phase 7 (Reject & Pipeline)

### 6. Pi thermal throttling drops FPS

**Warning signs:** Missed picks under continuous run.

**Prevention:** INT8 model; reduce debug writes in production; optional frame skip.

**Phase:** Phase 5–8

### 7. Contract mismatch with robot integrator

**Warning signs:** Robot parser expects tuple corners; Python returns nested dataclass.

**Prevention:** Use `result_to_json()`; integration test with sample payloads.

**Phase:** Phase 1 (already partially mitigated)

## Medium Pitfalls

| Pitfall | Prevention | Phase |
|---------|------------|-------|
| `approxPolyDP` epsilon too loose | Sweep epsilon on test set | 3 |
| Partial occlusion → non-quad | Convexity + corner angle checks | 3, 7 |
| Training set lacks far/near scale | Stratified capture script | 5, 8 |
| USB vs CSI color difference | Separate WB profiles in config | 2 |

## Detection Checklist (field)

- [ ] Warped face visually upright and centered
- [ ] Empty table → `no_detection`, not random class
- [ ] Rotated 45° still correct `block_id`
- [ ] Two blocks in frame → reject or stable policy documented

---
*Pitfalls research for: block_detected*
*Researched: 2026-05-31*
