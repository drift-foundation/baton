# W385625 / M385782 — joined reviewer correction for K review

Outcome: focused deterministic recovery now traverses actual reviewer admission,
delivery, worker execution, output freezing/custody, verdict collection and
checkpoint verdict recording. Candidate is pending independent review; no
acceptance, main import or live installation is claimed.

## Identity and paths

Base: `acf29092bf1e31fd5085bbb53d54db317b24adb7` (owner checkpoint acf29092).
Candidate: SHA-256 of candidate-manifest.json, `5cb76d8267838da78e49cccac03ec3fb1a12a6d257a37c785f5a19f12fc5a9f0`.
Seven changed paths are fully enumerated in that manifest with base/candidate
hashes. `candidate.patch`, `base/` and `candidate/` preserve the exact delta.
No new commit. Isolated author tree: work/scratch/w385625-joined-385784.
Canonical evidence: work/records/2026/11/finding-v12-retained-recovery-verification/evidence/joined-385784/.

Product paths: v12/python/src/baton_v12/job_manager/review_driver.py;
v12/python/src/baton_v12/worker_manager/review_cycles.py;
v12/python/tools/single_worker.py; v12/python/tools/stage_execution.py;
v12/worker/claude_agent.py. Documentation: v12/python/DEPLOYMENT.md.
Only test path changed: v12/python/tests/job_manager/test_retained_recovery_execution.py
(additive joined class; prior accepted cases unchanged).

## Confirmed gap and correction

The acf29092 producer probe ran the actual workload with a scripted provider
and a failing real verifier. Normal ending froze/collected the real proposal,
released the writer, and left the line idle with no review checkpoint. The
DEFAULT owner command approved recovery; the real manager verified/handed off,
admitted and claimed the reviewer, then preparation refused a None checkpoint.
`connected-probe.log` retains that failure. This was beyond the previously
accepted source's handoff-only proof.

The review-line owner now freezes the original released writer using its
committed release fence after positive retained cleanup. It does not create a
writer or assignment, reopen the producer, or alter original frozen outputs.
A later writer/line advance refuses. Frozen base/head must equal the approved
candidate, on first execution and replay. Ordinary freeze remains behind its
existing public signature; recovery uses a separate checked entry.

Stage composition resolves the recovery checkpoint before attaching the actual
reviewer. A separately pinned `recovery-review.json` delivers candidate and
verifier-account identities plus the handoff digest. The workload presents it
to the provider; its substantive report echoes `recovery_digest`. The host
requires exactly that claim on the findings output before recording any
verdict. Missing/foreign evidence holds with no verdict; rejection is preserved.
The original admitted task is not rewritten. No new profile, timeout, automatic
retry, W385695 behavior, or specification change is included.

## Connected evidence and verification

`focused-final.log` / `focused-final-run.json`: 95 tests, 95 passed, zero
failures/errors/skips; unittest 17.554 s, measured wall 17.829027 s.
This includes seven new joined cases and 88 targeted existing review-driver,
workload-report and checkpoint-lifecycle cases. `diff-check.txt` records clean
diff checking. TEST-ACCOUNTING.json retains every development run, including
initial fixture mistakes and red reproductions; unknown early wall durations
remain unknown. Earlier 94-case focused run passed before the final replay
checks/refactoring; only the final run binds the sealed bytes.

The seven joined cases establish:
- DEFAULT owner read/approval/admission, actual reviewer delivery and collected
  accepted verdict, with one original producer and no implementation redispatch.
- A substantive scripted rejection remains recorded as rejected.
- Missing or foreign verifier-evidence binding records no verdict.
- A review-only successor reaches acceptance with zero additional verifier
  calls; its own verification execution record is absent.
- An advanced line cannot be reviewed as the retained candidate.
- Restart/recomposition after handoff reaches review without another verifier.

The scripted provider reads the actual delivered source and recovery document
at its ordinary process boundary. It asserts the source contains the original
retained change, the account says passed and the prompt carries the exact
handoff digest, then authors its selected accept/reject report. The host takes
custody of that result and records its verdict through ordinary owners. Counts
prove one verifier, two total stage starts (original producer and reviewer),
no successor implementation stage, and unchanged original custody bytes.
The source/Authority/custody/offer/assignment/collection/verdict receipts are
real fixture-owner operations, not fabricated rows or FakeOperations.

Evidence reused, not rerun: M385779 / review-2026-11-23T00-02-34Z.md accepted
materialization, crash-cut reconciliation, profiles and refusals; its 168/215/508
checks and acf29092 packaging24 remain their own historical evidence. Ordinary
review's foreign-candidate and malformed-report checks were included narrowly
in this run. No whole module pair, 508-case composition suite, packaging run,
new native kickoff or live engine/model was run here.

## Explicit limits and continuation

This is deterministic orchestration/workload proof, not live diagnostic or
model judgment quality. The analysis side is a labelled scripted finite
analysis-failed endpoint through its product API after the real producer
ending; accepted Stage1-A analysis behavior is reused, not re-proved as a
positive live-analysis chain. All subsequent owner/reviewer operations are
shipped operations, with only engine/provider boundaries simulated. The
no-daemon fixture copies the pinned recovery document into its simulated input
mount because the inherited symlink view correctly fails the workload's
no-follow bounded reader.

If the original line has advanced, recovery refuses rather than resetting it
or reconstructing it over another writer. No capability to repair that case is
claimed. The recovery input binds attributable verifier metadata/digests; it
does not mount host verifier log paths into the review container. No reviewer
acceptance is inferred from verifier success or structural checks.

K should independently review the seven exact paths, especially released-writer
fence reuse, replay/current-checkpoint checks, pinned input lifetime and the
new report binding. No owner decision is requested. After acceptance, import
requires current-target overlap checks; packaging/worker-image qualification
and any live rollout are separate. Main source/index/history and all existing
instances remain untouched.

## Reproduce

Use a disposable copy of acf29092, verify manifest base hashes, apply
candidate.patch or copy candidate/ bytes, and verify all candidate hashes.
From that copy's root, set PYTHONPATH=v12/python/src:v12/python and run the
exact command array in focused-final-run.json with a 120-second ceiling.
Fixtures use disposable disk-backed repositories and execute real Git and
verifier subprocesses; no daemon, credentials or network provider is needed.
