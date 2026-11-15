# dby-w09-kernel

R4 (2026-11-15): the maintainer passed a fresh installation from a blank **16 GB card** following the public documentation, with bundle **`20261115-1`** (**H + R**: Claude’s SSH checks and the user’s observations, supplied in the maintainer report). See the [fresh-install results and checklist](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/fresh-install.md). Independent third-party reproduction remains **U**. Existing private inputs were reused; extraction was not repeated and retains its prior evidence level. The existing Recovery/U-Boot was retained, without rebuilding or reflashing; preserve the previous working card for rollback.

Current source scope: twelve patches plus board integration. Device evidence is limited to one tablet; audio, charging, power-key/cover and Venus results and unresolved defects are in the [hub status](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md). An unlocked bootloader and replacement Recovery are required; an incorrect image can leave the device unbootable. **The installation workflow has not been independently validated by a third party starting from a blank card. Feedback is welcome.**

Twelve patches, configuration and board source for Linux 7.2.10 on the Huawei MatePad 11 (DBY-W09, Snapdragon 865 / SM8250). Full upstream sources and owner-specific data are supplied separately.

[简体中文](README.zh-CN.md) · [Project hub](https://github.com/youzjuzi/dby-w09-linux) · [U-Boot](https://github.com/youzjuzi/dby-w09-uboot) · [Install and device checks](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md)

## Scope and evidence

**O, historical six-patch baseline**: six patches replay with fuzz=0; Image/modules and the standalone DTB were built from pinned sources. The comment cleanup reproduced the DTB hash with 36 dtc warnings, without dt-schema acceptance. **H**, 2026-11-02: the rebuilt kernel/DTB/module combination booted minimal and full desktop cards on one unlocked DBY-W09/HarmonyOS 4.2.0.213. Display/network records and **R** desktop observations are detailed in the hub's [status page](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md).

Touch passed a short rebuilt-baseline device/interaction check with guard=0 (**H + R**, 2026-11-02); see the hub's [status page](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md). Current three-finger gestures, stylus, touch startup/long-term reliability, suspend and long-term stability and other devices/firmware remain **U**. Historical earlier-project results do not validate those items here. DP3 improved normal-paced screen cycling on one tablet (2026-11-15, maintainer H + R record); rapid-toggle stripes and long-term reliability remain unresolved. Patches are device-specific development work, not ready for general upstream use.

Bluetooth on one tablet (2026-11-03): with an owner-supplied DTB controller identity, the controller is UP and visible to BlueZ/GNOME (**H + R**); one Bluetooth mouse paired and worked (**R**). Reconnection after reboot/sleep, other device types and A2DP remain **U**. See the hub status page linked above.

The [hub](https://github.com/youzjuzi/dby-w09-linux) supplies out-of-tree backlight/gauge/touch sources, bundle/rootfs builders and the SD installer. The [U-Boot repository](https://github.com/youzjuzi/dby-w09-uboot) builds the Recovery bootloader. This repository does not install or flash a system.

## Prepare owner inputs

Generate your private panel header using [panel-data.md](docs/panel-data.md), and the private memory include using the [board-tree guide](dts/README.md). Use your own supported stock runtime FDT; no panel command arrays, memory include, identity or firmware is distributed. Hash checks fix the inspected input/layout; do not bypass them for another version. Touch requires separate private plan inputs and is not built by this kernel recipe.

## Reproduce the pinned kernel and DTB

Obtain [linux-7.2.10.tar.xz](https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.10.tar.xz). Dependencies include arm64 GCC/binutils (recorded GCC 15.2.0), native kernel build prerequisites, make/patch/tar/xz, coreutils, Python 3 and dtc (recorded 1.7.2). See the [complete build/integration guide](docs/build.md) for dependency details, expected files and external modules.

Run from this repository in a fresh shell. Replace the archive, work, panel-header and memory-include placeholders; the new work directory's parent must exist, outside Git. This builds on the host only:

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
test "$#" -eq 12
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

The archive is pinned to SHA-256 `2feaa70453e91f541be6a5c9078d8168e081af45a3d9718054850538cff2ebf3`. Keep the final olddefconfig result: `PCI_PWRCTRL_PWRSEQ` changes from y to m, and the hub bundle module list includes that module. Keep the complete source/build pair for `modules_install`, along with matching external drivers. Do not use the host kernel's build tree or force the old config to hide a difference.

## Recorded outputs (O)

These are the historical six-patch baseline hashes, not expected hashes for the current twelve-patch configuration, audio, Hall/timer or Venus board additions.

| Output | SHA-256 |
|---|---|
| Raw `Image` | `0f1d0a0802c651cd2cbe049c78e3c8d21b14d95b95fca588bb8bae5f89f509a7` |
| `dby-w09.dtb` | `f2cf2c8fb6c8a170ad753062823760dd100e3fc915d6b60b4b428795f1a50cfd` |

The DTB hash was rebuilt identically after comment cleanup. Image identity also depends on toolchain, final configuration, timestamps and private panel data; its hash is from the recorded full build, separate from the later DTB-only recheck. These hashes are recorded baselines, not compatibility gates for arbitrary owner inputs. The original board-source comparison and its phandle/model/identity differences are explained in [provenance](dts/provenance.md); the normalized comparison was not repeated in the clean rebuild.

## Handoff and references

Use the [build guide](docs/build.md#5-bundle-handoff) for source/build/DTB/external-module mappings. The hub's [installation guide](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md) covers bundle configuration, test/full rootfs, whole-SD installation, seed, Recovery, first boot and checks. There is no dependency on an internal development repository.

- [Patch notes](docs/patch-notes.md) — changes and limits.
- [Source review](docs/provenance-review.md) — upstream/revert references and data boundaries.
- [Board source and build](dts/README.md).
- [Third-party materials](THIRD_PARTY.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md).

This is an independent, unofficial device-porting project. It is not affiliated with, endorsed by, or sponsored by Huawei/HarmonyOS/MatePad, Canonical/Ubuntu, Qualcomm or TeamWin. Names and trademarks belong to their respective owners. Vendor firmware is not provided, and compatibility with other devices or firmware is not guaranteed.

An already unlocked bootloader is required for the integrated system. Flashing replaces Recovery, and the modified image does not match the original AVB digest. An incorrect image or operation can make the device unbootable or Recovery unusable. Installation erases the selected SD card. Keep and verify your own stock rollback image, and restore stock Recovery before a factory reset. The software is provided as is, without warranty. This is a source repository; follow the hub's [installation guide](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md) for integration prerequisites and risks.

Source licences follow the original files and the [per-patch table](THIRD_PARTY.md). See [LICENSE](LICENSE), `dts/NOTICE` and `LICENSES/`. Owner-extracted data is not licensed by these tools.

## Experimental onboard capture

Opt-in onboard capture topology (**H + R**, one tablet, 2026-11-06): with the matching hub packages (`20261102-12` / `20261102-13`) and patch `0008`, default boot leaves ADSP stopped; explicit two-stage startup brought ADSP/APR up, registered `sm8250 - DBY-W09`, recorded real signal simultaneously on all four analog microphone channels (`rms_dbfs` −31.79 / −47.82 / −29.97 / −32.63), and exposed the 4-channel `Internal Microphone` in PipeWire/GNOME via read-only ALSA UCM2 alongside USB-C digital headsets; reboot returned to the stopped default. Speakers (**H + R**, one tablet, 2026-11-07, hub package `20261102-16`): with patches `0009`/`0010`, the four TFA9874 amplifiers on Primary TDM0 played desktop audio through `Internal Speakers` in short sessions with no fault flags; there is no speaker protection algorithm. Physical channel-to-microphone mapping and long-term speaker use remain **U**. See [audio notes](docs/audio-capture.md).

`SOURCE_DATE_EPOCH` alone does not freeze the kernel UTS/initramfs timestamps on this baseline; R4 records actual build times. See the [R4 build notes](docs/build.md#r4-host-recheck-notes-2026-11-15) for the additional variables needed for a separately controlled byte-reproduction run.
