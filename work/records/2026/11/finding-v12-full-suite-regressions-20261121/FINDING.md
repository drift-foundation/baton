# W385517 — full-suite regressions, 2026-11-21

## Owner selection

Owner explicitly selects these failures as the current showstopper before further delivery/W9901 planning. Fixes are v12 source/tests; v11 is coordination authority only. No new live model Job selected.

## Observed

Owner-run suite at c06befa89f557f2999a57ef0758bf6f6d7007bb9, unchanged source:11841 collected/executed,11829passed,7failures,3errors,2optional skips; no required skips,duplicates or unaccounted. Exact logs/accounting/source identities/supervised evidence preserved at work/records/2026/10/finding-v12-development-coordination-pilot/evidence/full-suite-20261121T202947Z/.

Three clusters: six tests.tools.test_stack cases report negative snapshot write age and fail expected freshness/output; tests.tools.test_next_run_flow.JoinedFlow.test_two_tasks_and_failed_start_recovery_after_one_installation returns1 for recovered execution; three tests.tools.test_dogfood_retry_engine.DockerPublicRetry cases refuse activate_assignment because the attempt has no committed claim. These are observed symptoms, not settled root causes. Prior disclosure does not waive failures.

## Bounded acceptance

Independently diagnose baseline and candidate, preserve product claim/freshness/recovery invariants and genuine coverage. Correct faulty fixture assumptions where proved; correct product defects where proved. Do not remove cases, weaken ownership checks or merely inflate deadlines to get green. Necessary test changes are authorized; implementer selects paths and records rationale. Focused deterministic verification and the affected Docker fixture tests are selected; no live provider, installed-instance changes or broad stress. Disposable Git authority applies; protected main Git state belongs to owner.

All ten cases and affected focused regressions must pass with exact accounting; independent review, integration and human checkpoint precede owner full-suite rerun. Close only after clean required full-suite acceptance at the fixed checkpoint, including no required skips/errors/duplicates/unaccounted. Existing optional exclusions stay explicit. W9901 waits; no unrelated UX/team changes.

## E385520 diagnosis and bounded repair

Confirmed baseline: exact10 case selection gives6failures/3errors/1pass. Stack helper deliberately writes mtime now+1 (then increasing), violating current future-timestamp refusal. Preserve freshness invariant; use actual write time and observe after publication. Docker fixture passes fixed W.NOW while public capability construction opens store on deployment clock; accept settlement expires before submit_claim, so activation correctly refuses absent claim. Align fixture timestamps to actual deployment time; retain activation checks. Recovery retained output is settled with verification passed, but outer child_status=-15 and final enforcement publication recorded; focused retry passes, confirming timing dependence rather than recovery permission failure. Existing cooperative Python handler does not survive interpreter teardown indefinitely. At completed child final accounting/publication, set SIGTERM/SIGINT to SIG_IGN (retained OS disposition), leaving outer SIGKILL/deadline/cessation checks unchanged; update exiting-child assertion from callable handler to SIG_IGN. No deadline inflation.

Codxpc isolated ownership: tests/tools/test_stack.py, tests/tools/test_dogfood_retry_engine.py, tools/authoring_enforcement.py, tests/tools/test_next_run_flow.py and bounded new regressions as needed. Groups tools-pure, manager-pure, manager-engine. Candidate in work/scratch/w385517/candidate, basec06befa89f557f2999a57ef0758bf6f6d7007bb9; evidence/repair-385520 retains baseline and full-run extracted recovery results. No protected Git or live-instance edits.

## 2026-11-21 — E385520 ready for independent review

All10 original cases pass; candidate adjacent222 pass (225 distinct candidate IDs,232 pass executions). Baseline6failures/3errors/1pass and deterministic finalization negative-control1failure preserved. Total verification190.975258s. Five-path candidate treec5ec0445e7215ce84188f3eb6884300fc67fcbd75dabbb922451f083123d9d15, basec06befa89f557f2999a57ef0758bf6f6d7007bb9, manifestecf0cfbd205aed3e4ba1ed262f59aa90b0781b47c13b5b860e67a25f51a8bd5d; exact evidence/repair-385520/REPORT.md and manifest.json with snapshots/patch/logs/ledgers/source identities. Freshness fixture corrected without threshold changes, Docker fixture clocks aligned without weakened claim checks, final child exit uses ignored OS stop signals after accounting while outer kill/cessation/deadline remains. Protected index/HEAD unchanged; host v12 clean. Current step independent review, then reviewed import/human checkpoint (`fix(v12): preserve completed child exit and align regression fixture clocks`) and owner full-suite rerun. Work stays open until full required acceptance; no broad run or owner Git act performed. Last discussion M385518; claimE385520.
