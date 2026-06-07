# Phase 8: YOLO inference params expansion and hot-reload API - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
Extend InferenceConfig + YoloDetector.predict() for imgsz, iou, max_det, device; expose conf/IoU hot-reload via web API (Phase 7 server).

</domain>

<decisions>
## Implementation Decisions

- Extend config_schema InferenceConfig with imgsz=640, iou=0.45, max_det=10, device auto
- Pass params to Ultralytics predict(); add to HOT reload keys where safe
- REST PATCH /api/config/inference for conf + iou
- class_names optional override in config when model lacks embedded names

### Claude's Discretion
ONNX backend stub optional — defer full implementation unless trivial

</decisions>

<code_context>
- detection/yolo/backend.py, runtime/config_schema.py, runtime/api/ (Phase 7)
- BACKEND_GAP_ANALYSIS.md §2

</code_context>

<deferred>ONNX full backend — future phase</deferred>
