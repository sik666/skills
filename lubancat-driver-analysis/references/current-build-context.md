# Current Build Context

## Workspace and Tree Identity

- The SDK kernel tree may appear under more than one absolute path on this machine, commonly:
  - `/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel`
  - `/mnt/data_0/xuke/from_haodong_data/LubanCat_Linux_rk3588_SDK_20260113/kernel`
- Always anchor analysis and file edits to the current `pwd`. Do not mix trees in one answer or patch.

## Current Kernel Baseline

- Kernel version from `.config`: `5.10.160`
- Architecture: `arm64`
- Compiler recorded in `.config`:
  - `aarch64-none-linux-gnu-gcc 10.3.1`
- Current board family in this SDK: LubanCat RK3588 / LubanCat 5 IO carrier

## SDK Board Build Facts

These were already traced in the local notes and should be treated as the working board defaults unless the user explicitly switches products.

- `RK_ARCH=arm64`
- `RK_KERNEL_DEFCONFIG=lubancat_linux_rk3588_defconfig`
- `RK_KERNEL_DTS=rk3588-lubancat-generic`
- `RK_EXTBOOT=true`
- `build.sh kerneldeb` ultimately uses kernel `bindeb-pkg`

High-signal local note:

- `.ai_output/all/build_summary.md`

## Device Tree Build Chain

For this SDK, the important mental model is:

1. `make ARCH=arm64 lubancat_linux_rk3588_defconfig`
2. `make ARCH=arm64 rockchip/rk3588-lubancat-generic.dtb`
3. `gcc -E` preprocesses `.dts` and expands included `.dtsi`
4. `dtc` compiles the merged tree into `.dtb`
5. overlay `.dts` files are compiled separately into `.dtbo`

Important consequence:

- There is no “link many dtb files together at the end”.
- Each final board target such as `rk3588-lubancat-generic.dtb` comes from one board `.dts` entry plus all included `.dtsi`.

## External Module Build Context

The IMX415 external-module labs use a lighter, isolated build environment instead of the full firmware-build container.

Known local files:

- `.ai_output/camera_learning/src/imx415_port/Dockerfile`
- `.ai_output/camera_learning/src/imx415_port/README.Docker.md`
- `.ai_output/camera_learning/src/imx415_port/README.md`

Important defaults from that environment:

- `ARCH=arm64`
- `CROSS_COMPILE=aarch64-linux-gnu-`
- toolchain package is `gcc-aarch64-linux-gnu`
- `dtc` is installed for overlay and dtbo experiments

Use this lighter container when the task is “compile external module / compile overlay / keep camera lab environment isolated”. Use the full SDK build flow only when the task truly needs boot image, extboot, Debian packages, or firmware packaging.
