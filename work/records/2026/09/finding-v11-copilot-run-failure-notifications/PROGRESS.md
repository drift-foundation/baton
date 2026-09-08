# Progress

2026-09-07 — baton.prompt: owner-authorized foreground implementation started.
The existing notifier and tests were read; live canonical incident/runtime
projections confirmed the response shapes. No workflow recovery or live notifier
execution performed.

Implementation complete: added exact-action-owner incident and failed-runtime
attention, stable failure versions, simultaneous/late representation correlation,
and persisted pairing acknowledgement that preserves new-incident recurrence.
Notifications contain only incident/runtime locators. Existing busy admission,
socket acceptance, authority checks, cursor persistence and advisory policy remain.

Validation: python3 -B -m unittest tools.test_codex_copilot_notifier -v.
Final result: 28 tests pass in 0.003 seconds (13 existing, 15 additive).
Initial sandbox run passed 26 cases but the existing Unix-socket bind was denied;
approved execution outside the sandbox passed all 27 then-current cases. Final
inspection identified a new-incident-after-dismissal deduplication concern; the
pairing cursor correction and its added regression produced the final 28 passes.
No broad tests or live provider/notification run. git diff --check passed, but
these three pre-existing notifier files are still untracked in this checkout;
the retained prior reviewed candidate supplies the meaningful delta baseline.

Candidate, baseline delta and verification account are retained under evidence/.
Await independent review, then operator restart of the existing notifier only.

## 2026-09-08 — baton.prompt, approved foreground correction

Addressed review-2026-09-07T23-44-02Z.md within the existing three-file scope.
attention collects derived expired runtime locators separately from deliverable
attention. poll preserves only existing accepted hashes and their paired markers
for those locators; accepting unrelated attention merges current acknowledgements
without erasing this stale memory. Reported recovery/absence/ownership change
prunes it, and a changed failed version remains new attention. No cursor schema,
runtime protocol, bridge behavior or deployment changed.

Added eight test methods covering expiry/identical renewal after cursor reload,
unrelated accepted delivery, pairing across expiry/dismissal and a new incident,
rejected/busy unaccepted runtime and paired attention, reported recovery, absence,
ownership, stale incarnation replacement, first-observed expiry and a new failed
transition. All 28 previous test methods are AST-identical to the reviewed
candidate. The original review probe used a stale fixture without provenance;
the new fixtures include the canonical provenance=derived field confirmed in
projection.py. The independent review evidence is preserved unchanged.

Validation: python3 -B -m unittest tools.test_codex_copilot_notifier -v.
Sandbox run passed 35 tests but denied the existing temporary Unix-socket bind.
Approved execution with that permission passed all 36 tests in 0.004 seconds.
No full-suite run, live advisory, worker launch or notifier restart. Exact output,
three-file candidate, manifest, deltas against review-114371 and test preservation
audit are in evidence/correction-2026-09-08/. Awaiting independent review;
restart remains gated on sign-off and live delivery remains a separate check.
