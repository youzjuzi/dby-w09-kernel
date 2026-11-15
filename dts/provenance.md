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

Upstream input: Linux 7.2.10 archive SHA-256 `2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3`. The 32 include paths and their content hashes are in upstream-sha256.json; all were checked against the archive. They remain external kernel files with their own notices. The PM8150B interrupt declaration in the project USB delta was taken from upstream pm8150b.dtsi; its Linux Foundation/Linaro BSD-3-Clause notice is retained in the board file and NOTICE. Existing attribution records are retained, and project modifications use GPL-2.0-only. This is not a claim that every inherited hardware description is original project work.

The memory generator follows the project's owner-FDT extraction recipe: copy only RAM/reserved reg and no-map properties from owner runtime FDT, assign standard cmd-db/SMEM roles, retain the deliberate splash no-map policy and construct the known framebuffer description. No private memory include is distributed. A pinned layout fingerprint limits use to the inspected baseline; this is an offline check, not a hardware safety certificate or a grant to redistribute input data.

The old snapshot's incomplete provenance is not used as the source for this reconstruction. It is used only indirectly as a comparison reference: the historical USB-integration DTB. In a private build with aligned reference phandles, the only property differences were model text and omitted Bluetooth address. Natural-handle public builds were repeatable; exact binary identity to the old reference is not claimed. Full board-reconstruction and comparison records are retained privately.

## Later board integration / 后续板级集成

Later project layers add ADSP/ASoC capture and Primary TDM speaker routing, the PM8150B charger binding, Hall GPIO113/121/23 and PM8150L LDO8 at 1.8 V, the existing MMIO timer at `timer@17c20000`, and the video reservation label. The Hall GPIO/supply description was checked against owner stock runtime-FDT evidence and accessory observations; no owner FDT snapshot is included. The memory extractor adds a label to the video reservation, while the generated memory include remains private. These edits keep existing upstream attribution and the board file's combined licence expression. They do not establish rights to redistribute omitted inputs. Single-tablet behavior is documented separately in the hub status; suspend remains U.

后续项目层增加 ADSP／ASoC 录音与 Primary TDM 放音、PM8150B 充电节点、三路霍尔与 1.8 V LDO8、MMIO 定时器及视频保留区标签。霍尔 GPIO／供电经所有者原厂运行时 FDT 和配件观察核对，不分发原厂快照；生成的内存 include 仍为私有。保留已有上游署名和组合许可，不据此授权原输入。单机行为证据另见中心状态页，休眠仍为 U。

The charging indicator uses minimal PM8150L parent/LPG declarations from upstream
`pm8150l.dtsi`, retaining the Linux Foundation/Linaro notice in the board source.
The empty USID 4 node supplies read-only revision information; only USID 5 hosts
the LPG. Owner runtime-FDT wiring maps PWM 0/red and PWM 1/green to upstream LED
reg 1/2. Stock brightness ratios 70/255 and 120/255 are now applied by the charger LED triggers (previously userspace).
No blue, flash, WLED or other PM8150L child is enabled. On one tablet (2026-11-15,
H + R) the red/green channels and the shutdown turn-off were confirmed.

充电指示灯采用上游 PM8150L 最小父节点与 LPG 声明，保留原署名。USID 4
仅供读取版本，USID 5 承载红绿灯；原厂运行时 FDT 的 PWM 0/1 对应上游
LED reg 1/2，亮度比例为 70/255、120/255。未启用蓝灯、闪光灯、WLED
及其它子设备。2026-11-15 一台平板实机确认红绿通道与关机灭灯(H + R)。


The charger IRQ tuples come from owner stock runtime-FDT `qpnp-smb5` nodes:
`chg-state-change` at USID 2/block 0x10/bit 1 rising,
`usbin-plugin` at USID 2/block 0x13/bit 4 both edges, and
`wdog-bark` at USID 2/block 0x16/bit 1 rising. The Linux 7.2.10 upstream
`drivers/power/supply/qcom_smbx.c` named threaded-IRQ and watchdog-bark handling
provided the API/handling pattern; its PMIC support is not claimed for PM8150B.
The charger retains its own health and write gates. The two LPG
`linux,default-trigger` properties select project simple LED triggers;
no additional PMIC peripherals are enabled. On one tablet (2026-11-15, H) the
three IRQs registered and only their enable bits were set.


The FG `msoc-delta` tuple (USID 2, block 0x40, bit 3, rising edge) comes from
the owner stock runtime-FDT `qcom,fg-batt-soc@4000` node. The linked
`simple-battery` declares lithium-ion-polymer chemistry, design charge 7150 mAh
and maximum design voltage 4.4 V, using the task's stock battery-profile evidence
(DesayAtl and SunwodaCosmx have the same capacity/voltage). Design energy
27670500 uWh is explicitly **estimated** as 7150 mAh × 3.87 V; the nominal
3.87 V is not supplied by that FDT and remains unverified. No temperature,
resistance, OCV table or FG SRAM programming is added. The Linux 7.2.10
power-supply core supplies these design properties from `monitored-battery`.
On one tablet (2026-11-15, H) the IRQ registered with only its enable bit set
and the four design properties appeared in sysfs; the IRQ fired about every
60–130 s while discharging but not in step with displayed `capacity` changes,
so it is kept only as an extra notification.
