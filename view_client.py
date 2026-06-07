#!/usr/bin/env python3
import concurrent.futures
import ipaddress
import json
import platform
import queue
import re
import socket
import struct
import subprocess
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk
from typing import Optional

import cv2
import numpy as np


TCP_PORT = 5000
UDP_PORT = 5001
DISCOVERY_MESSAGE = b"RASPI_CAM_DISCOVER_V1"
WINDOW_NAME = "raspi stream"
CACHE_PATH = Path(__file__).with_name(".raspi_cam_viewer.json")

RESOLUTIONS = {
    "640x480": (640, 480),
    "1280x720": (1280, 720),
    "1920x1080": (1920, 1080),
}

SKIP_INTERFACE_TERMS = ("tailscale", "radmin", "vpn", "loopback", "teredo")


@dataclass(frozen=True)
class NetworkInterface:
    name: str
    address: ipaddress.IPv4Address
    network: ipaddress.IPv4Network
    priority: int


@dataclass(frozen=True)
class DiscoveryCandidate:
    host: str
    response: dict
    interface: Optional[NetworkInterface]
    source: str


class DiscoveryError(TimeoutError):
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def recvall(sock, n, stop_event):
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


def send_json_line(sock, payload):
    sock.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")


def recv_json_line(sock, max_bytes=4096):
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


def _is_usable_network(name, address, network):
    lowered = name.lower()
    if address.is_loopback or address.is_link_local or address.is_multicast:
        return False
    if network.prefixlen >= 32:
        return False
    if any(term in lowered for term in SKIP_INTERFACE_TERMS):
        return False
    return True


def _interface_priority(name, address):
    lowered = name.lower()
    if address.is_private:
        base = 0
    else:
        base = 50
    if "ethernet" in lowered or "wi-fi" in lowered or "wifi" in lowered:
        base -= 10
    return base


