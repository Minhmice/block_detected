"""Fake telemetry generator for simulator mode."""

from __future__ import annotations

import asyncio
import math
import time
from typing import TYPE_CHECKING

from pi_monitor.core.schema import (
    GamepadState,
    ImuState,
    MotorState,
    RobotState,
    ServoState,
    TelemetryFrame,
)

if TYPE_CHECKING:
    from pi_monitor.core.config import AppConfig
    from pi_monitor.core.state import TelemetryState


async def run_simulator(config: AppConfig, state: TelemetryState, jsonl_writer, csv_writer) -> None:
    interval = 1.0 / max(1, config.telemetry.rate_hz)
    seq = 0
    t0 = time.time()
    motor_names = config.hardware_names.motors or ["leftFront", "rightFront"]
    servo_names = config.hardware_names.servos or ["claw"]

    while True:
        seq += 1
        elapsed = time.time() - t0
        wave = math.sin(elapsed * 2.0)
        motors = [
            MotorState(
                name=name,
                power=round(wave * 0.8, 3),
                encoder=int(elapsed * 100 * (idx + 1)),
                velocity=round(wave * 120, 2),
                current=round(abs(wave) * 2.5, 2),
                target=int(wave * 500),
                mode="RUN_USING_ENCODER",
            )
            for idx, name in enumerate(motor_names)
        ]
        servos = [
            ServoState(name=name, position=round(0.5 + wave * 0.2, 3))
            for name in servo_names
        ]
        frame = TelemetryFrame(
            seq=seq,
            ts_hub_ms=int(time.time() * 1000),
            heartbeat=True,
            loop_time_ms=12.5,
            robot_state=RobotState.RUNNING,
            driver_hub_connected=True,
            pi_connected=True,
            gamepad1=GamepadState(
                left_stick_x=round(wave * 0.5, 3),
                left_stick_y=round(math.cos(elapsed) * 0.5, 3),
                a=seq % 40 < 5,
            ),
            gamepad2=GamepadState(right_trigger=round(abs(wave), 3)),
            motors=motors,
            servos=servos,
            imu=ImuState(
                yaw=round(elapsed * 15 % 360, 2),
                pitch=round(wave * 5, 2),
                roll=round(math.cos(elapsed) * 3, 2),
                angular_velocity_z=round(wave * 30, 2),
            ),
            battery_v=12.4,
            sensors={"distance_in": round(24 + wave * 2, 2)},
        )
        payload = frame.model_dump(mode="json")
        ingested = await state.ingest(payload)
        state.hub_connected = True
        jsonl_writer.write(ingested)
        csv_writer.write(ingested)
        await state.broadcast_dashboard()
        await asyncio.sleep(interval)
