# Migration config and snapshot publication crash-durability

Status: **implemented for protocol 7**.

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

**Window 1 — config staging**, in `RUNBOOK-offline-migration.md`. The rollback
copy is taken **first**, `baton.json` → `baton.json.gen2`, under a name
`os.replace` cannot consume, and synced. The staged file is fsynced **before**
the rename and the containing directory **after** it.

**Window 2 — snapshot parent entry**, in `baton_v6.py`. `_take_snapshot`
fsyncs the parent directory when it creates `dest`, so the directory's own
entry is durable and not only its contents. Skipped when `dest` already
exists, where the entry is already durable.

**Source config preservation** is satisfied more strongly than the contract
asked. `migrate` reconstructs the accepted pre-migration config by setting
`generation` and `protocol_version` back, and refuses unless that reproduces
the recorded `config_sha256`; the reconstructed config is what is written into
the snapshot. That proof is also what makes the snapshot restorable at all —
an earlier version paired the old database with the *new* config, producing an
artifact neither executable could open.

## Regression

`test_snapshot_persists_its_own_directory_entry` records every fsynced
`(dev, ino)` and asserts the parent's is among them, so it fails if the sync
is dropped rather than passing vacuously.

This hardening is for the offline migration capability. It does not block the
availability-first fresh-instance cutover and does not mutate the live
authority.
