package org.firstinspires.ftc.teamcode.bridge;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

/** Validates and applies whitelisted commands from Pi. */
public class CommandReceiver {
    private static final Set<String> DEFAULT_WHITELIST =
            new HashSet<>(Arrays.asList("emergency_stop"));

    private final AtomicBoolean emergencyStop = new AtomicBoolean(false);

    public boolean isEmergencyStop() {
        return emergencyStop.get();
    }

    public void clearEmergencyStop() {
        emergencyStop.set(false);
    }

    public void handleIncoming(String json) {
        if (!BridgeConfig.COMMANDS_ENABLED) {
            return;
        }
        try {
            JsonObject obj = JsonParser.parseString(json).getAsJsonObject();
            String type = obj.has("type") ? obj.get("type").getAsString() : "";
            String token = obj.has("token") ? obj.get("token").getAsString() : "";
            if (!BridgeConfig.COMMAND_TOKEN.equals(token)) {
                return;
            }
            if (!DEFAULT_WHITELIST.contains(type)) {
                return;
            }
            if ("emergency_stop".equals(type)) {
                emergencyStop.set(true);
            }
        } catch (Exception ignored) {
        }
    }
}
