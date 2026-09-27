---
name: next-ai-draw-io-mcp
description: Install, register, and verify the DayuanJiang/next-ai-draw-io MCP server for Codex, including environments where Codex is launched from the VS Code extension rather than a system-wide CLI. Use when Codex needs draw.io MCP support added or when draw.io MCP registration needs to be checked quickly.
---

# Next AI Draw.io MCP

Prefer Codex's MCP manager instead of editing config files by hand.

## Workflow

1. Register the server with:

```bash
codex mcp add drawio -- npx @next-ai-drawio/mcp-server@latest
```

2. Verify registration with:

```bash
codex mcp list
```

3. If `codex` is not available in the shell, check whether the VS Code extension provides the binary under `~/.vscode-server/extensions/openai.chatgpt-*/bin/linux-x86_64/codex`.
4. If needed, run Codex through that full path or switch to the VS Code-integrated Codex shell.

## Guardrails

- Do not assume `codex` is installed system-wide.
- Keep validation lightweight unless the user asks for a deeper runtime test.
- If the server is registered but tools are still missing in the current session, switch to the MCP injection troubleshooting skill.
