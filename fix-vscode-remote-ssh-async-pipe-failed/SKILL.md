---
name: fix-vscode-remote-ssh-async-pipe-failed
description: Diagnose and repair VS Code Remote SSH failures that report AsyncPipeFailed, missing Unix sockets, or inability to connect to the remote extension host for one user while other users still work. Use when Codex needs to inspect stale ~/.vscode-server processes, broken /tmp/code-* sockets, pid files, or selective cache removal on the remote host.
---

# Fix VS Code Remote SSH AsyncPipeFailed

Assume stale Remote SSH server state before assuming the remote machine or project is broken.

## Workflow

1. Inspect the affected user's `.vscode-server` processes and capture any `--socket-path=/tmp/code-*` arguments.
2. Verify whether those sockets still exist on disk.
3. Read the relevant Remote SSH logs for `AsyncPipeFailed`, missing socket, pty host, or SIGPIPE errors.
4. Kill only the stale VS Code server processes for the affected user.
5. Remove stale `pid.txt` or the specific cached server version only if a simple process cleanup is insufficient.
6. Avoid broad user-process kills unless the user explicitly accepts the risk.

## Resources

- Read `references/troubleshooting.md` for command sequences, expected symptoms, and escalation steps.

## Guardrails

- Scope cleanup to the failing user and the failing VS Code server version.
- Prefer process cleanup before deleting all `.vscode-server` state.
