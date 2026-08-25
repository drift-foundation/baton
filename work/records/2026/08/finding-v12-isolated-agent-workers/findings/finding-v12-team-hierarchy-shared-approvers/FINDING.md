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

## Open design questions

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
