#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fault-test the patched LPASS runtime callbacks, not a Python reimplementation."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'


def function(text, name):
    match = re.search(r'static (?:int|void) ' + name + r'\([^;]*?\)\n\{', text)
    begin = text.index('{', match.start())
    end, depth = begin + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


MOCK = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
struct device { void *data; bool suspended, disabled; };
struct platform_device { struct device dev; };
struct clk { int id, refs; };
struct regmap { bool cache_only, dirty; };
struct macro {
    struct device *dev;
    struct clk *macro, *dcodec, *mclk, *npl, *fsgen;
    struct regmap *regmap;
    bool has_npl_clk;
    void *pds;
};
static int fail, step, stack[5], depth, exits;
static struct regmap map;
static void *dev_get_drvdata(struct device *dev) { return dev->data; }
#define dev_err(...) ((void)0)
static int clk_prepare_enable(struct clk *clk)
{
    if (!clk) return 0;
    assert(map.cache_only);
    if (++step == fail) return -5;
    assert(!clk->refs++);
    stack[depth++] = clk->id;
    return 0;
}
static void clk_disable_unprepare(struct clk *clk)
{
    if (!clk) return;
    assert(map.cache_only);
    assert(depth && stack[--depth] == clk->id);
    assert(clk->refs-- == 1);
}
static void regcache_cache_only(struct regmap *m, bool only) { m->cache_only = only; }
static void regcache_mark_dirty(struct regmap *m) { m->dirty = true; }
static int regcache_sync(struct regmap *m)
{
    assert(!m->cache_only && depth >= 3);
    if (++step == fail) return -5;
    m->dirty = false;
    return 0;
}
static void pm_runtime_disable(struct device *d) { d->disabled = true; }
static bool pm_runtime_status_suspended(struct device *d) { return d->suspended; }
static void pm_runtime_set_suspended(struct device *d) { d->suspended = true; }
static void lpass_macro_pds_exit(void *pds) { (void)pds; exits++; }
'''

MAIN = r'''
int main(void)
{
    for (int optional = 0; optional < 2; optional++) {
        int clocks = 3 + optional + HAS_FSGEN;
        for (int failure = 0; failure <= clocks + 1; failure++) {
            struct clk c[5] = {{0,0}, {1,0}, {2,0}, {3,0}, {4,0}};
            struct platform_device p = {0};
            struct macro m = {&p.dev, &c[0], &c[1], &c[2],
                optional ? &c[3] : NULL, HAS_FSGEN ? &c[4] : NULL,
                &map, optional, NULL};
            p.dev.data = &m;
            map = (struct regmap){true, true};
            fail = failure; step = depth = exits = 0;
            int ret = macro_runtime_resume(&p.dev);
            assert(ret == (failure ? -5 : 0));
            if (failure) {
                assert(!depth && map.cache_only && map.dirty);
                for (int i = 0; i < 5; i++) assert(!c[i].refs);
                /* A failed resume remains suspended: remove must not put twice. */
                p.dev.suspended = true;
                macro_remove(&p);
                assert(!depth && p.dev.disabled && p.dev.suspended);
                /* Retry the exact same callback after each failed stage. */
                p.dev.disabled = false;
                fail = step = 0;
                assert(!macro_runtime_resume(&p.dev));
            }
            assert(depth == clocks && !map.cache_only && !map.dirty);
            assert(!macro_runtime_suspend(&p.dev));
            assert(!depth && map.cache_only && map.dirty);
            for (int i = 0; i < 5; i++) assert(!c[i].refs);
            /* Repeated idle cycles and active remove must remain balanced. */
            for (int cycle = 0; cycle < 3; cycle++) {
                step = 0;
                assert(!macro_runtime_resume(&p.dev));
                assert(!macro_runtime_suspend(&p.dev));
            }
            step = 0;
            assert(!macro_runtime_resume(&p.dev));
            p.dev.suspended = false;
            macro_remove(&p);
            assert(!depth && map.cache_only && p.dev.disabled && p.dev.suspended);
        }
    }
    return 0;
}
'''


class RuntimeVotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not UPSTREAM.exists() or not shutil.which('cc'):
            raise unittest.SkipTest('Linux 7.2.10 and a host C compiler are required')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.tree = Path(cls.tmp.name)
        for kind in ('rx', 'tx', 'va'):
            path = Path(f'sound/soc/codecs/lpass-{kind}-macro.c')
            (cls.tree / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(UPSTREAM / path, cls.tree / path)
        subprocess.run(['patch', '-d', str(cls.tree), '-p1', '--batch', '--fuzz=0',
                        '-i', str(ROOT / 'patches/0020-asoc-lpass-macro-runtime-votes.patch')],
                       check=True, stdout=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check_macro(self, kind):
        source = (self.tree / f'sound/soc/codecs/lpass-{kind}-macro.c').read_text()
        callbacks = '\n'.join(function(source, kind + '_macro_' + name)
                              for name in ('runtime_suspend', 'runtime_resume', 'remove'))
        callbacks = callbacks.replace(kind + '_macro', 'macro')
        body = MOCK + callbacks + MAIN.replace('HAS_FSGEN', str(int(kind != 'va')))
        file = self.tree / f'{kind}.c'
        file.write_text(body)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', str(file), '-o', str(file.with_suffix(''))], check=True)
        subprocess.run([str(file.with_suffix(''))], check=True)
        probe = function(source, kind + '_macro_probe')
        self.assertLess(probe.index('pm_runtime_get_noresume(dev)'),
                        probe.index('pm_runtime_enable(dev)'))
        self.assertLess(probe.index('pm_runtime_enable(dev)'),
                        probe.index(kind + '_macro_register_'))
        self.assertIn('pm_runtime_put_autosuspend(dev)', probe)
        error = probe[probe.index('err_pm:'):]
        self.assertLess(error.index('pm_runtime_disable(dev)'), error.index('pm_runtime_put_noidle(dev)'))
        self.assertLess(error.index('regcache_cache_only'), error.index('clk_disable_unprepare'))

    def test_rx(self):
        self.check_macro('rx')

    def test_tx(self):
        self.check_macro('tx')

    def test_va(self):
        self.check_macro('va')


if __name__ == '__main__':
    unittest.main()
