---
name: fix-kernel-clangd-issues
description: Diagnose and fix clangd failures in Linux or Android kernel workspaces, especially when compile_commands.json exists but VS Code or clangd still falls back, loads the wrong database, uses a stale global CompilationDatabase, mixes symlink and real paths, misses generated headers, fights cpptools, opens sibling-tree definitions, or reports errors for files not built by the current kernel .config.
---

# Fix Kernel Clangd Issues

## Workflow

1. Capture state before changing files.
2. Prove whether clangd loads the intended `compile_commands.json`.
3. Compare the editor workspace path with `realpath`.
4. Inspect user-level clangd config, workspace `.vscode/settings.json`, project `.clangd`, and clangd logs.
5. Fix workspace-local settings first, then user-level config if a trusted global rule is polluting every project.
6. Clear clangd background index only after configuration is correct.
7. Validate with `clangd --check` on a file that has a real compile database entry.

## Fast State Capture

Run:

```bash
/home/xuke/.codex/skills/fix-kernel-clangd-issues/scripts/kernel_clangd_snapshot.sh \
  /path/to/workspace \
  /path/to/source.c
```

Use the output to find `Loaded compilation database`, `Failed to find compilation database`, `command clangd fallback`, and which config files were loaded.

## Decision Rules

- If command-line `clangd --check=<file> --compile-commands-dir=<db-dir>` works but VS Code does not, fix VS Code workspace settings and restart clangd.
- If plain `clangd --check=<file>` fails while a compile database exists, inspect `~/.config/clangd/config.yaml` for an unconditional `CompilationDatabase`.
- If a project `.clangd` is read but cannot override `CompilationDatabase`, remember that project config may be untrusted; use a scoped trusted user config.
- If files from `sm8650-modules` need the database in sibling `sm8650`, add a scoped user config or VS Code `--compile-commands-dir`.
- If a source file is not in the current compile database, treat residual diagnostics as possible build-config false positives.

## Preferred Fixes

Add workspace settings:

```json
{
  "clangd.enable": true,
  "clangd.path": "/path/to/android/clangd",
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=${workspaceFolder}/kernel/oneplus/sm8650",
    "--header-insertion=never",
    "--completion-style=detailed"
  ],
  "C_Cpp.intelliSenseEngine": "disabled"
}
```

Scope user config instead of using an unconditional compile database:

```yaml
If:
  PathMatch: ".*/LinegaOS/kernel/oneplus/sm8650(-modules)?/.*"
CompileFlags:
  CompilationDatabase: "/home/xuke/LinegaOS/kernel/oneplus/sm8650"
```

Then move `~/.cache/clangd` aside and restart clangd.

## References

- Read `references/kernel-clangd-troubleshooting.md` for symptom-to-cause mapping, log interpretation, and fixes for stale indexes, symlink paths, global config pollution, and uncovered source files.
