"""Webcam runtime engine — frame loop, inference, render, metrics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2

from block_detected.config.paths import MODELS_DIR
from block_detected.core.domain import RuntimeStatus
from block_detected.core.protocols import DetectorBackend
from block_detected.runtime.detector_loader import load_detector
from block_detected.detection.yolo.loader import default_model_index, discover_model_paths
from block_detected.io.camera.capture import open_camera, switch_camera
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.metrics import RuntimeMetrics
from block_detected.runtime.state import RuntimeState
from block_detected.vision.drawing.eval import draw_eval_boxes
from block_detected.vision.drawing.overlays import draw_overlay_history
from block_detected.vision.drawing.widgets import draw_model_switch_button, draw_status_bar

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProcessedFrame:
    annotated: Any
    button_rect: tuple[int, int, int, int]
    status: RuntimeStatus


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
            model_index=default_model_index(model_paths, config.inference.default_model_name),
        )
        self.state.reset_overlay_history(config.inference.overlay_history)
        self.metrics = RuntimeMetrics()
        self._cap: cv2.VideoCapture | None = None

    @classmethod
    def create(cls, config: AppConfig) -> WebcamEngine | None:
        model_paths = discover_model_paths()
        if not model_paths:
            logger.error("No .pt models found in: %s", MODELS_DIR)
            return None

        model_index = default_model_index(model_paths, config.inference.default_model_name)
        model_path = model_paths[model_index]
        try:
            detector = load_detector(model_path)
        except Exception as exc:
            logger.error("Failed to load model %s: %s", model_path.name, exc)
            return None

        engine = cls(config, model_paths, detector)
        engine.state.model_index = model_index
        logger.info(
            "Loaded model (%s/%s): %s",
            model_index + 1,
            len(model_paths),
            model_path.name,
        )
        return engine

    def start(self) -> bool:
        cam = self.config.camera
        self._cap = open_camera(
            self.state.camera_index,
            width=cam.width,
            height=cam.height,
        )
        if self._cap is None:
            logger.error("Failed to open webcam source: %s", self.state.camera_index)
            return False
        logger.info("Opened webcam source: %s", self.state.camera_index)
        logger.info(
            "Available models (%s): %s",
            len(self.model_paths),
            ", ".join(p.name for p in self.model_paths),
        )
        return True

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
            self.state.box_history.clear()
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
        except Exception as exc:
            logger.error("Failed to load model %s: %s", model_path.name, exc)

    def switch_camera(self) -> bool:
        if self._cap is None:
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
            logger.info("Switched to webcam source: %s", new_index)
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

        inf = self.config.inference
        active_conf = inf.eval_conf if self.state.eval_mode else self.state.confidence

        try:
            frame_result = self._detector.predict(frame, conf=active_conf)
        except Exception as exc:
            logger.error("Inference failed: %s", exc)
            return None

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
        status = RuntimeStatus(
            eval_mode=self.state.eval_mode,
            overlay_enabled=self.state.overlay_enabled,
            confidence=self.state.confidence,
            model_name=self._detector.model_name,
            camera_index=self.state.camera_index,
            stats=stats,
        )
        return ProcessedFrame(annotated=annotated, button_rect=button_rect, status=status)

    def _render(self, frame, frame_result) -> Any:
        inf = self.config.inference
        if self.state.eval_mode:
            annotated = frame.copy()
            draw_eval_boxes(annotated, frame_result.raw)
            self.state.box_history.clear()
        else:
            annotated = frame_result.raw.plot()
            if self.state.overlay_enabled:
                from block_detected.detection.boxes import boxes_from_detections

                self.state.box_history.append(boxes_from_detections(frame_result.detections))
                draw_overlay_history(annotated, list(self.state.box_history))
            else:
                self.state.box_history.clear()

        draw_status_bar(
            annotated,
            eval_mode=self.state.eval_mode,
            conf=self.state.confidence,
            eval_conf=inf.eval_conf,
            overlay_enabled=self.state.overlay_enabled,
            model_name=self._detector.model_name,
            stats=self.metrics.last_stats if self.config.ui.show_fps_in_status else None,
        )
        return annotated

    def apply_hot_config(self, config: AppConfig) -> None:
        """Apply fields that do not require camera/detector restart."""
        self.config = config
        self.state.set_overlay_maxlen(config.inference.overlay_history)

    def shutdown(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._detector.close()
        cv2.destroyAllWindows()
        logger.info("Camera released and windows destroyed.")
