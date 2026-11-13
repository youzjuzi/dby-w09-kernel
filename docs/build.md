# Kernel build and integration

[简体中文](build.zh-CN.md) · [Back to README](../README.md)

Language: English; [中文](build.zh-CN.md). These commands describe host builds (O), without installation or card writes. A matching rebuilt kernel/DTB/module combination booted test/full cards on 2026-11-02 (H); see the hub [status](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md). A separately built guard=0 touch module passed a short device/interaction check (H + R); current three-finger gestures, stylus and long-term behavior remain U. The full kernel build record is separate from later DTB-only rechecks.

First [extract the private panel header](panel-data.md); the panel driver cannot compile without it.

## 1. Prerequisites

Supply this repository, the upstream `linux-7.2.10.tar.xz` archive and a Linux host. The recipe checks the pinned archive digest; this identifies the baseline but does not authenticate its origin.

Use a host C compiler and development headers, arm64 GCC/binutils with the `aarch64-linux-gnu-` prefix, GNU make, patch, tar, xz, bash, coreutils (including sha256sum and realpath), bc, bison, flex, Python 3, and OpenSSL/libcrypto and libelf development files. Consult the archive's `Documentation/process/changes.rst` for minimum versions. Enabling BTF may additionally require pahole; standalone DT compilation needs dtc. Packaging has separate dependencies including kmod and squashfs-tools.

The supplied configuration records GCC 15.2. Other toolchains may change configuration, warnings or output; byte-identical reproduction is not promised. Prepare enough disk space for the extracted source and full module build; peak usage has not been measured here. Obtain packages and sources separately for your distribution. Do not substitute the host's `/lib/modules/$(uname -r)/build` for the target build tree.

## 2. Verify and build

Run the complete block in a fresh shell after replacing its four absolute paths. Avoid spaces in paths. The work directory must not exist; its parent must exist, and it should be outside all Git checkouts. A failure stops the recipe: retain the work directory for diagnosis rather than continuing with a partially patched tree.

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
test "$#" -eq 10
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

Patches apply in filename order with zero fuzz. Review changes made by `olddefconfig` and retain the resulting `.config`; toolchain differences may change it. Do not ignore patch errors or disable required features to force progress. Parallelism is omitted; add `-jN` only as appropriate for host memory.

## 3. Expected outputs

These are expected after a successful build; they were not produced during this documentation task.

| File under `$KERNEL_BUILD` | Purpose |
|---|---|
| `arch/arm64/boot/Image` | Uncompressed arm64 kernel read from `kernel_build_dir` |
| `drivers/…/*.ko` and other module paths | In-tree modules; retain the entire tree for `kernel_build_dir` |
| `.config`, `Module.symvers` | Configuration and symbol information for module builds and packaging |
| `modules.order`, `modules.builtin`, `modules.builtin.modinfo` | Module installation metadata |
| `include/config/kernel.release` | Release string; the pack builder requires exactly `7.2.10` |

Retain both source and build trees: packaging invokes `modules_install` and needs all built modules. `CONFIG_LOCALVERSION_AUTO` is enabled, so use the clean archive outside Git checkouts and check the actual release. Investigate mismatches instead of changing gates to disguise them.

This does not build the board DTB, initramfs, device pack or Ubuntu filesystem. Use the separate [board-tree recipe](../dts/README.md) with an owner-generated memory include. Select the resulting DTB explicitly in the hub bundle configuration; the fixed digest gate belonged to the retired builder.

