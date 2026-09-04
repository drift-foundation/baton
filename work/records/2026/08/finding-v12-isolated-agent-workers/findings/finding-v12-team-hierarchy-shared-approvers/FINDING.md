# V12 team hierarchy and shared approvers

## Parent campaign

This is a deferred M6 adoption finding under
`work/records/2026/08/finding-v12-isolated-agent-workers/`.
Its authoritative ledger item is W9901. V11 refused `baton.prompt` attaching
the child directly to W10 because only W10's resolved `baton.feat` handler may
mutate its containment. W9901 therefore remains top-level until an authorized
handler places it; the dossier and roadmap preserve its intended M6 ownership.

## Confirmed requirement — 2026-08-25

V12 needs organizational team hierarchy and principals that are not owned by
one leaf team. A single approver may oversee several related subprojects;
another leaf team may use a dedicated one-to-one approver. The authority must
preserve that these are scoped grants to one principal rather than unrelated
copies of a person under several team addresses.

Example shape:

```text
infrastructure
  orch
  tls
  uflow

product
  pc
```

An infrastructure approver may receive an approval grant over the
`infrastructure` subtree, while `pc` may bind its own approver. This hierarchy
does not place repositories inside one another and creates no Work dependency.

These node names and shapes are deployment choices. For example, Slawomir may
instead create one grouping-only `admins` node above every working team and
grant one Slawomir principal approval authority over that complete subtree.
The `admins` node need not own a repository or Work. Another deployment may
have no administrative root and use only leaf-local one-to-one approvers.
Baton supplies the model and deterministic resolution; it does not prescribe
either topology.

## Required properties

- Principals, organizational/team scopes, repositories, and routes are
  separate canonical entities.
- Organizational nodes may be grouping-only, with no repository and no owned
  Work.
- A role grant names one principal, one role, and one explicit scope.
- A shared principal has one inbox, runtime identity, availability/capacity
  view, and audit history across every scope it serves.
- Every act records both the principal and effective team/scope.
- Leaf-local one-to-one bindings remain possible.
- Resolution is deterministic and inspectable and refuses missing or
  ambiguous authority.
- Organizational ancestry never implies Work containment, dependency,
  scheduling order, repository ancestry, or filesystem access.

## Cross-team manager clarification — confirmed 2026-09-04

V12 must let one principal act as a team manager for several explicitly scoped
teams without creating or selecting a separate `<team>.member` identity for
each team. The manager has one authenticated identity, session, inbox,
capacity view, and audit history. A deployment grants that principal the
desired management roles or capabilities over one organizational node or
subtree; it may grant approval, recovery, configuration, dispatch, or a
smaller deployment-defined set without changing the principal's identity.

Each authorized operation still records the one principal, the effective team
or scope, the exercised grant, and its provenance. Cross-team management does
not make Work ownership, repositories, routes, or worker identities global,
and it does not grant authority outside the configured scope. `team manager`
is the operator-facing concept; it is not an alias-generation scheme and does
not require one durable identity per managed team.

## Historical open design questions — resolved 2026-08-25

**Superseded by the confirmed M6 baseline below.** These questions are
retained as the chronological record of what the reviewer design pass had to
rule; none remains open after Slawomir's approval in T9901 message 10740.

- Whether the organizational structure is strictly a tree or a constrained
  DAG.
- Whether a leaf binding overrides, augments, or must explicitly mask an
  inherited grant.
- How multiple approvers express alternatives versus quorum approval.
- How shared-principal capacity and absence affect routing without silently
  changing authority.
- How the TUI shows inherited versus local grants and provides one cross-team
  inbox for the principal.

These questions are intentionally deferred until M6 ordering. They are not a
reason to expand v11's team-local participant model.

## Reviewer baseline — 2026-08-25

**Observed:** the current Python v12 authority has no principal, organization,
team, repository or role records.  `authority/schema.py` stores an opaque
`work.route`, maps that route directly to a `team.member`-shaped participant in
`route_handler`, grants deployment-global capabilities directly to that same
participant, and keys the one live `claim_slot` by participant.  Workflow
receipts record only `actor`; neither the effective Work-owning scope nor the
grant that authorized the act survives in the row.

**Observed:** `authority/identity.py`, `authority/session.py`, and
`worker_manager/authority_port.py` deliberately bind a runtime session and an
assignment to one `team.member` participant.  That is the correct v11-shaped
fence, but it cannot represent one principal acting for two scopes without
minting two participant identities.  `receipt_one_per_kind` also admits only
one approval receipt per proposal, so quorum is not expressible by treating
multiple approvers as more route handlers.

**Confirmed:** the current global `claim_slot` is a useful invariant to retain
at the principal level.  One human or agent serving several scopes is still one
resource and must not acquire one live claim per spelling of its team address.
The key must change identity, not become scope-local.

**Inferred implementation boundary:** eventual adoption reaches
`authority/{schema,identity,api,core,session}.py`, the authority tests and
boundary inventory, assignment/receipt manifests, and the Worker Manager's
participant-bound port, offers, attempts, sessions, capacity and projections.
The TUI has no v12 Teams/Inbox implementation yet.  No production edit belongs
in this design Work, and M6 remains gated behind W1431/W1433.

