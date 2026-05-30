"""GEO-01 preprocess tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from block_detected.preprocess import PreprocessResult, PreprocessSettings, preprocess_bgr

REPO_ROOT = Path(__file__).resolve().parents[1]
VISION_EXAMPLE = REPO_ROOT / "config" / "vision.example.json"


def _blank_bgr() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def _bright_square_bgr(size: int = 120) -> np.ndarray:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    y0 = (480 - size) // 2
    x0 = (640 - size) // 2
    frame[y0 : y0 + size, x0 : x0 + size] = (240, 240, 240)
    return frame


def _dark_square_on_bright_bgr(size: int = 120) -> np.ndarray:
    frame = np.full((480, 640, 3), 220, dtype=np.uint8)
    y0 = (480 - size) // 2
    x0 = (640 - size) // 2
    frame[y0 : y0 + size, x0 : x0 + size] = (30, 30, 30)
    return frame


def test_preprocess_rejects_non_bgr_input() -> None:
    settings = PreprocessSettings()
    with pytest.raises(ValueError, match="BGR"):
        preprocess_bgr(np.zeros((480, 640), dtype=np.uint8), settings)
    with pytest.raises(ValueError, match="uint8"):
        preprocess_bgr(np.zeros((480, 640, 3), dtype=np.float32), settings)
    with pytest.raises(ValueError, match="shape"):
        preprocess_bgr(np.zeros((240, 320, 3), dtype=np.uint8), settings)


def test_adaptive_threshold_config_validation() -> None:
    with pytest.raises(ValueError, match="adaptive_block_size"):
        PreprocessSettings(adaptive_block_size=30)
    with pytest.raises(ValueError, match="blur_kernel"):
        PreprocessSettings(blur_kernel=(4, 4))


def test_preprocess_adaptive_outputs_uint8_mask() -> None:
    frame = _bright_square_bgr()
    before = frame.copy()
    result = preprocess_bgr(frame, PreprocessSettings(mode="adaptive_threshold"))
    assert np.array_equal(frame, before)
    _assert_preprocess_result(result)
    assert result.mask.max() > 0


def test_preprocess_canny_outputs_uint8_mask() -> None:
    frame = _bright_square_bgr()
    result = preprocess_bgr(frame, PreprocessSettings(mode="canny"))
    _assert_preprocess_result(result)
    assert result.mask.dtype == np.uint8


def test_preprocess_polarity_inversion_configurable() -> None:
    bright = _bright_square_bgr()
    dark_on_bright = _dark_square_on_bright_bgr()

    binary = preprocess_bgr(
        bright,
        PreprocessSettings(adaptive_threshold_type="THRESH_BINARY"),
    )
    binary_inv = preprocess_bgr(
        dark_on_bright,
        PreprocessSettings(adaptive_threshold_type="THRESH_BINARY_INV"),
    )

    assert binary.mask.sum() > 0
    assert binary_inv.mask.sum() > 0


def test_vision_example_json_matches_preprocess_settings() -> None:
    data = json.loads(VISION_EXAMPLE.read_text(encoding="utf-8"))
    preprocess = data["preprocess"]
    settings = PreprocessSettings(
        mode=preprocess["mode"],
        blur_kernel=tuple(preprocess["blur_kernel"]),
        adaptive_block_size=preprocess["adaptive_block_size"],
        adaptive_c=preprocess["adaptive_c"],
        adaptive_threshold_type=preprocess["adaptive_threshold_type"],
        canny_low=preprocess["canny_low"],
        canny_high=preprocess["canny_high"],
        morph_kernel=tuple(preprocess["morph_kernel"]),
        morph_open_iterations=preprocess["morph_open_iterations"],
        morph_close_iterations=preprocess["morph_close_iterations"],
    )
    assert settings.mode == "adaptive_threshold"
    assert settings.adaptive_threshold_type == "THRESH_BINARY_INV"


def _assert_preprocess_result(result: PreprocessResult) -> None:
    for field in ("gray", "blurred", "raw_mask", "opened", "mask"):
        arr = getattr(result, field)
        assert arr.shape == (480, 640)
        assert arr.dtype == np.uint8
