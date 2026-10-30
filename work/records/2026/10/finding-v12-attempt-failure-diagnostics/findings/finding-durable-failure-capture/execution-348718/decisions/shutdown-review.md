# Exact correction candidate independently accepted

baton.rvpc claim338596. Read current detail, complete new handoff/events through
338596 and thread through338449 (unchanged), scope/current PLAN, owner direct
exception, PROGRESS and candidate notes. Repository policy, operating guide,
protocol and DESIGN remain as read in this context. This review uses only the
W338305 direct disposable-workspace exception. No integration or live execution.

Accepted subject: CANDIDATE-338472.json SHA256
 a2fe281fbeac8e0c2fa58628aafc2c658a704ed5063a0eed689babced4d2ba83;
candidate-338472.tar.gz SHA256
 c2bcbadbb141bf4ffbecbbd346a5d185205c7c4cc795b6c295f3dfad3f3395e6.
Verified every one of1196 archive members against the candidate manifest, safe
regular-file paths, all1193 base hashes against Git objects at exact
fb48797903160aa764229d58f3a5beaf29648bfc, and exactly six changed/added paths.
Extracted a fresh reviewer-owned writable copy at review-338596/candidate; custody
modes were not imposed on test fixtures. All listed candidate bytes remained
unchanged after tests. Canonical existing targets still match base; no import.

Reviewed changed paths:

- v12/python/tools/authoring_enforcement.py: exact outer manager cutoff request,
  inner deadline composition, bounded snapshot reads/result publication and held
  partial evidence; existing outer kill/reap and admission/settlement semantics retained.
- v12/python/tools/authoring_shutdown.py: new same-incarnation monotonic deadline,
  phase reservations and interruptible main-thread operation limits. Repeated begin
  does not renew the allowance; outer process remains the manager backstop.
- work/records/2026/09/finding-v12-single-implementation-proof/baseline.py: optional
  shared deadline for cleanup, accounting, publication, closing and final reporting;
  reports cleanup failure instead of retaining its earlier stale field.
- v12/python/tests/manager/shutdown_fixture.py and test_authoring_shutdown_deadline.py:
  new candidate-native fake-boundary/real-process regressions and deadline checks.
- v12/python/tests/manager/test_authoring_manager_guard.py: the sole existing-test
  edit adds optional shutdown=None to the workload stub. Existing assertions and
  expected behaviors are unchanged. Standing test-change authority applies.

Independent command from fresh candidate/v12/python:
`python3 -B -m unittest tests.manager.test_authoring_shutdown_deadline tests.manager.test_authoring_enforcement tests.manager.test_authoring_manager_guard`.
Explicit PYTHONPATH=candidate/v12/python:candidate/v12/python/src,
PYTHONDONTWRITEBYTECODE=1, fresh disk root review-338596/disk and retained
BATON_SHUTDOWN_EVIDENCE=review-338596/composition. Outer timeout150s; each matrix
process20s plus5s reap as implemented. Passed44 tests, no skips, in72.891s unittest
time /73.374157594s measured command time. No broader suite repeated. Evidence
focused.log/focused.json and eleven composition cases are bound by
review-338596/REVIEW-EVIDENCE.json SHA256
bbd79069cd7678445c80a61f394328b9a80313de317bec439678171b469ede9e.
Hash/source/read overhead unmeasured. Author366.732553117s across six commands and
historical prior Work costs remain distinct; nested case times are not double-counted.

Confirmed cooperative blocked-sweep and absent-writer/pending-cleanup expiry cases
publish workload and final guard state before the transmitted manager cutoff; the
manager exits without SIGKILL. Pending cleanup/output does not prevent exact token
return. Delayed/stuck guard publication, workload publication, cleanup sweep and
accounting yield bounded held/partial evidence with step information. Unknown engine
expiry retains revoked/unreturned permission and typed uncertainty. Pre-serving
signal prevents invocation; repeated deferred signal and original bounds remain
visible. Existing late/unbound/wrong-runtime, manager exclusion and restart/envelope
checks pass. All eleven independent manager start/reap pairs match, PIDs are absent,
and real workspace guards are reacquired. Retained fixtures are disposable and are
not original run stores. No required file was unreadable.

No blocking defect found in this bounded candidate. Its distinction between
execution cessation and output acceptance aligns with the selected primary lifecycle,
LIM-4/OBS-3/REC-1: this change does not modify token settlement or infer success from
report presence, expired time or manager death. Phase evidence identifies the last
entered step; it is not a sampled stack or independent cessation receipt. The main
thread's alarm is a cooperative interruption mechanism, not proof that arbitrary
kernel I/O can always be interrupted. Process kill/reap is still the manager backstop;
if outer publication cannot complete, earlier evidence remains and the missing report
is incomplete, never acceptance. No real Docker cessation/authentication/deployment
claim follows from fake engine boundaries. Normal matrix return is orderly fake-create
refusal, not successful live authored output. Full Git-backed proposal suites were
excluded to preserve the no-Git-mutation boundary.

The deadline/ending behavior remains one coupled outcome; no decomposition needed.
Independent acceptance expires the W338305 direct exception now. Pass to owner for
separately selected human integration/checkpoint and real v12 validation. Keep Work
open and both W333485/W333486 consumer gates until corrected accepted-base delivery
is observed; this candidate acceptance alone does not authorize those executions.
Proposed human checkpoint: `fix(v12): coordinate authoring shutdown deadlines and final reports`.
Exact reviewed six-path import requires ordinary base/target/ownership preflight;
no correction, mode repair or unreviewed bytes are authorized by this verdict.