## Proposed M6 model — approved in the confirmed ruling below

The `Proposed` labels in this section preserve its pre-approval decision
history. The complete package was subsequently approved without replacement;
the confirmed ruling after the conformance matrix is now authoritative.

### 1. Organizational structure is a strict forest

**Proposed:** each organizational scope has zero or one parent.  The accepted
configuration is a forest: unique scope ids, no cycles, no multi-parent nodes.
A node independently declares whether it may own Work, routes or repositories;
grouping-only nodes declare none of them.

A shared principal receives multiple grants when it crosses unrelated roots.
That is clearer than making the organization a DAG: every target then has one
ancestry chain, one subtree meaning, and one deterministic place to inspect
inheritance.  Cross-cutting authority remains explicit in grants instead of
being hidden in a second parent edge.

### 2. Canonical records stay separate

**Proposed records:**

- `principal(principal_id, display, state)` — one human/agent identity;
- `org_scope(scope_id, parent_scope_id, kind)` — the strict forest;
- `membership(principal_id, scope_id, relation)` — directory/roster evidence
  only, never authorization;
- `role(role_id)` — the closed role vocabulary for the accepted generation;
- `role_grant(grant_id, principal_id, role_id, scope_id, extent)` where extent
  is exactly `local` or `subtree`;
- `role_mask(mask_id, role_id, scope_id, extent)` — an explicit stop to
  ancestor inheritance;
- `route(route_id, owner_scope_id, role_id, selection_policy)`;
- `repository(repository_id, owner_scope_id, root_binding)`; and
- `approval_rule(rule_id, scope_id, mode, threshold, policy_generation)`.

Membership never implies a role.  A repository never implies an organizational
parent.  A route never invents a scope from its spelling.  Work stores both its
owner scope and route id, and configuration validation requires the route to
belong to that scope.

### 3. Inheritance augments; replacement is explicit

**Proposed:** grants applicable along the unique root-to-target chain
accumulate.  A local grant therefore augments inherited grants and never
silently overrides them.  A deployment wanting a dedicated leaf approver adds
an explicit mask for the inherited approval role at that leaf and then adds the
leaf grant.  A mask affects only the named role and extent; it grants nothing.

Resolution is order-independent: apply the nearest applicable mask boundary,
then collect applicable grants at and below that boundary.  Duplicate grants
to the same principal collapse by principal identity while retaining every
grant id as audit provenance.  Missing grants refuse.  Multiple surviving
principals are valid only under an explicit route/approval selection policy;
otherwise resolution refuses as ambiguous.

### 4. Alternatives and quorum are policy, not handler count

**Proposed:** route execution uses explicit `one-of` selection: every resolved
principal is eligible, one successful claim wins atomically, and no grant is
promoted because another principal is absent.

Approval supports `one-of`, `all-of`, and integer `threshold` rules.  The rule
and the resolved eligible-principal set are frozen at the proposal's approval
policy generation.  One principal contributes at most one approval decision to
that proposal.  `threshold=1` expresses alternatives; `threshold=N` expresses
quorum.  Conflicting decisions or an unreachable threshold remain visible and
do not synthesize approval.

This requires approval attestations separate from the one aggregate approval
outcome; expanding `receipt_one_per_kind` into multiple indistinguishable
`approval` rows would lose both the rule and whether it was satisfied.

### 5. Availability and capacity never rewrite authority

**Proposed:** eligibility is resolved entirely from accepted grants, masks and
policy.  Runtime availability and capacity are separate operational facts.
The scheduler may offer only to a currently available eligible principal, but
zero available principals produces an inspectable `no-available-principal`
condition while Work stays at its configured route.  Absence never activates a
masked grant, changes a threshold, reroutes Work, or delegates authority.

The claim slot, runtime inventory, offer state and capacity counters key on the
global principal id.  Thus one Slawomir approver has one capacity and runtime
view across every scope.  The principal's inbox is the union of obligations,
offers, approvals and attention addressed to that principal, with each row
annotated by effective scope, role and source grant.

### 6. The authority derives and records the acting scope

**Proposed:** a runtime session is bound to one principal, not to a caller-
supplied team spelling.  For every act, the authority derives the effective
scope from the target Work/proposal/route, resolves the principal's role at
that scope under the accepted policy generation, and records:

- exact principal id;
- effective scope id;
- role id;
- source grant id(s) and mask boundary;
- accepted configuration/policy generation; and
- the existing exact Work/assignment/proposal identity.

The caller never chooses `effective_scope`.  Supplying another scope cannot
broaden a principal's session.  Standalone assignment and workflow receipts
carry the derived scope so evidence remains attributable without reopening the
live configuration.

## Required conformance matrix

**Positive:**

1. one principal approves `infrastructure/orch`, `infrastructure/tls` and
   `infrastructure/uflow` through one subtree grant and appears once in the
   unified inbox/capacity projection;
