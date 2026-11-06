#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Zero-fuzz replay and executable fixup regression against Linux 7.2.10."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'
PATCH = ROOT / 'patches/0008-asoc-qcom-sm8250-preserve-tx-codec-dma-channels.patch'
SOURCE = Path('sound/soc/qcom/sm8250.c')


class CaptureFixup(unittest.TestCase):
    def test_patch_and_behavior(self):
        original = (UPSTREAM / SOURCE).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            target = work / SOURCE
            target.parent.mkdir(parents=True)
            shutil.copyfile(UPSTREAM / SOURCE, target)
            result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1',
                                     '-d', str(work), '-i', str(PATCH)],
                                    check=True, capture_output=True, text=True)
            self.assertNotIn('offset', result.stdout)
            patched = target.read_text()
            second = next((ROOT / 'patches').glob('0010-*'))
            result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1',
                                     '-d', str(work), '-i', str(second)],
                                    check=True, capture_output=True, text=True)
            self.assertNotIn('offset', result.stdout)
            patched = target.read_text()
            self.assertIn('.hw_params = sm8250_snd_hw_params,', patched)
            self.assertIn('.shutdown = sm8250_snd_shutdown,', patched)
            self.assertIn('GENMASK(channels - 1, 0), 4, 32)', patched)
            self.assertIn('6144000, SNDRV_PCM_STREAM_PLAYBACK)', patched)
            self.assertIn('0, SNDRV_PCM_STREAM_PLAYBACK)', patched)
            self.assertIn('qcom_snd_sdw_shutdown(substream);', patched)
            function = re.search(r'static int sm8250_be_hw_params_fixup\(.*?\n}',
                                 patched, re.S).group()
            header = UPSTREAM / 'include/dt-bindings/sound/qcom,q6dsp-lpass-ports.h'
            ids = sorted(set(int(n) for n in re.findall(
                r'^#define\s+\w+\s+(\d+)\s*$', header.read_text(), re.M)))
            self.assertGreater(len(ids), 100)
            harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include "qcom,q6dsp-lpass-ports.h"
#define SNDRV_PCM_HW_PARAM_RATE 0
#define SNDRV_PCM_HW_PARAM_CHANNELS 1
#define SNDRV_PCM_HW_PARAM_FORMAT 2
#define SNDRV_PCM_FORMAT_S16_LE 2
struct snd_interval { unsigned min, max; };
struct snd_mask { unsigned bits; };
struct snd_pcm_hw_params { struct snd_interval intervals[2]; struct snd_mask fmt; };
struct snd_soc_dai { int id; };
struct snd_soc_pcm_runtime { struct snd_soc_dai cpu; };
#define hw_param_interval(p, i) (&(p)->intervals[i])
#define hw_param_mask(p, i) (&(p)->fmt)
#define snd_soc_rtd_to_cpu(r, i) (&(r)->cpu)
static void snd_mask_set_format(struct snd_mask *m, unsigned f) { m->bits |= 1U << f; }
'''
            harness += function + '\nint main(void) {\nint ids[] = {'
            harness += ','.join(map(str, ids)) + '};\n'
            harness += r'''
unsigned count = 0;
for (unsigned i = 0; i < sizeof(ids)/sizeof(ids[0]); i++)
 for (unsigned lo = 1; lo <= 8; lo++)
  for (unsigned hi = lo; hi <= 8; hi++)
   for (unsigned bits = 0; bits < 8; bits++) {
    struct snd_soc_pcm_runtime r = { .cpu = { .id = ids[i] } };
    struct snd_pcm_hw_params p = { .intervals = {{8000,192000},{lo,hi}}, .fmt = {bits} };
    int ret = sm8250_be_hw_params_fixup(&r, &p);
    count++;
    if (ids[i] == PRIMARY_TDM_RX_0 && lo > 4) {
     assert(ret == -EINVAL);
     assert(p.intervals[1].min == lo && p.intervals[1].max == hi);
     continue;
    }
    assert(ret == 0);
    assert(p.intervals[0].min == 48000 && p.intervals[0].max == 48000);
    assert(p.intervals[1].min == ((ids[i] == TX_CODEC_DMA_TX_3 || ids[i] == PRIMARY_TDM_RX_0) ? lo : 2));
    assert(p.intervals[1].max == (ids[i] == PRIMARY_TDM_RX_0 ? (hi > 4 ? 4 : hi) : ids[i] == TX_CODEC_DMA_TX_3 ? hi : 2));
    assert(p.fmt.bits == (bits | (1U << SNDRV_PCM_FORMAT_S16_LE)));
   }
printf("PASS: %u fixup combinations\n", count);
return 0;
}
'''
            (work / 'test.c').write_text(harness)
            subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                            '-I', str(header.parent), str(work / 'test.c'),
                            '-o', str(work / 'test')], check=True)
            subprocess.run([str(work / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
