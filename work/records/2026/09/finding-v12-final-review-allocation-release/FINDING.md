# V12 final reviewer allocation remains reserved

Owner E316900 on W236087 authorizes bounded follow-up implementation. Discovery: baton:work/records/2026/09/finding-v12-managed-session-resume/review-2026-09-30T15-26-48Z.md and REVIEW-EVIDENCE-316831.json. Prior live correction/restore acceptance is preserved.

Observed residual: STATUS-COPY-316831.json reports completed Job316689 final review attempt5eb882b5efcc8b41b507d51c2d64af614318adeeb66e52899350b676c15f56ca, allocation reserved, released_at null. Runtime685195e7f98d023ac1bf01e0b66dc19679f13df36c26251ed0ade6737678fb65 is independently absent; retained outcome records cleanup retained. Earlier reviewer/implementation allocations released. This is suspected terminal scheduling/accounting defect; whether one more authorized normal tick would release it and its capacity impact need deterministic reproduction. Do not mutate the completed deployment to test the hypothesis.

Scope: trace final review conclusion/cleanup and scheduler allocation release through normal Job termination. Ensure proven cessation and cleanup drive release without requiring a new Job or manual sweep after success; if existing contract intentionally defers release, substantiate exact supported lifecycle and prevent misleading completion/resource reporting. Do not conflate worker allocation with workspace resource token. Revalidate scheduler.release in job_manager/scheduler.py, terminal sweep in manager.py, pooled composition in tools/stage_execution.py and supervisor stopping boundary. Product files only where causally necessary; no general scheduling redesign.

Acceptance: focused fake-provider/engine scenario completes independent review then stops at normal supervisor terminal condition; final allocation must release once with matching assignment and reason when cessation/cleanup proven. A later independent Job can use freed capacity; no duplicate allocation/release on replay or restart. Negative running/unknown/unsettled cleanup keeps capacity held, never frees early. Preserve accepted verdict/proposal and original immutable evidence. Include ordinary accepted review and correction-then-accepted if their code paths differ. No live models/engine, deployed cleanup or broad stress. Return independent review with candidate hashes and evidence.

Independent top-level record because this follow-up may outlive accepted W236087. No containment or blocking edge to W236087; no dependency on the other follow-up. No broad hardening gate.

Ledger binding: W316918, routed baton.impl at creation under E316900. Sibling follow-up W316915 is independent, not a prerequisite.

## 2026-09-30T16:18:01Z — independent acceptance, claim317216

Confirmed cause supersedes the suspected-cause status above: the pre-act projection omitted cleanup settled during conclude; a subsequent sweep previously released the allocation. A fresh post-act reconciliation corrects the terminal-tick timing using unchanged release/hold rules. Independent 24-test acceptance passed in 5.407s; all four candidate hashes matched. See review-2026-09-30T16-18-01Z.md. Recommend owner acceptance; no deployed repair.

Explicit qualifications of author evidence: a later Job queuing forever is not established because another sweep could release the allocation. The proven defect is its reserved state at natural completion. The live-runtime-named test actually sets execution_runtime=ended in its helper and does not prove that named combination; acceptance uses composed terminal settlement and cleanup negatives. Preserve historical author records with these qualifications.

Author residuals F1–F4 remain outside this correction: W316915 empty-store status fixture, registry omissions, adjacent signature expectations and unmeasured import-path suites. They are not independently resolved, waived or newly assigned by this acceptance.
