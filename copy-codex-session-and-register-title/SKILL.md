---
name: copy-codex-session-and-register-title
description: Migrate or restore a Codex session into another local user's history, including cross-provider copies. Use when a rollout must be copied, registered, and made visible under the destination provider rather than merely copying one JSONL file.
---

# Copy Codex Session and Register Title

Treat Codex history as a coordinated system: rollout files, a SQLite thread record,
and a session-index entry. Skills are local files and can be shared by an OS user;
chat threads are provider-scoped and need migration metadata.

## Choose the mode

- For a missing local index entry or a title-only change, update the existing thread
  and index entry; do not duplicate the rollout.
- For another Unix user, another Codex login/provider, or a same-directory import,
  use the cross-user script. It creates a distinct target thread and preserves the
  source unchanged.

## Cross-user and cross-provider migration

1. Identify the source home, destination home, source thread ID, destination
   provider, and requested title. Confirm the user authorizes the destination
   mutation and the potentially large file copy.
2. Run `scripts/copy_cross_user_session.py` without `--apply` first. Report its
   segment count and byte total.
3. Run it again with `--apply` only after the preview identifies the intended
   session. The script backs up destination state and index, copies every rollout
   segment for the thread, creates a new UUIDv7 thread ID, updates only each
   copied `session_meta` ID/provider, inserts a destination database row, and
   appends one index entry.
4. Validate the reported thread, index entry, and copied rollout files, then tell
   the user to reload the VS Code window.

Do not promise that a source account can continue to own a chat after a direct
filesystem reference. A symlink or a database-path rewrite is not a supported
cross-provider resume mechanism.

## Resources

- Read `references/guide.md` for the migration command and recovery details.

## Guardrails

- Do not rename rollout files to arbitrary titles; retain `rollout-*.jsonl` names.
- Do not mutate source rollout files, its database, or its index.
- Do not copy only the database row or only one rollout when the thread has
  continuation segments.
- Do not use `--apply` until the dry-run source ID, provider, segments, and size
  have been checked.
- The destination database and index must be backed up before mutation.
