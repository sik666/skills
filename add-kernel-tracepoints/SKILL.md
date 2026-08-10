---
name: add-kernel-tracepoints
description: Add, extend, and validate Linux or Android kernel tracepoints. Use when Codex must instrument a kernel code path, choose an existing tracepoint versus a new TRACE_EVENT, expose stable fields to ftrace or eBPF, verify events through tracefs, or avoid misleading entry-point instrumentation.
---

# Add Kernel Tracepoints

## Workflow

1. Define the measurement question as a completed operation and its required fields. Do not instrument a broad entry point merely because it is nearby.
2. Search existing events first:

   ```bash
   rg -n 'TRACE_EVENT|DECLARE_EVENT_CLASS|DEFINE_EVENT|trace_<name>' \
     include/trace drivers kernel mm fs
   adb shell 'cat /sys/kernel/tracing/available_events | rg "<subsystem>|<keyword>"'
   ```

   Prefer a stable tracepoint when its semantics and fields answer the question. Use a kprobe only for transient debugging or when a tracepoint cannot expose the needed state safely.

3. Trace the source call chain and choose the point after the operation is committed. For example, record readahead after the code has formed and submitted its read window, not at a fault entry that may return without I/O.
4. Place the definition in `include/trace/events/<system>.h`; use `DECLARE_EVENT_CLASS` plus `DEFINE_EVENT` when multiple events share a layout. Include the header in the instrumented `.c` file and call the generated `trace_<event>()` function.
5. Export only fields needed for correlation and analysis. Prefer scalars, bounded strings, stable object identities, offsets, lengths, result codes, and flags. Do not export kernel pointers or raw physical addresses unless an explicitly privileged debug build requires them.
6. Rebuild the affected kernel or module, deploy through the established device-specific safe path, and validate in tracefs before writing eBPF/user-space consumers.

## Event Design

- Give each event one completed semantic action: `*_alloc`, `*_map`, `*_submit`, `*_complete`, `*_fault`, or `*_reclaim`.
- Use one event class only when all derived events have the same field meaning. Create separate classes for different semantics, such as faults versus readahead windows.
- Include a correlation identity appropriate to the subsystem: `pid_tgid`, device/context ID, DMA-BUF debug ID, `dev:ino`, IOVA, or request ID.
- Record quantities in unambiguous units and name fields accordingly: `offset_bytes`, `size_pages`, `latency_ns`.
- Keep `TP_fast_assign` nonblocking and allocation-free. Do not take locks, sleep, perform I/O, or dereference objects whose lifetime is not guaranteed.
- Keep `TP_printk` readable, but treat the binary trace record as the API used by eBPF/perf.

## Implementation Pattern

Read [references/tracepoint-patterns.md](references/tracepoint-patterns.md) before editing. Follow its header template and validation commands.

Required checks after editing:

```bash
rg -n 'TRACE_SYSTEM|DECLARE_EVENT_CLASS|DEFINE_EVENT|trace_<event>' \
  include/trace/events/<system>.h <instrumented-source>

adb shell 'test -e /sys/kernel/tracing/events/<system>/<event>/enable'
adb shell 'cat /sys/kernel/tracing/events/<system>/<event>/format'
adb shell 'echo 1 > /sys/kernel/tracing/events/<system>/<event>/enable'
adb shell 'echo 1 > /sys/kernel/tracing/tracing_on'
# Run the smallest workload that must trigger the event.
adb shell 'cat /sys/kernel/tracing/trace'
```

Validate all of the following:

- The event exists under the intended subsystem and its `format` contains every field.
- A known-positive workload emits the expected records.
- A known-negative path does not emit the event.
- Field units and identities match the source values.
- Event rate is acceptable with tracing enabled.

## eBPF Consumer

Attach by tracepoint name, define the raw context layout from the event `format` file, filter as early as possible by target PID/TGID or stable object identity, then copy only needed fields to a ring buffer. Do not infer a tracepoint layout from C structs alone; confirm the deployed kernel's `format` file.

## Safety

- Preserve existing tracepoint ABI when consumers already exist. Add a new event rather than changing field order or meaning.
- Do not call tracepoints under locks if their field extraction may take locks or access unstable objects.
- Rate-limit or aggregate high-frequency events when full per-operation tracing perturbs the workload.
- For Android boot-image work, build and flash only through the already validated device-specific workflow; verify boot and tracefs availability before collecting data.
