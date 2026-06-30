"""Tests for stream package protocol."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from stream.protocol import DISCOVERY_MESSAGE, pack_frame, require_int


def test_discovery_message():
    assert DISCOVERY_MESSAGE == b"RASPI_CAM_DISCOVER_V1"


def test_pack_frame():
    payload = b"jpeg"
    packed = pack_frame(payload)
    assert packed.endswith(payload)
    assert len(packed) == 4 + len(payload)


def test_require_int():
    assert require_int({"width": 640}, "width", 1, 4096) == 640
