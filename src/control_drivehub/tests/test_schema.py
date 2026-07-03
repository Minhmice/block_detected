from pi_monitor.core.schema import GamepadState, ImuState, MotorState, RobotState, TelemetryFrame


def test_telemetry_frame_roundtrip():
    frame = TelemetryFrame(
        seq=1,
        ts_hub_ms=1000,
        robot_state=RobotState.RUNNING,
        gamepad1=GamepadState(left_stick_x=0.5),
        motors=[MotorState(name="leftFront", power=0.8)],
        imu=ImuState(yaw=90.0),
        battery_v=12.5,
    )
    data = frame.model_dump(mode="json")
    restored = TelemetryFrame.model_validate(data)
    assert restored.seq == 1
    assert restored.motors[0].name == "leftFront"
    assert restored.imu.yaw == 90.0
