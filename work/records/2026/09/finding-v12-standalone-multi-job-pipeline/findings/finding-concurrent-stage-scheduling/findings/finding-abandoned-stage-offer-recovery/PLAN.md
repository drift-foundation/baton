# Plan

1. [done, reviewer reproduction 2026-09-02] Prove that restart abandonment
   leaves the Job stage projected `offered` with only a permanently deferred
   claim owed.
2. [done 2026-09-03] Publish regenerable, level-triggered
   `offer.state` events from canonical Worker Manager state after recovery and
   whenever a consumer attaches or reconnects. Carry stable offer/attempt
   identity, canonical state, and monotonic state revision; do not expose
   Worker Manager tables to the Job Manager. Publication only enqueues after
   commit; it never invokes a recipient inline.
3. [done 2026-09-03] Consume those events at least once and idempotently in the Job
   Manager. Persist append-only stage execution episodes, ignore stale
   revisions, and constrain one abandoned predecessor to one fresh
   offer/attempt/assignment episode. Use a non-reentrant run-to-completion pump:
   each handler records or enqueues its next act and returns without waiting
   for another event.
4. [done 2026-09-03] Cover lost delivery followed by replay, duplicate and periodic
   republication, undelivered abandonment, accepted recovery, repeated
   restart, stale/out-of-order state, concurrent replacement, status history,
   no dispatch while either store transaction is held, and queued rather than
   recursive follow-up delivery.
5. [done 2026-09-03] Independent review found that a canonical `claimed`
   offer was incorrectly recorded as the end of the stage episode on the next
   restart, dropping its current execution identity and projecting it
   `exceptional`. See `review-2026-09-03T03-34-03Z.md`. Corrected in
   correction pass 1: `documents.EPISODE_ENDINGS` separates the offer endings
   that end an EXECUTION from the offer's terminal set, `claimed` is
   deliberately absent, and two real two-restart regressions cover the claimed
   stage and the dependent gate it still holds.
6. [done 2026-09-03] Declare and exercise boundary probes for
   `worker_manager/events.py`'s three owned entries. The inherited 49-entry
   deficit did not authorize this candidate to widen the fail-closed gap to
   52. Done in correction pass 1, and correcting it uncovered a second
   deficit: removing `offer_state`'s double validation had left four RECEIVING
   entries with no owner (130 to 134), now declared in `STATED_OWNERS` and
   witnessed. Both counts are back to their inherited values with no exemption
   and no weakened assertion.
7. [done 2026-09-03] Decide and pin the read-only status attachment contract.
   Pinned: ONLY THE SERVING RECONCILER ATTACHES. Applying a canonical ending
   is a durable act and a read-only surface performs none, so
   `_ReadOnly.attach` and `_ReadOnly.drain` are removed rather than wired up;
   the review's non-mutating overlay was deliberately declined as a second
   derivation of stage state. The staleness bound is stated in
   `projection.status` and `tools._ReadOnly` and regressed.
8. [done 2026-09-03] Correction pass 2, answering
   `review-2026-09-03T04-01-25Z.md`: this plan's contradictory and duplicated
   items resolved into one ordered state; the vacuous
   `receipt_rows == receipt_rows` assertion in the no-write status regression
   replaced with before/after snapshots of episodes, receipts AND the
   operations journal, each proved to move when something does write; and the
   strict `EPISODE_ENDINGS`/`TERMINAL_OFFER_STATES` relation made a real
   import-time assertion in `manager.py` rather than an overstated claim in
   the proposal. Resealed.
9. [parked 2026-09-03, for a NAMED later pass] Decide whether `expired` and
   `declined` offers join `REPLACEABLE_ENDINGS`. Both wedge a stage the same
   way an abandonment does, but both were DELIVERED and answered, so whether
   to re-offer them to the same worker, a different one, or to report them is
   scheduling policy owned by W71877 rather than by this recovery correction.
   Neither is hidden meanwhile: the ending is recorded, stays in the status
   history, and projects the stage `exceptional`.

THE ONE LIVE ITEM IS 9, and it is parked deliberately. Items 1-8 are done; the
verdicts that produced 5-8 are preserved in the append-only review files, which
is where that history belongs -- this plan says what is true now.
