# Cross-user Codex session migration

## Destination configuration

Identify the destination OS home and the Codex directory actually used by its
client. Usually these are `/home/target_user` and `/home/target_user/.codex`, but
`CODEX_HOME` may select another directory. The migration script accepts
`--src-codex-home` and `--dst-codex-home` to override its OS-home-based defaults.
Both histories must already contain `state_5.sqlite`; do not create an empty
database as a substitute or guess a different schema version.

Use the Codex executable shipped with the destination VS Code extension where
possible. Inspect the destination client's effective configuration with:

```bash
python3 scripts/codex_history_api.py \
  --codex-home /home/target_user/.codex \
  --codex-bin /path/to/destination/codex \
  --cwd /path/to/destination/workspace
```

The helper initializes a bounded, temporary stdio app-server, uses `config/read`,
prints only the effective provider and relevant verification results, and stops
the process. It does not call a model or resume a conversation. Codex may maintain
its normal caches/logs during these diagnostic requests.

Pass repeated `--config KEY=VALUE` only when matching the destination client's
actual startup context; these are not tools for forcing a mismatch to disappear.
`--profile NAME` is available only if that Codex build accepts profiles with
`app-server`. Some builds restrict profiles to runtime commands and will reject
it. In that case query `config/read` from the actual destination client first,
then mirror its verified effective provider/settings via `--config`; do not
silently ignore the profile, parse it with regex, or guess its selected provider.
Keep credentials out of command lines/output. The helper sets `CODEX_HOME` only
for its subprocess, not the user's environment.

Provider IDs are exact, case-sensitive identifiers, not brand or login labels.
For example, a config can define both `model_providers.OpenAI` and
`model_providers.custom` while selecting `model_provider = "custom"`. In that
case the normal destination provider is `custom`, not `OpenAI` or `openai`.
An earlier successful import can corroborate configuration, not replace it.
If `config/read` omits the optional provider setting, the helper uses Codex's
documented `openai` default. If the API fails or returns an invalid value, stop
before copying rather than guessing.

## Preview, then apply

A thread can have multiple rollout segments. The migration copies all discovered
segments with that ID and preserves the source conversation records. Preview
does not copy/register a thread or create migration backups; its config query
can update normal Codex caches. It reports the effective provider, display title,
segment count, and byte total:

```bash
python3 scripts/copy_cross_user_session.py \
  --src-home /home/source_user \
  --dst-home /home/target_user \
  --thread-id 019fcb59-3220-7e41-89db-843b6c25fed1 \
  --codex-bin /path/to/destination/codex \
  --cwd /path/to/destination/workspace \
  --title "Imported session"
```

The provider defaults to `config/read`. Optional `--target-provider` must match
it. `--allow-provider-mismatch` is only for an explicitly intentional import to
an inactive provider, not a routine workaround. Default display title prefers
the source `threads.name`, then `threads.title`, then the source ID.

Once the preview identifies the intended source, repeat the same command with
`--apply`. The apply invocation generates a new ID; the preview ID is provisional.
The script backs up state/index before writing and reports the actual target ID,
backup location, and final rollout path. Use that reported ID for all subsequent
verification and repairs; do not import again just to refresh the UI.

The copied filenames retain the `rollout-*.jsonl` shape. Each first `session_meta`
gets the new ID and provider. The cloned target `threads` row receives the new
ID, rollout path, provider, title/name, and current recency; the index receives
one `{id, thread_name, updated_at}` entry. Original conversation bodies and source
state/index remain unchanged.

## Verify what actually works

After checking the destination row/index and every copied metadata record, run:

```bash
python3 scripts/codex_history_api.py \
  --codex-home /home/target_user/.codex \
  --codex-bin /path/to/destination/codex \
  --cwd /path/to/destination/workspace \
  --thread-id NEW_IMPORTED_ID
```

This checks `thread/list` with `modelProviders: [effective_provider]` and
`useStateDbOnly: true`, following `nextCursor` until the ID is found. It then
checks metadata with `thread/read` and all history pages using
`thread/turns/list` with `itemsView: "full"`. A pagination limit or API error is
an incomplete verification, never success. For unusually large histories adjust
`--timeout` or `--max-pages` after inspecting the reported error.

APIs are version-dependent. Inspect the destination executable's generated
schema/help if a method is unsupported. Older builds may require
`thread/read` with `includeTurns: true`; newer paginated histories should use the
turn/item pagination APIs. Do not assume a single successful read proves every
segment is accessible. Empty history is possible, but unexpected zero counts
require comparison with the source rather than being dismissed.

For VS Code, direct navigation to the actual imported ID can verify opening:

```bash
code --open-url 'vscode://openai.chatgpt/local/NEW_IMPORTED_ID'
```

Use the correct destination OS user and VS Code instance. An accepted URI command
is not itself proof that the conversation opened. Confirm via the extension's
resume-success log for that ID or the user's observation. Report the stages
separately: registered on disk, listed/readable through the API, opened in the UI.

## Invisible copies and recovery

Work on the existing imported ID. Compare the effective provider with the target
row and every copied `session_meta`, then reproduce the actual list/read error.
Some clients use no provider filter; provider mismatch is not the universal
explanation for every missing conversation. Check the client's actual filters
(workspace/cwd, archive, source kind), pagination, configuration context, and logs.

If provider repair is needed, back up destination state and each target file to
be changed first, and update only the imported copy with coherent metadata.
Do not alter the source or global provider configuration. Undocumented extension
catalogs such as `sqlite/codex-dev.db` are caches, not the primary success test;
inspect their current schema/client behavior before any narrowly justified repair.
Do not clear broad caches or write every local database as a speculative fix.

Do not blindly copy `thread_history_*.sqlite` projections, checkpoints, or byte
offsets between IDs. They may refer to specific rollout segments. Let supported
Codex reads materialize history; if they fail, diagnose the returned error rather
than inventing projection records. Stop and report the exact failed check when
safe supported diagnostics do not resolve it.

On migration failure, inspect the backup and partial results. Cleanup must target
only the newly created ID/files; never restore an entire live database over newer
unrelated conversations or alter source history. A symlink/database path pointing
to another provider's live rollout is not a substitute for migration.

## Official API/config references

- [Configuration reference](https://developers.openai.com/codex/config-reference/)
- [App-server configuration and history APIs](https://developers.openai.com/codex/app-server/)

These document configuration layering and history APIs, not a supported contract
for direct SQLite migration. Verify local schema compatibility before mutation.

For script changes, run `python3 scripts/test_history_migration.py -v`. Its fake
histories and mocked API pages are isolated from real user state; separately
verify config/history reads using the destination client's actual executable.
