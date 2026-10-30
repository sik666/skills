#!/usr/bin/env python3
"""Read-only summary for local VS Code Codex webview startup failures."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


def newest(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    return max(existing, key=lambda path: path.stat().st_mtime) if existing else None


def read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def count(text: str, needle: str) -> int:
    return text.count(needle)


def extension_records(extensions_dir: Path) -> list[dict[str, object]]:
    registry = extensions_dir / "extensions.json"
    if not registry.is_file():
        return []
    try:
        entries = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    records = []
    for entry in entries:
        identifier = entry.get("identifier", {})
        if identifier.get("id") != "openai.chatgpt":
            continue
        metadata = entry.get("metadata", {})
        location = entry.get("location", {})
        records.append(
            {
                "version": entry.get("version"),
                "path": location.get("fsPath") or location.get("path"),
                "preRelease": metadata.get("preRelease"),
                "updated": metadata.get("updated"),
            }
        )
    return records


def workspace_bloat(workspace_root: Path) -> list[dict[str, object]]:
    results = []
    if not workspace_root.is_dir():
        return results
    for database in workspace_root.glob("*/state.vscdb"):
        try:
            connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
            page_count = connection.execute("PRAGMA page_count").fetchone()[0]
            free_count = connection.execute("PRAGMA freelist_count").fetchone()[0]
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            connection.close()
            workspace_file = database.parent / "workspace.json"
            workspace = json.loads(workspace_file.read_text()) if workspace_file.is_file() else {}
            results.append(
                {
                    "database": str(database),
                    "bytes": database.stat().st_size,
                    "free_ratio": round(free_count / page_count, 4) if page_count else 0,
                    "integrity": integrity,
                    "workspace": workspace,
                }
            )
        except (OSError, sqlite3.Error, json.JSONDecodeError):
            continue
    return sorted(results, key=lambda item: int(item["bytes"]), reverse=True)[:5]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-dir", type=Path, default=Path.home() / ".config/Code")
    parser.add_argument("--extensions-dir", type=Path, default=Path.home() / ".vscode/extensions")
    args = parser.parse_args()

    logs_root = args.code_dir / "logs"
    codex_log = newest(list(logs_root.glob("*/window*/exthost/openai.chatgpt/Codex.log")))
    latest_log_dir = codex_log.parents[3] if codex_log else newest([path for path in logs_root.glob("*") if path.is_dir()])
    main_log = latest_log_dir / "main.log" if latest_log_dir else None
    shared_log = latest_log_dir / "sharedprocess.log" if latest_log_dir else None
    sync_log = latest_log_dir / "userDataSync.log" if latest_log_dir else None

    codex_text = read_text(codex_log)
    main_text = read_text(main_log)
    updater_text = read_text(shared_log) + "\n" + read_text(sync_log)
    versions = sorted(set(re.findall(r"openai\.chatgpt-([0-9.]+)-linux", codex_text)))
    timeout_versions = sorted(set(re.findall(r"extensionVersion=([0-9.]+)", codex_text)))
    installed_lines = [line for line in updater_text.splitlines() if "openai.chatgpt" in line and any(word in line.lower() for word in ("install", "extract", "removed"))]

    summary = {
        "latest_log_dir": str(latest_log_dir) if latest_log_dir else None,
        "codex_log": str(codex_log) if codex_log else None,
        "backend": {
            "spawn_count": count(codex_text, "Spawning codex app-server"),
            "initialize_count": count(codex_text, "Initialize received"),
        },
        "renderer": {
            "timeout_count": count(codex_text, "renderer_ready_timeout"),
            "ready_mentions": count(codex_text, "renderer_ready"),
            "success_count": count(codex_text, "app_start outcome=success"),
        },
        "window_unresponsive_count": count(main_text, "detected unresponsive"),
        "versions_seen_in_codex_log": versions,
        "timeout_extension_versions": timeout_versions,
        "registered_extensions": extension_records(args.extensions_dir),
        "recent_extension_update_lines": installed_lines[-12:],
        "largest_workspace_databases": workspace_bloat(args.code_dir / "User/workspaceStorage"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
