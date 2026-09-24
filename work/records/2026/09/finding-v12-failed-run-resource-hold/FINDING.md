# Bounded failed-run recovery and resource protection

Work W257624, created by baton.tuner under W247941 claim257612 on 2026-09-24.
Authority: owner M257333/M257341 and reroute257608. This is a prerequisite
delivery split, not a replacement for W247941 or a new live execution grant.

The preserved two-jobs-251156 run has two faulted implementation attempts,
no reviews and outstanding cleanup. The stopped candidate has useful recovery
and budget components but has not earned end-to-end acceptance. The latest
[review](../finding-v12-real-jobs-adoption-gate/review-2026-09-24T14-07-09Z.md)
identifies reclamation before hold checking, nonexclusive submission admission,
incomplete hold/clearance validation, unjustified clearance on any CLI answer,
and absent reuse/deletion guards. Its
[checkpoint](../finding-v12-real-jobs-adoption-gate/review-2026-09-24T14-07-09Z-checkpoint.json)
preserves candidate bytes, not approved bytes. Historical source, tests, reviews,
spending and unknowns remain at the original canonical dossier; nothing moves.

Selected outcome: small independently checked stages leading to either supported
positive cleanup or a durable, enforceable held/unresolved result identifying
every affected resource. A hold is not positive cleanup and cannot clear the
adoption gate. No new generic durable engine service is required; W44342 stays
parked. An uncertain daemon request must not be resubmitted, reclaimed, reused
or deleted merely because its local client exited or its operation ID repeats.

Planning only at creation. Proposed executor is baton.claude through baton.impl,
retaining existing ownership; reviewer baton.rvpc through baton.bug. The owner
selects the first small stage, not all remaining changes as one correction loop.
No source/test edit, live engine/provider, deployed recovery, deletion, store
reset or preserved snapshot mutation is authorized by this planning record.

Exact stages and commands: [PLAN.md](PLAN.md). Dependency rationale: W247941
cannot attest safe parallel development with these unresolved cleanup/resource
protection defects; W257627's final fresh packet must bind the accepted result.

## 2026-09-24T15:03:35Z — R1 independent review, baton.rvpc

Owner257693 selected R1 only, superseding the creation-time planning-only
status for that stage. Author257742 delivered the admission change. The
[independent review](review-2026-09-24T15-03-35Z.md) confirms the earlier hold
and transactional recheck in the hash-matched candidate. Acceptance remains
pending a committed-hold/pre-submission crash case, controlled contested
admission interleavings, and disposition of the operator-provisioned runner
prerequisite. Existing reported tests are preserved as author evidence; this
review ran no tests. Return to owner for selection, not automatically to R2.
