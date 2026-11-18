#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay the 7nm DSI C-PHY patch and verify register programming on host."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
_CANDIDATES = [ROOT.parent / 'upstream/linux-7.2.10']
if len(ROOT.parents) >= 3:
    _CANDIDATES.append(ROOT.parents[2] / 'upstream/linux-7.2.10')
UPSTREAM = next((p for p in _CANDIDATES if p.is_dir()), _CANDIDATES[0])
SOURCE = Path('drivers/gpu/drm/msm/dsi/phy/dsi_phy_7nm.c')


def function(text, name):
    pos = text.index(name + '(')
    start = text.rfind('\n', 0, pos) + 1
    begin = text.index('{', pos)
    depth = 1
    end = begin + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


MOCK = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef uint32_t u32;
#define __iomem

#define REG_DSI_7nm_PHY_CMN_CLK_CFG1 0x00000014u
#define REG_DSI_7nm_PHY_CMN_CTRL_3   0x00000030u
#define REG_DSI_7nm_PHY_CMN_CTRL_5   0x000001b0u

#define DSI_7nm_PHY_CMN_CLK_CFG1_CLK_EN             0x00000020u
#define DSI_7nm_PHY_CMN_CLK_CFG1_CLK_EN_SEL         0x00000010u
#define DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL__MASK   0x0000000cu
#define DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL__SHIFT  2u
static inline u32 DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL(u32 val)
{
	return (val << DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL__SHIFT) &
	       DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL__MASK;
}
#define DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL__MASK   0x00000003u
#define DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL__SHIFT  0u
static inline u32 DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL(u32 val)
{
	return (val << DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL__SHIFT) &
	       DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL__MASK;
}

#define DSI_MAX 2
#define DSI_PHY_7NM_QUIRK_V7_2 (1u << 2)
#define DBG(...) ((void)0)
#define spin_lock_irqsave(l, f) ((void)(l), (f) = 0)
#define spin_unlock_irqrestore(l, f) ((void)(l), (void)(f))

enum msm_dsi_phy_usecase {
	MSM_DSI_PHY_STANDALONE,
	MSM_DSI_PHY_MASTER,
	MSM_DSI_PHY_SLAVE,
};

struct msm_dsi_phy_cfg { u32 quirks; };
struct msm_dsi_phy {
	int id;
	bool cphy_mode;
	enum msm_dsi_phy_usecase usecase;
	const struct msm_dsi_phy_cfg *cfg;
	void __iomem *base;
	void *vco_hw;
};
struct dsi_pll_7nm {
	struct msm_dsi_phy *phy;
	struct dsi_pll_7nm *slave;
	int pclk_mux_lock;
};

static struct dsi_pll_7nm *pll_7nm_list[DSI_MAX];
static inline struct dsi_pll_7nm *to_pll_7nm(void *hw)
{
	return (struct dsi_pll_7nm *)hw;
}

struct mmio_bank { u32 clk_cfg1, ctrl_3, ctrl_5, writes; };
static struct mmio_bank banks[DSI_MAX];
static u32 *bank_reg(const void __iomem *addr, struct mmio_bank **out_bank)
{
	uintptr_t raw = (uintptr_t)addr;
	uintptr_t idx = (raw >> 12) - 1u;
	uintptr_t off = raw & 0xfffu;
	assert(idx < DSI_MAX);
	*out_bank = &banks[idx];
	if (off == REG_DSI_7nm_PHY_CMN_CLK_CFG1) return &(*out_bank)->clk_cfg1;
	if (off == REG_DSI_7nm_PHY_CMN_CTRL_3) return &(*out_bank)->ctrl_3;
	if (off == REG_DSI_7nm_PHY_CMN_CTRL_5) return &(*out_bank)->ctrl_5;
	assert(0 && "unexpected register offset");
	return NULL;
}
static u32 readl(const void __iomem *addr)
{
	struct mmio_bank *b;
	return *bank_reg(addr, &b);
}
static void writel(u32 val, void __iomem *addr)
{
	struct mmio_bank *b;
	u32 *reg = bank_reg(addr, &b);
	*reg = val;
	b->writes++;
}
'''

HARNESS = r'''
static struct msm_dsi_phy_cfg cfgs[DSI_MAX];
static struct msm_dsi_phy phys[DSI_MAX];
static struct dsi_pll_7nm plls[DSI_MAX];

static void setup_phys(bool cphy, u32 quirks0, u32 quirks1)
{
	memset(banks, 0, sizeof(banks));
	cfgs[0].quirks = quirks0;
	cfgs[1].quirks = quirks1;
	for (int i = 0; i < DSI_MAX; i++) {
		phys[i] = (struct msm_dsi_phy){
			.id = i,
			.cphy_mode = cphy,
			.usecase = MSM_DSI_PHY_STANDALONE,
			.cfg = &cfgs[i],
			.base = (void __iomem *)((uintptr_t)(i + 1) * 0x1000u),
			.vco_hw = &plls[i],
		};
		plls[i] = (struct dsi_pll_7nm){ .phy = &phys[i], .slave = NULL };
		pll_7nm_list[i] = &plls[i];
	}
}

