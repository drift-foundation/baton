# V12 adoption backlog checkpoint, 2026-11-26

This is a recovery index for W321608. Canonical v11 Work details own assignments and dependencies until cutover. The table at the end lists all 104 open team Works selected by the supported v11 work-graph read at snapshot 386446, including older and non-v12 items. Read current Work detail before scheduling. A queued item can already have product commits pending administrative disposition.

## Keep in view

| Subject | Record and next deliverable |
| --- | --- |
| Immutable Job identity | W386374, parked, owner route, no dossier binding. Separate opaque immutable Job IDs from editable names. Preserve stable replay identity across rename and migrate existing references (stages, worker homes, attempts and receipts). Works already have stable IDs. UUID format and migration design belong to this Work. |
| Architecture cleanup | W386228, queued for owner, assessment completed and reviewed. Start with separate provider and verifier environment construction through the shared assignment loop. Keep vendor-specific behavior independently changeable. Recovery-journal reader duplication and fresh-deployment documentation are additional proposals. See the [plan](../../11/finding-v12-system-maintainability-review/PLAN.md), [assessment](../../11/finding-v12-system-maintainability-review/REPORT.md) and [review](../../11/finding-v12-system-maintainability-review/review-2026-11-25T17-23-19Z.md). |
| Worker inbox and held field Job | W386413. Job main-thread delivery checkpointed at 03137d53. Worker inbox remains under development. Job M386446 on gen-21b9296e has an owner answer recorded; serving runtime 35c7fe81 lacks reconciliation. Preserve the Job, Work and checkpoint. Need a disposable same-instance runtime-upgrade proof. No separately titled upgrade Work found in this snapshot. |
| Receipts and status | W385263. READY FOR INTEGRATION and DONE checkpointed at 57eb1c0b. M386415 is recorded DONE. M386419's joined integration at 03137d53 cannot be represented by the exact-tree receipt. M386443 records pending-versus-rejected model wording. |
| Field defects and extra capacity | W386413 dossier records third-worker selection, heterogeneous credential configurations and live pool adoption gaps, the M386440 missing-input/citation fault, and the M386442 misplaced reviewer reply. Those findings are recorded; no standalone Work for each is asserted here. W386048 separately tracks provider-selected integration and home ordering. |
| Context reuse | W385853 dossier holds the [conversation-resume proposal](../../11/finding-host-worker-instruction-separation/FOLLOW-UP-RESUME-WORK-REV2-2026-11-24.md). Retained provider homes and restart-safe owner replies are separate capabilities. Check for a bound implementation Work before dispatch. |
| Cutover and parked intake | W321608 [adoption plan](PLAN.md). Prove parked intake and rediscovery without execution, inventory graph edges and claims, then select a cutover. Keep W386374 parked during that proof. |
| Delivered items to reconcile | W386365 submission while serving checkpoint 0cb8b0de; W386295 MANUAL Jobs checkpoint 76b2f2b2; W386308 TUI, W386361 phase names and W386395 held-review display have delivered source. Use dossier and canonical state before assigning further changes. |

## Open Work inventory

