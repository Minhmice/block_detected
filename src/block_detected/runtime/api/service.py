"""Thread-safe wrapper around WebcamEngine for HTTP handlers."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

import cv2

from block_detected.core.domain import RuntimeStatus
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_JPEG_PARAMS = [int(cv2.IMWRITE_JPEG_QUALITY), 80]


class EngineService:
    """Owns a single WebcamEngine and background frame loop (mirrors GUI FrameThread)."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._engine: WebcamEngine | None = None
        self._latest_jpeg: bytes | None = None
        self._latest_status: RuntimeStatus | None = None
        self._running = False
        self._last_error: str | None = None
        self._pending_switch_model = False
        self._pending_switch_camera = False
        self._switch_camera_result = False
        self._switch_camera_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def get_latest_jpeg(self) -> bytes | None:
        with self._lock:
            return self._latest_jpeg

    def get_status(self) -> RuntimeStatus | None:
        with self._lock:
            return self._latest_status

    def start(self) -> tuple[bool, str | None]:
        if self._running:
            return True, None

        engine, create_error = WebcamEngine.try_create(self._config)
        if engine is None:
            self._last_error = create_error
            return False, create_error

        started, start_error = engine.try_start()
        if not started:
            engine.shutdown(destroy_cv_windows=False)
            self._last_error = start_error
            return False, start_error

        self._engine = engine
        self._last_error = None
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="EngineServiceLoop", daemon=True)
        self._thread.start()
        self._running = True
        logger.info("EngineService started")
        return True, None

    def stop(self) -> None:
        if not self._running and self._thread is None:
            return

        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)

        engine = self._engine
        if engine is not None:
            engine.shutdown(destroy_cv_windows=False)

        with self._lock:
            self._latest_jpeg = None
            self._latest_status = None
            self._pending_switch_model = False
            self._pending_switch_camera = False

        self._engine = None
        self._thread = None
        self._running = False
        logger.info("EngineService stopped")

    def switch_model(self) -> None:
        with self._lock:
            self._pending_switch_model = True

    def switch_camera(self) -> bool:
        if not self._running:
            return False
        with self._lock:
            self._pending_switch_camera = True
            self._switch_camera_event.clear()
        if not self._switch_camera_event.wait(timeout=2.0):
            logger.warning("switch_camera timed out waiting for frame loop")
            return False
        with self._lock:
            return self._switch_camera_result

    def _apply_pending(self, engine: WebcamEngine) -> None:
        with self._lock:
            switch_model = self._pending_switch_model
            switch_camera = self._pending_switch_camera
            self._pending_switch_model = False
            self._pending_switch_camera = False

        if switch_model:
            engine.switch_model()
        if switch_camera:
            result = engine.switch_camera()
            with self._lock:
                self._switch_camera_result = result
            self._switch_camera_event.set()

    def _loop(self) -> None:
        engine = self._engine
        if engine is None:
            return
        try:
            while not self._stop_event.is_set():
                self._apply_pending(engine)
                processed = engine.process_frame()
                if processed is None:
                    self._last_error = "Frame loop ended (camera read failed or engine stopped)."
                    logger.warning(self._last_error)
                    break
                ok, buf = cv2.imencode(".jpg", processed.annotated, _JPEG_PARAMS)
                if ok:
                    with self._lock:
                        self._latest_jpeg = buf.tobytes()
                        self._latest_status = processed.status
                time.sleep(0.001)
        finally:
            self._running = False
