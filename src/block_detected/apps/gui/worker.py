"""Background frame worker for PySide6 GUI."""

from __future__ import annotations

import copy
import threading
from typing import TYPE_CHECKING

from block_detected.runtime.config_apply import apply_hot_runtime_settings
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine

if TYPE_CHECKING:
    from PySide6 import QtCore


def create_frame_thread(qt_core: type) -> type:
    """Build FrameThread bound to the given QtCore module (lazy PySide6 import)."""

    class FrameThread(qt_core.QThread):
        frame_ready = qt_core.Signal(object, object)
        error = qt_core.Signal(str)

        def __init__(self, config: AppConfig, generation: int) -> None:
            super().__init__()
            self.generation = generation
            self._config = copy.deepcopy(config)
            self._stop = threading.Event()
            self._lock = threading.Lock()
            self._pending_conf: float | None = None
            self._pending_eval: bool | None = None
            self._pending_hot_config: AppConfig | None = None
            self._switch_model_requested = False
            self._switch_camera_requested = False

        def run(self) -> None:
            engine, create_error = WebcamEngine.try_create(self._config)
            if engine is None:
                self.error.emit(create_error or "Failed to create webcam engine.")
                return
            started, start_error = engine.try_start()
            if not started:
                self.error.emit(start_error or "Failed to open camera source.")
                engine.shutdown(destroy_cv_windows=False)
                return

            try:
                while not self._stop.is_set():
                    self._apply_pending(engine)
                    processed = engine.process_frame()
                    if processed is None:
                        break
                    self.frame_ready.emit(processed.annotated, processed.status)
                    self.msleep(1)
            finally:
                engine.shutdown(destroy_cv_windows=False)

        def stop(self) -> None:
            self._stop.set()

        def set_confidence(self, value: float) -> None:
            with self._lock:
                self._pending_conf = value

        def set_eval_mode(self, value: bool) -> None:
            with self._lock:
                self._pending_eval = value

        def apply_hot_config(self, config: AppConfig) -> None:
            with self._lock:
                self._pending_hot_config = copy.deepcopy(config)

        def request_switch_model(self) -> None:
            with self._lock:
                self._switch_model_requested = True

        def request_switch_camera(self) -> None:
            with self._lock:
                self._switch_camera_requested = True

        def _apply_pending(self, engine: WebcamEngine) -> None:
            with self._lock:
                conf = self._pending_conf
                eval_mode = self._pending_eval
                hot_config = self._pending_hot_config
                switch_model_requested = self._switch_model_requested
                switch_camera_requested = self._switch_camera_requested
                self._pending_conf = None
                self._pending_eval = None
                self._pending_hot_config = None
                self._switch_model_requested = False
                self._switch_camera_requested = False

            if hot_config is not None or conf is not None or eval_mode is not None:
                apply_hot_runtime_settings(
                    engine,
                    hot_config if hot_config is not None else engine.config,
                    confidence=conf if conf is not None else engine.state.confidence,
                    eval_mode=eval_mode if eval_mode is not None else engine.state.eval_mode,
                )
            if switch_model_requested:
                engine.switch_model()
            if switch_camera_requested:
                engine.switch_camera()

    return FrameThread
