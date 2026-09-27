# Samba SMB Share Setup And Troubleshooting

Last updated: 2026-05-09

This note records how to expose a Linux directory through SMB/Samba so that
Windows can map it as a network drive. It also records the permission and
Windows credential issues that appeared on this machine.

## Goal

Share a Linux path, for example:

```text
/mnt/data_0
```

to Windows as:

```text
\\192.168.31.70\Data0_xuke
```

using SMB user:

```text
xuke
```

## Important Paths

Samba config:

```text
/etc/samba/smb.conf
```

Common service name on Ubuntu/Debian:

```text
smbd
```

Example shared path:

```text
/mnt/data_0
```

## Basic Share Config

Append a share section to `/etc/samba/smb.conf`:

```ini
[Data0_xuke]
    path = /mnt/data_0
    browseable = yes
    writable = yes
    valid users = xuke
```

Meaning:

```text
[Data0_xuke]        Windows-visible share name.
path                Real Linux directory being shared.
browseable = yes    Show it in share listing.
writable = yes      Samba share layer allows writes.
valid users = xuke  Only SMB user xuke can connect to this share.
```

`writable = yes` only opens the Samba layer. The Linux filesystem permissions
still need to allow the connecting Unix user to write.

## Safe Editing Workflow

Back up the current config first:

```bash
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak_$(date +%Y%m%d_%H%M%S)
```

Edit the config:

```bash
sudo nano /etc/samba/smb.conf
```

or copy a prepared file into place:

```bash
sudo install -m 0644 -o root -g root smb.conf /etc/samba/smb.conf
```

Validate syntax:

```bash
testparm -s
```

If `testparm` says:

```text
Loaded services file OK.
```

the config syntax is acceptable.

## Enable And Reload Samba

Install Samba if needed:

```bash
sudo apt update
sudo apt install samba smbclient
```

Start and enable service:

```bash
sudo systemctl enable --now smbd
```

After changing `/etc/samba/smb.conf`, reload:

```bash
sudo systemctl reload smbd
```

If group membership or authentication state changed, restart is safer:

```bash
sudo systemctl restart smbd
```

Check service status:

```bash
systemctl is-active smbd
systemctl is-enabled smbd
```

Expected:

```text
active
enabled
```

## Samba Users

Samba accounts are separate from normal Linux login passwords, although they
map to Linux users.

Check Samba users:

```bash
sudo pdbedit -L
```

Create or update the SMB password for `xuke`:

```bash
sudo smbpasswd -a xuke
```

Enable the account if needed:

```bash
sudo smbpasswd -e xuke
```

The Linux user must exist:

```bash
id xuke
```

## Local SMB Tests

List shares from the server itself:

```bash
smbclient -L //127.0.0.1 -U 'xuke%PASSWORD' -m SMB3
```

Test entering the share:

```bash
smbclient //127.0.0.1/Data0_xuke -U 'xuke%PASSWORD' -m SMB3 -c 'pwd; ls'
```

Test write access through SMB:

```bash
smbclient //127.0.0.1/Data0_xuke -U 'xuke%PASSWORD' -m SMB3 \
  -c 'cd xuke/from_haodong_data/esp32/aaa_ai_output; put /etc/hostname .smb_write_test; del .smb_write_test'
```

If this works locally but Windows still fails, the Windows client likely has a
cached credential or mapped-drive issue.

## Windows Mapping

Find the Linux server IP:

```bash
hostname -I
```

Example LAN IP:

```text
192.168.31.70
```

Windows Explorer path:

```text
\\192.168.31.70\Data0_xuke
```

Command Prompt mapping example:

```cmd
net use Z: \\192.168.31.70\Data0_xuke /user:xuke PASSWORD
```

Show existing Windows SMB connections:

```cmd
net use
```

Remove the specific share:

```cmd
net use Z: /delete
```

Remove all SMB mappings:

```cmd
net use * /delete
```

Remove all connections to the same server:

```cmd
net use \\192.168.31.70\* /delete
```

## Windows Error: Already Mapped With Another User

Windows error text can look like:

```text
The network folder specified is currently mapped using a different user name
and password. To connect using a different user name and password, first
disconnect any existing mappings to this network share.
```

Cause:

Windows does not allow multiple SMB logins to the same server/IP using
different credentials at the same time. If `\\192.168.31.70\HomeDir_xuke` is
connected as one user, Windows may refuse `\\192.168.31.70\Data0_xuke` as a
different user.

