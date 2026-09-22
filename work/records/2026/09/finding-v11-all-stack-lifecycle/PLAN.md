# Current plan

## Completed — 2026-09-22, owner claim235316

Independent review accepted implementation; reviewed registration is installed
and host aggregate status verifies coverage of all15 services across three
stacks. Main/reviewer are healthy; stopped coder is truthfully reported as an
overall failure. This supersedes pending install and older routing/implementation
instructions below. No restart is needed for the command change. The separate
coder recovery requires explicit operator action; no live service mutation was
performed. Git changes remain for Slawomir.

## Implementation state — owner claim235256

Prompt implemented the approved scope in `tools/infra_deployment.py`, `justfile`, `docs/BATON-SETUP.md`, and new focused `tests/work/test_infra_deployment.py`; the existing per-stack controller/tests are unchanged. New tests use only stand-in processes. `infra-stacks.json` and `INSTALL.md` in this dossier supply the current deployment packet. Independent review remains before registry installation; no service restart is required to use the wrapper/registry. Earlier outstanding-all-steps and tuner routing text below is historical, superseded by this current state.

Owner-approved bounded implementation; independent review before live rollout. Current executor selection: tuner per M235250, superseding M235233. Pass235253 had already returned Work to baton.ops before tuner read the concurrent clarification; return routing to baton.tune and a fresh successful claim are required before tuner implementation resumes.

1. Revalidate `justfile`, `tools/infra.py`, `tests/work/test_w20_infrastructure_lifecycle.py`, and lifecycle instructions in `docs/BATON-SETUP.md`. Choose the smallest explicit registration format and orchestration entry point. Preserve the existing single-stack entry point for maintenance and existing callers.
2. Make the normal just start/stop/status surface cover the registered deployment. Validate registration before lifecycle mutation, reject duplicate canonical stack paths and malformed membership, define deterministic start/reverse-stop order, and serialize conflicting deployment-wide invocations. Reuse per-stack identity checks and locks. Define honest partial-start failure behavior without stopping pre-existing healthy stacks. Status must inspect/report every member and return failure if any member is unhealthy or uninspectable; stop should attempt each registered member and aggregate failures.
3. Add focused deterministic coverage: three registered stacks; main healthy with reviewer stopped; partial failure and aggregate exit status; stop ordering; malformed/duplicate registrations before side effects; single-stack compatibility; start does not resume dispatch. Test edits and fixtures within these lifecycle files are approved under standing test authority. Do not broaden into a full test discovery run or live provider execution.
4. Update operator documentation, including how newly provisioned stacks join the explicit registry, single-stack maintenance, and recovery of stale post-reboot lifecycle state. Prepare a deployment registration/installation packet for main, rview-pc and codx-pc; do not stop/start the live deployment during implementation.
5. Hand off changed paths, focused test evidence and rollout steps for independent review, then owner acceptance. No Git mutations.

File ownership: M235250 restores tuner selection for justfile, tools/infra.py (or one narrowly scoped sibling orchestration helper), lifecycle-focused tests and docs/BATON-SETUP.md under a fresh implementation claim. Coordinate before editing any overlapping path. Keep this record's FINDING/PLAN current; actual implementer owns PROGRESS. No other agent's existing changes may be overwritten.

## Historical handoff — claim235224 (routing superseded by M235233)

Initial source review complete: review-2026-09-22T03-41-11Z.md; SOURCE-BASELINE-235224.json. Pass to baton.tune for the already-approved implementation, then baton.bug for independent candidate review and owner rollout. Revalidate exact file ownership before edits. The review records bounded proposed registry/failure defaults and concrete compatibility regressions; tuner pins final routine choices before implementation without another planning-only handoff. No product or test changes made by reviewer; PROGRESS remains implementer-owned.

## Historical handoff — claim235246

Return to baton.ops per owner follow-up M235233. Initial review and baseline remain available; steps 1–5 are outstanding for prompt-assisted implementation and independent review. Tuner changed only FINDING.md and PLAN.md to pin the routing correction. No implementation or tests executed; additional verification spending 0 seconds. PROGRESS.md remains untouched and implementation not started.

## Current continuation — M235250 read after pass235253

Owner restored tuner selection while this handback was in flight. Return existing Work from baton.ops to baton.tune for a fresh claim; retain the bounded implementation plan and source review. Implementation remains unstarted, with no product/test changes or verification spending. This is a routing race, not a product or protocol defect.


## 2026-09-22T03-50-29Z — independent review claim235291 accepts bounded implementation

review-2026-09-22T03-50-29Z.md and REVIEW-EVIDENCE-235291.json accept the exact candidate and installation registry. Existing single-stack controller/tests match the initial baseline. Author15 new plus6 compatibility cases are attributed; six additional independent no-service probes pass in0.002326763999008108s. Three existing deployment manifests parse, alias matches and registration destination is currently absent. No live health or rollout inferred. Next baton.ops installs reviewed registration and runs read-only host status, rechecking destination/alias. No restart, live model or Git mutation performed by reviewer.

Current action: owner registration installation and host status per INSTALL.md. This supersedes pending independent candidate review and all older implementation/routing continuation text; implementation is accepted at the recorded hashes. Preserve actual host status failures if any; do not silently restart services.
