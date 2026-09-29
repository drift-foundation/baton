# W306614 — failed-pipeline reporting and interruption presentation

## 2026-09-29 — assigned research boundary

Owner report T306614/306614; tuner claim306616, binding306619. Research only, independent of W247941. Inspect retained two-jobs-247941-01 evidence and focused deterministic reproductions; propose a bounded later Claude implementation with coordinated ownership. No live provider/engine, rerun, cleanup, active W247941 file edit, broad redesign or new adoption dependency. Preserve provider failure in the human-facing outcome; failed Jobs must not prematurely stop unrelated runnable Jobs. New dossier evidence/tests belong to this claim.

## 2026-09-29 — confirmed diagnosis, bounded research delivery

**Observed retained evidence:** outcome submitted14:33:04.609Z, finished14:40:24.322Z:439.713 seconds elapsed, stopped=interrupted, state=held, two implementation/zero review admissions. Both exact runtime identities are recorded destroyed; cleanup retained with absent observations, no outstanding/unresolved cleanup or uncertainty. The two provider stdout result records report api_error/is_error=true and the exact supported OAuth-expired/refresh-failed constant, with provider durations37ms and70ms. Those durations are provider-reported, not host failure-observation times. Outcome held reasons mention only missing attributed verdicts. Its facts must not be rewritten to claim success or unknown cleanup. EVIDENCE.json pins source/outcome/log hashes and selected safe fields; no native session backup or credential was read.

**Owner-reported:** both implementation stages exceptional/authentication_failed and reviews blocked; Ctrl-C displayed baseline.SupervisorInterrupted traceback. No terminal transcript or exact first-failure-observation timestamp was supplied. We did not reopen deployed stores or query a live engine to manufacture either. The retained result confirms provider failure and interruption; deterministic main reproduction confirms exception leakage. Current supervisor matches reviewed candidate306393; OPERATOR-306505 selects that supervisor with the frozen single-job runtime.

**Confirmed cause A:** two_job_supervisor.supervise.should_continue (around648–676) records generations, optional test turns, caps and serving deadline only. It never reads per-Job terminal/failure/blocked dependency state. job_manager.manager.serve (804 onward) deliberately loops on that injected predicate, discarding all but the last sweep report; the generic service is not an all-Jobs-finished scheduler. A real supervisor plus real serve reproduction with terminal failed sweep reports still performs four simulated1s sleeps until its4s serving bound. It does not preserve authentication_failed in the outcome. This is structural, not a slow provider or cleanup wait. Successful-only completion detection is absent here too; that implication is code-derived, not a new observed live run.

**Confirmed cause B:** supervise intentionally publishes outcome, restores termination handling and then raises baseline.SupervisorInterrupted (922). main calls it inside try/finally but has no matching except (1014–1038). Handle cleanup still runs; the summary and return afterward are skipped. A main reproduction publishes the outcome, raises that exact exception, observes empty stdout and all three handles closed. Existing test_two_jobs.test_an_interruption_publishes_the_outcome_and_still_raises tests the lower-level contract, not CLI presentation; preserve that contract. Single-job baseline.main already catches the exception, prints outcome location and returns130; reuse that presentation pattern at the two-Job CLI boundary.

**Verification:** test_diagnosis.py2PASS0.002s. These are explicitly current-defect witnesses, using simulated status/sweep/time/lifecycle and mocked main acquisition; not full connected failure/cessation acceptance. They assert the defect and must be converted/complemented with desired-behavior regressions in later implementation. No active W247941 files or product implementation changed. Proposed scope and independent acceptance are in PROPOSAL.md. No dependency added; no live retry/cleanup selected.


# Independent research review — 2026-09-29T14-51-38Z

Reviewer baton.rvpc claim306667; tuner306616/pass306662. Canonical events through306667; complete T306614/306614 read. ACCEPT research diagnosis and PROPOSAL.md as a bounded implementation proposal for later owner selection. This does not authorize edits to active W247941 files or close the defect as fixed.

All six CANDIDATE-306616.json hashes and all seven EVIDENCE.json file hashes matched before reviewer record updates. Independently reran test_diagnosis.py with accepted frozen manager-source imports, -B -W error::ResourceWarning and30-second timeout:2PASS0.002s, zero warnings. Confirmed frozen manager.serve's predicate-driven loop and supervisor publication/raise/main-finally boundaries by source inspection. The mocked failure report is a localization input, not an actual canonical status-schema fixture; it proves omission of terminal inspection, not the proposed classifier's correctness. Main witness establishes escaped expected exception, empty summary output and closed handles; publication/cleanup internals remain mocked. Retained outcome and owner report support diagnosis, not a measured first-failure latency or captured terminal transcript.

