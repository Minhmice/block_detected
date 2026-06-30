"""Shared wire protocol for Pi camera stream server and viewer."""

from __future__ import annotations

import json
import socket
import struct

TCP_PORT = 5000
UDP_PORT = 5001
DISCOVERY_MESSAGE = b"RASPI_CAM_DISCOVER_V1"
MAX_CONFIG_BYTES = 4096
MAX_JPEG_QUALITY = 95
MIN_JPEG_QUALITY = 50


def send_json_line(sock, payload) -> None:
    sock.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")


def recv_json_line(sock, max_bytes: int = MAX_CONFIG_BYTES) -> dict:
    data = bytearray()
    while len(data) < max_bytes:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("connection closed during handshake")
        if chunk == b"\n":
            break
        data.extend(chunk)
    else:
        raise ValueError("handshake response is too large")
    return json.loads(data.decode("utf-8"))


def recvall(sock, n: int, stop_event) -> bytes | None:
    data = bytearray()
    while len(data) < n and not stop_event.is_set():
        try:
            pkt = sock.recv(n - len(data))
        except socket.timeout:
            continue
        if not pkt:
            return None
        data.extend(pkt)
    return bytes(data) if len(data) == n else None


def pack_frame(jpeg_bytes: bytes) -> bytes:
    return struct.pack("!I", len(jpeg_bytes)) + jpeg_bytes


def require_int(config: dict, key: str, minimum: int, maximum: int) -> int:
    value = config.get(key)
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    value = int(value)
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value
