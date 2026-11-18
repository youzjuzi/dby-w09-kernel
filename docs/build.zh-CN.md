# 内核构建与项目衔接

[English](build.md) · [返回首页](../README.zh-CN.md)

本文给出主机构建配方与输入映射（O），不安装模块或写卡。匹配的内核／DTB／模块组合已于 2026-11-02 启动测试与完整卡（H），见中心仓库[状态](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)；独立构建的 guard=0 触摸模块通过短时设备／交互检查（H + R），本次三指手势、笔与长期表现仍为 U。全量内核构建记录与后续 DTB 单独重验分开。

先按[面板数据教程](panel-data.md)生成私有头文件；缺少它将无法编译面板驱动。

## 1. 准备输入与工具

- 本仓库的十五个补丁和 `config/dby-w09.config`。
- 自行取得上游 `linux-7.2.10.tar.xz`；预期 SHA-256 在下方命令及首页中。摘要一致说明输入与本项目基线一致，不代替来源核实。
- Linux 主机、主机 C 编译器及开发头文件、arm64 GCC/binutils（前缀 `aarch64-linux-gnu-`）。已有配置记录的 GCC 版本为 15.2；其他版本可能影响配置、警告和产物，本文不承诺逐字节复现。
- GNU make、patch、tar、xz、bash、coreutils（含 sha256sum、realpath）、bc、bison、flex、Python 3，以及 OpenSSL/libcrypto 和 libelf 开发文件。具体最低要求以该压缩包中的 `Documentation/process/changes.rst` 为准；如修改配置启用 BTF，还需匹配的 pahole。
- 仅在单独编译设备树时需要 dtc；设备包还需要 kmod、squashfs-tools 等，详见主仓库 `tools/dby-bundle/README.md`。
- 准备足够容纳源码与模块构建树的磁盘空间。完整构建占用远大于本补丁仓库；本文未测量峰值，不提供未经验证的最低容量。

工具安装和上游下载由使用者按自己的发行版准备。不要用宿主机的 `/lib/modules/$(uname -r)/build` 代替目标内核构建目录。

## 2. 校验、解包与构建

在一个新的 shell 中执行完整代码块。将四个绝对路径替换为自己的路径；路径避免空格，`KERNEL_WORK` 的父目录须存在，工作目录本身必须不存在，并应位于所有 Git 仓库之外。命令校验压缩包后才解包，源码和产物分开保存。失败时停止并保留现场，不继续打补丁或使用部分产物。

```sh
set -eu
# Replace these four absolute paths before running.
KERNEL_REPO=/path/to/dby-w09-kernel
KERNEL_ARCHIVE=/path/to/linux-7.2.10.tar.xz
KERNEL_WORK=/path/to/new-kernel-work
PANEL_DATA=/path/to/private/dby-w09-panel-data.h

KERNEL_REPO=$(realpath "$KERNEL_REPO")
KERNEL_ARCHIVE=$(realpath "$KERNEL_ARCHIVE")
case "$KERNEL_WORK" in /*) ;; *) exit 1 ;; esac
test ! -e "$KERNEL_WORK"
test ! -L "$KERNEL_WORK"
printf '%s  %s\n' \
  2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3 \
  "$KERNEL_ARCHIVE" | sha256sum -c -
mkdir "$KERNEL_WORK"
tar -xf "$KERNEL_ARCHIVE" -C "$KERNEL_WORK"
KERNEL_SOURCE="$KERNEL_WORK/linux-7.2.10"
KERNEL_BUILD="$KERNEL_WORK/build"
mkdir "$KERNEL_BUILD"
set -- "$KERNEL_REPO"/patches/*.patch
test "$#" -eq 15
for patch_file do
    patch --batch -d "$KERNEL_SOURCE" -p1 --fuzz=0 < "$patch_file"
done
test -f "$PANEL_DATA"
cp "$PANEL_DATA" "$KERNEL_SOURCE/drivers/gpu/drm/panel/dby-w09-panel-data.h"
cp "$KERNEL_REPO/config/dby-w09.config" "$KERNEL_BUILD/.config"
make -C "$KERNEL_SOURCE" O="$KERNEL_BUILD" \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
make -C "$KERNEL_SOURCE" O="$KERNEL_BUILD" \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image modules
```

补丁按文件名顺序、零容差应用。`olddefconfig` 可能随工具链调整配置；保留最终 `.config`，与仓库配置比较并理解差异。不要通过忽略补丁错误或随意关闭功能让构建继续。配方未指定并行任务数；可按主机内存情况自行添加 `-jN`。