2. `product/pc` masks an inherited approver and authorizes its dedicated local
   principal;
3. one-of alternatives race safely and one atomic act wins;
4. a threshold rule records independent attestations and emits one aggregate
   outcome only when the frozen threshold is met; and
5. a grouping-only root owns no Work, route, repository or filesystem root.

**Negative/race/retry:**

1. cycles, a second parent, missing parents and duplicate scope ids refuse at
   configuration acceptance;
2. membership alone, repository ownership and name-prefix similarity grant
   nothing;
3. local-plus-inherited approvers without an explicit selection rule refuse as
   ambiguous;
4. a leaf mask for `approve` does not mask `review`, sibling scopes or its own
   local grants;
5. a principal absent or at capacity remains authorized but receives no new
   offer; no substitute is invented;
6. the same principal cannot consume two quorum seats through two grants;
7. policy-generation change cannot alter the eligible set or threshold of an
   existing proposal; and
8. an exact retry replays the same principal/scope/grant authorization proof,
   while reuse after a grant or scope change collides or starts a new operation
   under the new accepted generation.

## Decision package — superseded by approval

**Superseded 2026-08-25:** this approval request was answered affirmatively in
T9901 message 10740. It originally asked to adopt the package above as one
coherent baseline:
strict forest; augment-by-default plus explicit role masks; explicit one-of or
threshold policy; principal-global capacity and inbox; availability that never
changes authority; and authority-derived scope/grant audit evidence.  A change
to any member should name the replacement rule because the pieces determine
each other's ambiguity and audit behavior.

## Confirmed M6 baseline — 2026-08-25

**Approved by Slawomir in T9901 message 10740:** adopt the complete reviewer
package without replacement:

1. organizational scopes form a strict forest; cross-root sharing is expressed
   through explicit grants to one global principal, never multiple parents;
2. principal, scope, membership, role grant, role mask, route, repository and
   approval-policy records remain separate canonical entities;
3. inherited grants augment by default, while replacement requires an explicit
   role-specific mask;
4. approval policy explicitly selects `one-of`, `all-of`, or integer
   `threshold`, with the eligible principal set and rule frozen at the
   proposal's accepted policy generation;
5. runtime, inbox, claim capacity and audit identity are principal-global;
   availability may affect offers but never rewrites authority; and
6. the authority derives effective scope from the target and records principal,
   scope, role, source grant/mask provenance and accepted generation on every
   act.

This baseline supports both one shared parent/subtree approver and dedicated
one-to-one leaf approvers as deployment choices. It does not authorize
production implementation in this design Work: schema/resolver, receipt,
scheduler/manager, conformance and Teams/Inbox implementation remains ordered
after W1431/W1433 and must be decomposed into independently reviewable M6 Jobs.

## Cross-milestone compatibility ruling — 2026-08-26

Parking W9901 defers the complete M6 hierarchy implementation and its Teams /
Inbox UX; it does **not** defer applicability of the approved model. The
baseline above is a binding architectural constraint on foundational M2-M5
work now. The purpose is to avoid completing earlier schemas, identities,
receipts, routes or runtime contracts that must later be discarded when M6 is
implemented.

Any earlier Work that touches principals/participants, organizational scope,
route ownership, repository ownership, grants, claim slots, approval receipts,
runtime/capacity or inbox identity must revalidate against W9901. It need not
implement the full hierarchy early, but it must preserve a representational
seam for global principal identity, authority-derived effective scope and
grant provenance rather than making `team.member`, actor-only evidence or a
flat team spelling irreversible.

If an active design cannot preserve that seam without guessing the later M6
schema, it stops and records a typed dependency/correction; it does not ship a
flat assumption merely because W9901 itself is parked. A bounded compatibility
audit is therefore required before foundational v12 authority/manager
contracts are treated as complete.

The earlier W1431/W1433 wording records the pre-migration schedule and is
superseded as a literal locator. In the current authority, W10 is the M6
rollout/adoption milestone and remains blocked behind W9. That ordering still
defers full feature implementation, not this compatibility constraint.

## Foundation compatibility audit outcome — 2026-08-26

W16793 completed the required source/schema audit in its bound child record.
The four-part authority/Work/participant/generation assignment remains a valid
endpoint execution fence, participant-bound sessions correctly prevent callers
from choosing an actor, opaque route spelling is usable, and absent repository,
hierarchy and Inbox models remain safely deferred.

Three flat assumptions cannot wait for M6: the authority lacks a distinct
principal, Work scope and grant-provenance decision and keys global claim
capacity by endpoint participant; the trusted Worker Manager persists and
labels execution without that principal/scope context; and the receipt schema
permits only one approval actor rather than immutable attestations plus a frozen
one-of/all-of/threshold decision. Bound provider Work W16821, W16823 and W16830
own those corrections respectively. Full forest resolution, inherited grants,
masks and Teams/Inbox UX remain deferred here. Approver obligation 16832 records
the serial scheduler edges because the reviewer has no authority to mutate
`impl`-routed Work.
