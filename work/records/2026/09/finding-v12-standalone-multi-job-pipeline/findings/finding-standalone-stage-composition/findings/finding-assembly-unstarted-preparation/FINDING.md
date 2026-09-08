# Complete never-started assembly preparation

Ledger Work: W119113. Created by baton.codex under W103083 claim119091.
Parent: ../../ (standalone stage composition). Historical evidence remains in
../finding-shared-stage-assembly/; no record was moved or rebound.

## Confirmed boundary — 2026-09-08

The real assembly still skips prepare when a published delivery has a
not-started runtime witness. A fresh IntegrationRuntimePort therefore has no
execution-local credential and refuses before starting. Independent evidence:
../finding-shared-stage-assembly/evidence/review-119091/audit.json (0.362s),
and its review-2026-09-08T12-41-47Z.md. Zero prepare calls, zero engine starts,
with the runtime remaining not-started. This is the uncorrected third P1 of
review-2026-09-08T04-06-54Z.md, not a newly invented requirement.

Owner M118923 explicitly approved the exact observed-then-prepare assertion
change before implementer claim118937. M118986 reconfirmed it before handoff.
The assertion permission is settled; do not request it again. Preserve
no-refresh, exactly one admission, no continuation, and unrelated assertions.

Own only v12/python/tools/stage_execution.py and
v12/python/tests/tools/test_stage_execution.py. This is a serial subdivision
of the accepted five-path assembly scope, not a scope expansion. Call the
accepted idempotent prepare(stage, job) before admitting an independently
proved never-started delivery. Preserve started/uncertain holds and do not
mint credentials inside admission or reopen the closed port provider.

Focused acceptance uses the real factory and fresh production port with the
accepted deterministic engine and disposable local stores: interrupted first
admission before run, reconstruction of a fresh port, preparation then one
start; valid initial and same-execution controls; no refresh on never-started;
no duplicate start and preserved started/uncertain holds. Add regressions for
held task replacement/missing verification and actual nominal-group use if
needed to retain the independent controls as ordinary tests. Do not replace
real public readers with mocks at the boundary being proved.

The two preceding defects (held/raw configuration and integer group) are
independently corrected at the retained candidate hashes. Preserve them.
The complete lifecycle/custody acceptance is separately scheduled in
../finding-composed-one-job-proof/; this correction does not establish it.

## Decomposition authority and limits

EFFECTIVE-BATON.md requires a split after repeated incomplete reviews. The
existing owner-approved behavior/path/test scope is unchanged. baton.claude
implements this bounded correction and returns through baton.bug for independent
review. Shared test/source writes finish before the lifecycle proof begins.
No live model, OCI campaign, canonical target import, mutating Git operation,
new path or unrelated assertion change is authorized by this subdivision.
