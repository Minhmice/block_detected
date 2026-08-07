"""Single-frame read → infer → postprocess → render."""

from __future__ import annotations

import logging
from time import perf_counter

import cv2

from block_detected.config.schema import AppConfig
from block_detected.core.domain import Detection, FrameResult, RuntimeStatus
from block_detected.core.protocols import DetectorBackend
from block_detected.io.camera.capture import PiCameraCapture, RpicamCapture
from block_detected.runtime.logging_setup import log_event
from block_detected.runtime.metrics import RuntimeMetrics
from block_detected.runtime.postprocess import DetectionPostProcessor
from block_detected.runtime.preprocess import apply_preprocess
from block_detected.runtime.render import render_frame
from block_detected.runtime.state import RuntimeState
from block_detected.vision.drawing.widgets import draw_model_switch_button
from block_detected.vision.geometry import box_center

logger = logging.getLogger(__name__)


def process_single_frame(
    cap: cv2.VideoCapture | PiCameraCapture | RpicamCapture,
    *,
    config: AppConfig,
    state: RuntimeState,
    detector: DetectorBackend,
    metrics: RuntimeMetrics,
    postprocess: DetectionPostProcessor,
    last_primary_log: tuple[str, float] | None,
    error_out: list[str] | None = None,
) -> tuple[object, tuple[int, int, int, int], RuntimeStatus, list[Detection], tuple[str, float] | None] | None:
    frame_start = metrics.begin_frame()
    ok, frame = False, None
    for attempt in range(3):
        ok, frame = cap.read()
        if ok and frame is not None:
            break
        if attempt < 2:
            logger.debug("Camera read retry %s/3", attempt + 1)
    read_end = perf_counter()
    if not ok or frame is None:
        logger.warning("Camera frame read failed. Stopping inference loop.")
        if error_out is not None:
            error_out.append("Camera frame read failed. Try another index (C) or run --probe-cameras.")
        return None

    pp = config.preprocess
    cl = config.classical
    frame = apply_preprocess(
        frame,
        contrast=pp.contrast,
        brightness=pp.brightness,
        saturation=pp.saturation,
        blur_kernel=cl.blur_kernel,
    )

    inf = config.inference
    active_conf = inf.eval_conf if state.eval_mode else state.confidence

    try:
        frame_result = detector.predict(
            frame,
            conf=active_conf,
            iou=inf.iou,
            imgsz=inf.imgsz,
            max_det=inf.max_det,
            agnostic_nms=inf.agnostic_nms,
        )
    except Exception as exc:
        logger.error("Inference failed: %s", exc)
        log_event("ERR", f"Inference failed: {exc}")
        if error_out is not None:
            error_out.append(f"Inference failed: {exc}")
        return None

    frame_h, frame_w = frame.shape[:2]
    filtered = postprocess.process(
        frame_result.detections,
        frame_width=frame_w,
        frame_height=frame_h,
    )
    frame_result = FrameResult(detections=filtered, raw=frame_result.raw)

    infer_end = perf_counter()
    annotated = render_frame(
        frame,
        frame_result,
        config=config,
        state=state,
        detector=detector,
    )
    render_end = perf_counter()

    stats = metrics.record(
        frame_start=frame_start,
        read_end=read_end,
        infer_end=infer_end,
        render_end=render_end,
        model_name=detector.model_name,
        camera_index=state.camera_index,
    )

    ui = config.ui
    button_rect = draw_model_switch_button(
        annotated,
        detector.model_name,
        button_margin=ui.button_margin,
        button_height=ui.button_height,
        button_pad_x=ui.button_pad_x,
    )
    sorted_detections = sorted(
        frame_result.detections,
        key=lambda d: d.confidence,
        reverse=True,
    )
    ui_cap = min(8, config.inference.max_det)
    top_detections = sorted_detections[:ui_cap]
    primary = top_detections[0] if top_detections else None
    if primary is not None:
        key = (primary.class_name, round(primary.confidence, 3))
        if last_primary_log != key:
            last_primary_log = key
            log_event(
                "DET",
                f"Found {primary.class_name.upper()} (conf: {primary.confidence:.2f})",
            )

    primary_center_px = box_center(primary.box) if primary is not None else None
    camera_center_px = (frame.shape[1] // 2, frame.shape[0] // 2)

    status = RuntimeStatus(
        eval_mode=state.eval_mode,
        confidence=state.confidence,
        model_name=detector.model_name,
        camera_index=state.camera_index,
        stability_enabled=config.stability.enabled,
        detection_count=len(frame_result.detections),
        primary_detection=primary,
        detections=top_detections,
        stats=stats,
        primary_center_px=primary_center_px,
        camera_center_px=camera_center_px,
    )
    return annotated, button_rect, status, list(frame_result.detections), last_primary_log
