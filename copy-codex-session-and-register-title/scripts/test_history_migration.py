#!/usr/bin/env python3
"""Isolated regression tests; never access or modify real user histories."""

import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

import codex_history_api as api
import copy_cross_user_session as migration


class FakeServer:
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        pass

    def provider(self):
        return "custom"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-history-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.src = self.root / "source"
        self.dst = self.root / "destination"
        self.old_id = "019fcb59-3220-7e41-89db-843b6c25fed1"
        for home in (self.src, self.dst):
            codex = home / ".codex"
            codex.mkdir(parents=True)
            with sqlite3.connect(codex / "state_5.sqlite") as db:
                db.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, "
                           "model_provider TEXT, title TEXT, name TEXT, created_at INTEGER, "
                           "updated_at INTEGER, archived INTEGER)")
        self.files = []
        for tree, stamp in (("sessions/2026/09/01", "2026-09-01T00-00-00"),
                            ("sessions/2026/09/02", "2026-09-02T00-00-00"),
                            ("archived_sessions", "2026-09-03T00-00-00")):
            file = self.src / ".codex" / tree / f"rollout-{stamp}-{self.old_id}.jsonl"
            file.parent.mkdir(parents=True, exist_ok=True)
            first = {"type": "session_meta", "payload": {
                "id": self.old_id, "session_id": self.old_id, "model_provider": "OpenAI"}}
            file.write_text(json.dumps(first) + '\n{"type":"message","payload":"unchanged"}\n')
            self.files.append(file)
        with sqlite3.connect(self.src / ".codex/state_5.sqlite") as db:
            db.execute("INSERT INTO threads VALUES (?,?,?,?,?,?,?,?)",
                       (self.old_id, str(self.files[-1]), "OpenAI", "Initial prompt", "Display name", 1, 1, 0))
        self.index = self.dst / ".codex/session_index.jsonl"
        self.index.write_text('{"id":"existing","thread_name":"Existing"}\n')
        self.source_snapshot = {file: file.read_bytes() for file in (self.src / ".codex").rglob("*") if file.is_file()}

    def run_migration(self, *options):
        argv = ["copy_cross_user_session.py", "--src-home", str(self.src), "--dst-home", str(self.dst),
                "--thread-id", self.old_id, *options]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(migration, "server_for", return_value=FakeServer()), contextlib.redirect_stdout(output):
            result = migration.main()
        return result, output.getvalue()

    def assert_source_unchanged(self):
        self.assertEqual(self.source_snapshot, {file: file.read_bytes() for file in self.source_snapshot})

    def test_dry_run_detects_provider_and_name_without_mutation(self):
        before = {file: file.read_bytes() for file in (self.dst / ".codex").rglob("*") if file.is_file()}
        result, output = self.run_migration()
        plan = json.loads(output)
        self.assertEqual(result, 0)
        self.assertEqual((plan["target_provider"], plan["title"], plan["segments"]), ("custom", "Display name", 3))
        self.assertEqual(before, {file: file.read_bytes() for file in (self.dst / ".codex").rglob("*") if file.is_file()})
        self.assert_source_unchanged()

    def test_mismatch_refused_before_copy_or_backup(self):
        for provider in ("OpenAI", "openai", "Custom"):
            with self.assertRaisesRegex(ValueError, "differs from effective provider"):
                self.run_migration("--apply", "--target-provider", provider)
        self.assertFalse(list((self.dst / ".codex").glob("backup-*")))
        self.assertFalse(list((self.dst / ".codex").rglob("rollout-*.jsonl")))
        self.assert_source_unchanged()

    def test_apply_copies_all_segments_and_preserves_bodies(self):
        result, output = self.run_migration("--apply")
        plan, _ = json.JSONDecoder().raw_decode(output)
        new_id = plan["target_thread_id"]
        targets = list((self.dst / ".codex/sessions").rglob("rollout-*.jsonl"))
        self.assertEqual((result, len(targets)), (0, 3))
        for target in targets:
            meta = migration.metadata(target)
            self.assertEqual((meta["id"], meta["session_id"], meta["model_provider"]), (new_id, new_id, "custom"))
            self.assertEqual(target.read_bytes().split(b"\n", 1)[1], self.files[0].read_bytes().split(b"\n", 1)[1])
        with sqlite3.connect(self.dst / ".codex/state_5.sqlite") as db:
            self.assertEqual(db.execute("SELECT model_provider,name,title FROM threads WHERE id=?", (new_id,)).fetchone(),
                             ("custom", "Display name", "Display name"))
        self.assertEqual([json.loads(line)["id"] for line in self.index.read_text().splitlines()], ["existing", new_id])
        backups = list((self.dst / ".codex").glob("backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "session_index.jsonl").read_text(), '{"id":"existing","thread_name":"Existing"}\n')
        self.assert_source_unchanged()

    def test_copy_failure_cleans_partially_written_target(self):
        def fail_copy(source, target, *unused):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("partial")
            raise OSError("simulated copy failure")
        with patch.object(migration, "copy_rollout", side_effect=fail_copy), self.assertRaises(OSError):
            self.run_migration("--apply")
        self.assertFalse(list((self.dst / ".codex").rglob("rollout-*.jsonl")))
        self.assert_source_unchanged()

    def test_same_home_import_preserves_source(self):
        self.dst = self.src
        result, _ = self.run_migration("--apply", "--title", "Copied title")
        self.assertEqual(result, 0)
        for file in self.files:
            self.assertEqual(file.read_bytes(), self.source_snapshot[file])
        with sqlite3.connect(self.src / ".codex/state_5.sqlite") as db:
            self.assertEqual(db.execute("SELECT model_provider,name FROM threads WHERE id=?", (self.old_id,)).fetchone(),
                             ("OpenAI", "Display name"))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM threads").fetchone()[0], 2)

    def test_source_schema_without_name_falls_back_to_title(self):
        with sqlite3.connect(self.src / ".codex/state_5.sqlite") as db:
            db.execute("ALTER TABLE threads DROP COLUMN name")
        _, output = self.run_migration()
        self.assertEqual(json.loads(output)["title"], "Initial prompt")


class ApiTests(unittest.TestCase):
    def test_optional_provider_uses_documented_default(self):
        server = object.__new__(api.AppServer)
        server.cwd = Path("/tmp")
        server.request = lambda *args: {"config": {"model_provider": None}}
        self.assertEqual(server.provider(), "openai")
        server.request = lambda *args: {"config": {"model_provider": "custom"}}
        self.assertEqual(server.provider(), "custom")

    def test_intentional_mismatch_needs_explicit_switch(self):
        self.assertEqual(api.select_provider("custom", "OpenAI", True), "OpenAI")
        with self.assertRaises(ValueError):
            api.select_provider("custom", "OpenAI")
        with self.assertRaises(ValueError):
            api.select_provider("custom", "")

    def test_verification_follows_list_and_history_cursors(self):
        calls = []
        class Server:
            def request(self, method, params):
                calls.append((method, params))
                if method == "thread/list":
                    self.assert_filter = params["modelProviders"] == ["custom"]
                    if params["cursor"] is None:
                        return {"data": [{"id": "other"}], "nextCursor": "list2"}
                    return {"data": [{"id": "target"}], "nextCursor": None}
                if method == "thread/read":
                    return {"thread": {"id": "target", "modelProvider": "custom"}}
                return {"data": [{"items": [{"id": "item"}]}],
                        "nextCursor": "turn2" if params["cursor"] is None else None}
        server = Server()
        report = api.verify_thread(server, "target", "custom", 3)
        self.assertTrue(server.assert_filter)
        self.assertEqual((report["turns"], report["items"], report["ui_opened"]), (2, 2, "not_checked"))
        self.assertEqual(len(calls), 5)

    def test_pagination_bound_is_failure_not_success(self):
        class Server:
            def request(self, *unused):
                return {"data": [], "nextCursor": "more"}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            list(api.pages(Server(), "thread/list", {}, 1))

    def test_missing_list_entry_does_not_report_success(self):
        class Server:
            def request(self, *unused):
                return {"data": [], "nextCursor": None}
        with self.assertRaisesRegex(ValueError, "not found"):
            api.verify_thread(Server(), "target", "custom", 1)


if __name__ == "__main__":
    unittest.main()
