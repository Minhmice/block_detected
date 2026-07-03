# FTCBridge — Gradle Setup

Copy the `java/org/firstinspires/ftc/teamcode/bridge/` package into your Android Studio **TeamCode** module:

```
TeamCode/src/main/java/org/firstinspires/ftc/teamcode/bridge/
```

## Dependencies

Add to `TeamCode/build.gradle` inside `dependencies { ... }`:

```gradle
implementation 'com.squareup.okhttp3:okhttp:4.12.0'
implementation 'com.google.code.gson:gson:2.11.0'
```

Sync Gradle, rebuild, deploy to Control Hub.

## Configuration

Edit constants in `BridgeConfig.java` before deploying:

| Constant | Description |
|----------|-------------|
| `PI_HOST` | Raspberry Pi IP on Control Hub WiFi (e.g. `192.168.49.100`) |
| `PI_WS_PORT` | Pi hub WebSocket port (default `8765`) |
| `PUBLISH_HZ` | Telemetry rate (default `20`) |
| `COMMAND_TOKEN` | Must match Pi `commands.token` in YAML |

## Integration

At the end of your OpMode loop:

```java
FTCBridge.getInstance().publish(this, hardwareMap, gamepad1, gamepad2, imu, loopTimeMs);
```

If emergency stop is active, zero motor power before your drive logic:

```java
if (FTCBridge.getInstance().isEmergencyStop()) {
    // stop all configured motors
}
```

## OpMode sample

Run `BridgeTeleOpExample` from the Driver Station to verify connectivity.

## Safety

- Network runs on a **daemon thread** with a bounded queue (capacity 2).
- Commands are **disabled by default** on Pi; only whitelisted types with matching token are accepted.
- **No automatic motor control** when Pi heartbeat is lost.

Do **not** modify `FtcRobotController` SDK sources.
