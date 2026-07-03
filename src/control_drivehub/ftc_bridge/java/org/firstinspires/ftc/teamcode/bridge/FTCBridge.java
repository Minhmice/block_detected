package org.firstinspires.ftc.teamcode.bridge;

import com.qualcomm.robotcore.hardware.DcMotor;
import com.qualcomm.robotcore.hardware.Gamepad;
import com.qualcomm.robotcore.hardware.HardwareMap;
import com.qualcomm.robotcore.hardware.IMU;

import org.firstinspires.ftc.robotcore.external.Telemetry;

/** Facade: start/stop bridge, publish snapshots, emergency stop. */
public final class FTCBridge {
    private static final FTCBridge INSTANCE = new FTCBridge();

    private final TelemetryCollector collector = new TelemetryCollector();
    private final CommandReceiver commandReceiver = new CommandReceiver();
    private final WebSocketPublisher publisher = new WebSocketPublisher(commandReceiver);
    private long lastPublishNs;
    private long publishIntervalNs = 1_000_000_000L / BridgeConfig.PUBLISH_HZ;

    private FTCBridge() {}

    public static FTCBridge getInstance() {
        return INSTANCE;
    }

    public void start() {
        publisher.start();
    }

    public void stop() {
        publisher.stop();
    }

    public boolean isEmergencyStop() {
        return commandReceiver.isEmergencyStop();
    }

    public void applyEmergencyStop(HardwareMap hardwareMap) {
        if (!commandReceiver.isEmergencyStop()) {
            return;
        }
        for (String name : BridgeConfig.MOTOR_NAMES) {
            try {
                DcMotor motor = hardwareMap.get(DcMotor.class, name);
                motor.setPower(0);
            } catch (Exception ignored) {
            }
        }
    }

    public void onInit() {
        collector.tracker().onInit();
    }

    public void onRunning() {
        collector.tracker().onRunning();
    }

    public void onStopped() {
        collector.tracker().onStopped();
    }

    /** Call once per OpMode loop. Throttles to PUBLISH_HZ. */
    public void publish(HardwareMap hardwareMap,
                        Gamepad gamepad1,
                        Gamepad gamepad2,
                        IMU imu,
                        double loopTimeMs,
                        boolean opModeStarted) {
        applyEmergencyStop(hardwareMap);
        long now = System.nanoTime();
        if (now - lastPublishNs < publishIntervalNs) {
            return;
        }
        lastPublishNs = now;
        TelemetrySnapshot snap = collector.collect(
                hardwareMap, gamepad1, gamepad2, imu, loopTimeMs, opModeStarted);
        publisher.enqueue(snap);
    }

    public void logStatus(Telemetry telemetry) {
        telemetry.addData("Bridge WS", publisher.isConnected() ? "connected" : "reconnecting");
        telemetry.addData("E-Stop", commandReceiver.isEmergencyStop());
    }
}
