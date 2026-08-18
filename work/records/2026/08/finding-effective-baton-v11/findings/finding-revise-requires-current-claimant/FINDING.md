# Finding: require the current claimant for Work contract revisions

## Observed — 2026-08-18

W104's post-W245 documentation proof used two participants who both resolve
through one route. Participant `ada` claimed the Work, but unclaimed route
handler `bee` could still run `revise` successfully and replace the live Work
contract while `ada` was executing it.

The authority currently gates `revise` only through route-handler
eligibility. It does not require the actor to be the exact `current` claimant.
That permits one eligible worker to alter assigned scope underneath another
eligible worker and defeats the claim's single-executor boundary.

## Confirmed decision being violated

The v11 design ruling recorded by the parent finding is that outsiders may
propose scope changes through discussion, but only the participant currently
handling the assigned Work may promote the complete replacement revision.
W245 clarified the vocabulary: `route` names who MAY claim; nullable `current`
names the one participant who IS executing. Therefore the revision authority
is the exact current claimant, not every handler eligible through the route.

This is a behavioral authority defect, not documentation latitude. W104 must
not normalize the broader implementation as the intended contract.

## Required behavior

- `revise` succeeds only when the actor is the exact current claimant of the
  open Work and is still eligible through its live route.
- An eligible but unclaimed route peer refuses without changing the revision,
  event journal, operation journal, messages, phase, route, or claim.
- Unclaimed Work refuses revision; discussion remains available for proposals.
- The claimant check and `expect=` compare-and-swap occur in the same authority
  transaction, so claim release/pass/recovery and competing revisions fail
  closed under races.
- Effectively-once retry preserves the exact committed revision; conflicting
  reuse or a retry after the assignment episode changes cannot authorize a new
  revision.
- Canonical JSON, CLI help, tests, and EFFECTIVE-BATON use W245 vocabulary:
  route is eligibility, current is the exact claimant.

## Acceptance boundary

- Positive coverage for the exact claimant promoting a discussion message.
- Negative coverage for an eligible route peer, an outsider, and unclaimed
  Work, each proving no mutation.
- Claim/pass/release/recovery and concurrent-revision race coverage proves the
  actor cannot revise after losing the claim and cannot revise Work claimed by
  somebody else.
- Operation replay/mismatch and injected-failure coverage proves one durable
  revision or none.
- The W104 guide, its regression, and executable workflow proof teach and
  verify claimant-only promotion after the authority correction lands.

