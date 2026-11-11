#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Generate a private board memory include from an owner's stock runtime FDT.

Only the audited layout is accepted. This reads host files with fdtget; it does
not access devices, mount images, or copy serials, bootargs or MAC addresses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

LAYOUT_SHA256 = '549bc7fbfbe52da9ac18e52215a8614cc49cd48af9de42a0d6deb7d6315086fd'


def query(dtb, *args):
    result = subprocess.run(['fdtget', *args[:2], str(dtb), *args[2:]],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError('required FDT content unavailable')
    return result.stdout.split()


def read_layout(dtb):
    def get(node, prop):
        return bytes(int(x, 16) for x in query(dtb, '-t', 'bx', node, prop)).hex()
    # fdtget list commands take one option; invoke them separately.
    def listing(option, node):
        x = subprocess.run(['fdtget', option, str(dtb), node], capture_output=True,
                           text=True, timeout=15)
        if x.returncode:
            raise ValueError('cannot list memory nodes')
        return x.stdout.split()
    if get('/', '#address-cells') != '00000002' or get('/', '#size-cells') != '00000002':
        raise ValueError('unsupported root cell format')
    if get('/reserved-memory', '#address-cells') != '00000002' or get('/reserved-memory', '#size-cells') != '00000002':
        raise ValueError('unsupported reserved-memory cell format')
    layout = {'memory': get('/memory', 'reg'), 'reserved': {}}
    for name in listing('-l', '/reserved-memory'):
        if not re.fullmatch(r'[A-Za-z0-9_,@+-]+', name):
            raise ValueError('unsupported node name')
        path = '/reserved-memory/' + name
        props = listing('-p', path)
        if 'reg' in props:
            layout['reserved'][name] = {'reg': get(path, 'reg'), 'no-map': 'no-map' in props}
    return layout


def digest(layout):
    return hashlib.sha256(json.dumps(layout, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def generate(layout):
    if digest(layout) != LAYOUT_SHA256:
        raise ValueError('memory layout differs from audited baseline; do not bypass this check')
    def cells(raw):
        data = bytes.fromhex(raw)
        if not data or len(data) % 16:
            raise ValueError('invalid 64-bit address/size tuples')
        return ' '.join('0x' + data[i:i+4].hex() for i in range(0, len(data), 4))
    lines = ['/* Owner-extracted private layout. Do not publish. */', '/ {',
             ' memory { device_type = "memory"; reg = <' + cells(layout['memory']) + '>; };',
             ' reserved-memory { #address-cells = <2>; #size-cells = <2>; ranges;']
    found = set()
    for name, props in sorted(layout['reserved'].items()):
        label = ''
        if name == 'reserved-memory@80860000': label = 'cmd_db'
        if name.startswith('smem_region@'): label = 'dby_smem'
        if name.startswith('pil_gpu_region@'): label = 'dby_gpu_zap_mem'
        if name.startswith('pil_video_region@'): label = 'dby_video_mem'
        if label:
            if label in found: raise ValueError('duplicate role')
            found.add(label)
        prefix = (label + ': ') if label else ''
        line = ' ' + prefix + name + ' { reg = <' + cells(props['reg']) + '>;'
        if props['no-map'] or name.startswith('cont_splash_region@'): line += ' no-map;'
        if label == 'cmd_db': line += ' compatible = "qcom,cmd-db";'
        lines.append(line + ' };')
    if found != {'cmd_db', 'dby_smem', 'dby_gpu_zap_mem', 'dby_video_mem'}:
        raise ValueError('missing required reservation role')
    splashes = [p for n, p in layout['reserved'].items() if n.startswith('cont_splash_region@')]
    if len(splashes) != 1: raise ValueError('ambiguous splash region')
    raw = bytes.fromhex(splashes[0]['reg'])
    if len(raw) != 16: raise ValueError('unsupported splash layout')
    address, size = int.from_bytes(raw[:8], 'big'), int.from_bytes(raw[8:], 'big')
    if size < 1600 * 2560 * 4: raise ValueError('splash region too small')
    lines += [' };', ' chosen { #address-cells = <2>; #size-cells = <2>; ranges;',
              f' framebuffer@{address:x} {{ compatible = "simple-framebuffer"; reg = <0x{address >> 32:x} 0x{address & 0xffffffff:x} 0 0xfa0000>; width = <1600>; height = <2560>; stride = <6400>; format = "a8r8g8b8"; status = "okay"; }};',
              ' };', '};', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dtb', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.dtb.is_symlink() or not args.dtb.is_file() or not 40 <= args.dtb.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError('input must be a regular FDT file within size bounds')
    if args.output.exists() or args.output.is_symlink(): raise ValueError('output already exists')
    text = generate(read_layout(args.dtb.resolve()))
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: f.write(text)
    print('Private memory include generated; hardware unverified.')


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
