---
name: fix-codex-sandbox-git-symlink
description: Diagnose and fix Codex sandbox failures caused by repositories whose `.git` path is a symbolic link or indirection outside the current workspace root. Use when Codex reports sandbox or restricted-mount failures on a Git tree, especially in Android/Linux SDK trees managed by `repo`, where opening the session at a subdirectory such as `kernel/` leaves the real Git metadata under a parent `.repo/projects/...` path.
---

# Fix Codex Sandbox Git Symlink

## Overview

Use this skill when Codex can read the source tree but sandbox setup fails because Git metadata lives outside the allowed workspace root. The common pattern is a large SDK opened at a subdirectory while `.git` resolves to a parent-managed `repo` metadata directory.

## Workflow

1. Confirm whether the failure is really about sandbox path resolution, not Git ownership or permissions.
2. Resolve the real `.git` target from the current working tree.
3. Compare the workspace root with the real Git metadata path.
4. If the `.git` target escapes the workspace root, reopen Codex at the nearest common ancestor that contains both the source tree and the resolved Git metadata.
5. Avoid patching `.git` or using `safe.directory` as the primary fix unless the problem is independently confirmed to be a Git ownership issue.

## Quick Diagnosis

Run these checks from the current tree:

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
stat -c '%n -> %F' .git
readlink -f .git
```

Interpretation:

- If `.git` is a real directory inside the workspace root, this skill is probably not the right fix.
- If `.git` is a symlink and `readlink -f .git` points outside the current workspace root, the sandbox failure is likely caused by the workspace being opened too deep.
- In `repo`-managed trees, the usual target is something like `.repo/projects/<subtree>.git`.

## Correct Fix

Do not only `cd` to another directory inside the same Codex session. That does not change the session’s workspace root.

Instead:

1. Close the current Codex session.
2. Reopen Codex from the nearest common ancestor that contains:
   - the working source subtree
   - the resolved `.git` target
3. Re-enter the source subtree after the new session starts.

For `repo`-managed Android/Linux SDK trees, that usually means:

- wrong session root: `.../kernel`
- correct session root: `.../SDK-root`

## Common Misdiagnoses

- `git config --global safe.directory ...`
  - This fixes Git ownership checks, not sandbox mount boundaries.
- Changing shell `cwd` only
  - This does not widen the existing session’s allowed workspace root.
- Editing the `.git` symlink
  - Risky in `repo` trees and usually unnecessary.
- Treating it as a plain permissions problem
  - If the resolved `.git` target is outside the root, the core issue is workspace scope, not file mode bits.

## When To Read More

Read `references/repo-git-symlink-patterns.md` when the tree appears in multiple absolute paths, when `.git` resolves into `.repo/projects/...`, or when you need to explain the difference between session root, shell `cwd`, and Git metadata location.
