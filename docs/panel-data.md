# 面板命令表自行提取 / Owner-extracted panel data

本仓库仅提供驱动逻辑、补丁和提取工具，不分发原厂面板命令表。生成的 `dby-w09-panel-data.h` 是私有构建输入，不适用提取工具的 GPL 声明，也不要上传到 GitHub。提取不代表取得再分发许可。使用者应确认输入来源、读取权限并自行决定是否执行；本教程不保证运行成功。

## 输入是什么

需要所有者自己的 DBY-W09 原厂**运行时 DTB**，即原厂系统的 `/sys/firmware/fdt` 对应的完整 FDT。它不是我们 Linux 的 DTB、不是 `.dts` 文本，也不是整个 recovery 镜像。适用历史基线为 HarmonyOS 4.2.0.213；其他版本未验证。

工具从固定面板节点读取两个属性，校验各自 SHA-256、包数、类型、长度和标志。只接受已有驱动所配套的 104 条开屏、5 条关屏命令。补丁 0003 依赖固定命令位置，不能删掉摘要检查来兼容其他面板。未找到属性或摘要不同就停止，没有自动适配方法。

## 取得自己的输入

优先使用自己已经保存的、可追溯的原厂运行时 DTB。若选择设备读取，应已具备 ADB 和相应读取权限。下面只是所有者手动执行的读取示例，本轮未在设备上执行。它不解锁、不提权、不刷机、不更改权限。

在主机创建全新的私有目录（已有目录则先停止，另选工作区），可读时使用：

```sh
umask 077
mkdir /path/to/new-private-panel
adb pull /sys/firmware/fdt /path/to/new-private-panel/runtime.dtb
```

若普通 ADB 无读取权限，但所有者已有 root 读取权限，采用主仓库 `docs/firmware-preparation.md` 中的 base64 传输和双端 SHA-256 校验方法，将来源换成 `/sys/firmware/fdt`。不要用 `adb exec-out su -c cat` 直接传二进制；历史采集中会发生换行损坏。不要修改设备权限或把文件先写到设备其他目录。没有权限或没有匹配副本时，本教程无法继续。

运行时 DTB 可能含设备身份信息，原文件、日志和生成表均保存在私有目录。不能上传 DTB 供别人代提取。

## 生成并接入构建

主机需 Python 3 和 dtc 工具包提供的 `fdtget`。以下命令在内核补丁仓库根目录执行，所有路径替换为自己的绝对路径：

```sh
python3 -B tools/extract-panel-data.py \
  --dtb /path/to/new-private-panel/runtime.dtb \
  --output /path/to/new-private-panel/dby-w09-panel-data.h
```

输出父目录须已存在；工具拒绝覆盖文件，生成文件权限为 0600。它只读两个属性，不输出完整 DTB 或执行其中内容。本轮使用既有本地 DTB，提取结果与旧补丁数组逐字节一致；不是重新读取设备或实机运行验证。

按[构建指南](build.zh-CN.md)应用六个补丁后、运行 make 前，将头文件复制到独立内核源码树：

```sh
test ! -e "$KERNEL_SOURCE/drivers/gpu/drm/panel/dby-w09-panel-data.h"
cp /path/to/new-private-panel/dby-w09-panel-data.h \
  "$KERNEL_SOURCE/drivers/gpu/drm/panel/dby-w09-panel-data.h"
```

没有这个文件，面板驱动编译会因缺少头文件而失败。没有空表、默认数据或跳过初始化的回退。

## 设备树是另一项输入

从原厂 DTB 提取面板表，不会得到主线 Linux 可用的板级设备树。原厂 DTB 不能直接当作本项目 Linux DTB。公开候选不再提供反编译板级快照，现提供基于上游 include 整理的板级 DTS 和私有内存布局提取／编译配方，实机未验证，见[设备树说明](../dts/README.md)。触摸私有计划数据也不会由此工具生成。

## English summary

Provide your own stock runtime FDT from `/sys/firmware/fdt`, not a Linux board DTB, DTS text or recovery image. Use existing authorised read access or an already saved traceable copy; if necessary follow the hub firmware guide's base64 transport and source/destination SHA-256 checks. No device extraction was performed in this task.

Run the Python tool above with dtc's `fdtget` installed. It validates the two pinned properties and writes a new private header with mode 0600. Copy it into `drivers/gpu/drm/panel/` in the separately patched kernel source before building. Missing data fails compilation. Do not relax pins: the refresh-rate patch depends on packet order. The generator grants no licence to extracted data; keep input, logs and output private. The board DTS now has a separate memory-extraction/build guide; touch plan data remains unavailable.
