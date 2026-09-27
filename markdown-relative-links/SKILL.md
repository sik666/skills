---
name: markdown-relative-links
description: Generate clickable local file references for Markdown documents using paths relative to the current Markdown file and #L line anchors. Use when Codex needs to write repository notes, code-tracing documents, review records, or design docs that must contain Markdown links like [label](relative/path#L123) instead of chat-style `@path:line` references.
---

# Markdown Relative Links

Generate links relative to the Markdown file being edited, not relative to the workspace root.

## Workflow

1. Identify the path of the Markdown file being created or edited.
2. Identify the target file path and target line number.
3. Compute the relative path from the Markdown file's directory to the target file.
4. Emit a Markdown link in the form `[label](relative/path#L123)`.
5. Keep the label short. Prefer `filename:line` unless a longer label improves clarity.

## Rules

- Always use `#L<line>` anchors.
- Never assume the workspace root is the base path unless the Markdown file is at the root.
- Use one link per location when citing multiple files.
- Use this skill only for Markdown output. If the environment expects chat-style references such as `@path:line`, use the relevant reference-format skill instead.

## Example

If the Markdown file is `docs/trace/uart.md` and the target file is `drivers/tty/serial/8250/8250_dw.c` line `540`, write:

```md
[8250_dw.c:540](../../drivers/tty/serial/8250/8250_dw.c#L540)
```
