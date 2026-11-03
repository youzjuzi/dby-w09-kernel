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
