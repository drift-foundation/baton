# Concrete workers are skipped during construction unwind

Ledger Work: W129838. Discovered by baton.tuner under W103950 claim129808.

## 2026-09-09 — Confirmed

`StageExecution._closers` in `v12/python/tools/stage_execution.py` selects
`operations.release`. The actual `single_worker._Operations` implements
`close`; its ManagerOperations base implements neither close nor release.
The scheduler's pooled close uses `close`, but StageExecution owns its own
close path and does not reach that pooled method.

The direct factory regression constructs a real Authority, coordinator and
implementation worker using the accepted ServingCase fixture. It injects the
same RuntimeError before construction of the review worker. The expected close
sequence is implementation, coordinator, Authority; observed is coordinator,
Authority. The original failure propagates and pool activation is not reached.
Two early-failure controls pass. Exact command, hashes, result and elapsed time:
`../../evidence/claim-129808/verification.json` and `verification.log`.
Reproducer: `v12/python/tests/tools/test_stage_execution_hardening.py`,
`ConstructionUnwindsConcreteHandles.test_worker_construction_failure_closes_every_acquired_handle`.

The current per-worker disposal callback is deliberately a no-op because the
composer owns the shared Authority. This proves a skipped concrete cleanup
interface, not a leaked database connection, live runtime or credential.
Existing fake-handle tests expose `release` and cannot catch the mismatch.

## Proposed correction boundary

Align composition cleanup with the concrete worker close contract while
preserving reverse order, single shared Authority ownership and continuation
after a cleanup failure. Revalidate whether compatibility with release-only
objects remains required by an accepted public contract. Do not change worker
or protocol semantics merely to fit the fakes. Review must allocate production
ownership before implementation; W103950 tuner authority remains test-only.

## 2026-09-09T18:06:02.065342+00:00 — independently confirmed and bounded

review-2026-09-09T18-06-02Z.md confirms the mismatch and valid3-case parent evidence.
The same _closers AST exists in accepted one-Job bytes; no concurrent-worker
regression or current resource leak is inferred. Concrete, pooled and outer
factory contracts use close; old test handles expose both close and release.
Use concrete close without inventing release-only compatibility. Preserve
shared Authority ownership and reverse cleanup with failure continuation.
Source/test ownership is the two-path serial allocation in PLAN, after the
approved multi-Job providers finish; parent hardening test remains tuner-owned.
Missing dossier at pickup M129842 resolved before this assessment.

## 2026-09-11T01:15:02Z — deferred at the multi-Job acceptance handoff

Owner M140286/M140288 and campaign FINDING/PLAN2026-09-11T00:30:54Z prioritize
ordinary standalone A/B feasibility and defer separable robustness work. At
W119400 reviewer140552's safe handoff, canonical W129838 has no Handler and
is still gated on W119400. Park this cleanup correction before releasing that
gate; this explicitly supersedes automatic implementation immediately after
W119400 acceptance. No active author or file ownership is interrupted.

The concrete close/release mismatch remains confirmed and unresolved. Its
current callback is a no-op and no database/runtime/credential leak was proved;
it does not prevent or falsify the accepted ordinary A/B result. Revisit after
the standalone milestone, or immediately if a concrete successful-run cleanup
requirement exposes an actual resource/ownership failure. Preserve the exact
two-path correction,60s cumulative author ceiling, original reproduction and
independent review requirement for that future handoff; no spending, transfer
or source edit here. The defect is deferred, never labelled fixed or passed.

Canonical disposition completed: W119400 close140582 released the existing
gate normally; phase140585 parked W129838, and reroute140586 restored baton.impl
while preserving parked state. The earlier blocked-to-parked request was refused
by the gate rule and made no change. No Work claim or source execution occurred.
