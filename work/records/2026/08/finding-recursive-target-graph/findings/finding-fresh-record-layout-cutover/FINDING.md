# Finding: the next v11 authority must start on the permanent record layout

## Observed

The v11 protocol and WS-6 design use permanent canonical dossiers under
`work/records/YYYY/MM/...` plus optional human `work/open/...` symlinks, but
this repository still operates under its older `AGENTS.md` rule requiring
ephemeral `work/finding-*` folders. Current trial Messages consequently carry
references to the old paths.

Moving folders during the live schema-14 trial would either break immutable
published references or require permanent compatibility aliases. Continuing
to create more old-style dossiers makes the eventual cutover worse.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** Finish the current
same-schema request batch (W77, W74 and W71), run its full verification and
checkpoint it. Then start the next v11 schema/authority fresh rather than
migrating the trial database.

At that boundary:

- adopt canonical `work/records/YYYY/MM/<stable-record>/` dossiers;
- create optional relative `work/open/<friendly>` symlinks only for human
  sweeping;
- update `AGENTS.md` so new findings, bindings and communications use the
  permanent record path and no longer describe dossiers as ephemeral;
- retire the old trial authority after its checkpoint rather than pretending
  its immutable old-path references were rewritten;
- recreate only still-relevant open/parked Work in the fresh authority, with
  canonical record bindings and current decisions;
- do not carry obsolete trial messages, accidental queue state, or old path
  aliases into the new authority.

The durable v11 design record must remain available through the cutover. The
exact filesystem relocation/cleanup set is resolved from the checkpointed
tree before any move; no broad or recursive deletion is inferred from this
ruling.

The old `AGENTS.md` policy remains active until the checkpoint is complete.
Changing it early would leave agents following the new rule while active Work
and references still use the old one.
