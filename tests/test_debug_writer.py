"""DebugFrameWriter tests (CAM-03).

Quick run: python -m pytest tests/test_debug_writer.py -q
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from block_detected.camera import CaptureFrame
from block_detected.debug import DebugFrameWriter, DebugSettings


def _sample_frame(frame_id: str = "frame_000001") -> CaptureFrame:
    return CaptureFrame(
        frame_id=frame_id,
        image_bgr=np.zeros((480, 640, 3), dtype=np.uint8),
        timestamp_ns=0,
        source="test",
        metadata={},
    )


def test_debug_writer_uses_monotonic_frame_ids(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    writer = DebugFrameWriter(
        DebugSettings(enabled=True, directory=root / "debug", allowed_root=root)
    )
    writer.write(_sample_frame("frame_000001"))
    writer.write(_sample_frame("frame_000002"))
    assert (root / "debug" / "frame_000001_raw.png").is_file()
    assert (root / "debug" / "frame_000002_raw.png").is_file()


def test_debug_writer_disabled_writes_nothing(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    writer = DebugFrameWriter(
        DebugSettings(enabled=False, directory=root / "debug", allowed_root=root)
    )
    writer.write(_sample_frame())
    assert not (root / "debug").exists()


def test_debug_writer_path_confinement(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    allowed = root / "sandbox"
    allowed.mkdir()
    writer = DebugFrameWriter(
        DebugSettings(
            enabled=True,
            directory=root / "outside",
            allowed_root=allowed,
        )
    )
    with pytest.raises(ValueError, match="outside allowed root"):
        writer.write(_sample_frame())


def test_debug_writer_max_files_retention(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    writer = DebugFrameWriter(
        DebugSettings(
            enabled=True,
            directory=root / "debug",
            allowed_root=root,
            max_files=2,
        )
    )
    writer.write(_sample_frame("frame_000001"))
    writer.write(_sample_frame("frame_000002"))
    writer.write(_sample_frame("frame_000003"))
    raw_files = list((root / "debug").glob("*_raw.png"))
    assert len(raw_files) == 2


def test_debug_writer_every_n_frames(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    writer = DebugFrameWriter(
        DebugSettings(
            enabled=True,
            directory=root / "debug",
            allowed_root=root,
            every_n_frames=2,
        )
    )
    writer.write(_sample_frame("frame_000001"))
    writer.write(_sample_frame("frame_000002"))
    raw_files = list((root / "debug").glob("*_raw.png"))
    assert len(raw_files) == 1
    assert raw_files[0].name == "frame_000002_raw.png"
