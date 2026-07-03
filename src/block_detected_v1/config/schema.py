"""Typed application configuration (dataclasses + JSON-friendly dicts)."""

from dataclasses import asdict, dataclass, field
from typing import Any

from block_detected.config.defaults import (
    BUTTON_HEIGHT,
    BUTTON_MARGIN,
    BUTTON_PAD_X,
    CONF_MAX,
    CONF_MIN,
    CONF_STEP,
    DEFAULT_CONF,
    DEFAULT_MODEL_NAME,
    EVAL_CONF,
    KEY_ARROW_DOWN,
    KEY_ARROW_UP,
    WINDOW_NAME,
)
RESTART_CAMERA_KEYS = frozenset(
    {"camera.index", "camera.width", "camera.height", "camera.max_index", "camera.source"}
)
RESTART_DETECTOR_KEYS = frozenset({"inference.imgsz"})


@dataclass
class CameraConfig:
    index: int = 8
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
        from block_detected.config.validate import validate_app_config

        return validate_app_config(self)

    @staticmethod
    def needs_camera_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_CAMERA_KEYS)

    @staticmethod
    def needs_detector_restart(changed_keys: set[str]) -> bool:
        return bool(changed_keys & RESTART_DETECTOR_KEYS)
