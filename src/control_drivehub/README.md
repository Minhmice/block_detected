# Control DriveHub Monitor

Hệ thống giám sát **REV Control Hub** và **Driver Hub** qua **Raspberry Pi 5**.

- **FTCBridge** (Java, TeamCode): gửi telemetry JSON 20 Hz qua WebSocket tới Pi
- **PiMonitor** (Python 3.11, FastAPI): nhận telemetry, ghi log, fan-out tới dashboard
- **Dashboard** (Next.js): UI realtime, biểu đồ, logs, emergency stop

Không sửa Driver Station APK. Không dùng API nội bộ FTC.

## Yêu cầu

| Thành phần | Phiên bản |
|------------|-----------|
| FTC SDK | Hiện hành (DECODE 2025-2026+) |
| Raspberry Pi OS | 64-bit |
| Python | 3.11+ |
| Node.js | 20+ |

## Cấu trúc

```
src/control_drivehub/
├── ftc_bridge/       # Copy Java vào TeamCode
├── pi_monitor/       # FastAPI server
├── dashboard/        # Next.js UI
├── deploy/           # systemd + install-pi.sh
├── scripts/          # dev / fake hub client
└── tests/
```

## Cài đặt Raspberry Pi 5

### 1. Mạng

1. Pi 5 kết nối Wi-Fi do Control Hub phát (robot LAN)
2. Gán IP tĩnh cho Pi (ví dụ `192.168.49.100`)
3. Mở port: `8765` (hub WS), `8080` (API), `3000` (dashboard)

### 2. Cài PiMonitor + Dashboard

```bash
cd src/control_drivehub
bash deploy/install-pi.sh
```

Hoặc thủ công:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r pi_monitor/requirements.txt
cp pi_monitor/config.example.yaml pi_monitor/config.yaml
# sửa config.yaml: logging.dir, commands.token

export PYTHONPATH=$PWD
python -m pi_monitor serve --config pi_monitor/config.yaml
```

Dashboard:

```bash
cd dashboard
npm ci
NEXT_PUBLIC_API_URL=http://<pi-ip>:8080 npm run build
npm run start
```

### 3. Chế độ simulator (không cần robot)

```bash
export PYTHONPATH=src/control_drivehub
python -m pi_monitor simulate --config pi_monitor/config.example.yaml
```

Hoặc: `bash scripts/run_simulator.sh`

### 4. Chạy dev (API + simulator + Next.js)

```bash
bash scripts/run_dev.sh
```

Dashboard: http://localhost:3000

## Cài đặt Control Hub

### 1. Copy Java

Copy thư mục:

`ftc_bridge/java/org/firstinspires/ftc/teamcode/bridge/`

vào:

`TeamCode/src/main/java/org/firstinspires/ftc/teamcode/bridge/`

### 2. Gradle

Xem [`ftc_bridge/README_GRADLE.md`](ftc_bridge/README_GRADLE.md).

Thêm OkHttp + Gson vào `TeamCode/build.gradle`, sync, deploy.

### 3. Cấu hình

Sửa `BridgeConfig.java`:

- `PI_HOST` = IP Pi trên robot WiFi
- `PI_WS_PORT` = `8765`
- `COMMAND_TOKEN` = khớp với `commands.token` trên Pi

### 4. Tích hợp OpMode

```java
FTCBridge bridge = FTCBridge.getInstance();
bridge.onInit();
bridge.start();

waitForStart();
bridge.onRunning();

while (opModeIsActive()) {
    bridge.applyEmergencyStop(hardwareMap);
    // ... robot logic ...
    bridge.publish(hardwareMap, gamepad1, gamepad2, imu, loopTimeMs, true);
}

bridge.onStopped();
bridge.stop();
```

Chạy OpMode mẫu **Bridge TeleOp Example** để kiểm tra.

## Giao thức

Control Hub (client) → `ws://<pi>:8765/ws/hub`

Dashboard (browser) → `ws://<pi>:8080/ws/dashboard`

Telemetry 20 Hz, stale nếu không nhận packet trong **1 giây**.

## An toàn

- Mặc định **chỉ đọc** (`commands.enabled: false`)
- Lệnh cần token + whitelist
- `emergency_stop` dừng motor qua OpMode (không tự chạy khi mất heartbeat)
- Network chạy thread riêng, queue giới hạn (capacity 2)

## Log

- JSONL: `logs/telemetry-YYYY-MM-DD.jsonl`
- CSV: `logs/telemetry-YYYY-MM-DD.csv`

## Kiểm thử

```bash
cd src/control_drivehub
pip install -r pi_monitor/requirements.txt pytest pytest-asyncio
export PYTHONPATH=$PWD
pytest tests/ -v
python scripts/fake_hub_client.py --url ws://127.0.0.1:8765/ws/hub
```

## Troubleshooting

| Triệu chứng | Gợi ý |
|-------------|-------|
| Dashboard STALE | Kiểm tra Control Hub WS, IP Pi, port 8765 |
| Hub không kết nối | Pi và Control Hub cùng subnet WiFi robot |
| IMU trống | Cấu hình tên IMU trong `BridgeConfig.IMU_NAME` |
| E-Stop không hiện | Bật `commands.enabled: true` trong YAML |
