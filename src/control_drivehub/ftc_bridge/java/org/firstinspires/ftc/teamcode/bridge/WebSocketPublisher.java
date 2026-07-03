package org.firstinspires.ftc.teamcode.bridge;

import com.google.gson.Gson;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

/** Background WebSocket client with bounded queue and auto-reconnect. */
public class WebSocketPublisher implements Runnable {
    private static final Gson GSON = new Gson();

    private final ArrayBlockingQueue<TelemetrySnapshot> queue =
            new ArrayBlockingQueue<>(BridgeConfig.QUEUE_CAPACITY);
    private final AtomicBoolean running = new AtomicBoolean(false);
    private final AtomicBoolean connected = new AtomicBoolean(false);
    private final CommandReceiver commandReceiver;
    private Thread thread;
    private OkHttpClient client;
    private WebSocket webSocket;

    public WebSocketPublisher(CommandReceiver commandReceiver) {
        this.commandReceiver = commandReceiver;
    }

    public void start() {
        if (running.getAndSet(true)) {
            return;
        }
        client = new OkHttpClient.Builder()
                .pingInterval(10, TimeUnit.SECONDS)
                .build();
        thread = new Thread(this, "FTCBridge-WS");
        thread.setDaemon(true);
        thread.start();
    }

    public void stop() {
        running.set(false);
        if (webSocket != null) {
            webSocket.close(1000, "shutdown");
        }
        if (thread != null) {
            thread.interrupt();
        }
    }

    public void enqueue(TelemetrySnapshot snapshot) {
        if (!running.get()) {
            return;
        }
        if (!queue.offer(snapshot)) {
            queue.poll();
            queue.offer(snapshot);
        }
    }

    public boolean isConnected() {
        return connected.get();
    }

    @Override
    public void run() {
        long backoff = BridgeConfig.RECONNECT_BASE_MS;
        while (running.get()) {
            try {
                connectAndSend();
                backoff = BridgeConfig.RECONNECT_BASE_MS;
            } catch (Exception ignored) {
            }
            connected.set(false);
            try {
                Thread.sleep(backoff);
            } catch (InterruptedException e) {
                if (!running.get()) {
                    break;
                }
            }
            backoff = Math.min(backoff * 2, BridgeConfig.RECONNECT_MAX_MS);
        }
    }

    private void connectAndSend() throws InterruptedException {
        String url = "ws://" + BridgeConfig.PI_HOST + ":" + BridgeConfig.PI_WS_PORT + BridgeConfig.WS_PATH;
        Request request = new Request.Builder().url(url).build();
        final Object latch = new Object();
        final boolean[] open = {false};

        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                connected.set(true);
                open[0] = true;
                synchronized (latch) {
                    latch.notifyAll();
                }
            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                commandReceiver.handleIncoming(text);
            }

            @Override
            public void onClosing(WebSocket webSocket, int code, String reason) {
                connected.set(false);
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                connected.set(false);
                synchronized (latch) {
                    latch.notifyAll();
                }
            }
        });

        synchronized (latch) {
            if (!open[0]) {
                latch.wait(3000);
            }
        }

        while (running.get() && connected.get()) {
            TelemetrySnapshot snap = queue.poll(100, TimeUnit.MILLISECONDS);
            if (snap == null) {
                continue;
            }
            snap.piConnected = connected.get();
            String json = GSON.toJson(snap);
            if (!webSocket.send(json)) {
                break;
            }
        }
    }
}
