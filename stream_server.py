#!/usr/bin/env python3
import json
import socket
import struct
import subprocess
import threading
import time

import cv2


TCP_HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001
CAMERA_DEVICE = 0
DISCOVERY_MESSAGE = b"RASPI_CAM_DISCOVER_V1"
MAX_CONFIG_BYTES = 4096
MAX_JPEG_QUALITY = 95
MIN_JPEG_QUALITY = 50


def send_json_line(sock, payload):
    sock.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")


def recv_json_line(sock):
    data = bytearray()
    while len(data) < MAX_CONFIG_BYTES:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("client closed during handshake")
        if chunk == b"\n":
            break
        data.extend(chunk)
    else:
        raise ValueError("config JSON is too large")

    return json.loads(data.decode("utf-8"))


def require_int(config, key, minimum, maximum):
    value = config.get(key)
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    value = int(value)
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def read_actual(cap, prop, fallback):
    value = cap.get(prop)
    if value <= 0:
        return fallback
    return int(round(value))


def get_local_ipv4_addresses():
    addresses = set()
    try:
        result = subprocess.run(
            ["ip", "-o", "-4", "addr", "show", "up"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if "inet" not in parts:
                continue
            cidr = parts[parts.index("inet") + 1]
            address = cidr.split("/", 1)[0]
            if not address.startswith(("127.", "169.254.")):
                addresses.add(address)
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        hostname = socket.gethostname()
        for family, _socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(hostname, None, socket.AF_INET):
            if family != socket.AF_INET:
                continue
            address = sockaddr[0]
            if not address.startswith(("127.", "169.254.")):
                addresses.add(address)
    except OSError:
        pass

    return sorted(addresses)


def discovery_response():
    return {
        "name": "raspi-cam",
        "tcp_port": TCP_PORT,
        "version": 1,
        "hostname": socket.gethostname(),
        "addresses": get_local_ipv4_addresses(),
    }


def open_camera(width, height, fps):
    cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError("cannot open camera /dev/video0")

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = read_actual(cap, cv2.CAP_PROP_FRAME_WIDTH, width)
    actual_height = read_actual(cap, cv2.CAP_PROP_FRAME_HEIGHT, height)
    actual_fps = read_actual(cap, cv2.CAP_PROP_FPS, fps)
    return cap, actual_width, actual_height, actual_fps


def discovery_loop(stop_event):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))
        sock.settimeout(0.5)
        print(f"discovery: udp 0.0.0.0:{UDP_PORT}", flush=True)

        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break

            valid = data.strip() == DISCOVERY_MESSAGE
            print(
                f"discovery request from {addr[0]}:{addr[1]} valid={valid} bytes={len(data)}",
                flush=True,
            )
            if not valid:
                continue

            payload = discovery_response()
            response = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            try:
                sock.sendto(response, addr)
                print(
                    f"discovery reply to {addr[0]}:{addr[1]} addresses={payload['addresses']}",
                    flush=True,
                )
            except OSError as exc:
                print(f"discovery reply failed to {addr}: {exc}", flush=True)


def read_config(conn):
    config = recv_json_line(conn)
    if config.get("type") != "config":
        raise ValueError("first message must be a config object")

    width = require_int(config, "width", 1, 4096)
    height = require_int(config, "height", 1, 2160)
    fps = require_int(config, "fps", 1, 120)
    quality = require_int(config, "quality", MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)
    return width, height, fps, quality


def handle_client(conn, addr):
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    conn.settimeout(8.0)
    print(f"client connected: {addr}", flush=True)

    cap = None
    handshake_done = False
    try:
        width, height, fps, quality = read_config(conn)
        cap, actual_width, actual_height, actual_fps = open_camera(width, height, fps)
        send_json_line(
            conn,
            {
                "ok": True,
                "actual_width": actual_width,
                "actual_height": actual_height,
                "actual_fps": actual_fps,
            },
        )
        handshake_done = True
        print(
            f"streaming {actual_width}x{actual_height}@{actual_fps} quality={quality} to {addr}",
            flush=True,
        )

        conn.settimeout(1.0)
        frame_dt = 1.0 / max(fps, 1)
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

        while True:
            start = time.perf_counter()
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("camera read failed")

            ok, buf = cv2.imencode(".jpg", frame, encode_params)
            if not ok:
                continue

            data = buf.tobytes()
            conn.sendall(struct.pack("!I", len(data)))
            conn.sendall(data)

            delay = frame_dt - (time.perf_counter() - start)
            if delay > 0:
                time.sleep(delay)
    except (BrokenPipeError, ConnectionResetError, TimeoutError):
        print(f"client disconnected: {addr}", flush=True)
    except Exception as exc:
        print(f"client error {addr}: {exc}", flush=True)
        if not handshake_done:
            try:
                send_json_line(conn, {"ok": False, "error": str(exc)})
            except OSError:
                pass
    finally:
        if cap is not None:
            cap.release()
        try:
            conn.close()
        except OSError:
            pass
        print("waiting for next client", flush=True)


def main():
    stop_event = threading.Event()
    discovery = threading.Thread(target=discovery_loop, args=(stop_event,), daemon=True)
    discovery.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((TCP_HOST, TCP_PORT))
        srv.listen(1)
        print(f"stream server: tcp {TCP_HOST}:{TCP_PORT}", flush=True)

        try:
            while True:
                conn, addr = srv.accept()
                handle_client(conn, addr)
        except KeyboardInterrupt:
            print("stopping", flush=True)
        finally:
            stop_event.set()


if __name__ == "__main__":
    main()
