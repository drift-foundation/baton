# Implementation handoff — seedless participant identity

Implements `FINDING.md` in this folder, authorized 2026-08-07 after commit
`b4d847e`. Fresh-authority release: **no migration path was written and the
retired protocol-7 mailbox was never read, written, or migrated.** No Git
mutation; Slawomir stages and commits.

    tool 3.0.0   protocol 8
    artifact_sha256      75a8b206e4f7a4be01260d526fa328a01fec0e2bcd6dae29b4cd2c8a3e343b4b
    source_sha256        dc24beba58ce6ae582dcae8cefbd21e2756c5d138ec81b07549f19ee822202ea
    protocol_doc_sha256  c9253eddb56249549facf63317a9a7d3eb9946d0e501169f46d18812916a8a1f

**318 tests pass, 0 fail.** Revised after review round 1; see the closing
section for what changed.

## The contract as built

The participant address is the complete logical identity. There is no actor
and no seed anywhere: not in the CLI, the config, the schema, the
authorization path, or the audit trail.

`_check_actor_for` became `_check_identity`, which does exactly one thing —
confirm the address is a configured participant. There is no second factor to
validate, because a second factor that everyone can read was worse than none.

## Breaking surface

Every item here is a deliberate protocol-8 break, not an oversight.

**CLI.** `--actor` and `--seed` are gone from all 21 identity-bearing
commands; `--participant` alone. `reply` and `close` now *use* the
`--participant` they previously parsed and discarded.

**Config.** `identity` and `singleton_actor` are removed from the participant
shape. A config still carrying either is **rejected with the reason**, never
accepted-and-ignored — an ignored identity field would leave an operator
believing a binding is enforced when nothing enforces it.

**Schema.** `actor` and `seed` columns dropped from `op_context`, `claims`,
`notices`, `notice_seen`, `quarantines`, `recoveries`, `ceremonies`,
`transitions`. `claims` gains `participant`. `instance_meta.maintainer_actor`
becomes `maintainer_participant`. `notice_seen`'s primary key collapses to
`(notice_id, participant)`. The `_CTX_ACTOR` and `_CTX_SEED` trigger macros
are gone, so the ledger attributes to a participant and a verb.

**Ownership.** `_load_active_claim` requires the caller to be the claiming
participant *and* that participant to be the message recipient. Two checks,
because they can disagree only if something is already wrong, and a
disagreement should say so rather than pick one.

**No legacy columns.** Per the reviewer's disposition, the retired authority
keeps its history and the replacement starts fresh, so nothing nullable was
carried forward.

## Acceptance tests, against the eight in FINDING.md

All eight are covered and passing. Demonstrated on a live protocol-8 instance
rather than only in fixtures:

1. Non-recipient disposal refused — `claim … belongs to 'acme.implementer',
   not 'acme.reviewer'`, for first disposition and retry.
2. Known foreign claim id refused as a *permission* failure, not a lookup
   miss: `test_reply_wrong_owner_refused` asserts the true owner still
   succeeds immediately afterwards, so the refusal cannot be a broken lookup.
3. `dump` contains no bearer credential — asserted by scanning its full output
   for `seed` and `actor`, both absent.
4. Receipts dedupe per participant; second consumption returns nothing.
5. A publishing participant receives its own unseen notice exactly once.
6. Recovery still requires the `recovery` capability
   (`test_recovery_still_requires_the_capability`).
7. A config with `identity`, `singleton_actor`, or either alone is rejected
   (`test_old_identity_config_is_rejected_not_ignored`).
8. `doctor` reports no identity-shaped inconsistency on a fresh instance.

Also verified: the README's documented flow runs end to end against the built
executable — init, send, wait, reply, `doctor ok: true`. Documentation that
does not execute is a defect I have shipped before in this project.

## What I would review hardest

**The regex sweep.** Most of this change was mechanical removal across ~500
test occurrences and ~67 source ones. Mechanical edits at that volume are
where quiet damage hides, and it did: one pass silently set
`participant="acme.implementer"` on *every* disposition, which passed
superficially and only failed where a test disposed as `acme.reviewer`. It is
now derived from the claim (`participant=claim["participant"]`) rather than
assumed. **Assume there are more of these and check the diff, not the test
count.**

