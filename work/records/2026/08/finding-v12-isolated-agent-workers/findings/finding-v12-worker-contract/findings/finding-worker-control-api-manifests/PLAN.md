# Plan: v12 worker-control API and typed manifests

1. [completed] Revalidate every field and transition against W151 and the parent
   M1 freeze boundary.
2. [completed] Define version negotiation, envelopes, operation/event ordering,
   errors, capabilities and extension rules.
3. [completed] Define the complete typed manifest family and canonicalization,
   digest, limit and secret-exclusion rules.
4. [completed] Add machine-readable valid/invalid examples and an executable
   design-level validator/model without changing product code.
5. [completed] Independently review compatibility, ambiguity, retry and stale-
   generation behavior, then return the child for approval.
6. [amended 2026-08-22, W4487] The frozen `claim_token: null` decline shape
   contradicted W151 §7's bearer requirement. `baton.slaw` ruled for this
   contract's shape and superseded W151. §0 records that the general "W151
   wins" precedence rule is intact and this ONE conflict was ruled the other
   way; §6.1, §12 rule 14 and §13 carry the replacement authorization; the
   schema carries a `$comment` naming the ruling; the evidence gained one
   valid and two invalid vectors and five model tests (12 -> 17). Reviewed
   under W4487;
   `work/records/2026/08/finding-worker-control-decline-token-conflict/`.
