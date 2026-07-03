package org.firstinspires.ftc.teamcode.bridge;

/** Tracks OpMode lifecycle and Driver Hub connection heuristics. */
public class RobotStateTracker {
    public enum State {
        INIT, RUNNING, STOPPED
    }

    private State state = State.INIT;
    private boolean driverHubConnected;
    private long lastGamepadActivityMs;

    public void onInit() {
        state = State.INIT;
    }

    public void onRunning() {
        state = State.RUNNING;
    }

    public void onStopped() {
        state = State.STOPPED;
    }

    public void noteGamepadActivity(com.qualcomm.robotcore.hardware.Gamepad gp1,
                                    com.qualcomm.robotcore.hardware.Gamepad gp2,
                                    boolean opModeStarted) {
        if (gp1.atRest() && gp2.atRest()) {
            driverHubConnected = opModeStarted;
        } else {
            driverHubConnected = true;
            lastGamepadActivityMs = System.currentTimeMillis();
        }
        if (opModeStarted && lastGamepadActivityMs == 0) {
            driverHubConnected = true;
        }
    }

    public String stateName() {
        return state.name();
    }

    public boolean isDriverHubConnected() {
        return driverHubConnected;
    }
}
