# Build the persistent v12 Job manager and submit/status API

Ledger Work: W71875

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed scope

Build the persistent host-side control plane that accepts a bounded multi-Job
submission and advances each Job through ordinary v12 stages without an
operator issuing every transition command. This leaf owns Job/submission and
stage-state persistence, restart reconciliation, the manager process boundary,
and documented CLI/JSON submit and read-only status surfaces.

The control plane composes the existing public Worker Manager and authority
operations. It does not duplicate offers, claims, attempts, runtime sessions,
output freezing, intake, retention, cleanup, or receipts with a second state
machine. It does not interpret Git, copy a source tree, implement worker-pool
selection, review policy, or integration policy. Those are separate leaves or
existing contracts.

## Observed baseline — 2026-09-02

- `v12/python/src/baton_v12/worker_manager/schema.py` persists manager
  operations, offers, attempts, sessions, outputs, intake, retention and
  runtime lanes, but has no Job, submission, stage queue, review, or
  integration scheduler relation.
- `offers.py`, `attempts.py`, `sessions.py`, `output.py`, and `intake.py`
  expose restart-safe bounded operations for the individual lifecycle steps.
- `v12/python/tools/dogfood_operator.py` is a supervised one-attempt command.
  It consumes operator-prepared grants/evidence and hands the result back to a
  v11 route; it is not a persistent scheduler and has no submit/status API.
- `v12/python/tools/parallel_test.py` is a test runner, not a product manager.

## Acceptance

- One documented JSON submission atomically records at least two Jobs, their
  immutable input identities, stage-scoped dependencies, requested runtime
  profiles, bounded test-change scope, and terminal policy.
- A long-lived manager process resumes that submission after restart and
  derives the next eligible act from persisted state rather than operator
  memory or a shell transcript.
- Every act delegates to the existing canonical Worker Manager/authority
  operation and records the returned identity/receipt; no shadow claim or
  lifecycle state can advance independently.
- The status command projects queued, offered, claimed, running, reviewing,
  changes-requested, integrating, completed, and exceptional states, runtime
  identity, dependency gates, and safe relative artifact/log locators.
- Replaying the same submitted intent is idempotent. Conflicting reuse of a
  submission or Job identity refuses.
- Restart tests stop the process at representative stage boundaries and prove
  that reconciliation neither repeats a committed act nor skips an owed act.
- No command-capable TUI, Git operation, source-tree walk/copy, or policy-driven
  acceptance/integration decision is added by this leaf.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` only where needed to verify this leaf's new control-plane
contracts and CLI/JSON behavior. Any deletion or weakening must be explicit in
the proposal and independently reviewed. It grants no authority over unrelated
tests.
