# V13 campaign plan

## 2026-09-15 — owner confirms the usable-v12 delivery path

Slawomir confirmed the path: "yes that's the path. We need to be on the other side to finally benefit from the new model where we can begin work on v13". The immediate objective is usable v12, with its parallel development Jobs enabling subsequent v13 work.

Current delivery sequence:

1. Complete W61599 focused independent review, preserving the owner instruction to defer unrelated baseline suite failures.
2. Complete W161234 required context reuse and useful correction/restart proof. Tuner implements after Claude preparation and the independently reviewed W61599 shared-file release, using the accepted architecture and concrete B/C packets.
3. Connect the minimal read-only monitor and establish readiness for actual use, including the narrow production qualification facts that remain necessary.

Preparation must shorten this path. Classify findings by whether they concretely prevent this usable release; defer unrelated baseline repairs and broader hardening to W165786 after readiness. Preserve execution correctness, isolation and honest reviewed result collection; do not manufacture success or add speculative release gates. Do not repeat accepted architecture reviews or broad suites merely because work changes hands.

After readiness, use v12 parallel Jobs for small bounded v13 tasks. Keep v11 as the current coordination authority during preparation; no backlog copying or unselected authority cutover. This usable-release objective does not falsely close W2 while its historical open children remain. Record readiness explicitly against the selected minimum outcome.

Owning Work: W165786. Canonical scheduler state remains in Baton.

## Additional owner assignment — 2026-09-15

W103525's latest FINDING and W2 FINDING explicitly assign remaining broad
certification and operator replacement to v13, superseding their v12 gate.
Retain original dossiers and accepted scheduling evidence. No implementation
is selected; W103525 remains parked. W174357's already-queued independent design
review may finish as nonblocking pre-work and must not delay ready v12 delivery.

| Existing Work | Release assignment | Ledger containment |
| --- | --- | --- |
| W103525 | v13: remaining certification and operator-designated replacement | Standalone; preserved |
| W174357 | v13: retained operator-replacement design and existing review | Standalone; preserved |

The original 42-member audit below is historical; these are later explicit
additions, not corrections to its retained snapshot or new Work identities.

Current owner disposition 2026-09-14T09:04:44Z: park this umbrella until v12
readiness. A parking-only handoff to baton.feat supplies the route-handler act;
it does not select v13 execution. W165782 now owns finalizing the selected
classification and updating this membership table, serially under the same
reviewer. Awaiting-classification-selection wording below is superseded; current
consumer triage remains required for unresolved/mixed rows. Preserve actual
ledger containment and all existing Work identities.

1. [done] Create the v13 umbrella and pin the strategy of using v12 parallelism
   to expedite its delivery. Preserve W2's minimum v12 release boundary.
2. [selected; graph operation unavailable] W103950 belongs to v13 hardening.
   The deployed v11 CLI has no existing-Work reparent command; FINDING records
   the limitation and supersedes the initial handler-attachment assumption.
   Use the explicit release-membership table below as a stated stopgap; preserve
   its actual ledger graph, identity, canonical record and children.
3. [done planning; W165782 selected] Classify other existing Work as v12-required,
   v13-hardening or unresolved. Propose exact relationship changes with reasons;
   do not duplicate backlog or infer membership from historical titles.
4. [pending v12 readiness] Select independent v13 development tasks for parallel
   execution through v12, with explicit file ownership, inputs, reviewed results
   and recovery. The basic read-only monitor is a v12 prerequisite; richer UI
   and broad performance work remain here.
5. [deferred] Deliver the classified hardening outcomes through bounded Jobs,
   reusing accepted evidence and maintaining truthful cumulative verification.

No product implementation or execution is currently assigned by this umbrella.

## Selected existing members

| Existing Work | Release assignment | Ledger containment |
| --- | --- | --- |
| W103950 | v13: expanded stage composition hardening | Still standalone; no reparent operation available |

W165782's complete audit is
`baton:work/records/2026/08/finding-v12-isolated-agent-workers/RELEASE-CLASSIFICATION-165799.md`.
Its retained canonical graph is RELEASE-GRAPH-165799.json beside it. The audit
enumerates all65 open Work at snapshot165832 with technical reasons, minimum
monitor reuse/gaps, unresolved correctness questions and exact proposed gates.
This is release planning, not an alternative live claim/dependency ledger.

## Additional members — classification selected; current-state reconciliation in W165782

Owner selection2026-09-14T09:04:44Z adopts these release assignments subject to
W165782 current-state reconciliation; older "awaiting" cells below are historical
audit labels superseded by this selection. These rows extend the documentary
stopgap. They do not change containment, close Work or authorize v13 execution.
W165786 itself is the umbrella; W103950 above is already selected.

