---
name: fix-plugin-issues-from-file-permissions
description: Diagnose plugin or editor failures that are really caused by file ownership, symlink path mismatches, Git safe.directory restrictions, or stale compile_commands paths. Use when Codex needs to explain why Git, clangd, or VS Code tooling behaves differently across users or paths even though the software itself is installed.
---

# Fix Plugin Issues from File Permissions

Assume the environment is lying before assuming the plugin is broken.

## Workflow

1. Identify the current user, the visible workspace path, and the real filesystem path.
2. Check repository ownership and whether Git reports `dubious ownership`.
3. Check whether the current path and the paths embedded in `compile_commands.json` still match.
4. Verify the language-server binary exists before debugging extension UI messages.
5. Prefer correcting ownership trust, path mappings, and workspace settings before reinstalling tools.

## Resources

- Read `references/troubleshooting.md` for concrete commands covering Git safety, symlink mismatches, clangd path issues, and workspace configuration.

## Guardrails

- A missing or inactive plugin UI often reflects an underlying path or permission problem.
- When symlinks are involved, inspect both the displayed path and the canonical path.
