# 板级设备树 / Board device tree

语言：简体中文与 English summary。当前基线 2026-11-02 的 DTB 已有启动 H 记录，见[中心状态页](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)；下文最初源码整理的比对为 O，不能推广到其他输入。Current boot evidence is separate from the original offline audit below.

本目录提供整理后的 `sm8250-huawei-dby-w09.dts`：基于 Linux 7.2.10 的标准 SM8250/PM8150 include，合并本项目历史板级修改及 USB 片段。它不再引用项目内部实验目录，也不是发布整棵反编译树。源码仍按历史功能层组织，尚未整理成可提交上游的最小板级文件。来源及离线比对见[provenance.md](provenance.md)。

**私有输入仍必需：** `dby-memory-private.dtsi` 由所有者从自己的原厂运行时 FDT 生成，不随仓库提供。板级源码不包含蓝牙地址。面板驱动的私有命令表是另一项输入，见[面板教程](../docs/panel-data.md)。

## 1. 准备自己的内存布局

主机需要 Python 3、dtc 工具包的 `fdtget`、`dtc`，以及 `aarch64-linux-gnu-gcc`。在内核补丁仓库根目录执行。原厂运行时 DTB 的取得、只读权限和 base64 传输方法见[面板教程](../docs/panel-data.md)；不需要公开自己的 DTB。

创建全新的私有工作目录，父目录应已存在。命令中的绝对路径均需替换：

```sh
umask 077
mkdir /path/to/new-private-dt
python3 -B tools/extract-memory-layout.py \
  --dtb /path/to/own-runtime.dtb \
  --output /path/to/new-private-dt/dby-memory-private.dtsi
```

工具仅读取 RAM 和具有 reg 的 reserved-memory 子节点。以这些内容的固定指纹限制到本次核对过的布局；不同内存容量、固件版本或保留区布局可能被拒绝。不能删除指纹检查或复制别人的 include 来继续。它不提取 bootargs、序列号或 MAC 地址。

输出包括 RAM、保留区和简单帧缓冲描述，保留原有 no-map，且按历史启动策略给连续 splash 区补 no-map；给 cmd-db、SMEM、GPU ZAP 和视频保留区建立标签。1600×2560、stride 6400、a8r8g8b8 的帧缓冲假定沿用此板基线，不是自动识别所有屏幕。工具不修改设备，也不授予所提取数据的再分发权利。

## 2. 编译独立 DTB

准备经[构建指南](../docs/build.zh-CN.md)校验过的 Linux 7.2.10 源码树。DT 编译不需要先构建完整内核；所用上游 include 由 `upstream-sha256.json` 校验。

```sh
python3 -B tools/build-board-dtb.py \
  --kernel /path/to/linux-7.2.10 \
  --memory /path/to/new-private-dt/dby-memory-private.dtsi \
  --output /path/to/new-private-dt/build
```

输出目录必须不存在。产物为 `build/dby-w09.dtb`，另有预处理源码、私有 include 副本、日志与 build-info.json。整个输出目录保持私有，不上传生成的 DTS、DTB、include 或日志。编译失败保留目录查看错误，重试另选目录。不要使用 dtc 的强制输出开关绕过错误。

## 3. 已做的离线检查

使用维护者既有本地 runtime DTB 生成私有输入，31 个上游 include 与原始压缩包一致。公开构建脚本两次生成的 DTB 字节相同，共 974 个节点。

为排除 phandle 自动编号差异，仅在私有比对副本中固定参考编号，再与历史 USB 整合参考 DTB 逐节点逐属性核对，只有两项预期差异：型号文字去掉旧实验编号、删除蓝牙地址属性。memreserve 表一致。公开源码不携带历史固定 phandle 表。

dtc 成功但报告 36 条警告，原始日志保存在私有实验记录；未做 dt-schema 验证，不能写成零警告或上游绑定验收通过。该次最初源码整理未完整编译内核或实机验证；后续干净重建与设备检查另见上述当前基线记录。

