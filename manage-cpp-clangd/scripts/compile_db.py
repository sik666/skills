#!/usr/bin/env python3
"""Inspect, rewrite, and merge Clang compilation databases."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
from typing import Any


def load_database(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{path}: top-level JSON value must be an array")
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: entry {index} is not an object")
        for field in ("directory", "file"):
            if not isinstance(entry.get(field), str):
                raise ValueError(f"{path}: entry {index} has no string {field!r}")
        has_command = isinstance(entry.get("command"), str)
        has_arguments = isinstance(entry.get("arguments"), list)
        if has_command == has_arguments:
            raise ValueError(
                f"{path}: entry {index} must contain exactly one of "
                "'command' or 'arguments'"
            )
    return data


def parse_mappings(values: list[str]) -> list[tuple[str, str]]:
    mappings: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid --map {value!r}; expected OLD=NEW")
        old, new = value.split("=", 1)
        if not old:
            raise ValueError("mapping OLD prefix cannot be empty")
        mappings.append((old, str(Path(new).expanduser()) if new else new))
    mappings.sort(key=lambda item: len(item[0]), reverse=True)
    return mappings


def rewrite_value(value: Any, mappings: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        for old, new in mappings:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [rewrite_value(item, mappings) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_value(item, mappings) for key, item in value.items()}
    return value


def resolved_paths(entry: dict[str, Any], database: Path) -> tuple[Path, Path]:
    directory = Path(entry["directory"]).expanduser()
    if not directory.is_absolute():
        directory = database.parent / directory
    directory = Path(os.path.normpath(directory))
    source = Path(entry["file"]).expanduser()
    if not source.is_absolute():
        source = directory / source
    return directory, Path(os.path.normpath(source))


def invocation_key(entry: dict[str, Any]) -> str:
    if "command" in entry:
        return entry["command"]
    return json.dumps(entry["arguments"], ensure_ascii=False, separators=(",", ":"))


def compiler_name(entry: dict[str, Any]) -> str:
    try:
        argv = (
            shlex.split(entry["command"])
            if "command" in entry
            else [str(arg) for arg in entry["arguments"]]
        )
    except ValueError:
        return "<unparseable-command>"
    if not argv:
        return "<empty-command>"
    first = Path(argv[0]).name
    if first in {"ccache", "sccache", "distcc"} and len(argv) > 1:
        return f"{first} -> {Path(argv[1]).name}"
    return first


def write_database(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def inspect_command(args: argparse.Namespace) -> int:
    database = args.database.expanduser().resolve()
    entries = load_database(database)
    workspace = args.workspace.expanduser().resolve() if args.workspace else None
    missing_directories = 0
    missing_files = 0
    outside_workspace = 0
    relative_directories = 0
    relative_files = 0
    compilers: Counter[str] = Counter()
    components: Counter[str] = Counter()
    duplicates: Counter[tuple[str, str, str]] = Counter()
    serialized = json.dumps(entries, ensure_ascii=False)

    for entry in entries:
        if not Path(entry["directory"]).is_absolute():
            relative_directories += 1
        if not Path(entry["file"]).is_absolute():
            relative_files += 1
        directory, source = resolved_paths(entry, database)
        missing_directories += not directory.is_dir()
        missing_files += not source.is_file()
        compilers[compiler_name(entry)] += 1
        duplicates[(str(directory), str(source), invocation_key(entry))] += 1
        if workspace:
            try:
                relative = source.relative_to(workspace)
                components[relative.parts[0] if relative.parts else "."] += 1
            except ValueError:
                outside_workspace += 1

    print(f"database: {database}")
    print(f"entries: {len(entries)}")
    print(f"relative directories: {relative_directories}")
    print(f"relative files: {relative_files}")
    print(f"missing directories: {missing_directories}")
    print(f"missing files: {missing_files}")
    print(f"duplicate exact invocations: {sum(count - 1 for count in duplicates.values())}")
    if workspace:
        print(f"workspace: {workspace}")
        print(f"files outside workspace: {outside_workspace}")
        print("top-level coverage:")
        for name, count in components.most_common():
            print(f"  {name}: {count}")
    print("compilers:")
    for name, count in compilers.most_common():
        print(f"  {name}: {count}")
    for needle in args.contains:
        print(f"string occurrences {needle!r}: {serialized.count(needle)}")

    return 1 if missing_directories or missing_files else 0


def rewrite_command(args: argparse.Namespace) -> int:
    source = args.database.expanduser().resolve()
    mappings = parse_mappings(args.map)
    if not mappings:
        raise ValueError("rewrite requires at least one --map OLD=NEW")
    if args.in_place and args.output:
        raise ValueError("use either --in-place or --output, not both")
    data = rewrite_value(load_database(source), mappings)
    destination = (
        source
        if args.in_place
        else args.output.expanduser().resolve()
        if args.output
        else source.with_suffix(source.suffix + ".fixed")
    )
    if destination == source:
        backup = source.with_suffix(source.suffix + ".bak")
        shutil.copy2(source, backup)
        print(f"backup: {backup}")
    write_database(destination, data)
    print(f"wrote: {destination}")
    for old, new in mappings:
        print(f"mapped: {old} -> {new}")
    return 0


def merge_command(args: argparse.Namespace) -> int:
    mappings = parse_mappings(args.map)
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    skipped_missing = 0

    for database_arg in args.databases:
        database = database_arg.expanduser().resolve()
        for original in load_database(database):
            entry = rewrite_value(original, mappings)
            directory, source = resolved_paths(entry, database)
            if args.canonicalize:
                entry["directory"] = str(directory.resolve(strict=False))
                entry["file"] = str(source.resolve(strict=False))
                directory, source = resolved_paths(entry, database)
            if args.drop_missing and (not directory.is_dir() or not source.is_file()):
                skipped_missing += 1
                continue
            key = (str(directory), str(source), invocation_key(entry))
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)

    merged.sort(
        key=lambda entry: (
            entry["file"],
            entry["directory"],
            str(entry.get("output", "")),
            invocation_key(entry),
        )
    )
    output = args.output.expanduser().resolve()
    write_database(output, merged)
    print(f"wrote: {output}")
    print(f"entries: {len(merged)}")
    if args.drop_missing:
        print(f"skipped missing: {skipped_missing}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="validate and summarize a database")
    inspect_parser.add_argument("database", type=Path)
    inspect_parser.add_argument("--workspace", type=Path)
    inspect_parser.add_argument("--contains", action="append", default=[])
    inspect_parser.set_defaults(handler=inspect_command)

    rewrite_parser = subparsers.add_parser("rewrite", help="rewrite path strings")
    rewrite_parser.add_argument("database", type=Path)
    rewrite_parser.add_argument("--map", action="append", default=[], metavar="OLD=NEW")
    rewrite_parser.add_argument("--output", type=Path)
    rewrite_parser.add_argument("--in-place", action="store_true")
    rewrite_parser.set_defaults(handler=rewrite_command)

    merge_parser = subparsers.add_parser("merge", help="merge compilation databases")
    merge_parser.add_argument("databases", nargs="+", type=Path)
    merge_parser.add_argument("--output", required=True, type=Path)
    merge_parser.add_argument("--map", action="append", default=[], metavar="OLD=NEW")
    merge_parser.add_argument("--canonicalize", action="store_true")
    merge_parser.add_argument("--drop-missing", action="store_true")
    merge_parser.set_defaults(handler=merge_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
