# Finding: reduce readiness polling to one second

## Status

Confirmed by Slawomir on 2026-08-19 and ready for implementation.

## Observed

`wait_actionable()` implements v11's blocking readiness surface by repeatedly
re-deriving the participant-action projection from SQLite and sleeping at most
50 ms between empty reads. Each participant has its own readiness bridge and
its own `baton wait timeout=60` process, so an idle deployment performs about
20 projection reads per second per configured member.

This is agent coordination, not a real-time control loop. Agent pickup and
execution operate on seconds-to-minutes timescales; a 50 ms idle cadence spends
database and CPU capacity without a meaningful UX benefit.

## Confirmed decision — 2026-08-19

- Change the internal empty-read cadence from 50 ms to 1,000 ms.
- `wait timeout=` remains the caller's overall deadline. A timeout shorter than
  one second still returns at that timeout; the sleep is always bounded by the
  remaining duration.
- Action derivation, participant identity, read-only behavior, episode keys,
  due predicates, and bridge delivery semantics do not change.
- No configuration, schema, projection, or protocol field is added in this
  slice. One second is the fixed operating default for now.
- A future bridge control socket or `kick` may request an immediate canonical
  refresh, but that is explicitly outside this Work.

## Acceptance boundary

- An empty readiness wait performs no more than roughly one projection read per
  second after its initial read, rather than twenty.
- `timeout=0` remains an immediate pure read.
- Positive timeouts below one second remain bounded by the requested timeout.
- A committed actionable item is observed within at most one polling interval,
  subject to scheduling.
- Existing action contents, deduplication, redelivery, and read-only guarantees
  remain unchanged.
- Focused tests pin the one-second cadence without adding one-second sleeps to
  the test suite; concurrency/timeout and complete v11 gates remain green.

