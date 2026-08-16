# Ruling — participant-local draft storage

Draft storage is a TUI implementation detail and does not change protocol 9
or the authority schema.

Use the participant's explicit configured `projection_dir`, under a private
hidden namespace:

```text
<projection_dir>/.baton-tui/<participant>.json
```

The participant address grammar contains no path separator, but the
implementation must still construct the final component defensively rather
than accepting an arbitrary path.

## Why this location

- It is already explicit and participant-scoped in `baton.json`.
- Slawomir's live participant has a dedicated mailbox projection directory.
- It avoids silently writing private drafts under `$HOME`/XDG, which is a
  recurring sandbox/permission surprise in this deployment.
- It requires no config field, schema change, or protocol bump.
- `doctor` inventories only projection-shaped files in `projection_dir`; the
  hidden TUI subdirectory is outside that namespace and is not projection
  cache state.

Do not place drafts beside `mailbox.sqlite3`, where they would become an
unrecognized authority-directory artifact. Do not place them in a finding or
repository working tree. Do not infer a home-directory fallback.

## Failure and safety behavior

- Draft authoring requires a configured, existing, absolute
  `projection_dir`. If absent or unusable, explain how to configure it and do
  not pretend the draft is persistent.
- Create `.baton-tui` with mode `0700`; store the participant file with mode
  `0600`.
- Write a same-directory temporary file, flush/fsync, atomically replace, and
  fsync the directory. Never truncate the only good copy in place.
- Refuse symlink/reparse traversal and non-regular destination files.
- Parse strictly and fail closed on corruption; preserve the damaged file for
  diagnosis rather than overwriting it with an empty draft set.
- Never store authority credentials (there are none in protocol 9), message
  bodies outside the authored drafts, or unrelated projection content.

If a future deployment wants a different state root, add an explicit TUI
`--state-dir` override as a separate tool-surface decision. It is not needed
for this release and must not become a silent fallback.
