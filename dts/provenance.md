# Board source provenance / 板级源码来源

This file describes the reconstructed board source introduced after the decompiled snapshot was withdrawn. It does not reinstate that snapshot or distribute its private memory data.

| Source | Material retained |
|---|---|
| Project board bring-up | SM8250/PM8150 board baseline, selected peripherals, regulators and keys |
| Project display integration | Dual C-PHY panel and display wiring |
| Project backlight integration | I2C backlight and panel reference |
| Project touch integration | SPI touch wiring and later THP replacement of legacy reset ownership |
| Project battery monitoring | Read-only battery gauge node |
| Project SD voltage adjustment | SD I/O voltage setting |
| Project GPU bring-up | GPU enablement and owner-generated ZAP reservation reference |
| Project display cleanup and mailbox integration | Removal of temporary display-hold and IPCC enablement |
| Project USB integration | USB2 role graph and PM8150B Type-C/VBUS nodes |

The project source layers had accumulated over multiple experiments. The new file combines them in the same order, removes internal include paths and the Bluetooth identity property, and removes the old experiment number from model text. The GPU reservation label is now emitted by the private generator. USB phandle literals are replaced by label references. Historical overrides remain visible rather than being represented as a newly upstreamed minimal design.

Upstream input: Linux 7.2.10 archive SHA-256 `2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3`. The 31 include paths and their content hashes are in upstream-sha256.json; all were checked against the archive. They remain external kernel files with their own notices. The PM8150B interrupt declaration in the project USB delta was taken from upstream pm8150b.dtsi; its Linux Foundation/Linaro BSD-3-Clause notice is retained in the board file and NOTICE. Existing attribution records are retained, and project modifications use GPL-2.0-only. This is not a claim that every inherited hardware description is original project work.

The memory generator follows the project's owner-FDT extraction recipe: copy only RAM/reserved reg and no-map properties from owner runtime FDT, assign standard cmd-db/SMEM roles, retain the deliberate splash no-map policy and construct the known framebuffer description. No private memory include is distributed. A pinned layout fingerprint limits use to the inspected baseline; this is an offline check, not a hardware safety certificate or a grant to redistribute input data.

The old snapshot's incomplete provenance is not used as the source for this reconstruction. It is used only indirectly as a comparison reference: the historical USB-integration DTB. In a private build with aligned reference phandles, the only property differences were model text and omitted Bluetooth address. Natural-handle public builds were repeatable; exact binary identity to the old reference is not claimed. Full board-reconstruction and comparison records are retained privately.

## Later board integration / 后续板级集成

Later project layers add ADSP/ASoC capture and Primary TDM speaker routing, the PM8150B charger binding, Hall GPIO113/121/23 and PM8150L LDO8 at 1.8 V, the existing MMIO timer at `timer@17c20000`, and the video reservation label. The Hall GPIO/supply description was checked against owner stock runtime-FDT evidence and accessory observations; no owner FDT snapshot is included. The memory extractor adds a label to the video reservation, while the generated memory include remains private. These edits keep existing upstream attribution and the board file's combined licence expression. They do not establish rights to redistribute omitted inputs. Single-tablet behavior is documented separately in the hub status; suspend remains U.

后续项目层增加 ADSP／ASoC 录音与 Primary TDM 放音、PM8150B 充电节点、三路霍尔与 1.8 V LDO8、MMIO 定时器及视频保留区标签。霍尔 GPIO／供电经所有者原厂运行时 FDT 和配件观察核对，不分发原厂快照；生成的内存 include 仍为私有。保留已有上游署名和组合许可，不据此授权原输入。单机行为证据另见中心状态页，休眠仍为 U。
