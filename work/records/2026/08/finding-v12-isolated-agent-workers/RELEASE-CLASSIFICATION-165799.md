# V12 delivery / v13 hardening classification — W165782

Prepared by baton.codex under claim165799, 2026-09-14 UTC.
This is the lightweight W165782 planning deliverable in W2's existing record,
not a new dossier or implementation assignment.

## Decision requested

Select the release classifications and bounded follow-up sequence below.
W103950 and the W165786 membership-table stopgap are already owner-approved;
other placements are reviewer proposals until selected. Of the 65 open Work
at canonical graph snapshot165832, this audit proposes 9 v12-required rows
(including two planning/umbrella rows), 42 v13-hardening rows and 14 explicit
unresolved placements. A required row can name only a bounded subset of an
older Work. These counts do not mean 65 implementation Jobs must run.

**Confirmed criterion:** reliably execute multiple independent development
Jobs concurrently, monitor them cheaply, collect correctly bound reviewed
results, and explicitly recover failures while preserving work and context.
W2 FINDING's "V12 parallel delivery enables v13 hardening" ruling controls.
Historical titles, parentage, full-suite failures or prerequisites of a
hardening campaign do not independently establish a v12 release requirement.

**Observed graph:** RELEASE-GRAPH-165799.json retains the complete canonical
open graph response at snapshot165832: 65 selected open nodes, 41 closed context
nodes and 123 edges. All 65 selected nodes appear exactly once below. The
closed context nodes supply provenance, not new work. This is a snapshot for
review, not an alternative scheduler. Detail/thread reads additionally checked
W103950, W91072, W110783, W106052 and W161230; canonical searches for monitor,
observation, status, TUI and read-only identified existing supporting work.

**Scope:** repository/CLI research and durable planning only. No source/test
edits, test execution, live store inspection, runtime/provider/model execution,
graph mutation, backlog migration, additional Work creation, or Git mutation.
No verification allowance is granted or spent here. Existing failed receipts,
unknown costs and cumulative budgets remain with their owners.

## Complete open-Work classification

"Unresolved" means the exact remaining release impact needs the stated
revalidation. It is neither an automatic release gate nor permission to ignore
a known correctness defect. "v13-hardening" means the recorded outcome is
outside the minimum release; it is not fixed, waived, closed or approved for
immediate execution.

