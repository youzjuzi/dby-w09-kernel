# dby-w09-kernel

R4（2026-11-15）：维护者从空白 **16 GB 新卡**照公开文档全新安装通过，包 **`20261115-1`**（**H + R**：用户提供的 Claude SSH 核对与用户交互观察）。见[新卡结果与操作清单](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/fresh-install.md)。第三方独立复现仍为 **U**；已有私有输入复用，提取未重做、保持原证据级别。现有 Recovery/U-Boot 未重编、未重刷；原工作卡保留作回退。

当前源码含二十一个补丁与板级集成，证据只覆盖一台平板；音频、充电、电源键／合盖、Venus 及缺陷见[中心状态页](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)。需要已解锁 Bootloader 并替换 Recovery，错误镜像可能导致无法启动。**安装流程未经第三方从空白卡独立验证，欢迎反馈。**

在华为 MatePad 11（DBY-W09，骁龙 865／SM8250）上运行 Linux 7.2.10 的二十一个补丁、配置与板级源码。完整上游源码和所有者数据另行准备。

[English](README.md) · [项目中心](https://github.com/youzjuzi/dby-w09-linux) · [U-Boot](https://github.com/youzjuzi/dby-w09-uboot) · [安装与上机检查](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md)

## 范围与证据

**O 离线，历史六补丁基线**：六补丁 fuzz=0 应用，锁定来源构建了 Image／模块及独立 DTB。注释整理后 DTB 哈希仍一致，有 36 条 dtc 警告，未通过 dt-schema 验收。**H 实机记录**：2026-11-02，一台已解锁、HarmonyOS 4.2.0.213 的 DBY-W09 用重建后的内核／DTB／模块启动了最小和完整桌面卡。显示、网络与 **R 用户桌面观察**详见中心仓库[状态页](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)。

新基线触摸已于 2026-11-02 在 guard=0 下通过短时设备／交互检查（**H + R**），见中心仓库[状态页](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)。本次三指手势、笔、触摸启动／长期可靠性、休眠与长时间稳定性及其他设备／固件仍为 **U 未验证**。旧工程历史不能替代这些项目的本次验收；2026-11-18 补丁 `0017` 与 `0018` 已在一台平板上解决唤醒黑屏与快速连按条纹根因（**H + R**：46 次开机后唤醒／切率含 38 次 `13–68 ms` 极限连按 0/46 ESD 复位；多日长期可靠性与 2026-11-16 单次亮屏静止报警复位后需触摸才出图仍为 **U**，见[补丁说明](docs/patch-notes.md)）。补丁是设备专用开发修改，未按通用上游方案准备。

蓝牙（2026-11-03，一台平板）：DTB 带所有者提供的控制器身份配置时，控制器 UP、BlueZ／GNOME 可见（**H + R**）；一只蓝牙鼠标配对并可用（**R**）。重启／休眠后回连、其他设备类型、A2DP 仍为 **U**。证据见上方中心仓库状态页。

[中心仓库](https://github.com/youzjuzi/dby-w09-linux)提供树外背光／电量计／触摸源码、bundle／rootfs 构建器与 SD 安装器；[U-Boot 仓库](https://github.com/youzjuzi/dby-w09-uboot)构建 Recovery 引导器。本仓库不执行系统安装或刷写。

## 准备所有者输入

按[面板教程](docs/panel-data.md)生成私有头文件，按[板级指南](dts/README.md)生成内存 include。输入必须是自己的、受支持的原厂运行时 FDT；不分发面板命令数组、内存 include、身份或固件。摘要检查固定已审查输入／布局，不得为其他版本绕过。触摸另需私有计划输入，本内核配方不构建触摸模块。

## 复现锁定内核与 DTB

自行取得 [linux-7.2.10.tar.xz](https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.10.tar.xz)。需要 arm64 GCC/binutils（记录 GCC 15.2.0）、内核原生构建依赖、make／patch／tar／xz、coreutils、Python 3、dtc（记录 1.7.2）。依赖细目、产物与外部模块见[完整构建接入指南](docs/build.zh-CN.md)。

从本仓库在新 shell 执行，替换四个输入／工作目录以及内存 include 占位符。工作目录必须是 Git 外的新目录，父目录已存在，只在主机构建：

```sh
set -eu
KERNEL_REPO=$(pwd)
KERNEL_ARCHIVE=/path/to/linux-7.2.10.tar.xz
KERNEL_WORK=/path/to/new-kernel-work
KERNEL_PANEL=/path/to/own-panel-header.h
test ! -e "$KERNEL_WORK"
printf '%s  %s\n' \
  2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3 \
  "$KERNEL_ARCHIVE" | sha256sum -c -
mkdir "$KERNEL_WORK"
tar -xf "$KERNEL_ARCHIVE" -C "$KERNEL_WORK"
KERNEL_SOURCE="$KERNEL_WORK/linux-7.2.10"
KERNEL_BUILD="$KERNEL_WORK/build"
mkdir "$KERNEL_BUILD"
set -- "$KERNEL_REPO"/patches/*.patch
test "$#" -eq 21
for patch_file do
  patch --batch -d "$KERNEL_SOURCE" -p1 --fuzz=0 < "$patch_file"
done
cp "$KERNEL_PANEL" "$KERNEL_SOURCE/drivers/gpu/drm/panel/dby-w09-panel-data.h"
cp "$KERNEL_REPO/config/dby-w09.config" "$KERNEL_BUILD/.config"
export SOURCE_DATE_EPOCH=1791417600 KBUILD_BUILD_USER=builder KBUILD_BUILD_HOST=offline
make -C "$KERNEL_SOURCE" O="$KERNEL_BUILD" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
make -C "$KERNEL_SOURCE" O="$KERNEL_BUILD" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j8 Image modules
python3 -I -B tools/build-board-dtb.py --kernel "$KERNEL_SOURCE" \
  --memory /path/to/own-memory-include.dtsi --output "$KERNEL_WORK/dtb"
```

归档锁定 SHA-256 为 `2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3`。保留 olddefconfig 最终结果：`PCI_PWRCTRL_PWRSEQ` 从 y 变为 m，中心仓库的 bundle 模块列表已包含它。保留完整源码／构建树供 `modules_install`，另提供匹配的树外驱动。不要用宿主机内核树或强改旧配置来掩盖差异。

## 记录产物（O）

下表为历史六补丁基线摘要，不是当前二十一补丁配置、音频、霍尔／定时器或 Venus 板级增量的预期摘要。

| 产物 | SHA-256 |
|---|---|
| 未压缩 `Image` | `0f1d0a0802c651cd2cbe049c78e3c8d21b14d95b95fca588bb8bae5f89f509a7` |
| `dby-w09.dtb` | `f2cf2c8fb6c8a170ad753062823760dd100e3fc915d6b60b4b428795f1a50cfd` |

注释清理后 DTB 重建逐字节一致。Image 还依赖工具链、最终配置、时间与私有面板数据，这里的摘要来自记录中的全量构建，与后续 DTB 单独重验分开。摘要是记录基线，不是任意所有者输入的兼容门禁。板级源码初次比对及 phandle／型号／身份差异见[来源说明](dts/provenance.md)；干净重建没有重复规范化逐节点比对。

## 交给中心仓库

源码／构建目录、DTB 与外部模块映射见[构建接入指南](docs/build.zh-CN.md#5-交给-bundle-工具的输入)。中心仓库[安装指南](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md)覆盖 bundle 配置、test／full rootfs、整张 SD 卡安装、种子、Recovery、首次启动与检查，不依赖内部开发仓库。

- [补丁说明](docs/patch-notes.md)：修改与限制。
- [来源核查](docs/provenance-review.md)：上游／撤回引用和数据边界。
- [板级源码与构建](dts/README.md)。
- [第三方材料](THIRD_PARTY.md)、[贡献](CONTRIBUTING.md)、[安全政策](SECURITY.md)。

本项目是独立、非官方的设备移植工作，与 Huawei／HarmonyOS／MatePad、Canonical/Ubuntu、Qualcomm 或 TeamWin 无关联，未获其认可或赞助；相关名称和商标属于各自权利人。本项目不提供厂商固件，也不保证适用于其他设备或固件。

运行集成系统需要已经解锁的 Bootloader。刷写会替换 Recovery，修改后的镜像不匹配原 AVB 摘要；错误镜像或操作可能导致设备无法启动或 Recovery 无法使用。写卡会清除所选 SD 卡的数据。先保留并核对自己的原厂回退镜像；恢复出厂前恢复原厂 Recovery。软件按现状提供，无担保。本库仅提供源码，集成前置条件与风险见中心仓库[安装指南](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md)。

源码沿用各文件许可，见[逐补丁许可表](THIRD_PARTY.md)、[LICENSE](LICENSE)、`dts/NOTICE` 和 `LICENSES/`；工具不授予所有者数据的许可。

## 实验性板载录音

显式启用的板载录音拓扑（**H + R**，一台平板，2026-11-06）：配合中心仓库对应设备包（`20261102-12`／`20261102-13`）与补丁 `0008`，开机默认不启动 ADSP；手动两阶段启动后 ADSP／APR 上线、声卡 `sm8250 - DBY-W09` 注册，在全部四路模拟麦克风通道同时录到真信号（RMS −31.79／−47.82／−29.97／−32.63 dBFS），并通过只读 ALSA UCM2 在 PipeWire／GNOME 桌面自动呈现 4 声道 `Internal Microphone`、与 USB-C 数字耳机切换共存，重启后恢复默认停止状态。上述为历史录音阶段；后续四喇叭 S16LE 桌面短测通过（**H + R**，一台平板，2026-11-07，包 `20261102-16`），没有喇叭保护算法。物理麦克风映射、长期高音量使用仍为 **U**。详见[音频说明](docs/audio-capture.md)。

`SOURCE_DATE_EPOCH` 单独不能固定本内核的 UTS/initramfs 时间；R4 记录的是实际构建时间。专门做字节复现所需的其他变量见[构建补充](docs/build.zh-CN.md)。
