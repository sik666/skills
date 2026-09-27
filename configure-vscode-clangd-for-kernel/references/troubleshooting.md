# VS Code Clangd for Kernel Troubleshooting

## Scope

This reference captures a real Linux kernel workspace failure in VS Code where:

- `compile_commands.json` existed
- `clangd` was installed
- parsing and indexing could be made to work
- `Ctrl+Click` jump-to-definition opened a fake file name such as `imx415.c#L55`
- reopening the workspace via the real path fixed navigation

Use this file when the user reports any combination of:

- clangd not working in a kernel tree
- jump-to-definition opening nonexistent files
- a workspace opened through `/home/...` but backed by a symlink to `/mnt/...`
- `compile_commands.json` containing GCC-only kernel flags

## Fast triage

Run these first:

```bash
pwd
realpath .
command -v clangd
clangd --version
python3 - <<'PY'
import json
with open('compile_commands.json') as f:
    data = json.load(f)
for item in data:
    if item.get('file', '').endswith('/drivers/media/i2c/imx415.c'):
        print(item['file'])
        print(item['directory'])
        break
PY
```

If the workspace was opened via a symlinked path, also inspect:

```bash
stat -c '%N' /home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113
```

## Known failure pattern: fake `file#Lline` document

One concrete bad symptom is that clangd or the client starts treating:

```text
/home/haodong/data/.../drivers/media/i2c/imx415.c#L55
```

as the file path itself.

This is visible in clangd logs. A representative line looked like:

```text
ASTWorker building file /home/haodong/data/.../imx415.c#L55 version 1 with command inferred from /home/haodong/data/.../imx415.c
```

That means the client/editor session is trying to parse a synthetic document name ending in `#L55`, not a normal source file path. When VS Code then opens that target, it reports that the file does not exist.

In the observed case, simply reopening the workspace through the real path fixed this.

## Real-path fix

If the visible workspace path is a symlinked entry such as:

```text
/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel
```

and it resolves to:

```text
/mnt/data_0/xuke/from_haodong_data/LubanCat_Linux_rk3588_SDK_20260113/kernel
```

then prefer opening the real path in VS Code:

```text
/mnt/data_0/xuke/from_haodong_data/LubanCat_Linux_rk3588_SDK_20260113/kernel
```

This can fix navigation even when parsing already works.

## Recommended `.vscode/settings.json`

Pin a known clangd binary and basic arguments:

```json
{
  "clangd.enable": true,
  "clangd.path": "/home/haodong/data/kernel/prebuilts/clang/host/linux-x86/clang-r450784e/bin/clangd",
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=${workspaceFolder}",
    "--header-insertion=never",
    "--completion-style=detailed"
  ],
  "C_Cpp.intelliSenseEngine": "disabled"
}
```

Notes:

- Prefer a project-provided clangd over `/usr/bin/clangd` when the system version is old or less compatible.
- Disable the Microsoft C/C++ IntelliSense engine to avoid overlap with clangd.

## Recommended `.clangd`

Use `.clangd` to keep the compile database intact while removing flags that clangd rejects:

```yaml
CompileFlags:
  Add:
    - --target=aarch64-linux-gnu
    - -isystem
    - /mnt/data_0/xuke/from_haodong_data/LubanCat_Linux_rk3588_SDK_20260113/prebuilts/gcc/linux-x86/aarch64/gcc-arm-10.3-2021.07-x86_64-aarch64-none-linux-gnu/lib/gcc/aarch64-none-linux-gnu/10.3.1/include
  Remove:
    - -isystem
    - -fno-allow-store-data-races
    - -fconserve-stack
    - -mabi=lp64
    - -mstack-protector-guard=sysreg
    - -mstack-protector-guard-reg=sp_el0
    - -mstack-protector-guard-offset=1336
    - /work/prebuilts/gcc/linux-x86/aarch64/gcc-arm-10.3-2021.07-x86_64-aarch64-none-linux-gnu/bin/../lib/gcc/aarch64-none-linux-gnu/10.3.1/include
```

Why this helps:

- Linux kernel compile databases often contain GCC-only flags that clangd cannot parse.
- Some generated databases refer to toolchain include directories under `/work/...` that do not exist locally.
- Adding the real builtin include directory and stripping the invalid flags lets clangd build a preamble and AST.

## Typical command-line reproduction

Use this to separate clangd-core failures from VS Code UI failures:

```bash
clangd --check=drivers/of/platform.c --compile-commands-dir=. --log=verbose
```

Before normalization, a kernel compile command may fail with messages such as:

- `unknown argument: '-fno-allow-store-data-races'`
- `unknown argument: '-fconserve-stack'`
- `invalid value 'sysreg' in 'mstack-protector-guard='`
- `unknown target ABI 'lp64'`
- `'stdarg.h' file not found`

After `.clangd` normalization, the important milestone is:

- clangd can build the preamble
- clangd can build the AST
- definition and hover work in `--check`

If `--check` works but VS Code navigation still opens fake files, focus on workspace path handling rather than compile flags.

## Decision rule

Use this order:

1. Verify real path versus symlink path.
2. Verify the active clangd binary and version.
3. Verify `.vscode/settings.json`.
4. Verify `.clangd`.
5. Verify `clangd --check`.
6. Reopen the real path in VS Code.

If step 5 succeeds but step 6 is still broken, suspect a client-side URI/path issue rather than a parser failure.
