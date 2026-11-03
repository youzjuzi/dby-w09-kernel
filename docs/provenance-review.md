# 来源核查 / Provenance review

## 已核实 / 未核实范围（2026-11-03 整理）

已核实范围：历史本地归档与两个下游参考文件的字节对应和许可声明、面板表与历史运行时 DTB 的对应、下述上游 PLL 计数提交及撤回的来源补核记录；本轮另核对 Linux 7.2.10 各补丁目标文件的 SPDX，见[逐补丁许可表](../THIRD_PARTY.md)。本轮未重新进行历史输入比对或联网来源验证。

未核实范围：下游发布编号与原下载页面未独立重新核实；提取面板数据的再分发许可、历史 DTS 输入的完整归属与对应关系仍未闭合。当前不分发命令数组和反编译快照，不代表这些缺口已被解决。来源审查门禁仍未关闭，不能把文字整理视为发布前完整审查已完成。

日期：2026-10-29。范围：面板表、当前设备树快照、补丁 0004/0005 的下游参考源码。证据来自本地文件和历史生成脚本，不是完整法律审查，也不包含联网重新核实下载来源、编译或设备操作。

## 2026-10-29 follow-up: patch 0005 source resolved / 计数修改来源补核

本节更新下方历史审查中的“PLL 计数修改来源未核验”结论，其余历史记录保留。

