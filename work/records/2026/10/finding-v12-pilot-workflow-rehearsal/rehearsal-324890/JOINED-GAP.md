# SUPERSEDED 2026-10-18 by rehearsal-324985 — read that first

**This note's conclusion was wrong and is withdrawn.** Review
2026-10-18T17-50-33Z established why: the driver stopped at integration
`claimed`, which is BEFORE admission, and
`integration/driver.py:_accepted_receipts` (1105-1178) writes verification,
review and approval — `admit_accepted` calls it around 1513, before any
runtime. So null receipts at a stop point I chose proved nothing about whether
receipts are produced, and the claim that a container turn was needed to find
out was an untested hypothesis rather than a finding.

Two further corrections to the text below: the proposal id quoted in the prose
(`fa5686a9…`) is from an earlier run and is not the one the manifest binds
(`integration-driver.proposal:0eb2794d…`), and the "suggested disposition"
section asked for work that `rehearsal-324985` has now simply done.

What is actually true at that boundary — receipts written automatically by the
configured approver, and what that does to the selected human approval — is in
`rehearsal-324985/RECEIPT-BOUNDARY.md`. The observations of the native
lifecycle in the sections below (stage states, route moves, attempt and
candidate identities) stand; only the conclusion drawn from the absent
receipts is withdrawn.

---

# Reproduced joined gap — the owner path's inputs are never written

Claim 324890, 2026-10-18. Reproduced by `joined_rehearsal.py` on the accepted
`ComposedOneJobCase` world; evidence beside this file. Recorded, not fixed:
this is a preparation assignment and the review's instruction is to file a
reproduced product gap with evidence rather than edit product source here.

## What was driven, all through the accepted code

One submitted Job, carried by ordinary manager ticks:

| Stage | State reached | Work route after |
| --- | --- | --- |
| implementation | `completed` | `rview` |
| review | `completed` | `integration` |
| integration | `claimed` | `integration` |

Real identities captured in `step-1-native-lifecycle.json` and
`step-3b-integration-stage.json`: implementation attempt
`attempt-7b5e070a…`, review attempt `attempt-9e961a44…`, and a published
proposal `integration-driver.proposal:fa5686a9…` whose `assignment_ref` names
the implementation participant and generation. So the terminal implementation
result DOES reach a native eligible independent review assignment with exact
Work/attempt/candidate binding — M324395 proof 1, behavioural half, and it is
not merely a status row.

## The gap

At every point reachable above, the four authority receipts on that published
proposal are `null`:

    verification: null   review: null   approval: null   integration: null

So `disposition pending` on that same authority answers `awaiting-verification`
with `holds: {approve: true, integrate: true, close: true}` — the owner is
authorized and has nothing to decide. The owner's approval can never become
due, because `approve` requires a passed verification receipt and an accepted
review receipt, and the native review ending does not write either. The Job
side records its verdict (stage `completed`, route advanced to the integration
stage); the authority side, which is where the owner's disposition reads from,
is untouched.

The two halves of the selected pilot workflow therefore do not meet on this
path.

## What this does NOT establish, stated precisely

The integration stage is `claimed`, not run. Its worker turn is a container,
which this Work excludes, so this rehearsal cannot say whether the integration
worker would write those receipts once it ran. The honest bound is:

- **Reproduced:** from a natively reviewed Job, nothing between the
  implementation ending and the integration *claim* writes the verification or
  review receipt the owner disposition requires, and the owner path is
  therefore unreachable without the integration worker's own turn.
- **Unproven either way:** whether that turn writes them. The accepted
  composed case stops at `claimed` for the same reason.

That distinction matters for what the pilot packet may claim: a deployment
cannot promise the owner disposition is reachable until the link at the
integration worker turn is demonstrated, and the demonstration needs either
the real container boundary or a supported simulation of that worker's turn.

## Suggested disposition

A bounded follow-up that answers exactly one question: does the integration
worker's turn write the verification and review receipts for its published
proposal, and if not, which actor is meant to? It needs the integration worker
turn simulated at its own boundary — `tests/tools/test_integration_worker.py`
already composes that world — so it is deterministic work, not a live run.

No product source was edited to produce this note, and nothing here proposes a
correction to the owner command: `disposition` requiring a passed verification
and an accepted review is W321689's accepted behaviour and the reason the gap
is visible at all.