**Tests I rewrote rather than deleted.** Four tested behaviour that no longer
exists. Each was replaced with a test of the new contract at the same seam,
not dropped:

- `test_singleton_actor_enforced` → `test_participant_address_is_the_whole_identity`
- `test_actor_grammar_and_budget` → `test_old_identity_config_is_rejected_not_ignored`
- `test_wrong_singleton_actor_refused` → `test_recovery_still_requires_the_capability`
- `test_same_participant_different_actor_cannot_early_expire` → `test_only_the_authoring_participant_may_expire_early`
- `test_notice_delivered_to_each_actor` → `test_notice_receipt_is_per_participant`

If any of those lost a property rather than relocating it, that is the failure
mode to look for.

**Docstrings and prose.** I swept `baton_v6.py`, `README.md`,
`AGENTS-MAILBOX-PROTO.md` (now v8), `config-schema.json` and
`example-baton.json`. Comments describing the old model are misinformation
that tests cannot catch.

## Not done, deliberately

- No credential machinery, issuance system, lease protocol, or rotation
  policy. The model removes the need; adding any back needs evidence that
  participant-address identity is insufficient.
- No migration. `migrate` remains the audited refusing gate.
- The one-live-consumer rule stays **policy**, not mechanism. A seed never
  enforced it — two waits sharing participant, actor and seed still raced, and
  one claimed into a process nobody was reading. Inventing a lease now would
  be building machinery for a problem the credential never solved.

## Sequencing note

`work/finding-typed-content-envelope/` is pinned and must land **before** the
fresh authority is initialized, so protocol 8 carries both changes and the
deployment takes one teardown rather than two. Do not initialize the new
mailbox until that implementation is in.

## Review round 1 — corrections applied

**Public prose contradicting the contract.** `README.md` still promised
deduplication and fanout per `participant+actor`, including independent
delivery to multiple actors of one participant. That was a user-visible
contract contradiction, not a stale comment, and the most serious item in the
review: the code shipped one receipt per participant while the documentation
promised otherwise. Corrected, along with the remaining active-tree residue —
`README` calling the consumer an actor, `migrate`'s docstring and its test
claiming protocol 7, the module and suite docstrings claiming protocol 6, a
per-actor delivery comment, and a comment describing a changed participant as
a changed actor. Historical findings were left historical.

**Three acceptance pins were claimed but absent.** The handoff said all eight
were covered by regressions; three were only covered by my own ad-hoc
verification, which does not survive into the release. That is a worse error
than a missing test, because it asserted a tripwire existed:

- *Item 1, refusal on retry.* `test_reply_wrong_owner_refused` covered only
  first disposition. Retry is where an ownership check is most likely to be
  skipped, since the code is looking for idempotence rather than authority.
  Added, plus `test_close_ownership_enforced_on_first_and_retry` — a test of
  `reply` alone would not catch the two seams diverging.
- *Item 3, no bearer credential in `dump`.*
  `test_dump_carries_no_bearer_credential` now walks every key recursively.
- *Item 7, literal `actor`/`seed` config fields.* These were rejected only by
  generic unknown-field handling. Rather than assert that behaviour, `actor`
  and `seed` joined `_REMOVED_PARTICIPANT_FIELDS`, so a config author who
  writes them is told *why* they are gone rather than that they are unknown.

**Mechanical sweep residue.** All cleaned: a duplicated `exact_author`
comparison, a duplicated malformed-participant check that could emit doubled
`doctor` problems, the unused `singleton_ok` parameter, unused `SEED_A/B/C`
constants, dangling continuation lines and trailing commas from removed
arguments, and the trailing whitespace that failed `git diff --check`.

This was the failure mode I flagged in the original handoff and the reviewer
still had to find the instances. The lesson stands: a passing suite says
nothing about residue, because residue compiles.

**Verification after the corrections:** 318 passed, 0 failed; deterministic
rebuild; artifact, source and protocol-document hashes match
`DISTRIBUTION.json`; `git diff --check` clean.
