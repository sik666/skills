# Reference Map

## Board Hardware Documents

Read these first when the question is about connector pinout, GPIO availability, interface compatibility, voltage, FPC pitch, or which SoC signal reaches a board connector.

- `.ai_output/鲁班猫5-BTB/[野火]鲁班猫5BTB开发板硬件规格书_V1.1.2.pdf`
- `.ai_output/鲁班猫5-BTB/20240820_fix1/SCH/LubanCat5IOB_EBF410153V1R0_SCH_20240820.pdf`
- `.ai_output/鲁班猫5-BTB/20240820_fix1/SCH/LubanCat5CB_EBF410152V1R0_SCH_20240820.pdf`
- `.ai_output/鲁班猫5-BTB/20240820_fix1/尺寸图/LubanCat5IOB_EBF410153V1R0_尺寸图_20240820.pdf`
- `.ai_output/鲁班猫5-BTB/20240820_fix1/装配图/LubanCat5IOB_EBF410153V1R0_器件值文件_20240820.pdf`
- `.ai_output/鲁班猫5-BTB/20240820_fix1/LubanCat5CB_EBF410153V1R0_引脚功能复用表_20240820.xlsx`

## Build and Packaging Notes

Read these when the task is “how is this kernel/dtb/image built” or “which target produces what artifact”.

- `.ai_output/all/build_summary.md`
- `.ai_output/camera_learning/src/imx415_port/README.Docker.md`
- `.ai_output/camera_learning/src/imx415_port/README.md`

## Interface and Bring-Up Method Notes

Read these when the task is broader than one file and needs a repeatable method.

- `.ai_output/鲁班猫5-BTB/接口适配方法论.md`
- `.ai_output/camera_learning/README.md`
- `.ai_output/camera_learning/IMX415外部模块驱动开发阶段计划.md`

## Camera-Specific Local Knowledge

Read these when the task involves the LubanCat camera chain, IMX415, V4L2/media, or the existing lab project.

- `.ai_output/camera_learning/立芯嵌入式/CAM2_IMX415_全链路代码分布报告.md`
- `.ai_output/camera_learning/i2c和client驱动初始化/CAM2_IMX415_I2C控制器与Client初始化总结.md`
- `.ai_output/camera_learning/参考资料/V4L2系统关键数据结构与算法树状图_README.md`
- `.ai_output/camera_learning/src/stage0/README.md`
- `.ai_output/camera_learning/src/checkpoint/README.md`

## Useful Upstream/Source Tree Entry Points

Use these when you need to jump from notes to source:

- `arch/arm64/boot/dts/rockchip/`
- `arch/arm64/configs/lubancat_linux_rk3588_defconfig`
- `drivers/media/i2c/`
- `drivers/media/platform/rockchip/cif/`
- `drivers/media/platform/rockchip/isp/`

## Practical Rule

If the user asks “can this module/interface/device be adapted on this board”, do not start in `drivers/`. Start in the hardware documents, then move to DTS, then to the Linux bus/probe chain, then to runtime validation.
