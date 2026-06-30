from __future__ import annotations

import pytest

from block_detection_v2.benchmark import list_dataset, run_benchmark


def test_list_dataset_count():
    paths = list_dataset()
    if len(paths) < 108:
        pytest.skip("block_dataset incomplete")
    assert len(paths) == 108
    assert paths[0].name == "dt1.jpg"


def test_benchmark_summary_keys():
    paths = list_dataset()
    if len(paths) < 108:
        pytest.skip("block_dataset incomplete")
    summary = run_benchmark(write_overlays=False)
    for key in ("total", "accepted", "accept_rate", "fail_roi", "fail_fit", "low_score"):
        assert key in summary


def test_benchmark_accept_rate():
    paths = list_dataset()
    if len(paths) < 108:
        pytest.skip("block_dataset incomplete")
    summary = run_benchmark(write_overlays=False)
    assert summary["accept_rate"] >= 0.80
