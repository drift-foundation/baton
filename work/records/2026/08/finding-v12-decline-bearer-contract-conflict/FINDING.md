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

## Approver ruling — 2026-08-28, reaffirmed 2026-09-02

Keep the previously approved bearer-free decline contract. The claim bearer is
an acceptance capability, not a general offer-decision token:

- acceptance requires the exact unspent bearer, atomically consumes it and may
  mint a claim;
- decline carries no bearer, creates no claim, atomically terminates the exact
  offer and consumes its verifier so the bearer cannot later accept;
- an exact repeat of either committed decision replays that committed result;
- a decline carrying any bearer refuses as `integrity/schema` without changing
  the offer; and
- a stale, foreign, differently bound or operation-colliding decline refuses
  without rewriting committed state.

The decline remains authorized by the caller's participant authority and the
exact integrity-protected binding of offer, runtime attempt, Work, decision and
reason. Bearer-free does not mean anonymous or unauthenticated.

Revalidation on 2026-09-02 found that the assignment state-machine, worker
control manifest and portable conformance case already contain this rule. They
chronologically superseded the older W151 requirement on 2026-08-22. The
conflict measured by W6 is therefore not between two live durable rulings: the
Python `accept_offer` boundary is stale because it validates possession before
branching and currently lets a bearer-carrying decline settle the offer.
Correct that implementation and its tests; do not weaken the portable case or
revive the superseded W151 rule.

## Acceptance

- Offer validation, authority effects, replay/fencing, portable case text, and
  evidence requirements express one ruled bearer contract.
- Positive, missing/wrong/replayed bearer, accept/decline, and unchanged-offer
  refusal tests cover the selected rule.
- Register and case digests are deliberately revised after the ruling.
- An exact acceptance retry replays the committed acceptance after bearer
  consumption instead of failing merely because the verifier is now spent.
