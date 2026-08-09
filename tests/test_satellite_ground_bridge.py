import csv
import importlib.util
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = REPO_ROOT / "satellite-ground-bridge.py"
TLM_DEFINITION_PATH = (
    REPO_ROOT
    / "tools/cFS-GroundSystem/Subsystems/tlmGUI/satellite-mission-hk-tlm.txt"
)
SPEC = importlib.util.spec_from_file_location("satellite_ground_bridge", BRIDGE_PATH)
BRIDGE_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BRIDGE_MODULE
SPEC.loader.exec_module(BRIDGE_MODULE)


class SatelliteGroundBridgePacketTest(unittest.TestCase):
    def test_packet_matches_ground_system_default_offset(self):
        bridge = BRIDGE_MODULE.SatelliteGroundBridge(SimpleNamespace())
        self.addCleanup(bridge.tlm_sock.close)
        self.addCleanup(bridge.cmd_sock.close)

        bridge.state.sequence = 7
        bridge.state.command_counter = 1
        bridge.state.error_counter = 2
        bridge.state.mode = 3
        bridge.state.status = 4
        bridge.state.uptime_seconds = 0x11223344
        bridge.state.payload_samples = 0x55667788
        bridge.state.battery_percent = 90

        packet = bridge.build_tlm_packet()

        self.assertEqual(len(packet), 32)
        self.assertEqual(struct.unpack_from(">H", packet, 0)[0], 0x0883)
        self.assertEqual(struct.unpack_from(">H", packet, 4)[0], len(packet) - 7)
        self.assertEqual(
            struct.unpack_from("<BBBBIIH", packet, 16),
            (1, 2, 3, 4, 0x11223344, 0x55667788, 90),
        )

        decoded_fields = []
        with TLM_DEFINITION_PATH.open(newline="") as definition_file:
            for row in csv.reader(definition_file, skipinitialspace=True):
                if not row or row[0].startswith("#"):
                    continue
                field_offset = int(row[1]) + 4
                field_size = int(row[2])
                field_data = packet[field_offset : field_offset + field_size]
                self.assertEqual(len(field_data), field_size, row[0])
                decoded_fields.append(struct.unpack("<" + row[3], field_data)[0])

        self.assertEqual(
            decoded_fields,
            [1, 2, 3, 4, 0x11223344, 0x55667788, 90],
        )


if __name__ == "__main__":
    unittest.main()
