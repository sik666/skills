---
name: fix-codex-mcp-not-injected
description: Diagnose cases where a Codex MCP server appears enabled in the UI but its tools are missing from the current session. Use when Codex needs to troubleshoot MCP registration versus runtime availability, especially around missing npx/npm, broken /tmp/codex-ipc permissions, extension IPC failures, or sessions that need to be recreated after environment fixes.
---

# Fix Codex MCP Not Injected

Treat this as a three-layer problem: command runtime, Codex IPC bridge, and session lifecycle.

## Workflow

1. Confirm the MCP server is registered with `codex mcp list` and `codex mcp get <name>`.
2. Verify the server command itself can start outside Codex.
3. Inspect Codex IPC state, especially `/tmp/codex-ipc` ownership and socket creation.
4. Check extension logs for bridge failures such as `listen EACCES`.
5. If runtime and IPC are fixed after the session already started, recreate the Codex session instead of assuming hot injection will occur.

## Resources

- Read `references/troubleshooting.md` for the full command checklist and the draw.io-specific example.

## Guardrails

- An enabled toggle in the UI does not prove the MCP process started successfully.
- A repaired environment does not guarantee the current conversation gains tools without a new session.
