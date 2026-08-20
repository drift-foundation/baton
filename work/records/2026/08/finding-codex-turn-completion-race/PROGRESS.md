# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The code path is exactly as the finding describes.
`waitForTurnCompletion` was a pure listener: it attached to
`turnCompleted` when called, had no prior-state check and no timeout.
`#notification` emitted `turn/completed` straight to the emitter, so a
completion delivered before a waiter existed went nowhere.

Three production callers install the wait after awaiting `turn/start`
— `runOnce`, the dispatcher's drain, and W424's `bootstrapThread` —
so all three depend on the app-server not completing a turn in that
window.

Still classified suspected: I have not seen it against a live
app-server, and this slice does not claim to have. What it does is
remove the dependence on an ordering nobody has established.

## What changed

`CodexClient` retains completions. `#notification` records the turn
under `(threadId, turnId)` BEFORE it emits `turnCompleted`, and
`waitForTurnCompletion` consumes a matching record first and only then
installs its listener. `takeCompletion` is the one read, and it
consumes: one completion answers one wait.

The listener path consumes too. A wait that was already listening
takes the record when it fires, so it cannot leave one behind for a
later wait on the same turn to find — which would have turned this
fix into a different bug.

**Bounded**, at 64 by default and configurable per client. A
long-lived dispatcher completes turns forever and a cache that only
grows is a leak with a helpful name; the record evicted is the oldest
one nobody came back for, and re-insertion on a duplicate keeps that
order genuinely least-recently-received.

**Cleared on disconnect and on close.** Retained completions belong to
the connection that delivered them. A wait installed after the socket
died is unsettled, and unsettled waits fail closed — resolving one from
a pre-disconnect record would report a turn as freshly complete to a
caller with no connection to act on it.

A malformed `turn/completed` with no turn id is not retained: there is
nothing to key it by, and inventing a key would let it satisfy a
waiter it has nothing to do with.

## A test that hangs is not a regression

The defect's symptom is a wait that NEVER settles, so the obvious
regression makes the suite stall rather than fail — I wrote it that
way first and it cost a run to discover. Both cases that await a
completion now race a 250 ms timer and assert the wait settled, so
removing the fix produces two named failures in under a second instead
of a hang somebody has to interrupt and diagnose.

I verified that in both directions: with the prior-state check removed,
`a completion that arrives before the waiter still resolves it` and
`one completion answers one wait` fail; with it restored, all eleven
pass.

## Verification

- `tools/codex-event-bridge/test/codex_client.test.mjs` — **11 passed**
  (7 new). The racing fake completes the turn BEFORE resolving
  `turn/start`, which is the ordering the old waiter could not
  survive. Covered: the early completion resolves the wait; a
  completion after the waiter behaves exactly as before and leaves
  nothing behind; thread AND turn identity both have to match, so
  neither another thread's completion nor another turn's satisfies a
  waiter; one completion answers one wait; five duplicates retain one
  record; retention is bounded and evicts the oldest unconsumed
  record; a disconnect drops the records and fails a pending wait
  closed; and a completion with no turn id is not retained.
- The Codex bridge suite — **119 passed**, including W424's bootstrap
  cases and the dispatcher's own turn handling, which exercise the
  changed primitive without changing.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2488 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## What this slice does not do

No timeout was added to `waitForTurnCompletion`. The finding names the
missing timeout as part of why the hang was unrecoverable, but a
timeout is a different decision with its own failure semantics — how
long, and what a caller should do when it fires — and the acceptance
boundary asks for the race-safe primitive rather than a deadline.
Recorded here rather than done quietly.

No Baton protocol, projection, or database change, as ruled.


## Response to review `review-2026-08-19T22-25-08Z.md`

**P1 accepted — I closed one missed-event window and left the one next
to it.** Rejecting on the `disconnected` EVENT only covers a waiter
that was already listening. A caller whose socket dropped between
`startTurn` returning and `waitForTurnCompletion` being called heard
nothing, found an empty cache (disconnect clears it, correctly), and
waited forever. That is the same class of defect this Work exists to
remove, arrived at from the other side — and my own dossier had
already written down that disconnect must stay fail-closed for an
unsettled wait, so the requirement was not even in doubt.

The connection is now a state to CHECK and not only an event to hear:
`waitForTurnCompletion` rejects immediately when the client is already
disconnected, naming the turn. It is checked BEFORE the cache
deliberately — a disconnect clears retention, so there is nothing to
find, and reading the state first says why rather than leaving a bare
unresolved lookup.

The ruled cache semantics are untouched: retention is still cleared on
disconnect and is never used to report success afterwards.

The reviewer's regression passes unedited, and I checked it in both
directions — removing the state check makes
`a waiter installed just after disconnect also fails closed` the one
failure in the file.

- `codex_client.test.mjs` — **12 passed**.
- The Codex bridge suite — **124 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2488 passed** (parallel), **40 passed** (serial), both bridge
  suites green — W459's reviewer regressions were corrected under
  their own claim in the round before this one, so the shared tree is
  green again.
