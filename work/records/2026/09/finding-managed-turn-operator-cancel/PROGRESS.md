# Progress

## 2026-09-17 — baton.tuner, claim 195317

Started explicitly assigned bridge implementation after canonical detail,
standalone claim, complete work-events/thread reads and dossier revalidation.
Initial PROGRESS.md was absent; recorded the operational finding in FINDING.md
and T195314 message195328 before creating this author record. No prior progress
has been replaced. Product changes and deterministic verification are in progress.

## 2026-09-17 — baton.tuner, claim 195453 — awaiting independent review

Read complete canonical handoff/discussion and reviewer triage. Continued preserved
claim195317 candidate. Corrected the generated claim-held prompt to require the
standalone claim, added exact loaded-session refusal, fixed socket cleanup on
runtime-start/facts/settlement-restore failure, finished README commands and
corrected the new continuation test to await completion rather than session
construction. Existing acp_baton_bridge.test.mjs expectations were unchanged.
New operator_control.test.mjs tests exact targets, idempotency, cancellation vs
completion, journal restart/corruption, duplicate socket ownership, stale
authority, changed retry instructions, unknown teardown, session drift and fake
ACP tool cancellation/timeout/acknowledgement. Fake peer and package test list
are the only other test-related paths changed.

Verification: final npm test from tools/acp-baton-bridge passed 138/138 tests
in 14.647480s, exit0. git diff --check passed. Deterministic fake provider only.
The existing descendant-escape test explicitly reports no PID namespace in this
environment: this does not certify production process-domain containment. No
production cancellation, restart, deployment, model execution or Git mutation.

Earlier attempts this turn: sandbox Unix socket listen EPERM, node --test
5.077590s; focused diagnostic 0.078427s; direct test output 5.009529s confirmed
EPERM. Permitted npm test then exposed startup socket leakage and a new test
predicate race; interrupted that stalled run through its own execution session
(exit130) at 81.546572s. Both were corrected before the final passing run.
Measured test-run total this turn 106.359598s; an accidental npm test invocation
at repository root failed ENOENT before running tests (duration not measured).
Earlier author cumulative spending remains unknown. The execution API allowed
the npm test escalation used for Unix sockets; no production authority was used.

Candidate files and hashes are captured in CANDIDATE-195453.json and
candidate-195453/. BASE-195317.json and base-195317/ retain prior base bytes.
Newest prior review: review-2026-09-17T15-06-00Z.md (triage only). Independent
review must evaluate this complete candidate; no acceptance is claimed here.

## 2026-09-17 — baton.tuner, claim195504 — retry correction awaiting review

Addressed P2 in review-2026-09-17T15-12-08Z.md. Persisted original target inside
the accepted continuation payload and moved duplicate comparison before the
current-target guard. Exact retries return status without mutation or dispatch;
changed target/spec/changes refuse. Stale cancellation remains guarded by the
current active target. Added one regression covering admission, completion and
restart, asserting no extra prompt or pending request and no journal mutation.
Only src/operator_control.mjs and test/operator_control.test.mjs differ from
candidate195453; all other product hashes match that reviewed candidate.

Verification: npm test, default execution boundary, 139/139 passed, exit0,
14.657881910s. git diff --check passed. Author measured cumulative test time is
121.017479910s plus unknown earlier author spending. Reviewer previous measured
14.631876361s plus unmeasured probe is separate. No production operations, live
provider execution or Git mutation. Prior containment limitations remain.
CANDIDATE-195504.json and candidate-195504/ supersede candidate195453 for
acceptance; prior candidate and reviews remain intact.
