"""Tests for io.images."""

from pathlib import Path

from block_detected.io.images import iter_image_paths


def test_iter_image_paths_empty_dir(tmp_path: Path):
    assert iter_image_paths(tmp_path) == []


def test_iter_image_paths_finds_png(tmp_path: Path):
    (tmp_path / "a.png").write_bytes(b"x")
    (tmp_path / "skip.txt").write_text("nope")
    paths = iter_image_paths(tmp_path)
    assert len(paths) == 1
    assert paths[0].name == "a.png"
