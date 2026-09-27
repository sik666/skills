---
name: fix-codex-workspace-root-for-repo-git-symlink
description: Diagnose and fix Codex sandbox failures caused by opening a `repo`-managed source subtree too deep, where `.git` is a symlink to metadata outside the current workspace root. Use when Codex reports restricted-mount, sandbox path, or read-only mount failures on trees such as `kernel/`, `u-boot/`, or `device/...` inside a larger SDK whose real Git metadata lives under a parent `.repo/projects/...` directory.
---

# Fix Codex Workspace Root For Repo Git Symlink

## Overview

Use this skill when Codex can access source files but sandbox setup fails because the current session was opened at a subtree whose `.git` resolves outside the workspace root. The correct fix is usually to reopen Codex at a higher directory, not to rewrite `.git`.

## Workflow

1. Confirm the current source tree and the real `.git` target.
2. Separate `cwd`, workspace root, and resolved Git metadata path.
3. Check whether `.git` escapes the current workspace root.
4. If it does, reopen Codex at the nearest common ancestor that contains both the source subtree and the resolved Git metadata path.
5. Avoid treating this as a Git ownership or file-permission problem unless independent evidence points there.

## Quick Diagnosis

Run these checks from the affected tree:

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
stat -c '%N' .git
readlink -f .git
```

Interpret the result in this order:

- If `.git` is a real directory under the session root, this skill is probably not the right fix.
- If `.git` is a symlink and resolves into a parent `.repo/projects/...` path, the tree is a `repo`-managed checkout.
- If the resolved `.git` path is outside the current Codex workspace root, sandbox setup can fail even though Git itself works in a normal shell.

## Correct Fix

Do not rely on `cd` alone. Changing shell `cwd` inside an existing session does not widen the workspace root that Codex is allowed to mount.

Instead:

1. Close the current Codex session.
2. Reopen Codex from the nearest common ancestor of:
   - the source subtree you want to work in
   - the resolved `.git` target
3. After the new session starts, `cd` back into the source subtree if you want to work there.

For `repo`-managed SDKs, the good session root is usually the SDK root:

- wrong session root: `.../kernel`
- correct session root: `.../SDK-root`

## Concrete Pattern

Typical layout:

```text
SDK-root/
  .repo/projects/kernel.git
  kernel/.git -> ../.repo/projects/kernel.git
```

If Codex is opened at `SDK-root/kernel`, the real Git metadata lives outside the session root. Sandbox or restricted-mount setup may then fail on `.git`.

If Codex is opened at `SDK-root`, both paths are inside the same workspace root and the failure usually disappears.

## Non-Fixes

These are common detours and should not be the primary remediation:

- `git config --global safe.directory ...`
  - fixes Git ownership checks, not workspace-root scope
- `chmod` or `chown` on the tree
  - fixes file access issues, not a root that is too narrow
- editing the `.git` symlink in a `repo` checkout
  - risky and usually unnecessary
- `cd ..` inside the same active session
  - changes `cwd`, not the Codex workspace root

## Deliverable

When using this skill, the answer should state:

1. the current source path
2. the resolved `.git` target
3. whether that target is outside the current workspace root
4. the exact directory from which Codex should be reopened

## Example

If the current working tree is:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113/kernel
```

and `.git` resolves to:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113/.repo/projects/kernel.git
```

then the correct Codex session root is:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113
```