计数部分对应 Neil Armstrong 的 Linux 上游提交
[93c97bc8d85d](https://github.com/torvalds/linux/commit/93c97bc8d85d)
（drm/msm: dsi: fix PLL init in bonded mode），修复对象为
[cb55f39bf7b1](https://github.com/torvalds/linux/commit/cb55f39bf7b1)。
本次直接查阅上游提交差异，将发布补丁与双路 DSI 时钟调整及主从分频同步的历史生成记录逐项核对：

| 当前 0005 中的计数修改 | 上游对应 |
|---|---|
| bias enable 不再因计数非零提前返回；保留递增和溢出警告 | 93c97bc8d85d 的同一函数修改 |
| PHY enable 删除强制计数赋 1 | 同一提交的 PHY enable 修改 |
| PHY disable 删除强制计数赋 0 | 同一提交的 PHY disable 修改 |

这是针对本地树的部分适配，不是完整 cherry-pick：本地保留 `pll_data`、相关局部变量和寄存器写入周围的锁；上游原提交还删除了这些内容。主从分频同步是另一部分本地修改，仍按下方厂商 GPL 参考文件单独归因。不能将整个 0005 称为原创，也不能将计数修改归给厂商分频实现。

上游随后通过
[44784327815b](https://github.com/torvalds/linux/commit/44784327815b)
撤回该提交，原因是非 bonded 模式下分频设置回归。因此 0005 是保留供 DBY-W09 双路 C-PHY 使用的本地适配，不是通用上游修复，未证明适用于其他设备或单路模式。此次仅补充出处、署名和限制，没有改变补丁代码，没有新增构建或设备验证。

The PLL-count changes are adapted from Neil Armstrong's upstream commit
93c97bc8d85d, with local locking and `pll_data` retained. They are distinct
from the downstream-inspired divider synchronization. Upstream reverted the
original change in 44784327815b after a non-bonded divider regression. This
repository retains a DBY-W09-specific adaptation, not a generally accepted
upstream fix. Source identification is now resolved for this part; this is
not a blanket legal clearance for every repository input.

## 板级源码后续整理

后续板级源码整理从历史源码层重建独立 DTS，附私有内存提取工具；不是恢复原反编译快照。来源与离线比对见[板级说明](../dts/provenance.md)。以下对旧快照的核查作为历史依据保留。

## 当前发布范围更新

用户决定公开自写逻辑和提取工具。命令数组已移出补丁，反编译设备树已移出发布候选；原件保留本地。以下核查结论描述调整前的材料，不代表当前仍分发它们。面板表由[使用者提取](panel-data.md)，数据本身未因提取工具开源而获得许可。

## 结果

| 材料 | 本次确认 | 尚未确认 |
|---|---|---|
| 补丁 0002 的命令表 | 104 条开屏、5 条关屏命令，与历史运行时 DTB 的对应属性逐条一致；历史生成脚本确实读取该 DTB | 此组设备数据的明确再分发许可依据 |
| 设备树快照 | 找到 11 层板级 DTS 引用链，及后续触摸、USB 修改记录 | 所有输入的完整来源/声明覆盖，以及当前快照与该链条的完整对应 |
| 补丁 0004/0005 的下游显示参考 | 两份参考 C 文件与本地厂商压缩包成员逐字节一致；均有 GPL-2.0-only 文件头和 Linux Foundation 版权声明 | 原下载页面/发布编号尚未重新核实；0005 的 PLL 计数修改不由这两份参考文件单独证明来源 |

## 面板表：更正直接来源

历史双路 C-PHY 面板生成脚本读取所有者设备的运行时 DTB，从面板 timing 节点取 on/off command 属性，转换为 C 数组。本次解析原始 DTB 后，与发布补丁逐条核对类型、延时、长度和数据：104/104 条开屏命令、5/5 条关屏命令一致。

早期 XBL 面板分析查看的是其中另一份面板 XML，用于比较初始化差异；不能把这份 XML 当作补丁表的直接来源。厂商源码包中的 `lcdkit3.0/config/qcom/kona/debussy/290-20d-10p9-qcom.xml` 和 `Dual-nt36523-video-mode_default.xml` 已核对成员字节，但所查看文件没有单独 SPDX/许可声明，未据此建立本补丁完整 on/off 表的来源和许可对应。源码包中的 kernel/COPYING 不能单独证明从运行时 DTB 提取的每项数据都对应同一授权输入。

因此，“来自原厂配置”是来源描述，不作为许可已经核清的结论。

## 下游参考文件

本地归档名：`DBY-W09_opensource.tar.gz.gz`。归档 SHA-256：

`3364a5b41a4f5d4f6281babceddf39606598e1137f2981217f1e585c005a96a9`

以下均为归档中的路径：

| 参考文件 | 声明与对应用途 |
|---|---|
| `Code_Opensource/kernel/techpack/display/msm/dsi/dsi_ctrl_hw_cmn.c` | GPL-2.0-only；Copyright (c) 2015–2020, The Linux Foundation. All rights reserved.；两处设置 HS TX timeout 为 0x3FD08，对应 0004 的参考说明 |
| `Code_Opensource/kernel/techpack/display/pll/dsi_pll_7nm.c` | GPL-2.0-only；Copyright (c) 2016–2020, The Linux Foundation. All rights reserved.；主从分频写入路径，对应 0005 的分频同步参考说明 |

文件 SHA-256 分别为：

- `dsi_ctrl_hw_cmn.c`：`bd033c21958a9f7fe87332ed34b13c83361459444961c593732b0c00971ac4d3`
- `dsi_pll_7nm.c`：`a286700822a0fb2fa1e9bff39cc6720295254c6137f29de65a37bcb819a8dd64`

归档哈希用于固定本次检查对象，不代替官方网站来源验证。这两份文件没有作为完整文件加入本仓库。0005 同时有 PLL 计数调整；最初审查尚未核验上游提交对象，随后已由本文开头的计数修改来源补核更新；不能将整个补丁的来源都归到厂商分频实现。

## 设备树：找到了源码链，但尚未闭合

板级 include 链按从外到内的主题为：IPCC 启用 → 移除临时显示保持节点 → GPU 启用 → 面板背光引用 → SD 电压设置 → 只读电量计 → SPI 触摸 → 背光节点 → I2C 控制器 → 双路 C-PHY 面板 → 板级基线。底层引用上游 `sm8250.dtsi`、`pm8150.dtsi` 以及私有 memory include；各层有 GPL SPDX 标识。后续 THP 触摸修改引用 IPCC 层，候选复核记录其 DTB 原样沿用；USB 整合再从该 DTB 反编译并加入 USB 片段，形成发布快照的直接前身。

这比“没有源码、只能从头重建”更完整；但只找到 include 关系和生成记录，不能证明每个历史编译输入、私有 include、后续编辑及现有快照已经逐项核对。当前 NOTICE 保留部分上游声明，不能视为完整来源审查结果。本次不重新编译、也不复制私有 include 到公开候选。

## 历史方案与当前状态

最初审查建议暂不分发来源许可未闭合的面板数组和反编译快照。后续已移除这两类材料，改为所有者自行提取面板数据及独立板级源码，见上方“当前发布范围更新”和板级说明。上游计数修改的来源已单独补核；下游发布来源、数据授权和完整历史输入链仍待核实。仅加免责声明或“责任自负”不会增加来源证明。

## English summary

Patch 0002's 104 on packets and 5 off packets exactly match the historical runtime DTB. The generation script reads that DTB; the XBL XML examined later is comparison material, not the direct source. Redistribution evidence for the extracted table remains unresolved.

Both downstream reference C files match members of the pinned local vendor archive and carry explicit GPL-2.0-only notices. This verifies those reference files, not every change in patch 0005 or the original download page. An eleven-file board DTS include chain was recovered, but complete input attribution and correspondence to the published snapshot are still unverified.

The initial audit proposed omitting unresolved panel arrays and the decompiled snapshot. Subsequent source separation removed both from the distributed tree and supplied extraction tools/reconstructed board source. The upstream count attribution was resolved separately above; downstream download provenance, data permissions and complete historical input attribution remain unresolved.
