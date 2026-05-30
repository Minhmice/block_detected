"""Debug frame persistence — separate from camera capture backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .camera import CaptureFrame


@dataclass
class DebugSettings:
    enabled: bool = False
    directory: Path = Path("debug_frames")
    every_n_frames: int = 1
    max_files: Optional[int] = None
    max_bytes: Optional[int] = None
    run_id: Optional[str] = None
    allowed_root: Optional[Path] = None

    @classmethod
    def from_mapping(cls, data: dict, *, allowed_root: Optional[Path] = None) -> "DebugSettings":
        return cls(
            enabled=bool(data.get("enabled", False)),
            directory=Path(data.get("directory", "debug_frames")),
            every_n_frames=int(data.get("every_n_frames", 1)),
            max_files=data.get("max_files"),
            max_bytes=data.get("max_bytes"),
            run_id=data.get("run_id"),
            allowed_root=allowed_root,
        )


class DebugFrameWriter:
    """Writes normalized BGR pipeline frames to disk for field tuning."""

    def __init__(self, settings: DebugSettings) -> None:
        self._settings = settings
        self._write_count = 0
        self._resolved_dir: Optional[Path] = None

    def _resolve_debug_dir(self) -> Path:
        base = self._settings.directory
        if self._settings.run_id:
            base = base / self._settings.run_id
        resolved = base.resolve()
        allowed = (self._settings.allowed_root or Path.cwd()).resolve()
        try:
            resolved.relative_to(allowed)
        except ValueError as exc:
            raise ValueError(
                f"debug directory {resolved} is outside allowed root {allowed}"
            ) from exc
        return resolved

    def _ensure_dir(self) -> Path:
        if self._resolved_dir is None:
            self._resolved_dir = self._resolve_debug_dir()
            self._resolved_dir.mkdir(parents=True, exist_ok=True)
        return self._resolved_dir

    def write(self, frame: CaptureFrame, overlay_bgr: Optional[np.ndarray] = None) -> None:
        self.write_raw(frame.frame_id, frame.image_bgr, overlay_bgr=overlay_bgr)

    def write_raw(
        self,
        frame_id: str,
        image_bgr: np.ndarray,
        overlay_bgr: Optional[np.ndarray] = None,
    ) -> None:
        if not self._settings.enabled:
            return

        self._write_count += 1
        if self._settings.every_n_frames > 1:
            if self._write_count % self._settings.every_n_frames != 0:
                return

        debug_dir = self._ensure_dir()
        raw_path = debug_dir / f"{frame_id}_raw.png"
        if not cv2.imwrite(str(raw_path), image_bgr):
            raise OSError(f"failed to write debug frame: {raw_path}")

        if overlay_bgr is not None:
            overlay_path = debug_dir / f"{frame_id}_overlay.png"
            if not cv2.imwrite(str(overlay_path), overlay_bgr):
                raise OSError(f"failed to write debug overlay: {overlay_path}")

        self._enforce_retention(debug_dir)

    def _enforce_retention(self, debug_dir: Path) -> None:
        if self._settings.max_files is not None:
            raw_files = sorted(debug_dir.glob("*_raw.png"))
            while len(raw_files) > self._settings.max_files:
                oldest = raw_files.pop(0)
                oldest.unlink(missing_ok=True)
                overlay = oldest.with_name(oldest.name.replace("_raw.png", "_overlay.png"))
                overlay.unlink(missing_ok=True)
