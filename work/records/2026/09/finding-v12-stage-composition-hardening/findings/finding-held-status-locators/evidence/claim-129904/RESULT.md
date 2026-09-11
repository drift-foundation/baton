# Held-integration status join passes

baton.tuner, claim129904. Implements the exact allocation in
`../../review-2026-09-09T18-11-13Z.md` and the owning FINDING/PLAN.

The new file invokes the actual `tools.job_manager.main` status path with
`--control` and configured `tools.stage_execution:observing_factory` after the
real isolated uncertain-integration fixture and ordinary tick. It composes the
existing fixture explicitly; only the two new tests run.

The positive readback binds Job `job-a`, stage `job-a/integration`, episode1,
attempt/offer, scheduler allocation and runtime assignment to the fixture's
public owners. Status is `exceptional`; the coordinator entry stays `held`,
the target stays `blocked`, and no integration-pass exists. Public Work,
allocation, runtime, activity, frozen-output and coordinator documents are
unchanged after the read. The four database byte digests and modes also match.

Integration has no ordinary exchange or frozen artifacts: both status members
are null. Activity retains this attempt's identity with `bytes_observed` and
`observed_at` null. No log locator is available in this selected state; this
proves explicit availability/absence, not a new logging capability. Existing
generic present-locator and completed-state evidence is reused.

The negative configures a missing coordinator. The same CLI path raises
ContractRefusal(`refused`, `precondition`), emits no partial status, creates no
coordinator file, and preserves the same public records and protected bytes.
Guards prohibit serving construction, Authority sessions, launch/conclude,
integration run/finish, pool activation, preflight, port prepare/refresh and
terminal pass. SQLite-managed WAL/SHM effects remain allowed.

Run1 exposed an incorrect new assertion expecting activity itself to be null;
the existing owner contract returns the attempt-bound record above. That
assertion was corrected without changing behavior or production code. Run2
passes both tests. Exact commands, timings and logs: `verification.json`,
`run-1/` and `run-2/`. **3.481925s/20s** cumulative; **16.518075s** remain.
No broader run. Each run hashes all234 v12 Python files before/after; no
concurrent changes occurred within either run or between run2 and final audit.

Only `v12/python/tests/tools/test_stage_execution_status_hardening.py` and this
dossier's evidence/progress changed under this claim. Candidate mode0664,
SHA256 `acdd44ae69d6ad2ba78567cd607ca5efb711364af544024a80de59ba2fa020af`;
retained as `candidate-test_stage_execution_status_hardening.py`. `final.json`
contains the concise audit/readback; run2 JSON files retain full owner/status
correlation. Syntax, whitespace and scoped diff checks pass.

Return to baton.bug for independent acceptance. No production defect was
exposed. Registry integration remains its owner's later serial handoff;
W103950 retains joined hardening acceptance.