Proposal is appropriately bounded: report each selected failed episode promptly without cancelling unrelated useful work, stop only after all selected pipelines cannot progress, preserve original safely attributed cause separately from cleanup/missing-verdict facts, and catch only the expected published interruption at the CLI boundary. Keep existing lower-level raise contract and exact cleanup/uncertainty handling. Any implementation must validate canonical snapshots, failed-dependency versus independent-runnable classification, and real published diagnostic attribution through the existing connected deterministic fixture. Never infer permanent failure from generic blocked/empty/unknown status. The accepted matrix covers mixed failure/success, all-success, duplicate observations, interruption, publication failure and unknown cleanup; no live call is needed for those regressions.

Research limitation: the existing safe diagnostic helper has packet-specific identities/layout. Reuse or a minimal adapter is a later coordinated scope choice, not permission to copy the whole helper, weaken provenance or print raw provider text. Owner must select later Claude implementation and coordinate two_job_supervisor.py/test_two_jobs.py ownership with W247941; any additional helper path must be recorded then. No new dependency/adoption gate, protocol redesign, credential repair, rerun or consumed-instance mutation is introduced.

Operational read note: the reviewer initially requested EVIDENCE.md, which does not exist; the handoff's actual EVIDENCE.json was then read in full and hash-verified. No required evidence remains unread. No product/test/PROGRESS edit, deployed store access, engine/provider or cleanup operation occurred. Reviewer owns only this append-only review and FINDING/PLAN checkpoint updates. Return baton.decide for later implementation selection.

## 2026-09-29T17-20-22Z — owner implementation selection pinned; review requests corrections

Owner306697/306698 selected bounded implementation after W247941 closure; wake
307583 satisfied that dependency. This supersedes historical research-only and
owner-waiting scheduling restrictions for this Work. Review review-2026-09-29T17-20-22Z.md assesses
candidate307593. Preserve per-Job stop and narrow CLI catch as partial progress.
R1: status-reader BaseException catches serving Ctrl-C and continues until deadline.
R2: original safe cause/identity is not collected and later unreadable status
erases earlier failure evidence. R3: connected failure/diagnostic matrix remains.
Independent9PASS0.008s plus two confirming probes0.0017395629547536373s; full
hashes and observations in review-evidence-307718.json. No live/product changes.
Return directly baton.impl within existing scope; accepted delivery to owner.
Run03 was already accepted and W247941 closed before implementation; author
warning treating it as unperformed is explicitly superseded, evidence preserved.

## 2026-09-29T17-33-48Z — correction review307831: accepted slices, one remaining gap

review-2026-09-29T17-33-48Z.md accepts R1 serving interruption, R2 immutable failure history and R3
connected failed/mixed pipeline behavior. Independent16PASS1.7014698840212077s;
full candidate hashes and observations in review-evidence-307831.json.
R2 cause consumption remains: exchange.diagnostic is supplied only by mock test,
whereas actual structured provider diagnostics live in retained adapter reports.
Wire bounded attributed report consumption and targeted positives/negatives;
retain canonical terminal cause too. Explicit unknown fallback remains correct.
Return baton.impl within scope, preserve accepted slices; no new owner gate.

## 2026-09-29T17-44-50Z — retained reader wired; boundary corrections remain

review-2026-09-29T17-44-50Z.md preserves accepted lifecycle slices and confirms actual report
consumption. Independent18PASS1.6585647830506787s plus counterexamples:
ancestor symlink escapes storage; array JSON/provider raises; nested terminal
fault discarded. Source follow-up: late cause needs exact first-failure identity
and a dedup-aware prompt update. Full hashes/evidence in review-evidence-307909.json.
Return bounded corrections directly baton.impl; no scope/owner gate or live run.

## 2026-09-29T17-51-34Z — independent implementation acceptance307960

ACCEPT candidate307931; review-2026-09-29T17-51-34Z.md closes selected review findings.
Independent23PASS1.6975614010589197s and original counterexamples now pass.
Full4 hashes in review-evidence-307960.json. Reader ancestry/nonblocking/shapes,
nested canonical cause and same-identity deduplicated supplements verified;
prior interruption/history/mixed-Job acceptance preserved. Return baton.decide
for owner satisfying disposition. No live/deployment/rerun/Git authority implied;
future packet must bind new supervisor, historical run03 remains unchanged.
