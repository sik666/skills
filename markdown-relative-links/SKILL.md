---
name: markdown-relative-links
description: Generate IDE-clickable links inside Markdown files using a path relative to the document and a `#L` line anchor. Not for chat replies.
---

# Markdown Relative Links

Use this skill only when writing or editing an on-disk Markdown document. Do
not use it for links emitted in a chat reply.

## Format

```md
[rk3588s-lubancat-4.dts:1331](../../../kernel-6.1/arch/arm64/boot/dts/rockchip/suit/rk3588s-lubancat-4.dts#L1331)
```

## Rules

- Use a path relative to the directory containing the Markdown file, followed
  by `#L<LINE>`.
- Verify that the target file exists and the cited line is in range.
- Use a separate link for each location. A single link targets one line, not a
  range.
- Keep each visible label concise and identify the file and line, for example
  `filename.c:42`.
- Do not use absolute `:LINE` targets, `file://`, or `vscode://` inside an
  on-disk Markdown document.
- Do not wrap the link itself in backticks.
