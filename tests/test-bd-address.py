# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic private address validation and DT fragment integration tests."""
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1]/'tools/build-board-dtb.py'
api = runpy.run_path(str(TOOL))


class AddressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'address'

    def test_valid(self):
        for value in ('02:00:00:00:00:01', 'aA:bB:cC:dD:eE:fF',
                      '06:12:34:56:78:9A', '0E:12:34:56:78:9A'):
            for ending in ('', '\n'):
                with self.subTest(value=value, ending=ending):
                    self.source.write_text(value + ending)
                    expected = bytes.fromhex(value.replace(':', ''))[::-1]
                    self.assertEqual(api['read_bd_address'](self.source), expected)
        self.source.write_text('02:00:00:00:00:01')
        self.assertEqual(api['read_bd_address'](self.source).hex(' '), '01 00 00 00 00 02')

    def reject(self):
        with self.assertRaises(ValueError) as caught:
            api['read_bd_address'](self.source)
        self.assertTrue(str(caught.exception).startswith('invalid Bluetooth address file;'))
        # Exercise the CLI too: invalid inputs cannot create the output directory.
        out = self.root/'output'
        result = subprocess.run([sys.executable, '-B', str(TOOL), '--kernel',
                                 str(self.root/'unused-kernel'), '--memory',
                                 str(self.root/'unused-memory'), '--output', str(out),
                                 '--bd-address-file', str(self.source)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr.decode(), 'Error: ' + str(caught.exception) + '\n')
        self.assertFalse(out.exists())
        self.assertNotIn(str(self.source), result.stderr.decode())

    def test_invalid_contents(self):
        cases = [b'', b'\n', b'02:00:00:00:00:01\n02:00:00:00:00:02',
                 b'02:00:00:00:01', b'02:00:00:00:00:00:01', b'02:00:00:00:00:GG',
                 b'02-00-00-00-00-01', b'03:00:00:00:00:01', b'00:11:22:33:44:55',
                 b'00:00:00:00:00:00', b'00:00:00:00:5A:AD', b'x'*65,
                 b'02:00:00:00:00:01\n\n', b'02:00:00:00:00:01\r\n',
                 b' 02:00:00:00:00:01', b'02:00:00:00:00:01 ', b'\xff',
                 b'\xef\xbb\xbf02:00:00:00:00:01', b'02:00:00:00:00:01\x00']
        for value in cases:
            with self.subTest(value=value):
                self.source.write_bytes(value)
                self.reject()

    def test_symlink(self):
        target = self.root/'target'
        target.write_text('02:00:00:00:00:01')
        self.source.symlink_to(target)
        self.reject()

    def test_directory(self):
        self.source.mkdir()
        self.reject()

    def test_missing(self):
        self.reject()

    def test_fifo(self):
        import os
        os.mkfifo(self.source)
        self.reject()

    @unittest.skipUnless(shutil.which('dtc') and shutil.which('cpp'), 'dtc/cpp unavailable')
    def test_fragment_compiles(self):
        self.source.write_text('02:00:00:00:00:01')
        address = api['read_bd_address'](self.source)
        source = b'/dts-v1/; / { uart6: serial { bluetooth { compatible = "qcom,qca6390-bt"; }; }; };\n'
        source += api['bd_address_fragment'](address)
        cpp = subprocess.run(['cpp', '-P', '-nostdinc', '-undef', '-x', 'assembler-with-cpp'],
                             input=source, capture_output=True, check=True)
        dtb = subprocess.run(['dtc', '-I', 'dts', '-O', 'dtb'], input=cpp.stdout,
                             capture_output=True, check=True)
        decoded = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts'], input=dtb.stdout,
                                 capture_output=True, check=True)
        self.assertIn(b'local-bd-address = [01 00 00 00 00 02];', decoded.stdout)
        self.assertEqual(decoded.stdout.count(b'bluetooth {'), 1)


if __name__ == '__main__': unittest.main()
