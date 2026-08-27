# Separate approval attestations from the aggregate approval decision

## Discovery and ownership

Discovered by W16793 while auditing the Python authority's already-built
workflow substrate before M3. Ledger Work W16830 is bound to this record. The
record is promoted to a top-level dossier because the discovery record already
occupies the permitted second child level.

## Confirmed incompatibility

W9901 requires approval policies that may be one-of, all-of or threshold, with
the eligible principal set and rule frozen at proposal policy generation. Each
attestation must be attributable to principal, effective scope, role and grant
provenance; availability never changes eligibility.

The current authority instead stores exactly one receipt of each kind:

- `authority/schema.py:receipt` has `UNIQUE (proposal_id, kind)` and records one
  participant `actor` plus a caller-supplied `policy_generation`;
- `authority/core.py:_write_receipt` refuses a second approval as immutable,
  and `integrate` asks only whether that single row says `approved`;
- `authority/session.py:approve` supplies the session participant as actor but
  no authority-derived effective scope or grant proof;
- worker-control 1.0 `approvalReceipt` likewise models one actor and generation,
  not a frozen eligible set, policy rule, individual attestations and an
  aggregate decision.

One shared approver can fit that row, but a 2-of-3 or all-of policy cannot be
represented without overwriting evidence or inventing an aggregate actor. This
is an invalidating M3 foundation, not deferred Teams/Inbox UX.

## Required correction boundary

1. Separate immutable per-principal approval attestations from the one
   aggregate approval decision/outcome consumed by integration.
2. Freeze the policy rule, eligible principal set and policy generation against
   the proposal before accepting the first attestation. Later availability,
   route or membership changes do not rewrite that snapshot.
3. Authorize each attestation through W16821's principal/scope decision seam and
   retain principal, effective scope, role and grant/mask provenance.
4. Define denial, duplicate principal, changed policy, stale proposal and
   threshold race behavior explicitly. One principal contributes at most one
   effective attestation per frozen policy unless a later approved model says
   otherwise.
5. Keep verification, technical review and integration receipts distinct.
   Decide explicitly whether their existing one-row semantics remain valid.
6. Version authority persistence and worker-control receipt exchange rather
   than changing sealed 1.0 receipt meanings in place. Full hierarchy policy
   resolution remains deferred to W9901; direct M3 policies may exercise the
   same typed evaluator seam.

## Acceptance

- Positive cases prove one-of, all-of and threshold approval, including one
  shared parent-scope approver and one dedicated leaf approver.
- Negative cases prove an ineligible principal, masked grant, duplicate
  principal, caller-selected scope and post-publication policy/membership
  changes cannot satisfy the frozen rule.
- Concurrent final attestations produce one deterministic aggregate outcome
  without losing either immutable attestation.
- Integration consumes only the aggregate result tied to the proposal,
  candidate/target digests and frozen policy generation.
- Existing single-approver deployments remain expressible as a one-of policy;
  no full M6 org resolver or UI is implemented here.
