# Kernel clangd Troubleshooting

## Log Lines That Matter

Search clangd logs for:

```text
Working directory:
Loading config file at
Loaded compilation database from
Failed to find compilation database
ASTWorker building file
command clangd fallback
command inferred from
```

Interpretation:

- `Loaded compilation database from <expected>` means clangd found the database.
- `command clangd fallback` means it did not use kernel flags; expect missing `linux/*.h`, `bool`, `CONFIG_*`, and generated-header errors.
- `command inferred from <other-file>` means the current file lacks its own database entry.
- `ASTWorker building file <wrong-tree>` means the editor still has a stale or sibling-tree file open.

## Common Causes And Fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `compile_commands.json` exists but clangd fallback is used | VS Code opened a parent workspace and no `--compile-commands-dir` is set | Add `.vscode/settings.json` with `--compile-commands-dir=<kernel-root>` |
| Plain `clangd --check` ignores local database | Unconditional `~/.config/clangd/config.yaml` `CompilationDatabase` points elsewhere | Restrict it with `If: PathMatch` |
| Project `.clangd` is read but database does not change | Project config is untrusted for this option in the active clangd | Put scoped `CompilationDatabase` in user config or pass CLI arg |
| Module source cannot find database | Database is in sibling kernel tree, not an ancestor of module file | Use `--compile-commands-dir`, scoped user config, or include module entries during generation |
| Jump-to-definition opens sibling copy | Duplicate trees and stale background index | Close wrong-tree editors, scope config, move `~/.cache/clangd`, restart clangd |
| Paths differ between `/home/...` and `/mnt/...` | Workspace is symlinked | Prefer opening the real path or ensure compile db and editor paths resolve to same realpath |
| `clangd --check` works but VS Code does not | Extension session is stale or cpptools competes | Reload VS Code, kill clangd/cpptools, disable `C_Cpp.intelliSenseEngine` |
| One file still has errors but built files are fine | File not built by current `.config`; no `.cmd` entry | Verify Makefile and `.config`; treat inferred-command errors as false positives unless that file should be built |

## Commands

Find configs:

```bash
find <workspace> -path '*/.vscode/settings.json' -o -name '.clangd' -o -name 'compile_commands.json'
sed -n '1,120p' ~/.config/clangd/config.yaml 2>/dev/null
```

Check real path:

```bash
pwd
realpath .
readlink -f <workspace>
```

Validate compile database:

```bash
clangd --check=<kernel-root>/init/main.c --compile-commands-dir=<kernel-root>
clangd --check=<kernel-root>/init/main.c
```

Clear state:

```bash
mv ~/.cache/clangd ~/.cache/clangd.bak_$(date +%Y%m%d_%H%M%S)
pkill -u "$USER" -x clangd
pkill -u "$USER" -f '/ms-vscode\.cpptools-.*/bin/cpptools'
```

## Known Android Kernel Pattern

For a LinegaOS-style tree:

```yaml
If:
  PathMatch: ".*/LinegaOS/kernel/oneplus/sm8650(-modules)?/.*"
CompileFlags:
  CompilationDatabase: "/home/xuke/LinegaOS/kernel/oneplus/sm8650"
```

And VS Code workspace settings:

```json
{
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=${workspaceFolder}/kernel/oneplus/sm8650",
    "--header-insertion=never",
    "--completion-style=detailed"
  ],
  "C_Cpp.intelliSenseEngine": "disabled"
}
```

## Validation Milestones

A fixed representative file should show:

```text
Loaded compilation database from .../compile_commands.json
Compile command from CDB is: ...
All checks completed, 0 errors
```

For a file not in the database, this is still progress:

```text
Loaded compilation database from ...
Compile command inferred from ...
```

Do not overfit fixes to inferred-command diagnostics until a compiled file has been validated.
