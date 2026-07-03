package org.firstinspires.ftc.teamcode.bridge;

import com.qualcomm.hardware.rev.RevHubOrientationOnRobot;
import com.qualcomm.robotcore.hardware.DcMotor;
import com.qualcomm.robotcore.hardware.DcMotorEx;
import com.qualcomm.robotcore.hardware.Gamepad;
import com.qualcomm.robotcore.hardware.HardwareMap;
import com.qualcomm.robotcore.hardware.IMU;
import com.qualcomm.robotcore.hardware.Servo;
import com.qualcomm.robotcore.hardware.VoltageSensor;

import org.firstinspires.ftc.robotcore.external.navigation.AngleUnit;
import org.firstinspires.ftc.robotcore.external.navigation.CurrentUnit;
import org.firstinspires.ftc.robotcore.external.navigation.YawPitchRollAngles;

/** Collects telemetry using public FTC SDK APIs only. */
public class TelemetryCollector {
    private final RobotStateTracker tracker = new RobotStateTracker();
    private long seq;

    public RobotStateTracker tracker() {
        return tracker;
    }

    public TelemetrySnapshot collect(HardwareMap hardwareMap,
                                     Gamepad gamepad1,
                                     Gamepad gamepad2,
                                     IMU imu,
                                     double loopTimeMs,
                                     boolean opModeStarted) {
        tracker.noteGamepadActivity(gamepad1, gamepad2, opModeStarted);

        TelemetrySnapshot snap = new TelemetrySnapshot();
        snap.seq = ++seq;
        snap.tsHubMs = System.currentTimeMillis();
        snap.loopTimeMs = loopTimeMs;
        snap.robotState = tracker.stateName();
        snap.driverHubConnected = tracker.isDriverHubConnected();
        snap.piConnected = false;
        snap.gamepad1 = fromGamepad(gamepad1);
        snap.gamepad2 = fromGamepad(gamepad2);
        snap.motors = collectMotors(hardwareMap);
        snap.servos = collectServos(hardwareMap);
        snap.imu = collectImu(imu);
        snap.batteryV = collectBattery(hardwareMap);
        return snap;
    }

    private TelemetrySnapshot.GamepadSnapshot fromGamepad(Gamepad gp) {
        TelemetrySnapshot.GamepadSnapshot g = new TelemetrySnapshot.GamepadSnapshot();
        g.leftStickX = gp.left_stick_x;
        g.leftStickY = gp.left_stick_y;
        g.rightStickX = gp.right_stick_x;
        g.rightStickY = gp.right_stick_y;
        g.leftTrigger = gp.left_trigger;
        g.rightTrigger = gp.right_trigger;
        g.dpadUp = gp.dpad_up;
        g.dpadDown = gp.dpad_down;
        g.dpadLeft = gp.dpad_left;
        g.dpadRight = gp.dpad_right;
        g.a = gp.a;
        g.b = gp.b;
        g.x = gp.x;
        g.y = gp.y;
        g.leftBumper = gp.left_bumper;
        g.rightBumper = gp.right_bumper;
        g.back = gp.back;
        g.start = gp.start;
        g.guide = gp.guide;
        g.leftStickButton = gp.left_stick_button;
        g.rightStickButton = gp.right_stick_button;
        return g;
    }

    private java.util.List<TelemetrySnapshot.MotorSnapshot> collectMotors(HardwareMap map) {
        java.util.List<TelemetrySnapshot.MotorSnapshot> list = new java.util.ArrayList<>();
        for (String name : BridgeConfig.MOTOR_NAMES) {
            try {
                DcMotor motor = map.get(DcMotor.class, name);
                TelemetrySnapshot.MotorSnapshot m = new TelemetrySnapshot.MotorSnapshot();
                m.name = name;
                m.power = motor.getPower();
                m.encoder = motor.getCurrentPosition();
                m.velocity = motor.getVelocity();
                m.mode = motor.getMode() != null ? motor.getMode().name() : "UNKNOWN";
                if (motor instanceof DcMotorEx) {
                    DcMotorEx ex = (DcMotorEx) motor;
                    m.current = ex.getCurrent(CurrentUnit.AMPS);
                    m.target = ex.getTargetPosition();
                }
                list.add(m);
            } catch (Exception ignored) {
                // motor not configured in this robot
            }
        }
        return list;
    }

    private java.util.List<TelemetrySnapshot.ServoSnapshot> collectServos(HardwareMap map) {
        java.util.List<TelemetrySnapshot.ServoSnapshot> list = new java.util.ArrayList<>();
        for (String name : BridgeConfig.SERVO_NAMES) {
            try {
                Servo servo = map.get(Servo.class, name);
                TelemetrySnapshot.ServoSnapshot s = new TelemetrySnapshot.ServoSnapshot();
                s.name = name;
                s.position = servo.getPosition();
                list.add(s);
            } catch (Exception ignored) {
            }
        }
        return list;
    }

    private TelemetrySnapshot.ImuSnapshot collectImu(IMU imu) {
        TelemetrySnapshot.ImuSnapshot out = new TelemetrySnapshot.ImuSnapshot();
        if (imu == null) {
            return out;
        }
        try {
            YawPitchRollAngles angles = imu.getRobotYawPitchRollAngles();
            out.yaw = angles.getYaw(AngleUnit.DEGREES);
            out.pitch = angles.getPitch(AngleUnit.DEGREES);
            out.roll = angles.getRoll(AngleUnit.DEGREES);
            org.firstinspires.ftc.robotcore.external.navigation.AngularVelocity vel =
                    imu.getRobotAngularVelocity(AngleUnit.DEGREES);
            out.angularVelocityX = vel.xRotationRate;
            out.angularVelocityY = vel.yRotationRate;
            out.angularVelocityZ = vel.zRotationRate;
        } catch (Exception ignored) {
        }
        return out;
    }

    private double collectBattery(HardwareMap map) {
        double max = 0;
        for (VoltageSensor sensor : map.voltageSensor) {
            max = Math.max(max, sensor.getVoltage());
        }
        return max;
    }

    /** Helper for OpModes that need to initialize IMU once. */
    public static IMU getImu(HardwareMap map) {
        try {
            IMU imu = map.get(IMU.class, BridgeConfig.IMU_NAME);
            IMU.Parameters params = new IMU.Parameters(
                    new RevHubOrientationOnRobot(
                            RevHubOrientationOnRobot.LogoFacingDirection.UP,
                            RevHubOrientationOnRobot.UsbFacingDirection.FORWARD
                    )
            );
            imu.initialize(params);
            return imu;
        } catch (Exception e) {
            return null;
        }
    }
}
