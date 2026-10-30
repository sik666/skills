---
name: manage-cpp-clangd
description: Generate, merge, validate, diagnose, and repair compile_commands.json, then configure clangd and VS Code for C/C++ projects. Use for CMake, Meson, Make, Kbuild/Android kernel, cross-compiled, container-built, or multi-component workspaces when completion, diagnostics, includes, or definition jumps are missing, stale, or resolve into the wrong source tree.
---

# Manage C/C++ Clangd

Make clangd reproduce the real build environment. Treat the compilation
database, path identity, toolchain visibility, and editor session as separate
layers and prove each layer before changing the next one.

## Workflow

1. Capture the current state before editing: workspace path and `realpath`,
   clangd version, build systems, existing databases, generated output trees,
   workspace/user configs, and a representative file that was actually built.
2. Generate a database from native build metadata whenever possible. Read
   [references/generation.md](references/generation.md) for generator choice,
   container path handling, and multi-component merging.
3. Inspect the database structurally and verify its paths. Use
   `scripts/compile_db.py inspect` before assuming clangd is at fault.
4. Configure the workspace without discarding unrelated editor settings. Read
   [references/configuration.md](references/configuration.md) for VS Code,
   `.clangd`, cross-toolchain, and mixed host/target examples.
5. Run `clangd --check` on at least one real database entry from every distinct
   component or target. A JSON-valid database alone is not acceptance.
6. If behavior remains wrong, capture evidence with
   `scripts/clangd_snapshot.sh` and follow
   [references/diagnostics.md](references/diagnostics.md).
7. For Linux Kbuild or Android kernel output layouts, additionally read
   [references/kernel-android.md](references/kernel-android.md).

## Acceptance

Do not report success until the relevant claims are demonstrated:

- the intended database is loaded, not merely present;
- `directory` and `file` paths resolve in the environment running clangd;
- compiler include paths, generated headers, and target architecture are
  visible;
- representative files build a preamble and AST with `clangd --check`;
- VS Code opens definitions in the intended real source tree.

Report coverage honestly. A workspace may contain repositories or Buildroot
packages that were not compiled or did not retain recoverable command metadata.

## Guardrails

- Prefer native generators and recorded commands over invented flags.
- Do not trigger a costly full rebuild merely to capture commands when existing
  CMake/Meson databases, Kbuild `.cmd` files, Ninja metadata, or a safe dry run
  can provide them.
- Rewrite large JSON databases deterministically; never use blind ad-hoc text
  replacement without a backup or separate output.
- Preserve multiple commands for one source when they represent distinct
  targets or configurations. Deduplicate exact invocations, not filenames.
- Scope target flags in `.clangd`; a combined database may contain both native
  host tools and cross-compiled firmware.
- Fix configuration and path identity before moving caches or restarting
  processes. Cache removal is not a diagnosis.
- clangd is a C-family language server. A compilation database can record
  assembly commands, but `.S`/`.s` files do not receive full C/C++ semantics.
