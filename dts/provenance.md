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


The fixed sink PDOs 5 V / 2 A and 9 V / 1.5 A follow the owner stock FDT
`qcom,default-sink-caps` values (5000 2000 9000 1500); operating sink power is
13.5 W. Existing PDO flags, source PDOs and role settings are retained. The
charger `power-supplies` reference names the upstream Type-C node so standard
power-supply registration deferral and `external_power_changed` notifications
can be used. No new voltage-override or PD-PHY register programming is included.
On one tablet (2026-11-16, H) a Lenovo PD charger negotiated fixed 9 V/1.5 A
and charged with the driver's input-current control; a 3 A Rp charger, unplug,
PC port and OTG behaved as expected. Regular dtc handle numbering is used; numeric
phandle changes are not functional wiring changes.


The 2026-11-16 offline power-ramp candidate raises only the fixed 9 V sink PDO
to 3 A and operating sink power to 27 W, using the supplied observation that
the Lenovo source offers 9 V/3 A. This is an upper contract declaration, not a
operating point by itself: dby-chg bounds current by its selected ceiling
(default 2.5 A) and software thermal cap. On one tablet (2026-11-16, H) the
Lenovo source negotiated fixed 9 V/3 A and the driver ran 1.5–3 A input limits
without hard resets; `chg_temp` read 41–68 C across that range. The 5 V/2 A
PDO, source PDO and roles are unchanged. The additional charger IIO consumer
channel names the upstream PM8150B `ADC5_CHG_TEMP` provider, whose processed
temperature is in millicelsius. No new ADC channel definition, thermal-source
register programming or higher-power hardware validation is claimed.


The 2026-11-16 USB SuperSpeed candidate retains the owner stock FDT's
QMP PHY supplies: L18A (0.912 V) and the existing L9A `wifi_l9a` (1.2 V).
The PHY requests L18A without an always-on or boot-on constraint.

The earlier RB5/NB7VPQ904M graph and its descriptive fixed 1.8 V VCC provider
have been withdrawn. The supplied board observation reports no ACK at I2C15
address 0x1c (`ENXIO`), while 0x43 responds on the same bus. This suggests the
stock redriver entry may be an unpopulated reference-design component; its
physical absence and direct SS wiring are inferences, not established facts.
The NB7VPQ904M driver and its default tuning are no longer used, and I2C15
returns to its upstream disabled state without board children.

The connector SS endpoint now connects directly to `usb_1_qmpphy_out`, using
the graph pattern in upstream Linux 7.2.10 `sm8350-hdk.dts` and
`sm8450-hdk.dts`. The QMP PHY retains its orientation switch and handles cable
orientation. No data-lanes override is added. DP/SBU/FSA4480 and the secondary
`usb_2` controller are unchanged.

Device results (2026-11-16, bundle 20261116-8): no deferred devices; the Type-C
port registers and only the QMP PHY orientation switch/mux appear; NCM gadget,
PD 9 V and 5 V charging, and a USB 2.0 hub work in both plug orientations.
Actual SuperSpeed (5 Gbps) link operation has not been tested yet because no
USB 3 cable or adapter was available.
