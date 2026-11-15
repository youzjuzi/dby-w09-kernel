#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline board DT build; outputs stay in a NEW private host directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read_bd_address(path):
    """Validate a private address file and return its six little-endian bytes."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError
        # Refuse symlink replacement and never block on a substituted FIFO.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 64:
                raise ValueError
            raw = stream.read(65)
        if len(raw) > 64:
            raise ValueError
        text = raw.decode('utf-8').removesuffix('\n')
        if not re.fullmatch(r'[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}', text):
            raise ValueError
        address = bytes.fromhex(text.replace(':', ''))
        if (address == bytes(6) or address == bytes.fromhex('000000005aad')
                or address[0] & 1 or not address[0] & 2):
            raise ValueError
        return address[::-1]
    except (OSError, ValueError):
        # Neither contents nor input paths belong in terminal diagnostics.
        raise ValueError('invalid Bluetooth address file; require a regular non-symlink '
                         'file of at most 64 bytes containing one locally administered '
                         'unicast address') from None


def bd_address_fragment(address):
    return ('\n// owner-supplied, build-time private input\n'
            '&uart6 { bluetooth { local-bd-address = ['
            + address.hex(' ') + ']; }; };\n').encode('ascii')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kernel', type=Path, required=True, help='Linux 7.2.10 source tree')
    p.add_argument('--memory', type=Path, required=True, help='owner-generated dby-memory-private.dtsi')
    p.add_argument('--bd-address-file', type=Path,
                   help='optional private file: one locally administered unicast AA:BB:CC:DD:EE:FF')
    p.add_argument('--output', type=Path, required=True, help='new output directory; must not exist')
    p.add_argument('--cpp', default='aarch64-linux-gnu-gcc')
    p.add_argument('--dtc', default='dtc')
    a = p.parse_args()
    os.umask(0o077)
    address = read_bd_address(a.bd_address_file) if a.bd_address_file is not None else None
    kernel = a.kernel.resolve()
    for name, expected in json.loads((ROOT/'dts/upstream-sha256.json').read_text()).items():
        f = kernel/name
        if not f.resolve().is_relative_to(kernel) or not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != expected:
            raise ValueError('upstream include missing or changed: ' + name)
    if a.memory.is_symlink() or not a.memory.is_file():
        raise ValueError('memory input must be a regular file')
    if a.output.exists() or a.output.is_symlink(): raise ValueError('output already exists')
    a.output.mkdir(mode=0o700)
    out = a.output.resolve()
    (out/'dby-memory-private.dtsi').write_bytes(a.memory.read_bytes())
    # Copy the public board source so its quoted private include resolves here
    # before any stale private include in the user's kernel source tree.
    # Panel supplies are board defaults; no build-time overlay is needed.
    board = (ROOT/'dts/sm8250-huawei-dby-w09.dts').read_bytes()
    if address is not None:
        board += bd_address_fragment(address)
    (out/'board.dts').write_bytes(board)
    commands = [
        [a.cpp, '-E', '-P', '-nostdinc', '-undef', '-D__DTS__', '-x', 'assembler-with-cpp',
         '-I'+str(out), '-I'+str(kernel/'include'),
         '-I'+str(kernel/'arch/arm64/boot/dts/qcom'), str(out/'board.dts'), '-o', str(out/'board.pp.dts')],
        [a.dtc, '-I', 'dts', '-O', 'dtb', '-o', str(out/'dby-w09.dtb'), str(out/'board.pp.dts')],
    ]
    for name, command in zip(('cpp', 'dtc'), commands):
        result = subprocess.run(command, capture_output=True, timeout=120)
        (out/(name+'.stdout')).write_bytes(result.stdout)
        (out/(name+'.stderr')).write_bytes(result.stderr)
        if result.returncode: raise ValueError(name + ' failed; inspect private output logs')
    (out/'build-info.json').write_text(json.dumps({
        'evidence': 'offline compilation only; no schema or device validation',
        'dtb_sha256': hashlib.sha256((out/'dby-w09.dtb').read_bytes()).hexdigest(),
        'memory_sha256': hashlib.sha256(a.memory.read_bytes()).hexdigest(),
        'bd_address': 'supplied' if address is not None else 'none',
    }, indent=2)+'\n')
    print('DTB built; inspect dtc.stderr warnings. This is not device validation.')


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