| Existing Work | Proposed release class | Technical rationale and boundary |
| --- | --- | --- |
| W2 — Design v12 isolated agent workers | v12-required | Release criterion and classification/selection work only; umbrella closure is distinct from delivery readiness. |
| W3 — V12 M2: Prove local isolated execution | unresolved | Mixed local milestone: required deadline cleanup and completed isolation evidence coexist with optional Podman/full certification. Separate release accounting; do not require whole milestone closure. |
| W7 — V12 M3: Build the proposal pipeline | unresolved | Legacy proposal umbrella: basic reviewed-content/import correctness is required, but threshold-attestation extension W16830 is not. Reconcile already accepted pipeline evidence before selecting any residual. |
| W8 — V12 M4: Certify agent and remote runtimes | v13-hardening | Broad runtime/remote certification, resilience/scale and rollout milestones exceed the selected local parallel-Job release. Required concrete correctness remains with its own Work. |
| W9 — V12 M5: Prove resilience and scale | v13-hardening | Broad runtime/remote certification, resilience/scale and rollout milestones exceed the selected local parallel-Job release. Required concrete correctness remains with its own Work. |
| W10 — V12 M6: Prepare rollout and adoption | v13-hardening | Broad runtime/remote certification, resilience/scale and rollout milestones exceed the selected local parallel-Job release. Required concrete correctness remains with its own Work. |
| W9901 — V12 M6: Model hierarchical teams and shared approvers | v13-hardening | Hierarchical teams/shared approvers extend organization beyond the selected local Job actors; no minimum-release consumer demonstrated. |
| W16830 — M3 foundation: Separate approval attestations from decisions | v13-hardening | Separate one-of/all-of/threshold attestations and aggregate policy decisions are advanced approval capability. Reuse existing independent review/import receipts for v12. |
| W28880 — Add searchable tags to v12 Work | v13-hardening | Generic searchable tags and their CLI/TUI surfaces are optional organization, not the minimum Job monitor. Preserve the existing label dependency chain. |
| W29401 — Expose v12 Work labels through protocol and CLI | v13-hardening | Generic searchable tags and their CLI/TUI surfaces are optional organization, not the minimum Job monitor. Preserve the existing label dependency chain. |
| W29408 — Surface v12 Work labels in the TUI | v13-hardening | Generic searchable tags and their CLI/TUI surfaces are optional organization, not the minimum Job monitor. Preserve the existing label dependency chain. |
| W32382 — M2: Complete local OCI negative and race endings | unresolved | Mixed negative/race umbrella. W32577's concrete deadline settlement is required; the complete certification matrix is not. Retain its open child and failure evidence. |
| W32391 — M2: Certify local OCI lifecycle on Podman | v13-hardening | Second-engine Podman certification is outside the selected local reference runtime and cannot be a universal release gate. |
| W32577 — M2: Define and compose runtime deadline cleanup | v12-required | Deadline fencing/quiescence/cleanup must leave honest recovery and resource ownership; retained failed engine evidence is not a pass. Preserve current operator-owned gate and cumulative spending. |
| W33755 — Revise direct-topology conformance and certify local OCI | v13-hardening | Full frozen direct-topology 1.1 conformance matrix is a separate certification claim. It does not replace or expand focused execution correctness for v12. |
| W39366 — Harden the v12 supervised dogfood path | v13-hardening | Broad supervised-dogfood negative/restart/retry matrix; reconcile concrete defects under their existing leaf owners without importing the inventory. |
| W39435 — Flatten v12 canonical dossier storage | v13-hardening | Flat allocation of new dossiers is not needed to execute Jobs while v11 remains authoritative and existing canonical paths are preserved. |
| W39649 — Normalize worker telemetry and introspection | v13-hardening | Normalized usage/quota/commands and CPU/network telemetry exceed the minimum monitor. Reuse unknown/freshness principles without requiring provider adapters or full telemetry. |
| W44342 — Settle or cancel the engine-side custody operation | unresolved | Supervised engine-operation provider was explicitly made optional; the later inert-start/durable-activation subset intersects duplicate-execution prevention. Map current accepted lifecycle evidence before selecting a residual. |
| W48697 — Complete the global v12 receiving-boundary inventory | v13-hardening | Global receiving-boundary census and whole-suite remediation remain unfinished certification/accounting, not automatic v12 gates. Concrete runtime defects discovered there are separately assessed; no green-suite claim or assertion waiver. |
| W61599 — Make live worker progress observable | v12-required | Only bounded provider-safe progress/last-activity inputs needed by the monitor. Existing wiring has changes requested; richer stream following, search/filter and raw transcript work remain v13. |
| W61981 — Make v12 verification context complete and explicit | unresolved | Complete declared verification context is required, but this older dogfood-v2 Work may overlap later Git/verification providers. Reconcile current accepted inputs/environment evidence before assigning remaining implementation. |
| W62098 — Make retained v12 proposals complete against their import base | unresolved | Correct immutable base/private-line/review checkpoint identity is required. Later source/workspace and persistent-correction providers implement much of this older plan; reconcile rather than repeat the whole superseded dogfood program. |
| W62535 — Preflight v12 dogfood before staging source | unresolved | Pre-staging profile/toolchain checks concern the older supervised operator; prove whether the supported release entry still creates stranded attempts or mislabels verification context. No blanket failure-path waiver. |
| W63214 — Make v12 source staging respect canonical entry bounds | v13-hardening | 512-entry temporary generic-tree copier correction is explicitly outside production Git-backed source inputs. Preserve supported bounded-source refusal and defer generic profile expansion. |
| W63255 — Fence pre-attach assignments during explicit abandonment | v12-required | Confirmed pre-attach abandon reports resolved while exact Authority assignment remains live: false recovery. Require the existing bounded fence correction or positive evidence that the released recovery surface excludes/supersedes this path. |
| W91072 — v12: Enforce live workspace byte and entry ceilings | v13-hardening | Owner explicitly deferred live byte/entry reservation beyond launch-time free-capacity preflight. Preserve no-live-quota claim; do not silently change rootless storage privileges. |
| W103525 — V12: Certify parallel scheduling with deterministic traces | v12-required | Deterministic scheduling traces supply the necessary concurrency/accounting evidence. Reconcile retained accepted proof and its limitations; no automatic rerun or broad stress expansion. |
| W103950 — V12: Extend stage composition hardening coverage | v13-hardening | Owner-selected expanded composition matrix. Do not import it through ancestry or its prerequisites; concrete child W129838 assessed separately. |
| W106052 — V11: Existing Work has no canonical parent attachment operation | unresolved | Existing v11 containment-interface limitation, not a v12/v13 implementation deliverable. Approved membership-table stopgap suffices; keep parked and create no replacement/reparent prerequisite. |
| W110783 — V12: Resume implementation ending after checkpoint fencing | unresolved | Checkpoint-fenced restart defect intersects required recovery, but later W124784 accepted a bounded driver correction. Compare both consumer and driver cuts under W161234 before deciding residual/duplicate disposition. |
| W111793 — V12: API model adapters and testing roles | v13-hardening | Additional API model adapters/testing roles are optional provider breadth; use existing supported provider/context evidence. |
| W114077 — V12: Investigate retry discard runtime quiescence refusal | unresolved | Retained intermittent engine/retry failures have no established current causal regression. Inspect exact supported release path and focused evidence; required if they invalidate recovery/isolation, otherwise deferred investigation. No broad rerun. |
| W114252 — V12: Represent explicit executable and mode-change scope | v13-hardening | Explicit executable/mode-change support is an extension; current content-only importer correctly refuses unsupported mode candidates. |
| W114516 — V12: Investigate intermittent worker-entry engine failures | unresolved | Retained intermittent engine/retry failures have no established current causal regression. Inspect exact supported release path and focused evidence; required if they invalidate recovery/isolation, otherwise deferred investigation. No broad rerun. |
| W115981 — Resolve and verify the twelve v12 suite checks diagnosed by W115824 | v13-hardening | Global receiving-boundary census and whole-suite remediation remain unfinished certification/accounting, not automatic v12 gates. Concrete runtime defects discovered there are separately assessed; no green-suite claim or assertion waiver. |
| W116975 — Complete review_cycles receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116977 — Complete intake receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116979 — Complete authority_port receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116981 — Complete interrogation receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116987 — Complete sessions receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116992 — Complete attempts receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116995 — Complete workspaces receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116997 — Complete oci receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W116999 — Complete handshake receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117002 — Complete documents receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117004 — Complete credentials receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117006 — Complete exchange receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117008 — Complete launch receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117017 — Complete source_boundary receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117020 — Complete custody receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117022 — Complete posture_slots receiving-boundary inventory coverage | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117024 — Prepare bounded output attempt-key fixture scope | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W117026 — Resolve the surviving worker-entry operation-identity inventory delta | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W121039 — Resolve review-cycle helper-call inventory residuals | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W121042 — Resolve review-cycle nested fence inventory probes | v13-hardening | Bounded inventory/probe coverage under W48697; no concrete runtime defect is established by missing declaration/stimulus alone. Preserve its exact module scope, serial file ownership and all aggregate assertions. |
| W129838 — V12: Close concrete worker operations during stage construction unwind | v13-hardening | Concrete close/release mismatch is confirmed but the callback is currently no-op and no database/runtime/credential leak was proved. Preserve bounded correction and 60s author cap; reselect if actual ownership failure appears. |
| W136578 — V12: deferred integration-result recovery and storage hardening | unresolved | Mixed hardening owner: exhaustive crash/tamper/storage matrices remain v13; exact publication replay and detached per-Job observation may be required by new recovery/monitor consumers. Reuse slice1 fixes and select only surviving concrete cuts. |
| W144335 — V12: Re-enter sealed intake without losing the original held reason | unresolved | Sealed-intake re-entry masks the original unable/held reason. Determine the current ordinary recovery/monitor impact and required bounded receipt replay; never treat the failed provider run as successful. |
| W144813 — V12: Preserve the first integration launch refusal across re-entry | unresolved | Launch-root re-entry masks the original refusal after materialization. Revalidate against W161230's managed ordinary lifecycle; correct a surviving selected recovery/monitor failure, not all launch permutations. |
| W156162 — V12: Configure execution and verification budgets per Job | v12-required | Original Job-specific execution/verification limits must reach managed phases without cross-Job leakage. Preserve its existing W161230 dependency and all measured/unknown historical costs. |
| W161230 — V12: Run integration through managed relocatable execution | v12-required | Owner explicitly requires managed preparation and apply using ordinary worker I/O. Slice1 accepted; slice2 selected at165830; derived apply/failure settlement remains slice3. |
| W161234 — V12: Prove code correction and restart without duplicate execution | v12-required | Existing owner for correction, context reuse and restart without duplicate execution. Reuse provider-context evidence and deterministic runtime-seam proofs; do not broaden to a farm. |
| W165782 — V12: Classify release delivery and v13 hardening | v12-required | Release criterion and classification/selection work only; umbrella closure is distinct from delivery readiness. |
| W165786 — V13: Harden the platform using v12 parallel Jobs | v13-hardening | Owner-approved umbrella and documentary release-membership stopgap; execution waits for v12 readiness. |

