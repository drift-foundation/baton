# Plan: manager intake, retention and cleanup

1. [done 2026-08-24] Create this dossier and revalidate worker-control and the
   closed W4 record. Recorded in `FINDING.md`: the cleanup axis and its
   transitions are already pinned by W4; `blocked-on-intake` is a first-class
   state rather than a retry condition; `retained` is terminal and is not
   `complete`; and THE FROZEN SCHEMA HAS NO DEFINITION FOR INTAKE, RETENTION OR
   CLEANUP AT ALL -- `retention_policy_digest` is a digest of a document whose
   shape no contract states.
2. [needs a ruling] Name the owner of the retention policy DOCUMENT, or rule
   that this Job defines it. It cannot be consumed from a contract that does
   not exist, and inventing it here is what the assignment's own "must not
   reconstruct any of them" forbids by implication.
3. [blocked on W6627, W6628, W6630 and item 2] Intake over sealed artifacts and
   certified observations, through W4's existing journal rather than a second.
4. [blocked on item 3] Recoverable cancellation material, kept distinguishable
   from material retained by policy -- two different reasons for the same bytes
   still being there.
5. [blocked on item 4] Cleanup authorization and positive absence, with
   restart/retry ordering preserved.
6. [blocked on item 5] Tests, evidence and independent review.


## Implementation — 2026-08-26

The three dependencies are CLOSED now (W6627, W6628, W6630, and W6592 under
them), so items 3-6 are unblocked, and item 2's question dissolved under
revalidation rather than needing a ruling.

2. [resolved 2026-08-26, superseded] The retention policy needs no owner to be
   named. It is one of TEN `*_policy_digest` members whose document shape the
   frozen schema states for NONE of them: policies are consumed by IDENTITY,
   and interpreting one here would be the boundary violation. Recorded in
   `FINDING.md` with the count that settles it.
3. [done] **Intake over the sealed result**, through W4's existing journal:
   `output.collect` journalled before the adapter is called, the collection
   COMPARED against what the freeze recorded rather than adopted, and
   `frozen -> sealed` written under an intake receipt this manager produces.
4. [done] **Recoverable cancellation material kept distinguishable from
   material retained by policy.** `recoverable` is derived from the worker
   disposition so it cannot disagree with the axis it is about; `custody` says
   on what terms the material is held; retention says what a policy decided.
   Three different reasons the bytes are still there, and none of them
   collapsed into "still there".
5. [done] **Cleanup authorization and positive absence.**
   `blocked-on-intake` is used as the state it is -- recorded, no adapter call,
   no refusal, no retry loop -- and `retained` is never reported as `complete`.
   Only an engine that says this exact identity does not exist settles a
   destroy; a survivor is `failed` and an unreadable account moves nothing.
6. [done] **Restart/retry ordering preserved**, in the shape W6628's receiver
   was corrected for twice: replay sits above every state read, so an exact
   retry reproduces its answer once the axes have moved.
7. [done] 47 focused cases in `tests/manager/test_intake.py`; three rules
   mutated and measured to fail. Store schema 10 -> 11 with three tables.
8. [next] Independent review.


## Correction to item 7 and 8 — 2026-08-26, after the full suite

Item 7 recorded the focused suite and the mutation measurements and was
written before the full suite ran. The full suite found FOUR package gates my
new surface had not satisfied, and the entry above should not have implied
otherwise. Three are corrected; one is not.

7a. [done] `tools/parallel_test.py` did not register
    `tests.manager.test_intake`. The registry gate is exactly the check for
    that and it caught it.
7b. [done] Eight `documents.py` constructors this Work added had no stated
    owner in the boundary inventory.
7c. [done] **Every retention column was invisible to the inventory's origin
    walk**, because the rows were pulled through a second local before their
    members were read. The reads were owned; the inventory could no longer SEE
    them, which is worse -- nothing could have told me a column had stopped
    being covered. Written in `frozen_output_of`'s shape, and the reason is
    recorded in the module so the shape survives the next edit.
7d. [done, source] **Six exported surfaces composed caller text into a
    portable operation identity with no section 13 walk.** Measured, not
    reasoned: a live bearer in an attempt row's own id came straight back out
    inside a returned operation id. The four derived identities now walk their
    operands the way `manager_signature` does, and the two read-side surfaces
    walk what they hand back the way `certified_agent_session_profile` does.
7e. [NOT DONE] **The section 13 accounting for the new public surface.**
    `test_secrets` requires every exported callable to be classified and every
    constructing surface to be PROVED by a probe that drives it with the bearer
    live. Six of the ten refuse already and are measured; four --
    `decide_retention`, `authorize_cleanup`, `intake_receipt_of` and
    `retentions_of` -- need a store fixture to reach their walk, and the
    classification table and its probes are unwritten. Two `test_secrets` gates
    are red because of this.
8. [blocked on 7e] Independent review. **This Work is not ready to pass back.**


## Item 7e closed — 2026-08-26

