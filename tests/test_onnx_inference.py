"""Integration tests for ONNX model inference."""

from pathlib import Path

import cv2
import pytest

from block_detected.config.paths import MODELS_DIR
from block_detected.config.schema import AppConfig
from block_detected.detection.yolo.loader import discover_model_paths, load_yolo, read_onnx_task
from block_detected.runtime.detector_loader import load_detector
from block_detected.runtime.engine import WebcamEngine

ONNX_FP32 = MODELS_DIR / "rbs-final.onnx"
SAMPLE_IMAGE = Path(__file__).resolve().parents[1] / "block_dataset" / "dt1.jpg"


@pytest.mark.skipif(not ONNX_FP32.is_file(), reason="models/rbs-final.onnx not present")
def test_onnx_fp32_produces_detections():
    frame = cv2.imread(str(SAMPLE_IMAGE))
    assert frame is not None

    detector = load_detector(ONNX_FP32)
    result = detector.predict(frame, conf=0.25, iou=0.45, imgsz=640, max_det=100, agnostic_nms=False)
    detector.close()

    assert len(result.detections) > 0


@pytest.mark.skipif(not ONNX_FP32.is_file(), reason="models/rbs-final.onnx not present")
def test_engine_loads_onnx_default():
    config = AppConfig.defaults()
    config.inference.last_model_name = ONNX_FP32.name

    engine, error = WebcamEngine.try_create(config)
    assert engine is not None, error
    assert engine.detector.model_name == ONNX_FP32.name
    engine.shutdown(destroy_cv_windows=False)


@pytest.mark.skipif(not ONNX_FP32.is_file(), reason="models/rbs-final.onnx not present")
def test_read_onnx_task_from_metadata():
    assert read_onnx_task(ONNX_FP32) == "detect"


@pytest.mark.skipif(not ONNX_FP32.is_file(), reason="models/rbs-final.onnx not present")
def test_discover_includes_onnx():
    names = [p.name for p in discover_model_paths()]
    assert ONNX_FP32.name in names
