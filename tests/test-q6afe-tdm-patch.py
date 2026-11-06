#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay the TDM transport patch without fuzz; check each DT-to-APR field."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'

class TdmTransport(unittest.TestCase):
    def test_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'sound/soc/qcom/qdsp6'
            directory.mkdir(parents=True)
            for name in ('q6afe.h', 'q6afe.c', 'q6afe-dai.c'):
                shutil.copyfile(UPSTREAM / 'sound/soc/qcom/qdsp6' / name, directory / name)
            patch = next((ROOT / 'patches').glob('0009-*'))
            result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', tmp,
                                     '-i', str(patch)], check=True, capture_output=True, text=True)
            self.assertNotIn('offset', result.stdout)
            for field, apr in (('data_out_enable', 'ctrl_data_out_enable'),
                               ('invert_sync', 'ctrl_invert_sync_pulse'),
                               ('data_delay', 'ctrl_sync_data_delay')):
                self.assertIn('u16 ' + field + ';', (directory / 'q6afe.h').read_text())
                self.assertIn(f'tdm->{field} = dai_data->priv[dai->id].{field};',
                              (directory / 'q6afe-dai.c').read_text())
                self.assertIn(f'pcfg->tdm_cfg.{apr} = cfg->{field};',
                              (directory / 'q6afe.c').read_text())

if __name__ == '__main__':
    unittest.main()
