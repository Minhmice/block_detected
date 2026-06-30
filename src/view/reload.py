"""Hot-reload block_detected.json into a running engine."""

from __future__ import annotations

import logging
from pathlib import Path

from block_detected.config.schema import AppConfig
from block_detected.config.store import load_config, validate_config
from block_detected.runtime.config_apply import apply_hot_runtime_settings
from block_detected.runtime.engine import WebcamEngine
from block_detected.runtime.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def make_config_reloader(
    engine: WebcamEngine,
    *,
    config_path: Path | None = None,
) -> callable:
    """Return a callable that reloads JSON config and applies hot settings."""

    def reload() -> None:
        baseline = engine.config
        config = load_config(config_path)
        errors = validate_config(config)
        if errors:
            for error in errors:
                logger.error("Config reload: %s", error)
            return

        changed = AppConfig.needs_camera_restart(
            _changed_keys(baseline, config)
        ) or AppConfig.needs_detector_restart(_changed_keys(baseline, config))
        if changed:
            logger.warning("Config changed keys require app restart (camera or imgsz).")
            return

        apply_hot_runtime_settings(
            engine,
            config,
            confidence=config.inference.default_conf,
            eval_mode=engine.state.eval_mode,
        )
        setup_logging(config.ui.log_level)
        logger.info("Config reloaded from JSON.")

    return reload


def _changed_keys(baseline: AppConfig, current: AppConfig) -> set[str]:
    from block_detected.runtime.config_apply import config_changed_keys

    return config_changed_keys(current, baseline)