7e. [done] **The section 13 accounting for the new public surface**, in the
    shape `test_secrets` requires: every exported callable in exactly one of
    the two closed classes, every constructing one PROVED by a probe that
    drives the real operation with the bearer live, and every durable writer
    covered by a reason naming the path that actually runs.

    - **Three durable writers covered.** `_seal` writes `intakes` and
      `intake_artifacts`, `_retain` writes `retentions`; each is private with
      exactly one door and each runs inside `store.transact`, whose journal
      row is walked before the COMMIT that would keep the action's writes.
    - **Six surfaces classified as CONSTRUCTING and probed in place** -- the
      four derived operation identities, which take a caller's attempt mapping
      and answer with portable protocol identity, and the two read-side doors,
      one of which hands back the digest a destroy is AUTHORIZED by.
    - **Four classified prose-only and driven where they can be reached.**
      `request_intake`, `record_intake`, `decide_retention` and
      `authorize_cleanup` refuse a missing attempt long before their walk, so
      a probe against `test_secrets`' fixture would pass for the wrong reason.
      This is `record_frozen_result`'s situation and it is resolved the same
      way: the walk is named, the walk is probed directly, and the door is
      driven in `test_intake` -- one case per door, plus a control that drives
      the same operands with the bearer FORGOTTEN so a precondition refusal
      cannot pass for a §13 one.
    - **Measured by removing the guards**, source restored byte for byte. The
      four identities are guarded by this module's own walk and nothing else;
      the two read-side doors are guarded twice and it takes both; the four
      journalled doors are layered three deep. Evidence in
      `evidence/gate-section-13-accounting-2026-08-26.txt`.
8. [next] **Independent review.** The two gates this Work's own surface turned
   red are green, and the surface is passed back rather than closed.


## Independent review changes requested — 2026-08-26

8. [changes requested] Six additive regressions pin four P1 correction
   boundaries. Review journal:
   `review-2026-08-26T07-35-43Z.md`.
9. [next] Refuse a new cleanup authorization while the authority still reports
   the attempt's fixed assignment live. Ended or fenced is the gate; participant
   equality is not a substitute.
10. [next] Deliver both frozen commands through the adapter boundary:
    `output.retain` with its complete body and operation, and
    `runtime.destroy` with its complete authorizing body and operation. Preserve
    replay-before-current-state ordering and positive-absence settlement.
11. [next] Derive `output.retain` identity from every operand that distinguishes
    one valid command from another, including artifact group and disposition,
    so one policy can decide different artifact groups independently.
12. [next] Authenticate reconstructed intake receipts and retention decisions
    against their committed journal operation/signature. Self-consistent row
    edits must fail as integrity defects before they can authorize cleanup.
13. [done] Re-ran all six review cases and the full focused module after the
    concurrently changing Python schema snapshot again accepted the published
    input vector. Current result: 52 retained passes, four failures and two
    errors, 58 total. Expected corrected focused result: 58/58.


## Independent correction re-review — 2026-08-26

9. [done] Cleanup now refuses a new authorization while the exact fixed
   assignment remains live, below exact committed replay.
10. [done] Complete `output.retain` and `runtime.destroy` commands and their
    operations now cross the adapter boundary.
11. [done] Retention operation identity now includes the canonical artifact
    set and disposition.
12. [done] Persisted intake and retention rows are now checked against
    committed journal evidence. The review's two `integrity` assertions are
    corrected and explicitly approved as category checks.
14. [next, P1] Preserve per-artifact replacement while authenticating
    retention rows: validate each current row as a member of the committed
    `output.retain` result named by its operation id instead of reconstructing
    the historical whole command from only rows that remain current.
15. [next] Keep
    `test_a_later_policy_can_replace_part_of_a_grouped_decision` and the forged
    receipt/retention cases together: partial replacement must pass while an
    edited row still fails closed as integrity.
16. [next] Re-run the focused intake module and the manager secret,
    dependency and text-sweep gates, then return for independent review.


## Independent correction re-review, round 4 — 2026-08-26

14. [done] Per-surviving-row membership authentication now preserves partial
    policy replacement and rejects forged disposition/policy rows.
15. [done] The partial-replacement and forged-row regressions pass together.
17. [next, P1] Bind each retention row to the committed result's
    `attempt_id`, not only its artifact, disposition and policy. A row for one
    attempt must not borrow journal evidence from another attempt whose local
    artifact id happens to match.
18. [next] Keep
    `test_a_retention_cannot_borrow_another_attempts_committed_act`; rerun the
    60-case focused module and the manager secret/dependency/text-sweep gates,
    then return for independent review.


## Independent final re-review — 2026-08-26

17. [done, verified] Retention authentication binds the committed result's
attempt identity before accepting per-row artifact/policy/disposition
membership.

18. [done] Intake 60/60; manager secret/dependency/text-sweep 114 tests green
with one expected skip; whitespace clean.

8. [done, signed off] Independent review is complete with no open finding.
