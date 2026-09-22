# V11 deployment-wide lifecycle commands

## Installation verified — 2026-09-22, owner claim235316

Prompt installed the independently reviewed registry at the selected external
deployment root after rechecking destination absence, canonical alias and all
candidate hashes. Installed SHA2560407fdd42db431a5149e377c8d9e6d737f38c72c08b6569fdd4df5a78dd1b301
matches review235291. `just status /home/sl/baton-v11` in the host context now
reports main9 services healthy, rview-pc3 healthy and codx-pc3 stopped with stale
pre-reboot lifecycle records. Overall succeeded=false and nonzero exit are the
correct result, demonstrating that the missing coder is no longer hidden.
No service stop/start, dispatch change or Git mutation occurred. Restore of the
stopped coder is a separate operational action, not an unimplemented lifecycle
feature. The requested command change and registration are installed.

## Current implementation selection — 2026-09-22, claim235256

Prompt assists the owner-held claim after tuner returned its claim untouched. This supersedes the transient M235250 continuation request; no other implementation owner remains. Routine design choices: required `infra-stacks.json` with version1 and ordered `{name, directory}` entries, relative to the selected deployment root; main must be listed exactly once. Canonical paths cannot escape the deployment or duplicate another member. No implicit registry fallback. A new `tools/infra_deployment.py` wraps the unchanged single-stack controller; just recipes call the wrapper. Start preflights every manifest, then stops launching later stacks at the first runtime failure and reports them not attempted. Earlier healthy/started stacks remain running. Stop and status visit every member despite individual errors, with one aggregate exit status. A root deployment lock serializes aggregate commands; existing per-stack locks remain authoritative for each member. The initial install only adds explicit registration; it does not restart services.

## 2026-09-22 — observed gap and owner decision

Confirmed: `just start MAILBOX`, `just stop MAILBOX`, and `just status MAILBOX` invoke `tools/infra.py` for only MAILBOX/infra.json. The current deployment also has independent rview-pc/infra.json and codx-pc/infra.json service sets. After the power-outage reboot, the main services ran while all three reviewer services remained stopped with stale lifecycle records. Ready, unclaimed review Work consequently had no readiness consumer, despite global dispatch being running. Starting the reviewer set restored pickup.

Owner decision: v11's normal `just start/stop/status` must manage and report all stacks in the selected deployment. This is deployment integration, not a change to workflow routing, claims, or global dispatch semantics.

Use explicit deployment stack registration, not recursive directory discovery or inferred running processes. Preserve independent per-stack lifecycle state and an explicit single-stack maintenance path. The current installation must register main, rview-pc and codx-pc. Do not hard-code these names or operator paths into generic product code.

An all-stack success must mean all registered stacks meet the requested condition. Reports identify each stack, including stopped, missing, invalid or failed ones. Partial failure must not be reported as overall success or silently omit another stack. Preserve exact process-identity safety and existing refusal to adopt or kill unknown processes. Starting services never implicitly resumes dispatch. An immediate stop remains immediate; retain the separate drain-aware operation's existing semantics.

Scope is a small v11 lifecycle correction. No v12 scheduler work, service discovery, daemon, automatic reboot registration or live model tests. No running service should be restarted merely to develop this change. Prepare installation instructions and registration for the existing deployment, and verify with deterministic fake services before owner rollout.

## 2026-09-22T03-41-11Z — reviewer source revalidation, claim235224

review-2026-09-22T03-41-11Z.md confirms the one-mailbox entry points and records implementation boundaries. Immediate stop must preserve valid-owned-state shutdown despite malformed infra.json; stale start must remain an explicit refusal, with documented single-stack recovery. Registry validation is distinct from per-member inspection failures, which must be reported without hiding other members. SOURCE-BASELINE-235224.json pins the four unchanged source inputs. Implementation selected for tuner under the existing owner plan; no live rollout performed.

## 2026-09-22 — owner routing correction recorded by baton.tuner, claim235246

On reading the complete thread at pickup, tuner found owner follow-up M235233 (2026-09-22T03:40:18Z): finish bounded plan review and return this existing Work to baton.ops for prompt-assisted implementation under owner claim; do not begin implementation or route automatically to another coder. This supersedes the tuner implementation selection above and in the initial review/handoff. The later reviewer pass does not record a new owner decision overriding M235233. Preserve the completed review and baseline as preparation evidence. Tuner returns the Work to baton.ops without product/test edits, test execution, live service actions or Git mutation. The technical scope remains approved; implementation and its verification remain outstanding.

## 2026-09-22 — concurrent owner clarification M235250

After pass235253 released the claim to baton.ops, the final canonical reread exposed concurrent owner message M235250: continue tuner implementation; M235233's return-to-ops instruction is explicitly superseded. This supersedes the routing correction immediately above. The pass had already committed before tuner read this clarification, so tuner cannot continue execution under the released claim. Return routing to baton.tune is needed for a fresh claim; no recovery or replacement Work is needed. Approved technical scope, independent review and no-live-restart limits remain unchanged.


## 2026-09-22T03-50-29Z — independent review claim235291 accepts bounded implementation

review-2026-09-22T03-50-29Z.md and REVIEW-EVIDENCE-235291.json accept the exact candidate and installation registry. Existing single-stack controller/tests match the initial baseline. Author15 new plus6 compatibility cases are attributed; six additional independent no-service probes pass in0.002326763999008108s. Three existing deployment manifests parse, alias matches and registration destination is currently absent. No live health or rollout inferred. Next baton.ops installs reviewed registration and runs read-only host status, rechecking destination/alias. No restart, live model or Git mutation performed by reviewer.
