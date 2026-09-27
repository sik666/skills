---
name: fix-clangd-wrong-compile-db
description: Diagnose and fix VS Code clangd sessions that load the wrong compile_commands.json, jump to definitions in a sibling copy of the project, or mix symbols across duplicated lab/branch trees. Use when a C/C++ or kernel workspace has multiple similar source trees, stale clangd index state, symlink versus realpath mismatches, or workspace-local settings that fail to force clangd onto the current project.
---

# Fix Clangd Wrong Compile Db

Use this skill when clangd behavior is wrong even though `compile_commands.json` exists.

Typical symptoms:

- go-to-definition opens a sibling project copy such as `lab3/...` while editing `all/...`
- clangd loads a compile database from an unexpected directory
- clangd parses the file but symbol jumps still land in the wrong tree
- a workspace copied from another lab or branch keeps resolving symbols against the old path

## Quick workflow

1. Confirm the real workspace path.
2. Confirm which source file VS Code actually sent to clangd.
3. Confirm which compile database clangd loaded for that file.
4. Fix workspace-local config before touching global config.
5. Clear stale background index state only after proving the config is correct.
6. Reopen only files from the intended tree and validate with logs.

## Step 1: Capture the active state

Run `scripts/clangd_state_snapshot.sh <workspace> [source-file]`.

Use it to collect:

- `pwd` and `realpath`
- active clangd processes and their working directories
- workspace-local `.vscode/settings.json`, `.clangd`, and `compile_commands.json`
- recent clangd logs with `Loaded compilation database` and `ASTWorker building file`

If the workspace path is a symlinked entry path, prefer the real path.

## Step 2: Apply the decision rule

Read `references/solutions.md` and follow this order:

1. If the opened file path is wrong, close the wrong editors first.
2. If the workspace lacks project-local `.vscode/settings.json`, add one.
3. If the workspace lacks project-local `.clangd`, add one.
4. If clangd still loads an older sibling compile database, clear caches and restart clangd.
5. If the project is a Git history lab tree, add the local clangd files to every lab commit that must work standalone.

Do not start with global plugin settings unless workspace-local configuration is already correct.

## Step 3: Preferred local fixes

Prefer these fixes in this order:

- Add `.vscode/settings.json` in the actual workspace root with `--compile-commands-dir=${workspaceFolder}`.
- Add `.clangd` in the actual workspace root with `CompilationDatabase: .`.
- Keep the active workspace opened through the real path, not a symlink alias.
- Close sibling-tree editors so clangd stops indexing them in the same session.
- Clear `~/.cache/clangd` and restart the language server only after the two local config files are in place.

For kernel trees, strip GCC-only flags in `.clangd` instead of rewriting the whole compile database.

## Step 4: Reset state when needed

Run `scripts/reset_clangd_state.sh`.

This script:

- moves `~/.cache/clangd` to a timestamped backup
- kills current clangd processes so VS Code respawns them

Use it only after confirming the intended workspace contains the right local config files.

## Step 5: Validate

Validation is complete only when all of the following are true:

- clangd log shows `Loaded compilation database` from the intended workspace
- clangd log shows `ASTWorker building file` for the intended file path
- symbol jumps from the active file land in the intended tree
- reopening the workspace does not regress the result

## References

- Read `references/solutions.md` for the root-cause model, all viable fixes, and the duplicated-lab-tree case.
