"""Robot navigation state machine — điều hướng robot tiếp cận block.

States:
    SEARCHING      → tìm block, quay phải nếu không thấy
    APPROACHING    → tiến thẳng đến block (mecanum: forward)
    AT_TARGET      → đã đến vị trí cách block 2cm
    BACKING_UP     → lùi lại 10cm
    SHIFTING_RIGHT → sang phải đến khi thấy block mới
"""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass

from block_detected.core.domain import Detection

logger = logging.getLogger(__name__)


class NavState(enum.Enum):
    SEARCHING = "SEARCHING"
    APPROACHING = "APPROACHING"
    AT_TARGET = "AT_TARGET"
    BACKING_UP = "BACKING_UP"
    SHIFTING_RIGHT = "SHIFTING_RIGHT"


@dataclass
class RobotNavConfig:
    """Config for robot navigation behaviour."""

    enabled: bool = False
    target_distance_cm: float = 2.0
    backup_distance_cm: float = 10.0
    approach_speed: int = 120       # 0-255 PWM
    strafe_speed: int = 100
    rotation_speed: int = 100
    search_rotation_ms: int = 200
    shift_distance_cm: float = 15.0
    align_threshold_deg: float = 5.0


@dataclass
class RobotCommand:
    """A single robot movement command to send via UART."""

    CMD_FORWARD = 0x01
    CMD_BACKWARD = 0x02
    CMD_LEFT = 0x03
    CMD_RIGHT = 0x04
    CMD_STOP = 0x05
    CMD_ROTATE_LEFT = 0x06
    CMD_ROTATE_RIGHT = 0x07

    command: int
    speed: int = 0  # 0-255

    @classmethod
    def stop(cls) -> RobotCommand:
        return cls(command=cls.CMD_STOP, speed=0)

    @classmethod
    def forward(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_FORWARD, speed=min(255, max(0, speed)))

    @classmethod
    def backward(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_BACKWARD, speed=min(255, max(0, speed)))

    @classmethod
    def strafe_right(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_RIGHT, speed=min(255, max(0, speed)))

    @classmethod
    def strafe_left(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_LEFT, speed=min(255, max(0, speed)))

    @classmethod
    def rotate_right(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_ROTATE_RIGHT, speed=min(255, max(0, speed)))

    @classmethod
    def rotate_left(cls, speed: int) -> RobotCommand:
        return cls(command=cls.CMD_ROTATE_LEFT, speed=min(255, max(0, speed)))


