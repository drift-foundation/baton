# Progress

Owned by the participant making the implementation change under the W43975
claim.

## 2026-08-30 — first round (`baton.claude`, W43975 impl claim)

**NO PRODUCTION CODE CHANGED THIS ROUND, deliberately.** What this round did
is revalidate the enrichment against the tree, create and bind the child
record, and pin the decisions the wiring rests on — one of which I am not
willing to take alone.

### Revalidated, not assumed

All three of the enrichment's observations hold: no production caller of
`custody_act`, no production caller of `discard_workspace`, and no axis or
receipt for directory custody — `attempts.TRANSITIONS`'s `cleanup` axis is
`pending → blocked-on-intake → {complete, retained, failed}` and
`schema.CUSTODY` is `("accepted", "quarantined")`, which is intake's ARTIFACT
ownership and a different fact about a different object.

I also read the ordering `authorize_cleanup` already has, because the
enrichment says to retain it: authority fence, receipt as part of the identity,
live-assignment refusal, `uncertain`-runtime refusal, destroy, exact absence,
and no journal for an unsettled result so a retry can try again.

### Pinned

- **The noun is `directory_custody`**, not `custody`. Overloading intake's
  would make a receipt about artifacts answer a question about directories.
- **One identity per (attempt, root, verb)**, so `workspace` and `result` stay
  separately attributable and success on one cannot hide failure on the other.
  It is the same triple W43974's helper identity derives from, which is what
  lets a crash mid-act reconcile the helper against the journal.
- **An accountable success is a precondition, not a report.** Nothing is
  removed and no terminal cleanup is written until the helper answers `ok`.
  W43974's lost-act answer is `UNRESOLVED` by construction on the Docker CLI
  boundary, so this path treats that as retryable and never records a false
  completion from it — which is the rule this ending already applies to an
  unsettled destroy rather than a second one invented beside it.

### THE RULING I AM ASKING FOR

Which of the three endings directory custody applies to.
`authorize_failed_start_cleanup` ends at `retained` on **approver ruling
M33800** — the result directory "began untrusted and stays untrusted after a
start fault", it deletes nothing, and a later explicit retention cleanup owns
that deletion. Running normalize-and-remove there would contradict a ruling
this Work does not own.

My reading is that it applies to the ORDINARY cleanup only, and that the other
two stay as they are until the retention cleanup M33800 names exists. I am
asking rather than guessing because wiring the wrong reading either leaves the
manager unable to remove what it must, or deletes material an approver said to
keep — and the second is not a mistake a test round would catch, because the
test would encode the same guess.

### Not started

The production wiring, the durable receipt, and the regression matrix.