Fix:

```cmd
net use
net use \\192.168.31.70\* /delete
net use Z: \\192.168.31.70\Data0_xuke /user:xuke PASSWORD
```

Also clear saved credentials:

```text
Control Panel -> Credential Manager -> Windows Credentials
```

Delete entries related to:

```text
192.168.31.70
```

Then reconnect.

## Windows Error: Need Permission To Write

Windows may show:

```text
Destination Folder Access Denied
You need permission to perform this action.
```

If `smb.conf` has `writable = yes`, the most common cause is Linux filesystem
permissions.

Example problem found here:

```text
/mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output
```

was owned by:

```text
haodong:haodong
```

and had mode:

```text
drwxrwxr-x
```

The SMB connection was authenticated as `xuke`, so Linux refused writes because
`xuke` was neither the owner nor a writable group member.

Inspect permissions:

```bash
ls -ld /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output
getfacl -p /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output
id xuke
```

Quick ACL fix for one directory tree:

```bash
sudo setfacl -R -m u:xuke:rwx /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output
sudo setfacl -R -m d:u:xuke:rwx /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output
sudo systemctl restart smbd
```

The first command gives `xuke` access to existing files/directories.

The second command sets a default ACL so new files and directories created
under that tree inherit `xuke` write access.

Test as Linux user:

```bash
sudo -u xuke bash -lc 'touch /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output/.xuke_write_test && rm /mnt/data_0/xuke/from_haodong_data/esp32/aaa_ai_output/.xuke_write_test'
```

Test through SMB:

```bash
smbclient //127.0.0.1/Data0_xuke -U 'xuke%PASSWORD' -m SMB3 \
  -c 'cd xuke/from_haodong_data/esp32/aaa_ai_output; put /etc/hostname .smb_write_test; del .smb_write_test'
```

## Group-Based Fix

If many files are owned by group `haodong` and have group write permission,
another fix is to add `xuke` to that group:

```bash
sudo usermod -aG haodong xuke
sudo systemctl restart smbd
```

Check:

```bash
id xuke
```

Important: Existing user sessions may not pick up new group membership until
they log out and log back in. Restarting `smbd` helps new SMB sessions use the
new group list.

## Samba Config Options For Permission Behavior

For private writable shares, these can be useful:

```ini
[Data0_xuke]
    path = /mnt/data_0
    browseable = yes
    writable = yes
    valid users = xuke
    create mask = 0664
    directory mask = 0775
```

If you want every file created through this share to become owned as `xuke`,
you can use:

```ini
    force user = xuke
```

Be careful with `force user`; it changes ownership semantics and may surprise
other Linux users. Prefer ACLs or Unix groups when multiple local users share
the same data.

## Firewall Notes

If another machine cannot connect at all, check firewall and ports.

Samba commonly uses:

```text
TCP 445
TCP 139
UDP 137
UDP 138
```

On Ubuntu with UFW:

```bash
sudo ufw allow Samba
sudo ufw status
```

## Current Machine Example

Share configured:

```ini
[Data0_xuke]
    path = /mnt/data_0
    browseable = yes
    writable = yes
    valid users = xuke
```

Windows path:

```text
\\192.168.31.70\Data0_xuke
```

Known existing shares:

```text
HomeDir_xuke    -> /home/xuke
HomeDir_haodong -> /home/haodong
Data_xuke       -> /home/xuke/data
Data_haodong    -> /home/haodong/data
Data0_xuke      -> /mnt/data_0
```

Useful verification commands:

```bash
testparm -s
systemctl is-active smbd
sudo pdbedit -L
smbclient -L //127.0.0.1 -U 'xuke%PASSWORD' -m SMB3
```

## Fast Checklist

1. Add share section to `/etc/samba/smb.conf`.
2. Run `testparm -s`.
3. Ensure SMB user exists with `sudo pdbedit -L`.
4. Reload or restart `smbd`.
5. Test locally with `smbclient`.
6. Map from Windows with `\\SERVER_IP\SHARE_NAME`.
7. If Windows says credentials conflict, run `net use \\SERVER_IP\* /delete`.
8. If Windows says permission denied, check Linux `ls -ld`, `getfacl`, and `id`.
9. Fix Linux write permissions with ACLs, groups, or ownership.
10. Restart `smbd` after group membership changes.
