#!/usr/bin/env python3
"""Bridge the FreeRTOS/QEMU cFS POC to cFS-GroundSystem.

The current Cortex-M3 FreeRTOS port does not implement OSAL sockets, so this
host-side bridge converts mission-app console telemetry into the UDP packets
that cFS-GroundSystem already understands.
"""

import argparse
import signal
import socket
import struct
import subprocess
import sys
import threading
from dataclasses import dataclass


MISSION_TLM_PREFIX = "SAT_MISSION_HK,"
SATELLITE_TLM_MID = 0x0883
SATELLITE_CMD_MID = 0x1882


@dataclass
class MissionState:
    sequence: int = 0
    command_counter: int = 0
    error_counter: int = 0
    mode: int = 0
    status: int = 0
    uptime_seconds: int = 0
    payload_samples: int = 0
    battery_percent: int = 0


class SatelliteGroundBridge:
    def __init__(self, args):
        self.args = args
        self.state = MissionState()
        self.state_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.qemu = None
        self.tlm_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def build_tlm_packet(self):
        with self.state_lock:
            state = MissionState(**self.state.__dict__)

        secondary_header = b"\x00" * 6
        payload = struct.pack(
            "<BBBBIIHH",
            state.command_counter & 0xFF,
            state.error_counter & 0xFF,
            state.mode & 0xFF,
            state.status & 0xFF,
            state.uptime_seconds & 0xFFFFFFFF,
            state.payload_samples & 0xFFFFFFFF,
            state.battery_percent & 0xFFFF,
            0,
        )
        data = secondary_header + payload
        primary = struct.pack(
            ">HHH",
            SATELLITE_TLM_MID,
            0xC000 | (state.sequence & 0x3FFF),
            len(data) - 1,
        )
        return primary + data

    def publish_telemetry(self, reason):
        packet = self.build_tlm_packet()
        self.tlm_sock.sendto(packet, (self.args.tlm_host, self.args.tlm_port))
        with self.state_lock:
            state = MissionState(**self.state.__dict__)
        print(
            "[bridge] UDP telemetry -> "
            f"{self.args.tlm_host}:{self.args.tlm_port} "
            f"seq={state.sequence} cmd={state.command_counter} "
            f"err={state.error_counter} mode={state.mode} "
            f"status={state.status} reason={reason}",
            flush=True,
        )

    def update_from_qemu_line(self, line):
        if not line.startswith(MISSION_TLM_PREFIX):
            return False

        fields = line.strip().split(",")
        if len(fields) != 9:
            return False

        try:
            sequence = int(fields[1], 10)
            mode = int(fields[4], 10)
            status = int(fields[5], 10)
            uptime_seconds = int(fields[6], 10)
            payload_samples = int(fields[7], 10)
            battery_percent = int(fields[8], 10)
        except ValueError:
            return False

        with self.state_lock:
            self.state.sequence = sequence
            self.state.mode = mode
            self.state.status = status
            self.state.uptime_seconds = uptime_seconds
            self.state.payload_samples = payload_samples
            self.state.battery_percent = battery_percent

        self.publish_telemetry("flight-hk")
        return True

    def handle_command_packet(self, packet, sender):
        if len(packet) < 8:
            return

        pkt_id = struct.unpack(">H", packet[:2])[0]
        cmd_code = packet[6]
        valid = pkt_id == SATELLITE_CMD_MID and cmd_code in (0, 1, 2)

        with self.state_lock:
            if valid:
                if cmd_code == 1:
                    self.state.command_counter = 0
                    self.state.error_counter = 0
                else:
                    self.state.command_counter += 1
                    if cmd_code == 2:
                        self.state.payload_samples += 1
                self.state.status = 0
            else:
                self.state.error_counter += 1
                self.state.status = 2

        verdict = "accepted" if valid else "rejected"
        print(
            "[bridge] UDP command <- "
            f"{sender[0]}:{sender[1]} pkt=0x{pkt_id:04X} "
            f"cc={cmd_code} {verdict}",
            flush=True,
        )
        self.publish_telemetry(f"command-{verdict}")

    def command_loop(self):
        self.cmd_sock.bind((self.args.cmd_host, self.args.cmd_port))
        self.cmd_sock.settimeout(0.5)
        print(
            "[bridge] listening for GroundSystem commands on "
            f"{self.args.cmd_host}:{self.args.cmd_port}",
            flush=True,
        )

        while not self.stop_event.is_set():
            try:
                packet, sender = self.cmd_sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            self.handle_command_packet(packet, sender)

    def qemu_args(self):
        return [
            self.args.qemu,
            "-machine",
            "mps2-an385",
            "-monitor",
            "null",
            "-semihosting",
            "--semihosting-config",
            "enable=on,target=native",
            "-kernel",
            self.args.kernel,
            "-serial",
            "stdio",
            "-nographic",
        ]

    def run_qemu(self):
        print("[bridge] starting QEMU satellite FreeRTOS cFS POC", flush=True)
        self.qemu = subprocess.Popen(
            self.qemu_args(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert self.qemu.stdout is not None
        for line in self.qemu.stdout:
            print(line, end="", flush=True)
            self.update_from_qemu_line(line)

        return self.qemu.wait()

    def stop(self):
        self.stop_event.set()
        try:
            self.cmd_sock.close()
        except OSError:
            pass
        if self.qemu is not None and self.qemu.poll() is None:
            self.qemu.terminate()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--qemu", default="qemu-system-arm")
    parser.add_argument("--cmd-host", default="127.0.0.1")
    parser.add_argument("--cmd-port", type=int, default=1234)
    parser.add_argument("--tlm-host", default="127.0.0.1")
    parser.add_argument("--tlm-port", type=int, default=2234)
    return parser.parse_args()


def main():
    args = parse_args()
    bridge = SatelliteGroundBridge(args)

    def handle_signal(signum, frame):
        del signum, frame
        bridge.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    cmd_thread = threading.Thread(target=bridge.command_loop, daemon=True)
    cmd_thread.start()

    try:
        return bridge.run_qemu()
    finally:
        bridge.stop()
        cmd_thread.join(timeout=1)


if __name__ == "__main__":
    sys.exit(main())
