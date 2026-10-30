# Linux, U-Boot, and Android Kernel Databases

## Use Kbuild Metadata

Kernel-family builds record full invocations in `.cmd` files. Prefer the tree's
generator:

```bash
python3 <source>/scripts/clang-tools/gen_compile_commands.py \
  -d <object-directory> \
  -o <source>/compile_commands.json \
  <object-directory> [additional-module-object-directories...]
```

Set `-d` to the object directory, not automatically to the source directory.
Relative generated includes such as `./include/generated` must resolve from the
actual object tree.

For in-tree builds, source and object directory may be the same.

## Android Output Discovery

Common paths are:

```text
out/target/product/<device>/obj/KERNEL_OBJ
out/target/product/<device>/obj/<vendor>-modules
```

Discover rather than guess:

```bash
rg --files <kernel-root> | rg 'scripts/clang-tools/gen_compile_commands.py$'
find <out-root> -name '.*.cmd' | head
find <out-root>/target/product -maxdepth 5 -type d \
  | rg '/obj/(KERNEL_OBJ|.*modules)'
```

Use `scripts/generate_android_kernel_compile_commands.py --dry-run` when the
layout matches Android and multiple candidates need review.

## Coverage Follows `.config`

A valid database omits source files not built by the active configuration.
clangd may infer a nearby command for them and report false errors. Before
patching flags, determine whether the relevant `Makefile` condition and
`CONFIG_*` selected that file.

External module sources require their module object directories during
generation. Validate both an in-kernel file and a module file when module
coverage is requested.

## Common GCC-Only Flags

New kernels built by GCC may record flags an older clangd rejects, for example:

```text
-fconserve-stack
-fno-allow-store-data-races
-femit-struct-debug-baseonly
-mstack-protector-guard=sysreg
-mstack-protector-guard-reg=sp_el0
-mstack-protector-guard-offset=...
```

Use `clangd --check` to obtain the actual rejected set, then remove only those
flags in a path-scoped `.clangd` fragment. Add `--target=<triple>` and builtin
includes/query-driver configuration when the failure is target discovery, not
as a universal kernel template.
