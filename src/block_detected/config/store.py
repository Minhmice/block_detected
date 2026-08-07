"""Load, save, and validate AppConfig (JSON inside the package)."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from block_detected.config.paths import PACKAGE_ROOT, PROJECT_ROOT
from block_detected.config.schema import AppConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"
LEGACY_TOML_PATH = PROJECT_ROOT / "block_detected.toml"
LEGACY_ROOT_JSON = PROJECT_ROOT / "block_detected.json"


def _load_toml_dict(path: Path) -> dict:
    import tomllib

    with path.open("rb") as fh:
        return tomllib.load(fh)


def _load_json_dict(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _migrate_legacy_config_if_needed(config_path: Path) -> None:
    if config_path.is_file():
        return
    if LEGACY_ROOT_JSON.is_file():
        logger.warning(
            "Migrating %s → %s",
            LEGACY_ROOT_JSON,
            config_path,
        )
        shutil.copy2(LEGACY_ROOT_JSON, config_path)
        return
    if LEGACY_TOML_PATH.is_file():
        logger.warning(
            "Migrating %s → %s (TOML config is deprecated)",
            LEGACY_TOML_PATH.name,
            config_path.name,
        )
        config = AppConfig.from_dict(_load_toml_dict(LEGACY_TOML_PATH))
        save_config(config, config_path)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if path is None:
        _migrate_legacy_config_if_needed(config_path)
    if not config_path.is_file():
        return AppConfig.defaults()

    return AppConfig.from_dict(_load_json_dict(config_path))


def save_config(config: AppConfig, path: Path | None = None) -> None:
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.write_text(
        json.dumps(config.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def validate_config(config: AppConfig) -> list[str]:
    return config.validate()
