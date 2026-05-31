"""Runtime camera selection (UI-driven, env is bootstrap default only)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_mock() -> bool:
    raw = os.getenv("MOCK_CAMERA")
    if raw is not None and raw.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return os.getenv("DETECTION_MODE", "").strip().lower() == "mock"


@dataclass
class CameraRuntimeState:
    mock_camera: bool | None = field(default=None)
    camera_index: int | None = field(default=None)

    def is_mock(self) -> bool:
        if self.mock_camera is not None:
            return self.mock_camera
        return _env_mock()

    def get_camera_index(self) -> int:
        if self.camera_index is not None:
            return self.camera_index
        return 0

    def set_mock(self, value: bool) -> None:
        self.mock_camera = value

    def set_camera_index(self, value: int) -> None:
        if value < 0:
            raise ValueError("camera_index must be non-negative")
        self.camera_index = value

    def reset_for_tests(self) -> None:
        self.mock_camera = None
        self.camera_index = None


camera_runtime = CameraRuntimeState()