## Existing monitor inputs and the missing bounded deliverable

**Confirmed existing providers:**

- W71875 (closed satisfying): persistent Job manager and submit/status API.
  Current `v12/python/tools/job_manager.py:_status`, `_ReadOnly` and
  `src/baton_v12/job_manager/projection.py:status` provide the supported
  persisted projection. Stage state is derived from receipts/owner reads,
  including exceptional/blocked states; reading must not reconcile or serve.
- W129844 (closed satisfying): composed held integration/status/log-locator
  evidence, including absent log/activity shape. Reuse its exact reviewed
  coverage; absence is not fresh activity.
- W130229 (closed satisfying): selected public per-Job completion reads.
  Its OBSERVATION-HANDOFF-2026-09-11.md explicitly distinguishes existing
  serving-handle reads from a detached observer. It did not certify every
  detached completion path.
- W136578 H-7 owns the unresolved detached observer: global fallback without
  per-Job binding and model-free completion omitted before the result reader.
  Current `StageObservation.observe_integration` remains the seam to audit
  after managed slices. The monitor must use a correct existing reader or
  select this bounded correction; never construct a serving factory for status.
- W61599 owns safe native-session progress. Its PLAN still has changes
  requested: outer stderr is not the native session stream, synchronous
  publication can backpressure draining, and zero-byte EOF must not claim
  activity. Revalidate the actual current boundary before implementing the
  minimum progress subset. Raw transcript exposure is not authorized.
