"""Pydantic models for telemetry protocol v1."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RobotState(str, Enum):
    INIT = "INIT"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class GamepadState(BaseModel):
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    dpad_up: bool = False
    dpad_down: bool = False
    dpad_left: bool = False
    dpad_right: bool = False
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    left_bumper: bool = False
    right_bumper: bool = False
    back: bool = False
    start: bool = False
    guide: bool = False
    left_stick_button: bool = False
    right_stick_button: bool = False


class MotorState(BaseModel):
    name: str
    power: float = 0.0
    encoder: int = 0
    velocity: float = 0.0
    current: float = 0.0
    target: int = 0
    mode: str = "UNKNOWN"


class ServoState(BaseModel):
    name: str
    position: float = 0.0


class ImuState(BaseModel):
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    angular_velocity_x: float = 0.0
    angular_velocity_y: float = 0.0
    angular_velocity_z: float = 0.0


class TelemetryFrame(BaseModel):
    v: int = 1
    seq: int = 0
    ts_hub_ms: int = 0
    heartbeat: bool = True
    loop_time_ms: float = 0.0
    robot_state: RobotState = RobotState.INIT
    driver_hub_connected: bool = False
    pi_connected: bool = False
    gamepad1: GamepadState = Field(default_factory=GamepadState)
    gamepad2: GamepadState = Field(default_factory=GamepadState)
    motors: list[MotorState] = Field(default_factory=list)
    servos: list[ServoState] = Field(default_factory=list)
    imu: ImuState = Field(default_factory=ImuState)
    battery_v: float = 0.0
    sensors: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = None


class CommandRequest(BaseModel):
    v: int = 1
    type: str
    token: str = ""
    ts: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    hub_connected: bool
    dashboard_clients: int
    stale: bool
    last_seq: int | None
    last_ts_hub_ms: int | None
    latency_ms: float | None
    robot_state: RobotState | None
    driver_hub_connected: bool | None
    received_at_ms: int | None


class DashboardEnvelope(BaseModel):
    stale: bool
    received_at_ms: int
    frame: TelemetryFrame | None = None
