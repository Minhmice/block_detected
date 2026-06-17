"""Auto-detect Raspberry Pi vs desktop platform."""

import sys
from pathlib import Path


def _read_first_line(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def is_raspberry_pi() -> bool:
    """Return True if running on a Raspberry Pi (ARM + model string)."""
    if not sys.platform.startswith("linux"):
        return False
    model = _read_first_line(Path("/proc/device-tree/model"))
    if "Raspberry Pi" in model:
        return True
    cpuinfo = _read_first_line(Path("/proc/cpuinfo"))
    return "BCM" in cpuinfo