## 4. 接入限制

生成的 DTB 与旧设备包固定摘要不同；原先的摘要拒绝记录属于已淘汰构建器的历史限制。当前主仓库的 `tools/dby-bundle/README.md` 说明如何在 bundle 配置中显式选择 DTB。这里的编译和比对仅提供离线证据，不代表任意 DTB、模块及私有输入组合已通过实机验证。蓝牙地址的所有者配置仍需自行处理，不能填入别人的地址。

<a id="bluetooth-address"></a>
## 蓝牙地址（可选私有输入） / Bluetooth address (optional private input)

在一台平板上观察到：缺少地址时控制器被标为未配置，BlueZ 看不到它。可在构建时提供 `--bd-address-file`，把所有者选择的地址写入输出目录中的板级副本；板级源码仍不含地址。此路径的编译和字节检查为离线证据（O），带地址的 DTB 在一台平板上已启动：控制器 UP、BlueZ／GNOME 可见（**H + R**，2026-11-03，设备包 20261102-4）；一只蓝牙鼠标配对并可用（**R**，2026-11-03）；回连与 A2DP 仍为 **U**。

文件须为非符号链接的普通文件，最多 64 字节，UTF-8/ASCII，内容严格为一行 `AA:BB:CC:DD:EE:FF`，仅允许末尾有一个 LF 换行，不接受空格、CRLF 或额外行。地址须为本地管理单播地址（首字节低两位为二进制 `10`），拒绝全零和控制器默认占位值。每台设备应选择不同地址，不要复制别人的地址，也不要使用带厂商前缀的公有地址。下面是虚构格式示例，使用前替换为自己选择的唯一地址；这项格式检查不能保证无线环境中没有冲突。

```sh
umask 077
# Fictional format example only: replace with your own unique address.
printf '%s\n' '02:00:00:00:00:01' > /path/to/private/bd-address
python3 -B tools/build-board-dtb.py \
  --kernel /path/to/linux-7.2.10 \
  --memory /path/to/private/dby-memory-private.dtsi \
  --bd-address-file /path/to/private/bd-address \
  --output /path/to/new-private-dt-with-bt
```

地址按小端字节序写入 `uart6/bluetooth/local-bd-address`，DTB 哈希因此与不带参数时不同。不提供参数时板级副本与 DTB 保持原样。`build-info.json` 只记录 `bd_address` 为 `supplied` 或 `none`，终端不打印地址；生成的 DTS、DTB 和整个构建输出目录均须保持私有。

On one tablet, omitting the address left the controller unconfigured and invisible to BlueZ. The optional `--bd-address-file` writes an owner-selected address into the output board copy; the public board source still contains no address. Compilation and byte checks are offline evidence (O); a DTB with an address booted on one tablet with the controller UP and visible to BlueZ/GNOME (**H + R**, 2026-11-03, bundle 20261102-4); one Bluetooth mouse paired and worked (**R**, 2026-11-03); reconnection and A2DP remain **U**.

