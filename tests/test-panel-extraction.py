# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic parser tests only; no device data or accepted command table."""
from pathlib import Path
import runpy
import unittest

api = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tools/extract-panel-data.py'))


class PacketTests(unittest.TestCase):
    def test_packet_framing(self):
        raw = bytes([0x15, 1, 0, 0, 7, 0, 2, 0x12, 0x34])
        self.assertEqual(api['decode'](raw), [(0x15, 7, bytes([0x12, 0x34]))])

    def test_reject_malformed(self):
        valid = bytes([0x15, 1, 0, 0, 7, 0, 2, 0x12, 0x34])
        for raw in (b'', valid[:5], valid[:-1], bytes([0x15, 1, 1, 0, 7, 0, 2, 1, 2]),
                    bytes([0x05, 1, 0, 0, 0, 0, 2, 1, 2]),
                    bytes([0x39, 1, 0, 0, 0, 0, 7]) + b'1234567'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                api['decode'](raw)

    def test_unknown_data_refused(self):
        with self.assertRaises(ValueError):
            api['generate']({'on': b'not the device data', 'off': b''})


if __name__ == '__main__':
    unittest.main()
