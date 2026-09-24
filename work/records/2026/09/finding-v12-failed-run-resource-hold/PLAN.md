# Current action: owner selects R1 only

2026-09-24T15:03:35Z, baton.rvpc: R1 delivered and independently inspected;
acceptance pending the bounded evidence and runner prerequisite in
[review-2026-09-24T15-03-35Z.md](review-2026-09-24T15-03-35Z.md).
Return to owner under selection257693. No R2 execution or automatic correction
cycle is selected by this review. This updates the planning-only status below;
existing product/test ownership remains with Claude.

W257624 is placed at baton.decide. Proposed implementation: baton.claude;
independent review: baton.rvpc. Review each stage before beginning its successor.
Each handoff says stage/result/evidence/next stage. A red regression remains red
evidence; do not make a new invariant optional to make the stage pass.

Shared inputs: stopped review/checkpoint linked from FINDING; parent
OWNERSHIP-255823.md, PATHS-256145.md, test_abandonment.py and
test_routed_abandonment.py. Five product paths remain Claude-owned: tools/
single_worker.py and stage_execution.py under v12/python; intake.py, oci.py,
custody.py under v12/python/src/baton_v12/worker_manager. No ownership transfers
by this plan. Historical tests stay in their original dossier; add the following
small test modules here after assignment. Names below are planned deliverables,
not files asserted to exist today.

## Commands and repetition contract

Use an authorized isolated test runner, the current source candidate and a fresh
per-test temporary root; never the preserved deployment. Every module below must
exercise real manager/store code with fake engine/provider at the normal port,
close its handles and account for its own scratch resources. Coordinate any
fixture Git creation with the existing repository policy; no Git mutation in
the shared checkout. Set BATON_V12_DISK_ROOT to an operator-provisioned writable
disk-backed scratch parent outside the checkout and snapshots when the fixture
needs one. The old recorded /var/tmp/baton-w247941 is not a permission grant.
Missing suitable storage is an actionable runner prerequisite, not a test pass.

```sh
cd /home/sl/src/baton
export PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-real-jobs-adoption-gate:$PWD/work/records/2026/09/finding-v12-failed-run-resource-hold"
export PYTHONDONTWRITEBYTECODE=1
PY=/home/sl/.local/state/baton-v12-venv/bin/python
```

Current baseline command (two existing selectors; reviewed previously, not rerun
by tuner) is executable before writing R1 tests:

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_abandonment.TheComposedAbandonmentIsCalled.test_an_unresolved_submission_holds_the_root test_abandonment.TheComposedAbandonmentIsCalled.test_a_reconciliation_lifts_one_episode_and_the_act_proceeds
```

These two passes are sequential baseline evidence only. They do not cover the
five open findings. The per-command limits below are proposed test backstops,
not product guarantees or cumulative spending gates. Capture exit status,
elapsed time, exact source hashes and counter/receipt output. A timeout kills
only this isolated fake-boundary test process; it proves no daemon settlement.

## R1 — one exclusive submission before any destructive helper act

Outcome: one caller owns a pre-effect uncertainty episode; all concurrent or
restarted callers refuse before submission **or reclamation** while it stands.
Inputs: stopped custody.py and the two baseline cases. Proposed edit boundary:
custody.py and new test_hold_admission.py only, using existing transactions;
any additional shared primitive needs an enumerated ownership amendment first.

Deliver a barrier-driven two-connection race (no sleep-based ordering), a late
visible helper behind a standing hold, and crash points before/after submission.
Expected evidence: exactly one engine submit vector; zero stop/remove vectors
on the held path; unchanged root bytes; durable held episode readable on reopen.
Replay of the record must not authorize a second caller to submit.

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_hold_admission
```

Command becomes runnable when R1 supplies that focused module. Failure stays
held/unresolved, with exact helper/root/episode identity. Stop after independent
R1 acceptance; do not add clearance, resource guards or supervisor edits here.

## R2 — only exact settlement evidence clears one hold

