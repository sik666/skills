---
name: output-clickable-text-file-references
description: Format local text-file citations so the client can open the exact file and line, using either chat-style `@path:line[:column]` references or Markdown absolute-path links when required. Use when Codex needs to cite source files, configs, or logs in responses and the formatting itself determines whether the reference is clickable in the target UI.
---

# Output Clickable Text File References

Choose the reference style based on the client, then keep the format exact.

## Workflow

1. Determine whether the target environment expects chat-style references or Markdown links.
2. If the client supports chat references, output `` `@relative/path:line[:column]` ``.
   Put each chat-style reference in its own standalone paragraph/line. Do not
   place two or more backtick-wrapped `@...` references on one physical line;
   this client may only make the final one clickable.
3. If the client requires Markdown links or the user explicitly wants absolute paths, output `[label](/absolute/path#L123)`.
4. Emit one reference per cited location.

## Styles

- Chat-style: `` `@drivers/of/platform.c:174` ``
- Markdown-style: `[drivers/of/platform.c](/abs/path/drivers/of/platform.c#L174)`

## Resources

- Read `references/format-guide.md` for examples and edge cases.

## Guardrails

- Do not output plain unlinked file paths when the user asked for clickable references.
- Do not mix styles in one answer unless the user explicitly asks for both.
- When emitting multiple chat-style references, separate them with blank lines;
  never join them with spaces, punctuation, or Markdown hard line breaks.