- W39649 owns much richer normalized provider telemetry and later UI. Keep
  that program in v13; a monitor does not need token/account/quota/command
  adapters, CPU/network sampling or terminal scraping.
- W102477 (closed v11 idle-TUI correction) provides a useful measured strategy:
  sequence-gated projection avoided idle tree rebuilds; recorded idle CPU
  fell from about22.7% to0.02% of one core. This is evidence about v11,
  not a measured v12 guarantee or a requirement to expose new v12 protocol.

**Missing deliverable, proposed allocation:** a thin read-only Job viewer over
the existing status/observation boundaries. No existing open Work returned by
the complete graph/search owns this concrete minimum front end. Scope it as
one bounded child under W2 only after owner selection, referencing these
providers. Do not recreate W61599, W39649, W130229 or W136578. W29408 owns labels,
not this viewer. No Work was created by this audit.

Proposed acceptance to pin in that bounded plan:

1. Show exact Job identity, current stage and worker/assignment when known,
   elapsed time, last positive activity/progress and observation age; blocked,
   failed and pending operator-action reasons remain distinct and visible.
2. Drill down to manager-permitted logs/results by stable locators. Missing
   capability/content remains explicitly unavailable. Do not expose arbitrary
   host paths or credentials; content-safe boundaries continue unchanged.
