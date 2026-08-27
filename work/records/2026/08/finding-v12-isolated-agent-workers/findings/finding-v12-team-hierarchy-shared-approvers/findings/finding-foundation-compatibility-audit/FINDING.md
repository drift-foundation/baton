# Audit v12 foundations against the shared-principal model

## Parent context

W9901's approved hierarchy/shared-approver design is intentionally implemented
in full at M6, but its identity and authority model constrains foundational
work now. This audit prevents M2-M5 from hardening a flat `team.member` model
that would later invalidate completed schemas, receipts, routes or runtime
contracts.

## Boundary

Inventory active Python v12 authority and Worker Manager surfaces that encode
participant identity, organizational/effective scope, route and repository
ownership, grants, claim slots, approval evidence, runtime/capacity and inbox
identity. Classify each as:

- already compatible with the W9901 baseline;
- safely opaque/extensible until M6; or
- irreversible flat coupling that must be corrected or explicitly gated now.

This Work does not implement the complete hierarchy feature or its TUI. Any
code correction discovered here is separately scoped and reviewed.

## Acceptance

- Exact code/schema/manifest surfaces and their current invariants are named.
- Positive and negative examples show why each claimed seam is sufficient.
- Must-fix-now findings become bound provider Work before affected foundations
  close.
- Safely deferred M6 work remains indexed by W9901 without speculative code.

## Audit result — 2026-08-26

### Classification rule

This audit distinguishes three identities that the current code calls one
participant:

- the **endpoint/Handler address** used to route and fence an execution;
- the **canonical principal** whose capacity and authority are global; and
- the **effective scope** in which an act is authorized.

Keeping a `team.member` string as an operational endpoint is compatible. Using
that string itself as the principal, deriving scope from its prefix, or storing
it as the only authorization evidence is not. A field is safely deferred only
when its absence does not force later policy to reinterpret already-recorded
facts.

### Compatibility matrix

