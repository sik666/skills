# Cross-user Codex session migration

## When to use this workflow

Use it when a source session belongs to another Unix user or uses a provider that
the current login will not display. A session can consist of many
`rollout-*.jsonl` fragments; copying one file may create an incomplete history.

The migration script copies every source fragment with the specified thread ID,
creates a new destination thread ID, and changes only the copied session metadata
to the requested destination provider. It never changes the source history.

## Required inputs

- Source home directory, such as `/home/haodong`
- Destination home directory, such as `/home/xuke`
- Source thread ID
- Destination provider, normally `openai` for the current OpenAI login
- A display title

The destination must already contain `.codex/state_5.sqlite`. The script uses its
schema and will not create an empty Codex database.

## Preview, then apply

Preview is read-only and reports the number and combined size of rollout segments:

```bash
python3 scripts/copy_cross_user_session.py \
  --src-home /home/source_user \
  --dst-home /home/target_user \
  --thread-id 019fcb59-3220-7e41-89db-843b6c25fed1 \
  --target-provider openai \
  --title "dmabuf创新路线"
```

After confirming the preview is the intended session, add `--apply`:

```bash
python3 scripts/copy_cross_user_session.py \
  --src-home /home/source_user \
  --dst-home /home/target_user \
  --thread-id 019fcb59-3220-7e41-89db-843b6c25fed1 \
  --target-provider openai \
  --title "dmabuf创新路线" \
  --apply
```

The script writes a destination backup directory named
`backup-YYYYmmdd-HHMMSS-cross-user-session` before changing state. It prints the
new thread ID and final rollout path. Reload the VS Code window afterward.

## What the script changes

For each matching rollout file, the target copy retains its standard filename
shape and date directory. The first `session_meta` record receives the new thread
ID and target provider. All original conversation records stay unchanged.

The target `threads` row is cloned from the source row with a new ID, target
rollout path, target provider, title, name, and current recency. The target index
gets exactly one `{id, thread_name, updated_at}` line.

## Limits and recovery

This is a local history migration, not a supported way to have two providers
share a live resumable chat. Never point a target database directly at a source
rollout tree or symlink it as a substitute for migration.

If the copied chat is not visible after reload, check that the target row and all
copied `session_meta` records have the same `model_provider` as the active login.
If a migration fails, remove only the new target thread/files after inspecting the
backup; do not alter the source history.