3. Disconnected/stale status is conspicuous, never an apparently live success.
   Keep source-observation time separate from local refresh time. Unknown
   worker/activity facts remain unknown; avoid inventing new telemetry.
4. No submit/claim/cancel/serve/cleanup or other mutation capability. Verify
   that ordinary refresh/drill-down leaves owner state untouched and cannot
   trigger a worker or reconcile an engine.
5. Proposed measurable cost target: on a named local host and a representative
   20-Job deterministic snapshot, <=1% of one core over60s idle, <=2s visible
   change/freshness update at a configured1s refresh, and no busy-spin or
   unbounded per-refresh log reads. Record CPU time, wall time, refresh/projection
   counts and input size. These are proposed limits requiring selection, not
   results or a newly authorized60s test run. Reuse an existing change sequence
   when available; otherwise bound/cache public reads without raw DB shortcuts.
6. Deterministic fixtures exercise two different Jobs, held/failed/completed
   state, missing logs/activity, reconnect and model-free completion. Use the
   ordinary read-only entry point; no live model/engine is needed for display
   or idle-cost questions.

## Concrete correctness triage without importing campaigns

W129838 is individually examined, not automatically required because it is a
W103950 child. Its FINDING/PLAN and independent review establish that construction
selects release while concrete workers offer close, but the current disposal
callback is a no-op and no DB/runtime/credential leak is proved. Keep its
60s cumulative author cap and exact two-path future correction in v13. An
actual ownership failure changes that placement; a failing interface regression
alone does not manufacture an observed leak.

W136578 is mixed. Slice1 W161230 already accepted exact publication/replay,
lease/target and capacity boundaries at review-2026-09-14T01-09-21Z.md; do not
reimplement old limitations from stale notes. Reconcile its specific historical
publication and H-7 claims against accepted/current managed bytes. Select only
a surviving ordinary recovery or monitor defect. Exhaustive storage-alias,
persisted-tamper and cross-product matrices remain v13.

W110783 is also a potential duplicate of later accepted corrections: W124784's
checkpoint-fenced cleanup review accepted a bounded driver repair; W122060
owned the separate serving consumer. W161234 should compare those exact cuts
and retained evidence. Do not create another restart implementation merely
because the old lightweight Work remains open.

W63255 records actual false recovery (resolved=true with live Authority
assignment), so it cannot be silently deferred as hardening if that command
ships as supported recovery. Its public pre-attach fence design is already
approved. Revalidate whether the release path uses it or a later accepted
replacement; either correct the survivor under W63255 or record explicit
evidence of supersession/exclusion. Keep resources and old failure unchanged.

W144335/W144813 preserve failed historical runs and masked reasons. New monitor
and recovery claims make their exact user-visible impact worth a current
assessment. They do not make provider errors/provisioning mismatches succeed.
W114077/W114516 remain intermittent observed engine failures, not established
current regressions. Triage only their affected release paths using retained
logs first; do not run the full engine suite to rediscover their existence.

W61981/W62098/W62535 need current-provider reconciliation: their older task/
verification/workspace plans overlap subsequent standalone work. Required
immutable inputs, honest command/context results and checkpoint continuity
must be established, but none of these historical plans warrants duplicate
implementation without identifying a surviving gap.

Inventory rows W48697 and its listed descendants are test/declaration/probe
coverage work. Their confirmed-defect classification in Baton is not evidence
that every missing inventory row is a runtime work-loss defect. Preserve all
assertions, residuals and the final honest W115981 suite obligation. A newly
demonstrated runtime defect gets its own concrete release assessment; the
entire inventory is not a prerequisite to focused ordinary verification.

## Exact relationship proposals — no operations performed

In the retained graph, dependency source is the blocker and target is the
consumer. The following are proposed supported CLI changes for the authorized
route handler after selection and a fresh detail/claim check.

