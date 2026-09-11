# Progress

Implementation entries belong to the assigned change author.

## 2026-09-09 — baton.claude, claim 129949

**Claimed first**, at seq129949, before any edit. The accepted pool bytes are
revalidated byte-identical, every remaining singleton consumer is traced, and
the exact per-Job document, its configuration rules, the selection interface
and the one boundary this cut reports rather than expands are all recorded in
PLAN.md before editing.

### Delivered

**The per-Job document.** `/2` gains one optional member, `job_bindings`, each
entry closed to `(job_id, job_work_id, review_work_id, line_declared_base,
canonical_target_id, source_worker_id)`. `/1` is not asked for a new member —
its binding is DERIVED from the members it already has, so every existing
assertion about them stands, and carrying `job_bindings` there is refused
because two places for one fact is how they drift. Held before anything
durable: `job_id` unique; `source_worker_id` naming a configured
implementation worker, whose nomination `single_worker`'s own validator already
proved — an identity, never a list position; and the implementation and review
Works equal, because one line is keyed by one `(authority, work)` pair and
`attach_review` binds the reviewer to the writer's own Work.

**The selection interface.** `binding_for` refuses an unknown Job before
anything is prepared for it; `line_for` materializes that Job's own line from
its own source, base and Work; `works_for`, `target_for` and `source_for` read
the same binding; `line()` stays the one-Job spelling of `line_for` so the
one-Job path is the same code rather than a parallel one; `worker_for(stage)`
answers the worker the SCHEDULER allocated, never list order; and
`_prepare(stage)` takes the stage, because the line it grants on belongs to
that stage's Job — reaching one global line from an attempt alone is exactly
why a second Job could only share the first one's checkout.

**The proof** is over the composed fixture, so both sources are real
version-controlled trees and both lines are materialized by the accepted
checkpoint profile: two Jobs give two distinct line ids, paths, Works, declared
bases and source paths, read back through the provider's own reader; the same
Job reaches the same line every time; an unbound Job is refused with the line
count unchanged; and a stage with no allocation is refused rather than guessed.

### Reported rather than expanded

`single_worker._matches` compares a stage's `work_id` against the WORKER's own
input manifest, and the scheduler allocates by lane and eligible kind without
consulting a worker's configured Work. Two Jobs on two Works therefore need
either per-Job worker eligibility in the scheduler or a worker whose manifest
is not Work-bound — both outside these two paths, and the FINDING says such a
gap is reported rather than taken as implicit permission. This cut binds every
Job to its own line, Works, source, base and target and refuses a mismatch
clearly.

### Test delta, recorded under the standing authority

The pool fixture's `/2` document gains a binding (it could not otherwise serve
a Job); `test_a_per_job_question_refuses_and_names_the_next_cut` becomes
`test_selecting_among_producers_is_still_not_a_pool_question`, because its
second half asserted the absence of exactly the capability this cut lands while
its first half still holds; and the case that calls `_prepare` directly hands
it a stage. Added `EachJobBindsItsOwnDeploymentAndLine`, 12 cases.

### Runs

Five module iterations settling the document and the pool fixture (84.079s,
ending 173 OK) → five iterations of the new class (2.446s) → 185 with 2
failures (21.412s) → **185 OK** (21.475s) → **321 OK** across
`test_single_worker`, `test_scheduling` and `test_review_driver` (9.224s).
**138.0s of the declared 250s, 112.0s left.** No live model or OCI
demonstration and no whole-suite pass. Detail:
`evidence/provider-129949.json`.

Passing back to `baton.bug`; the parent owns joined acceptance.

## claim130076 — the review's three P1s, corrected

Evidence: `evidence/provider-130076.json`, `evidence/run-130076-neighbours.log`.
Candidate, both mode 0664 relative to v12/python:

- tools/stage_execution.py `6c9007ba241fce41f63c3bae1d93dd37b0ee5bf351b48c9ba1fe843e7ef38550`
- tests/tools/test_stage_execution.py `714a49b1ccf82e998b903131231beb4d18c02f8cbe2a5c52dbb54bd0fed3487a`

**All three P1s are accepted, and the third is a withdrawal.** The readers
existed and nothing called them; the PLAN sentence saying `required_tests`,
`account` and the targets selected through them described a change that was not
in those bytes. They are now connected: the ending publishes through the
producer's own seam, the integration stage reads its Job's line, target and
producing worker, `account` reads the allocated integrator and the bound Work,
and the factory audits every bound Work's own effective scope. Binding refusal
moved ahead of `reserve` through the existing `PooledManagerOperations(...,
independence=)` seam, which also excludes Job-incompatible workers — so **I
withdraw the claim that two Works necessarily needed a scheduler or
single-worker change.** It was unsupported; the seam was already public, and
`single_worker`'s own validation is untouched. The fixture's second Work is now
real in the Authority rather than a name nobody held.

185 assembly tests and 321 neighbours pass. Read-only observation, the accepted
integration doubles and `/1` all keep exactly the answers they were accepted
with, through one rule (`_bound_id`) rather than scattered fallbacks.

**Budget finding, before exhaustion and not extended.** Declared 250s; prior
138.636s (the reviewer's figure, which I accept over my 138.0); this claim
94.1s; spent **232.7s**, remaining **17.3s**. The assembly module alone measures
21.3s, so *what is left cannot measure another run.* Unmeasured and therefore
unclaimed: the public-admission tests for the unknown Job, the cross-Job worker
and the mismatched input/Work; the second producer's manifest re-derived for
`SECOND_WORK` with a second submission; and the correction, reconstruction,
concurrent coding/review, fault-capacity, serialized same-target and joined
W119400 witnesses, all of which reuse that traversal fixture.
