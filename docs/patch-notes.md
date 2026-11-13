# Patch notes

Language: English. 中文构建入口：[README.zh-CN.md](../README.zh-CN.md)。This page describes patch mechanisms/provenance (O); current hardware limits are in the hub [status](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md).

All patches apply to Linux 7.2.10. Evidence classes: H = observed on hardware by the maintainer; O = offline check only.

| # | Patch | Purpose | Upstream suitability |
|---|---|---|---|
| 0001 | dt-bindings: panel nt36523 | Adds the compatible `huawei,dby-w09-nt36523` to the existing Novatek NT36523 panel binding | Suitable once 0002 is |
| 0002 | drm/panel: nt36523 DBY-W09 panel | Adds a panel description (timings, owner-generated command-header integration, reset steps) for this device to the existing Novatek NT36523 driver | Needs rework; initialisation data is device specific |
| 0003 | drm/panel: nt36523 refresh-rate parameters | Adds `refresh_hz` (60 or 120) and `non_burst`, defaulting to 120 Hz; parameters lock at first DBY probe. Also acquires the external backlight directly and controls it through panel enable/disable callbacks for the DRM=y/BACKLIGHT_CLASS_DEVICE=m configuration | Local policy and backlight integration; not prepared for upstream |
| 0004 | drm/msm/dsi: host | Programs the DSI high-speed transmit timeout. The soft-reset default repeatedly times out on this device. The value follows the downstream Qualcomm driver | Candidate; needs an upstream review of the value and the hardware revisions affected |
| 0005 | drm/msm/dsi: 7nm PHY | Applies the clock divider of the master to the slave PHY in bonded C-PHY mode before PLL start; adjusts PLL enable-count handling | Local DBY-W09 adaptation; the original upstream count fix was reverted for a non-bonded regression |
| 0006 | ath11k: QCA6390 caldata | Adds QCA6390 HW2.0 to the calibration-data skip condition, including its BIN board-data case; the hardware-revision condition itself is not restricted to BIN | Candidate |

## Provenance

- The PLL-count portion of 0005 adapts Neil Armstrong's [upstream commit 93c97bc8d85d](https://github.com/torvalds/linux/commit/93c97bc8d85d), retaining local locking and `pll_data`. The original was [reverted in 44784327815b](https://github.com/torvalds/linux/commit/44784327815b) after a non-bonded divider regression. See the [hunk mapping and limitations](provenance-review.md). This is not a complete cherry-pick or a general upstream fix.
- Patch 0004 and the divider-synchronization portion of 0005 were informed by reading the open-source downstream kernel sources published for the device (Qualcomm display driver code and the vendor's PLL divider handling). The two inspected reference files carry GPL-2.0-only notices; the original download page and release identifier remain unverified. See the [per-patch licence table](../THIRD_PARTY.md).
- Patch 0002's command tables were generated from the owner's runtime DTB (104 on and 5 off packets verified). The XBL XML examined later was comparison material, not the direct source. See [provenance review](provenance-review.md) for remaining permission questions and exact downstream reference files.

## Verification

Patches 0001–0006 applied in order with zero fuzz to pristine files from the 7.2.10 archive reproduce the source files used to build the tested kernel and modules, byte for byte (class O). Functional behaviour (display, wireless) was observed on one device (class H).

## Owner-data separation

Command arrays are no longer embedded in 0002. Use [the extraction tool and guide](panel-data.md) to supply the private header before compiling. Patch 0003 still relies on the pinned packet ordering. Zero-fuzz replay was repeated after this change; no complete rebuild or device validation was performed.

## Four-channel capture (H + R, 2026-11-06)

Patch `0008` preserves the negotiated channel interval only for
`TX_CODEC_DMA_TX_3`. The AFE and TX macro DAIs allow 1–8 channels and
WCD938x capture allows 1–4, so their intersection permits four channels.
The machine driver's hardcoded fixup has no DT property override.
All other backends retain stereo; every backend retains 48 kHz/S16_LE.
The externally rebuilt `snd-soc-sm8250` module supplements the historical
six-patch full build without rebuilding Image or changing DTB, and was
validated on one tablet (H + R, 2026-11-06, bundle `20261102-12`) with
real simultaneous signal on all four analog microphone channels.

## A3a Primary TDM speaker transport (O)

Patch 0009 carries DT data-output, sync inversion and data delay fields through
q6afe-dai into the q6afe APR TDM configuration. Patch 0010 applies after 0008,
preserves negotiated Primary TDM0 channels, sets a 6.144 MHz bit clock, and
configures four 32-bit slots with byte offsets 0, 4, 8, 12. Shutdown disables that
clock and retains SoundWire cleanup. The four-microphone fix remains intact.

The board enables GPI DMA0 and I2C3, four board-specific TFA9874 codecs, the shared
active-high reset on GPIO109, and Primary TDM pins 138..141. New phandles occupy
0x100e..0x1013. The DTB test checks these values and restricts raw property changes
to the audio allowlist, including only the DMA status property. WSA stays disabled.

The companion amplifier module requires [private table generation](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md) before building, with `TFA_TABLES_DIR` pointing to the generated header. These owner inputs are not distributed. / 喇叭模块构建前须从所有者自己的配置生成私有表，并通过 `TFA_TABLES_DIR` 指定；所有者数据不分发。

The companion amplifier module defaults locked off. UCM2 remains microphone-only.
Host patch replay, compilation and DT comparison are O; I2C probe, TDM timing,
speaker output and coexistence with capture still require owner device testing (U).

A3b extends 0010's Primary TDM fixup: reject channel minimum greater than four and
cap maximum at four. The executable harness covers all frontend IDs and channel
intervals 1..8, including rejection and the unchanged microphone branch (O).

Device result (H + R, 2026-11-07, one tablet, Linux package `20261102-16`): with
patches 0009/0010 and the companion amplifier module, all four TFA9874 amplifiers
locked to Primary TDM0 and played desktop audio with no clock, TDM or clip flags,
and four-channel capture kept working. Desktop loudness depends on the Linux
package's WirePlumber S16LE rule; this kernel tree is unchanged by that rule.
