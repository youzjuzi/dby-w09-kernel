# Third-party components

## Verified and unresolved scope / 已核实与未核实范围

Verified locally: the Linux 7.2.10 target-file SPDX headers listed below; the earlier archive/member comparison and downstream notices recorded in the [source review](docs/provenance-review.md); and the recorded upstream PLL-count attribution and revert, distinct from downstream divider synchronization.

Unresolved: the downstream release identifier and original download page have not been independently reverified; permission to redistribute extracted panel data and complete attribution/correspondence of the historical DTS input chain remain unclosed. The command arrays and decompiled snapshot are excluded from the current tree. Documentation cleanup does not close the provenance gate or establish complete release clearance.

| Component | Version | Licence | Use |
|---|---|---|---|
| Linux kernel | 7.2.10 | GPL-2.0-only; exceptions and dual licences are file-specific | Baseline; modified by the patches (not redistributed here) |
| Downstream kernel sources published for the device | local archive pinned in source review; release/download page unverified | GPL-2.0-only in the two inspected reference files | Reference for 0004 and the divider-synchronization part of 0005; no complete reference files are redistributed |

The PLL-count portion of 0005 is adapted from Neil Armstrong's Linux commit [93c97bc8d85d](https://github.com/torvalds/linux/commit/93c97bc8d85d), under the Linux source licensing noted above. The original change was reverted upstream in [44784327815b](https://github.com/torvalds/linux/commit/44784327815b); local adaptation and regression limits are recorded in [the source review](docs/provenance-review.md). This inventory covers identified components; it is not a claim of exhaustive legal clearance.

## Per-patch licensing (Linux 7.2.10 headers checked locally)

The target-file SPDX values below were read from the local upstream Linux 7.2.10 source. Existing copyright notices and file-specific terms remain applicable; the repository GPL text does not replace them.

| Patch | Upstream target file | Target SPDX (verbatim) | Treatment of project changes |
|---|---|---|---|
| [0001-dt-bindings-panel-nt36523-add-dby-w09.patch](patches/0001-dt-bindings-panel-nt36523-add-dby-w09.patch) | `Documentation/devicetree/bindings/display/panel/novatek,nt36523.yaml` | `GPL-2.0-only OR BSD-2-Clause` | Project changes follow the same dual licence. |
| [0002-drm-panel-nt36523-add-dby-w09-panel.patch](patches/0002-drm-panel-nt36523-add-dby-w09-panel.patch) | `drivers/gpu/drm/panel/panel-novatek-nt36523.c` | `GPL-2.0-only` | Project changes follow GPL-2.0-only. |
| [0003-drm-panel-nt36523-refresh-rate-parameters.patch](patches/0003-drm-panel-nt36523-refresh-rate-parameters.patch) | `drivers/gpu/drm/panel/panel-novatek-nt36523.c` | `GPL-2.0-only` | Project changes follow GPL-2.0-only. |
| [0004-drm-msm-dsi-host-dby-w09.patch](patches/0004-drm-msm-dsi-host-dby-w09.patch) | `drivers/gpu/drm/msm/dsi/dsi_host.c` | `GPL-2.0-only` | Project changes follow GPL-2.0-only. |
| [0005-drm-msm-dsi-phy-7nm-dby-w09.patch](patches/0005-drm-msm-dsi-phy-7nm-dby-w09.patch) | `drivers/gpu/drm/msm/dsi/phy/dsi_phy_7nm.c` | `GPL-2.0` | Preserve the literal legacy SPDX above; project adaptation follows GPL version 2 only. Count and divider sources are separately described below. |
| [0006-ath11k-qca6390-skip-caldata.patch](patches/0006-ath11k-qca6390-skip-caldata.patch) | `drivers/net/wireless/ath/ath11k/qmi.c` | `BSD-3-Clause-Clear` | Project changes follow BSD-3-Clause-Clear; not GPL-only. |
| [0007-iio-adc-qcom-spmi-adc5-add-bat-therm-30k.patch](patches/0007-iio-adc-qcom-spmi-adc5-add-bat-therm-30k.patch) | `drivers/iio/adc/qcom-spmi-adc5.c` | `GPL-2.0` | Project channel-table addition, preserving the upstream SPDX and standard voltage conversion. Temperature interpretation is not part of this patch. |
| [0008-asoc-qcom-sm8250-preserve-tx-codec-dma-channels.patch](patches/0008-asoc-qcom-sm8250-preserve-tx-codec-dma-channels.patch) | `sound/soc/qcom/sm8250.c` | `GPL-2.0` | Project capture-channel fixup, preserving the upstream SPDX and standard ASoC negotiation. |
| [0009](patches/0009-asoc-qcom-qdsp6-q6afe-propagate-tdm-dt-config.patch) | `sound/soc/qcom/qdsp6/q6afe.h`, `q6afe.c`, `q6afe-dai.c` | `GPL-2.0` | Project DT-to-APR field propagation; existing notices retained. |
| [0010](patches/0010-asoc-qcom-sm8250-add-primary-tdm-rx0-support.patch) | `sound/soc/qcom/sm8250.c` | `GPL-2.0` | Project Primary TDM startup, shutdown, slot and channel-map support after 0008. |

