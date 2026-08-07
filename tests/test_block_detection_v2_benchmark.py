from __future__ import annotations

from pathlib import Path

from block_detection_v2.benchmark import dataset_dir, list_dataset, run_benchmark


def test_list_dataset_count():
    repo_root = Path(__file__).resolve().parents[1]
    paths = list_dataset()
    assert dataset_dir() == repo_root / "block_dataset"
    assert len(paths) == 108
    assert paths[0].name == "dt1.jpg"
    assert paths[-1].name == "dt108.jpg"


def test_benchmark_summary_keys():
    summary = run_benchmark(write_overlays=False)
    for key in ("total", "accepted", "accept_rate", "fail_roi", "fail_fit", "low_score"):
        assert key in summary


def test_benchmark_accept_rate():
    summary = run_benchmark(write_overlays=False)
    assert summary["accept_rate"] >= 0.80
