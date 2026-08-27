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
