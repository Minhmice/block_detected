"""Webcam runtime engine — facade over session, frame loop, and model switching."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2

from block_detected.config.paths import MODELS_DIR
from block_detected.config.schema import AppConfig
from block_detected.config.store import save_config
from block_detected.core.domain import Detection, RuntimeStatus
from block_detected.core.protocols import DetectorBackend
from block_detected.detection.yolo.loader import discover_model_paths, resolve_model_index
from block_detected.io.camera.capture import PiCameraCapture, RpicamCapture
from block_detected.runtime.detector_loader import load_detector
from block_detected.runtime.frame_loop import process_single_frame
from block_detected.runtime.logging_setup import log_event
from block_detected.runtime.metrics import RuntimeMetrics
from block_detected.runtime.postprocess import DetectionPostProcessor
from block_detected.runtime.session import try_open_camera, try_switch_camera
from block_detected.runtime.state import RuntimeState

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
        self._cap: cv2.VideoCapture | PiCameraCapture | RpicamCapture | None = None
        self._camera_source: int | str = 0
        self._last_primary_log: tuple[str, float] | None = None
        self.last_process_error: str | None = None

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

    def try_start(self) -> tuple[bool, str | None]:
        cap, source, error = try_open_camera(self.config, self.state)
        if error is not None:
            return False, error
        self._cap = cap
        self._camera_source = source
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
        self._cap, self._camera_source, switched = try_switch_camera(
            self._cap,
            self._camera_source,
            self.config,
            self.state,
        )
        return switched

    def process_frame(self) -> ProcessedFrame | None:
        if self._cap is None:
            self.last_process_error = "Camera is not open."
            return None
        errors: list[str] = []
        result = process_single_frame(
            self._cap,
            config=self.config,
            state=self.state,
            detector=self._detector,
            metrics=self.metrics,
            postprocess=self._postprocess,
            last_primary_log=self._last_primary_log,
            error_out=errors,
        )
        if result is None:
            self.last_process_error = errors[-1] if errors else "Frame processing failed."
            return None
        self.last_process_error = None
        annotated, button_rect, status, detections, self._last_primary_log = result
        return ProcessedFrame(
            annotated=annotated,
            button_rect=button_rect,
            status=status,
            detections=detections,
        )

    def apply_hot_config(self, config: AppConfig) -> None:
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
