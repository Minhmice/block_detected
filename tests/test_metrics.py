"""Tests for runtime metrics."""

from block_detected.runtime.metrics import RuntimeMetrics


def test_metrics_fps_computed():
    metrics = RuntimeMetrics()
    t0 = metrics.begin_frame()
    stats = metrics.record(
        frame_start=t0,
        read_end=t0 + 0.01,
        infer_end=t0 + 0.03,
        render_end=t0 + 0.04,
        model_name="train-3.pt",
        camera_index=0,
    )
    assert stats.model_name == "train-3.pt"
    assert stats.camera_index == 0
    assert stats.inference_ms > 0
    assert stats.fps > 0
