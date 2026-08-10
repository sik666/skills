# Kernel Tracepoint Patterns

## Definition Header

Create `include/trace/events/<system>.h` with the standard trace header guard. Use one `TRACE_SYSTEM` per subsystem.

```c
/* SPDX-License-Identifier: GPL-2.0 */
#undef TRACE_SYSTEM
#define TRACE_SYSTEM example

#if !defined(_TRACE_EXAMPLE_H) || defined(TRACE_HEADER_MULTI_READ)
#define _TRACE_EXAMPLE_H

#include <linux/tracepoint.h>

DECLARE_EVENT_CLASS(example_op_class,
    TP_PROTO(u64 id, u64 offset_bytes, u32 size_bytes, int ret),
    TP_ARGS(id, offset_bytes, size_bytes, ret),
    TP_STRUCT__entry(
        __field(u64, id)
        __field(u64, offset_bytes)
        __field(u32, size_bytes)
        __field(int, ret)
    ),
    TP_fast_assign(
        __entry->id = id;
        __entry->offset_bytes = offset_bytes;
        __entry->size_bytes = size_bytes;
        __entry->ret = ret;
    ),
    TP_printk("id=%llu off=%llu size=%u ret=%d",
        __entry->id, __entry->offset_bytes,
        __entry->size_bytes, __entry->ret)
);

DEFINE_EVENT(example_op_class, example_submit,
    TP_PROTO(u64 id, u64 offset_bytes, u32 size_bytes, int ret),
    TP_ARGS(id, offset_bytes, size_bytes, ret));

#endif /* _TRACE_EXAMPLE_H */

#include <trace/define_trace.h>
```

In the instrumented C file:

```c
#include <trace/events/example.h>

/* Emit only after the requested operation is known to have occurred. */
trace_example_submit(id, offset_bytes, size_bytes, ret);
```

## Placement Rules

| Goal | Correct location | Avoid |
| --- | --- | --- |
| Read/readahead window | After the code chooses and submits the actual window | Generic page-fault/function entry |
| Allocation outcome | After allocation returns with size and result known | Before allocation or before reclaim fallback completes |
| DMA/IOMMU map granule | Immediately after the map size is selected | Before alignment/contiguity checks |
| Device submission | After descriptors are accepted/queued | Userspace ioctl entry alone |
| Reclaim work | At the confirmed reclaim path with amount/result | Generic allocation failure site |

## Field Selection

Use `dev_t + ino` for file identity, not a pathname. Recover paths in user space if needed. Use page offsets or byte offsets consistently. For memory mappings, include IOVA, physical address only in privileged debug traces, size, selected page granule, protection flags, and a stable buffer/context ID.

## Tracefs Validation

```bash
TRACE=/sys/kernel/tracing
adb shell "grep -w '<system>:<event>' $TRACE/available_events"
adb shell "cat $TRACE/events/<system>/<event>/format"
adb shell "echo 0 > $TRACE/tracing_on; echo > $TRACE/trace"
adb shell "echo 1 > $TRACE/events/<system>/<event>/enable"
adb shell "echo 1 > $TRACE/tracing_on"
# trigger workload
adb shell "echo 0 > $TRACE/tracing_on; cat $TRACE/trace"
adb shell "echo 0 > $TRACE/events/<system>/<event>/enable"
```

For high event rates use `trace_pipe` for streaming and filters such as:

```bash
adb shell "echo 'common_pid == <pid>' > $TRACE/events/<system>/<event>/filter"
```

Clear filters after the run:

```bash
adb shell "echo 0 > $TRACE/events/<system>/<event>/filter"
```

## Android Kernel Build and Deployment

Use the repository's existing build and flash process. Before flashing, confirm the changed object is included in the target image/module, preserve active-slot backups, and verify the booted device exposes the event under tracefs. Do not claim an event works because the source compiles; require a real trace record from the target workload.