| Current relationship | Proposed disposition | Rationale / supported expression |
| --- | --- | --- |
| W32391 blocks W3, edge34942 | Remove for the selected release boundary | `unblock work=W3 on=W32391 rationale=...`: Podman certification is explicitly optional; retain both Works and Podman evidence. W3 still cannot close while its open children remain. |
| W3 blocks W2, edge19 | Replace the broad release gate with explicit minimum providers | After recording W2 as the historical umbrella plus this release checklist, propose `unblock work=W2 on=W3 rationale=...` and `block work=W2 on=W32577 rationale=...`, plus W161230, W161234, W156162, W103525 and W61599 each as its own `on=`. Add the new viewer only after it exists. W61599 must first pin its minimum subset so this does not pull in its rich-stream roadmap. |
| W63255 / unresolved issues versus W2 | Conditional exact gate only after applicability disposition | If the false-recovery path is supported and survives, `block work=W2 on=W63255 rationale=...`. Do not add blanket W136578/W48697/W103950 gates. Link a surviving required sub-result to its existing owning Work after bounded scope is selected. |
| W161230 blocks W156162, edge161306; blocks W161234, edge161487 | Keep | Managed-phase limits and correction/restart proof consume the actual managed execution result. Classification is not grounds for early unblocking. |
| W32577 blocks W32382, edge32797; W32382 blocks W3, edge34941; W32382 blocks W33755, edge86098 | Keep | True child/completion and full-certification dependencies remain valid for those outcomes; the broad umbrellas no longer define minimum delivery. |
| W129838 blocks W103950, edge129888 | Keep | The concrete cleanup correction is genuinely required by its expanded hardening parent; this does not make either a v12 gate. |
| W3→W7/W8/W16830, W7/W8→W9, W9→W10 | Keep pending their own v13 scope review | These are historical technical milestones, not current W2 release dependencies once the explicit minimum replaces edge19. No need to tear down valid future ordering now. |
| Label chain W29401→W29408→W28880; inventory chain through W48697→W115981 | Keep | Still valid internal completion/ownership ordering for v13. No scope or assertion waiver. |
| Reparent W103950 and other proposed v13 members under W165786 | Unavailable in deployed v11; do not promise a command | Preserve canonical containment/IDs/dossiers. Extend W165786 PLAN's owner-approved release-membership table as a documentary stopgap. |

The existing limitation is already tracked as **W106052**, with owner
M106724 permitting continued documentary references while they suffice.
W165786 FINDING logs the current CLI limitation and owner approval of the
stopgap; link W106052 rather than creating a duplicate or adding reparenting
implementation to the v12 path. Actual `contains` edges remain unchanged.

**Closure versus release:** AGENTS.md prohibits closing a parent with an open
child. W2 contains historical broad milestones which cannot be reparented by
this deployment. Therefore v12 delivery can be recorded as a reviewed release
outcome/checklist while W2 remains an open historical umbrella; do not claim
that unblocking W2 makes it closable, cancel unfinished v13 children or mutate
the store. If a terminal release receipt needs a separate bounded Work, select
that tracking-only deliverable later; no duplicate implementation backlog is
needed and no such Work is created now.

## Actionable sequence and ownership

1. baton.decide selects this classification, the explicit unresolved triage
   questions and whether to apply the proposed gate replacement. Selection
   does not close any unresolved Work or grant execution to proposed v13 members.
2. Continue W161230 immediately under its own claim. Owner165830 selected
   SLICE2-SCOPE-165724.md SHA256
   4c18e791a29516b92d5afaba93c2042f5adaefa60bd57b7c54b13a04acba4fa0:
   pin that selection and hand its existing implementation packet to baton.impl.
   Local ordinary worker input/output reuse and deterministic providers remain
   mandatory; derived apply/failure settlement stays slice3. This classification
   adds no source paths, tests or demands to that active sequence.
3. While its author works, research the narrow unresolved current-consumer
   questions and scope the minimum viewer/progress work using existing owners.
   Establish disjoint file ownership before edits; stage_execution.py and
   integration_worker.py remain in W161230's selected packet. No competing
   observer cleanup or test rewrite under this audit. W32577 retains DEPLOYMENT.md.
