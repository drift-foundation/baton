# Preserve the v12 principal/scope authority seam

## Discovery and ownership

Discovered by W16793 while auditing the completed Python assignment authority
against W9901's approved shared-principal model. Ledger Work W16821 is bound to
this record. The record is promoted to a top-level dossier because the discovery
record already occupies the permitted second child level.

## Confirmed incompatibility

The current authority makes one `team.member` participant string serve as the
route endpoint, authenticated session identity, authorization principal,
capability grantee, claim-capacity key, Handler and audit actor:

- `authority/schema.py`: `work.route`/`work.handler`, `route_handler`,
  `capability`, `claim_slot`, assignment/contract/activity/proposal rows and
  receipt/integration actors carry only participant text;
- `authority/identity.py`: `check_participant`, `assignment_ref` and
  `claim_signature` freeze that participant into identity and replay keys;
- `authority/api.py` and `authority/session.py`: the bootstrap grants and route
  handlers, while one participant-bound session supplies claimant and actor;
- `authority/core.py`: `claim` authorizes direct `(route, participant)`
  membership, `_take_slot` enforces capacity by participant, and
  `_require_capability` authorizes direct `(participant, capability)`
  membership.

That is internally consistent for one flat deployment, but it cannot represent
W9901's one global principal acting through more than one organizational scope.
Two endpoint spellings for the same person receive two claim slots, while one
endpoint spelling cannot record which effective scope and inherited or direct
grant authorized an act. Work has no target scope from which the authority
could derive that answer later. The schema is especially time-sensitive:
`authority/store.py:_check_compatibility` explicitly refuses every other schema
version and performs no migration.

## Required correction boundary

This Work preserves a typed foundation; it does not implement the M6 hierarchy
resolver.

1. Separate the operational endpoint/Handler address from a canonical global
   principal identity. A deployment mapping may be minimal at M2, but the
   authority owns it and callers do not select their principal.
2. Give each Work an authority-owned effective-scope input or target reference
   from which later M6 policy can derive scope. Do not infer it from route,
   repository or participant spelling.
3. Put route and capability authorization behind one authority-owned decision
   seam that returns principal, effective scope, role and grant/mask provenance.
   M2 may return direct-grant provenance; its shape must admit inherited grants
   and explicit masks later.
4. Key the one-live-claim slot by canonical principal, preserving the current
   deployment-global capacity invariant across every endpoint/scope used by
   that principal.
5. Record the authorization decision and accepted policy generation with every
   attributable act. Keep participant/Handler where operational routing and
   assignment fencing still need it; do not relabel it as the principal.
6. Version persistence and public projections deliberately. An old schema must
   either have an explicit upgrade/rebuild disposition or remain a clearly
   unsupported disposable proof; silent reinterpretation is forbidden.

## Acceptance

- A positive case maps two distinct endpoint addresses to one principal and
  proves the second concurrent claim is refused by the shared principal slot.
- A negative case proves that supplying a different endpoint, route, repository
  or scope string cannot choose or widen the authenticated principal or
  effective scope.
- Claim, close and workflow-actor evidence expose the endpoint separately from
  principal, effective scope, role, grant/mask provenance and policy
  generation.
- Direct M2 grants remain representable and tested; grouping scopes,
  inheritance and masks remain deferred provider implementations for W9901.
- Existing assignment generation and replay/fencing guarantees remain intact.

## Schema-1 disposition proposal — 2026-08-28, pending approval

**Observed:** PLAN item 1 was revalidated after W5 closed and every original
claim still holds. `authority/schema.py` remains schema version 1,
`authority/store.py:_check_compatibility` refuses every other version without
migration, Work has no scope, direct authorization is still keyed by endpoint
participant, and `claim_slot` is still participant-keyed. The existing store
therefore has no facts from which a schema-2 principal, effective scope or
grant provenance could be reconstructed safely.

**Confirmed context:** the parent v12 campaign and the completed in-repository
migration record classify the current authority, Job records, attempt state,
credentials and proof output as disposable PoC state under one external state
root. W9901 and W16793 approve a principal/scope/provenance correction but do
not approve inventing those missing facts from route, repository or participant
spelling.

**Proposed disposition:** schema 2 is a clean initialization boundary, not an
in-place migration from schema 1. A schema-2 build MUST recognize a schema-1
store as its own older product, refuse it read-only, and explain that this
disposable proof store must be removed by the operator and initialized afresh.
It MUST NOT delete, rewrite, reinterpret, auto-upgrade or partially apply the
schema to that file. `Authority.create` continues to require an absent path;
no create-or-adopt shortcut is added. New additive and mutation tests retain
the current byte-for-byte refusal guarantee and prove the operator-directed
reinitialization path using a separate disposable fixture path.

This proposal deliberately does not authorize a product data-loss policy. If
schema-1 state has become non-disposable or must survive a deployment upgrade,
the correction stops and a separately designed, transactional migration Work
must define how endpoint principals, Work scopes and grant provenance are
supplied rather than guessed. Approver ruling is required before PLAN items
2-7 begin.

## 2026-08-28 — schema initialization ruling

**Confirmed by approver response M33752:** v12 remains early development, so
schema 2 and later schema versions may establish clean initialization
boundaries for disposable proof stores. Backward compatibility and migration
are not required for those stores.

