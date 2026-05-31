"""Single-owner detection loop: capture → detect_block → publish."""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

from block_detected.classifier import ClassifierSettings
from block_detected.detector import DetectorSettings
from block_detected.pipeline import PipelineSettings
from block_detected.preprocess import PreprocessSettings
from block_detected.vision import VisionSettings

from app.schemas.wire import DetectionParamsWire
from app.services.param_utils import coerce_odd_kernel
from app.services.edge_impulse_runner import ei_runner_service
from app.services.eim_model import is_vision_mock_mode
from app.services.frame_source_factory import create_frame_source_from_env
from app.services import vision_mock
from app.services.wire_builder import build_telemetry_from_contract
from app.ws.manager import ConnectionManager

_REPO_ROOT = Path(__file__).resolve().parents[3]


class DetectionLoopService:
    def __init__(self, ws_manager: ConnectionManager) -> None:
        self._ws = ws_manager
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._latest_jpeg: Optional[bytes] = None
        self._latest_telemetry: dict[str, Any] = {}
        self._frame_source = None
        self._settings = PipelineSettings()
        self._load_vision_config()

    @property
    def running(self) -> bool:
        return self._running

    def _load_vision_config(self) -> None:
        config_path = os.getenv("VISION_CONFIG", "config/vision.example.json")
        path = Path(config_path)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        preprocess = data.get("preprocess", {})
        detector = data.get("detector", {})
        blur = preprocess.get("blur_kernel", [5, 5])
        self._settings = PipelineSettings(
            vision=VisionSettings(
                preprocess=PreprocessSettings(
                    blur_kernel=(int(blur[0]), int(blur[1])),
                    adaptive_block_size=int(preprocess.get("adaptive_block_size", 31)),
                    adaptive_c=int(preprocess.get("adaptive_c", 5)),
                    canny_low=int(preprocess.get("canny_low", 50)),
                    canny_high=int(preprocess.get("canny_high", 150)),
                ),
                detector=DetectorSettings(
                    min_area_px=float(detector.get("min_area_px", 1000)),
                    max_area_px=float(detector.get("max_area_px", 80000)),
                    aspect_min=float(detector.get("aspect_min", 0.75)),
                    aspect_max=float(detector.get("aspect_max", 1.33)),
                ),
            ),
            min_face_area_px=float(detector.get("min_area_px", 1000)),
        )

    def apply_params(self, params: DetectionParamsWire) -> None:
        classifier = self._settings.classifier
        blur_k = coerce_odd_kernel(int(params.blur_kernel))
        self._settings = PipelineSettings(
            vision=VisionSettings(
                preprocess=PreprocessSettings(
                    blur_kernel=(blur_k, blur_k),
                    adaptive_block_size=params.adaptive_block_size,
                    adaptive_c=params.adaptive_c,
                    canny_low=params.canny_low,
                    canny_high=params.canny_high,
                ),
                detector=DetectorSettings(
                    min_area_px=float(params.min_area_px),
                    max_area_px=float(params.max_area_px),
                    aspect_min=params.aspect_min,
                    aspect_max=params.aspect_max,
                ),
            ),
            classifier=ClassifierSettings(
                model_path=classifier.model_path,
                min_confidence=params.confidence_threshold,
                backend=classifier.backend,
            ),
            calibration=self._settings.calibration,
            min_face_area_px=float(params.min_area_px),
        )

    def latest_jpeg(self) -> Optional[bytes]:
        return self._latest_jpeg

    def latest_telemetry(self) -> dict[str, Any]:
        return self._latest_telemetry

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._frame_source is not None:
            self._frame_source.stop()
            self._frame_source = None

    def _infer_frame(self, frame: object):
        if is_vision_mock_mode():
            return vision_mock.detect_from_frame(frame, settings=self._settings)
        return ei_runner_service.detect_from_frame(frame, self._settings)

    async def _run_loop(self) -> None:
        self._frame_source = create_frame_source_from_env()
        try:
            await asyncio.to_thread(self._frame_source.start)
        except Exception as exc:
            self._running = False
            self._frame_source = None
            raise RuntimeError(f"camera start failed: {exc}") from exc
        target_period = 1.0 / 30.0
        try:
            while self._running:
                loop_start = time.perf_counter()
                frame = await asyncio.to_thread(self._frame_source.read)
                if not is_vision_mock_mode():
                    await asyncio.to_thread(ei_runner_service.ensure_initialized)
                result, scores = await asyncio.to_thread(self._infer_frame, frame)
                jpeg = await asyncio.to_thread(_encode_jpeg, frame.image_bgr)
                self._latest_jpeg = jpeg
                latency_ms = (time.perf_counter() - loop_start) * 1000.0
                fps = 1.0 / max(latency_ms / 1000.0, 1e-6)
                telemetry = build_telemetry_from_contract(
                    result, fps=fps, latency_ms=latency_ms, classifier_scores=scores
                )
                payload = telemetry.model_dump(by_alias=True)
                self._latest_telemetry = payload
                await self._ws.broadcast_json(payload)
                elapsed = time.perf_counter() - loop_start
                await asyncio.sleep(max(0.0, target_period - elapsed))
        except asyncio.CancelledError:
            raise
        except Exception:
            self._running = False
            raise
        finally:
            if self._frame_source is not None:
                self._frame_source.stop()
                self._frame_source = None


def _encode_jpeg(image_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("failed to encode JPEG")
    return buf.tobytes()
