---
name: samba-smb-share
description: Configure, verify, and troubleshoot Samba/SMB shares on Linux for Windows clients, including smb.conf edits, SMB user setup, service reloads, permission checks, local smbclient validation, and Windows drive mapping issues. Use when Codex needs to expose a Linux directory over SMB or diagnose why a Windows client cannot browse or write to a Samba share.
---

# Samba SMB Share

Use the reference guide for concrete commands and keep the live workflow disciplined: configure, validate locally, then test from Windows.

## Workflow

1. Confirm the Linux path to share, the SMB share name, and the Unix user that should own access.
2. Update `/etc/samba/smb.conf` with the share stanza.
3. Validate the config with `testparm -s`.
4. Ensure the Samba service is installed, enabled, and reloaded or restarted as needed.
5. Ensure the Linux user exists and has an SMB password via `smbpasswd`.
6. Verify locally with `smbclient` before blaming Windows.
7. If local access works but Windows fails, inspect cached credentials and mapped-drive state on the Windows side.

## Resources

- Read `references/guide.md` for the full setup and troubleshooting checklist.
- Reuse `assets/example-smb.conf-snippet.ini` as a starting config fragment.
- Reuse `assets/windows-map-commands.cmd` for Windows mapping commands when the user wants a ready-made command file.

## Guardrails

- Treat Samba permissions and Linux filesystem permissions as separate layers.
- Prefer `systemctl reload smbd` after config-only changes; use restart when authentication or process state might be stale.
- Do not assume a UI browse failure is a Samba config issue until local `smbclient` tests fail.
