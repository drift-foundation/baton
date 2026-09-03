# Recover abandoned Job-stage offers after restart

Ledger Work: W73629

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-concurrent-stage-scheduling/`

## Observed — 2026-09-02

The Worker Manager correctly abandons an `issued` offer owned by an earlier
manager incarnation because no durable fact proves its bearer was delivered.
The Job manager, however, retains the stage's `admit` receipt, derives the
stage as `offered`, and continues to owe only `claim`. The canonical offer is
now `abandoned-after-restart`, so every claim attempt is an ordinary deferred
precondition and the stage never returns to an admissible state.

The retained reproduction is
`/tmp/w71877-abandoned-offer-repro.py`. Against `efbad19` it reports:

```text
{'recovered': {'abandoned': ['offer:job-a/implementation'], 'recoverable': []}, 'stage_state': 'offered', 'owed': ['claim'], 'offer_state': 'abandoned-after-restart'}
```

This predates W71877's pool implementation. Adding a durable worker
reservation around the existing path would turn the stage wedge into a pool
capacity leak as well.

## Confirmed boundary

An abandoned offer is immutable history and its receipt must not be deleted or
rewritten. Recovery needs a new offered-and-claimed execution episode with
fresh offer and runtime-attempt identities, while the status projection keeps
the abandoned episode visible. The Worker Manager remains the owner of offer
settlement; the Job manager consumes a public canonical offer observation and
decides that a new episode is owed.

W71877 must not hide this by freeing a slot while leaving the stage permanently
`offered`, nor by treating the old offer as live. Scheduler reservation release
may compose the corrected canonical ending once this Work closes.

## Approved level-triggered event boundary — 2026-09-03

**Confirmed:** Worker Manager recovery remains wholly owned by the Worker
Manager. The Job Manager neither reads its tables nor re-decides whether an
offer is abandoned. The normal communication boundary is a regenerable,
level-triggered Worker Manager state event, not a one-shot transition notice
and not Job Manager polling of Worker Manager storage.

After recovery, and again whenever a consumer attaches or reconnects, the
Worker Manager enumerates the relevant canonical offer rows and publishes
their current state as `offer.state` events. An event carries at least the
offer and attempt identities, canonical state, and a monotonic state revision.
The event transport is not authoritative: the Worker Manager store is, and
the same state event can be reconstructed from it at any time. An in-process
delivery is sufficient for the current combined Python process; a later
socket, broker, or remote adapter changes transport only.

Delivery is at least once. Republishing the same event immediately, after a
restart, or periodically is explicitly safe and has the same effect as one
delivery. The Job Manager records or applies the observed state idempotently,
ignores an older revision after a newer one, and constrains one abandoned
stage episode to at most one replacement episode. A duplicate abandonment
notice therefore cannot mint a second offer, attempt, assignment, or worker
reservation.

This ruling supersedes any interpretation of the earlier "public canonical
offer observation" language as a request/response read used for ordinary
recovery. A public diagnostic query may still exist, but recovery progress is
driven by replayable state events. A durable transition-event log is not
required for this slice because the retained offer row can regenerate the
current terminal state; preserving every intermediate Worker Manager
transition would be a separate requirement.

### Non-reentrant delivery

**Confirmed:** in-process does not mean inline callback. Publishing an event
only appends its owned document to a transient queue and returns. A top-level
run-to-completion pump dispatches queued events after the producer has
committed and released every store transaction and lock. A handler processes
one message, records its durable effect or owed action, enqueues any follow-up
command or event, and returns; it never waits for another event and never
recursively invokes another handler.

Worker-directed or otherwise blocking activity is outside the event pump. Its
request is represented durably, execution reports completion through a later
event, and the pump remains free to serve unrelated state. The current
single-process implementation needs only a small standard-library queue and
explicit pump; it does not require `asyncio`, a third-party signal package, or
a broker. The queue is not durable authority: losing it on restart is safe
because owed commands and current state events are regenerated from the two
canonical stores.

## Acceptance

- A restart after offer issuance but before acceptance records the old offer
  as abandoned and makes a fresh stage episode admissible.
- The fresh episode has distinct offer, attempt, and assignment identities;
  the old receipt and abandonment remain auditable.
- Reconciliation is idempotent across a second restart and cannot issue two
  live offers for one stage episode.
- A delivered-and-accepted offer remains recoverable and is never replaced.
- Status distinguishes the abandoned episode from the new queued/offered
  episode without storing a shadow copy of offer state.
- Startup and consumer attachment regenerate the current canonical
  `offer.state` assertions; losing an earlier delivery cannot wedge the stage.
- Repeating one state event, including periodic republication, is a no-op after
  its one corresponding Job Manager effect has committed.
- A stale lower revision cannot regress a stage or replace the fresh episode.
- No event is delivered inline under a Worker Manager or Job Manager
  transaction, and a follow-up event is queued rather than dispatched
  recursively.
- A handler that needs a later fact records that need and returns; it cannot
  block the pump waiting for the fact it expects another event to deliver.

## Test-change authority

This Work authorizes additive tests and edits under `v12/python/tests/job_manager/`
for abandoned-offer observation, episode replacement, restart races, and
status history. No deletion, weakening, or unrelated test change is authorized.
