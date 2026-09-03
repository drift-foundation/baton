# Plan

1. [done, reviewer reproduction 2026-09-02] Prove that restart abandonment
   leaves the Job stage projected `offered` with only a permanently deferred
   claim owed.
2. [pending; design approved 2026-09-03] Publish regenerable, level-triggered
   `offer.state` events from canonical Worker Manager state after recovery and
   whenever a consumer attaches or reconnects. Carry stable offer/attempt
   identity, canonical state, and monotonic state revision; do not expose
   Worker Manager tables to the Job Manager. Publication only enqueues after
   commit; it never invokes a recipient inline.
3. [pending] Consume those events at least once and idempotently in the Job
   Manager. Persist append-only stage execution episodes, ignore stale
   revisions, and constrain one abandoned predecessor to one fresh
   offer/attempt/assignment episode. Use a non-reentrant run-to-completion pump:
   each handler records or enqueues its next act and returns without waiting
   for another event.
4. [pending] Cover lost delivery followed by replay, duplicate and periodic
   republication, undelivered abandonment, accepted recovery, repeated
   restart, stale/out-of-order state, concurrent replacement, status history,
   no dispatch while either store transaction is held, and queued rather than
   recursive follow-up delivery.
5. [pending independent review] Bind the verdict to the immutable proposal,
   enumerate every changed production and test path, and confirm that the
   event transport is not a second authority or an exactly-once dependency.