**Clarified refusal contract:** a build encountering an incompatible store
must refuse it without interpreting or modifying it and direct the operator to
initialize a fresh store. The authority must not delete, rewrite, auto-migrate,
partially apply a new schema to, or infer missing facts from the old file.

**Confirmed future boundary:** migration becomes separate product Work only
when retained user state requires it. The schema-1 disposition proposal above
is therefore approved for this Work; its earlier “pending approval” status is
superseded by this ruling while the proposal text remains chronological
history.

## 2026-08-28 — the correction, implemented

**Confirmed — PLAN items 2 to 6 are implemented, and every rule is measured by
removal.** `authority/principals.py` pins the principal, the scope and the
authorization decision; schema 2 separates the principal from the endpoint,
gives Work an authority-owned scope, keys claim capacity by principal and
records the decision beside the acts it authorized;
`store._check_compatibility` refuses an incompatible store read-only with the
operator-directed diagnostic M33752 requires. 30 new cases; 14 of 14 mutations
caught; the whole existing authority suite (257 tests) green.

**Confirmed — the correction is compatible with the deployment that existed.**
The endpoint-to-principal mapping defaults to one principal per address, which
is exactly the prior behaviour, so binding two addresses to one person is a
configuration act rather than a change every existing caller has to make.

**Confirmed [P0], found and fixed inside this Work.** The first cut of
`check_principal` bounded a principal at 160 characters while
`check_participant` bounds nothing, so a wide but valid endpoint produced a
default principal the authority refused and a legitimate participant became
unclaimable. The authority's own caller-text boundary suite caught it. A
principal is now bounded by exactly what bounds the endpoint it names.

**Still open, and stated rather than implied.** Item 5 says "every attributable
act"; this cut records the decision on the two acts that pass through the
authorization seam — the claim and the four receipts — and not on `activity`,
`contract_event`, `proposal` or `integration_attempt`. Those are written under
an assignment that was already authorized, so the decision they would carry is
the claim's; whether to copy it forward or to join to it is a design question
the reviewer should settle before it is written four more times.

## 2026-08-28 — independent re-review: null-generation join is not exact

**Observed [P0]:** the review corrections retain the exact decisions for both
claim events, but `_claim_decision_for` reconstructs an assignment-derived
act's decision from `(work_id, participant, generation)` and chooses the newest
matching claim event. A v11 assignment has `generation = NULL`, so release and
reclaim by the same endpoint produces the same three stored identity fields for
two distinct claim acts. After rebinding that endpoint between the claims, the
public `activities` projection changes the earlier activity's principal and
policy generation to the later claim's decision.

The public-surface reproduction is retained at
`evidence/w16821-v11-reclaim-history-repro.py` with its transcript beside it.
It observes two immutable claim decisions, first for
`principal:baton.claude` and then for `principal:one-person`, while both the
old and new activity project as `principal:one-person` after the reclaim. The
focused 45-case principal suite and the full 272-case authority suite remain
green, so neither currently measures this historical boundary.

**Confirmed boundary:** joining through the assignment document is exact for
v12 because its generation is unique and non-null. It is not exact for the v11
contract this authority still supports, whose documented assignment identity
allows a null generation. Historical authorization evidence must name the
specific claim act it ran under, not search for whichever indistinguishable
claim is newest when projected.

**Required correction:** durably bind every assignment-derived row to its exact
claim event (for example by an immutable claim-event identity/foreign key), and
project through that binding. Preserve the existing assignment document for
fencing and caller identity; do not infer the claim from current configuration,
timestamps, row order, or the nullable generation tuple. Add release/rebind/
reclaim/reopen tests under v11 and retain the already-green v12 history case.

## 2026-08-28 — the v11 reclaim join, corrected

**Confirmed by reproduction before changing anything.** Assignment-derived acts
joined back to their claim at READ time over
`(work_id, participant, generation)`, newest first. A v11 assignment mints no
generation, so release and reclaim through one endpoint produced two claim acts
with identical join fields and the later one became the apparent authorization
of the earlier act's history. The v12 case could not express the defect,
because generations distinguish v12 claims.

**Corrected by an exact reference captured at the act.** `activity`,
`contract_event` and `proposal` carry `claim_seq NOT NULL`, the assignment
event of the claim they were performed under, resolved when the act happens and
never searched for afterwards. An act that cannot name its claim is refused
rather than written with a null reference.

## 2026-08-28 — independent review complete

**Confirmed:** the exact-claim correction resolves the remaining P0. The
retained v11 public reproduction now keeps the first activity attributed to
`principal:baton.claude` and the second to `principal:one-person`, even though
their public assignment documents are equal. The regression proves the same
history after reopening the store; v12 proposal history remains pinned to its
own claim event.

**Confirmed:** the complete correction boundary is independently green: target
Work scopes authorize all receipt and close doors; deployment-only grants do
not widen scoped targets; direct acts retain immutable decisions; derived acts
join through stored claim identities; scoped grants preserve provenance; and
principal-keyed capacity spans endpoint addresses. The focused 50-case seam
suite, full 277-case authority suite, both public reproductions and 25/25
removal harness all pass. Review is signed off in
`review-2026-08-28T21-30-11Z.md`.
