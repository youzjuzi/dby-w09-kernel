# Patch notes

Language: English. 中文构建入口：[README.zh-CN.md](../README.zh-CN.md)。This page describes patch mechanisms/provenance (O); current hardware limits are in the hub [status](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md).

All patches apply to Linux 7.2.10. Evidence classes: H = observed on hardware by the maintainer; O = offline check only.

| # | Patch | Purpose | Upstream suitability |
|---|---|---|---|
| 0001 | dt-bindings: panel nt36523 | Adds the compatible `huawei,dby-w09-nt36523` to the existing Novatek NT36523 panel binding | Suitable once 0002 is |
| 0002 | drm/panel: nt36523 DBY-W09 panel | Adds a panel description (timings, owner-generated command-header integration, reset steps) for this device to the existing Novatek NT36523 driver | Needs rework; initialisation data is device specific |
| 0003 | drm/panel: nt36523 refresh-rate parameters | Adds `refresh_hz` (60 or 120) and `non_burst`, defaulting to 120 Hz; parameters lock at first DBY probe. Also acquires the external backlight directly and controls it through panel enable/disable callbacks for the DRM=y/BACKLIGHT_CLASS_DEVICE=m configuration | Local policy and backlight integration; not prepared for upstream |
| 0004 | drm/msm/dsi: host | Programs the DSI high-speed transmit timeout. The soft-reset default repeatedly times out on this device. The value follows the downstream Qualcomm driver | Candidate; needs an upstream review of the value and the hardware revisions affected |
| 0005 | drm/msm/dsi: 7nm PHY | Applies the clock divider of the master to the slave PHY in bonded C-PHY mode before PLL start; adjusts PLL enable-count handling | Local DBY-W09 adaptation; the original upstream count fix was reverted for a non-bonded regression |
| 0006 | ath11k: QCA6390 caldata | Adds QCA6390 HW2.0 to the calibration-data skip condition, including its BIN board-data case; the hardware-revision condition itself is not restricted to BIN | Candidate |

## Provenance

