#!/usr/bin/env python3
"""Assert audio-only raw property changes; accepts two owner-built DTBs."""
from pathlib import Path
import argparse
import struct
import unittest


def parse(blob):
    h = struct.unpack_from('>10I', blob)
    assert h[0] == 0xd00dfeed
    off = h[2]
    strings = blob[h[3]:h[3]+h[8]]
    stack, nodes = [], {}
    while True:
        token = struct.unpack_from('>I', blob, off)[0]; off += 4
        if token == 1:
            end = blob.index(0, off)
            stack.append(blob[off:end].decode()); off = (end+4) & ~3
            nodes['/'.join(stack) or '/'] = {}
        elif token == 2:
            stack.pop()
        elif token == 3:
            length, name = struct.unpack_from('>II', blob, off); off += 8
            end = strings.index(0, name)
            nodes['/'.join(stack) or '/'][strings[name:end].decode()] = blob[off:off+length]
            off = (off+length+3) & ~3
        elif token == 9:
            break
        else:
            assert token == 4
    # memreserve table must also remain byte-identical.
    end = h[4]
    while blob[end:end+16] != bytes(16):
        end += 16
    return nodes, blob[h[4]:end+16]

ROOTS = ('/audio-codec', '/vph-pwr-regulator', '/sound',
         '/soc@0/remoteproc@17300000', '/soc@0/pinctrl@33c0000',
         '/soc@0/codec@3370000', '/soc@0/rxmacro@3200000',
         '/soc@0/txmacro@3220000', '/soc@0/soundwire@3210000',
         '/soc@0/soundwire@3230000', '/soc@0/rsc@18200000/regulators/bob')
EXACT = {('/reserved-memory/pil_adsp_region@8a100000', 'phandle'),
         ('/smp2p-adsp', 'status'),
         ('/soc@0/rsc@18200000/regulators', 'vdd-bob-supply')}

def allowed(node, prop):
    return (node, prop) in EXACT or any(node == r or node.startswith(r+'/') for r in ROOTS)


def compare(before, after):
    a, ar = parse(before); b, br = parse(after)
    assert ar == br, 'memreserve changed'
    changes = []
    for node in a.keys() | b.keys():
        assert node in b, 'node removed: '+node
        for prop in a.get(node, {}).keys() | b.get(node, {}).keys():
            if a.get(node, {}).get(prop) != b.get(node, {}).get(prop):
                assert allowed(node, prop), 'non-audio change: '+node+':'+prop
                changes.append((node, prop))
    assert changes, 'no audio change'
    for node in ('/soc@0/codec@3240000', '/soc@0/soundwire@3250000'):
        assert b[node]['status'] == b'disabled\0', 'WSA must remain disabled'
    assert b['/soc@0/remoteproc@17300000']['firmware-name'] == b'qcom/dby-w09/adsp.mdt\0'
    assert b['/soc@0/codec@3370000']['qcom,dmic-sample-rate'] == struct.pack('>I', 2400000)
    assert 'aux-devs' not in b['/sound']
    print('PASS: audio-only raw property changes:', len(changes))

class AllowlistTests(unittest.TestCase):
    def test_non_audio_rejected(self):
        for node in ('/soc@0/display-subsystem@ae00000', '/qca6390-pmu',
                     '/soc@0/spmi@c440000/pmic@2/charger@1000', '/soundevil'):
            self.assertFalse(allowed(node, 'status'))
    def test_exact_supply_scope(self):
        self.assertTrue(allowed('/soc@0/rsc@18200000/regulators', 'vdd-bob-supply'))
        self.assertFalse(allowed('/soc@0/rsc@18200000/regulators', 'compatible'))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        compare(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes())
    else:
        unittest.main()
