"""Camera capture: FrameSource adapters for CSI, USB, and offline image sequences."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

import cv2
import numpy as np

TARGET_WIDTH = 640
TARGET_HEIGHT = 480
TARGET_SHAPE = (TARGET_HEIGHT, TARGET_WIDTH, 3)
MAX_WARMUP_FRAMES = 60


@dataclass(frozen=True)
class CaptureFrame:
    frame_id: str
    image_bgr: np.ndarray
    timestamp_ns: int
    source: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass
class CameraSettings:
    backend: str = "image_sequence"
    width: int = TARGET_WIDTH
    height: int = TARGET_HEIGHT
    warmup_frames: int = 5
    lock_exposure: bool = True
    lock_white_balance: bool = True
    exposure_time_us: Optional[int] = None
    analogue_gain: Optional[float] = None
    colour_gains: Optional[tuple[float, float]] = None
    camera_index: int = 0
    device_path: Optional[str] = None
    image_dir: Optional[str] = None
    glob_pattern: str = "*.png"
    cv_backend: str = "auto"
    debug: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.warmup_frames < 0:
            raise ValueError("warmup_frames must be non-negative")
        if self.warmup_frames > MAX_WARMUP_FRAMES:
            raise ValueError(f"warmup_frames must be <= {MAX_WARMUP_FRAMES}")


@runtime_checkable
class FrameSource(Protocol):
    def start(self) -> None: ...
    def read(self) -> CaptureFrame: ...
    def stop(self) -> None: ...


def _normalize_bgr(image: np.ndarray, width: int, height: int) -> np.ndarray:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif image.shape[2] == 3:
        pass
    else:
        raise RuntimeError(f"unsupported channel count: {image.shape}")

    h, w = image.shape[:2]
    if (h, w) != (height, width):
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    out = np.ascontiguousarray(image, dtype=np.uint8)
    if out.shape != (height, width, 3):
        raise RuntimeError(f"expected shape {(height, width, 3)}, got {out.shape}")
    return out


def _format_frame_id(index: int) -> str:
    return f"frame_{index:06d}"


def _empty_cam02_metadata() -> dict[str, object]:
    return {
        "settings_requested": {},
        "settings_applied": {},
        "settings_verified": {},
        "settings_unsupported": [],
    }


_CV_BACKEND_MAP: dict[str, int] = {
    "v4l2": cv2.CAP_V4L2,
    "avfoundation": cv2.CAP_AVFOUNDATION,
    "dshow": getattr(cv2, "CAP_DSHOW", 700),
    "any": cv2.CAP_ANY,
}


def _select_cv_backend(cv_backend: str) -> int:
    """Return cv2 VideoCapture apiPreference for the given backend name."""
    if cv_backend and cv_backend != "auto":
        key = cv_backend.lower()
        if key not in _CV_BACKEND_MAP:
            raise ValueError(f"unknown cv_backend: {cv_backend!r}")
        return _CV_BACKEND_MAP[key]
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform.startswith("linux"):
        return cv2.CAP_V4L2
    return cv2.CAP_ANY


def list_usb_camera_indices(max_index: int = 10, cv_backend: str = "auto") -> list[int]:
    """Probe OpenCV camera indices that open successfully."""
    if sys.platform == "darwin":
        max_index = min(max_index, 2)
    backend_api = _select_cv_backend(cv_backend)
    found: list[int] = []
    consecutive_misses = 0
    miss_limit = 1 if sys.platform == "darwin" else 2
    # #region agent log
    try:
        import json as _json
        import time as _time
        from pathlib import Path as _Path

        _log_path = _Path(__file__).resolve().parents[2] / ".cursor" / "debug-7b62f0.log"
        with _log_path.open("a", encoding="utf-8") as _f:
            _f.write(
                _json.dumps(
                    {
                        "sessionId": "7b62f0",
                        "timestamp": int(_time.time() * 1000),
                        "location": "camera.py:list_usb_camera_indices:entry",
                        "message": "probe start",
                        "data": {
                            "max_index": max_index,
                            "platform": sys.platform,
                            "cv_backend": cv_backend,
                            "miss_limit": miss_limit,
                        },
                        "hypothesisId": "A",
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion
    for index in range(max_index):
        cap = cv2.VideoCapture(index, backend_api)
        try:
            opened = cap.isOpened()
            if opened:
                found.append(index)
                consecutive_misses = 0
            else:
                consecutive_misses += 1
        finally:
            cap.release()
        if consecutive_misses >= miss_limit and found:
            break
    # #region agent log
    try:
        import json as _json
        import time as _time
        from pathlib import Path as _Path

        _log_path = _Path(__file__).resolve().parents[2] / ".cursor" / "debug-7b62f0.log"
        with _log_path.open("a", encoding="utf-8") as _f:
            _f.write(
                _json.dumps(
                    {
                        "sessionId": "7b62f0",
                        "timestamp": int(_time.time() * 1000),
                        "location": "camera.py:list_usb_camera_indices:exit",
                        "message": "probe done",
                        "data": {"found": found, "max_index": max_index},
                        "hypothesisId": "A",
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion
    return found


def load_camera_settings(path: Path) -> CameraSettings:
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = data.get("active_profile", "image_sequence")
    profiles = data.get("profiles", {})
    if profile not in profiles:
        raise ValueError(f"unknown active_profile: {profile!r}")
    merged = {**data.get("defaults", {}), **profiles[profile]}
    settings = CameraSettings(
        backend=str(merged.get("backend", profile)),
        width=int(merged.get("width", TARGET_WIDTH)),
        height=int(merged.get("height", TARGET_HEIGHT)),
        warmup_frames=int(merged.get("warmup_frames", 5)),
        lock_exposure=bool(merged.get("lock_exposure", True)),
        lock_white_balance=bool(merged.get("lock_white_balance", True)),
        exposure_time_us=merged.get("exposure_time_us"),
        analogue_gain=merged.get("analogue_gain"),
        colour_gains=tuple(merged["colour_gains"])
        if merged.get("colour_gains") is not None
        else None,
        camera_index=int(merged.get("camera_index", 0)),
        device_path=merged.get("device_path"),
        image_dir=merged.get("image_dir"),
        glob_pattern=str(merged.get("glob_pattern", "*.png")),
        cv_backend=str(merged.get("cv_backend", "auto")),
        debug=data.get("debug"),
    )
    return settings


class ImageSequenceFrameSource:
    def __init__(self, settings: CameraSettings) -> None:
        self._settings = settings
        self._paths: list[Path] = []
        self._index = 0
        self._started = False

    def start(self) -> None:
        if not self._settings.image_dir:
            raise RuntimeError("image_sequence backend requires image_dir")
        root = Path(self._settings.image_dir)
        if not root.is_dir():
            raise RuntimeError(f"image_dir does not exist: {root}")
        self._paths = sorted(root.glob(self._settings.glob_pattern))
        if not self._paths:
            raise RuntimeError(f"no images match {self._settings.glob_pattern!r} in {root}")
        self._index = 0
        self._started = True

    def read(self) -> CaptureFrame:
        if not self._started:
            raise RuntimeError("ImageSequenceFrameSource not started")
        path = self._paths[self._index % len(self._paths)]
        self._index += 1
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"failed to read image: {path}")
        bgr = _normalize_bgr(image, self._settings.width, self._settings.height)
        return CaptureFrame(
            frame_id=_format_frame_id(self._index),
            image_bgr=bgr,
            timestamp_ns=time.time_ns(),
            source="image_sequence",
            metadata={"path": str(path), **_empty_cam02_metadata()},
        )

    def stop(self) -> None:
        self._started = False


class UsbVideoCaptureFrameSource:
    def __init__(self, settings: CameraSettings) -> None:
        self._settings = settings
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_index = 0
        self._control_metadata = _empty_cam02_metadata()

    def start(self) -> None:
        backend_api = _select_cv_backend(self._settings.cv_backend)
        index = self._settings.camera_index
        if self._settings.device_path:
            cap = cv2.VideoCapture(self._settings.device_path, backend_api)
        else:
            cap = cv2.VideoCapture(index, backend_api)
        if not cap.isOpened():
            raise RuntimeError(
                f"failed to open USB camera index={index} device={self._settings.device_path!r} "
                f"backend={self._settings.cv_backend!r}"
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._settings.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._settings.height)
        self._apply_usb_manual_controls(cap)
        self._cap = cap
        self._frame_index = 0

    def _apply_usb_manual_controls(self, cap: cv2.VideoCapture) -> None:
        requested: dict[str, object] = {}
        applied: dict[str, object] = {}
        verified: dict[str, object] = {}
        unsupported: list[str] = []

        if self._settings.lock_exposure:
            requested["auto_exposure"] = 0
            if cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0):
                applied["auto_exposure"] = 0
                readback = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                verified["auto_exposure"] = readback
            else:
                unsupported.append("CAP_PROP_AUTO_EXPOSURE")
        if self._settings.lock_white_balance:
            requested["auto_wb"] = 0
            if cap.set(cv2.CAP_PROP_AUTO_WB, 0):
                applied["auto_wb"] = 0
                verified["auto_wb"] = cap.get(cv2.CAP_PROP_AUTO_WB)
            else:
                unsupported.append("CAP_PROP_AUTO_WB")

        self._control_metadata = {
            "settings_requested": requested,
            "settings_applied": applied,
            "settings_verified": verified,
            "settings_unsupported": unsupported,
        }

    def read(self) -> CaptureFrame:
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("UsbVideoCaptureFrameSource not started")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise RuntimeError("USB camera read failed")
        bgr = _normalize_bgr(frame, self._settings.width, self._settings.height)
        self._frame_index += 1
        meta = dict(self._control_metadata)
        meta["width_readback"] = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        meta["height_readback"] = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return CaptureFrame(
            frame_id=_format_frame_id(self._frame_index),
            image_bgr=bgr,
            timestamp_ns=time.time_ns(),
            source="usb-opencv",
            metadata=meta,
        )

    def stop(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class PiCamera2FrameSource:
    def __init__(self, settings: CameraSettings) -> None:
        self._settings = settings
        self._picam2: Any = None
        self._frame_index = 0
        self._control_metadata = _empty_cam02_metadata()

    def start(self) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError(
                "picamera2 is required for CSI capture; install via apt: "
                "sudo apt install python3-picamera2"
            ) from exc

        picam2 = Picamera2()
        config = picam2.create_video_configuration(
            main={"size": (self._settings.width, self._settings.height), "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()

        for _ in range(self._settings.warmup_frames):
            picam2.capture_array()

        self._apply_picamera2_lock(picam2)
        self._picam2 = picam2
        self._frame_index = 0

    def _apply_picamera2_lock(self, picam2: Any) -> None:
        requested: dict[str, object] = {
            "AeEnable": False,
            "AwbEnable": False,
        }
        applied: dict[str, object] = {}
        verified: dict[str, object] = {}
        unsupported: list[str] = []

        try:
            metadata = picam2.capture_metadata()
            controls: dict[str, object] = {
                "AeEnable": False,
                "AwbEnable": False,
            }
            if self._settings.exposure_time_us is not None:
                controls["ExposureTime"] = self._settings.exposure_time_us
            elif "ExposureTime" in metadata:
                controls["ExposureTime"] = metadata["ExposureTime"]
            if self._settings.analogue_gain is not None:
                controls["AnalogueGain"] = self._settings.analogue_gain
            elif "AnalogueGain" in metadata:
                controls["AnalogueGain"] = metadata["AnalogueGain"]
            if self._settings.colour_gains is not None:
                controls["ColourGains"] = self._settings.colour_gains
            elif "ColourGains" in metadata:
                controls["ColourGains"] = metadata["ColourGains"]

            picam2.set_controls(controls)
            applied.update(controls)
            verified["post_lock_metadata"] = picam2.capture_metadata()
        except Exception as exc:  # noqa: BLE001 — record unsupported controls
            unsupported.append(str(exc))

        self._control_metadata = {
            "settings_requested": requested,
            "settings_applied": applied,
            "settings_verified": verified,
            "settings_unsupported": unsupported,
        }

    def read(self) -> CaptureFrame:
        if self._picam2 is None:
            raise RuntimeError("PiCamera2FrameSource not started")
        rgb = self._picam2.capture_array()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        bgr = _normalize_bgr(bgr, self._settings.width, self._settings.height)
        self._frame_index += 1
        return CaptureFrame(
            frame_id=_format_frame_id(self._frame_index),
            image_bgr=bgr,
            timestamp_ns=time.time_ns(),
            source="picamera2",
            metadata=dict(self._control_metadata),
        )

    def stop(self) -> None:
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2 = None


def create_frame_source(settings: CameraSettings) -> FrameSource:
    backend = settings.backend
    if backend == "image_sequence":
        return ImageSequenceFrameSource(settings)
    if backend == "picamera2":
        return PiCamera2FrameSource(settings)
    if backend == "usb":
        return UsbVideoCaptureFrameSource(settings)
    raise ValueError(f"unsupported camera backend: {backend!r}")
