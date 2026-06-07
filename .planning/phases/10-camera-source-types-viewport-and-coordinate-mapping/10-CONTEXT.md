# Phase 10: Camera source types viewport and coordinate mapping - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
cameraSource enum (USB/OBS/Pi stub), fpsTarget, exposure/WB lock, ViewportConfig with objectFit and coordDebug for web overlays.

</domain>

<decisions>
- CameraSource enum in config; adapter pattern in io/camera/
- ViewportConfig: frame vs viewport dims, objectFit contain, coordDebug scale/offset
- map_frame_to_viewport() in vision/geometry.py

</decisions>

<code_context>
- io/camera/capture.py, config_schema CameraConfig, runtime/api/

</code_context>

<deferred>Pi libcamera full impl — stub OK</deferred>
