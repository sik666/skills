# Repo Git Symlink Patterns

## Problem Pattern

Large Android/Linux SDK trees managed by `repo` often expose a subtree such as `kernel/`, `u-boot/`, or `vendor/...` as a Git working tree whose `.git` is not a local directory.

Typical shape:

```text
SDK-root/
  .repo/projects/kernel.git
  kernel/.git -> ../.repo/projects/kernel.git
```

If Codex is opened with workspace root at `SDK-root/kernel`, sandbox setup may only allow that subtree. The real Git metadata then lives outside the allowed root, so restricted-mount or sandbox setup fails even though `git` from a normal shell still works.

## Distinguish Three Paths

Always separate these concepts:

1. shell `cwd`
   - where commands run right now
2. Codex session workspace root
   - what the sandbox is allowed to see
3. resolved Git metadata path
   - where `.git` actually points

The bug occurs when:

- `cwd` is inside the tree
- workspace root is too narrow
- resolved `.git` path is outside that root

## Minimal Command Set

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
stat -c '%n -> %F' .git
readlink -f .git
```

Use the output to answer:

1. Is `.git` a directory or a symlink.
2. If it is a symlink, where does it resolve.
3. Is the resolved target still under the session workspace root.

## Correct Remediation Rule

Open the Codex session at the nearest common ancestor of:

- the source subtree you want to work on
- the resolved Git metadata path

That ancestor is often the SDK root, not the inner repo such as `kernel/`.

## Example

Bad session root:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113/kernel
```

Resolved `.git` target:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113/.repo/projects/kernel.git
```

Good session root:

```text
/mnt/.../LubanCat_Linux_rk3588_SDK_20260113
```

## Non-Fixes

These do not solve the real problem when the root cause is workspace scope:

- `git config --global safe.directory ...`
- `chmod` or `chown` on the tree
- editing `.git` symlinks in a `repo` checkout
- `cd ..` inside the same active Codex session

They may solve different problems, but not “sandbox cannot follow `.git` outside the allowed root”.
