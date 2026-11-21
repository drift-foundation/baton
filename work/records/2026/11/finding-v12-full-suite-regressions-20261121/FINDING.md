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

## Owner full rerun at d1919f95 — 2026-11-21

Evidence: evidence/full-suite-20261121T212320Z-3778097/. 11842 collected/executed,11839passed,2optional skips,0failures,1error,0required skips/duplicates/unaccounted. Source unchanged. All original ten cases passed; serial512 and supervised1 passed. Remaining error: tests.manager.test_authoring_manager_guard.ManagerComposition.test_manager_loss_retains_unknown_and_restart_does_not_repeat, JSONDecodeError at line126 reading action.json. Empty/partial publication race is a hypothesis, not a confirmed cause. Clean-suite gate remains unmet.

## Owner-selected accounting summary wording — 2026-11-21

Owner approved replacing the confusing passed-plus-optional arithmetic as the main accounting summary with explicit outcome counts. Show collected, passed, optional skipped, failures, errors and unaccounted with the final verdict; retain required skips, duplicates and fixture anomalies visibly when applicable. For the observed run, communicate 11842 collected,11839 passed,2 optional skips,0 failures,1 error,0 unaccounted -> FAILED. The error causes failure; no test is missing. Preserve all accounting/exit-status semantics and machine-readable summary fields; this is display-only, not a waiver or reinterpretation.

## 2026-11-21 — E385529 publication correction

M385526/M385528 scope revalidated at d1919f95. Fixture action.json is created by Path.write_text before bytes are written; await_file checks existence only. Force the post-open/pre-write interleaving, then publish the complete action atomically after retained partial output. Preserve real manager-loss/unknown/no-repeat assertions. Fixture helper and deterministic tests live in tests/manager/test_authoring_manager_guard.py. Secondary explicit accounting display and output cases live in tools/parallel_test.py and tests/tools/test_parallel_runner.py. Exclusive isolated candidate work/scratch/w385517-385529/candidate; no overlapping main-source edits, live runs or full rerun. Evidence: evidence/repair-385529/.

## 2026-11-21 — baton.codxpc E385529 ready for review

Confirmed fixture publication race: action.json becomes visible empty before Path.write_text writes JSON. Deterministic post-open reader reproduces character-0 decode error; new regression rejects legacy writer. Candidate publishes complete action by sibling rename after partial output; existing manager-loss/unknown/no-repeat semantics preserved. Secondary explicit accounting display leaves JSON/verdict logic unchanged. Three-path candidate tree e467b92f20a73340835ed52ee84777cb3d5da0ba9050fe8d8ab04d0289d00f04 over d1919f951f919e0064386d131a9bfa457e9eaaec. Exact immutable bytes, manifest, root cause, initial instrumentation failure and final 81/81 focused passes (28.187153s) at evidence/repair-385529/REPORT.md. No full-suite rerun. Next independent review, then reviewed integration/checkpoint and owner acceptance; no outstanding product decision.

## Final full-suite acceptance — 2026-11-21

Owner full run at735061237c4e176a25db4a22afa96dd78f1491bd finished23:41:20Z exit0; source unchanged (aa96c2335b090d7608ed3e3cf531f5bc2f04aebad4c574e4e6a06fa65aa266d1).11844collected/executed,11842passed,2explicit optional skips,0failures/errors/required skips/fixture anomalies/duplicates/unaccounted. Parallel,serial512,supervised1 phases all green; all prior failing IDs resolved. Full evidence preserved at evidence/full-suite-20261121T233239Z-3923644/. Required acceptance achieved; recommend owner closure of W385517. Optional bind-mount-capability and >64MiB proof exclusions remain exactly recorded, not silently waived required tests. This establishes this checkpoint, not blanket future reliability.
