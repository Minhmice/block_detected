# Features Research

**Domain:** Robot pick-and-place block detection (fiducial-free)
**Researched:** 2026-05-31
**Confidence:** HIGH

## Table Stakes (must have for v1)

| Feature | Complexity | Notes |
|---------|------------|-------|
| Fixed-res capture 640×480 | Low | Foundation for all geometry |
| Preprocess (gray, blur, threshold, morphology) | Medium | Tuning-heavy; environment-specific |
| Square contour detection | Medium | Core differentiator vs bbox detectors |
| Corner ordering TL→BR | Medium | Bugs here break warp and angle |
| Perspective warp to canonical face | Medium | Enables classifier invariance |
| 4-class identity | Medium | CNN default path |
| Center + angle in pixels | Low | Derived from ordered corners |
| Confidence + reject reasons | Medium | Robot safety |
| Debug frame persistence | Low | Essential for field tuning |
| Output contract validation | Low | **Already partially shipped** in `detection_contract.py` |

## Differentiators (competitive / quality)

| Feature | Complexity | Notes |
|---------|------------|-------|
| TFLite INT8 on Pi | Medium | Latency + power vs float |
| Table homography → mm pickup pose | High | Requires calibration discipline |
| Rich status enum (`multiple_candidates`, etc.) | Low | Already in contract |
| Offline eval harness with labeled set | Medium | Proves pick reliability |

## Anti-Features (deliberately NOT build)

| Anti-feature | Why avoid |
|--------------|-----------|
| ArUco on blocks | User constraint; changes block hardware |
| YOLO-only | Insufficient corner geometry for grasp |
| Template matching primary | Scale/light/view fragile |
| End-to-end giant model | Hard to debug on Pi; overkill for 4 classes |
| Detect-all-blocks planner | v2; v1 needs deterministic single pick |

## Feature Dependencies

```
CAM capture → preprocess → contours → order corners → warp → classify → pose → reject gate → DetectionResult
                ↑______________________________|
                     debug overlays at each stage
```

## v1 vs v2 Split

**v1:** Full pipeline through reject logic + dataset eval; `pickup_pose` when calibration files exist.

**v2:** Template fallback, multi-block ranking, temporal tracking, tuning UI.

---
*Features research for: block_detected*
*Researched: 2026-05-31*
