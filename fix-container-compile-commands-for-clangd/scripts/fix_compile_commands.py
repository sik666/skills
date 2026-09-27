#!/usr/bin/env python3
"""
Rewrite container-style paths in compile_commands.json for local clangd use.

Typical use:
    python fix_compile_commands.py --workspace /home/haodong/data/esp32 --in-place

Default rewrite:
    /workspace -> <workspace>

You can append more rules with repeated --map OLD=NEW.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite path prefixes inside compile_commands.json."
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Local path that should replace the container's /workspace prefix.",
    )
    parser.add_argument(
        "--file",
        default="compile_commands.json",
        help="Path to compile_commands.json. Defaults to ./compile_commands.json.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Rewrite the file in place. A .bak backup is created automatically.",
    )
    parser.add_argument(
        "--output",
        help="Write the rewritten JSON to this path instead of modifying the input file.",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="Additional prefix rewrite rule. Can be passed multiple times.",
    )
    return parser.parse_args()


def normalize_prefix(path: str) -> str:
    expanded = Path(path).expanduser()
    normalized = str(expanded if expanded.is_absolute() else Path(os.path.abspath(expanded)))
    return normalized.rstrip("/") or "/"


def build_rewrites(workspace: str, extra_rules: list[str]) -> list[tuple[str, str]]:
    rewrites: list[tuple[str, str]] = [("/workspace", normalize_prefix(workspace))]
    for rule in extra_rules:
        if "=" not in rule:
            raise ValueError(f"Invalid --map value: {rule!r}. Expected OLD=NEW.")
        old, new = rule.split("=", 1)
        old = old.rstrip("/") or "/"
        new = normalize_prefix(new)
        rewrites.append((old, new))
    rewrites.sort(key=lambda item: len(item[0]), reverse=True)
    return rewrites


def replace_prefix(value: str, rewrites: list[tuple[str, str]]) -> str:
    result = value
    for old, new in rewrites:
        result = result.replace(old, new)
    return result


def rewrite_json(value: Any, rewrites: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        return replace_prefix(value, rewrites)
    if isinstance(value, list):
        return [rewrite_json(item, rewrites) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_json(item, rewrites) for key, item in value.items()}
    return value


def main() -> int:
    args = parse_args()
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"compile_commands not found: {source}", file=sys.stderr)
        return 1

    if args.in_place and args.output:
        print("Use either --in-place or --output, not both.", file=sys.stderr)
        return 1

    try:
        rewrites = build_rewrites(args.workspace, args.map)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    with source.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    rewritten = rewrite_json(data, rewrites)

    if args.output:
        destination = Path(args.output).expanduser().resolve()
    elif args.in_place:
        destination = source
    else:
        destination = source.with_suffix(source.suffix + ".fixed")

    if destination == source:
        backup = source.with_suffix(source.suffix + ".bak")
        shutil.copy2(source, backup)
        print(f"Backup created: {backup}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as fh:
        json.dump(rewritten, fh, indent=2)
        fh.write("\n")

    print(f"Rewritten file: {destination}")
    print("Applied prefix rewrites:")
    for old, new in rewrites:
        print(f"  {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
