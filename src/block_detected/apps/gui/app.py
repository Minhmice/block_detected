"""PySide6 desktop GUI — Robo-Vision OS shell (see robo_window.py)."""

from __future__ import annotations

import sys

from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import load_config, validate_config
from block_detected.runtime.logging_setup import setup_logging

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None  # type: ignore[assignment]

from block_detected.apps.gui.robo_window import MainWindow, RoboVisionWindow

__all__ = ["MainWindow", "RoboVisionWindow", "main"]


def _print_missing_qt() -> int:
    print("[ERROR] PySide6 is not installed.")
    print('[INFO] Install with GUI deps: pip install -e .')
    return 1


def main() -> int:
    if QtWidgets is None:
        return _print_missing_qt()

    config = load_config()
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"[ERROR] Config: {error}")
        return 1

    setup_logging(config.ui.log_level)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
