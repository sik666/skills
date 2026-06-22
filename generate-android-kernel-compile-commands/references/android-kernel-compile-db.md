# Android Kernel compile_commands.json Guide

## What Works Best

Android kernel trees usually already contain:

```text
scripts/clang-tools/gen_compile_commands.py
```

Use this script instead of parsing `.cmd` files manually. It knows the Kbuild `.cmd` format:

```text
cmd_<object>.o := <compiler flags> <source>.c
```

## Locate Inputs

Find the kernel script:

```bash
rg --files <kernel-root> | rg 'scripts/clang-tools/gen_compile_commands.py$'
```

Find `.cmd` files:

```bash
find <out-root> -name '*.cmd' | head
find <out-root> -name '*.cmd' | wc -l
```

Find kernel object directories:

```bash
find <out-root>/target/product -maxdepth 5 -type d | rg '/obj/(KERNEL_OBJ|.*modules)'
```

Useful object paths commonly look like:

```text
out/target/product/<device>/obj/KERNEL_OBJ
out/target/product/<device>/obj/sm8650-modules
```

## Generate

Use `KERNEL_OBJ` as `-d`:

```bash
python3 <kernel-root>/scripts/clang-tools/gen_compile_commands.py \
  -d <out>/target/product/<device>/obj/KERNEL_OBJ \
  -o <kernel-root>/compile_commands.json \
  <out>/target/product/<device>/obj/KERNEL_OBJ \
  <out>/target/product/<device>/obj/sm8650-modules
```

Why `-d KERNEL_OBJ` matters:

- `./include/generated` resolves under the object tree.
- `./arch/arm64/include/generated` resolves under the object tree.
- The `directory` field in the database matches where generated headers exist.

## Path Mismatches

`.cmd` files may record the real path while the user opens a symlink path:

```text
/home/xuke/LinegaOS
/mnt/data_0/xuke/from_xuke_home_data/LinegaOS
```

Check with:

```bash
readlink -f /home/xuke/LinegaOS
readlink -f /mnt/data_0/xuke/from_xuke_home_data/LinegaOS
```

If both resolve to the same directory, clangd can usually still match files by realpath. If they differ, regenerate from the current tree or rewrite path prefixes.

## Validate

Check JSON and entry count:

```bash
python3 -m json.tool <kernel-root>/compile_commands.json >/dev/null
python3 - <<'PY'
import json, sys
data=json.load(open(sys.argv[1]))
print(len(data))
print(data[0]["directory"])
print(data[0]["file"])
PY <kernel-root>/compile_commands.json
```

Check clangd:

```bash
clangd --check=<kernel-root>/init/main.c --compile-commands-dir=<kernel-root>
```

Expected milestone:

```text
Loaded compilation database from <kernel-root>/compile_commands.json
All checks completed, 0 errors
```

## Common Surprises

- A valid database can omit files that were not built by the current `.config`.
- If a file has no database entry, clangd may infer a command from a nearby source file.
- Inferred commands can still produce false errors for config-specific files.
- External module sources need their module object directory included during generation.
- VS Code may need workspace settings even after command-line `clangd --check` works.
