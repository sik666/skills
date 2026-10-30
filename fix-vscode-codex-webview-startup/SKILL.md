---
name: fix-vscode-codex-webview-startup
description: Diagnose and repair local VS Code Codex panels that hang, stay blank, or report "Codex could not start its user interface" while the Codex App still works. Use for renderer_ready_timeout, a high-CPU Codex webview, or an extension update that was installed but has not taken effect; distinguish these from app-server, authentication, GPU, and workspace-state failures before changing data.
---

# Fix VS Code Codex Webview Startup

## Failure model

The VS Code extension has two relevant parts: the Codex `app-server` backend and an Electron webview renderer. The Codex App uses a separate UI runtime, so a working App is evidence that the account and common Codex backend are probably healthy; it does not prove that the VS Code webview can start.

In the observed failure, the old extension process started `app-server` and received `Initialize` in about 150 ms, but its webview never sent a first message and logged:

```text
[CodexWebviewProvider] Webview renderer did not become ready
reason=renderer_ready_timeout receivedWebviewMessage=false stage=renderer
```

The webview consumed high CPU and a five-second `strace -f -c` sample showed roughly 267,000 `recvmsg`/`sendto` calls, consistent with an IPC message loop. VS Code Settings Sync had already installed a newer Codex extension and marked the running version obsolete, but extension code does not switch inside the existing process. A graceful VS Code restart loaded the new version; `renderer_ready` appeared after about 8.9 seconds, `app_start outcome=success` after about 10.9 seconds, and CPU returned to idle. Treat those version numbers and timings as incident evidence, not permanent required versions.

## Diagnose before repairing

Run the bundled read-only summary first:

```bash
python3 scripts/diagnose_vscode_codex.py
```

Then inspect the latest files under `~/.config/Code/logs/<timestamp>/`:

- `window*/exthost/openai.chatgpt/Codex.log` identifies backend initialization, webview timeout, active extension paths, and successful renderer startup.
- `main.log` reports `CodeWindow: detected unresponsive` and `UnresponsiveSampleError`.
- `sharedprocess.log` and `userDataSync.log` show extension downloads, extraction, installation, and obsolete-version marking.
- `code --status` identifies the workbench, webview, extension host, and Codex `app-server` processes and their CPU use.

Classify the evidence:

- `Spawning codex app-server` followed by `Initialize received` means the backend started. Do not treat unrelated 401 feature-cache warnings, ignored configuration keys, or plugin-manifest warnings as the UI root cause.
- `renderer_ready_timeout` with `receivedWebviewMessage=false`, especially with high webview CPU, localizes the failure to the webview startup path.
- A newer `openai.chatgpt` record in `~/.vscode/extensions/extensions.json` plus an older version in the active log means a restart is required before judging the update.
- If `Initialize received` is absent, diagnose the extension binary, configuration, and authentication separately instead of applying the webview repair blindly.

Do not infer the cause from a large `state.vscdb` alone. Map a workspace directory through its `workspace.json`, compare its modification time with the failing window, and inspect `PRAGMA page_count`, `freelist_count`, and `integrity_check`. In the observed incident, a 199 MB database was almost entirely free pages and belonged to an older WiFi workspace; it was not the active window's direct failure.

## Repair

Prefer the smallest reversible action supported by the evidence.

1. If a newer complete extension is installed but the running process still uses the old version, back up the VS Code Codex state and webview stores, gracefully close VS Code, and reopen it. Preserve unsaved editor state where possible.
2. Back up at least `User/globalStorage/state.vscdb`, `Local Storage`, `Service Worker`, `WebStorage`, and `GPUCache` under a timestamped private directory. Do not remove `~/.codex`, sessions, skills, authentication, or workspace data.
3. Let VS Code select the registered extension from `extensions.json`. Do not copy, rename, or delete extension versions when an already installed update resolves the mismatch.
4. If the same version still times out after restart, close VS Code and move only the backed-up, regenerable webview stores aside. Reopen and test before changing extension global state.
5. Test `code --disable-gpu` only when cache reset does not help and renderer/GPU evidence supports it. Make hardware acceleration changes persistent only after a successful comparison run.
6. Repair a bloated workspace database only when it maps to the failing workspace and integrity or free-page evidence makes it relevant. Back it up, use SQLite `VACUUM` or `VACUUM INTO`, and verify logical rows before replacing it.

## Verify

Observe at least one full former timeout interval and require all applicable evidence:

- `Codex.log` contains `renderer_ready` and `app_start outcome=success`.
- No new `renderer_ready_timeout` appears.
- `main.log` has no new window-unresponsive entry.
- `code --status` or `ps` shows the Codex webview and VS Code processes returning to normal idle CPU.
- The user can open and interact with the Codex panel.

Report the active version before and after, the decisive log evidence, the backup path, and any state that was moved or reset.