For an owner-selected Bluetooth address, optionally pass `--bd-address-file` in the DTB step; see [Bluetooth address rules and evidence](../dts/README.md#bluetooth-address).

## 4. Out-of-tree drivers

The hub repository `dby-w09-linux` supplies backlight, battery, charger, speaker and touch drivers. Use the same target source, build tree, configuration and toolchain as Image, after completing the full kernel/module build above. All four driver-copy destinations below must be new; retain old results before any repeat attempt.

Before copying or compiling the speaker module, [generate its private configuration tables](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md) from the owner's own files. Set `TFA_TABLES_DIR` to the absolute directory holding the generated header; missing inputs fail the build. The tables and modules containing them are not distributed.

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

Each `.ko` appears in its copied driver directory. Consult the hub's `drivers/rt8555-backlight/README.md` and `drivers/dby-fg-readonly/README.md` for dependencies and DT integration; a successful compile does not establish correct DT wiring.

Touch additionally requires pinned plan JSON inputs and generated `thp-plan-table.h`. Follow the hub's [optional touch setup](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md#31-enable-touch-optional) and build in a separate module directory with the same prepared kernel/source pair. Firmware extraction alone does not generate the plan data. The bundle requires a matching ten-parameter module and firmware, pins the unaccepted guard feature off, and uses the existing board touch node without a DTB/kernel change. The separate short H + R record does not establish long-term stability or hardware equivalence to the earlier module.

## 5. Bundle handoff

Paths below are relative to the respective repository roots; no adjacent checkout layout is required. In the hub, consult `tools/dby-bundle/README.md` and `tools/dby-install/README.md`, plus `docs/firmware-preparation.md` and `docs/source-scope.md`, for packaging, installation and private inputs. Start from `tools/dby-bundle/examples/bundle.example.json`; all relative paths resolve beside the configuration file.

| Bundle configuration field | Input |
|---|---|
| `kernel_source_dir` | Matching patched `$KERNEL_SOURCE` |
| `kernel_build_dir` | Complete `$KERNEL_BUILD`, including Image and built modules |
| `dtb` | Explicitly selected board DTB |
| `external_modules` | Destination-to-file mapping for separately built modules below |
| `private_inputs` | Explicit array of owner-supplied locked firmware/configuration directories |
| `touch.enabled` | Optional; requires matching module, firmware and pinned plan inputs; follow the hub's [touch setup](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md#31-enable-touch-optional) |
| `output` | New output directory with an existing parent |
| `sources` | Full repository commits and pinned upstream versions/digests |

In-tree modules are selected from the kernel build by the bundle tool's `modules.list`; historical external override paths are no longer defaults. For the separate modules, use these `external_modules` entries with actual build paths:

| Destination inside the device image | Host file |
|---|---|
| `kernel/drivers/video/backlight/rt8555-backlight.ko` | `$KERNEL_WORK/rt8555-backlight/rt8555-backlight.ko` |
| `kernel/drivers/power/supply/dby-fg-readonly.ko` | `$KERNEL_WORK/dby-fg-readonly/dby-fg-readonly.ko` |
| `kernel/drivers/power/supply/dby_chg.ko` | `$KERNEL_WORK/dby-chg/dby_chg.ko` |
| `kernel/sound/soc/codecs/dby-tfa9874.ko` | `$KERNEL_WORK/dby-tfa9874/dby-tfa9874.ko` |
| `kernel/drivers/input/touchscreen/nt36523-thp.ko` | Separately prepared touch build's `nt36523-thp.ko`, when enabled |

The builder invokes `modules_install`, checks exact module vermagic, and validates supplied private inventories, modes and digests. With touch disabled, omit its module and firmware inputs; supplied private directories are still validated. The selected DTB is used unchanged rather than compared to a historical fixed DTB digest.

A p1-only bundle is an intermediate output. The installer also requires the selected full or minimal rootfs archive; follow the hub tool documentation for rootfs construction and dry-run plans. Packaging or an offline build alone does not establish device operation. Neither the kernel repository nor the bundle builder assembles the U-Boot Recovery image.

The current hub module list selects `dby_chg.ko` and `dby-tfa9874.ko` as well as backlight/gauge/touch. Add the two new external mappings above; the older example JSON supplies only three external mappings. A successful compile is not a source-clearance or hardware-safety result. The charger writes PMIC registers; the speakers have no protection algorithm. Read the hub driver notes before selecting a bundle. Audio also needs owner-supplied locked ADSP firmware; the historical radio/GPU/touch-only recipe does not reproduce the current audio system.
