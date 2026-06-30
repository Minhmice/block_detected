"""Re-export from block_detected.config.store (deprecated path)."""

from block_detected.config.store import (
    DEFAULT_CONFIG_PATH,
    load_config,
    save_config,
    validate_config,
)

__all__ = ["DEFAULT_CONFIG_PATH", "load_config", "save_config", "validate_config"]
