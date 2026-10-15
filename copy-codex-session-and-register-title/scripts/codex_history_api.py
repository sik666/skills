#!/usr/bin/env python3
"""Resolve destination configuration and verify history through Codex app-server."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time


class AppServer:
    def __init__(self, codex_home: Path, binary: str = "codex", cwd: Path | None = None,
                 profile: str | None = None, overrides: list[str] | None = None,
                 timeout: float = 20):
        self.codex_home = codex_home.resolve()
        self.cwd = (cwd or Path.cwd()).resolve()
        self.timeout = timeout
        self.profile = profile
        self.buffer = b""
        self.request_id = 0
        command = [binary]
        if profile:
            command.extend(["-p", profile])
        for override in overrides or []:
            command.extend(["-c", override])
        command.append("app-server")
        environment = dict(os.environ, CODEX_HOME=str(self.codex_home))
        self.process = subprocess.Popen(command, cwd=self.cwd, env=environment,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)

    def __enter__(self):
        try:
            result = self.request("initialize", {
                "clientInfo": {"name": "local_history_migration", "version": "1.1"},
                "capabilities": {"experimentalApi": True},
            })
            reported_home = result.get("codexHome")
            if reported_home and Path(reported_home).resolve() != self.codex_home:
                raise ValueError("app-server initialized with an unexpected Codex home")
            self.send({"method": "initialized"})
            return self
        except Exception:
            self.close()
            raise

    def __exit__(self, *unused):
        self.close()

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()

    def send(self, message: dict):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        self.process.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        self.request_id += 1
        request_id = self.request_id
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    error = message["error"]
                    raise ValueError(f"{method} failed ({error.get('code')}): {error.get('message')}")
                return message["result"]
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError(f"{method} timed out after {self.timeout:g}s")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                if self.profile:
                    raise ValueError("app-server could not start with --profile; some builds restrict profiles "
                                     "to runtime commands. Read config/read from the destination client, then "
                                     "pass only its verified effective settings via --config")
                raise ValueError(f"app-server closed stdout during {method}; check its configuration/version")
            self.buffer += chunk

    def provider(self) -> str:
        result = self.request("config/read", {"includeLayers": False, "cwd": str(self.cwd)})
        provider = result["config"].get("model_provider")
        if provider is None:
            # config/read exposes optional settings; Codex's documented default is openai.
            return "openai"
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("config/read did not resolve model_provider; do not guess from a login label")
        return provider


def select_provider(active: str, requested: str | None, allow_mismatch: bool = False) -> str:
    if requested is not None and not requested.strip():
        raise ValueError("target provider must not be empty")
    if requested is not None and requested != active and not allow_mismatch:
        raise ValueError(f"target provider {requested!r} differs from effective provider {active!r}; "
                         "use the effective value, or --allow-provider-mismatch only for an intentional import")
    return active if requested is None else requested


def api_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--codex-bin", default="codex", help="Codex executable used by the destination client")
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="destination workspace for config layering")
    parser.add_argument("--profile", help="destination profile (only for builds supporting app-server profiles)")
    parser.add_argument("--config", action="append", default=[], metavar="KEY=VALUE",
                        help="destination client's runtime override; repeat as needed (not printed)")
    parser.add_argument("--timeout", type=float, default=20, help="per-request API timeout in seconds")


def server_for(args, codex_home: Path) -> AppServer:
    if args.timeout <= 0:
        raise ValueError("timeout must be positive")
    return AppServer(codex_home, args.codex_bin, args.cwd, args.profile, args.config, args.timeout)


def pages(server: AppServer, method: str, params: dict, max_pages: int):
    cursor = None
    seen = set()
    for _ in range(max_pages):
        result = server.request(method, dict(params, cursor=cursor))
        yield result["data"]
        cursor = result.get("nextCursor")
        if not cursor:
            return
        if cursor in seen:
            raise ValueError(f"{method} returned a repeated pagination cursor")
        seen.add(cursor)
    raise ValueError(f"{method} exceeded --max-pages; verification is incomplete")


def verify_thread(server: AppServer, thread_id: str, provider: str, max_pages: int) -> dict:
    listed = False
    for page in pages(server, "thread/list", {
        "limit": 100, "sortKey": "updated_at", "modelProviders": [provider],
        "useStateDbOnly": True,
    }, max_pages):
        if any(thread.get("id") == thread_id for thread in page):
            listed = True
            break
    if not listed:
        raise ValueError(f"thread {thread_id} not found in provider-filtered non-archived history")
    thread = server.request("thread/read", {"threadId": thread_id, "includeTurns": False})["thread"]
    if thread.get("id") != thread_id or thread.get("modelProvider") != provider:
        raise ValueError("thread/read returned inconsistent ID/provider")
    turns = items = 0
    for page in pages(server, "thread/turns/list", {
        "threadId": thread_id, "limit": 100, "itemsView": "full", "sortDirection": "asc",
    }, max_pages):
        turns += len(page)
        items += sum(len(turn.get("items", [])) for turn in page)
    return {"thread_id": thread_id, "provider": provider, "listed": True,
            "metadata_readable": True, "history_readable": True, "turns": turns,
            "items": items, "ui_opened": "not_checked"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, required=True, help="destination Codex directory, not OS home")
    parser.add_argument("--thread-id", help="existing imported ID to verify; omit for config-only inspection")
    parser.add_argument("--provider", help="expected provider; must match effective destination config")
    parser.add_argument("--max-pages", type=int, default=100, help="bounded pagination; never silently truncate")
    api_arguments(parser)
    args = parser.parse_args()
    if not args.codex_home.is_dir() or args.max_pages <= 0:
        raise ValueError("Codex home must exist and max-pages must be positive")
    with server_for(args, args.codex_home) as server:
        active = server.provider()
        provider = select_provider(active, args.provider)
        report = {"codex_home": str(server.codex_home), "effective_provider": active,
                  "provider_source": "config/read"}
        if args.thread_id:
            report.update(verify_thread(server, args.thread_id, provider, args.max_pages))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
