"""Frame annotation rendering."""

from __future__ import annotations

from typing import Any

from block_detected.config.schema import AppConfig
from block_detected.core.domain import FrameResult
from block_detected.core.protocols import DetectorBackend
from block_detected.runtime.state import RuntimeState
from block_detected.vision.drawing.detections import (
    draw_detection_boxes,
    draw_detection_centers,
    draw_camera_center,
)
from block_detected.vision.drawing.eval import draw_eval_boxes
from block_detected.vision.drawing.overlays import draw_contours_overlay, draw_corners_overlay
from block_detected.vision.drawing.widgets import draw_status_bar


def render_frame(
    frame,
    frame_result: FrameResult,
    *,
    config: AppConfig,
    state: RuntimeState,
    detector: DetectorBackend,
) -> Any:
    inf = config.inference
    stability_on = config.stability.enabled
    if state.eval_mode:
        annotated = frame.copy()
        if stability_on:
            draw_detection_boxes(
                annotated,
                frame_result.detections,
                color=(0, 220, 255),
            )
        else:
            draw_eval_boxes(annotated, frame_result.raw)
    elif stability_on:
        annotated = frame.copy()
        draw_detection_boxes(annotated, frame_result.detections)
    else:
        annotated = frame_result.raw.plot()

    draw_detection_centers(annotated, frame_result.detections, color=(0, 0, 255))
    draw_camera_center(annotated)
    draw_status_bar(
        annotated,
        eval_mode=state.eval_mode,
        conf=state.confidence,
        eval_conf=inf.eval_conf,
        model_name=detector.model_name,
    )

    cl = config.classical
    if cl.show_contours:
        draw_contours_overlay(
            annotated,
            blur_kernel=cl.blur_kernel,
            canny_low=cl.canny_low,
            canny_high=cl.canny_high,
        )
    if cl.show_corners:
        draw_corners_overlay(annotated)

    return annotated