Depends on accepted R1. Outcome: clearance changes one exact episode's eligibility
and nothing else. Paths: custody.py and new test_hold_clearance.py; oci.py only
if its engine-answer contract needs a coordinated bounded change.
Validate hold and clearance kind/state/signature and full attempt, canonical
resource/root, helper, image and episode binding. Require a precise provider
observation proving settlement of that submitted mutation. Plain observation
text, local CLI exit, an empty helper listing after client timeout, or any
nonzero/unaccountable answer is not enough to exclude a delayed daemon request.
If that evidence cannot be supplied, the selected result is still held.

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_hold_clearance
```

Evidence: positive exact-episode clearance and immutable replay; forged/wrong
signature, root, helper, image, episode and malformed/overflow/gap records all
refuse; second uncertainty remains separate; ambiguous answers never clear.
Fake engine only. Stop at accepted reader/clearance contract, before resource
reuse is claimed safe. Do not invent a generic engine-service prerequisite.

## R3 — every route to a held physical resource refuses

Depends on R1/R2. Outcome: restart, reuse and deletion cannot bypass the hold
through a different entry or alias. First enumerate every path that can touch
the exact held resources, then record one writer and the smallest path set.
Proposed additional boundary: worker_manager/workspaces.py
(assignment_workspace, adopted_assignment_workspace, line_assignment_workspace,
discard_workspace) with custody.py/oci.py callers and test_resource_guards.py.
These workspace paths are **not yet transferred or authorized for edits** by
the existing ownership record; coordinate the exact extension before editing.
Do not assume this provisional list is exhaustive or scatter fixes into all
callers without a recorded call graph.

```sh
timeout --signal=TERM --kill-after=5s 60s "$PY" -B -W error::ResourceWarning -m unittest test_resource_guards
```

Evidence: guard matrix for all enumerated entries, physical-root aliases,
reopen/restart and competing hold/reuse; no mutation behind a hold; unaffected
root still usable; validated clearance permits only the selected resource.
Real files/stores, fake engine. Missing path coverage blocks this stage. Stop
after independent protection acceptance, not after printing FROZEN.

## R4 — a bounded supervisor reports recovery or hold truthfully

Depends on R3. Outcome: one stranded attempt leaves a retained outcome before
the selected overall bound, with exact positive cleanup or explicit unresolved
resource holds. Paths: existing single_worker.py, stage_execution.py, intake.py,
oci.py and the parent two_job_supervisor.py, with new test_bounded_recovery.py;
edit only the boundaries shown necessary, keeping one Claude writer.
Carry one decreasing allowance across engine calls, actual store waits and
readback; measure lock contention and account for filesystem uncertainty.
An unproved I/O ceiling must remain a limitation, not a hard deadline claim.

```sh
timeout --signal=TERM --kill-after=5s 120s "$PY" -B -W error::ResourceWarning -m unittest test_bounded_recovery
```

Expected evidence through actual supervise: first-call crash, launch-absent
recovery, prior cancellation before/after declaration, lost discharge receipt,
restart/replay, interrupted/expired budget, contended store and uncertain engine.
No duplicate effect, unchanged old intent, no success without committed cleanup
and discharge; ordinary success remains covered. Use real stores/clock for lock
checks and controlled fake engine timing; label each. Stop at reviewed lifecycle
behavior. Existing broad-suite pass counts cannot substitute for these cases.

## R5 — independently validated grants and recovery command

Depends on R4. Outcome: a complete operator packet binds the two failed attempts
and produces verifiable readback without trusting typed IDs or granting itself
authority. New owned docs RECOVERY.md and GRANTS.md here plus
test_recovery_packet.py; retain original evidence at its canonical location.
Name exact authority/manager privileges and separate grant issuance from use.
Use only supported interfaces; reject wrong scope/generation/identity and
missing rights before destructive effects. No raw SQLite or docker-rm shortcut.

```sh
timeout --signal=TERM --kill-after=5s 60s "$PY" -B -W error::ResourceWarning -m unittest test_recovery_packet
```

Exercise the literal packet command on disposable stores/fake engine, checking
receipt replay, custody/retention and post-operation readback. Deliver exact
production recovery and reconciliation commands for separate owner selection;
**do not run them**. Positive cleanup and held/unresolved exits must be distinct.
Close this prerequisite only on independently accepted stage evidence and owner
disposition; actual preserved-run recovery remains a separately selected act.