| Existing Work | Release assignment | Ledger containment at snapshot165832 |
| --- | --- | --- |
| W8 — V12 M4: Certify agent and remote runtimes | Selected v13; execution deferred | Still child of W2; unchanged |
| W9 — V12 M5: Prove resilience and scale | Selected v13; execution deferred | Still child of W2; unchanged |
| W10 — V12 M6: Prepare rollout and adoption | Selected v13; execution deferred | Still child of W2; unchanged |
| W9901 — V12 M6: Model hierarchical teams and shared approvers | Selected v13; execution deferred | Still standalone; unchanged |
| W16830 — M3 foundation: Separate approval attestations from decisions | Selected v13; execution deferred | Still child of W7; unchanged |
| W28880 — Add searchable tags to v12 Work | Selected v13; execution deferred | Still standalone; unchanged |
| W29401 — Expose v12 Work labels through protocol and CLI | Selected v13; execution deferred | Still child of W28880; unchanged |
| W29408 — Surface v12 Work labels in the TUI | Selected v13; execution deferred | Still child of W28880; unchanged |
| W32391 — M2: Certify local OCI lifecycle on Podman | Selected v13; execution deferred | Still child of W3; unchanged |
| W33755 — Revise direct-topology conformance and certify local OCI | Selected v13; execution deferred | Still standalone; unchanged |
| W39366 — Harden the v12 supervised dogfood path | Selected v13; execution deferred | Still standalone; unchanged |
| W39435 — Flatten v12 canonical dossier storage | Selected v13; execution deferred | Still standalone; unchanged |
| W39649 — Normalize worker telemetry and introspection | Selected v13; execution deferred | Still standalone; unchanged |
| W48697 — Complete the global v12 receiving-boundary inventory | Selected v13; execution deferred | Still standalone; unchanged |
| W63214 — Make v12 source staging respect canonical entry bounds | Selected v13; execution deferred | Still standalone; unchanged |
| W91072 — v12: Enforce live workspace byte and entry ceilings | Selected v13; execution deferred | Still standalone; unchanged |
| W111793 — V12: API model adapters and testing roles | Selected v13; execution deferred | Still standalone; unchanged |
| W114252 — V12: Represent explicit executable and mode-change scope | Selected v13; execution deferred | Still standalone; unchanged |
| W115981 — Resolve and verify the twelve v12 suite checks diagnosed by W115824 | Selected v13; execution deferred | Still standalone; unchanged |
| W116975 — Complete review_cycles receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116977 — Complete intake receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116979 — Complete authority_port receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116981 — Complete interrogation receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116987 — Complete sessions receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116992 — Complete attempts receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116995 — Complete workspaces receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116997 — Complete oci receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W116999 — Complete handshake receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117002 — Complete documents receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117004 — Complete credentials receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117006 — Complete exchange receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117008 — Complete launch receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117017 — Complete source_boundary receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117020 — Complete custody receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117022 — Complete posture_slots receiving-boundary inventory coverage | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117024 — Prepare bounded output attempt-key fixture scope | Selected v13; execution deferred | Still child of W48697; unchanged |
| W117026 — Resolve the surviving worker-entry operation-identity inventory delta | Selected v13; execution deferred | Still standalone; unchanged |
| W121039 — Resolve review-cycle helper-call inventory residuals | Selected v13; execution deferred | Still child of W116975; unchanged |
| W121042 — Resolve review-cycle nested fence inventory probes | Selected v13; execution deferred | Still child of W116975; unchanged |
| W129838 — V12: Close concrete worker operations during stage construction unwind | Selected v13; execution deferred | Still child of W103950; unchanged |

Mixed Work W61599 and W136578 retain broad progress/telemetry and exhaustive
recovery/observation portions for v13, but are not wholesale members here:
minimum progress and exact current recovery/monitor defects may be required
for v12. The audit identifies those bounded questions. W3/W7/W32382 and
the other unresolved rows likewise require the stated current-scope
reconciliation; ancestry never settles their release placement.

The existing v11 containment limitation is already W106052 (T106052,
owner clarification M106724). Reuse that record and this approved table.
No duplicate limitation Work or reparent implementation prerequisite is needed.
W2 can record v12 delivery readiness while remaining an open historical
umbrella with unfinished children; do not close/cancel them to fake migration.

## W165782 follow-through — claim167877

All42 v13 rows from the owner-selected audit are retained (the41 external rows
above plus W165786 itself). Current snapshot167877 preserves their IDs and
containment. RELEASE-CHECKLIST-167877.md in W2 carries minimum consumers and
unresolved triage. W167896 owns the minimal viewer; W61599 minimum positive
activity stays v12, while its older rich follow/search/retention ideas are future
W39649/v13 selection material. No new v13 execution or graph reparenting.
Membership editing for this turn is complete; the separate W165786 turn may
park the umbrella without repeating classification or changing these rows.


## 2026-09-15 — owner defers reported pre-existing suite failures until post-v12

After W61599 implementation handoff178359, Slawomir directed: "the so called 'preexisting' failures need to be addressed in post-v12 era, where we have speedy access to parallel work. I don't want to burn time on them now".

Record the baseline failure backlog under W165786 for bounded parallel work after v12 readiness. W61599's ACTIVITY-IMPLEMENTATION-177898.md reports baseline7259 tests/89 failures-errors and candidate7333 tests/88 failures-errors, with the remaining set reported unchanged from baseline. These are author-reported classifications, not an independent certification or a green suite. Preserve the existing results, failure identifiers/log locators where already available, and the exact baseline/candidate context. Do not spend current release time repairing those baseline failures, reconstructing broad suite history, or repeating full suites merely to investigate them.

The active W61599 reviewer should use existing evidence and focused checks of the changed behavior and any concrete suspected introduced regression. Candidate acceptance does not require fixing unrelated baseline failures. Report a concretely demonstrated defect in selected v12 execution separately; do not call a new regression pre-existing to waive it, or use speculative classification concerns to launch a baseline cleanup campaign. This ruling narrows current verification/repair scope, not truthful result reporting or independent acceptance.

After readiness, W165786 will decompose surviving failures into small Jobs with explicit file ownership, prioritization and acceptance, reusing v12 parallel execution. Reuse existing defect Works when identified; no new implementation/backlog copies or release-gate edges are created now. The downstream consumer must revalidate the surviving failures then rather than treating this snapshot as current indefinitely.

Evidence: baton:work/records/2026/09/finding-live-worker-log-observability/ACTIVITY-IMPLEMENTATION-177898.md, section8; PROGRESS.md claim177898; W61599 pass178359. This explicit post-v12 repair selection supersedes any interpretation that the baseline suite must be made green before W61599/W2 can proceed. W161234 and the already-selected required v12 outcomes remain independently accountable.
