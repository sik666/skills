---
name: ssh-remote-unlock-linux-desktop
description: Unlock a locked local Linux desktop session over SSH and disable GNOME screen blanking, auto-lock, and suspend. Use when a device is reachable by SSH but its monitor is stuck on a lock screen, resumes to a black screen, or keeps blanking/locking due to idle timeouts, especially on GDM/GNOME systems.
---

# SSH Remote Unlock Linux Desktop

Use `scripts/unlock-and-disable-gnome-idle.sh` to recover a desktop that is locally locked but still reachable over SSH.

## Workflow

1. Verify SSH access works to the target host.
2. Run the script with the SSH login user and the desktop session user.
3. Let the script locate the active local graphical session with `loginctl`.
4. Let the script send `loginctl unlock-session` and clear GNOME ScreenSaver over D-Bus.
5. Let the script set GNOME idle and power keys to permanent values:
   - `org.gnome.desktop.session idle-delay = 0`
   - `org.gnome.desktop.screensaver lock-enabled = false`
   - `org.gnome.desktop.screensaver lock-delay = 0`
   - `org.gnome.settings-daemon.plugins.power sleep-inactive-*-type = 'nothing'`
   - `org.gnome.settings-daemon.plugins.power sleep-inactive-*-timeout = 0`
6. Read the printed verification values. If the panel still shows the old frame, wake the display once locally. If the compositor is visually stuck after the script reports success, restart the display manager manually.

## Quick Start

SSH as the same user that owns the desktop session:

```bash
bash scripts/unlock-and-disable-gnome-idle.sh \
  --host 192.168.31.95 \
  --ssh-user cat \
  --session-user cat
```

SSH as `root` or another privileged account but recover user `cat`:

```bash
bash scripts/unlock-and-disable-gnome-idle.sh \
  --host 192.168.31.95 \
  --ssh-user root \
  --session-user cat
```

Use a different SSH port if needed:

```bash
bash scripts/unlock-and-disable-gnome-idle.sh \
  --host 192.168.31.95 \
  --port 2222 \
  --ssh-user cat \
  --session-user cat
```

## Constraints

- Prefer SSH as the same desktop user or as `root`. If SSH uses another account, that account must be able to run commands as the session user with `sudo` or `runuser`.
- The script uses non-interactive SSH with `BatchMode=yes`. Set up SSH keys first, or replace the SSH invocation yourself if the environment requires password prompts.
- Treat the GNOME-specific `gsettings` and `org.gnome.ScreenSaver` calls as best effort. The script still attempts `loginctl unlock-session` first, which is useful beyond GNOME.
- Do not assume the desktop password equals the system `root` password. This workflow recovers the session through system/session control rather than injecting keystrokes.
- If the machine has no active local graphical session, inspect `loginctl list-sessions` and the display manager state before retrying.
