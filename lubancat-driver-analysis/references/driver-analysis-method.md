# Driver Analysis Method

## 1. Start From the Physical Interface

Do not start from C code. First answer:

1. Which real connector or header is involved.
2. What its pin count, pitch, orientation, and voltage rails are.
3. Which pins are power, ground, low-speed control, and high-speed data.
4. Whether the target module is physically and electrically compatible.

For LubanCat work, that usually means reading:

- schematic PDF
- size drawing
- assembly/BOM file
- pinmux spreadsheet

If connector compatibility is unclear, treat that as a hardware question first, not a driver question.

## 2. Map Nets to SoC Resources

Convert board net names into SoC-visible resources:

- GPIO bank and pin
- I2C/SPI/UART controller instance
- MIPI CSI/DSI, USB, PCIe, Ethernet, audio, or display controller
- power switch, regulator, GPIO expander, clock source, reset source

This step turns “CAM2_PWDN” or “I2C2_SDA_M4” into something Linux can model.

## 3. Read the Device Tree as the Board Model

Answer these questions in order:

1. Which board `.dts` is the final entry.
2. Which `.dtsi` files it includes.
3. Which nodes are provided by the SoC layer and which are enabled at board level.
4. Whether the feature is turned on by the base board `.dts` or by overlay.
5. Which `status`, `pinctrl`, `clocks`, `resets`, `supplies`, `gpios`, `ports`, and `remote-endpoint` properties matter.

For media pipelines, always trace both:

- control path resources such as clocks, GPIOs, regulators, I2C
- data path graph such as `port` and `endpoint`

## 4. Trace Linux Device Modeling

Do not stop at “which file contains the driver”. Explain:

1. Which bus creates the device.
2. Which structure represents the device at runtime.
3. How driver matching happens.
4. Which probe function performs the real setup.
5. Which private struct owns the device state.
6. Which ops tables expose behavior to the rest of the kernel or to user space.

Typical bus questions:

- `platform_bus_type`: SoC-integrated controllers and many board-level devices
- `i2c_bus_type`: sensor/client devices behind an I2C adapter
- `spi_bus_type`: SPI peripherals behind a SPI controller
- V4L2/media-specific objects on top of the above, such as `v4l2_subdev`, `video_device`, and `media_entity`

## 5. Separate “Bus Identity” From “Subsystem Identity”

Many complex peripherals have two identities at once.

Examples:

- a camera sensor is an `i2c_client` on the I2C bus
- the same sensor is also a `v4l2_subdev` in the media graph
- an ISP block may be a `platform_device`, while also creating several `video_device` and subdev nodes

If a chain is confusing, explicitly write both identities for each component.

## 6. Trace Runtime Evidence, Not Just Static Code

Once the static chain is understood, validate with live evidence:

- `dmesg`
- `lsmod`
- `/proc/device-tree`
- `/sys/class/*`
- `i2cdetect`, `i2ctransfer`, or subsystem-specific tools when appropriate
- `media-ctl`, `v4l2-ctl` for camera/media

For V4L2/media, record at least:

- `/dev/mediaX`
- `/dev/videoX`
- `/dev/v4l-subdevX`
- entity names
- enabled links
- active format on each relevant pad

## 7. Produce a Reusable Summary

A good board-driver analysis summary should leave:

1. the physical connector and compatibility conclusion
2. the exact DTS nodes and overlays involved
3. the bus and probe chain
4. the private structs and ops that matter
5. the runtime nodes and validation commands
6. unresolved gaps that still require schematic, datasheet, or live-board confirmation

## 8. Camera-Specific Shortcut

For LubanCat camera work, the most efficient order is usually:

1. board camera connector and schematic
2. board camera `.dtsi` and overlay
3. sensor node and endpoint graph
4. I2C adapter -> sensor probe
5. DPHY / CSI2 / CIF / ISP chain
6. V4L2/media runtime graph
7. user-space capture or preview validation

Do not collapse the whole path into “the sensor driver”. Camera bring-up spans multiple drivers and a media graph.
