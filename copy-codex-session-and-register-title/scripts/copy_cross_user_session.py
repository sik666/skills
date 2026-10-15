#!/usr/bin/env python3
"""Copy all rollout fragments for one Codex thread into another local history.

Run without --apply to inspect the migration. The apply path makes destination
backups, creates a new UUIDv7-style thread ID, and preserves source history.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import uuid

from codex_history_api import api_arguments, select_provider, server_for


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src-home", type=Path, required=True)
    parser.add_argument("--dst-home", type=Path, required=True)
    parser.add_argument("--src-codex-home", type=Path, help="override source .codex directory")
    parser.add_argument("--dst-codex-home", type=Path, help="override destination .codex directory")
    parser.add_argument("--thread-id", required=True, help="source UUID thread ID")
    parser.add_argument("--target-provider", help="default: effective destination provider from config/read")
    parser.add_argument("--allow-provider-mismatch", action="store_true",
                        help="allow an intentional import to a provider other than the active one")
    parser.add_argument("--title", help="destination display title; source name, then title by default")
    parser.add_argument("--apply", action="store_true", help="perform the copy after preview")
    api_arguments(parser)
    return parser.parse_args()


def uuid7() -> str:
    milliseconds = int(time.time() * 1000)
    value = (
        (milliseconds << 80)
        | (0x7 << 76)
        | (0x2 << 62)
        | (int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1))
    )
    return str(uuid.UUID(int=value))


def source_rollouts(source_root: Path, thread_id: str) -> list[Path]:
    files: list[Path] = []
    for tree in (source_root / "sessions", source_root / "archived_sessions"):
        if tree.is_dir():
            files.extend(tree.rglob(f"rollout-*{thread_id}*.jsonl"))
    return sorted(path for path in files if path.is_file())


def metadata(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        item = json.loads(handle.readline())
    payload = item.get("payload")
    if item.get("type") != "session_meta" or not isinstance(payload, dict):
        raise ValueError(f"{path} does not begin with a session_meta record")
    return payload


def destination_path(source: Path, source_root: Path, destination_root: Path, old_id: str, new_id: str) -> Path:
    sessions = source_root / "sessions"
    if source.is_relative_to(sessions):
        relative = source.relative_to(sessions)
        return destination_root / "sessions" / relative.parent / source.name.replace(old_id, new_id)
    stamp = source.name.removeprefix("rollout-").split("T", 1)[0]
    try:
        day = dt.date.fromisoformat(stamp)
    except ValueError as exc:
        raise ValueError(f"cannot derive date from archived rollout name: {source.name}") from exc
    return destination_root / "sessions" / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}" / source.name.replace(old_id, new_id)


def copy_rollout(source: Path, destination: Path, new_id: str, target_provider: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8") as reader, destination.open("w", encoding="utf-8") as writer:
        first = json.loads(reader.readline())
        payload = first["payload"]
        payload["id"] = new_id
        payload["session_id"] = new_id
        payload["model_provider"] = target_provider
        writer.write(json.dumps(first, ensure_ascii=False, separators=(",", ":")) + "\n")
        shutil.copyfileobj(reader, writer, length=1024 * 1024)
    shutil.copystat(source, destination)


def backup(destination_root: Path, stamp: str) -> Path:
    db = destination_root / "state_5.sqlite"
    index = destination_root / "session_index.jsonl"
    directory = destination_root / f"backup-{stamp}-cross-user-session"
    directory.mkdir(mode=0o700)
    source = sqlite3.connect(db)
    target = sqlite3.connect(directory / "state_5.sqlite")
    source.backup(target)
    target.close()
    source.close()
    if index.exists():
        shutil.copy2(index, directory / "session_index.jsonl")
    return directory


def insert_thread(source_db: Path, destination_db: Path, old_id: str, new_id: str, rollout: Path, provider: str, title: str, now: float) -> None:
    source = sqlite3.connect(f"{source_db.as_uri()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    row = source.execute("select * from threads where id=?", (old_id,)).fetchone()
    source.close()
    if row is None:
        raise ValueError(f"source threads row not found: {old_id}")

    destination = sqlite3.connect(destination_db)
    if destination.execute("select 1 from threads where id=?", (new_id,)).fetchone():
        destination.close()
        raise ValueError(f"target thread ID already exists: {new_id}")
    columns = [item[1] for item in destination.execute("pragma table_info(threads)")]
    values = {key: value for key, value in dict(row).items() if key in columns}
    seconds, milliseconds = int(now), int(now * 1000)
    overrides = {
        "id": new_id,
        "rollout_path": str(rollout),
        "model_provider": provider,
        "title": title,
        "name": title,
        "created_at": seconds,
        "updated_at": seconds,
        "created_at_ms": milliseconds,
        "updated_at_ms": milliseconds,
        "recency_at": seconds,
        "recency_at_ms": milliseconds,
        "archived": 0,
        "archived_at": None,
    }
    values.update({key: value for key, value in overrides.items() if key in columns})
    if "id" not in values:
        destination.close()
        raise ValueError("destination threads schema has no id column")
    names = list(values)
    destination.execute(
        f"insert into threads ({','.join(names)}) values ({','.join('?' for _ in names)})",
        [values[name] for name in names],
    )
    destination.commit()
    destination.close()


def write_index(index: Path, thread_id: str, title: str, now: float) -> None:
    entries = []
    if index.exists():
        with index.open(encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
    entries = [entry for entry in entries if entry.get("id") != thread_id]
    updated = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    entries.append({"id": thread_id, "thread_name": title, "updated_at": updated})
    temporary = index.with_name(index.name + f".{thread_id}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    if index.exists():
        shutil.copystat(index, temporary)
    temporary.replace(index)


def main() -> int:
    args = parse_args()
    source_root = (args.src_codex_home or args.src_home / ".codex").resolve()
    destination_root = (args.dst_codex_home or args.dst_home / ".codex").resolve()
    source_db = source_root / "state_5.sqlite"
    destination_db = destination_root / "state_5.sqlite"
    for database in (source_db, destination_db):
        if not database.is_file():
            raise SystemExit(f"required database is missing: {database}")
    files = source_rollouts(source_root, args.thread_id)
    if not files:
        raise SystemExit(f"no rollout files found for thread: {args.thread_id}")
    for file in files:
        item = metadata(file)
        if item.get("id") != args.thread_id or item.get("session_id") != args.thread_id:
            raise SystemExit(f"thread ID mismatch in source metadata: {file}")
    with server_for(args, destination_root) as server:
        active_provider = server.provider()
    target_provider = select_provider(active_provider, args.target_provider, args.allow_provider_mismatch)
    source = sqlite3.connect(f"{source_db.as_uri()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    row = source.execute("select * from threads where id=?", (args.thread_id,)).fetchone()
    source.close()
    if row is None:
        raise SystemExit(f"source threads row not found: {args.thread_id}")
    title = args.title or dict(row).get("name") or row["title"] or args.thread_id
    new_id = uuid7()
    targets = [destination_path(file, source_root, destination_root, args.thread_id, new_id) for file in files]
    plan = {
        "mode": "apply" if args.apply else "dry-run",
        "source_thread_id": args.thread_id,
        "source_provider": row["model_provider"],
        "target_thread_id": new_id,
        "target_provider": target_provider,
        "effective_destination_provider": active_provider,
        "provider_source": "config/read",
        "provider_matches_active": target_provider == active_provider,
        "title": title,
        "segments": len(files),
        "source_bytes": sum(file.stat().st_size for file in files),
        "latest_target_rollout": str(targets[-1]),
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.apply:
        return 0
    if any(target.exists() for target in targets):
        raise SystemExit("refusing to overwrite an existing target rollout")

    backup_dir = backup(destination_root, dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    created: list[Path] = []
    db_inserted = False
    try:
        for source_file, target_file in zip(files, targets, strict=True):
            created.append(target_file)
            copy_rollout(source_file, target_file, new_id, target_provider)
        now = time.time()
        insert_thread(source_db, destination_db, args.thread_id, new_id, targets[-1], target_provider, title, now)
        db_inserted = True
        write_index(destination_root / "session_index.jsonl", new_id, title, now)
    except Exception:
        if db_inserted:
            connection = sqlite3.connect(destination_db)
            connection.execute("delete from threads where id=?", (new_id,))
            connection.commit()
            connection.close()
        for file in created:
            file.unlink(missing_ok=True)
        raise
    plan["backup"] = str(backup_dir)
    plan["copied_bytes"] = sum(file.stat().st_size for file in created)
    plan["registration_status"] = "written; API and UI verification still required"
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
