"""Webcam runtime engine — frame loop, inference, render, metrics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2

from block_detected.config.paths import MODELS_DIR
from block_detected.core.domain import Detection, FrameResult, RuntimeStatus
from block_detected.core.protocols import DetectorBackend
from block_detected.detection.yolo.loader import discover_model_paths, resolve_model_index
from block_detected.runtime.config_store import save_config
from block_detected.runtime.detector_loader import load_detector
from block_detected.runtime.platform import is_raspberry_pi
from block_detected.io.camera.capture import open_camera, switch_camera
from block_detected.runtime.config_schema import AppConfig, CameraConfig
from block_detected.runtime.metrics import RuntimeMetrics
from block_detected.runtime.logging_setup import log_event
from block_detected.runtime.postprocess import DetectionPostProcessor
from block_detected.runtime.preprocess import apply_preprocess
from block_detected.runtime.state import RuntimeState
from block_detected.vision.drawing.detections import (
    draw_detection_boxes,
    draw_detection_centers,
    draw_camera_center,
)
from block_detected.vision.geometry import box_center
from block_detected.vision.drawing.eval import draw_eval_boxes
from block_detected.vision.drawing.overlays import draw_contours_overlay, draw_corners_overlay
from block_detected.vision.drawing.widgets import draw_model_switch_button, draw_status_bar

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProcessedFrame:
    annotated: Any
    button_rect: tuple[int, int, int, int]
    status: RuntimeStatus
    detections: list[Detection]


class WebcamEngine:
    def __init__(
        self,
        config: AppConfig,
        model_paths: list[Path],
        detector: DetectorBackend,
    ) -> None:
        self.config = config
        self.model_paths = model_paths
        self._detector = detector
        self.state = RuntimeState(
            confidence=config.inference.default_conf,
            camera_index=config.camera.index,
            model_index=resolve_model_index(model_paths, config.inference.last_model_name),
        )
        self.metrics = RuntimeMetrics()
        self._postprocess = DetectionPostProcessor(config.stability)
        self._cap: cv2.VideoCapture | None = None
        self._camera_source: int | str = 0
        self._last_primary_log: tuple[str, float] | None = None

    @classmethod
    def try_create(cls, config: AppConfig) -> tuple[WebcamEngine | None, str | None]:
        model_paths = discover_model_paths()
        if not model_paths:
            message = (
                f"No .pt models found in {MODELS_DIR}. "
                "Add a YOLO weights file (e.g. train-3.pt) and restart."
            )
            logger.error(message)
            return None, message

        model_index = resolve_model_index(model_paths, config.inference.last_model_name)
        model_path = model_paths[model_index]
        try:
            detector = load_detector(model_path)
        except Exception as exc:
            message = f"Failed to load model {model_path.name}: {exc}"
            logger.error(message)
            return None, message

        engine = cls(config, model_paths, detector)
        engine.state.model_index = model_index
        logger.info(
            "Loaded model (%s/%s): %s",
            model_index + 1,
            len(model_paths),
            model_path.name,
        )
        log_event("INIT", f"Loading model {model_path.name}...")
        log_event("OK", "Model loaded successfully.")
        return engine, None

    @classmethod
    def create(cls, config: AppConfig) -> WebcamEngine | None:
        engine, _error = cls.try_create(config)
        return engine

    @staticmethod
    def _resolve_pi_source(cam: CameraConfig) -> int | str:
        """Decide Pi camera source from config — no interactive prompt."""
        if cam.source == "usb":
            logger.info("Pi config: camera.source=usb — using USB webcam index %s", cam.index)
            return cam.index
        if cam.source == "libcamera":
            logger.info("Pi config: camera.source=libcamera — using Pi Camera Module (CSI)")
            return "libcamera"
        # "auto": try libcamera first, fallback handled in try_start
        logger.info("Pi config: camera.source=auto — trying libcamera first")
        return "libcamera"

    def try_start(self) -> tuple[bool, str | None]:
        cam = self.config.camera
        if is_raspberry_pi():
            self._camera_source = self._resolve_pi_source(cam)
        else:
            self._camera_source = self.state.camera_index

        self._cap = open_camera(
            self._camera_source,
            width=cam.width,
            height=cam.height,
        )

        # "auto" fallback on Pi: if libcamera failed, try USB webcam
        if self._cap is None and is_raspberry_pi() and cam.source == "auto":
            logger.info("libcamera failed — falling back to USB camera index %s", self.state.camera_index)
            self._camera_source = self.state.camera_index
            self._cap = open_camera(
                self._camera_source,
                width=cam.width,
                height=cam.height,
            )

        if self._cap is None:
            message = (
                f"Failed to open camera source {self._camera_source} "
                f"({cam.width}x{cam.height}). "
                "Check permissions, USB connection, or another app using the camera."
            )
            logger.error(message)
            return False, message
        logger.info("Opened camera source: %s", self._camera_source)
        log_event("CAM", f"Camera {self._camera_source} acquired.")
        logger.info(
            "Available models (%s): %s",
            len(self.model_paths),
            ", ".join(p.name for p in self.model_paths),
        )
        return True, None

    def start(self) -> bool:
        ok, _error = self.try_start()
        return ok

    @property
    def detector(self) -> DetectorBackend:
        return self._detector

    def switch_model(self) -> None:
        next_index = (self.state.model_index + 1) % len(self.model_paths)
        model_path = self.model_paths[next_index]
        try:
            next_detector = load_detector(model_path)
            previous_detector = self._detector
            self._detector = next_detector
            self.state.model_index = next_index
            self._postprocess.reset()
            try:
                previous_detector.close()
            except Exception as exc:
                logger.warning("Failed to close previous model cleanly: %s", exc)
            logger.info(
                "Switched model (%s/%s): %s",
                next_index + 1,
                len(self.model_paths),
                model_path.name,
            )
            log_event("OK", f"Model switched to {model_path.name}.")
            self.config.inference.last_model_name = model_path.name
            try:
                save_config(self.config)
            except OSError as exc:
                logger.warning("Failed to persist last_model_name: %s", exc)
        except Exception as exc:
            logger.error("Failed to load model %s: %s", model_path.name, exc)

    def switch_camera(self) -> bool:
        if self._cap is None:
            return False
        if isinstance(self._camera_source, str):
            logger.warning("Cannot switch camera — Pi Camera Module is the only CSI source.")
            return False
        cam = self.config.camera
        self._cap, new_index, switched = switch_camera(
            self._cap,
            self.state.camera_index,
            max_index=cam.max_index,
            width=cam.width,
            height=cam.height,
        )
        if switched:
            self.state.camera_index = new_index
            self._camera_source = new_index
            logger.info("Switched to camera source: %s", new_index)
            log_event("CAM", f"Camera {new_index} acquired.")
        else:
            logger.warning("No other camera source available to switch.")
        return switched

    def process_frame(self) -> ProcessedFrame | None:
        if self._cap is None:
            return None

        frame_start = self.metrics.begin_frame()
        ok, frame = self._cap.read()
        read_end = perf_counter()
        if not ok or frame is None:
            logger.warning("Camera frame read failed. Stopping inference loop.")
            return None

        pp = self.config.preprocess
        cl = self.config.classical
        frame = apply_preprocess(
            frame,
            contrast=pp.contrast,
            brightness=pp.brightness,
            saturation=pp.saturation,
            blur_kernel=cl.blur_kernel,
        )

        inf = self.config.inference
        active_conf = inf.eval_conf if self.state.eval_mode else self.state.confidence

        try:
            frame_result = self._detector.predict(
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
            return None

        frame_h, frame_w = frame.shape[:2]
        filtered = self._postprocess.process(
            frame_result.detections,
            frame_width=frame_w,
            frame_height=frame_h,
        )
        frame_result = FrameResult(detections=filtered, raw=frame_result.raw)

        infer_end = perf_counter()
        annotated = self._render(frame, frame_result)
        render_end = perf_counter()

        stats = self.metrics.record(
            frame_start=frame_start,
            read_end=read_end,
            infer_end=infer_end,
            render_end=render_end,
            model_name=self._detector.model_name,
            camera_index=self.state.camera_index,
        )

        ui = self.config.ui
        button_rect = draw_model_switch_button(
            annotated,
            self._detector.model_name,
            button_margin=ui.button_margin,
            button_height=ui.button_height,
            button_pad_x=ui.button_pad_x,
        )
        sorted_detections = sorted(
            frame_result.detections,
            key=lambda d: d.confidence,
            reverse=True,
        )
        ui_cap = min(8, self.config.inference.max_det)
        top_detections = sorted_detections[:ui_cap]
        primary = top_detections[0] if top_detections else None
        if primary is not None:
            key = (primary.class_name, round(primary.confidence, 3))
            if getattr(self, "_last_primary_log", None) != key:
                self._last_primary_log = key
                log_event(
                    "DET",
                    f"Found {primary.class_name.upper()} (conf: {primary.confidence:.2f})",
                )

        primary_center_px = box_center(primary.box) if primary is not None else None
        camera_center_px = (frame.shape[1] // 2, frame.shape[0] // 2)

        status = RuntimeStatus(
            eval_mode=self.state.eval_mode,
            confidence=self.state.confidence,
            model_name=self._detector.model_name,
            camera_index=self.state.camera_index,
            stability_enabled=self.config.stability.enabled,
            detection_count=len(frame_result.detections),
            primary_detection=primary,
            detections=top_detections,
            stats=stats,
            primary_center_px=primary_center_px,
            camera_center_px=camera_center_px,
        )
        return ProcessedFrame(
            annotated=annotated,
            button_rect=button_rect,
            status=status,
            detections=list(frame_result.detections),
        )

    def _render(self, frame, frame_result: FrameResult) -> Any:
        inf = self.config.inference
        stability_on = self.config.stability.enabled
        if self.state.eval_mode:
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

        # Draw detection centers with XYWH coordinates (red)
        draw_detection_centers(annotated, frame_result.detections, color=(0, 0, 255))

        # Draw camera center (purple/magenta)
        draw_camera_center(annotated)

        draw_status_bar(
            annotated,
            eval_mode=self.state.eval_mode,
            conf=self.state.confidence,
            eval_conf=inf.eval_conf,
            model_name=self._detector.model_name,
        )

        cl = self.config.classical
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

    def apply_hot_config(self, config: AppConfig) -> None:
        """Apply fields that do not require camera/detector restart."""
        self.config = config
        self._postprocess.update_config(config.stability)

    def shutdown(self, *, destroy_cv_windows: bool = True) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._detector.close()
        if destroy_cv_windows:
            cv2.destroyAllWindows()
            logger.info("Camera released and windows destroyed.")
        else:
            logger.info("Camera released.")
