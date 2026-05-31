"""Edge Impulse .eim model path resolution, registry, and startup validation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.services.eim_runtime import eim_runtime

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class EimModelEntry:
    id: str
    label: str
    path: Path

    @property
    def executable(self) -> bool:
        return self.path.is_file() and os.access(self.path, os.X_OK)


@dataclass(frozen=True)
class EimModelStatus:
    path: Path
    exists: bool
    executable: bool
    error: Optional[str] = None


def _registry_config_path() -> Path:
    raw = os.getenv("EI_MODELS_CONFIG", "config/eim_models.json")
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def load_eim_registry() -> tuple[str, list[EimModelEntry]]:
    config_path = _registry_config_path()
    if not config_path.exists():
        return "", []
    data = json.loads(config_path.read_text(encoding="utf-8"))
    default_id = str(data.get("default_id", ""))
    models: list[EimModelEntry] = []
    for item in data.get("models", []):
        rel = str(item.get("path", ""))
        path = Path(rel)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        models.append(
            EimModelEntry(
                id=str(item.get("id", "")),
                label=str(item.get("label", item.get("id", ""))),
                path=path,
            )
        )
    return default_id, models


def list_eim_models() -> list[EimModelEntry]:
    _, models = load_eim_registry()
    return models


def get_model_by_id(model_id: str) -> Optional[EimModelEntry]:
    for model in list_eim_models():
        if model.id == model_id:
            return model
    return None


def resolve_selected_model_id() -> str:
    override = os.getenv("EI_MODEL_ID")
    if override:
        return override.strip()
    runtime_id = eim_runtime.get_selected_id()
    if runtime_id:
        return runtime_id
    default_id, _ = load_eim_registry()
    if default_id:
        return default_id
    return ""


def resolve_eim_path() -> Path:
    env_path = os.getenv("EI_MODEL_PATH", "").strip()
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        return path

    model_id = resolve_selected_model_id()
    if model_id:
        entry = get_model_by_id(model_id)
        if entry is not None:
            return entry.path

    fallback = _REPO_ROOT / "backend/models/block_detector.eim"
    return fallback


def validate_eim_model(path: Optional[Path] = None) -> EimModelStatus:
    target = path if path is not None else resolve_eim_path()
    exists = target.is_file()
    executable = exists and os.access(target, os.X_OK)
    error = None
    if not exists:
        error = f"EIM model not found: {target}"
    elif not executable:
        try:
            rel = target.relative_to(_REPO_ROOT)
            chmod_hint = f"chmod +x {rel}"
        except ValueError:
            chmod_hint = f"chmod +x {target}"
        error = f"EIM model not executable — run: {chmod_hint}"
    return EimModelStatus(path=target, exists=exists, executable=executable, error=error)


def get_selected_model_entry() -> Optional[EimModelEntry]:
    model_id = resolve_selected_model_id()
    if not model_id:
        return None
    return get_model_by_id(model_id)


def is_vision_mock_mode() -> bool:
    val = os.getenv("VISION_MOCK_MODE", "true").strip().lower()
    return val in ("1", "true", "yes", "on")
