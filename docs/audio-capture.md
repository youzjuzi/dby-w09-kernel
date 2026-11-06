# Experimental capture board tree

板载录音：离线构建，实验性，未验证 (U)。The topology adds ADSP/APR, VA and WCD938x capture links over the existing board tree. No playback link or speaker amplifier is enabled; WSA remains disabled. Upstream sm8250-mtp supplies the structural reference. Reset GPIO, SoundWire ports, microphone wiring and 1.8 V micbias retain previously device-tested board parameters; this newly packaged combination is unverified.

The private memory include already reserves the ADSP region. The board tree restores its memory-region reference after replacing upstream reserved-memory. The relocatable MDT uses segment offsets within that region; no new memory carveout is created. DMIC routes remain from the earlier capture topology, alongside the eight analog routing pairs; retaining them does not claim digital microphone hardware is present. VA uses the previously tested 2.4 MHz setting, not a claim that the stock VA property itself has that value.

Audio-only phandles occupy a separate fixed range to preserve unrelated property bytes. The DTB comparison test rejects every non-audio raw property change, including charger, display, input and radio changes; both baseline and candidate retain 36 dtc warnings. This is not dt-schema validation.

耳机检测基础设施已初始化；3.5 mm 接口是否存在未验证。On explicit startup, the unchanged codec probe configures HPH gain/HD2, reference-buffer and surge-protection registers; MBHC allocates state/interrupts, and the machine driver creates a jack and starts detection. No claim of zero headphone activity is made. No additional headset jack/aux-devs route is described in DT. Two capture channels are the unmodified backend limit.

Use the matching hub package with explicit startup and coldplug blacklists. Merely enabling these nodes without that packaging policy is not the tested default. Device boot, capture signals and coexistence remain U.

Host-only comparison:

```sh
python3 -B tests/test-audio-dtb.py /path/to/control.dtb /path/to/capture.dtb
```
