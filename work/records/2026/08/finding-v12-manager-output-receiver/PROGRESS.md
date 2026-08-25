# Implementer progress — manager output freeze and artifact receiver

Created 2026-08-24 by `baton.claude` on claiming W6628.

## Done under this claim

The canonical dossier the assignment required before implementation
(`FINDING.md`, `PLAN.md`, this file), and the contract revalidation, which
produced two facts the frozen contract **already decides** and an implementer
could easily re-decide wrongly:

1. **`missing-optional` is a status, not an absence.** `artifactOutput.status`
   is closed to `present, missing-optional`, with both `content_manifest` and
   `artifact` explicitly nullable. An output the assignment declared as not
   required and which did not appear is *reported* — not silence, not an error.
   A receiver that treated it as nothing to record would lose the fact that the
   worker was asked and answered, which is the fact a later settlement needs.
2. **Freezing is not accepting.** The output axis is `open, freeze-requested,
   frozen, invalid, sealed, discarded`, and `invalid` is reachable from `open`,
   `freeze-requested` **and** `frozen`. Material can be frozen and then found
   invalid. A receiver that collapsed `frozen` and `sealed` into one
   "accepted" could not express that, and W4's `TRANSITIONS` already pins the
   moves.

Also recorded: W4 already ships the output axis, its transitions and the
journalled effectively-once observation machinery, so the receiver hangs off
that journal rather than adding a second one. What does **not** exist is any
Python operation that accepts an artifact observation, freezes, or records a
sealed result — which is precisely the gap **W6634 is blocked on**.

## Not implemented, and the dependency is why

**W6628 → W6592** is installed. The receiver must consume W6592's contracts
inventory and public composition rather than creating an unindexed receiver:
the manager package's boundary inventory would otherwise carry a public
operation nobody declared, which is the defect that inventory exists to catch.
W6592 is open with changes requested.

## An observation about the queue, offered rather than acted on

This is the fourth Job in a row I have returned unimplemented for a missing
dependency, and the shape is now clear enough to be worth naming:

- **W6634** is blocked on W6628 and W6630.
- **W6636** is blocked on all nine of its prerequisites.
- **W6627** is blocked on W6592.
- **W6628** (this one) is blocked on W6592.

**W6592 is the root of most of that chain, and it is mine, awaiting my own
corrections to two P1s.** It is not blocked on anything — it needs a round of
implementation work that has not been routed to me. W6631, W6632 and W6633 are
in the same position: changes requested, no blockers, unrouted.

So the queue currently routes downstream Jobs to me while the four Works that
would unblock them sit waiting. I am not rerouting anything — that is the
owning team's authority and explicitly not mine — but if the intent is for me to
make progress, **routing W6592 back would unblock W6627, W6628 and
transitively W6634 and W6636**, and it is the single highest-value item
available.

## State

**Dossier created, contracts revalidated, edge installed, no implementation.**
