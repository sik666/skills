---
name: fix-container-compile-commands-for-clangd
description: Repair compile_commands.json files generated inside containers so host-side clangd can index correctly by remapping container path prefixes to host paths. Use when Codex needs to diagnose clangd failures caused by /workspace-style paths, nonexistent build directories, or stale compile database prefixes, and when a reusable rewrite script is preferable to ad hoc editing.
---

# Fix Container Compile Commands for Clangd

Prefer rewriting the compile database deterministically instead of doing manual search-and-replace in a large JSON file.

## Workflow

1. Confirm `compile_commands.json` contains container-only paths such as `/workspace/...`.
2. Determine the host workspace root and any additional container-to-host prefix mappings.
3. Run `scripts/fix_compile_commands.py` with `--workspace` and optional `--map` arguments.
4. Recheck the rewritten `directory`, `file`, and include-path entries.
5. If clangd still fails, continue with toolchain or `.clangd` investigation instead of repeating path rewrites.

## Resources

- Run `scripts/fix_compile_commands.py` for actual rewrites.
- Read `references/guide.md` for examples, limits, and follow-up diagnostics.

## Guardrails

- This skill fixes path-prefix mismatches, not missing toolchains or incompatible clangd flags.
- Prefer `--in-place` only when a backup is acceptable; the script already writes a `.bak` file.
