"""Typed application configuration (dataclasses + TOML-friendly dicts)."""

from dataclasses import asdict, dataclass, field
from typing import Any

from block_detected.config.inference import (
    CONF_MAX,
    CONF_MIN,
    CONF_STEP,
    DEFAULT_CONF,
    DEFAULT_MODEL_NAME,
    EVAL_CONF,
)
from block_detected.config.ui import (
    BUTTON_HEIGHT,
    BUTTON_MARGIN,
    BUTTON_PAD_X,
    KEY_ARROW_DOWN,
    KEY_ARROW_UP,
    WINDOW_NAME,
)


# Keys that require reopening camera or reloading detector when changed at runtime.
RESTART_CAMERA_KEYS = frozenset({"camera.index", "camera.width", "camera.height", "camera.max_index", "camera.source"})
RESTART_DETECTOR_KEYS = frozenset({"inference.imgsz"})


@dataclass
class CameraConfig:
    index: int = 0
    max_index: int = 10
    width: int = 640
    height: int = 480
    source: str = "auto"


@dataclass
class InferenceConfig:
    last_model_name: str = DEFAULT_MODEL_NAME
    conf_min: float = CONF_MIN
    conf_max: float = CONF_MAX
    conf_step: float = CONF_STEP
    default_conf: float = DEFAULT_CONF
    eval_conf: float = EVAL_CONF
    imgsz: int = 640
    iou: float = 0.45
    max_det: int = 100
    agnostic_nms: bool = False


@dataclass
class PreprocessConfig:
    contrast: float = 1.0
    brightness: int = 0
    saturation: float = 1.0


@dataclass
class ClassicalPipelineConfig:
    """Classical CV stages (blur, canny) and viewport overlay toggles."""

    enabled: bool = False
    blur_kernel: int = 0
    canny_low: int = 50
    canny_high: int = 150
    show_contours: bool = False
    show_corners: bool = False
    show_warped_face: bool = False


@dataclass
class StabilityConfig:
    """Post-inference filtering and temporal stability."""

    enabled: bool = False
    min_confidence: float = 0.0
    min_box_area_px: int = 0
    reject_edge_boxes: bool = False
    duplicate_merge_iou: float = 0.5
    temporal_window: int = 5
    required_stable_votes: int = 3


