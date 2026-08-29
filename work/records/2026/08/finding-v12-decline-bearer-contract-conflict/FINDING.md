# Resolve decline-bearing-claim contract conflict

## Discovery

Discovered by W6's digest-bound conformance capability pass. This is a
top-level record because W6 already occupies the permitted second child level.

Ledger Work: `W33937`.

## Confirmed specification conflict

Portable case `C-decline-carrying-bearer-refused` requires a decline carrying
the claim bearer to be refused as `integrity/schema` while the offer remains
unterminated. The reviewed v12 offer boundary instead proves possession before
branching on accept versus decline; the measured request succeeds and settles
the offer `declined`. Both contracts cannot remain authoritative.

Evidence is retained under W6 at
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-local-conformance-proof/evidence/w6-seal/decline-bearer.json`.

## Decision required

Choose and pin whether every terminal offer decision requires the single-use
claim bearer, or whether decline must exclude it and reject its presence.
Chronologically supersede the losing rule in its owning finding and portable
case; do not patch the implementation or assessor until that ruling exists.

## Acceptance

- Offer validation, authority effects, replay/fencing, portable case text, and
  evidence requirements express one ruled bearer contract.
- Positive, missing/wrong/replayed bearer, accept/decline, and unchanged-offer
  refusal tests cover the selected rule.
- Register and case digests are deliberately revised after the ruling.
