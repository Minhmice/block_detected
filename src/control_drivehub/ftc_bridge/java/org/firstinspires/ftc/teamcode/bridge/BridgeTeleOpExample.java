package org.firstinspires.ftc.teamcode.bridge;

import com.qualcomm.robotcore.eventloop.opmode.LinearOpMode;
import com.qualcomm.robotcore.eventloop.opmode.TeleOp;
import com.qualcomm.robotcore.hardware.DcMotor;
import com.qualcomm.robotcore.hardware.IMU;

/**
 * Example TeleOp demonstrating FTCBridge integration.
 * Configure motor names in BridgeConfig to match your robot.
 */
@TeleOp(name = "Bridge TeleOp Example", group = "Bridge")
public class BridgeTeleOpExample extends LinearOpMode {
    private IMU imu;

    @Override
    public void runOpMode() {
        FTCBridge bridge = FTCBridge.getInstance();
        bridge.onInit();
        bridge.start();

        imu = TelemetryCollector.getImu(hardwareMap);

        telemetry.addLine("FTCBridge example — connect Pi before START");
        telemetry.update();

        waitForStart();
        bridge.onRunning();

        long loopStart = System.nanoTime();
        while (opModeIsActive()) {
            long loopNs = System.nanoTime() - loopStart;
            loopStart = System.nanoTime();
            double loopMs = loopNs / 1_000_000.0;

            bridge.applyEmergencyStop(hardwareMap);

            if (!bridge.isEmergencyStop()) {
                double drive = -gamepad1.left_stick_y;
                double turn = gamepad1.right_stick_x;
                setDrive(drive + turn, drive - turn);
            }

            bridge.publish(hardwareMap, gamepad1, gamepad2, imu, loopMs, true);
            bridge.logStatus(telemetry);
            telemetry.update();
        }

        bridge.onStopped();
        bridge.stop();
        setDrive(0, 0);
    }

    private void setDrive(double left, double right) {
        try {
            DcMotor lf = hardwareMap.get(DcMotor.class, "leftFront");
            DcMotor rf = hardwareMap.get(DcMotor.class, "rightFront");
            lf.setPower(left);
            rf.setPower(right);
        } catch (Exception ignored) {
        }
    }
}
