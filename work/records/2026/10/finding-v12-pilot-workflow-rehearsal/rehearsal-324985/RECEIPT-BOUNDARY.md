# The native path approves its own candidate — reproduced

Claim 324985, 2026-10-18. Driven by `receipt_boundary.py` on the accepted
integration-worker world (real coordinator, real admission driver, real
Authority, real worker entry; engine and provider simulated and labelled).
Evidence: `RECEIPT-BOUNDARY.json`, `step-6-receipt-boundary.json`. Recorded,
not fixed: no product source was edited, no receipt was manufactured and no
owner precondition was weakened.

This answers the question review 2026-10-18T17-50-33Z named, and withdraws the
hypothesis in `../rehearsal-324890/JOINED-GAP.md`, which is superseded.

## What the supported admission writes

On Work `0000000a-W1`, proposal `integration-driver.proposal:e8e10a8f…`, at the
admission boundary and before any runtime:

| Receipt | Disposition | Actor |
| --- | --- | --- |
| verification | `passed` | `baton.verify` |
| review | `accepted` | `baton.review` |
| **approval** | **`approved`** | **`baton.approve`** |
| integration | — | — |

All three come from `_accepted_receipts`, which proves the accepted checkpoint
and the exact ordinary-test evidence first and then writes all three together.

## What that does to the selected human approval

Asked on that same store, through the installed command:

- `disposition pending --work 0000000a-W1 --participant baton.slaw` answers
  `owner_action: integration-due`, with `holds: {approve, integrate, close}`
  all true. The owner is authorized, and the decision the pilot selected for
  them has already been taken by something else.
- `disposition approve …` as that owner is **refused, exit 2:
  `approval receipt is immutable`.**

So on the native path the owner cannot make the approval decision at all. It is
not that the owner's inputs are missing — they exist, and one of them is an
approval the owner did not give.

## Why that is a defect rather than a configuration choice

- Owner M321677 selects **single-human approval** for this pilot.
- T321689 M321689: "never infer owner approval from worker verdict or completed
  Job."
- The pilot assessment's own P1: "Automatic integration receipt actors cannot
  stand in for Slawomir's decision."
- This Work's FINDING: "Do not invent owner receipts inside mock internals" —
  and nothing here does; the receipt is the product's own.

## Is there a supported way to withhold it?

Not through this operation. `_accepted_receipts` takes `issue` as a single
flag: `issue=False` skips the verification, review AND approval writes
together, after re-proving everything, so there is no granularity that
publishes independently justified verification and review while leaving the
approval for the human. `admit_accepted` and `continue_accepted` both require
an `approver` session holding the `approve` capability, so a deployment cannot
configure the automatic approval away either.

## Bounded follow-up this justifies

One question with a spec basis: how does a deployment that selects single-human
approval admit an integration without the approval receipt being written for
it? Either `_accepted_receipts` grows the granularity its callers need, or the
owner-approval-first ordering becomes the selected path and admission consumes
an existing owner approval instead of writing one. That is a product decision
with an owner dimension, so it is reported here rather than chosen: this is a
preparation assignment.

Until it is resolved, the packet cannot promise single-human approval on the
native path, and `PACKET.md` §7a says so.