class RobotNavigator:
    """State machine điều khiển robot tiếp cận block."""

    def __init__(self, config: RobotNavConfig | None = None) -> None:
        self.config = config or RobotNavConfig()
        self._state: NavState = NavState.SEARCHING
        self._state_start: float = time.monotonic()
        self._command_queue: list[RobotCommand] = []
        self._last_command: RobotCommand = RobotCommand.stop()
        self._cycle_count: int = 0

        # Current detection info (set each frame)
        self.primary_detection: Detection | None = None
        self.distance_cm: float = 999.0
        self.angle_deg: float = 0.0
        self.frame_width: int = 640

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        primary: Detection | None,
        distance_cm: float,
        angle_deg: float,
        frame_width: int,
    ) -> list[RobotCommand]:
        """Feed latest detection → returns list of commands to send."""
        self.primary_detection = primary
        self.distance_cm = distance_cm
        self.angle_deg = angle_deg
        self.frame_width = frame_width

        if not self.config.enabled:
            return [RobotCommand.stop()]

        self._command_queue.clear()
        self._tick()
        return list(self._command_queue)

    @property
    def state(self) -> NavState:
        return self._state

    @property
    def state_label(self) -> str:
        labels = {
            NavState.SEARCHING: "SEARCHING...",
            NavState.APPROACHING: "APPROACHING",
            NavState.AT_TARGET: "TARGET REACHED",
            NavState.BACKING_UP: "BACKING UP",
            NavState.SHIFTING_RIGHT: "SHIFTING RIGHT",
        }
        return labels.get(self._state, str(self._state))

    def reset(self) -> None:
        self._state = NavState.SEARCHING
        self._state_start = time.monotonic()
        self._command_queue.clear()
        self._last_command = RobotCommand.stop()
        self._cycle_count = 0

    # ------------------------------------------------------------------
    # State machine tick
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        handler = {
            NavState.SEARCHING: self._handle_searching,
            NavState.APPROACHING: self._handle_approaching,
            NavState.AT_TARGET: self._handle_at_target,
            NavState.BACKING_UP: self._handle_backing_up,
            NavState.SHIFTING_RIGHT: self._handle_shifting_right,
        }
        handler[self._state]()

    def _transition(self, new_state: NavState) -> None:
        logger.info("Nav: %s → %s", self._state.value, new_state.value)
        self._state = new_state
        self._state_start = time.monotonic()

    def _elapsed(self) -> float:
        return time.monotonic() - self._state_start

    def _is_aligned(self) -> bool:
        return abs(self.angle_deg) <= self.config.align_threshold_deg

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_searching(self) -> None:
        """Tìm block: có block → APPROACHING, không có → xoay phải."""
        if (
            self.primary_detection is not None
            and self.distance_cm > self.config.target_distance_cm
        ):
            self._transition(NavState.APPROACHING)
            return

        # No block → rotate right to scan
        self._cmd(RobotCommand.rotate_right(self.config.rotation_speed))

    def _handle_approaching(self) -> None:
        """Tiến đến block, căn chỉnh góc, dừng ở target_distance_cm."""
        if self.primary_detection is None:
            self._cmd(RobotCommand.stop())
            self._transition(NavState.SEARCHING)
            return

        if self.distance_cm <= self.config.target_distance_cm:
            self._cmd(RobotCommand.stop())
            self._transition(NavState.AT_TARGET)
            return

        cfg = self.config

        if self.angle_deg > cfg.align_threshold_deg:
            speed = min(cfg.rotation_speed, int(abs(self.angle_deg) * 5))
            self._cmd(RobotCommand.rotate_right(max(60, speed)))
        elif self.angle_deg < -cfg.align_threshold_deg:
            speed = min(cfg.rotation_speed, int(abs(self.angle_deg) * 5))
            self._cmd(RobotCommand.rotate_left(max(60, speed)))
        else:
            dist_factor = min(1.0, self.distance_cm / 30.0)
            speed = int(cfg.approach_speed * max(0.3, dist_factor))
            self._cmd(RobotCommand.forward(speed))

    def _handle_at_target(self) -> None:
        """Đã đến vị trí. Dừng 0.5s → BACKING_UP."""
        self._cmd(RobotCommand.stop())
        if self._elapsed() > 0.5:
            self._transition(NavState.BACKING_UP)

    def _handle_backing_up(self) -> None:
        """Lùi backup_distance_cm. Dùng thời gian ước lượng."""
        cfg = self.config
        speed_ratio = cfg.approach_speed / 255.0
        estimated_speed_cm_s = 15.0 * speed_ratio
        required_time = cfg.backup_distance_cm / max(estimated_speed_cm_s, 1.0)

        if self._elapsed() < required_time:
            self._cmd(RobotCommand.backward(cfg.approach_speed))
        else:
            self._cmd(RobotCommand.stop())
            self._cycle_count += 1
            logger.info(
                "Nav: cycle %d — backed up %.1f cm",
                self._cycle_count,
                cfg.backup_distance_cm,
            )
            self._transition(NavState.SHIFTING_RIGHT)

    def _handle_shifting_right(self) -> None:
        """Sang phải shift_distance_cm → SEARCHING."""
        cfg = self.config
        speed_ratio = cfg.strafe_speed / 255.0
        estimated_speed_cm_s = 10.0 * speed_ratio
        required_time = cfg.shift_distance_cm / max(estimated_speed_cm_s, 0.5)

        if self._elapsed() < required_time:
            self._cmd(RobotCommand.strafe_right(cfg.strafe_speed))
        else:
            self._cmd(RobotCommand.stop())
            logger.info(
                "Nav: shifted right %.1f cm → SEARCHING",
                cfg.shift_distance_cm,
            )
            self._transition(NavState.SEARCHING)

    # ------------------------------------------------------------------
    # Command queue helper
    # ------------------------------------------------------------------

    def _cmd(self, cmd: RobotCommand) -> None:
        """Enqueue command. Dedup: skip if same as last sent."""
        if (
            cmd.command != self._last_command.command
            or cmd.speed != self._last_command.speed
        ):
            self._command_queue.append(cmd)
            self._last_command = cmd

    def get_status_text(self) -> str:
        """One-line status for GUI overlay."""
        dist = f"{self.distance_cm:.1f}cm" if self.distance_cm < 999 else "--"
        ang = f"{self.angle_deg:+.0f}deg"
        cyc = self._cycle_count
        return f"Robot [{self.state_label}] dist:{dist} ang:{ang} cycle:{cyc}"
