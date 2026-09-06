# Progress

## 2026-09-06 — baton.tuner implementation result

Claimed W102477 and revalidated the recorded correction against the current
source. The timer still invalidated the entire shared cache unconditionally;
canonical projections still exposed their in-snapshot global sequence; and
successful local mutations, the monotonic event-loop deadline, and the
three-cycle phase cue retained the boundaries recorded in FINDING.md.

Changed `Console.tick()` to perform the cheap `Authority.last_seq()` probe and
schedule the existing invalidation only when the current cache generation is
absent or stale. The cache records the oldest successful `snapshot_seq` in its
generation, so a writer interleaved between separate cache misses is detected
conservatively on the next deadline. Every deadline still renders. A successful
unchanged probe can spend one phase-cue cycle from cached rows, while a changed
probe spends it only after projection succeeds; probe and projection failures
spend nothing. The event loop, local mutation path, projection SQL, authority
surface, and refresh interval are unchanged.

Updated the superseded unconditional-projection expectation, added a failed
freshness-observation regression, and made the existing failed-projection case
force the changed-sequence branch. The existing real-PTY and continuous-input
coverage remained intact; no host CPU percentage assertion was added.

Verification:

- Focused refresh/blink suite: 20 passed.
- `just test-v11`: 3,337 parallel Python tests, 54 serial/PTY Python tests, and
  129 bridge tests passed.
- Real-PTY `idle_probe.py normal jobs`: three ticks and three renders over
  7.706 idle seconds, zero idle tree projections, 0.001714 CPU seconds.
- Python compilation and `git diff --check`: passed.

Implementation and bounded regression work are complete. W102477 is ready for
independent review; PLAN.md item 5 remains queued.

## 2026-09-06 — baton.tuner response to first review

Addressed the bounded P1 in
`review-2026-09-06T15-13-51Z.md`. A successful render now retires any timer
token that was not spent by the table, search, or awaiting-work row boundary.
The retirement happens only after `_render_bar` completes the terminal refresh,
so Teams, Inbox, detail, links, and pokes leave the invisible cue count intact,
while a failed projection or terminal paint retains the token for retry.
Ordinary key renders have no timer token to retire.

Added the requested cross-view regression in
`tests/work/test_w336_blink_drain.py`. It arms a three-cycle cue, renders Teams
at an unchanged timer deadline, returns to Jobs by key and proves the count is
still three, then proves the next successful Jobs timer render spends exactly
one cycle.

Verification after the review correction:

- Focused refresh/blink suite: 21 passed.
- `just test-v11`: 3,338 parallel Python tests, 54 serial/PTY Python tests, and
  129 bridge tests passed.
- Real-PTY `idle_probe.py normal jobs`: three ticks and three renders over
  7.656 idle seconds, zero idle tree projections, 0.002054 CPU seconds.
- Python compilation passed; scoped `git diff --check` is recorded after this
  entry.

The first review finding is addressed and W102477 is awaiting independent
re-review. No projection SQL, event-loop deadline, interval, authority, or
unrelated behavior changed.