def _interfaces_from_ipconfig():
    result = subprocess.run(
        ["ipconfig", "/all"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    text = result.stdout
    interfaces = []
    current_name = None
    current_ip = None
    current_mask = None

    def flush():
        nonlocal current_ip, current_mask
        if not current_name or not current_ip or not current_mask:
            return
        try:
            iface = ipaddress.IPv4Interface(f"{current_ip}/{current_mask}")
        except ValueError:
            return
        if not _is_usable_network(current_name, iface.ip, iface.network):
            return
        interfaces.append(
            NetworkInterface(
                name=current_name,
                address=iface.ip,
                network=iface.network,
                priority=_interface_priority(current_name, iface.ip),
            )
        )

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if raw_line and not raw_line.startswith(" ") and raw_line.endswith(":"):
            flush()
            current_name = raw_line[:-1].strip()
            current_ip = None
            current_mask = None
            continue

        ip_match = re.search(r"IPv4 Address[.\s]*:\s*([0-9.]+)", line)
        if ip_match:
            current_ip = ip_match.group(1)
            continue

        mask_match = re.search(r"Subnet Mask[.\s]*:\s*([0-9.]+)", line)
        if mask_match:
            current_mask = mask_match.group(1)

    flush()
    return interfaces


def _interfaces_from_ip_command():
    result = subprocess.run(
        ["ip", "-o", "-4", "addr", "show", "up"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    interfaces = []
    for line in result.stdout.splitlines():
        match = re.search(r"\d+:\s+([^:]+):\s+.*\binet\s+([0-9.]+/\d+)", line)
        if not match:
            continue
        name = match.group(1)
        try:
            iface = ipaddress.IPv4Interface(match.group(2))
        except ValueError:
            continue
        if not _is_usable_network(name, iface.ip, iface.network):
            continue
        interfaces.append(
            NetworkInterface(
                name=name,
                address=iface.ip,
                network=iface.network,
                priority=_interface_priority(name, iface.ip),
            )
        )
    return interfaces


def _interfaces_from_socket_route():
    interfaces = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            address = ipaddress.IPv4Address(sock.getsockname()[0])
        except OSError:
            return []

    network = ipaddress.IPv4Network(f"{address}/24", strict=False)
    if _is_usable_network("default-route", address, network):
        interfaces.append(
            NetworkInterface(
                name="default-route",
                address=address,
                network=network,
                priority=_interface_priority("default-route", address),
            )
        )
    return interfaces


def get_network_interfaces():
    interfaces = []
    if platform.system().lower() == "windows":
        try:
            interfaces.extend(_interfaces_from_ipconfig())
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            interfaces.extend(_interfaces_from_ip_command())
        except (OSError, subprocess.SubprocessError):
            pass

    if not interfaces:
        interfaces.extend(_interfaces_from_socket_route())

    deduped = {}
    for iface in interfaces:
        deduped[(str(iface.address), str(iface.network))] = iface
    return sorted(deduped.values(), key=lambda item: (item.priority, item.network.prefixlen))


def load_cached_host():
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    host = str(payload.get("host", "")).strip()
    try:
        ipaddress.IPv4Address(host)
    except ValueError:
        return None
    return host


def save_cached_host(host):
    try:
        ipaddress.IPv4Address(host)
    except ValueError:
        return
    payload = {"host": host, "updated_at": int(time.time())}
    try:
        CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _valid_discovery_response(response):
    return (
        isinstance(response, dict)
        and response.get("version") == 1
        and response.get("tcp_port") == TCP_PORT
        and response.get("name")
    )


def _receive_discovery(sock, iface, source, deadline):
    candidates = []
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        sock.settimeout(min(0.1, remaining))
        try:
            data, addr = sock.recvfrom(2048)
        except socket.timeout:
            continue
        try:
            response = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if _valid_discovery_response(response):
            candidates.append(DiscoveryCandidate(addr[0], response, iface, source))
    return candidates


def _probe_targets(targets, iface, source, timeout):
    deadline = time.monotonic() + timeout
    candidates = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if iface is not None:
            try:
                sock.bind((str(iface.address), 0))
            except OSError:
                return []
        for host in targets:
            try:
                sock.sendto(DISCOVERY_MESSAGE, (host, UDP_PORT))
            except OSError:
                continue
        candidates.extend(_receive_discovery(sock, iface, source, deadline))
    return candidates


def _scan_interface(iface, timeout):
    targets = ["255.255.255.255", str(iface.network.broadcast_address)]
    if iface.network.prefixlen >= 24:
        targets.extend(str(ip) for ip in iface.network.hosts() if ip != iface.address)
    else:
        subnet_24 = ipaddress.IPv4Network(f"{iface.address}/24", strict=False)
        targets.extend(str(ip) for ip in subnet_24.hosts() if ip != iface.address)
    return _probe_targets(targets, iface, "lan-scan", timeout)


def _candidate_score(candidate):
    score = 100
    try:
        host_ip = ipaddress.IPv4Address(candidate.host)
    except ValueError:
        host_ip = None

    if candidate.source == "cache":
        score -= 40
    elif candidate.source == "lan-scan":
        score -= 20

    if candidate.interface is not None:
        score += candidate.interface.priority
        if host_ip is not None and host_ip in candidate.interface.network:
            score -= 30
    elif host_ip is not None and host_ip.is_private:
        score -= 10

    return score


def discover_server(timeout=2.5):
    diagnostics = []
    candidates = []
    cached_host = load_cached_host()
    interfaces = get_network_interfaces()

    if interfaces:
        iface_text = ", ".join(f"{iface.name} {iface.address}/{iface.network.prefixlen}" for iface in interfaces)
        diagnostics.append(f"interfaces: {iface_text}")
    else:
        diagnostics.append("interfaces: none usable")

    if cached_host:
        diagnostics.append(f"cache probe: {cached_host}")
        candidates.extend(_probe_targets([cached_host], None, "cache", 0.45))
        if candidates:
            best = sorted(candidates, key=_candidate_score)[0]
            return best.host, best.response, diagnostics

    scan_timeout = max(0.7, timeout)
    if interfaces:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(interfaces))) as executor:
            futures = [executor.submit(_scan_interface, iface, scan_timeout) for iface in interfaces]
            for future in concurrent.futures.as_completed(futures, timeout=scan_timeout + 0.5):
                try:
                    candidates.extend(future.result())
                except (OSError, RuntimeError):
                    continue
    else:
        candidates.extend(_probe_targets(["255.255.255.255"], None, "global-broadcast", scan_timeout))

    seen_hosts = sorted({candidate.host for candidate in candidates})
    diagnostics.append("responses: " + (", ".join(seen_hosts) if seen_hosts else "none"))
    diagnostics.append("tried: cache, global broadcast, directed broadcast, /24 UDP scan")

    if not candidates:
        raise DiscoveryError("no Raspberry Pi camera server replied", diagnostics)

    best = sorted(candidates, key=_candidate_score)[0]
    return best.host, best.response, diagnostics


class StreamViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Raspberry Pi camera viewer")
        self.resizable(False, False)

        self.messages = queue.Queue()
        self.worker = None
        self.stop_event = threading.Event()
        self.sock = None
        self.manual_ip_visible = False

        self.resolution_var = tk.StringVar(value="1280x720")
        self.fps_var = tk.StringVar(value="30")
        self.quality_var = tk.IntVar(value=70)
        self.manual_ip_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Idle")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(50, self._drain_messages)

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")

        ttk.Label(root, text="Resolution").grid(row=0, column=0, sticky="w")
        resolution = ttk.Combobox(
            root,
            textvariable=self.resolution_var,
            values=list(RESOLUTIONS.keys()),
            state="readonly",
            width=14,
        )
        resolution.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(root, text="FPS").grid(row=1, column=0, sticky="w")
        fps = ttk.Combobox(
            root,
            textvariable=self.fps_var,
            values=("15", "30"),
            state="readonly",
            width=14,
        )
        fps.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(root, text="JPEG quality").grid(row=2, column=0, sticky="w")
        quality = ttk.Scale(
            root,
            from_=50,
            to=95,
            orient="horizontal",
            variable=self.quality_var,
            command=self._quality_changed,
        )
        quality.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.quality_label = ttk.Label(root, text="70", width=3)
        self.quality_label.grid(row=2, column=2, sticky="e", padx=(6, 0))

        self.manual_frame = ttk.Frame(root)
        ttk.Label(self.manual_frame, text="Manual IP").grid(row=0, column=0, sticky="w")
        manual_ip = ttk.Entry(self.manual_frame, textvariable=self.manual_ip_var, width=18)
        manual_ip.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.connect_button = ttk.Button(root, text="Connect", command=self._connect_clicked)
        self.connect_button.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 4))

        ttk.Label(root, text="Status").grid(row=5, column=0, sticky="w")
        self.status_label = ttk.Label(root, textvariable=self.status_var, width=50)
        self.status_label.grid(row=5, column=1, columnspan=2, sticky="w", padx=(8, 0))

        root.columnconfigure(1, weight=1)

    def _quality_changed(self, _value):
        self.quality_label.configure(text=str(int(self.quality_var.get())))

    def _show_manual_ip(self):
        if self.manual_ip_visible:
            return
        self.manual_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.manual_frame.columnconfigure(1, weight=1)
        self.manual_ip_visible = True

    def _config(self):
        width, height = RESOLUTIONS[self.resolution_var.get()]
        return {
            "type": "config",
            "width": width,
            "height": height,
            "fps": int(self.fps_var.get()),
            "quality": max(50, min(95, int(self.quality_var.get()))),
        }

    def _connect_clicked(self):
        if self.worker and self.worker.is_alive():
            self._disconnect()
            return

        self.stop_event.clear()
        self.connect_button.configure(text="Connecting...", state="disabled")
        self.status_var.set("Searching LAN")

        manual_host = self.manual_ip_var.get().strip()
        config = self._config()
        self.worker = threading.Thread(
            target=self._stream_worker,
            args=(config, manual_host),
            daemon=True,
        )
        self.worker.start()

    def _disconnect(self):
        self.status_var.set("Disconnecting")
        self.stop_event.set()
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass

    def _stream_worker(self, config, manual_host):
        sock = None
        window_open = False
        failed = False
        try:
            if manual_host:
                host = manual_host
                self.messages.put(("status", f"Connecting {host}:{TCP_PORT}"))
            else:
                self.messages.put(("status", "Searching LAN"))
                host, info, diagnostics = discover_server()
                for line in diagnostics:
                    print(f"discovery: {line}")
                self.messages.put(("status", f"Found {host} ({info.get('name')})"))

            self.messages.put(("status", f"Connecting {host}:{TCP_PORT}"))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((host, TCP_PORT))
            self.sock = sock

            send_json_line(sock, config)
            ack = recv_json_line(sock)
            if not ack.get("ok"):
                raise RuntimeError(ack.get("error", "server rejected config"))

            save_cached_host(host)
            self.messages.put(
                (
                    "connected",
                    "Connected "
                    f"{host} "
                    f"{ack.get('actual_width')}x{ack.get('actual_height')} "
                    f"@ {ack.get('actual_fps')} FPS",
                )
            )

            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            window_open = True

            while not self.stop_event.is_set():
                hdr = recvall(sock, 4, self.stop_event)
                if hdr is None:
                    break

                size = struct.unpack("!I", hdr)[0]
                if size <= 0 or size > 20_000_000:
                    raise RuntimeError(f"invalid frame size: {size}")

                jpg = recvall(sock, size, self.stop_event)
                if jpg is None:
                    break

                arr = np.frombuffer(jpg, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) == 27:
                    self.stop_event.set()
                    break
        except DiscoveryError as exc:
            failed = True
            print("discovery failed:")
            for line in exc.diagnostics:
                print(f"  {line}")
            self.messages.put(("manual_ip", None))
            self.messages.put(("failed", f"Failed: {exc}; manual IP available"))
        except TimeoutError as exc:
            failed = True
            self.messages.put(("manual_ip", None))
            self.messages.put(("failed", f"Failed: {exc}"))
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            failed = True
            self.messages.put(("manual_ip", None))
            self.messages.put(("failed", f"Failed: {exc}"))
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            if window_open:
                try:
                    cv2.destroyWindow(WINDOW_NAME)
                except cv2.error:
                    pass
            self.sock = None
            self.messages.put(("done", "Failed" if failed else "Disconnected"))

    def _drain_messages(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == "status":
                    self.status_var.set(value)
                elif kind == "manual_ip":
                    self._show_manual_ip()
                elif kind == "connected":
                    self.status_var.set(value)
                    self.connect_button.configure(text="Disconnect", state="normal")
                elif kind == "failed":
                    self.status_var.set(value)
                    self.connect_button.configure(text="Connect", state="normal")
                elif kind == "done":
                    if value != "Failed":
                        self.status_var.set(value)
                    self.connect_button.configure(text="Connect", state="normal")
        except queue.Empty:
            pass
        self.after(50, self._drain_messages)

    def _close(self):
        self._disconnect()
        self.after(100, self.destroy)


def main():
    StreamViewer().mainloop()


if __name__ == "__main__":
    main()