0005 has two distinct source chains: its PLL-count adaptation follows Neil Armstrong's upstream commit and subsequent revert linked above; its divider synchronization follows the downstream `dsi_pll_7nm.c` reference, whose GPL-2.0-only notice and archive-member identity were checked locally. The downstream download/release provenance remains unresolved. The target's literal `GPL-2.0` identifier is retained in this table rather than silently rewritten.

[BSD-3-Clause-Clear](LICENSES/BSD-3-Clause-Clear.txt) is copied byte-for-byte, including metadata, from Linux 7.2.10's `LICENSES/preferred/BSD-3-Clause-Clear`. Existing [BSD-3-Clause.txt](LICENSES/BSD-3-Clause.txt) is a different licence and cannot replace it; the Clear text expressly grants no patent rights.

## Owner-supplied data

Panel command arrays and the decompiled board snapshot are no longer distributed. Local originals are retained privately; [panel extraction](docs/panel-data.md) produces a private header. The extractor licence does not grant rights to its input/output data. dts/NOTICE retains historical attribution records only.

Patch 0001 modifies an upstream YAML binding marked `GPL-2.0-only OR BSD-2-Clause`; source licensing follows the original file rather than a blanket repository-wide assumption. Patch 0002 now contains logic that includes an owner-generated header, not the extracted command arrays.

## 2026-10-29 local provenance check

See [the source review](docs/provenance-review.md) for pinned archive/member hashes, confirmed downstream GPL notices, the runtime-DTB origin of panel command data, and the recovered but incompletely verified DTS lineage. Panel-data permission and complete DT attribution remain unresolved; the two downstream reference file declarations have been verified locally.

## Reconstructed board source

The standalone board DTS is assembled from project source layers and uses external upstream includes; it does not restore the withdrawn decompiled snapshot. See [board provenance](dts/provenance.md) for source layers, upstream hashes, retained PM8150B attribution and owner-generated private memory inputs. No hardware verification was claimed by the initial 2026-10-29 source reconstruction/check alone. Later, separately scoped device evidence is recorded in the [README](README.md#scope-and-evidence); it does not establish complete provenance clearance.

## Board integration added after the initial release candidate

The project board source adds onboard audio/TDM routes, a PM8150B charger node, Hall input wiring and its PM8150L LDO8 supply, the standard MMIO timer enable and the video reservation reference. GPIO/supply parameters were checked against owner runtime-FDT evidence; that input is not distributed. These project edits retain the board file's `GPL-2.0-only AND BSD-3-Clause` notice and the existing upstream notices; the factual comparison does not license the original FDT or close its historical attribution gaps. The timer uses upstream `ARM_ARCH_TIMER` support. Patches 0007–0010 are project changes to the upstream ADC/ASoC files listed above, not imported vendor source files.

板级增量含音频／TDM、充电节点、霍尔 GPIO／LDO8、标准 MMIO 定时器及视频保留区引用。GPIO／供电参数经所有者运行时 FDT 核对，原输入不分发；保留现有板级双重声明和上游署名，不由事实核对推导原厂 FDT 的许可。0007–0010 是上表上游 ADC／ASoC 文件的项目修改，历史归属缺口仍未关闭。