Supply a regular, non-symlink file of at most 64 bytes, containing exactly `AA:BB:CC:DD:EE:FF` in UTF-8/ASCII, optionally followed by one LF. Spaces, CRLF and extra lines are rejected. Use a locally administered unicast address (the first byte's low two bits must be binary `10`); zero and controller placeholder addresses are rejected. Choose a distinct address for each device, do not copy another owner's address or use a vendor-assigned public prefix. Replace the fictional example above with your own unique choice; format validation cannot guarantee freedom from collisions.

The bytes are written little-endian to `uart6/bluetooth/local-bd-address`, changing the DTB digest. Omitting the option preserves the board copy and DTB bytes. Metadata records only `bd_address: supplied` or `none`, and terminal messages do not print the address. Keep generated DTS/DTB files and the entire output directory private.

## 霍尔传感器与合盖开关 / Hall sensors and lid switch

板级 DTS 为原厂的三个霍尔传感器建立了节点：GPIO113、GPIO121、GPIO23（上拉输入），供电为 PM8150L 的 `ldo8`（1.8 V，当前设为常开，策略仍是临时的）。GPIO113 作为独立的 `hall-lid` 节点上报 `SW_LID`（低有效，去抖 200 ms，**无 wakeup-source**，因为休眠从未验证）。GPIO121 与 GPIO23 只是观察用开关（`SW_KEYPAD_SLIDE`、`SW_DOCK`），不触发任何动作。GPIO23 同时被笔和完全合上的皮套触发，所以不用于合盖。

映射来自一台平板、一种三段磁性皮套和一支笔的实机观察（H + R，2026-11-08；皮套最靠近屏幕的一段贴下时 GPIO113 即有效，约半开）；键盘未测，其他配件需自行验证。`hall-lid` 与 `hall-probe` 共用同一个引脚配置状态，这在内核源码层面可行（GPIO 复用允许共享），并在上述平板上绑定成功（H）。休眠（s2idle）与合盖唤醒没有验证。

Three Hall sensors (GPIO113, GPIO121, GPIO23, pulled up) are powered from PM8150L `ldo8` at 1.8 V, currently always on as a temporary policy. GPIO113 is a separate `hall-lid` node reporting `SW_LID` (active-low, 200 ms debounce, **no wakeup-source** because suspend was never validated). GPIO121 and GPIO23 are observation-only switches (`SW_KEYPAD_SLIDE`, `SW_DOCK`) and trigger nothing. GPIO23 reacts to both the pen and a fully closed cover, so it is not used for lid detection.

The mapping comes from observations on one tablet with one magnetic tri-fold cover and one pen (H + R, 2026-11-08; GPIO113 becomes active once the segment nearest the screen is down, about half open). The keyboard is untested; verify other accessories yourself. `hall-lid` and `hall-probe` share one pin-control state, which the kernel source permits for GPIO-function pins and which bound successfully on that tablet (H). Suspend and lid wake are not validated.

## 内存映射广播定时器 / MMIO broadcast timer

`/soc@0/timer@17c20000`(`arm,armv7-timer-mem`,19.2 MHz)设为 `okay`。内核已编入 `arm_arch_timer_mmio` 驱动，无需改配置。一台平板上的实测（H，2026-11-08）：广播时钟事件设备由软件的 `bc_hrtimer` 变为 `arch_mem_timer`；关屏待机时簇级 cpuidle 状态由 0 次变为约 60–67% 的时间；关屏功率约降 0.05 W（落在原有波动范围内，结论为小幅）；亮屏几乎无收益。短按/合盖/长按/音频/时钟同步回归正常，约 15 分钟内未见 RCU stall 或 lockup。过夜等长时稳定性未验证（U）。

The memory-mapped timer `/soc@0/timer@17c20000` (`arm,armv7-timer-mem`, 19.2 MHz) is enabled; the driver is already built, so no config change is needed. Measured on one tablet (H, 2026-11-08): the broadcast clockevent changed from the software `bc_hrtimer` to `arch_mem_timer`; with the screen off, the cluster cpuidle state went from zero uses to about 60–67% of the time; screen-off power dropped by only about 0.05 W (within the earlier run-to-run spread); screen-on showed almost no benefit. Key, lid, audio and time-sync checks were normal and no RCU stall or lockup appeared within about 15 minutes. Long-run (overnight) stability is unverified (U).

## 视频编解码（SM8250 由 Venus 驱动，IRIS 关闭）

启用 `videocc` 与 `video-codec`，视频保留区由私有内存提取器标记为 `dby_video_mem`。为避免 dtc 插入新引用后重排已有 phandle，新保留区使用未占用的 `0x1014`，沿用已有显式编号的做法；其他节点编号保持不变。

固件是所有者从原厂 `modem.img` 提取的私有输入，不随仓库分发，来源与再分发许可门禁未关闭。固定在 Linux 7.2.10，使用 Venus 驱动：配置关闭 `VIDEO_QCOM_IRIS`、保留 `VIDEO_QCOM_VENUS=m`，因为上游 `!IS_ENABLED(CONFIG_VIDEO_QCOM_IRIS)` 条件下 Venus 才包含 SM8250 资源表和 `qcom,sm8250-venus` 匹配项。没有 `video-firmware` 子节点时走 TZ 路径（`qcom_mdt_load`、`qcom_scm_pas_auth_and_reset`、`qcom_scm_mem_protect_video_var`）。DTS、OPP、时钟及互联参数不变，不启用 no-TZ 的 `video-firmware` 子节点。

设备包只打包 Venus 三个模块，用 `blacklist venus_core` 阻止自动探测，**需要时手动 `modprobe venus_core`**。

**实机结果（H，一台平板，设备包 `20261102-28`，2026-11-10）**：`modprobe venus_core` 一次成功，固件被 TZ 接受；出现 `/dev/video0`（编码器）与 `/dev/video1`（解码器）。HEVC 与 VP9（profile 0）硬解正常；H.264 连续解码正常，但流结束或 seek 时固件会报系统错误，驱动约 3 s 后自行恢复，并丢失最后约 17 帧。1080p30 VP9 解码到空输出的对比中，硬解比软解低约 0.13 W（3 对交替测量，不含渲染与合成）。官方 Chrome 没有 V4L2 解码器，浏览器里用不上。未验证（U）：长时间播放、与桌面播放器的整合、休眠前后的行为。

## English summary

This standalone board source consolidates project DTS layers over pinned Linux 7.2.10 includes; it does not depend on internal experiment directories or distribute the decompiled snapshot. It is still a development source, not an upstream-ready board submission.

Generate the private memory include from your own stock runtime FDT using the first command, then build with the second. The extractor accepts only the audited RAM/reservation fingerprint; do not bypass it for a different layout. Outputs stay private. Panel command extraction is separate, and no Bluetooth address is shipped.

Two offline builds matched byte-for-byte. With reference phandles assigned only in a private comparison build, all 974 nodes matched the historical USB-integration reference except model text and omitted Bluetooth identity. The reservation table matched. There were 36 dtc warnings; dt-schema and device operation were not tested in that original source audit; later baseline boot evidence is linked above. The old device-pack digest rejection is a historical result; the current hub bundle configuration selects its DTB explicitly. Consult the hub's `tools/dby-bundle/README.md` for packaging requirements.

## 面板供电 / Panel supplies

板级 DTS 默认描述 VCI、IOVCC、VSP、VSN 四路供电，配合补丁 0011 使用；构建时不需要额外供电开关。VCI 使用 RPMh LDO11、HPM 初始模式，不设置 boot-on。IOVCC/VSP/VSN 使用三个 GPIO 控制的 fixed regulator，并设置 boot-on，使 probe 时按高电平申请 GPIO，避免在显示驱动接管前主动拉低。固定电压值只是描述，不表示 GPIO 能设定或测量电压。L14A/L5A 的既有 always-on 策略不变。

boot-on 不等于 always-on：Linux 7.2.10 不为只有 boot-on 的 regulator 增加永久 use_count。面板首次 prepare 仍先 enable 各路，再 disable 到零，真实关闭 GPIO 开关、保持 100 ms 后重新上电；随后每次按完整供电顺序开关。此结论来自源码分析（O）；开机画面保留与实际时序效果仍待设备验证。

The board DTS describes all four panel supplies by default, with patch 0011. VCI uses RPMh LDO11 in HPM without boot-on. The three GPIO-controlled fixed regulators use boot-on to request high GPIO levels at probe. They are not always-on: the first panel prepare still acquires and releases their enable references, switches them off, waits 100 ms and powers them on again. This is an offline source analysis, not hardware validation. Voltage properties describe the rails; GPIOs do not program or measure their voltage.
