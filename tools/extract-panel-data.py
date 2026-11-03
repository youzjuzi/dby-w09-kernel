#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Extract owner-supplied DTB panel properties into a private C header.

Uses dtc's fdtget. Never accesses a device or executes code from the DTB.
Only the historically matched property hashes are accepted: patch 0003 relies
on a specific packet index. Do not relax these pins for a different panel.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

NODE = '/soc/qcom,mdss_mdp@ae00000/lcd_kit_debussy_290_20d_10p9_qcom/qcom,mdss-dsi-display-timings/timing@0'
PINS = {'on': 'cb564b290e8242c37170067a7a67ae6c7d6ab432ebfc0f0920808c5c513dc372', 'off': '557531fb0d35113f018c2ae40afebe94c76204ff0bf39a4e1ccb10676320a664'}
COUNTS = {'on': 104, 'off': 5}


def decode(raw):
    rows = []
    pos = 0
    while pos < len(raw):
        header = raw[pos:pos + 7]
        if len(header) != 7:
            raise ValueError('truncated packet header')
        kind, last, channel, ack, delay = header[:5]
        size = int.from_bytes(header[5:7], 'big')
        payload = raw[pos + 7:pos + 7 + size]
        if (last, channel, ack) != (1, 0, 0):
            raise ValueError('unsupported packet flags')
        if kind not in (0x05, 0x15, 0x39) or not 1 <= size <= 6:
            raise ValueError('unsupported packet type or length')
        if len(payload) != size:
            raise ValueError('truncated payload')
        if (kind == 0x05 and size != 1) or (kind == 0x15 and size != 2):
            raise ValueError('invalid short packet length')
        rows.append((kind, delay, payload))
        pos += 7 + size
    if not rows:
        raise ValueError('empty sequence')
    return rows


def generate(properties):
    parts = ['/* Generated from owner-supplied data. Keep private; no licence is granted to the data. */\n']
    for kind in ('on', 'off'):
        raw = properties[kind]
        if hashlib.sha256(raw).hexdigest() != PINS[kind]:
            raise ValueError(kind + ' property does not match the supported panel data')
        rows = decode(raw)
        if len(rows) != COUNTS[kind]:
            raise ValueError('unexpected packet count')
        parts.append('static const struct dby_w09_cmd dby_w09_' + kind + '[] = {\n')
        for packet_type, delay, payload in rows:
            parts.append('\t{ 0x%02x, %d, %d, { ' % (packet_type, delay, len(payload)) +
                         ', '.join('0x%02x' % x for x in payload) + ' } },\n')
        parts.append('};\n\n')
    return ''.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dtb', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='new private header path; parent directory must exist')
    args = parser.parse_args()
    if args.dtb.is_symlink() or not args.dtb.is_file():
        raise ValueError('DTB must be a regular, non-symlink file')
    if not 40 <= args.dtb.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError('unsupported DTB size')
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('output already exists; refusing overwrite')
    props = {}
    for kind in ('on', 'off'):
        result = subprocess.run(['fdtget', '-t', 'bx', str(args.dtb.resolve()), NODE,
                                 'qcom,mdss-dsi-' + kind + '-command'],
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise ValueError('cannot read required panel property; check DTB and dtc tools')
        props[kind] = bytes(int(word, 16) for word in result.stdout.split())
    content = generate(props)
    # Exclusive creation, with private permissions from the first write.
    import os
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(content)
    print('Created private header (104 on / 5 off packets); hardware unverified.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
