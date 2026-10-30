# Configuring clangd and VS Code

## Establish Path Identity

Compare the visible and canonical roots:

```bash
pwd
realpath .
```

The editor URI, database paths, clangd working directory, and generated paths
should describe the same tree. Prefer opening the canonical path when symlink
aliases cause definition jumps to fake or sibling files.

## VS Code Workspace Settings

Preserve existing keys in `.vscode/settings.json` and add only the required
clangd settings:

```json
{
  "clangd.enable": true,
  "clangd.path": "/usr/bin/clangd",
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=${workspaceFolder}",
    "--header-insertion=never",
    "--completion-style=detailed"
  ],
  "C_Cpp.intelliSenseEngine": "disabled"
}
```

Adjust `clangd.path` to a compatible project-provided binary when available.
If the database lives below the workspace root, point
`--compile-commands-dir` at its directory.

For GCC cross toolchains, clangd can query builtin includes and target details:

```json
"--query-driver=${workspaceFolder}/toolchains/aarch64/bin/aarch64-linux-gnu-*"
```

Only trust compiler patterns belonging to the project or an expected system
toolchain. `--query-driver` permits executing matching compiler drivers.

## Project `.clangd`

Use `.clangd` for compilation-command normalization, not editor UI settings:

```yaml
CompileFlags:
  CompilationDatabase: .
```

Remove only flags demonstrated to be incompatible by `clangd --check`:

```yaml
CompileFlags:
  Remove:
    - -fconserve-stack
    - -fno-allow-store-data-races
    - -mstack-protector-guard=*
```

For cross compilation, add a target only to the relevant paths:

```yaml
If:
  PathMatch: ^(linux|u-boot|trusted-firmware-a)/.*
CompileFlags:
  Add:
    - --target=aarch64-linux-gnu
```

Do not add a global AArch64 target to a combined database that also compiles
x86-64 host utilities. Use multiple YAML fragments separated by `---`.

Do not broadly remove `-isystem`, `--sysroot`, forced includes, or generated
include paths. Replace a stale path with the correct path when possible.

## Generated Headers and Compiler Builtins

If a header is missing, classify it before editing flags:

- project source header: database include path is wrong;
- generated header: build/configuration stage did not run or `directory` is
  wrong;
- compiler builtin such as `stdarg.h`: query driver, target, resource dir, or
  toolchain include path is missing;
- container system header: host clangd cannot see the build environment.

Fix the corresponding layer. Adding unrelated global include directories often
hides the first error and creates conflicting definitions.

## Reloading

After settings are correct, use “clangd: Restart language server” or
“Developer: Reload Window.” Do not clear caches first. If command-line
`clangd --check` passes but VS Code fails, inspect extension logs and competing
language servers before changing the database again.