- The PLL-count portion of 0005 adapts Neil Armstrong's [upstream commit 93c97bc8d85d](https://github.com/torvalds/linux/commit/93c97bc8d85d), retaining local locking and `pll_data`. The original was [reverted in 44784327815b](https://github.com/torvalds/linux/commit/44784327815b) after a non-bonded divider regression. See the [hunk mapping and limitations](provenance-review.md). This is not a complete cherry-pick or a general upstream fix.
- Patch 0004 and the divider-synchronization portion of 0005 were informed by reading the open-source downstream kernel sources published for the device (Qualcomm display driver code and the vendor's PLL divider handling). The two inspected reference files carry GPL-2.0-only notices; the original download page and release identifier remain unverified. See the [per-patch licence table](../THIRD_PARTY.md).
- Patch 0002's command tables were generated from the owner's runtime DTB (104 on and 5 off packets verified). The XBL XML examined later was comparison material, not the direct source. See [provenance review](provenance-review.md) for remaining permission questions and exact downstream reference files.

## Verification

Patches 0001–0006 applied in order with zero fuzz to pristine files from the 7.2.10 archive reproduce the source files used to build the tested kernel and modules, byte for byte (class O). Functional behaviour (display, wireless) was observed on one device (class H).

## Owner-data separation

Command arrays are no longer embedded in 0002. Use [the extraction tool and guide](panel-data.md) to supply the private header before compiling. Patch 0003 still relies on the pinned packet ordering. Zero-fuzz replay was repeated after this change; no complete rebuild or device validation was performed.

## Four-channel capture (H + R, 2026-11-06)

Patch `0008` preserves the negotiated channel interval only for
`TX_CODEC_DMA_TX_3`. The AFE and TX macro DAIs allow 1–8 channels and
WCD938x capture allows 1–4, so their intersection permits four channels.
The machine driver's hardcoded fixup has no DT property override.
All other backends retain stereo; every backend retains 48 kHz/S16_LE.
The externally rebuilt `snd-soc-sm8250` module supplements the historical
six-patch full build without rebuilding Image or changing DTB, and was
validated on one tablet (H + R, 2026-11-06, bundle `20261102-12`) with
real simultaneous signal on all four analog microphone channels.

## A3a Primary TDM speaker transport (O)

Patch 0009 carries DT data-output, sync inversion and data delay fields through
q6afe-dai into the q6afe APR TDM configuration. Patch 0010 applies after 0008,
preserves negotiated Primary TDM0 channels, sets a 6.144 MHz bit clock, and
configures four 32-bit slots with byte offsets 0, 4, 8, 12. Shutdown disables that
clock and retains SoundWire cleanup. The four-microphone fix remains intact.

The board enables GPI DMA0 and I2C3, four board-specific TFA9874 codecs, the shared
active-high reset on GPIO109, and Primary TDM pins 138..141. New phandles occupy
0x100e..0x1013. The DTB test checks these values and restricts raw property changes
to the audio allowlist, including only the DMA status property. WSA stays disabled.

The companion amplifier module requires [private table generation](https://github.com/youzjuzi/dby-w09-linux/blob/main/drivers/dby-tfa9874/README.md) before building, with `TFA_TABLES_DIR` pointing to the generated header. These owner inputs are not distributed. / 喇叭模块构建前须从所有者自己的配置生成私有表，并通过 `TFA_TABLES_DIR` 指定；所有者数据不分发。

The companion amplifier module defaults locked off. UCM2 remains microphone-only.
Host patch replay, compilation and DT comparison are O; I2C probe, TDM timing,
speaker output and coexistence with capture still require owner device testing (U).

A3b extends 0010's Primary TDM fixup: reject channel minimum greater than four and
cap maximum at four. The executable harness covers all frontend IDs and channel
intervals 1..8, including rejection and the unchanged microphone branch (O).

Device result (H + R, 2026-11-07, one tablet, Linux package `20261102-16`): with
patches 0009/0010 and the companion amplifier module, all four TFA9874 amplifiers
locked to Primary TDM0 and played desktop audio with no clock, TDM or clip flags,
and four-channel capture kept working. Desktop loudness depends on the Linux
package's WirePlumber S16LE rule; this kernel tree is unchanged by that rule.

## 0013: GPIO alarm IRQ recovery (O; device results H + R, 2026-11-16)

Patch 0013 extends the binding in the new patch, leaving 0001 unchanged.
Optional `esd-gpios` allows one or two alarm inputs, normal low; this recovery
policy requires two corroborating outputs. Missing inputs leave monitoring off;
a single input or an acquisition/IRQ error warns and disables monitoring without
failing panel probe. Partial IRQ requests and GPIO ownership are released on
failure. No pin bias, panel power timing, DCS command or DPU/DSI change is made.

Both edges restart a 1000 ms delayed check; enable also schedules one check.
Both queueing sites use `system_dfl_wq` to avoid the deprecated workqueue warning;
the recovery policy and callback synchronization are unchanged.
Under DRM modeset locks, work rechecks the deadline, enabled flag, two high GPIOs
and an active connector/CRTC. GPIO read errors never count as high. The panel
bridge reference is balanced, with a bridge lifetime guard; reset uses upstream
`drm_bridge_helper_reset_crtc()` and modeset backoff on `-EDEADLK`, following
`ti-sn65dsi83.c`. Touch continues to use its existing panel follower callbacks.
Disable clears enabled and cancels non-synchronously: reset itself calls disable
and enable, so waiting for this work in either callback would deadlock. Remove
blocks new scheduling, disables both IRQs, then synchronously cancels work.

There are at most five attempts in any rolling 60 seconds. A sixth request logs
once and blocks recovery for 60 seconds; the next edge or enable after that can
recover again. There is no polling or independent cooldown timer. A successful
reset's enable schedules the follow-up check, including persistent-high alarms.
`esd_recovery` defaults to 1, is writable at runtime (0644), and 0 logs
“would reset” without resetting. It retains GPIO ownership and IRQ monitoring.

The stock panel DT enables GPIO-only ESD detection on TLMM 135/136 with normal
value 0. Both-high detection and the one-second delay follow the existing
userspace watchdog policy and reported sub-second enable transients. This IRQ
adaptation, reset latency, touch recovery and real failure rate remain Pending;
software tests and compilation cannot validate them. The minimum-off experiment
is not part of this series. See the hub's display recovery instructions before
manually starting the retained Python watchdog.

Device results (one tablet, one card, bundles `20261116-11`/`-12`; H = kernel log
read by the maintainer, R = user observation): about 450 alarm edges from normal
and rapid screen off/on produced no false reset. Four real both-high events were
seen; each reset completed with `ret=0` in one attempt and the alarms returned low.
Three of them happened shortly after a screen wake (including GNOME switching to
60 Hz at login): the picture returned by itself 1.6–1.9 s after the panel was
enabled, versus 5–6 s with the old userspace watchdog. **Known limitation:** one
event occurred while the screen was on and idle; after the reset the screen stayed
black until the user touched it, with no further kernel display activity (cause
not identified, U). Failure rates and long-term behavior are not established.


## 0014: selectable 30/60/120 Hz modes (O; device results H + R, 2026-11-16)

The DBY-W09 panel now exposes three DRM modes with the same 584849 kHz pixel
clock, horizontal timing, four-line VSYNC and 237-line VBP. VFP is 8507/2853/26
for 30/60/120 Hz (vtotal 11308/5654/2827); upstream `drm_mode_vrefresh()` rounds
them to exactly those rates. This changes only VFP: the DSI PLL/link rate stays
the same, but switching requires the existing full modeset with panel off/on.
It is not seamless DFPS or variable refresh.

`refresh_hz` now selects the preferred boot mode, accepting 30/60/120, default
120; it still locks at DBY probe. All three modes carry DRIVER, and only the
selected preference carries PREFERRED. Other panel variants keep their previous
first-mode preference. `non_burst`, power timings and ESD recovery are unchanged.
The installer seed still accepts only 60/120; no Linux hub code changes here.

The connector recorded by `get_modes` supplies the current CRTC's `adjusted_mode`
during prepare, after the atomic state swap. A missing/unusable state falls back
to `refresh_hz` and emits one warning per panel instance. Each successful path
through the rate setup logs `panel: mode NNN Hz, 0x23=0xNN`; ESD reset and normal
screen off/on therefore reapply the current mode, not merely the preference.

The original owner header is untouched: its initial page 0x2a/0x23 write remains
0x0c. The extra four-packet selector is inserted immediately before the first
DCS sleep-out (0x11), also before display-on (0x29), and returns to page 0x10.
The pinned table is already on page 0x10 there. The code finds sleep-out by packet
type/length/opcode, without depending on a packet index; a missing marker fails
before any transfer. All existing packets and delays, including commands after
display-on and the off sequence, are preserved. Any selector transfer error
aborts preparation through its existing power cleanup.

Provenance: the owner's `lcd_kit_debussy_290_20d_10p9_qcom` stock DT advertises
30/60/120 and VFP-based updates. Its to-30/60/120 commands select page 0x2a,
unlock with 0xfb=1, write 0x23=0x0e/0x0c/0x0d and return to page 0x10. They are
DCS long writes in HS mode for switching while video is running. During prepare,
this implementation sends the same selector values and long-write types to both
DSI links in **LP mode**, together with the initialization sequence, with no extra
delay.
The mode lookup/insertion approach was compared read-only with
[CoWave-Fall's panel patch at 6a77acb](https://github.com/CoWave-Fall/linux-on-arm-matepad11/blob/6a77acb2824198ff521e408b83585c32190315f3/kernel/patches/0006-drm-panel-nt36523-add-dby-w09.patch).
That reference describes another panel variant and is not our command-table
source; no code or initialization arrays were copied from it.

Device results (bundle `20261116-12`, H + R): GNOME Settings lists 30/60/120 Hz;
switching 120 → 60 → 30 → 120 logged `0x23=0x0c/0x0e/0x0d` with matching vtotal
5654/11308/2827, and the user saw no tearing, stripes or flicker. Screen off/on
(7 times at 30 Hz, 5 at 120 Hz) kept the selected rate; a 60 Hz choice persisted
across reboot (the kernel boots at 120 Hz, then GNOME applies 60 Hz). ESD resets
reapplied the current rate. Whether 60 Hz shows more black screens than 120 Hz
is not established (user impression R; small sample).

Offline tests execute the replayed mode enumeration, parameter policy and
transfer functions with synthetic panel data, together with upstream vrefresh.
They cover all preferred/active-rate combinations, missing-state fallback,
original LP command preservation, dual-link LP selectors and transfer failures.
GNOME enumeration, actual scan rate, transitions, remembered modes, ESD recovery,
black-screen/stripe rates and long-term stability require owner device testing.
