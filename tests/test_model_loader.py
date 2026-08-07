"""Tests for YOLO model discovery."""

from pathlib import Path

from block_detected.detection.yolo.loader import discover_model_paths


def test_discover_model_paths_includes_onnx(tmp_path: Path):
    (tmp_path / "a.pt").write_bytes(b"pt")
    (tmp_path / "b.onnx").write_bytes(b"onnx")
    (tmp_path / "c.txt").write_text("skip")

    paths = discover_model_paths(tmp_path)

    assert [p.name for p in paths] == ["a.pt", "b.onnx"]