`CONFIG_FW_DEVLINK_SYNC_STATE_TIMEOUT=y` 在 `deferred_probe_timeout`（最后一次驱动注册后 10 s）到期后对仍未完成的提供者强制执行 `sync_state()`，避免特意保持手动加载的消费者（如 Venus）长期锁住开机互联带宽与 `rpmhpd` 电压投票；配合板级 DTS 为 `sdhc_2` 补齐的互联与 OPP 带宽投票使用（O）。实机表现与功耗变化待验证（U）。

## 3. 构建产物在哪里

下列文件是在上一步成功后的预期输出，本次未生成：

| 文件 | 用途 |
|---|---|
| `$KERNEL_BUILD/arch/arm64/boot/Image` | 未压缩 arm64 内核，由 bundle 的 `kernel_build_dir` 定位 |
| `$KERNEL_BUILD/drivers/…/*.ko` 等 | 树内模块，保留整个构建树给 bundle 的 `kernel_build_dir` |
| `$KERNEL_BUILD/.config`、`Module.symvers` | 最终配置与符号信息，供模块构建和打包使用 |
| `$KERNEL_BUILD/modules.order`、`modules.builtin`、`modules.builtin.modinfo` | 模块安装与打包元数据 |
| `$KERNEL_BUILD/include/config/kernel.release` | 内核 release，当前设备包要求精确为 `7.2.10` |

不要只复制 Image 后删除源码/构建树；设备包会调用 `modules_install`，还需要全部已构建模块和源树。当前配置开启 `CONFIG_LOCALVERSION_AUTO`，因此采用干净压缩包且工作目录放在 Git 仓库外；仍需检查实际 release。版本或 vermagic 不符时查明配置、工具链和源码差异，不修改检查值伪装匹配。

这一步不生成本机 DTB、initramfs、设备包或 Ubuntu 根系统。[设备树指南](../dts/README.md)提供板级源码和独立编译配方，需所有者生成私有内存 include；在主仓库 bundle 配置中显式选择所得 DTB；固定摘要门禁属于已淘汰的旧构建器。

