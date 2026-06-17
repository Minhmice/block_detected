    """Tests for frame preprocessing."""

import numpy as np

from block_detected.runtime.preprocess import apply_preprocess


def test_apply_preprocess_preserves_shape():
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    out = apply_preprocess(
        frame,
        contrast=1.2,
        brightness=10,
        saturation=1.0,
        blur_kernel=0,
    )
    assert out.shape == frame.shape


def test_apply_preprocess_blur_odd_kernel():
    frame = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
    out = apply_preprocess(
        frame,
        contrast=1.0,
        brightness=0,
        saturation=1.0,
        blur_kernel=5,
    )
    assert out.shape == frame.shape
