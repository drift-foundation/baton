# Owner stop checkpoint — reviewed claim257382

**STOP implementation/review cycle; NOT READY.** Per M257333/M257341 and the
owning FINDING ruling, return to baton.decide for Tuner-led decomposition.
See `review-2026-09-24T14-07-09Z.md` and `review-2026-09-24T14-07-09Z-checkpoint.json`. Do not auto-pass
back to implementation. Preserve candidate/evidence and current ownership.
Two focused hold tests pass; reclamation-before-hold, nonexclusive submission,
incomplete evidence validation and absent resource guards block acceptance.
Owner-selected small stages must replace the continuing broad correction cycle.

## Prior author account — claim257340

# Current action — after claim 257340; RETURNED INCOMPLETE

Review 2026-09-24T13:58:36Z resolved the design question I returned, and its
distinction turned out to make the supersession unnecessary. The hold is
implemented end to end.

## The line the review drew, and where it put the write

"The hold is for ACTUAL ENGINE UNCERTAINTY", and "same-act identity does not
authorize resubmission of unresolved daemon request". That places the
write-ahead **inside `custody_act`, immediately before the request crosses** —
not around the adapter call, where I had put it.

**That is why no accepted rule needed superseding after all.** Everything
before the submission — a capability that raises, a malformed operand, a root
that does not exist — is pre-submission and still commits nothing, so
`test_an_unaccountable_answer_commits_nothing` holds unchanged. The
interrupted-normalization resume cases interrupt with a fake custodian that
raises BEFORE any submission, so they resume exactly as before. I had the
authority to append a bounded supersession and to update those tests, and did
not need it: **966 accepted tests pass with no test edited.**

## What the hold is now

  * **written before the submission** and cleared when the engine answers at
    all — a refused or unaccountable ANSWER is this manager's judgement about
    a helper that ran and exited, which is a different fact from silence;
  * **classified structurally**, not by exception type or string: the
    uncertainty is `status is None`, no engine answer, which `custody_act`
    already mints;
  * **binding on a NEW act** — a standing episode refuses the next submission
    over that root, naming the helper it would have created and saying the
    root is frozen: not acted on, not reused, not deleted on the strength of
    that act;
  * **per root, not per attempt** — asserted;
  * **episode-bearing identities**, so a second uncertainty is its own fact
    and the clearance already written does not cover it;
  * **fail-closed reading**: the record's kind, state and document are each
    checked, an unreadable hold or clearance refuses rather than being read
    past, and overflow past `_MOST_HOLDS` refuses;
  * **an operator clearance requiring what was OBSERVED**, refusing a blank
    observation, an episode that does not exist, and one naming a different
    helper.

## Corrected: my "five of six" was overstated

The reviewer is right. Last claim's case covered empty, missing and blank
inputs only — no actual hold, clear, restart or guard. This claim's cases
drive a REAL external uncertainty through the composition's own adapter: the
episode is written, the next act refuses, a reconciliation lifts exactly one
episode, the act then proceeds, and a second uncertainty becomes episode two.

## REMAINING

  1. reuse and deletion guards — `workspaces.py` and the other paths that
     would reuse or delete a held root, to be enumerated and coordinated
     before edits, exactly as `oci.py` and `custody.py` were;
  2. store-wait accounting — the actual lock and I/O bounds;
  3. the supervisor timeout and replay proofs through `supervise` with a
     stranded attempt;
  4. first-call crash and launch-absent alternate recovery;
  5. the two operator grants documents with validation and readback;
  6. the executed-image fault diagnosis;
  7. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **49 cases, all passing,
2.842s**, clean under `-W error::ResourceWarning`.
Accepted suites over the changed product files — **966 tests, OK, 22.607s**,
with no accepted test edited.
`test_two_jobs` — **85 tests, OK, 69.194s**.

## Standing constraints

No deployed mutation, live rerun, cleanup execution or deletion. The preserved
instance and the snapshot are read-only. W44342 unchanged and still parked.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