DTB 步骤可选用 `--bd-address-file` 提供所有者选择的蓝牙地址；格式、限制与证据范围见[蓝牙地址说明](../dts/README.md#bluetooth-address)。

## 4. 接入主仓库的树外驱动

`dby-w09-linux` 提供背光、电量计、充电、喇叭与触摸驱动。必须使用与 Image 相同的目标源码、构建树、配置和工具链，先完成上面的内核及模块构建。下面在主机创建独立驱动工作副本；四个目标目录也必须尚不存在，重复执行前先保留旧结果。

复制和编译喇叭模块前，先按[主仓库说明](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md)从所有者自己的文件生成私有配置表，并把 `TFA_TABLES_DIR` 设置为生成头所在的绝对目录；缺少输入时构建报错。这些表及含表的模块不分发。

```sh
# Keep KERNEL_SOURCE and KERNEL_BUILD from the kernel recipe above.
LINUX_REPO=/path/to/dby-w09-linux
cp -R "$LINUX_REPO/drivers/rt8555-backlight" "$KERNEL_WORK/rt8555-backlight"
cp -R "$LINUX_REPO/drivers/dby-fg-readonly" "$KERNEL_WORK/dby-fg-readonly"
cp -R "$LINUX_REPO/drivers/dby-chg" "$KERNEL_WORK/dby-chg"
cp -R "$LINUX_REPO/drivers/dby-tfa9874" "$KERNEL_WORK/dby-tfa9874"
: "${TFA_TABLES_DIR:?Generate private speaker tables first}"
for driver in rt8555-backlight dby-fg-readonly dby-chg dby-tfa9874; do
    make -C "$KERNEL_SOURCE" O="$KERNEL_BUILD" \
      M="$KERNEL_WORK/$driver" ARCH=arm64 \
      CROSS_COMPILE=aarch64-linux-gnu- TFA_TABLES_DIR="$TFA_TABLES_DIR" modules
done
```

四个 `.ko` 会生成在各自的驱动工作副本中。四个树外驱动还包括充电与喇叭；其设备树节点、依赖和使用范围见主仓库 `drivers/rt8555-backlight/README.md`、`drivers/dby-fg-readonly/README.md`、`drivers/dby-chg/README.md`、`drivers/dby-tfa9874/README.md`；编译成功不代表节点已正确接入。

触摸另需固定计划 JSON 和生成的 `thp-plan-table.h`；按主仓库[可选触摸接入](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md#31-启用触摸可选)准备输入，用同一对目标内核源码／构建树在独立模块目录内编译。提取固件本身不会生成计划数据。bundle 要求匹配的十参数模块与固件，固定关闭未验收的 guard；板级节点已存在，不需改 DTB 或内核。独立的短时 H + R 记录不证明长期稳定或与较早模块的实机等价。

## 5. 交给 bundle 工具的输入

以下路径以各自仓库根目录为基准，不要求相邻克隆布局。主仓库的 `tools/dby-bundle/README.md`、`tools/dby-install/README.md`、`docs/firmware-preparation.md` 和 `docs/source-scope.md` 分别说明打包、安装、私有输入和剩余缺项。从 `tools/dby-bundle/examples/bundle.example.json` 开始填写；所有相对路径均相对配置文件所在目录解析。

| bundle 配置字段 | 应提供的材料 |
|---|---|
| `kernel_source_dir` | 匹配的已打补丁 `$KERNEL_SOURCE` |
| `kernel_build_dir` | 完整 `$KERNEL_BUILD`，含 Image 和已构建模块 |
| `dtb` | 显式选择的板级 DTB |
| `external_modules` | 下表独立模块的目的路径到主机文件映射 |
| `private_inputs` | 所有者提供的锁定固件／配置目录数组 |
| `touch.enabled` | 可选；需匹配模块、固件与固定计划输入，构建见中心仓库[触摸接入](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md#31-启用触摸可选) |
| `output` | 尚不存在的输出目录，父目录须存在 |
| `sources` | 完整仓库提交及锁定的上游版本／摘要 |

树内模块由 bundle 工具的 `modules.list` 从内核构建目录选取，不再默认查找历史外部覆盖路径。独立模块在 `external_modules` 中填写以下映射，替换为实际构建文件：

| 设备镜像内目的路径 | 主机文件 |
|---|---|
| `kernel/drivers/video/backlight/rt8555-backlight.ko` | `$KERNEL_WORK/rt8555-backlight/rt8555-backlight.ko` |
| `kernel/drivers/power/supply/dby-fg-readonly.ko` | `$KERNEL_WORK/dby-fg-readonly/dby-fg-readonly.ko` |
| `kernel/drivers/power/supply/dby_chg.ko` | `$KERNEL_WORK/dby-chg/dby_chg.ko` |
| `kernel/sound/soc/codecs/dby-tfa9874.ko` | `$KERNEL_WORK/dby-tfa9874/dby-tfa9874.ko` |
| `kernel/drivers/input/touchscreen/nt36523-thp.ko` | 独立触摸构建目录里的 `nt36523-thp.ko`，仅开启时提供 |

构建器调用 `modules_install`，检查精确模块 vermagic，并校验所提供私有输入的清单、权限与摘要。关闭触摸时省略其模块和固件输入；显式提供的私有目录仍会被校验。所选 DTB 原样使用，不再与历史固定 DTB 摘要比较。

仅含 p1 的 bundle 是中间产物；安装器还需要所选的完整或最小 rootfs 归档。按主仓库工具说明构建根系统并先查看 dry-run 计划。打包或离线构建成功均不等于实机运行成功；内核仓库和 bundle 构建器均不负责组装 U-Boot 的 Recovery 镜像。

当前中心仓库模块列表除背光／电量计／触摸外还选择 `dby_chg.ko` 和 `dby-tfa9874.ko`，旧示例 JSON 只有三项树外映射，须补上表中的两项。编译成功不代表来源许可或硬件安全已核清。充电驱动写 PMIC 寄存器，喇叭没有保护算法，选包前先读中心仓库驱动说明。音频还需所有者提供锁定的 ADSP 固件；历史 radio／GPU／touch 配方不能复现当前完整音频系统。

## R4 主机复核补充（2026-11-15）

使用 0001–0012 十二个补丁及 README 的可复现环境变量。当前匹配的所有者面板、内存、触摸计划和 TFA 头文件可以复用，不代表本轮重做提取；内存 include 必须带 Venus 预留，蓝牙地址仍由所有者提供。更新后的示例 JSON 含五个树外模块映射，但占位路径和提交必须替换。

可选内核测试的文件名含连字符，unittest discover 不收集；用 shell 循环逐个执行 `python3 -I -B "$test_file"`。补丁测试还要求仓库旁 `../upstream/linux-7.2.10` 的原始文件，必须从已核对的压缩包新解压测试需要的文件，不能复用旧树或拿已经打补丁的源码充当原始输入。R4 的此目录只作测试 fixture。

R4 实测发现，单设 `SOURCE_DATE_EPOCH` 不会固定 Linux 7.2.10 的 UTS 时间或内置 initramfs mtime：`init/Makefile` 默认调用 date，`usr/Makefile` 接受的是 `KBUILD_BUILD_TIMESTAMP`。本轮照 README 使用实际构建时间；未来若专门做字节复现，还须显式指定 `KBUILD_BUILD_TIMESTAMP` 和 `KBUILD_BUILD_VERSION`，不能倒称本轮已如此执行。新旧 Image 均为 42,011,136 字节，只有 70 字节不同，均已定位到两个版本/时间字段、内核与 vDSO build-id、空 initramfs 的三个 mtime；其他字节完全相同（O）。
