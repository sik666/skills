#!/usr/bin/env python3
"""Generate compile_commands.json for Android kernel trees from Kbuild .cmd files."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def real(p: str) -> Path:
    return Path(p).expanduser().resolve()


def find_kernel_obj(out_root: Path) -> Path:
    candidates = sorted(out_root.glob("target/product/*/obj/KERNEL_OBJ"))
    if not candidates:
        candidates = sorted(out_root.rglob("KERNEL_OBJ"))
    dirs = [p for p in candidates if p.is_dir()]
    if not dirs:
        raise SystemExit(f"no KERNEL_OBJ directory found under {out_root}")
    if len(dirs) > 1:
        print("warning: multiple KERNEL_OBJ candidates; using first:", file=sys.stderr)
        for p in dirs:
            print(f"  {p}", file=sys.stderr)
    return dirs[0]


def find_module_dirs(out_root: Path) -> list[Path]:
    obj_roots = sorted(out_root.glob("target/product/*/obj"))
    dirs: list[Path] = []
    for obj in obj_roots:
        for p in sorted(obj.iterdir()):
            if p.is_dir() and "modules" in p.name and any(p.rglob(".*.o.cmd")):
                dirs.append(p)
    return dirs


def run(cmd: list[str], dry_run: bool) -> None:
    print("+ " + " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def validate(output: Path) -> int:
    with output.open() as f:
        data = json.load(f)
    print(f"entries: {len(data)}")
    if data:
        print(f"sample directory: {data[0].get('directory')}")
        print(f"sample file: {data[0].get('file')}")
    return len(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-root", default=".", help="Android kernel source root")
    parser.add_argument("--out-root", required=True, help="Android out directory")
    parser.add_argument("--kernel-obj", help="KERNEL_OBJ directory")
    parser.add_argument("--module-obj", action="append", default=[], help="extra module object directory")
    parser.add_argument("--include-modules", action="store_true", help="auto-include *modules object dirs")
    parser.add_argument("--output", help="compile_commands.json output path")
    parser.add_argument("--check-file", help="run clangd --check on this file after generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    kernel_root = real(args.kernel_root)
    out_root = real(args.out_root)
    gen_script = kernel_root / "scripts/clang-tools/gen_compile_commands.py"
    if not gen_script.exists():
        raise SystemExit(f"missing {gen_script}")

    kernel_obj = real(args.kernel_obj) if args.kernel_obj else find_kernel_obj(out_root)
    module_dirs = [real(p) for p in args.module_obj]
    if args.include_modules:
        module_dirs.extend(find_module_dirs(out_root))

    output = real(args.output) if args.output else kernel_root / "compile_commands.json"
    paths = [str(kernel_obj)] + [str(p) for p in dict.fromkeys(module_dirs)]
    cmd = ["python3", str(gen_script), "-d", str(kernel_obj), "-o", str(output)] + paths
    run(cmd, args.dry_run)

    if not args.dry_run:
        count = validate(output)
        if count == 0:
            raise SystemExit("generated database is empty")
        if args.check_file:
            run(["clangd", f"--check={real(args.check_file)}", f"--compile-commands-dir={output.parent}"], False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
