"""Load, save, and validate AppConfig (TOML via stdlib tomllib)."""

from pathlib import Path
from typing import Any

from block_detected.config.paths import PROJECT_ROOT
from block_detected.runtime.config_schema import AppConfig

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "block_detected.toml"


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def _dict_to_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for section, fields in data.items():
        lines.append(f"[{section}]")
        if isinstance(fields, dict):
            for key, value in fields.items():
                lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return AppConfig.defaults()

    import tomllib

    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.write_text(_dict_to_toml(config.to_dict()), encoding="utf-8")


def validate_config(config: AppConfig) -> list[str]:
    return config.validate()
