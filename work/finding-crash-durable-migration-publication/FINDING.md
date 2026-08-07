# Snapshot publication crash-durability

Status: **implemented for protocol 7; the migration half is moot.**

The 6 → 7 migration path and its offline runbook were removed after this
deployment moved to a fresh protocol-7 instance, so the config-staging window
described below no longer exists in the tool — there is no config staging to
get wrong. The snapshot fix is live and is what remains load-bearing.

Two durability windows existed in the offline migration path:

1. The runbook staged the target config with `json.dump` and `os.replace` but
   fsynced neither the staging file nor the mailbox directory. Its documented
   generation-2 backup referenced the staging pathname after replacement and
   therefore preserved no bytes.
2. `_take_snapshot` could create the snapshot directory with `os.makedirs` and
   then fsynced files and entries inside it. It did not fsync the parent
   directory holding the newly created snapshot-directory entry, so a crash
   could lose the rollback directory name after migration committed.

Required contract: configuration replacement and rollback publication must be
atomic and crash-durable at every directory boundary, and a verified source
config must be preserved before the target config is staged.

## As implemented

**Window 1 — config staging.** Fixed in the offline migration runbook: the
rollback copy taken first under a name `os.replace` cannot consume, the staged
file fsynced before the rename and the directory after it. That runbook and
the migration it described have since been removed, so this window is closed
by deletion rather than by the fix. Recorded because the underlying mistake —
a backup line naming a path the rename had already consumed, preserving
nothing — is worth not repeating anywhere else.

**Window 2 — snapshot parent entry**, in `baton_v6.py`. `_take_snapshot`
fsyncs the parent directory when it creates `dest`, so the directory's own
entry is durable and not only its contents. Skipped when `dest` already
exists, where the entry is already durable.

**Source config preservation — historical, removed with the migration.**
While `migrate` existed it reconstructed the accepted pre-migration config by
setting `generation` and `protocol_version` back, refused unless that
reproduced the recorded `config_sha256`, and wrote the reconstructed config
into the snapshot. `migrate` no longer does any of this; it is an audited
refusal with no snapshot of its own.

The lesson is why it was needed at all: the first version paired the old
database with the *new* config and produced an artifact neither executable
could open — a rollback artifact that could not roll back. Any future
migration must pair a snapshot's database with the config that matches it, and
prove the pairing rather than assume it.

## Regression

`test_snapshot_persists_its_own_directory_entry` records every fsynced
`(dev, ino)` and asserts the parent's is among them, so it fails if the sync
is dropped rather than passing vacuously.

What remains live is the snapshot fix, which belongs to the standalone
`snapshot` verb and is independent of any migration. It does not block the
availability-first fresh-instance cutover and does not mutate the live
authority.
