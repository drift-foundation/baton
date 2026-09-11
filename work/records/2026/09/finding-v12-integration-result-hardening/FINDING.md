# Deferred integration-result hardening — W136578

Created from W133117 review136558 at the safe handoff following author136400.
Authority: owner M136417 and W71830 FINDING/PLAN2026-09-10T13:06:51Z.
This independent follow-on is parked; it is not a child or prerequisite of the
two-Job demonstration. No implementation or runtime allocation exists.

## 2026-09-10 — exact deferred scope

1. **Observed static limitation:** integration/reconciliation.publish_result
   calls _live_assignment before external/local publication replay. A completed
   publication retried after its assignment retires is therefore not currently
   established as recoverable. Defer this retirement/interrupted-return case
   and the cross-product of target advance with publication/local-journal cuts.
   The required uninterrupted P path uses the current live assignment.
2. **Unproved additional cases:** external receipt creation before local
   adoption interruptions, receipt/policy changes across later retries, and
   broad persisted-tamper permutations. Reuse existing exact-retry/tamper
   evidence; no claim these additional cases passed.
3. **Observed static limitation:** _repository_identity returns None on profile
   errors for protected paths, and _prove_isolation then relies on resolved
   directory comparison. Defer failures resolving otherwise distinct protected
   repository/common-directory aliases and broader storage layouts. The
   demonstration requires actually resolved, distinct Git storage; producer,
   target, symlink and linked-worktree exclusions already have evidence.
4. **Deferred Q/R verification:** full crash matrix across content import,
   target-reference CAS, Authority receipt and final release; exhaustive competing
   writer/target races and restart combinations; multiplication across /1 and
   no-drift /2 scenarios. Keep existing holds/exclusion/recovery code and reuse
   its accepted controls. The immediate path must still prove actual import,
   post-import verification, aligned target/cursor, terminal linkage and one
   writer. Failures must remain held and never be labelled successful.

These are deferred capability claims, not deleted protections or permission to
weaken genuine defect tests. Owner direction explicitly supersedes exhaustive
matrix completion as a prerequisite regardless of milestone necessity. The
bounded supported demonstration is ordinary serial A then B with immutable
source submissions, actual separate combined verification, independent receipts,
exact target-write authority and honest terminal evidence.

Source/evidence locator:
baton:work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-custody/
contains exact candidate136400, earlier independent reviews, and
evidence/review-136558/result.json with the passing independent transition.
The parent DELIVERY-SCOPE-2026-09-10.md indexes the current minimum and deferrals.

Revisit after the standalone demonstration when separately prioritized, and
before advertising broader restart/storage/concurrency guarantees. An actual
failure preventing the accepted A/B or standalone demonstration is assessed
immediately as its smallest bounded correction, not hidden in this parked Work.

## 2026-09-11T00:40:24Z — owner acceptance applied

Owner M140286/M140288 in T133129 and baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md / PLAN.md at 2026-09-11T00:30:54Z govern. This explicitly supersedes older mandatory, essential and no-waiver wording below ONLY where it makes stronger robustness/resilience demonstrations prerequisites. Ordinary correctness, authorization, honest evidence, existing source scopes, cumulative budgets and file ownership remain. Deferred claims are unproved, never passed. No new planning Work or approval round is required.

Remain parked and nonblocking, with no implementation/runtime allocation. The new ruling expands the deferred proof boundary beyond exhaustive matrices: even representative fault-injection, crash/restart, adversarial alias/tamper and race/ended-grant demonstrations do not gate W71830 solely to establish robustness. Keep the current protections and passing controls; do not claim broader guarantees from them.

Index H-5: further R completion/finalization interruption, competing-runtime/lease/target race, storage-alias and persisted-tamper demonstrations; revisit after feasibility or before advertising those guarantees. Index H-6: improve test_stage_execution.py vcs/ancestry assertion to check process exit status; reviewer140320 independently checks exit0 in evidence/review-140320/ancestry.json, so the actual ancestry result is established and helper hardening does not block A/B. No product/test edits are scheduled here now.

Related unproved indexed deferrals remain with their existing owners: W130229 general observation hardening and W71879 C-1 deliberate fault-Job/companion-negative standalone proof. Any real defect preventing/falsifying the selected ordinary A/B path is handled immediately by its bounded owner, not hidden by this parked status.

## 2026-09-11T01:05:51Z — H-7 detached observation follow-on custody

Planning clarification at W130229 reviewer140487's safe handoff, under owner
M140286/M140288. W130229 accepts the selected existing public Job/attempt readers
without source changes. This parked Work now owns its deferred observation
follow-on, superseding the earlier statement that W130229 retains that future
scope. No execution claim, source authority, budget or blocking dependency added.

H-7: StageObservation.observe_integration creates a SimpleNamespace without
binding_for, allowing the global Work/target/first-integrator fallback; its
runtime-row/assignment early return also omits model-free B completion. Both
remain unresolved on source9cf2927f. Revalidate the exact required detached
consumer before correction; broader foreign-handle, database/mode/sidecar,
capability, restart and layout guarantees remain unproved. Do not instantiate
a serving factory simply for status or advertise this detached surface as the
accepted StageExecution.observe completion reader. Revisit after feasibility
or before promising those guarantees; a concrete actual standalone-reader gap
returns immediately for the smallest required correction.

Permanent evidence: baton:work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-per-job-readonly-observation/
FINDING.md, OBSERVATION-HANDOFF-2026-09-11.md and
review-2026-09-11T01-05-51Z.md. Fault-C remains with W71879 C-1.
