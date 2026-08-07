"""Re-export camera API (compat shim)."""

from block_detected.io.camera.open import open_camera
from block_detected.io.camera.pi.picamera2 import PiCameraCapture
from block_detected.io.camera.pi.rpicam import RpicamCapture
from block_detected.io.camera.v4l2 import find_usb_camera, switch_camera

__all__ = [
    "PiCameraCapture",
    "RpicamCapture",
    "find_usb_camera",
    "open_camera",
    "switch_camera",
]
