package org.firstinspires.ftc.teamcode.bridge;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Telemetry frame serialized to JSON protocol v1. */
public class TelemetrySnapshot {
    public int v = 1;
    public long seq;
    @SerializedName("ts_hub_ms")
    public long tsHubMs;
    public boolean heartbeat = true;
    @SerializedName("loop_time_ms")
    public double loopTimeMs;
    @SerializedName("robot_state")
    public String robotState = "INIT";
    @SerializedName("driver_hub_connected")
    public boolean driverHubConnected;
    @SerializedName("pi_connected")
    public boolean piConnected;
    public GamepadSnapshot gamepad1 = new GamepadSnapshot();
    public GamepadSnapshot gamepad2 = new GamepadSnapshot();
    public List<MotorSnapshot> motors = new ArrayList<>();
    public List<ServoSnapshot> servos = new ArrayList<>();
    public ImuSnapshot imu = new ImuSnapshot();
    @SerializedName("battery_v")
    public double batteryV;
    public Map<String, Object> sensors = new HashMap<>();

    public static class GamepadSnapshot {
        @SerializedName("left_stick_x") public double leftStickX;
        @SerializedName("left_stick_y") public double leftStickY;
        @SerializedName("right_stick_x") public double rightStickX;
        @SerializedName("right_stick_y") public double rightStickY;
        @SerializedName("left_trigger") public double leftTrigger;
        @SerializedName("right_trigger") public double rightTrigger;
        @SerializedName("dpad_up") public boolean dpadUp;
        @SerializedName("dpad_down") public boolean dpadDown;
        @SerializedName("dpad_left") public boolean dpadLeft;
        @SerializedName("dpad_right") public boolean dpadRight;
        public boolean a, b, x, y;
        @SerializedName("left_bumper") public boolean leftBumper;
        @SerializedName("right_bumper") public boolean rightBumper;
        public boolean back, start, guide;
        @SerializedName("left_stick_button") public boolean leftStickButton;
        @SerializedName("right_stick_button") public boolean rightStickButton;
    }

    public static class MotorSnapshot {
        public String name;
        public double power;
        public int encoder;
        public double velocity;
        public double current;
        public int target;
        public String mode;
    }

    public static class ServoSnapshot {
        public String name;
        public double position;
    }

    public static class ImuSnapshot {
        public double yaw, pitch, roll;
        @SerializedName("angular_velocity_x") public double angularVelocityX;
        @SerializedName("angular_velocity_y") public double angularVelocityY;
        @SerializedName("angular_velocity_z") public double angularVelocityZ;
    }
}
