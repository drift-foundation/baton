# W266329 — V12 micro-stage 1: reserve before launch

Own dossier for W266329, bound in claim 266537 as thread T266329 directs ("Bind own
dossier when implementation starts") and review 2026-09-25T14-12-41Z R2 requires. It
was absent until now; I reported the absence in claim 266370 instead of performing
the assigned step, and no CLI denial was involved.

## Scope, as selected

Owner 266361 and thread T266329: implement and independently verify ONE actual
reserve-before-launch path using real disposable stores and a controlled adapter --
durable pre-start operation identity, short atomic reservation, transaction committed
before external I/O, contention and failure refusal -- delivered as ONE bounded
runnable command with minimal demonstrated-path fixes. Reuse the existing
`runtime.start` transaction rather than inventing a pre-start runtime id. Explicitly
NOT in scope: stages 2 and 3, broad suites, live providers, deployed-store access,
cleanup, comprehensive planning revision.

## Current state

Stage 1 was NOT accepted on first delivery. Review 2026-09-25T14-12-41Z found a real
[P1]: a caller suspended after the preliminary `not-started` axis read resumed after
another manager had reserved and started the same attempt, REPLAYED the
`runtime.start` identity, and still called `adapter.start` -- a second external
crossing after the reservation was committed. Corrected in claim 266537 by deciding
ownership inside the transaction callback, which `transact` runs only when it commits;
a replaying caller reconciles instead of launching. The reviewer's immutable
regression passes unchanged.

## Ownership

- MINE: `work/records/2026/09/finding-v12-failed-run-resource-hold/test_reserve_before_launch.py`,
  this dossier, and the minimal `v12/python/src/baton_v12/worker_manager/attempts.py`
  correction owner 266361 authorized for the demonstrated path.
- REVIEWER'S, immutable:
  `work/records/2026/09/finding-v12-failed-run-resource-hold/review_stage1_stale_start.py`
  and the `review-2026-09-25T14-*.md` journals.

## Why the evidence files stay where they are

The stage-1 module and the reviewer's regression live in W257624's dossier because
that is where this stage began and where the review recorded their SHA-256 values.
Review R2 says to preserve existing files as historical evidence and cross-reference
them rather than move history, and moving them would invalidate hashes another party
recorded. So nothing was moved or deleted; this dossier carries the checkpoint and
points at them. W257624 keeps its own binding; no second Work is bound to it.

## Cross-references

- Parent Work W257624 dossier: `work/records/2026/09/finding-v12-failed-run-resource-hold/`
  — its `FINDING.md` carries the 2026-09-25 short-transaction/fenced-lease ruling this
  stage proves one path of, `PROGRESS.md` carries the stage-1 author entries, and
  `VERIFICATION-SELECTORS.md` carries the exact selectors and command.
- Stages 2 and 3 remain separate Works and are not begun here.

## 2026-09-25T14-34-37Z — independent stage 1 acceptance

[review-2026-09-25T14-34-37Z.md](review-2026-09-25T14-34-37Z.md) accepts the minimal start-admission correction. The unchanged
stale-precheck regression and nine author cases pass independently:10 cases0.099s.
A journal-replaying caller now reconciles instead of submitting again; transaction
exit before external start remains proved. Canonical own-dossier binding resolves
R2. PLAN.md was missing on review and is supplied as the reviewer checkpoint,
with this operational finding preserved. Return owner; stage2 release, stage3
recovery and wider W257624 obligations remain separate and unaccepted here.
No live provider/daemon/deployed-store operations or reviewer product edits.
