"""OpenCV detection preview — replaces PySide6 GUI."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2

from block_detected.config.schema import AppConfig
from block_detected.config.store import DEFAULT_CONFIG_PATH, load_config, validate_config
from block_detected.runtime.engine import WebcamEngine
from block_detected.runtime.logging_setup import setup_logging
from block_detected.runtime.platform import is_raspberry_pi
from view.input import handle_key, on_mouse
from view.reload import make_config_reloader

logger = logging.getLogger(__name__)


def _prompt_pi_camera_source() -> str:
    print()
    print("[Raspberry Pi detected] Chọn camera:")
    print("  1  USB webcam")
    print("  2  Pi Camera Module (CSI / libcamera)")
    while True:
        try:
            choice = input("Chọn [1/2] (mặc định 2): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "libcamera"
        if choice in ("", "2"):
            return "libcamera"
        if choice == "1":
            return "usb"
        print("Nhập 1 hoặc 2.")


def _apply_pi_camera_choice(config: AppConfig) -> AppConfig:
    if not is_raspberry_pi() or not sys.stdin.isatty():
        return config
    source = _prompt_pi_camera_source()
    if config.camera.source != source:
        config.camera.source = source
        from block_detected.config.store import save_config

        save_config(config)
    print()
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="block-detected-view",
        description="OpenCV preview with YOLO block detection.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Path to JSON config (default: {DEFAULT_CONFIG_PATH}).",
    )
    return parser


def run_view(config: AppConfig, *, config_path: Path | None = None) -> int:
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"[ERROR] Config: {error}")
        return 1

    setup_logging(config.ui.log_level)
    engine, create_error = WebcamEngine.try_create(config)
    if engine is None:
        print(f"[ERROR] {create_error}")
        return 1

    started, start_error = engine.try_start()
    if not started:
        engine.shutdown(destroy_cv_windows=False)
        print(f"[ERROR] {start_error}")
        return 1

    window_name = config.ui.window_name
    cv2.namedWindow(window_name)
    mouse_state: dict = {"button_rect": None, "switch_model": engine.switch_model}
    reload_config = make_config_reloader(engine, config_path=config_path)

    try:
        while True:
            processed = engine.process_frame()
            if processed is None:
                break
            mouse_state["button_rect"] = processed.button_rect
            cv2.setMouseCallback(window_name, on_mouse, mouse_state)
            cv2.imshow(window_name, processed.annotated)
            key = cv2.waitKeyEx(1)
            if not handle_key(
                key,
                runtime_state=engine.state,
                inference=config.inference,
                ui=config.ui,
                switch_model=engine.switch_model,
                reload_config=reload_config,
            ):
                break
    finally:
        engine.shutdown(destroy_cv_windows=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    config = _apply_pi_camera_choice(config)
    try:
        return run_view(config, config_path=args.config)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