| Work | Phase at snapshot | Canonical title |
| --- | --- | --- |
| W2 | parked | Design v12 isolated agent workers |
| W3 | parked | V12 M2: Prove local isolated execution |
| W7 | block | V12 M3: Build the proposal pipeline |
| W8 | block | V12 M4: Certify agent and remote runtimes |
| W9 | block | V12 M5: Prove resilience and scale |
| W10 | block | V12 M6: Prepare rollout and adoption |
| W9901 | queued | V12 M6: Model hierarchical teams and shared approvers |
| W16830 | block | M3 foundation: Separate approval attestations from decisions |
| W28880 | block | Add searchable tags to v12 Work |
| W29401 | parked | Expose v12 Work labels through protocol and CLI |
| W29408 | block | Surface v12 Work labels in the TUI |
| W32391 | parked | M2: Certify local OCI lifecycle on Podman |
| W33755 | parked | Revise direct-topology conformance and certify local OCI |
| W39366 | parked | Harden the v12 supervised dogfood path |
| W39435 | parked | Flatten v12 canonical dossier storage |
| W39649 | parked | Normalize worker telemetry and introspection |
| W44342 | parked | Settle or cancel the engine-side custody operation |
| W48697 | block | Complete the global v12 receiving-boundary inventory |
| W61981 | block | Make v12 verification context complete and explicit |
| W62098 | parked | Make retained v12 proposals complete against their import base |
| W62535 | parked | Preflight v12 dogfood before staging source |
| W63214 | parked | Make v12 source staging respect canonical entry bounds |
| W91072 | parked | v12: Enforce live workspace byte and entry ceilings |
| W103525 | parked | V12: Certify parallel scheduling with deterministic traces |
| W103950 | block | V12: Extend stage composition hardening coverage |
| W106052 | parked | V11: Existing Work has no canonical parent attachment operation |
| W110783 | parked | V12: Resume implementation ending after checkpoint fencing |
| W111793 | parked | V12: API model adapters and testing roles |
| W114077 | parked | V12: Investigate retry discard runtime quiescence refusal |
| W114252 | parked | V12: Represent explicit executable and mode-change scope |
| W114516 | parked | V12: Investigate intermittent worker-entry engine failures |
| W115981 | block | Resolve and verify the twelve v12 suite checks diagnosed by W115824 |
| W116975 | block | Complete review_cycles receiving-boundary inventory coverage |
| W116977 | block | Complete intake receiving-boundary inventory coverage |
| W116979 | block | Complete authority_port receiving-boundary inventory coverage |
| W116981 | block | Complete interrogation receiving-boundary inventory coverage |
| W116987 | block | Complete sessions receiving-boundary inventory coverage |
| W116992 | block | Complete attempts receiving-boundary inventory coverage |
| W116995 | block | Complete workspaces receiving-boundary inventory coverage |
| W116997 | block | Complete oci receiving-boundary inventory coverage |
| W116999 | block | Complete handshake receiving-boundary inventory coverage |
| W117002 | block | Complete documents receiving-boundary inventory coverage |
| W117004 | block | Complete credentials receiving-boundary inventory coverage |
| W117006 | block | Complete exchange receiving-boundary inventory coverage |
| W117008 | block | Complete launch receiving-boundary inventory coverage |
| W117017 | block | Complete source_boundary receiving-boundary inventory coverage |
| W117020 | block | Complete custody receiving-boundary inventory coverage |
| W117022 | block | Complete posture_slots receiving-boundary inventory coverage |
| W117024 | block | Prepare bounded output attempt-key fixture scope |
| W117026 | block | Resolve the surviving worker-entry operation-identity inventory delta |
| W121039 | parked | Resolve review-cycle helper-call inventory residuals |
| W121042 | block | Resolve review-cycle nested fence inventory probes |
| W129838 | parked | V12: Close concrete worker operations during stage construction unwind |
| W136578 | parked | V12: deferred integration-result recovery and storage hardening |
| W144335 | parked | V12: Re-enter sealed intake without losing the original held reason |
| W144813 | parked | V12: Preserve the first integration launch refusal across re-entry |
| W165786 | parked | V13: Harden the platform using v12 parallel Jobs |
| W174357 | parked | W103525: Design operator-designated replacement for v12 |
| W257624 | parked | V12: Bounded failed-run recovery and durable resource hold |
| W266096 | parked | Reviewer turn starts without claiming queued review Work |
| W270664 | parked | V12: Remove workspace-deletion I/O from database transactions |
| W319007 | parked | ACP operator control rejects fresh-start configuration after session creation |
| W321608 | active | Assess replacing v11 coordination with v12 for one development workflow |
| W321776 | queued | W61981: Deliver paired worker and operator verification contexts |
| W324316 | parked | Prepare automatic v12 terminal-result handoff to v11 coordination |
| W339626 | parked | Standardize the next-run path instead of bespoke execution packets |
| W370747 | block | Assess design changes to reduce v12 workflow fragility |
| W371072 | block | Plan residual template and adapter admission contracts |
| W371073 | block | Plan safe typed adapter failures through existing diagnostics |
| W371075 | block | Plan routine create while serving and installer prerequisites |
| W371076 | queued | Plan joined deterministic ordinary template workflow proof |
| W371295 | block | Compose qualified role contract admission and provenance |
| W371296 | block | Qualify actual role adapters against selected contract |
| W375516 | block | Prepare fresh installed startup prerequisites and read-only validation |
| W375517 | block | Implement shared creation admission ledger and immutable configuration recovery |
| W375518 | block | Compose create while serving and instance-addressed observation commands |
| W375519 | block | Prove installed ordinary creation recovery and whole-path startup timing |
| W376254 | queued | Complete supported read-only prerequisite and store validation |
| W376587 | queued | Propagate typed adapter failures through existing diagnostics |
| W376588 | block | Prove joined matched typed adapter failure reporting |
| W376731 | queued | Retain versioned role admission carriers and lane provenance |
| W376741 | block | Enforce role compatibility before creation and dispatch |
| W383239 | queued | Reconcile v12 delivery plan and remove stale scheduling instructions |
| W385227 | queued | Make installed status lead with Job outcomes and failures |
| W385251 | queued | Correct offer retirement integration regressions before next native kickoff |
| W385263 | queued | Research shared Job liveness model for status monitor and future TUI |
| W385292 | queued | Independently review retained native labels candidate 04648e1b |
| W385331 | queued | V12 native messaging handoffs and reviewer-dispositioned discovery |
| W385424 | queued | V12 status: surface attributable worker-declared failure causes |
| W385427 | queued | V12 monitor: actual running duration and named deadline countdown |
| W385454 | queued | V12 compatibility fixtures: explicit integration target permissions |
| W385635 | queued | V12 kickoff: validate exact task statements and referenced inputs |
| W385769 | queued | V12: phase-specific provider invocation limits |
| W385853 | queued | Consolidate host agent policy and separate v12 worker instructions |
| W386048 | queued | V12: provider-selected integration turn refused; home prepared before launch |
| W386057 | queued | Prevent Git fixture discovery of protected repositories; correct N4a incident |
| W386228 | queued | Review v12 architecture, maintainability and operational complexity |
| W386295 | queued | Owner-paced MANUAL Job selection, budget and explicit closure |
| W386299 | queued | Show the operator why a review was held when the worker had no usable report |
| W386308 | queued | Add a compact read-only TUI for watching v12 Jobs |
| W386361 | queued | Show phase names beside roles in the TUI detail |
| W386374 | parked | Give v12 Jobs immutable opaque IDs separate from operator-facing names |
| W386389 | queued | Clarify phase admission wording in the operator TUI |
| W386413 | queued | Give each v12 Job a main conversation and restart-safe owner replies |