| Surface | Current invariant and exact owner | Classification | Required disposition |
| --- | --- | --- | --- |
| Session authentication | `authority/session.py:Session` is minted for one participant; claim and actor operands come from the binding and caller-supplied `participant`/`actor` are refused. | **Compatible mechanism, conditionally opaque identity.** The caller cannot choose its endpoint. | Preserve the binding; W16821 makes the authority map the endpoint to a principal and derive scope. Never parse the team prefix as scope. |
| Assignment identity and fencing | `authority/identity.py:{assignment_ref,assignment_key,same_assignment}` and Worker Manager `authority_port.py:_assignment` compare authority UUID, Work id, participant endpoint and generation. | **Compatible.** This is an execution fence, not a complete authorization decision. | Retain all four parts. Add principal/scope context beside it; do not replace generation or silently redefine participant. |
| Work target/scope | `authority/schema.py:work` stores route and Handler but no owner/effective scope or target reference. `core.py:create_work` accepts opaque route text only. | **Must fix now.** Existing Work facts leave no target from which authority can derive later scope. | W16821 adds an authority-owned scope/target seam without implementing hierarchy resolution. |
| Principal and membership | No principal, organization, scope or membership relation exists in `authority/schema.py`; `identity.py:check_participant` requires `team.member`. | **Must fix now where identity is authoritative; safely deferred for the full forest.** | W16821 separates canonical principal from endpoint. W9901 retains forest, memberships and inherited resolution for M6. |
| Route authorization | `schema.py:route_handler` and `core.py:claim` authorize direct `(route, participant)` membership. Route itself is opaque text. | **Opaque route spelling is compatible; direct membership as authorization is must-fix.** | W16821 puts claim eligibility behind an authority decision returning principal, scope, role and provenance. |
| Repository ownership | Authority and Worker Manager schemas contain no repository ownership record and no source path derives org scope. | **Safely deferred.** Absence has not committed a contradictory owner. | W9901/M6 defines repository records separately from org scope. W16821's Work scope must not be inferred from repository spelling. |
| Grants and masks | `schema.py:capability`, `api.py:{grant_capability,revoke_capability}` and `core.py:_require_capability` store/check direct `(participant, capability)` membership. No grant id, scope, role, mask or provenance is retained. | **Must fix now.** Actor-only evidence cannot later prove a direct/inherited grant or mask. | W16821 introduces the decision/provenance seam; direct M2 grants are its first provider. Full inheritance/masks remain W9901. |
| Claim capacity | `schema.py:claim_slot` has participant as primary key; `core.py:{_take_slot,_release_slot,slot_holder}` enforces one live claim for that key inside the claim transaction. | **Invariant compatible; key must fix now.** Two endpoint addresses for one principal currently receive two slots. | W16821 keys capacity by canonical principal while preserving atomic global one-live-claim behavior. |
| Claim/operation replay | `identity.py:claim_signature` binds Work id and participant; operation and assignment generations are durable and collision checked. | **Compatible fencing, incomplete authorization replay.** | W16821 retains the endpoint claim signature and additionally binds the authority-derived decision/policy generation where changing it changes meaning. |
| Authority audit evidence | Assignment, contract, activity and proposal rows carry participant/generation; receipts and integration attempts carry actor only. | **Must fix now.** Evidence cannot answer principal, scope, role or grant provenance. | W16821 versions attributable evidence and projections; operational participant remains separate. |
| Approval evidence | `schema.py:receipt` is unique on `(proposal_id, kind)`; `core.py:_write_receipt` refuses a second approval and `integrate` consumes that one disposition. `policy_generation` is supplied by the caller. | **Must fix before M3.** One-of can be approximated; all-of and threshold cannot be represented. | W16830 separates immutable attestations from aggregate decisions and freezes eligible principals/rule/generation at proposal policy generation. |
| Worker Manager authority port | `worker_manager/authority_port.py` correctly consumes a participant-bound session and validates the full assignment, but its claim answer has no principal/scope/provenance. | **Mechanism compatible; answer contract must fix now.** | W16823 consumes W16821's authority-owned context and refuses mismatched context before persistence. |
| Manager offer/attempt persistence | `worker_manager/schema.py` stores `offers.participant` and `attempts.assignment_participant`; `attempts.py:activate_assignment` binds those four assignment parts atomically. | **Assignment fence compatible; principal-global execution identity missing.** | W16823 stores authorization context atomically beside the existing assignment and includes it in replay operands. |
| Runtime/session identity | `documents.py:runtime.labels`, `attempts.py:_runtime_labels`, execution `agent_sessions` and interrogations carry participant but no principal/effective scope. Posture slots are keyed by attempt/posture and inherit the attempt. | **Must fix trusted runtime context; posture-slot mechanism compatible.** | W16823 adds principal-global runtime labeling/reconciliation. Consent remains pre-claim; posture slots need no independent org policy. |
| Frozen worker/agent wire schemas | Worker-control and agent-session 1.0 seal `assignmentRef` as Work reference, participant and generation. The approved version policy says required-field/meaning changes need a new major. | **Safely retained as endpoint fence, not authority evidence.** | W16823 keeps principal/scope on the trusted side unless a concrete remote consumer needs it; then it must create an explicit negotiated-version Work, not mutate 1.0. |
| Availability | No Python authority rule rewrites grants, thresholds or routes from runtime availability. Offer issuance consults the authority claim slot and claim rechecks capacity transactionally. | **Compatible.** | Preserve the split. Future availability may suppress offers but never alter W16821/W16830 authority decisions. |
| Inbox and Teams UX | No v12 Python authority/manager inbox or org-Team view is implemented. | **Safely deferred.** | W9901 retains the principal-global Inbox and hierarchy UX for M6. No speculative M2 table is needed. |

### Concrete witnesses

