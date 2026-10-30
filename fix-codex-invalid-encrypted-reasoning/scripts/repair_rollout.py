#!/usr/bin/env python3
"""Replace post-compaction encrypted reasoning without shifting rollout byte offsets."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path


def file_identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def read_records(path: Path):
    lines = path.read_bytes().splitlines(keepends=True)
    if not lines or any(not line.endswith(b"\n") for line in lines):
        raise ValueError("rollout must contain newline-terminated JSONL records")
    return lines, [json.loads(line) for line in lines]


def replacement(record, original_length: int) -> bytes:
    event = {
        "timestamp": record["timestamp"],
        "ordinal": record["ordinal"],
        "type": "event_msg",
        "payload": {"type": "agent_message", "message": "", "phase": "commentary"},
    }
    encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) + 1 > original_length:
        raise ValueError(f"ordinal {record['ordinal']}: replacement does not fit")
    return encoded + b" " * (original_length - len(encoded) - 1) + b"\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rollout", type=Path, help="exact JSONL rollout segment to repair")
    parser.add_argument("--apply", action="store_true", help="write the verified, same-size repair")
    parser.add_argument("--backup-dir", type=Path, help="private directory for the original file")
    args = parser.parse_args()
    source = args.rollout.resolve(strict=True)
    if not source.is_file() or source.suffix != ".jsonl":
        parser.error("rollout must be a JSONL file")
    if args.apply and args.backup_dir is None:
        parser.error("--apply requires --backup-dir")

    initial_stat = source.stat()
    lines, records = read_records(source)
    if file_identity(source.stat()) != file_identity(initial_stat):
        raise RuntimeError("rollout changed while being read; close the session and retry")
    last_compaction = max((i for i, record in enumerate(records) if record.get("type") == "compacted"), default=-1)
    selected = [
        i
        for i, record in enumerate(records)
        if i > last_compaction
        and record.get("type") == "response_item"
        and (record.get("payload") or {}).get("type") == "reasoning"
        and (record.get("payload") or {}).get("encrypted_content")
    ]
    print(f"rollout: {source}")
    print(f"records: {len(records)}; last compaction line: {last_compaction + 1}; encrypted reasoning candidates: {len(selected)}")
    if not args.apply:
        return
    if not selected:
        raise ValueError("no post-compaction encrypted reasoning records to replace")

    backup_dir = args.backup_dir.expanduser().resolve()
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if stat.S_IMODE(backup_dir.stat().st_mode) & 0o077:
        raise ValueError("backup directory must not be accessible by group or others")
    backup = backup_dir / source.name
    if backup.exists() or backup == source:
        raise FileExistsError(f"backup target already exists: {backup}")

    patched = list(lines)
    for i in selected:
        patched[i] = replacement(records[i], len(lines[i]))
    if any(len(left) != len(right) for left, right in zip(lines, patched)):
        raise AssertionError("line byte length changed")
    if len(b"".join(lines)) != len(b"".join(patched)):
        raise AssertionError("file byte length changed")
    for i, line in enumerate(patched):
        parsed = json.loads(line)
        if i not in selected and parsed != records[i]:
            raise AssertionError(f"unexpected change at line {i + 1}")

    shutil.copy2(source, backup)
    backup.chmod(0o600)
    if backup.read_bytes() != b"".join(lines) or file_identity(source.stat()) != file_identity(initial_stat):
        raise RuntimeError("rollout changed before backup completed; close the session and retry")
    fd, temporary = tempfile.mkstemp(prefix=".reasoning-repair-", suffix=".jsonl", dir=source.parent)
    replaced = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.writelines(patched)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, stat.S_IMODE(source.stat().st_mode))
        if file_identity(source.stat()) != file_identity(initial_stat):
            raise RuntimeError("rollout changed before replacement; close the session and retry")
        os.replace(temporary, source)
        replaced = True
        reread, _ = read_records(source)
        if reread != patched:
            raise AssertionError("written file differs from verified repair")
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        if replaced:
            shutil.copy2(backup, source)
        raise
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    print(f"replaced: {len(selected)}; byte offsets preserved: yes")
    print(f"backup: {backup}; sha256: {digest}")


if __name__ == "__main__":
    main()
