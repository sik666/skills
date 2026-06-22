---
name: generate-android-kernel-compile-commands
description: Generate compile_commands.json for Android Linux kernel trees from an existing Android build out directory and Kbuild .cmd files. Use when Codex needs to make clangd work for kernel sources such as kernel/*/sm8650, locate KERNEL_OBJ or *-modules object directories under out/target/product/*/obj, use scripts/clang-tools/gen_compile_commands.py, handle symlinked /home versus /mnt paths, include external module trees, or validate the generated database with clangd --check.
---

# Generate Android Kernel Compile Commands

## Workflow

1. Confirm the kernel source root and the Android `out` root.
2. Prefer the kernel tree's own `scripts/clang-tools/gen_compile_commands.py`.
3. Locate the real kernel object directory, usually `out/target/product/<device>/obj/KERNEL_OBJ`.
4. Include external module object directories such as `out/target/product/<device>/obj/sm8650-modules` when the user wants vendor modules indexed too.
5. Generate `compile_commands.json` into the source tree that VS Code opens.
6. Validate with `python3 -m json.tool`, entry counts, and `clangd --check=<compiled-file>`.

## Fast Path

Run the bundled helper when the workspace resembles an Android tree:

```bash
python3 /home/xuke/.codex/skills/generate-android-kernel-compile-commands/scripts/generate_android_kernel_compile_commands.py \
  --kernel-root /path/to/android/kernel/vendor/device \
  --out-root /path/to/android/out \
  --include-modules \
  --check-file /path/to/android/kernel/vendor/device/init/main.c
```

Use `--dry-run` first when the tree has multiple devices or multiple `KERNEL_OBJ` candidates.

## Manual Fallback

If the helper cannot infer the paths, run:

```bash
python3 <kernel-root>/scripts/clang-tools/gen_compile_commands.py \
  -d <out>/target/product/<device>/obj/KERNEL_OBJ \
  -o <kernel-root>/compile_commands.json \
  <out>/target/product/<device>/obj/KERNEL_OBJ \
  <out>/target/product/<device>/obj/<module-obj-dir>
```

Set `-d` to the object directory, not the source directory. Kernel compile commands often contain relative generated include paths like `./include/generated`; those must resolve under `KERNEL_OBJ`.

## Validation Rules

- Confirm `compile_commands.json` exists where clangd will look.
- Confirm representative built source files report `Loaded compilation database`.
- Confirm module source files are included if module directories were requested.
- Treat files with no `.cmd` as uncovered by the current build config; clangd may infer a command from a neighbor and still show false diagnostics.

## References

- Read `references/android-kernel-compile-db.md` for object-directory discovery, path mismatch handling, and troubleshooting patterns.
