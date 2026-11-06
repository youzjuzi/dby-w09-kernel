# Experimental capture board tree

板载录音：实验性显式启动，四路模拟麦克风同时录音与桌面 UCM2 `Internal Microphone` 集成已在一台设备验证 (H + R, 2026-11-06)；物理麦克风映射与喇叭仍未验证 (U)。The topology adds ADSP/APR, VA and WCD938x capture links over the existing board tree. No playback link or speaker amplifier is enabled; WSA remains disabled. Upstream sm8250-mtp supplies the structural reference. Reset GPIO, SoundWire ports, microphone wiring and 1.8 V micbias retain device-tested board parameters.

The private memory include already reserves the ADSP region. The board tree restores its memory-region reference after replacing upstream reserved-memory. The relocatable MDT uses segment offsets within that region; no new memory carveout is created. DMIC routes remain from the earlier capture topology, alongside the eight analog routing pairs; retaining them does not claim digital microphone hardware is present. VA uses the previously tested 2.4 MHz setting, not a claim that the stock VA property itself has that value.

Audio-only phandles occupy a separate fixed range to preserve unrelated property bytes. The DTB comparison test rejects every non-audio raw property change, including charger, display, input and radio changes; both baseline and candidate retain 36 dtc warnings. This is not dt-schema validation.

耳机检测基础设施已初始化；3.5 mm 接口是否存在未验证。On explicit startup, the unchanged codec probe configures HPH gain/HD2, reference-buffer and surge-protection registers; MBHC allocates state/interrupts, and the machine driver creates a jack and starts detection. No claim of zero headphone activity is made. No additional headset jack/aux-devs route is described in DT.

Use the matching hub package (`20261102-12` / `20261102-13`) with explicit startup and coldplug blacklists. Merely enabling these nodes without that packaging policy is not the tested default. On one tablet (2026-11-06, H + R), default boot left ADSP stopped, explicit startup brought ADSP/APR and `sm8250 - DBY-W09` up, a 12-second 48 kHz S16_LE 4-channel capture recorded real signal simultaneously on channels 1–4, read-only UCM2 in `20261102-13` exposed the 4-channel `Internal Microphone` in PipeWire/GNOME alongside USB-C digital headsets, and reboot restored the stopped default. Speakers remain U.

Host-only comparison:

```sh
python3 -B tests/test-audio-dtb.py /path/to/control.dtb /path/to/capture.dtb
```

## Four-channel capture and desktop UCM2 integration (H + R, 2026-11-06)

Patch `0008` preserves the negotiated channel interval only for
`TX_CODEC_DMA_TX_3`. The AFE and TX macro DAIs allow 1–8 channels and
WCD938x capture allows 1–4, so their intersection permits four channels.
The machine driver's hardcoded fixup has no DT property override.
All other backends retain stereo; every backend retains 48 kHz/S16_LE.
The externally rebuilt `snd-soc-sm8250` module in packages `20261102-12` /
`20261102-13` supplements the historical six-patch full build without
rebuilding Image or changing DTB, and was validated on one tablet (H + R,
2026-11-06) with real signal on all four capture channels (`rms_dbfs`
−31.79 / −47.82 / −29.97 / −32.63) and 4-channel `Internal Microphone`
discovery in PipeWire/GNOME via hub package `20261102-13`. Physical
microphone-to-channel mapping and speakers remain U.

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

The companion amplifier module defaults locked off. UCM2 remains microphone-only.
Host patch replay, compilation and DT comparison are O; I2C probe, TDM timing,
speaker output and coexistence with capture still require owner device testing (U).
