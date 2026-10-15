---
name: copy-codex-session-and-register-title
description: Migrate or restore a Codex session into another local user's history, including cross-provider copies. Use when a rollout must be copied, registered, and made visible under the destination provider rather than merely copying one JSONL file.
---

# Copy Codex Session and Register Title

Treat Codex history as a coordinated system: rollout files, a SQLite thread record,
and a session-index entry. Skills are local files and can be shared by an OS user;
history APIs can filter threads by provider, so copies need consistent migration
metadata. A database row alone does not prove that the client can list or open it.

## Choose the mode

- For a missing local index entry or a title-only change, update the existing thread
  and index entry; do not duplicate the rollout.
- If an imported copy is still invisible, diagnose that existing destination ID.
  Do not repeat the import or create another UUID merely because reload failed.
- For another Unix user, another Codex login/provider, or a same-directory import,
  use the cross-user script. It creates a distinct target thread and preserves the
  source unchanged.

## Cross-user and cross-provider migration

1. Identify the source home, actual destination Codex home, source thread ID,
   destination client executable/configuration context, and requested title.
   Read `references/guide.md` before migration or visibility troubleshooting.
   Confirm that the requested import authorizes the destination mutation and copy.
2. Run `scripts/copy_cross_user_session.py` without `--apply` first. Report its
   segment count and byte total. It resolves the destination provider using
   `config/read`; never infer it from an account label or copy the source provider.
   Provider IDs are case-sensitive: `custom`, `OpenAI`, and `openai` are distinct.
   Match the destination workspace, profile, runtime overrides, and `CODEX_HOME`.
3. Run it again with `--apply` only after the preview identifies the intended
   session. The script backs up destination state and index, copies every rollout
   segment for the thread, creates a new UUIDv7 thread ID, updates only each
   copied `session_meta` ID/provider, inserts a destination database row, and
   appends one index entry.
4. Check the destination row, index entry, and metadata of every copied segment.
   Run `scripts/codex_history_api.py` on the new ID to verify provider-filtered
   listing, metadata reads, and paginated history reads through the destination
   client's API. If the installed version lacks an API, inspect its schema and
   use a supported equivalent; report unverified checks instead of claiming success.
5. For VS Code imports, open the existing target ID directly using the local
   conversation URI in the guide, or have the user open it. Report registration,
   API readability, and UI opening separately. Claim UI success only after client
   evidence or user confirmation; reload alone is not validation.

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
- Do not bypass provider mismatch refusal unless the user intentionally requests
  an inactive destination provider; explain that active-provider visibility is
  then not guaranteed. Do not change global provider configuration to expose a copy.
- Do not blindly clone projection/checkpoint records or offsets, or modify
  extension catalogs as a default fix. Diagnose actual API/client errors first.
