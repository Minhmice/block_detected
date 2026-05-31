"""Frame source factory with mock mode and runtime camera selection."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

from block_detected.camera import CameraSettings, create_frame_source, load_camera_settings

from app.services.camera_runtime import camera_runtime

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIVE_CONFIG = "config/camera.usb.mac.json"


def is_mock_mode() -> bool:
    return camera_runtime.is_mock()


def _camera_config_path() -> Path:
    raw = os.getenv("CAMERA_CONFIG", "config/camera.example.json")
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def _live_config_path() -> Path:
    path = _REPO_ROOT / _LIVE_CONFIG
    if path.exists():
        return path
    return _camera_config_path()


def _profile_to_settings(data: dict, profile_name: str) -> CameraSettings:
    merged = {**data.get("defaults", {}), **data["profiles"][profile_name]}
    filtered = {k: v for k, v in merged.items() if not str(k).startswith("_")}
    return CameraSettings(**filtered)


def load_camera_settings_from_env() -> CameraSettings:
    if is_mock_mode():
        config_path = _camera_config_path()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        settings = _profile_to_settings(data, "image_sequence")
        if settings.image_dir and not Path(settings.image_dir).is_absolute():
            return replace(settings, image_dir=str(_REPO_ROOT / settings.image_dir))
        return settings

    config_path = _live_config_path()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    profile = "usb" if "usb" in data.get("profiles", {}) else data.get("active_profile", "usb")
    settings = _profile_to_settings(data, profile)
    return replace(settings, camera_index=camera_runtime.get_camera_index())


def preview_camera_backend() -> str:
    return load_camera_settings_from_env().backend


def create_frame_source_from_env():
    settings = load_camera_settings_from_env()
    return create_frame_source(settings)
