---
name: configure-vscode-clangd-for-kernel
description: Configure and troubleshoot clangd for Linux kernel trees in VS Code, especially when compile_commands.json exists but clangd still fails due to unsupported GCC flags, missing builtin include paths, outdated clangd binaries, symlinked workspace paths, or broken definition jumps that open fake files like source.c#L55. Use when Codex needs to add .vscode/settings.json and .clangd, inspect clangd logs, or explain why opening the real path fixes jump-to-definition.
---

# Configure VS Code Clangd for Kernel

Treat this as a workspace-path and compile-flags problem before treating it as a generic clangd crash.

## Workflow

1. Confirm which path VS Code opened and compare it with the real path from `realpath .`.
2. Confirm `compile_commands.json` exists and inspect whether its `file` and `directory` values point at the same path prefix VS Code is using.
3. Check the active clangd binary and prefer a project-provided clangd if the system clangd is older or less compatible.
4. Add or update `.vscode/settings.json` to pin the clangd binary, compile commands directory, and disable competing IntelliSense engines.
5. Add or update `.clangd` to remove GCC-only flags that clangd rejects and to add the target and builtin include directory the kernel tree needs.
6. Reproduce with `clangd --check=<file> --compile-commands-dir=.` before assuming the VS Code extension is at fault.
7. If jump-to-definition opens fake files such as `foo.c#L55`, reopen the workspace using the real path rather than a symlinked entry path.

## Configuration

Use `.vscode/settings.json` to pin the clangd executable and basic arguments.

Use `.clangd` to normalize compile flags without rewriting the whole `compile_commands.json`.

## Resources

- Read `references/troubleshooting.md` for concrete settings, command lines, log signatures, and the symlink-path failure case where opening the real path fixes jump-to-definition.

## Guardrails

- Do not assume a valid `compile_commands.json` is sufficient; kernel trees often contain GCC-specific flags clangd must ignore.
- Do not assume the path shown in the editor is the same path clangd indexes; symlinked workspace roots can break definition jumps even when parsing succeeds.
- Prefer reopening the real path before rewriting a large compile database when the only user-visible bug is broken navigation.
