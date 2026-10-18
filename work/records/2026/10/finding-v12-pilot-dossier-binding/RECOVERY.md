# Retained v12 instance: compatibility, backup and restore — W321688

The bounded procedure the FINDING asks to be PINNED. It is written for one
retained pilot instance and nothing broader.

## Who owns what

**Slawomir is the production backup/restore authority and the sole canonical Git
owner.** No agent — reviewer, implementer or worker — may copy, restore or open a
live authority, or clear a runtime hold. This claim demonstrated the procedure on
disposable deterministic fixtures only; no real instance was read, copied or
restored, and nothing here selects a production backup operation.

**A source Git commit is not this backup.** The commit carries the code. The
recovery set carries the state the code was acting on. Restoring one without the
other restores a deployment that will act on facts it never recorded.

## The compatibility boundary, stated before the procedure

This authority does not migrate, in either direction. `work_dossier` and
`work_dossier_evidence` arrive at **schema 6**; a store at 5 holds no column,
label or convention a locator could be read out of, so `Authority.open` refuses
it **read-only**, names the file, and changes not one byte of it. Deletion is the
operator's act and never this build's.

So a retained authority written before this change is readable only by the build
that wrote it. That is the documented boundary, not a silent loss — and it is why
the recovery set records **which build** wrote it, not only the bytes.

## The recovery set — one consistent whole

`baton-v12-stack record recovery-manifest --instance <instance.json>` digests it.
A member missing makes the manifest refuse: a partial set is not a recoverable
deployment.

| member | why it is in the set |
| --- | --- |
| `authority_store` | Work identity, assignments, receipts, operations, and the dossier binding |
| `job_store` | submissions, stages, episodes, allocations |
| `control_store` | offers, attempts, runtime observations, custody |
| `deployment` | the configuration those rows were written under |
| `identity` | build stamp, version, distro digest — WHICH build wrote them |
| `runtime` | the distro file count and digest the instance was prepared with |

Immutable inputs, retained outputs and provider context live under the
instance's own `state`/`logs`/workspace roots; the manifest records the
destination so they travel with it rather than being reconstructed.

**Sidecars are named, not skipped.** The manifest reports any `-wal`, `-shm` or
`-journal` beside each store. A WAL store whose `-wal` holds committed
transactions is not fully described by its main file, so a cut taken while a
writer is attached can restore a deployment missing its newest commits.

## Taking a cut

1. **Stop admissions.** Not "stop the supervisor" — `tools/stack.py` stops
   supervisor processes and explicitly not every Job runtime.
2. **Positively account for every runtime and launch.** Stopping the manager or
   releasing a claim is not writer cessation. If any runtime state is unknown,
   the gate is retained and no cut is selected.
3. **Then** run `recovery-manifest` and copy the whole set with it.
4. Keep the manifest beside the copy. It is what makes a later restore checkable.

No guessed SQLite file-copy recipe, no automatic migration, no `VACUUM INTO`
improvisation: the cut is taken with the writers accounted for, which is what
makes a plain copy coherent.

## Admitting a restore

`baton-v12-stack record recovery-check --manifest <set.json> --root <where>`
reports and **refuses**; it never admits anything. Three refusals, each a
different way a restore goes wrong:

- **A missing, unreadable or changed member.** Every member must be present at
  its recorded digest. One store from a different cut than its siblings is an
  incoherent deployment, refused before anything opens it.
- **A possible old writer.** If the original instance destination still exists,
  or sidecars differ from those the manifest recorded, this cannot establish that
  the deployment which wrote these bytes has stopped. **Uncertainty holds.** Two
  writable instances over one state is the duplicate-effect failure the whole
  adoption boundary forbids, and "probably fine" is not an accounting.
- **A schema this build does not speak.** Read from the **restored store's own
  metadata**, through `Authority.stored_identity` — the authority's own
  read-only probe, the one `open` itself uses before it decides anything. The
  manifest's recorded version is compared against it rather than trusted in its
  place, so a manifest that disagrees with the bytes beside it is itself a
  fault. The answer is still available before anything is opened writably.

  **AND THE PROBE READS A COPY.** `mode=ro` is SQLite's guarantee about the
  database, not about its coordination files: reading a WAL store may create or
  maintain a `-shm`. So the store and its sidecars are copied to scratch, the
  copy is probed, and the restored set is left untouched — and
  `unchanged_after_observation` re-reads every member and sidecar afterwards to
  **prove** it rather than assert it. A check that modified the set it had just
  certified unchanged is a real defect this command used to have.
- **A missing or substituted instance selector.** The restored `instance.json`
  is a **required member**, verified against the selector document the manifest
  recorded. Absent, unreadable, malformed, or naming a different
  `authority_uuid`, it is a fault and the set is refused. Review
  2026-10-18T09-12-00Z reproduced both halves of this being accepted: with the
  selector deleted, and with it carrying a different UUID, `recovery-check`
  returned a clean `faults: []`. A set whose own instance document is gone or
  describes somebody else's deployment is not restorable, and discovering that
  after admission is too late.

**EXACTLY ONE REWRITE IS SUPPORTED, and it is named rather than tolerated.** A
restore that lands somewhere else may rewrite the selector's `destination` to
the root it actually landed under — and nothing else. That is reported as
`relocated` and is clean. A selector rewritten to any third path, or differing
in any other member, is `changed` and refused; the report names the members that
differ. This is why the manifest carries the selector **document** and not only
its digest: a digest alone cannot tell a relocation from a substitution, and the
only honest answer available from a digest would be to refuse every restore that
moved.

The manifest is therefore `baton.v12.instance-recovery-set/3`. A `/2` manifest
carries no selector document and is refused rather than checked by digest — the
same no-migration direction as the store itself.

A clean report is the **precondition** for an operator's admission, not the
admission. Admitting it still requires that every runtime and launch of the
previous instance is positively accounted for.

## Readback is acceptance

After a restore, the authority must still answer: its own UUID, the Work's
canonical dossier, the evidence that dossier cites, the act that created the
Work, the Work's projection and the operation journal. Rehearsed deterministically
in `tests/tools/test_dossier_command.py`
(`test_the_RESTORED_authority_still_answers_identity_record_and_history`).

## Evidence a restored record still cites

`record verify --work <id> --root <root>` resolves every citation and
distinguishes four outcomes, because they are not one fact: `present`, `absent`,
`unreadable` and `changed`. Reporting a permission problem as a missing file
would send an operator to restore something that was never lost. A dossier citing
nothing is refused rather than called intact.
