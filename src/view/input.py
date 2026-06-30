"""OpenCV keyboard and mouse input for detection view."""

from __future__ import annotations

import logging

import cv2

from block_detected.config.schema import InferenceConfig, UiDebugConfig
from block_detected.runtime.state import RuntimeState
from block_detected.vision.geometry import point_in_rect

logger = logging.getLogger(__name__)


def on_mouse(event, x, y, _flags, state: dict) -> None:
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    rect = state.get("button_rect")
    if rect and point_in_rect(x, y, rect):
        state["switch_model"]()


def handle_key(
    key: int,
    *,
    runtime_state: RuntimeState,
    inference: InferenceConfig,
    ui: UiDebugConfig,
    switch_model,
    reload_config=None,
) -> bool:
    """Process a key press from waitKeyEx. Returns True to continue, False to quit."""
    if key == -1:
        return True

    if key in (ord("r"), ord("R")) and reload_config is not None:
        reload_config()
        return True

    if key == ord("c"):
        return True

    if key in (ord("v"), ord("V")):
        switch_model()
        return True

    if key == ord("n"):
        runtime_state.eval_mode = not runtime_state.eval_mode
        logger.info("Eval mode: %s", "ON" if runtime_state.eval_mode else "OFF")
        return True

    if key == ui.key_arrow_up:
        if runtime_state.eval_mode:
            logger.info("Arrow Up disabled in eval mode.")
        else:
            runtime_state.confidence = min(
                inference.conf_max, runtime_state.confidence + inference.conf_step
            )
            logger.info("Confidence increased to: %.3f", runtime_state.confidence)
        return True

    if key == ui.key_arrow_down:
        if runtime_state.eval_mode:
            logger.info("Arrow Down disabled in eval mode.")
        else:
            runtime_state.confidence = max(
                inference.conf_min, runtime_state.confidence - inference.conf_step
            )
            logger.info("Confidence decreased to: %.3f", runtime_state.confidence)
        return True

    if key == ord("q"):
        logger.info("Quit requested by user (q key).")
        return False

    return True
