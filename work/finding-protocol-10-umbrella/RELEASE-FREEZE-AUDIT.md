# Protocol-10 cross-team release freeze audit

Date: 2026-08-10

Reviewer: `baton.reviewer`

Decision: **approved by Slawomir on 2026-08-10**. Protocol 10 freezes for the
cross-team release after the current protocol-free corrections. The inventoried
schema-bound enhancements move together to a later protocol-11 boundary; they
do not delay this release.

## Outcome

Protocol 10 is a suitable schema/wire freeze point for the first cross-team
release. No known correctness repair requires another authority replacement
before lang, mariadb, query, pushcoin, and the other teams adopt it.

Freeze does not mean the product is finished. It means the remaining current
candidate work can ship as tool, CLI, TUI, documentation, and repository-layout
updates against the protocol-10 authority. A future protocol 11 is already
inventoried for additive workflow features; it should be one deliberate later
boundary, not rushed into this release.

## Evidence at the boundary

- current executable reports `baton 6.0.0 (protocol 10)`;
- the live authority reports protocol 10, generation 2, maintenance off,
  move status `none`, and `doctor` `ok: true` with no problems;
- protocol-10 `messages.publication_id` is `NOT NULL`, and `send`/`reply`
  publish through the shared publication path. The historical orphan-reply
  defect is therefore closed for the fresh authority and does not require a
  second repair cutover;
- immutable publication and notice audiences, scoped notices,
  multi-recipient directed publication, `part_name`, typed multipart content,
  participant-authorized reread, and read-only `wait` are already in the
  protocol-10 schema/contract;
- the active frozen-candidate review found tool/TUI defects, not schema or wire
  defects. The corrections must land before release, but they do not require
  replacing the authority.

`doctor` currently reports operational warnings for archived/unrecognized
files and one orphan projection cache. They do not make the authority damaged
and are not protocol defects.

## Known future schema boundary — protocol 11

The post-cutover inventory already groups all known schema-bound enhancements
into one future boundary:

1. durable decision obligations, reactions, and multi-recipient voting;
2. append-only claim progress;
3. targeted blocker relationships/events;
4. priority, queue ordering, and fairness;
5. durable per-participant dismissal, bulk selection, and Trash;
6. recorded privileged reads (the current read is authorized but not audited
   as a first-class protocol event);
7. presence leases.

These improve workflow visibility and inbox ergonomics. None repairs a known
protocol-10 data-integrity, authorization, delivery, or queue-liveness failure.
They therefore do not block the cross-team release. Their older findings may
still say “protocol 10”; `POST-CUTOVER-AUDIT.md` is the later authoritative
sorting: protocol 10 is live, so these are protocol-11 candidates.

The one product limitation worth stating publicly is item 6: materialization
and reread are audience-authorized now, but the read itself is not stored as a
new audited event. If recorded reads become a release requirement rather than
a future hardening feature, that is the one choice that would force protocol
11 before release. The reviewer recommends documenting the limitation and
deferring it rather than delaying team communication.

## Work that remains before cross-team release, without a protocol bump

1. Resolve the active frozen-candidate review:
   - shared-list content options must conflict with `--tweet` rather than be
     silently discarded;
   - the selected-part footer must not leak stale metadata or report false part
     counts, and must preserve its count under truncation;
   - a lost Enter/claim race must not focus a failed open.
2. Run focused break checks while correcting, then one full suite on the frozen
   successor.
3. Rebuild `bin/baton` and `bin/baton-tui` sequentially and verify both
   distribution manifests and deterministic hashes.
4. Complete the human TUI smoke test and the normal send/wait/claim/reply/close,
   scoped-notice, and multi-recipient packaged smoke paths.
5. Commit the reviewed candidate, then perform repository-layout/documentation
   cleanup as a tool/repository change if it is kept in the same release.

## Freeze rule

After the current protocol-free corrections, treat protocol 10's schema,
delivery envelopes, retry identity, and authority semantics as frozen for this
release. A newly discovered integrity, authorization, delivery, or
queue-liveness defect may reopen the boundary only through a named finding and
explicit release decision. New workflow features do not.

## Cross-team onboarding gate — ruled 2026-08-10

Slawomir ruled that repository cleanup lands as its own reviewed commit before
other teams are brought onboard. `baton.reviewer` owns the release gate after
that commit; a successful implementation review alone is not permission to
announce or begin onboarding.

The reviewer clears onboarding only after verifying the committed state:

1. the repository-layout finding is review-approved and committed by
   Slawomir, with a clean worktree;
2. the root contains only the approved five-file allowlist (`.gitignore`,
   `README.md`, `LICENSE`, `AGENTS.md`, and `justfile`) plus directories;
3. the complete suite passed against the frozen layout candidate and the
   committed tree contains those exact reviewed source/test bytes;
4. deterministic CLI and TUI builds match their distribution manifests,
   retain the approved member boundaries, and run outside the repository
   without `PYTHONPATH`;
5. frozen protocol evidence retains its pinned hash and active source imports
   none of it;
6. the live protocol-10 authority remains ungated and `doctor` reports
   `ok: true` with no problems;
7. packaged smoke covers readiness, claim, reply/close, scoped notice,
   multi-recipient delivery, subject-only `--tweet`, and participant-authorized
   reread.

Only an explicit reviewer approval after these checks opens cross-team
onboarding. Any failure stays local to Baton and is corrected before peers are
asked to depend on it.
