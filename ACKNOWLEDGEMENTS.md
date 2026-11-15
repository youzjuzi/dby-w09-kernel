# Acknowledgements

- The **Linux kernel** community, in particular the maintainers of Qualcomm SM8250 support, the msm DRM driver, the Novatek NT36523 panel driver, and the ath11k wireless driver.
- **Neil Armstrong**, author of the upstream PLL-count fix adapted in patch 0005; see [the source and revert history](docs/provenance-review.md).
- **CoWave-Fall** ([linux-on-arm-matepad11](https://github.com/CoWave-Fall/linux-on-arm-matepad11)), whose
  independent work on the same tablet suggested the complete NT36523 panel power sequence with an
  initial power cycle (patch 0011) and powering the DSI PHY digital domain together with the PLL bias
  (patch 0012). Both were reimplemented here; no code was copied.
- **Huawei**, which published an open-source kernel package for this device that served as a hardware reference. This project is not affiliated with Huawei.
- Everyone who tested, advised, or shared research.

Maintainer: see repository history.