**Shared-principal capacity.** Suppose endpoints `infra.slaw` and `pc.slaw`
both authenticate canonical principal `P-slaw`. Today each endpoint can occupy a
different `claim_slot` primary key and hold a concurrent Work. Under W16821 both
resolve to `P-slaw`; the first claim takes its principal slot and the second is
refused, regardless of route or scope. Conversely, two different principals
using one organizational scope retain separate slots.

**Authority-derived scope.** Suppose a Work targets scope `infra/acp` and the
session endpoint is `pc.slaw`. A caller-supplied `infra` route, repository path
or alternate participant spelling must not choose the scope. W16821 derives it
from the Work target, resolves the endpoint to its principal, evaluates the
grant and records both the result and provenance. A mismatched supplied scope is
either absent from the API or refused.

**Assignment fencing stays valid.** A late runtime holding generation 7 must
still fail after the same endpoint claims generation 8. The existing exact
four-part assignment comparison already proves that negative case. Principal
context is additive authorization evidence; replacing participant/generation
with principal alone would weaken a compatible mechanism and is out of scope.

**Threshold approval.** For a frozen 2-of-3 policy, the current first approval
occupies the unique approval row and the second is refused as immutable. W16830
retains both eligible principals' immutable attestations and commits one
aggregate `approved` result when the threshold is crossed. A fourth ineligible
principal, a duplicate attestation by the same principal, or a membership
change after publication cannot contribute.

**Worker isolation.** A sandboxed agent may continue receiving only its exact
endpoint assignment fence. It cannot choose a principal or scope by omitting
those fields because the trusted authority/manager already fixed and retained
the authorization context. This is why the frozen 1.0 assignment object can
remain intact while trusted-side manager persistence changes.

### Provider Work and ordering

- **W16821**, bound to
  `work/records/2026/08/finding-v12-principal-scope-authority-seam/`, follows the
  closed Python authority W2845 and owns the principal/scope/provenance and
  principal-global claim-slot correction.
- **W16823**, bound to
  `work/records/2026/08/finding-v12-principal-aware-manager-context/`, follows
  closed Worker Manager core W4 and consumes W16821 in trusted manager/runtime
  state.
- **W16830**, bound to
  `work/records/2026/08/finding-v12-approval-attestations/`, is contained by M3
  W7 and owns policy snapshots, attestations and aggregate approval decisions.

The intended serial ordering is `W5 -> W16821 -> W16823 -> W6 -> W3 -> W16830`
before M2/M3 closure. `baton.codex` is not a resolved handler of `baton.impl`,
so the authority correctly refused its direct dependency mutations and an `@`
request on those provider Works. Asynchronous approver obligation **16832** on
W16793 records the exact requested dependency edges; provider threads 16833,
16834 and 16835 record the sequencing constraint for their eventual handlers.
This is an operational coordination boundary, not a Baton defect and not
permission to bypass Route authority.

### Verification evidence

Static inventory covered:

- `v12/python/src/baton_v12/authority/{schema,store,identity,api,session,core}.py`;
- `v12/python/src/baton_v12/worker_manager/{authority_port,schema,offers,attempts,sessions,posture_slots,documents}.py`;
- the frozen worker-control and agent-session 1.0 schemas and their version
  policy in the canonical M1 specification; and
- focused authority/manager tests that pin route, capability, slot, assignment,
  approval and runtime-label behavior.

A focused source run passed all 86 loaded authority assignment/contract cases.
The two requested manager modules did not load in the ambient repository venv
because `jsonschema` is not installed there; the run reported two import errors
and no manager pass is claimed. The manager classifications above therefore
rest on inspected source/schema invariants, while the provider Work retains the
normal locked distribution gate as its implementation proof.

## Approval — 2026-08-26

Slawomir approved the compatibility matrix, the three bounded provider Works,
and the intended serial ordering. This approval does not bypass Route
authority: each consumer Work's resolved handler must commit its own dependency
edge before beginning the affected implementation or conformance stage.
W9901 remains parked for the complete M6 hierarchy and UX rather than being
implemented speculatively in this audit.
