#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay patches and execute actual panel power functions with fake regulators."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'
SOURCE = Path('drivers/gpu/drm/panel/panel-novatek-nt36523.c')
BINDING = Path('Documentation/devicetree/bindings/display/panel/novatek,nt36523.yaml')


def replay(work):
    for name in (SOURCE, BINDING):
        dest = work / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(UPSTREAM / name, dest)
    for number in ('0001', '0002', '0003', '0011'):
        patch = next((ROOT / 'patches').glob(number + '-*.patch'))
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(work),
                                 '-i', str(patch)], capture_output=True, text=True, check=True)
        assert 'offset' not in result.stdout and 'fuzz' not in result.stdout
    return (work / SOURCE).read_text()


class PanelPower(unittest.TestCase):
    def test_actual_functions(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source = replay(work)
            names = ['nt36523_full_power', 'nt36523_power_off', 'nt36523_power_on',
                     'nt36523_prepare_power', 'nt36523_prepare', 'nt36523_unprepare']
            functions = '\n'.join(re.search(r'static (?:int|bool) ' + name +
                                  r'\(.*?\n}', source, re.S).group() for name in names)
            harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define BIT(i) (1UL << (i))
#define ARRAY_SIZE(a) ((int)(sizeof(a)/sizeof((a)[0])))
#define dev_err(...) ((void)0)
struct regulator { int id, refs; };
struct drm_panel { void *dev; };
struct panel_info;
struct panel_desc { int (*init_sequence)(struct panel_info *); };
struct panel_info {
 struct drm_panel panel;
 struct regulator *vci, *vddio, *vsp, *vsn;
 unsigned long power_enabled;
 bool boot_power_cycled;
 void *reset_gpio;
 struct panel_desc *desc;
};
static int events[1024], n, fail_enable=-1, fail_disable=-1, fail_init;
static void emit(int x) { assert(n < 1024); events[n++]=x; }
static void msleep(int ms) { emit(1000+ms); }
static int regulator_enable(struct regulator *r) {
 emit(100+r->id); if(r->id == fail_enable) return -EIO;
 assert(r->refs == 0); r->refs++; return 0;
}
static int regulator_disable(struct regulator *r) {
 emit(200+r->id); assert(r->refs == 1);
 if(r->id == fail_disable) return -EIO;
 r->refs--; return 0;
}
static void gpiod_set_value_cansleep(void *p, int x) { (void)p; assert(x==1); emit(300); }
static struct panel_info *to_panel_info(struct drm_panel *p) { return (struct panel_info *)p; }
static void nt36523_reset(struct panel_info *p) { (void)p; emit(400); }
static int init(struct panel_info *p) { (void)p; emit(500); return fail_init ? -EIO : 0; }
'''
            harness += functions + r'''
static struct regulator rails[4];
static struct panel_desc desc = { init };
static struct panel_info setup(unsigned mask) {
 for(int i=0;i<4;i++) rails[i]=(struct regulator){i,0};
 n=0; fail_enable=fail_disable=-1; fail_init=0;
 return (struct panel_info){ .vci=mask&1?&rails[0]:NULL, .vddio=&rails[1],
 .vsp=mask&2?&rails[2]:NULL, .vsn=mask&4?&rails[3]:NULL, .desc=&desc };
}
static void empty(void) { for(int i=0;i<4;i++) assert(rails[i].refs==0); }
int main(void) {
 struct panel_info p=setup(0);
 assert(nt36523_prepare(&p.panel)==0); assert(nt36523_unprepare(&p.panel)==0);
 int legacy[]={101,400,500,300,201};
 assert(n==ARRAY_SIZE(legacy) && !memcmp(events,legacy,sizeof(legacy))); empty();
 p=setup(0);fail_enable=1;assert(nt36523_prepare(&p.panel)==-EIO);assert(n==1);empty();
 p=setup(0);fail_init=1;assert(nt36523_prepare(&p.panel)==-EIO);
 int legacy_fail[]={101,400,500,201};
 assert(n==ARRAY_SIZE(legacy_fail) && !memcmp(events,legacy_fail,sizeof(legacy_fail)));empty();
 p=setup(7);assert(nt36523_prepare(&p.panel)==0);
 int full[]={100,1001,101,1002,102,1002,103,1002,300,1005,203,1005,202,1010,201,200,1001,1100,
             100,1001,101,1002,102,1002,103,1002,400,500};
 assert(n==ARRAY_SIZE(full) && !memcmp(events,full,sizeof(full)));
 assert(nt36523_unprepare(&p.panel)==0);empty();n=0;
 assert(nt36523_prepare(&p.panel)==0);
 int repeat[]={100,1001,101,1002,102,1002,103,1002,400,500};
 assert(n==ARRAY_SIZE(repeat) && !memcmp(events,repeat,sizeof(repeat)));
 assert(nt36523_unprepare(&p.panel)==0);empty();
 for(unsigned mask=1;mask<8;mask++) {
  p=setup(mask);assert(nt36523_prepare(&p.panel)==0);assert(p.boot_power_cycled);
  assert(nt36523_unprepare(&p.panel)==0);empty();
  for(int rail=0;rail<4;rail++) {
   p=setup(mask);struct regulator *present[]={p.vci,p.vddio,p.vsp,p.vsn};
   if(!present[rail]) continue;
   fail_enable=rail;assert(nt36523_prepare(&p.panel)==-EIO);empty();assert(!p.boot_power_cycled);
   fail_enable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
   p=setup(mask);fail_disable=rail;assert(nt36523_prepare(&p.panel)==-EIO);
   assert(!p.boot_power_cycled && rails[rail].refs==1);
   fail_disable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
   p=setup(mask);assert(nt36523_prepare(&p.panel)==0);fail_disable=rail;
   assert(nt36523_unprepare(&p.panel)==-EIO);assert(rails[rail].refs==1);
   fail_disable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
  }
  p=setup(mask);fail_init=1;assert(nt36523_prepare(&p.panel)==-EIO);empty();
 }
 puts("PASS: legacy traces, 7 supply combinations, all enable/disable failures and retries");
}
'''
            (work / 'test.c').write_text(harness)
            subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Wno-unused-variable',
                            '-Werror', str(work / 'test.c'), '-o', str(work / 'test')], check=True)
            subprocess.run([str(work / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
