---
name: lubancat-driver-analysis
description: Board-specific analysis guide for the LubanCat RK3588 SDK and carrier board. Use when Codex needs to analyze or modify drivers, device tree, overlays, build configuration, pinctrl, or interface compatibility on this board family, especially for camera/media, GPIO, I2C, SPI, UART, and bring-up tasks that must be traced from schematic and board documents through DTS, Linux bus/probe modeling, and runtime validation.
---

# LubanCat Driver Analysis

## Overview

Use this skill to keep LubanCat board work board-specific instead of drifting into generic kernel discussion. Start from the real connector and board documents, then map to DTS, Linux device model, driver-private structs and ops, and finally runtime evidence.

## Default Workflow

1. Anchor the workspace first.
2. Confirm the physical interface and electrical constraints before reading driver code.
3. Map the interface to the SoC controller, board DTS, and overlay/uEnv selection.
4. Trace Linux device creation and probe order on the correct bus.
5. Inspect the driver’s modeling style: private struct, ops tables, exported device nodes, and runtime graph objects.
6. Validate with runtime evidence from `/sys`, `/proc`, `dmesg`, and subsystem-specific tools.
7. Summarize the chain as “physical interface -> DTS nodes -> device objects -> probe path -> user/runtime entry points”.

## Read These References Selectively

- Read `references/current-build-context.md` when the task involves compiling, rebuilding dtbs, building external modules, or explaining how this SDK packages kernel artifacts.
- Read `references/reference-map.md` when the task is “where is the board document / prior note / camera report / schematic / pinmux table”.
- Read `references/driver-analysis-method.md` when tracing a new peripheral, producing a bring-up report, or explaining the modeling method across schematic, DTS, Linux bus, and runtime.

## Board-Specific Heuristics

- Prefer board documents and DTS over assumptions from connector names. A “24-pin MIPI” label does not imply electrical compatibility.
- Separate control plane and data plane. For cameras, I2C/resource control and MIPI/V4L2/media data flow are different layers and must be traced separately.
- Treat overlay and `uEnv` selection as first-class boot-time configuration, not as afterthoughts.
- For V4L2/media, track both identities of a component:
  - bus identity such as `i2c_client` or `platform_device`
  - media identity such as `v4l2_subdev`, `video_device`, `media_entity`
- For duplicated source trees under `/home/...` and `/mnt/...`, anchor all analysis to the current `pwd` and avoid mixing paths.

## Deliverables

- Prefer outputs that leave a reusable map:
  - key board documents and exact files to read
  - relevant DTS/overlay nodes
  - bus/match/probe chain
  - important runtime nodes such as `/dev`, `/sys`, `media-ctl`, or `v4l2-ctl`
  - remaining unknowns that still require schematic or live-board confirmation
