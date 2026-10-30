#!/usr/bin/env python3
"""Generate compile_commands.json from an existing Android Kbuild output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def real(value: str) -> Path:
    return Path(value).expanduser().resolve()


def find_kernel_obj(out_root: Path) -> Path:
    candidates = sorted(
        path for path in out_root.glob("target/product/*/obj/KERNEL_OBJ") if path.is_dir()
    )
    if not candidates:
        candidates = sorted(path for path in out_root.rglob("KERNEL_OBJ") if path.is_dir())
    if not candidates:
        raise ValueError(f"no KERNEL_OBJ directory found under {out_root}")
    if len(candidates) > 1:
        choices = "\n".join(f"  {path}" for path in candidates)
        raise ValueError(
            "multiple KERNEL_OBJ directories found; select one with --kernel-obj:\n"
            + choices
        )
    return candidates[0]


def find_module_dirs(out_root: Path) -> list[Path]:
    modules: list[Path] = []
    for object_root in sorted(out_root.glob("target/product/*/obj")):
        for path in sorted(object_root.iterdir()):
            if path.is_dir() and "modules" in path.name and any(path.rglob(".*.cmd")):
                modules.append(path)
    return modules


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--kernel-obj")
    parser.add_argument("--module-obj", action="append", default=[])
    parser.add_argument("--include-modules", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--check-file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        kernel_root = real(args.kernel_root)
        out_root = real(args.out_root)
        kernel_obj = real(args.kernel_obj) if args.kernel_obj else find_kernel_obj(out_root)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    generator = kernel_root / "scripts/clang-tools/gen_compile_commands.py"
    if not generator.is_file():
        print(f"error: missing generator: {generator}", file=sys.stderr)
        return 2

    modules = [real(path) for path in args.module_obj]
    if args.include_modules:
        modules.extend(find_module_dirs(out_root))
    modules = list(dict.fromkeys(modules))
    output = real(args.output) if args.output else kernel_root / "compile_commands.json"
    inputs = [kernel_obj, *modules]
    command = [
        "python3",
        str(generator),
        "-d",
        str(kernel_obj),
        "-o",
        str(output),
        *(str(path) for path in inputs),
    ]
    print("+ " + " ".join(command))
    if args.dry_run:
        return 0
    subprocess.run(command, check=True)

    with output.open(encoding="utf-8") as stream:
        entries = json.load(stream)
    if not entries:
        print("error: generated database is empty", file=sys.stderr)
        return 1
    print(f"entries: {len(entries)}")
    print(f"output: {output}")

    if args.check_file:
        subprocess.run(
            [
                "clangd",
                f"--check={real(args.check_file)}",
                f"--compile-commands-dir={output.parent}",
            ],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
