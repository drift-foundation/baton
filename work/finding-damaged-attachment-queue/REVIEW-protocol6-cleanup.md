# Review: protocol-6 dead-code removal

Status: **changes requested**.

Reviewed against commit `112b76e03162be658d27c272338eb7562134d650`.

The code deletion boundary is sound on this pass. In particular,
`_read_config_bytes_at` remains live for snapshots,
`quarantine_attachment_instance` remains the CLI ceremony entry point, the
shipped protocol-7 schema text is unchanged, and the rebuilt artifact matches
the source recorded in `DISTRIBUTION.json`. Removing the public
`migrate --snapshot-dir` flag is accepted: Slawomir explicitly included that
surface in the dead-code-removal scope. The corresponding existing-test edit
is likewise case-specifically authorized by that instruction.

## Required corrections

1. `AGENTS-MAILBOX-PROTO.md` still presents the current coordination contract
   as “v6” and says the channel is running protocol 6. It is the distribution's
   pinned protocol document and must describe protocol 7. Update its manifest
   hash after correcting it.
2. `Store` still says it is an open handle on a “protocol-6 instance.” Make
   that current and protocol-neutral (or protocol 7), then rebuild/re-pin the
   source and artifact.
3. `work/finding-maintenance-entry-claim-race/FINDING.md` says at the top that
   the protocol-6 fallback is moot, but its final two paragraphs still record
   that fallback as a live deferred limitation and prescribe work before a
   future in-place cutover. Remove or explicitly historicalize the
   contradiction.
4. `work/finding-crash-durable-migration-publication/FINDING.md` still says
   the current `migrate` reconstructs and digest-proves a prior-protocol
   config, and closes by calling this an offline-migration capability. Neither
   is true after this deletion. Keep the historical lesson, but do not present
   removed behavior as live.
5. `work/finding-damaged-attachment-queue/FINDING.md` still says “the in-place
   machinery still ships” and calls it the current correct procedure for
   migrating a copy. It also contains older `migrate --snapshot-dir` results.
   Preserve the historical review record where useful, but explicitly
   time-scope it and make the current removal unambiguous; no present-tense
   statement may claim that the deleted migration path still exists.

After those corrections, rerun the full suite, the five adversarial tests,
`git diff --check`, distribution hash verification, and live `doctor` with the
rebuilt executable. No protocol-6 migration implementation or schema-text
change is requested.

## Reviewer checks completed before response

- `python -m py_compile baton_v6.py`: pass.
- Removed-symbol search: no live migration-plumbing reference found.
- Current artifact/source hashes match `DISTRIBUTION.json`.
- `git diff --check`: pass.

## Review round 2

Status: **approved**.

All five requested current-contract/documentation corrections were applied.
The protocol document now names v7, the Store description is protocol-neutral,
the two finding contradictions are historicalized, and the damaged-attachment
finding states unambiguously that the in-place machinery and
`migrate --snapshot-dir` were removed.

Independent final verification:

- Full suite: **316 passed**.
- `git diff --check`: pass.
- Artifact, source, and protocol-document hashes match `DISTRIBUTION.json`.
- Rebuilt executable: `baton 2.0.0 (protocol 7)`.
- Live authority with rebuilt executable: `doctor ok: true`, `problems: []`.

The separate zero-byte body validation defect is recorded in
`work/finding-nonempty-message-bodies/FINDING.md`; it is not part of this
cleanup and no ad-hoc patch is requested here.

## Review round 3

Status: **changes requested**.

The README additions documenting `quarantine-attachment`, `snapshot`, and the
refusing `migrate` gate are in scope and should remain. Two corrections are
required:

1. README says “`migrate` is an audited gate, not a capability.” The command
   still requires the participant's `config` capability. State that
   requirement explicitly and use wording such as “not a migration path” or
   “not a conversion capability” for the intended distinction.
2. `_enforce_gates_in_txn` still permits
   `ceremony == "migrate" and row["protocol"] == PROTOCOL_VERSION - 1`, with a
   comment saying migration is the one transaction allowed to start on the
   previous protocol. `open_instance` now makes that branch unreachable, but
   it is remaining prior-protocol migration code. Remove the exception and
   require `row["protocol"] == PROTOCOL_VERSION` for every transaction. Do not
   alter the shipped schema text.

Rebuild/re-pin after the source correction and rerun the same verification.

## Review round 4

Status: **approved**.

README now describes `migrate` as an audited refusal rather than a conversion
capability and states both its `config` capability and maintenance-gate
requirements. `_enforce_gates_in_txn` now requires the current protocol for
every transaction; no prior-protocol ceremony exception or
`PROTOCOL_VERSION - 1` reference remains.

Independent final verification on the exact round-3 tree:

- Full suite: **316 passed**.
- `git diff --check`: pass.
- Artifact, source, and protocol-document hashes match `DISTRIBUTION.json`.
- Live authority with the final rebuilt executable: `doctor ok: true`,
  `problems: []`.

The README command documentation and both untracked review/finding artifacts
are accepted for inclusion. The zero-byte-body finding remains unstarted.
