# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic generator tests. No real RAM or reservation contents included."""
from pathlib import Path
import copy
import runpy
import unittest

api = runpy.run_path(str(Path(__file__).resolve().parents[1]/'tools/extract-memory-layout.py'))


def pair(address, size):
    return (address.to_bytes(8, 'big') + size.to_bytes(8, 'big')).hex()


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = {'memory': pair(0, 0x4000000), 'reserved': {
            'reserved-memory@80860000': {'reg': pair(0x100, 0x10), 'no-map': False},
            'smem_region@200': {'reg': pair(0x200, 0x10), 'no-map': False},
            'pil_gpu_region@300': {'reg': pair(0x300, 0x10), 'no-map': True},
            'pil_video_region@400': {'reg': pair(0x400, 0x10), 'no-map': True},
            'cont_splash_region@1000000': {'reg': pair(0x1000000, 0x1000000), 'no-map': False},
        }}

    def test_unknown_layout_refused(self):
        with self.assertRaises(ValueError):
            api['generate']({'memory': pair(0, 1), 'reserved': {}})

    def test_roles_and_splash_policy(self):
        layout = {'memory': pair(0, 0x4000000), 'reserved': {
            'reserved-memory@80860000': {'reg': pair(0x100, 0x10), 'no-map': False},
            'smem_region@200': {'reg': pair(0x200, 0x10), 'no-map': False},
            'pil_gpu_region@300': {'reg': pair(0x300, 0x10), 'no-map': True},
            'pil_video_region@400': {'reg': pair(0x400, 0x10), 'no-map': True},
            'cont_splash_region@1000000': {'reg': pair(0x1000000, 0x1000000), 'no-map': False},
        }}
        glob = api['generate'].__globals__
        original = glob['LAYOUT_SHA256']
        try:
            glob['LAYOUT_SHA256'] = api['digest'](layout)
            text = api['generate'](layout)
            self.assertIn('dby_gpu_zap_mem:', text)
            self.assertIn('cmd_db:', text)
            self.assertIn('dby_smem:', text)
            self.assertIn('dby_video_mem:', text)
            self.assertIn('no-map;', next(x for x in text.splitlines() if 'cont_splash_region@' in x))
            layout['reserved'].pop('smem_region@200')
            glob['LAYOUT_SHA256'] = api['digest'](layout)
            with self.assertRaises(ValueError): api['generate'](layout)
        finally:
            glob['LAYOUT_SHA256'] = original

    def test_missing_video_role_refused_even_with_matching_fingerprint(self):
        layout = copy.deepcopy(self.layout)
        layout['reserved'].pop('pil_video_region@400')
        glob = api['generate'].__globals__
        original = glob['LAYOUT_SHA256']
        try:
            glob['LAYOUT_SHA256'] = api['digest'](layout)
            with self.assertRaisesRegex(ValueError, 'missing required reservation role'):
                api['generate'](layout)
        finally:
            glob['LAYOUT_SHA256'] = original

    def test_video_address_or_size_change_refused(self):
        glob = api['generate'].__globals__
        original = glob['LAYOUT_SHA256']
        try:
            # Pin the complete synthetic baseline, just as production pins the
            # owner's entire layout. Never update the pin for a mutated region.
            glob['LAYOUT_SHA256'] = api['digest'](self.layout)
            for address, size in ((0x500, 0x10), (0x400, 0x20)):
                with self.subTest(address=address, size=size):
                    layout = copy.deepcopy(self.layout)
                    layout['reserved']['pil_video_region@400']['reg'] = pair(address, size)
                    with self.assertRaisesRegex(ValueError, 'memory layout differs'):
                        api['generate'](layout)
        finally:
            glob['LAYOUT_SHA256'] = original


if __name__ == '__main__': unittest.main()
