# Finding: retire v10 code and data without a fallback path

## Confirmed direction — 2026-08-17

**Requested by Slawomir during the v11 cutover trial.** Once v11 messaging has passed its live no-fallback gate, clean up the protocol-10 code and data so participants cannot silently fall back to the retired system.

This is post-cutover Work. It must not remove the current safety channel while W2 remains open, and it does not authorize deletion merely because the Work was filed. The destructive scope is enumerated and reviewed at execution time.

## Required outcome

- Stop and remove v10 readiness consumers, bridge inputs, client launch paths, and operational configuration that could continue accepting v10 work.
- Remove retired v10 implementation/deployment artifacts and mailbox data selected by the approved cleanup inventory; leave no alias or documented command that resolves back to them.
- Update active agent/operator guidance to name only the certified v11 distribution and coordination authority.
- Preserve durable historical evidence whose purpose is to explain earlier releases or decisions; history is not an executable fallback.
- Refuse partial cutover: if a participant, service, configuration, or required v11 recovery path still depends on v10, cleanup stops before deletion.
- Prove the human, Codex, and ACP participant paths restart and coordinate through v11 alone after cleanup.

## Gate

W2 (`Make v11 messaging sufficient to retire v10`) must close satisfying and Slawomir must explicitly approve the concrete retirement inventory before any destructive step. Cleanup is forward-only; recovery fixes v11 rather than resurrecting v10.

## Accountable sub-jobs

W99 contains four separately reviewable Work tracks:

1. retire v10 runtime/source code and tests that exist only to operate protocol 10;
2. retire v10 deployed executables, aliases, process/configuration paths, and mailbox data;
3. rewrite the active README, public documentation, and architecture picture for the v11-only system; and
4. replace the protocol-10 `EFFECTIVE-BATON.md` operating instructions with the confirmed v11 workflow.

Each child has a top-level permanent dossier because this record already occupies the repository policy's maximum finding depth. Their records explicitly link back to W99; the filesystem is not nested a third time.