int main(void)
{
	/* Bonded dual-DSI C-PHY across 5 reset/enable/disable cycles: */
	setup_phys(true, 0, 0);
	phys[0].usecase = MSM_DSI_PHY_MASTER;
	phys[1].usecase = MSM_DSI_PHY_SLAVE;
	for (int n = 0; n < 5; n++) {
		/* Simulate msm_dsi_host_reset_phy() clearing both banks: */
		banks[0].clk_cfg1 = 0;
		banks[1].clk_cfg1 = 0;
		assert(dsi_7nm_set_usecase(&phys[0]) == 0);
		assert(plls[0].slave == &plls[1]);
		assert(banks[0].clk_cfg1 == 0x03u);
		/* Master also runs restore_pll_state() -> DSICLK_SEL=3: */
		dsi_pll_cmn_clk_cfg1_update(&plls[0],
			DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL__MASK,
			DSI_7nm_PHY_CMN_CLK_CFG1_DSICLK_SEL(3));
		assert(banks[0].clk_cfg1 == 0x03u);

		/* Slave skips restore_pll_state() in dsi_phy.c: */
		assert(dsi_7nm_set_usecase(&phys[1]) == 0);
		assert(banks[1].clk_cfg1 == 0x07u);

		dsi_pll_enable_global_clk(&plls[0]);
		dsi_pll_enable_global_clk(&plls[1]);
		assert(banks[0].clk_cfg1 == 0x33u);
		assert(banks[1].clk_cfg1 == 0x37u);
		assert(banks[0].ctrl_3 == 0x04u && banks[1].ctrl_3 == 0x04u);

		dsi_pll_disable_global_clk(&plls[0]);
		dsi_pll_disable_global_clk(&plls[1]);
		assert(banks[0].clk_cfg1 == 0x13u);
		assert(banks[1].clk_cfg1 == 0x17u);
	}

	/* Standalone C-PHY with zeroed register and no restore_pll_state: */
	setup_phys(true, 0, 0);
	phys[0].usecase = MSM_DSI_PHY_STANDALONE;
	assert(dsi_7nm_set_usecase(&phys[0]) == 0);
	assert(banks[0].clk_cfg1 == 0x03u);
	dsi_pll_enable_global_clk(&plls[0]);
	assert(banks[0].clk_cfg1 == 0x33u);

	/* D-PHY mode: preserve DSICLK_SEL and upper bits untouched; check V7_2 quirk: */
	setup_phys(false, DSI_PHY_7NM_QUIRK_V7_2, DSI_PHY_7NM_QUIRK_V7_2);
	const enum msm_dsi_phy_usecase ucs[] = {
		MSM_DSI_PHY_STANDALONE, MSM_DSI_PHY_MASTER, MSM_DSI_PHY_SLAVE
	};
	for (unsigned u = 0; u < 3; u++) {
		for (u32 sel = 0; sel < 4; sel++) {
			banks[0].clk_cfg1 = 0x30u | DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL(3) | sel;
			banks[0].ctrl_5 = 0;
			phys[0].usecase = ucs[u];
			assert(dsi_7nm_set_usecase(&phys[0]) == 0);
			u32 want_bitclk = (ucs[u] == MSM_DSI_PHY_SLAVE) ? 1u : 0u;
			assert(banks[0].clk_cfg1 ==
			       (0x30u | DSI_7nm_PHY_CMN_CLK_CFG1_BITCLK_SEL(want_bitclk) | sel));
			assert(banks[0].ctrl_5 == ((ucs[u] == MSM_DSI_PHY_MASTER) ? 0x07u : 0x00u));
		}
	}

	/* Invalid usecase returns -EINVAL with zero MMIO writes: */
	setup_phys(true, 0, 0);
	phys[0].usecase = (enum msm_dsi_phy_usecase)99;
	assert(dsi_7nm_set_usecase(&phys[0]) == -EINVAL);
	assert(banks[0].writes == 0);

	puts("PASS: bonded C-PHY 0x33/0x37 across 5 cycles, standalone C-PHY, D-PHY preservation, invalid usecase");
	return 0;
}
'''


class DsiPhy7nmCphy(unittest.TestCase):
    def test_replay_and_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / SOURCE
            target.parent.mkdir(parents=True)
            shutil.copyfile(UPSTREAM / SOURCE, target)
            for num in ('0005', '0012'):
                patch = next((ROOT / 'patches').glob(num + '-*.patch'))
                res = subprocess.run(
                    ['patch', '--batch', '--fuzz=0', '-p1', '-d', tmp, '-i', str(patch)],
                    check=True, capture_output=True, text=True,
                )
                self.assertNotIn('offset', res.stdout)
                self.assertNotIn('fuzz', res.stdout)
            before17 = target.read_text()

            patch17 = ROOT / 'patches/0017-drm-msm-dsi-phy-7nm-cphy-dsiclk-sel.patch'
            res = subprocess.run(
                ['patch', '--batch', '--fuzz=0', '-p1', '-d', tmp, '-i', str(patch17)],
                check=True, capture_output=True, text=True,
            )
            self.assertNotIn('offset', res.stdout)
            self.assertNotIn('fuzz', res.stdout)
            after17 = target.read_text()

            old_fn = function(before17, 'static int dsi_7nm_set_usecase')
            new_fn = function(after17, 'static int dsi_7nm_set_usecase')
            self.assertNotEqual(old_fn, new_fn)
            self.assertEqual(before17.replace(old_fn, ''), after17.replace(new_fn, ''))

            extracted = '\n'.join([
                function(after17, 'static void dsi_pll_cmn_clk_cfg1_update'),
                function(after17, 'static void dsi_pll_disable_global_clk'),
                function(after17, 'static void dsi_pll_enable_global_clk'),
                new_fn,
            ])
            src = root / 'phy-cphy-test.c'
            exe = root / 'phy-cphy-test'
            src.write_text(MOCK + extracted + HARNESS)
            subprocess.run([
                'cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=undefined', '-fno-sanitize-recover=all',
                str(src), '-o', str(exe),
            ], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    unittest.main()
