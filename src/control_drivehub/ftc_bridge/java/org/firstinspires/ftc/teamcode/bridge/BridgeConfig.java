package org.firstinspires.ftc.teamcode.bridge;

/**
 * Static configuration for FTCBridge.
 * Edit PI_HOST to match your Raspberry Pi on the Control Hub WiFi subnet.
 */
public final class BridgeConfig {
    public static final String PI_HOST = "192.168.49.100";
    public static final int PI_WS_PORT = 8765;
    public static final String WS_PATH = "/ws/hub";
    public static final int PUBLISH_HZ = 20;
    public static final int QUEUE_CAPACITY = 2;
    public static final long RECONNECT_BASE_MS = 500;
    public static final long RECONNECT_MAX_MS = 5000;
    public static final String COMMAND_TOKEN = "change-me";
    public static final boolean COMMANDS_ENABLED = false;

    public static final String[] MOTOR_NAMES = {
            "leftFront", "rightFront", "leftRear", "rightRear"
    };
    public static final String[] SERVO_NAMES = {"claw"};
    public static final String IMU_NAME = "imu";

    private BridgeConfig() {}
}