@dataclass
class UiDebugConfig:
    window_name: str = WINDOW_NAME
    button_margin: int = BUTTON_MARGIN
    button_height: int = BUTTON_HEIGHT
    button_pad_x: int = BUTTON_PAD_X
    key_arrow_up: int = KEY_ARROW_UP
    key_arrow_down: int = KEY_ARROW_DOWN
    log_level: str = "INFO"


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    classical: ClassicalPipelineConfig = field(default_factory=ClassicalPipelineConfig)
    stability: StabilityConfig = field(default_factory=StabilityConfig)
    ui: UiDebugConfig = field(default_factory=UiDebugConfig)

    @classmethod
    def defaults(cls) -> "AppConfig":
        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        def section(name: str, dc_type: type):
            raw = data.get(name, {})
            if not isinstance(raw, dict):
                return dc_type()
            fields = {f.name for f in dc_type.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return dc_type(**{k: v for k, v in raw.items() if k in fields})

        def inference_section() -> InferenceConfig:
            raw = data.get("inference", {})
            if not isinstance(raw, dict):
                return InferenceConfig()
            if "last_model_name" not in raw and "default_model_name" in raw:
                raw = {**raw, "last_model_name": raw["default_model_name"]}
            fields = {f.name for f in InferenceConfig.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return InferenceConfig(**{k: v for k, v in raw.items() if k in fields})

        return cls(
            camera=section("camera", CameraConfig),
            inference=inference_section(),
            preprocess=section("preprocess", PreprocessConfig),
            classical=section("classical", ClassicalPipelineConfig),
            stability=section("stability", StabilityConfig),
            ui=section("ui", UiDebugConfig),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera": asdict(self.camera),
            "inference": asdict(self.inference),
            "preprocess": asdict(self.preprocess),
            "classical": asdict(self.classical),
            "stability": asdict(self.stability),
            "ui": asdict(self.ui),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        inf = self.inference

        def require_number(path: str, value: Any) -> bool:
            if isinstance(value, bool) or not isinstance(value, int | float):
                errors.append(f"{path} must be a number")
                return False
            return True

        def require_int(path: str, value: Any) -> bool:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{path} must be an integer")
                return False
            return True

        def require_bool(path: str, value: Any) -> bool:
            if not isinstance(value, bool):
                errors.append(f"{path} must be true or false")
                return False
            return True

        def require_str(path: str, value: Any) -> bool:
            if not isinstance(value, str):
                errors.append(f"{path} must be a string")
                return False
            return True

        conf_fields_valid = all(
            (
                require_number("inference.conf_min", inf.conf_min),
                require_number("inference.conf_max", inf.conf_max),
                require_number("inference.conf_step", inf.conf_step),
                require_number("inference.default_conf", inf.default_conf),
                require_number("inference.eval_conf", inf.eval_conf),
            )
        )
        require_str("inference.last_model_name", inf.last_model_name)
        inference_extra_valid = all(
            (
                require_int("inference.imgsz", inf.imgsz),
                require_number("inference.iou", inf.iou),
                require_int("inference.max_det", inf.max_det),
                require_bool("inference.agnostic_nms", inf.agnostic_nms),
            )
        )

        pp = self.preprocess
        preprocess_valid = all(
            (
                require_number("preprocess.contrast", pp.contrast),
                require_int("preprocess.brightness", pp.brightness),
                require_number("preprocess.saturation", pp.saturation),
            )
        )

        camera_fields_valid = all(
            (
                require_int("camera.index", self.camera.index),
                require_int("camera.max_index", self.camera.max_index),
                require_int("camera.width", self.camera.width),
                require_int("camera.height", self.camera.height),
            )
        )
        source_valid = self.camera.source in ("auto", "usb", "libcamera", "gstreamer", "rpicam")
        if not source_valid:
            errors.append("camera.source must be one of: auto, usb, libcamera, gstreamer, rpicam")

        cl = self.classical
        require_bool("classical.enabled", cl.enabled)
        require_int("classical.blur_kernel", cl.blur_kernel)
        require_int("classical.canny_low", cl.canny_low)
        require_int("classical.canny_high", cl.canny_high)
        require_bool("classical.show_contours", cl.show_contours)
        require_bool("classical.show_corners", cl.show_corners)
        require_bool("classical.show_warped_face", cl.show_warped_face)
        require_bool("stability.enabled", self.stability.enabled)
        require_number("stability.min_confidence", self.stability.min_confidence)
        require_int("stability.min_box_area_px", self.stability.min_box_area_px)
        require_bool("stability.reject_edge_boxes", self.stability.reject_edge_boxes)
        stability_iou_valid = require_number(
            "stability.duplicate_merge_iou",
            self.stability.duplicate_merge_iou,
        )
        stability_window_valid = require_int("stability.temporal_window", self.stability.temporal_window)
        stability_votes_valid = require_int(
            "stability.required_stable_votes",
            self.stability.required_stable_votes,
        )
        require_str("ui.window_name", self.ui.window_name)
        require_int("ui.button_margin", self.ui.button_margin)
        require_int("ui.button_height", self.ui.button_height)
        require_int("ui.button_pad_x", self.ui.button_pad_x)
        require_int("ui.key_arrow_up", self.ui.key_arrow_up)
        require_int("ui.key_arrow_down", self.ui.key_arrow_down)
        log_level_valid = require_str("ui.log_level", self.ui.log_level)

        if conf_fields_valid and not inf.conf_min <= inf.default_conf <= inf.conf_max:
            errors.append("inference.default_conf must be within [conf_min, conf_max]")
        if conf_fields_valid and (inf.eval_conf < inf.conf_min or inf.eval_conf > inf.conf_max):
            errors.append("inference.eval_conf must be within [conf_min, conf_max]")
        if inference_extra_valid and not 320 <= inf.imgsz <= 1280:
            errors.append("inference.imgsz must be within [320, 1280]")
        if inference_extra_valid and inf.imgsz % 32 != 0:
            errors.append("inference.imgsz must be a multiple of 32")
        if inference_extra_valid and not 0 < inf.iou <= 1:
            errors.append("inference.iou must be in (0, 1]")
        if inference_extra_valid and inf.max_det < 1:
            errors.append("inference.max_det must be >= 1")
        if preprocess_valid and not 0 <= pp.contrast <= 2:
            errors.append("preprocess.contrast must be within [0, 2]")
        if preprocess_valid and not -100 <= pp.brightness <= 100:
            errors.append("preprocess.brightness must be within [-100, 100]")
        if preprocess_valid and not 0 <= pp.saturation <= 2:
            errors.append("preprocess.saturation must be within [0, 2]")
        if camera_fields_valid and (self.camera.width < 1 or self.camera.height < 1):
            errors.append("camera width/height must be positive")
        if log_level_valid and self.ui.log_level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("ui.log_level must be a valid logging level name")
        stab = self.stability
        if stability_iou_valid and not 0 < stab.duplicate_merge_iou <= 1:
            errors.append("stability.duplicate_merge_iou must be in (0, 1]")
        if stability_window_valid and stab.temporal_window < 1:
            errors.append("stability.temporal_window must be >= 1")
        if stability_votes_valid and stab.required_stable_votes < 1:
            errors.append("stability.required_stable_votes must be >= 1")
        if (
            stability_window_valid
            and stability_votes_valid
            and stab.required_stable_votes > stab.temporal_window
        ):
            errors.append("stability.required_stable_votes must be <= temporal_window")
        if stab.min_confidence < 0 or stab.min_confidence > 1:
            errors.append("stability.min_confidence must be within [0, 1]")
        return errors

    @staticmethod
    def needs_camera_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_CAMERA_KEYS)

    @staticmethod
    def needs_detector_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_DETECTOR_KEYS)
