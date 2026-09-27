---
name: fix-vscode-remote-codex-server
description: Diagnose and repair user-specific VS Code Remote SSH failures involving a broken or partial ~/.vscode-server installation, stuck "Starting server with command..." bootstrap loops, orphaned command-shell/agent-host processes, stale /tmp VS Code sockets, and Codex/OpenAI VS Code extension panels that do not load for one Linux user while another user on the same machine works. Use when Codex needs to inspect VS Code Server logs, safely move aside a corrupt server commit, repair ownership/permissions, copy a known-good OpenAI Codex extension from another local user, or explain Codex auth 401/token symptoms without deleting user data.
---

# Fix VS Code Remote Codex Server

## Approach

Treat this as a per-user state repair unless system SSH itself is broken. The common failure pattern is:

- VS Code Remote SSH output repeats `Starting server with command...`.
- Remote processes show `sshd -> sh -> code-<commit> command-shell -> sleep 180`.
- `~/.vscode-server/cli/servers/Stable-<commit>/server` is incomplete, often containing only `node`.
- The Codex/OpenAI panel does not load because the extension is stale, partially installed, or cannot start after the server bootstrap stalls.

Prefer reversible repairs. Move broken directories aside with a timestamp instead of deleting them. Do not remove `~/.codex/auth.json`, sessions, or project data unless the user explicitly asks.

## Quick Workflow

Use `scripts/repair_vscode_codex_remote.sh` for repeatable local repairs when you have shell access to the affected machine:

```bash
scripts/repair_vscode_codex_remote.sh check --user haodong
scripts/repair_vscode_codex_remote.sh fix-server --user haodong --commit 6a44c352bd24569c417e530095901b649960f9f8
scripts/repair_vscode_codex_remote.sh copy-codex-extension --user haodong --source-user xuke
```

Run commands with `sudo` when checking another user's home directory or killing their processes:

```bash
sudo scripts/repair_vscode_codex_remote.sh check --user haodong
```

If SSH to the affected user fails because password automation is unavailable, inspect the user's home directory locally with sudo. Do not confuse user-namespace display artifacts such as `nobody:nogroup` with real ownership until checking with `sudo stat` or numeric UID/GID.

## Diagnosis

Check identity and ownership:

```bash
id <user>
getent passwd <user>
sudo stat -c '%U:%G %u:%g %a %n' /home/<user> /home/<user>/.vscode-server /home/<user>/.codex
```

List recent server logs:

```bash
sudo find /home/<user>/.vscode-server -maxdepth 5 -type f -name '*.log' -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' | sort | tail -40
sudo tail -160 /home/<user>/.vscode-server/.cli.<commit>.log
```

Inspect stuck processes:

```bash
sudo ps -u <user> -o pid,ppid,stat,etime,cmd --forest
```

Inspect the active server commit:

```bash
sudo ls -la /home/<user>/.vscode-server/cli/servers
sudo find /home/<user>/.vscode-server/cli/servers/Stable-<commit>/server -maxdepth 2 -printf '%M %u:%g %s %p\n' | head -80
```

A `server` directory with only `node`, or only a tiny subset of expected VS Code Server files, is a broken install. Move it aside and let VS Code reinstall.

## Repair VS Code Server

Use a timestamped backup path. Stop only VS Code Remote/Codex bootstrap processes for the affected user, not unrelated user services:

```bash
sudo scripts/repair_vscode_codex_remote.sh fix-server --user <user> --commit <commit>
```

The repair should:

- Kill `code-<commit>`, `command-shell`, `agent host`, and failed Remote SSH bootstrap leftovers for that user.
- Move `~/.vscode-server/cli/servers/Stable-<commit>` to `*.broken-<timestamp>`.
- Move `~/.vscode-server/code-<commit>` to `*.broken-<timestamp>` when present.
- Move obvious partial cleanup directories such as `_backup_cleanup_<date>` to `*.broken-<timestamp>`.
- Reapply ownership to `~/.vscode-server` and `~/.codex`.
- Preserve extensions, user settings, workspace storage, Codex sessions, and auth files.

After this, ask the user to reconnect with VS Code Remote SSH. A clean reconnect should reinstall the missing server for the current client commit.

## Repair Codex Extension

If the VS Code Server starts but the Codex/OpenAI panel stays blank or fails to load, compare extension versions between a working local user and the broken user:

```bash
find /home/<working-user>/.vscode-server/extensions -maxdepth 1 -type d -name 'openai.chatgpt-*' -printf '%f\n' | sort
find /home/<broken-user>/.vscode-server/extensions -maxdepth 1 -type d -name 'openai.chatgpt-*' -printf '%f\n' | sort
```

If the working user has a newer complete extension, copy it:

```bash
sudo scripts/repair_vscode_codex_remote.sh copy-codex-extension --user <broken-user> --source-user <working-user>
```

Then validate the binary as the affected user:

```bash
sudo -u <broken-user> /home/<broken-user>/.vscode-server/extensions/openai.chatgpt-<version>-linux-x64/bin/linux-x86_64/codex --version
```

Keep older extension versions unless they are clearly corrupt. VS Code can select or clean extension versions itself.

## Codex Auth Symptoms

Codex logs may contain:

- `Unable to extract account id and plan from auth token`
- `401 Unauthorized /wham/usage`
- `api key auth is not supported`
- `chatgpt authentication required ... api key auth is not supported`

Do not immediately delete `~/.codex/auth.json`. First compare with a working user, inspect only key names and token lengths, and check whether the extension binary starts. The panel can fail before auth is the true blocker. If the server and extension are healthy but 401 persists, have the user re-authenticate in the Codex/OpenAI extension UI or explicitly approve clearing the affected auth file.

Use redaction when showing auth diagnostics:

```bash
sudo node -e 'const fs=require("fs"); const p="/home/<user>/.codex/auth.json"; const j=JSON.parse(fs.readFileSync(p,"utf8")); console.log(Object.keys(j)); for (const [k,v] of Object.entries(j)) console.log(k, typeof v, typeof v==="string"?v.length:Object.keys(v||{}));'
```

## Verification

Before finishing, report:

- The broken server commit and why it looked corrupt.
- Backup paths created.
- Whether affected-user VS Code/Codex processes are now gone.
- Which Codex extension versions are installed.
- Any remaining action the user must do, usually "reconnect with VS Code Remote SSH" or "sign in again inside the Codex extension".
