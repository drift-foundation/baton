# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

`wait_actionable` is as the finding describes: one loop, one pure
re-derivation of `participant_actions` per pass, and
`_time.sleep(min(0.05, remaining))` on an empty read. Nothing else in
the tree polls readiness — the TUI has its own refresh timer on a
cached projection and never touches this path, and both bridges reach
it through `baton wait timeout=`.

The timeout semantics were already correct and needed no change: the
deadline is computed once from `monotonic()`, the sleep is already
bounded by `remaining`, and `timeout=0` already falls through to a
single read. So this slice is the interval and nothing else.

I checked which existing tests depend on the cadence. Two do — both in
`test_ws2_due.py`, and neither is ABOUT it: one proves the wait wakes
when a deadline arrives, the other that it sees a commit from another
connection. Both arrange their event at 0.15 s against a 5 s timeout,
so at the new cadence they still pass, one second later each.

## What changed

`READINESS_POLL_SECONDS = 1.0`, a module constant beside the function,
used as `min(READINESS_POLL_SECONDS, remaining)`. That is the whole
product change.

It is a constant rather than an operand because the finding rules one
fixed operating default for now, and a knob would invite tuning a
number nobody yet has evidence about. Being a module attribute is what
lets tests state a different interval without adding configuration to
the protocol.

The comment beside it records the two things a later reader needs: why
one second is right for coordination that happens on seconds-to-minutes
timescales, and that the interval is a floor on POLLING and never on
the caller's deadline.

`docs/EFFECTIVE-BATON.md`'s readiness section now says the wait
re-derives about once a second while empty, that the interval never
extends `timeout=`, and that `timeout=0` is still a single read — so
an agent meets the latency in the guide rather than in the wild.

## The two existing tests

I set the interval to 50 ms in `test_wait_wakes_when_the_deadline_arrives`
and `test_wait_sees_a_competing_message_commit`, with the reason at each
site. Their subject is that the wait wakes at all, not how long an idle
poll lasts, and leaving them at the shipped default would have spent two
seconds of gate time proving something my own suite pins deterministically
in microseconds. Their timing assertions are unchanged and still meaningful.

That is a judgement call, so it is written down rather than buried: the
alternative — leaving them slow — would have exercised one real
one-second sleep end to end, which is exactly what the acceptance
boundary asks the suite not to pay for.

## Verification

- `tests/work/test_w321_readiness_cadence.py` — new, **17 passed**,
  and it sleeps for **zero wall time**: the fake replaces both
  `monotonic` and `sleep`, so the durations the wait ASKED FOR are the
  evidence. Covered: the constant is one second; a five-second idle
  wait sleeps `[1,1,1,1,1]` and derives the projection six times, not
  a hundred; the deployed `timeout=60` shape costs 61 reads;
  `timeout=0` sleeps not at all and reads once; sub-second timeouts of
  10 ms, 50 ms, 250 ms and 999 ms each return at their own deadline;
  a 2.5 s wait ends on a bounded 0.5 s remainder; across five timeouts
  no sleep ever exceeds the interval or the remainder and they sum to
  the timeout exactly; an already-actionable wait returns without
  sleeping; a Work committed while the wait is asleep is returned by
  the very next read; the returned actions equal
  `participant_actions`'s own output key for key; the wait still
  writes nothing and stays participant-relative; and the guide states
  the cadence and its bound.
- One test is a live comparison rather than prose: with the interval
  set back to 50 ms the same idle minute costs about **1,200**
  derivations against **61**, so the finding's arithmetic stays
  checkable instead of becoming a claim in a document.
- `test_ws2_due.py` **33 passed** in 0.80 s (it was 1.9 s before this
  Work, because two of its cases slept at the old cadence and now
  poll faster deliberately).
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2467 passed** (parallel), **40 passed** (serial), both bridge
  suites green — and no slower than before this Work.

## What this slice deliberately does not do

No configuration, schema, projection or protocol field. No control
socket and no `kick` — the finding puts an immediate-refresh mechanism
explicitly outside this Work, and a second of latency is the cost that
buys until one exists.
