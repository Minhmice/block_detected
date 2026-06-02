"""Webcam inference application — thin orchestration entry."""

import logging

import cv2

from block_detected.runtime.config_store import load_config, validate_config
from block_detected.runtime.engine import WebcamEngine
from block_detected.runtime.logging_setup import setup_logging
from block_detected.ui.input.handlers import handle_key, on_mouse

logger = logging.getLogger(__name__)


def main() -> int:
    config = load_config()
    errors = validate_config(config)
    if errors:
        for err in errors:
            logger.error("Config: %s", err)
        return 1

    setup_logging(config.ui.log_level)

    engine = WebcamEngine.create(config)
    if engine is None:
        return 1
    if not engine.start():
        return 1

    logger.info("Click the model button (bottom-left) or press 'v' to switch model.")
    logger.info("Press 'c' to switch camera source.")
    logger.info("Press Arrow Up/Down to increase/decrease confidence.")
    logger.info("Press 'm' to toggle multi-overlay history.")
    logger.info("Press 'n' to toggle eval mode (percentage labels).")
    logger.info("Press 'q' to quit.")

    ui_state: dict = {"button_rect": None, "switch_model": engine.switch_model}

    cv2.namedWindow(config.ui.window_name)
    cv2.setMouseCallback(config.ui.window_name, on_mouse, ui_state)

    try:
        while True:
            processed = engine.process_frame()
            if processed is None:
                break

            ui_state["button_rect"] = processed.button_rect
            cv2.imshow(config.ui.window_name, processed.annotated)

            key = cv2.waitKeyEx(1)
            if key == ord("c"):
                engine.switch_camera()
                continue

            if not handle_key(
                key,
                runtime_state=engine.state,
                inference=config.inference,
                ui=config.ui,
                switch_model=engine.switch_model,
            ):
                break
    finally:
        engine.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