4. Complete the existing deadline-cleanup disposition and managed slices,
   then W156162 limits and W161234 correction/restart/context proof. Reuse
   W103525 scheduling traces and accepted context evidence (including W106673)
   with exact qualifications. A retained pass is not permission for a fresh
   live run; deterministic providers remain the default.
5. Obtain independent acceptance of the minimum read-only viewer and required
   concrete corrections. Record the exact final capability/evidence matrix
   against W2's criterion, including what remains unknown, failed or v13-only.
6. Only after readiness, select independent v13 tasks from W165786's table for
   v12 execution with explicit source ownership, inputs, results and recovery.
   V11 remains the coordination authority now. No automatic provider fallback,
   farm, backlog copy, or dual authority is introduced.

### Cumulative accounting preserved

This planning claim ran zero verification children. At the consumed W161230
handoff, author spending is401.4989696021221s and reviewer21.403079563991923s.
Owner165830 raises the cumulative author cap to1200s, leaving798.5010303978779s;
reviewer cap300s leaves278.5969204360081s. No reset/transfer. W32577 accounting
and its exact current operator execution disposition remain owned there; this
audit neither reruns its failed gate nor consumes its remaining allowance.
W103525/W156162/W161234 and every other existing ledger keep all accepted,
failed, overrun and unknown historical accounting intact.

## Evidence locators and research limits

All paths below are canonical repository-relative records under root baton:

- W2 FINDING/PLAN and AGENTS.md: owner release ruling; this audit is a proposal
  under that confirmed boundary.
- work/records/2026/09/finding-v13-parallel-hardening/FINDING.md and PLAN.md:
  W165786 creation/owner approval and documentary membership.
- work/records/2026/09/finding-v12-stage-composition-hardening/ and its
  findings/finding-concrete-worker-close/: W103950/W129838 scope distinction.
- work/records/2026/09/finding-live-worker-log-observability/PLAN.md and
  work/records/2026/08/finding-worker-telemetry-introspection/PLAN.md:
  minimum safe progress versus extended telemetry.
- work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-per-job-readonly-observation/OBSERVATION-HANDOFF-2026-09-11.md:
  accepted reader evidence and detached limitations.
- work/records/2026/09/finding-v12-integration-result-hardening/FINDING.md:
  H-7 and mixed recovery/observation ownership.
- work/records/2026/09/finding-v12-pre-attach-abandon-leaves-live-assignment/FINDING.md;
  finding-v12-sealed-intake-reentry/FINDING.md;
  finding-v12-integration-launch-refusal/FINDING.md in the same2026/09 records:
  concrete false-recovery/masked-reason evidence.
- work/records/2026/09/finding-v12-complete-verification-context/;
  finding-v12-proposal-import-base-closure/; finding-v12-dogfood-preflight-before-staging/;
  finding-v12-source-manifest-canonical-entry-bound/: older approved bounds,
  with current-overlap questions explicitly unresolved.
- work/records/2026/08/finding-v12-global-boundary-inventory-debt/PLAN.md and
  work/records/2026/09/finding-v12-suite-check-remediation/FINDING.md:
  inventory/module scope and retained whole-suite obligation.
- work/records/2026/08/finding-v12-direct-topology-conformance-certification/PLAN.md,
  finding-v12-approval-attestations/PLAN.md and finding-custody-engine-operation-settlement/PLAN.md:
  full-certification, advanced policy and deferred provider boundaries.
- Canonical T91072, T110783, T114077, T114252, T114516, T106052 and
  W161230 event165830: lightweight original scope, failures and current selection.

This was a planning audit, not independent acceptance of changed application
bytes. All named required record files could be read. One exploratory guessed
source locator, job_manager/cli.py, does not exist; the actual entry is
tools/job_manager.py, which was read. This is a corrected search-path mistake,
not a missing required artifact or a Baton operational defect. Broad help/read
output was occasionally truncated; targeted reads and the retained complete
graph supplied the material relied on. No scope conclusion relies on unseen
truncated text, and unresolved entries deliberately name their missing proof.

