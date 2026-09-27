# Root cause model and fixes

## Scope

Use this reference when clangd appears to ignore the current workspace and instead loads compile commands or symbols from another copy of the project.

## Root cause model

This failure is usually one or more of these:

1. The editor opened the wrong file path.
2. The workspace root lacks local clangd configuration, so clangd falls back to discovery and inference.
3. Another sibling tree contains the same filenames and symbols, and clangd reuses stale index entries or inferred commands.
4. The project was opened through a symlink path while compile commands or logs use the real path.
5. Global or parent-directory config is valid for another tree but too broad for the current one.

## What to prove with logs

Find these lines in the latest clangd log:

- `Working directory: ...`
- `Loading config file at ...`
- `Loaded compilation database from ...`
- `ASTWorker building file ...`
- `command inferred from ...`

Interpretation:

- If `Loaded compilation database from .../all/compile_commands.json` appears, clangd did read the correct database for at least one file.
- If another line shows `ASTWorker building file .../lab3/...` then VS Code still has a file from the old tree open, or clangd still received requests for that file.
- If `command inferred from .../lab3/...` appears for a file in `all/...`, the active session is polluted by a sibling tree.

## Fix options

### Option 1: Add project-local `.vscode/settings.json`

Use this when the workspace itself is the project you want indexed.

Recommended core setting:

```json
{
  "clangd.enable": true,
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=${workspaceFolder}",
    "--header-insertion=never",
    "--completion-style=detailed"
  ],
  "C_Cpp.intelliSenseEngine": "disabled"
}
```

Why:

- It forces the compile database to come from the actual opened workspace, not a parent tree.

### Option 2: Add project-local `.clangd`

Use this when the project is a kernel tree or any tree whose compile commands need flag cleanup.

Recommended core setting:

```yaml
CompileFlags:
  CompilationDatabase: .
```

Why:

- It forces clangd to resolve the compilation database relative to the project.
- It also gives a place to remove unsupported flags and add missing target/include settings.

### Option 3: Reopen the real path

Use this when the editor path is a symlink alias such as `/home/...` but the real files live under `/mnt/...`.

Why:

- clangd keys many artifacts by path identity. Mixed path prefixes can break jump targets even when parsing succeeds.

### Option 4: Close sibling-tree editors

Use this when logs show both `all/...` and `lab3/...` or other copied trees in one clangd session.

Why:

- clangd is allowed to index every open file it receives from the client.
- If symbols and filenames are duplicated across lab copies, jump results can be contaminated.

### Option 5: Clear clangd caches and restart

Use this only after Options 1 and 2 are already applied.

Targets:

- `~/.cache/clangd`
- per-project `.cache/clangd` if present
- current clangd processes

Why:

- This removes stale background index state that still refers to the old tree.

### Option 6: Rewrite or patch every standalone lab commit

Use this when each historical lab checkout must work as an independent workspace.

Why:

- If only the current commit has `.vscode/settings.json` and `.clangd`, older lab checkouts will regress.
- In Git-history-based lab projects, add the local clangd files to every historical lab commit that users are expected to check out directly.

## Preferred decision order

1. Fix the workspace-local config.
2. Fix the opened path.
3. Close wrong-tree editors.
4. Clear caches and restart.
5. Patch historical commits if the project is intentionally navigated commit-by-commit.

## Case study: duplicated lab tree

Pattern:

- Workspace `all/` was built by copying content from `lab0/`, `lab1/`, `lab3/`, and others.
- Symbols such as `imx415_probe` exist with identical names in multiple trees.
- clangd initially inferred commands from `lab3/...` and later loaded `all/compile_commands.json`.
- Jump results still pointed into `lab3/...` because old files were opened or indexed in the same session.

Working fix:

1. Add `all/.vscode/settings.json`.
2. Add `all/.clangd`.
3. Clear `~/.cache/clangd`.
4. Restart clangd.
5. Close all old `lab*` editors and reopen only files from `all/`.
6. If old lab commits must also work standalone, inject the two config files into each historical commit.
