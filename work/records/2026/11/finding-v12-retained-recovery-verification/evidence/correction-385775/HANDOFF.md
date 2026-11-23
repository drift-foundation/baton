# W385625 / M385773 correction for independent delta review

Implemented by baton.codxpc under E385775 in isolated
`work/scratch/w385625-correction-385775`. No new native kickoff, main product
edit/import, main Git mutation, container/model run or existing-instance change.

## Exact candidate and provenance

Candidate identity: SHA-256 of `candidate-manifest.json`:
`6a3ad526bba39d9395f9f3f96fe91d98ace0cb387c774df9355f7b18d4563c97`.
Retained parent: `4e869a1db07d1063b988704a3c892bfbfac1f2fa`.
Pinned cumulative base: `14276917cf4eceaf494dc04fe158aaad2440e7d6`.
No new commit was created. `correction.patch` binds seven paths against the
retained parent; `cumulative.patch` and `candidate/` bind all fifteen product/docs
paths against the pinned base. `base/` and `retained/` preserve comparison bytes.
The manifest enumerates every path and base/retained/candidate SHA-256.

Original custody is unchanged. `retained-proposal/` copies the exact native
proposal, including its objects bundle and full 26-path native change;
`retained-provenance.json` records origin/file hashes. `provenance-check.json`
verifies that native path set, eleven product hashes and original evidence
checksums. Original native dossier files are preserved through the bundle; they
are not silently imported over the current coordinator-owned FINDING/PLAN.
The immutable native review remains at sibling `../native-review-20261122/`.

## Corrections

1. Shipped bootstrap accepts and preserves explicit recovery-verification
   configuration. StageExecution composes the production seam/runner from the
   instance and configuration; ManagerOperations exposes the optional seam.
   Unknown configuration members/revisions refuse. DEPLOYMENT.md documents it.
   The joined DEFAULT-owner command proof now drives the middle acts using real
   StageExecution and manager.reconcile, recreating composition each tick. It
   checks the gate remains closed before handoff. No direct advance call is
   substituted for that serving proof.
2. A committed result with no Stage1-B verification account is reported as
   unaccounted, and execute replay finishes that account using the original
   result, argv, context and time. It does not spawn another child or invent an
   account from an intent. Passed/failed restart, concurrent duplicate replay
   and cancellation-after-result cases prove one child and a closed gate until
   a valid handoff. Existing identity/unknown/expiry/refusal tests remain.
3. ACCOUNTING-CORRECTION.md explicitly supersedes native report inaccuracies:
   authority 511 OK; four historical job-manager nonpassing cases, not six;
   corrected native run table and precise simulated/real boundaries. Original
   evidence is byte-preserved.

Affected test path: only the retained candidate's new
`v12/python/tests/job_manager/test_retained_recovery_execution.py`. Changes add
fault-cut/replay/configuration cases and replace direct middle-act calls with
production composition. Assertions were not removed to hide a defect. The
joined fixture fences its queued original placeholder (its retained failure
was fixture-seeded) before real serving; the original frozen evidence remains
unchanged. The later scheduler-admission assertion is explicitly FakeOperations.

## Verification and limits

See TEST-ACCOUNTING.json and retained logs for all attempts. The sealed focused
acceptance has 168 tests, 168 passed, zero failures/errors/skips, unittest
8.339 s / measured wall 8.571807 s. Targeted compatibility has 215 tests,
215 passed, zero failures/errors/skips, unittest 18.938 s / wall 19.182295 s.
It covers bootstrap, ManagerOperations delegation, serving drivers and the
existing analysis seam alongside the new verification seam. `git diff --check`
passes. No full-suite or live-model claim is made.

Analysis reports remain scripted. The joined runtime proof ends at the durable
review handoff; reviewer admission is separately simulated, and no reviewer
container or substantive verdict is executed. This delta does not claim a
new end-to-end model/reviewer proof. Original native review limitations and
known baseline environment failures remain historical, not retested here.

## Reproduction

Recover the retained parent from retained-proposal/objects.bundle into a
disposable repository, then apply correction.patch there; alternatively copy
candidate/ bytes over a disposable checkout of the pinned base. Verify all
manifest base and candidate digests before/after. Never apply to the main
checkout without independent review and overlap/import checks.
From the isolated repository root use PYTHONPATH=v12/python/src:v12/python
and run the exact command arrays in focused-sealed-run.json and
compatibility-focused-run.json. Ordinary fixtures create disposable disk-backed
repositories; no live provider or daemon is needed.

Review requested from K: exact delta and preserved earlier native fixes,
configuration wiring, crash-cut reconciliation and evidence qualifications.
No new product decision is requested. Mainline import and owner Git remain
separate from this candidate handoff.

Additional compatibility attempt: the whole test_stage_execution module with
bootstrap/delegation hit its configured 240-second subprocess limit. The
log records 461 completed OK lines, 0 FAIL lines, 0 ERROR lines;
no completed-suite verdict or full-module coverage is claimed. Exact elapsed
wall was not persisted by that harness. The child was killed/reaped by
subprocess.run; subsequent process inspection found no remaining process for
that test command or isolated candidate. Existing native services were left
untouched. Targeted compatibility above completed successfully; the broader
module remains uncompleted in this correction evidence.
