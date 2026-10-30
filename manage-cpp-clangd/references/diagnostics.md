# Diagnosing clangd and Compilation Database Failures

## Capture Evidence

Run the read-only snapshot before changing state:

```bash
scripts/clangd_snapshot.sh /path/to/workspace /path/to/built-source.c
```

Also inspect database structure:

```bash
python3 scripts/compile_db.py inspect \
  /path/to/compile_commands.json \
  --workspace /path/to/workspace
```

## Command-Line Reproduction

Choose a source file that has its own database entry:

```bash
clangd --check=/absolute/path/source.c \
  --compile-commands-dir=/absolute/path/db-directory \
  --log=verbose
```

For cross GCC, add the same trusted query-driver pattern used by VS Code.

Important milestones are:

- `Loaded compilation database from ...`;
- `Compile command from CDB is: ...`;
- preamble and AST build successfully;
- `All checks completed` without driver or missing-header errors.

## Log Interpretation

Search VS Code clangd logs for:

```text
Working directory:
Loading config file at
Loaded compilation database from
Failed to find compilation database
Compile command from CDB
command clangd fallback
command inferred from
ASTWorker building file
```

| Symptom | Evidence-based interpretation | Next action |
| --- | --- | --- |
| `command clangd fallback` | no usable entry/database was found | prove database location and file membership |
| `command inferred from` | file has no direct entry | test a built file; regenerate with its target/module if it should be built |
| failed to set CWD | `directory` is stale or container-only | map/regenerate paths and validate directories |
| builtin header missing | target/compiler discovery failed | configure trusted query driver or correct toolchain include/sysroot |
| project generated header missing | build output or working directory is wrong | locate the actual object/build directory |
| unknown GCC flag | clangd cannot parse a recorded driver option | remove the demonstrated flag in scoped `.clangd` config |
| wrong sibling tree in `ASTWorker` | editor or stale index is using another copy | close wrong files, fix local config/path identity, then restart |
| `clangd --check` passes, VS Code fails | language server core is working | fix extension session, workspace root, or competing cpptools |
| `foo.c#L55` treated as a filename | client/path URI problem | reopen the canonical workspace path and inspect the active editor URI |

## Wrong Database or Duplicate Trees

Prove all three independently:

1. which source URI VS Code sent;
2. which database clangd loaded;
3. which compile command clangd selected.

Add workspace-local settings before touching global config. Check
`${XDG_CONFIG_HOME:-$HOME/.config}/clangd/config.yaml` for an unconditional
`CompilationDatabase` that points at another project. Scope global rules with
`If: PathMatch` when they are genuinely needed.

Close editors from sibling copies. A language server may legitimately index
every open document even when the current workspace database is correct.

## Cache Reset Is Last

Only after configuration and paths are correct, move caches aside recoverably
and restart clangd:

```bash
mv ~/.cache/clangd ~/.cache/clangd.bak_$(date +%Y%m%d_%H%M%S)
pkill -u "$USER" -x clangd
```

Do not run these commands automatically for a read-only diagnosis. Killing the
language server interrupts active editor sessions.

## Permissions and Ownership

If behavior differs by user, check:

```bash
whoami
stat -c '%A %a %U:%G %n' /path/to/workspace /path/to/compile_commands.json
git -C /path/to/workspace status
```

Treat Git `dubious ownership`, unreadable build outputs, and workspace path
aliases as environment problems. Do not reinstall extensions until binary,
permissions, and path evidence justify it.
