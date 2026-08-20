# Progress

Implementer-owned. Work `W3243`, claimed by `baton.claude` 2026-08-20.

## Revalidation

The incident reproduces from the code without needing the logs. The dispatcher
already OBSERVED the approval request — `client.on("serverRequest", …)` logs
it, publishes `waiting-input(approval)` on the runtime lease, and re-emits it —
and then does nothing else. The request is never answered, so the app-server's
turn never ends; `state.status.type` stays non-idle; `#drain` returns early on
exactly that condition; and `statusSnapshot` computed `loaded` from
`connected && status !== "notLoaded"`, which is TRUE for a wedged target. That
is the whole defect: a target that could take no delivery reported healthy,
and every later readiness event queued behind one turn.

W482's and W484's fixes are untouched — this is neither a connection failure
nor a completion race, it is a turn that never completes.

## Implemented (PLAN item 3)

Two new client primitives, deliberately narrow:

- `CodexClient.respondError(id, code, message)` — the ONLY response shape this
  bridge may send to a server-initiated request. An error response DENIES: it
  cannot be mistaken for or widened into an approval, and it invents no result
  schema the bridge does not own. Leaving the request unanswered was the
  defect; answering it with a decision would be the other one.
- `CodexClient.interruptTurn(threadId, turnId)` — end a turn this bridge
  started and can no longer complete.

`EventBridge` gains the ruled sequence in `#denyAndRecover`: deny immediately,
record the target as `blocked` (turn, cause, method, instant, whether the
denial and interrupt succeeded), and start a bounded timer. On expiry
`#interruptBlocked` interrupts; if that fails the target is published `failed`
and stays visibly undeliverable, with a log naming the queue depth and telling
the operator to restart the managed stack. Nothing here approves anything and
nothing creates a replacement context — the ruling gives that to v12.

`#clearBlocked` runs from both paths that observe a turn actually ending
(`turnCompleted` and an `idle` status), so the unhealthy report clears on the
same fact that makes delivery possible again, and `#drain` refuses while
`state.blocked` is set so a wedged target cannot take a delivery it would only
queue.

`statusSnapshot` now distinguishes loadable-and-idle from loaded-but-unable.
Every target row carries `deliverable`, `participant`, `threadId`,
`queueDepth`, `oldestQueuedMs` and a `blocked` block; `ready` is false while
any target is blocked. `enqueue` stamps `queuedAt` because depth alone never
said for how long — 24 events was the incident's number, and the age is the
fact an operator acts on.

`approvalRecoveryMs` (default 15s) is validated deployment config beside the
other bounds.

## One superseded test, corrected in place

`runtime_publisher.test.mjs`'s "publishing the state is not answering the
request" asserted the behaviour this Work exists to change — and leaving the
request unanswered is exactly what wedged the target. It is now "the request
is DENIED, never approved", with a dated note saying which half was superseded
and which half stands. The half that stands is the one that matters: no path
here ever sends something an app-server could read as permission, and a
separate test asserts that directly.

The two test fakes gained `respondError` and `interruptTurn`; they model the
client, and they were simply incomplete.

## Regressions (PLAN item 4)

Ten cases in `tools/codex-event-bridge/test/event_bridge.test.mjs`, each named
for the ruling clause it holds:

- an approval request is DENIED rather than left unanswered;
- denying is not approving — every response is an error, never a decision;
- a blocked target reports `deliverable: false` and the stack `ready: false`,
  while STAYING connected and loaded, so loaded-but-unable is distinguishable;
- the diagnostics name the thread, turn, cause, queue depth and oldest age;
- more than one readiness event is retained, not dropped;
- the turn ending drains everything queued behind it;
- the blocked turn is interrupted within the bound;
- an interrupt that fails leaves the target visibly unhealthy and approves
  nothing on retry;
- one target's wedge never delivers its events to another identity, and does
  not stop an unrelated target receiving;
- a second request on the same wedge does not restart the recovery clock.

Confirmed non-vacuous in two directions: removing the deny-and-recover call
fails 8, and removing only the unhealthy reporting fails 2.

## Verification (PLAN item 4)

- `codex-event-bridge` — 147 passed.
- Full v11 gate on the final tree — 2746 parallel, 52 serial, 55 ACP,
  all passed. (The dispatcher suite is not part of `just test-v11`; it is
  run directly, above.)

## 2026-08-20 — review round 1: changes requested

`review-2026-08-20T15-17-04Z.md`. All three correct, all three mine, and the
reviewer's two additive cases are green.

**P1 — recovery interrupted a guessed turn.** I stored `state.activeTurn?.id`,
which is this bridge's record of a turn IT started and can still be null when
the server request races the continuation that sets it — precisely when
recovery matters. The app-server schema REQUIRES `params.turnId` on an
approval request, so the request is now the authoritative locator.

A disagreement between the named turn and a recorded one is REPORTED rather
than silently resolved: two different turn ids on one thread is a fact an
operator needs, and picking one quietly would hide it. The request still wins,
and a request that names no turn falls back to the recorded one — a bridge
that trusted the schema absolutely would interrupt nothing if a server omitted
it. Both directions are now covered.

**P2 — the recovery timer survived a clean stop.** `stop()` cleared
`retryTimer` and `reconcileTimer` and not `blockedTimer`, so a callback could
interrupt through a disconnected client and publish a failure caused by
nothing but the shutdown that failed to cancel its own timer — after the
runtime had already reported a clean exit. `stop()` now owns every timer this
bridge starts, and `#interruptBlocked` returns early while stopping.

**P2 — a tautological assertion, and it was mine.**
`assert.equal(status.ready, false || status.ready)` reduces to
`status.ready === status.ready` and could never fail. Replaced with the exact
ruled post-recovery expectations: the wedge is gone, the target is
`deliverable` again, and queue depth plus deliveries accounts for all three
retained events, so one cannot be lost rather than redelivered.

### Regressions added (now 151 cases)

The reviewer's two, plus two of my own for the reconciliation the fix
introduces: a turn-id disagreement is reported, and a request naming no turn
falls back to the recorded one.

Non-vacuous: reverting the authoritative locator fails 1, reverting the stop
cancellation fails 1 — each exactly the reviewer's case for it.

Verification after the correction: dispatcher suite 151 passed; full v11 gate
2746 parallel, 52 serial, 55 ACP.

## State

Awaiting independent review (round 2).
