"""Camera session: open, switch, Pi source resolution."""

from __future__ import annotations

import logging
import sys

import cv2

from block_detected.config.schema import AppConfig, CameraConfig
from block_detected.io.camera.capture import (
    PiCameraCapture,
    RpicamCapture,
    find_usb_camera,
    open_camera,
    switch_camera,
)
from block_detected.io.camera.probe import format_camera_display
from block_detected.io.camera.v4l2 import try_open_index
from block_detected.runtime.logging_setup import log_event
from block_detected.runtime.platform import is_raspberry_pi
from block_detected.runtime.state import RuntimeState

logger = logging.getLogger(__name__)


def resolve_pi_source(cam: CameraConfig) -> int | str:
    if cam.source == "libcamera":
        logger.info("Pi config: camera.source=libcamera — using Pi Camera Module (CSI)")
        return "libcamera"
    if cam.source == "rpicam":
        logger.info("Pi config: camera.source=rpicam — using rpicam-vid subprocess")
        return "rpicam"
    if cam.source == "gstreamer":
        logger.info("Pi config: camera.source=gstreamer — using GStreamer pipeline")
        return "gstreamer"
    logger.info("Pi config: camera.source=auto — trying libcamera first")
    return "libcamera"


def _usb_device_label(index: int) -> str:
    if sys.platform.startswith("linux"):
        return f"/dev/video{index}"
    return f"index {index}"


def _try_open_usb_camera(
    cam: CameraConfig,
    preferred_index: int,
) -> tuple[cv2.VideoCapture | None, int, str | None]:
    label = _usb_device_label(preferred_index)
    cap = try_open_index(preferred_index, width=cam.width, height=cam.height)
    if cap is not None:
        logger.info("Opened USB camera at %s", label)
        log_event("CAM", f"USB camera {label} acquired.")
        return cap, preferred_index, None

    logger.info("USB camera %s unavailable — scanning 0..%s", label, cam.max_index)
    usb_cap, usb_idx = find_usb_camera(
        width=cam.width,
        height=cam.height,
        max_index=cam.max_index,
    )
    if usb_cap is not None:
        found = _usb_device_label(usb_idx)
        logger.info("Opened USB camera via scan: %s", found)
        log_event("CAM", f"USB camera {found} acquired (scan).")
        return usb_cap, usb_idx, None

    message = (
        "No USB webcam detected. Is it plugged in? "
        + (
            "Try 'ls /dev/video*' on Pi/Linux."
            if sys.platform.startswith("linux")
            else "Run: python scripts/probe_cameras.py"
        )
    )
    logger.error(message)
    return None, preferred_index, message


def try_open_camera(
    config: AppConfig,
    state: RuntimeState,
) -> tuple[cv2.VideoCapture | PiCameraCapture | RpicamCapture | None, int | str, str | None]:
    cam = config.camera

    if cam.source == "usb":
        return _try_open_usb_camera(cam, state.camera_index)

    if is_raspberry_pi():
        camera_source: int | str = resolve_pi_source(cam)
    else:
        camera_source = state.camera_index

    cap = open_camera(camera_source, width=cam.width, height=cam.height)

    if cap is None and not is_raspberry_pi():
        logger.info("Camera index %s failed — scanning indices 0..%s", camera_source, cam.max_index)
        usb_cap, usb_idx = find_usb_camera(
            width=cam.width,
            height=cam.height,
            max_index=cam.max_index,
        )
        if usb_cap is not None:
            logger.info("Opened camera via auto-detect at index %s", usb_idx)
            log_event("CAM", f"Camera {usb_idx} acquired (auto-detect).")
            return usb_cap, usb_idx, None

    if cap is None and is_raspberry_pi() and cam.source == "auto":
        logger.info("libcamera failed — scanning for USB webcam")
        usb_cap, usb_idx = find_usb_camera(
            width=cam.width,
            height=cam.height,
            max_index=cam.max_index,
        )
        if usb_cap is not None:
            logger.info("Fallback USB camera at /dev/video%s", usb_idx)
            log_event("CAM", f"USB camera /dev/video{usb_idx} acquired (fallback).")
            return usb_cap, usb_idx, None

    if cap is None:
        message = (
            f"Failed to open camera source {camera_source} "
            f"({cam.width}x{cam.height}). "
            "Check permissions, USB connection, or another app using the camera."
        )
        logger.error(message)
        return None, camera_source, message

    logger.info("Opened camera source: %s", camera_source)
    log_event("CAM", f"Camera {camera_source} acquired.")
    return cap, camera_source, None


def try_switch_camera(
    cap: cv2.VideoCapture | PiCameraCapture | RpicamCapture,
    camera_source: int | str,
    config: AppConfig,
    state: RuntimeState,
) -> tuple[cv2.VideoCapture | PiCameraCapture | RpicamCapture, int | str, bool]:
    if isinstance(camera_source, str):
        logger.warning("Cannot switch camera — Pi Camera Module is the only CSI source.")
        return cap, camera_source, False
    cam = config.camera
    new_cap, new_index, switched = switch_camera(
        cap,
        state.camera_index,
        max_index=cam.max_index,
        width=cam.width,
        height=cam.height,
    )
    if switched:
        state.camera_index = new_index
        label = format_camera_display(new_index, cam.source)
        logger.info("Switched to camera: %s", label)
        log_event("CAM", f"Camera {label} acquired.")
    else:
        logger.warning("No other camera source available to switch.")
    return new_cap, new_index if switched else camera_source, switched
