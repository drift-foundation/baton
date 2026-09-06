# V11 TUI consumes sustained CPU without user input

Work: W102477

## 2026-09-06 — observed runtime cost

**Observed.** The operator identified PID 4106058 as the likely TUI process.
Process inventory confirmed the exact command as:

```text
python3 /home/sl/opt/baton/v11/latest/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw tui
```

While the TUI was receiving no operator input, `ps -Af` reported it at 23% CPU.
Across a ten-second sample its accumulated CPU time increased from 32 to 35
seconds, approximately 30% of one core. This is sustained work rather than one
transient render sample.

**Confirmed boundary.** This is a v11 TUI defect and is not on the v12
integration critical path. The cause is not yet established. In particular,
the observation does not by itself distinguish an event-loop spin, excessive
refresh cadence, repeated full projection reads, terminal rendering, or work
proportional to the current ledger size.

## Investigation and correction boundary

1. Reproduce the idle cost with the deployed TUI and a controlled local
   instance, recording elapsed and CPU-time deltas rather than relying on one
   instantaneous percentage.
2. Instrument or otherwise bound the rates of event-loop wakeups, refreshes,
   Baton projection reads, and renders. Identify the dominant path before
   changing behavior.
3. Establish whether the cost depends on the selected page, focus, terminal
   size, Work/message count, or active versus idle coordination state.
4. Apply the smallest v11-only correction that preserves timely updates and
   keyboard responsiveness. Do not redesign the TUI or pull v12 work into this
   defect.
5. Add deterministic behavioral coverage for the corrected scheduling or
   invalidation rule. Do not add a timing-sensitive CPU-percentage assertion
   as the primary regression.

## Acceptance boundary

The Work is complete when the responsible loop or refresh path is identified,
the idle TUI no longer performs sustained unnecessary work, normal update and
input latency remain acceptable, and focused tests prove the scheduling rule
without relying on host-load timing.

## 2026-09-06 — responsible path attributed

**Confirmed.** The repository and deployed archive contain byte-identical TUI
implementations (SHA-256
`ce569775e0b94d9e8556cf342aa4bd970e3908ed48cf9dd18a31425b1b581c69`). A
controlled real-PTY sample against the deployed v11 configuration reproduced
22.7% of one core over 7.762 idle seconds. The reader blocked for 6.003 seconds
and returned only three timer expirations. This is not a `getch()` spin.

All 1.759 idle CPU seconds were spent in the three timer renders, and 1.702
seconds were spent in three `projection.tree()` calls. The path is:

```text
deadline -> Console.tick() -> schedule_refresh() -> render()
         -> rows()/header -> _window() -> cache clear -> projection.tree()
```

`Console.tick()` currently invalidates unconditionally, even when the ledger
has not changed. On the sampled 140-row window one tree call took 0.571
seconds. `projection._claimed_ats()` accounted for 0.454 seconds, and the
projection executed 140 row views and 3043 SQLite statements. This explains
both the measured cost and its dependence on the size/history of the visible
team window.

**Confirmed.** Jobs, Inbox, and Teams all pay this tree cost. The shared header
obtains the Jobs actionable count through `_window()` even when another tab is
selected. Terminal geometry is not the dominant input: work outside the tree
projection accounted for about 0.057 seconds across three timer renders.
Focus changes only cached selection/presentation and cannot suppress the
timer's unconditional invalidation. Current coordination activity is likewise
not a gate: `_claimed_ats()` scans last-claim history for every returned Work,
regardless of whether that Work currently has a Handler. The row/history
population, rather than active versus quiet routing, drives this idle cost.

Full counters and the reusable probe are in `evidence/RESULTS.md` and
`evidence/idle_probe.py`.

## 2026-09-06 — bounded correction rule

**Proposed for implementation revalidation.** Keep the configured monotonic
timer as the sole background observation cadence and keep a render at each
deadline, so client-derived Held values, phase-change cues, and keyboard
responsiveness retain their cadence. Replace unconditional full-cache
invalidation with one cheap `Authority.last_seq()` freshness read. Invalidate
and reproject only when that sequence differs from the last successfully
observed value. A successful local mutation continues to invalidate
immediately through the existing path.

An evidence-only cheap-poll variant retained three timer renders but performed
no tree projection on an unchanged ledger. It consumed 0.001868 CPU seconds
over 7.656 idle seconds (0.02% of one core), versus 1.759 seconds for the
normal loop. The existing global sequence is already the token canonical
projections expose as `snapshot_seq`; no new SQLite-specific TUI contract is
needed.

The timer outcome must distinguish (a) a successful unchanged probe, (b) a
successful changed probe requiring projection, and (c) a failed probe or
projection. An unchanged successful timer render still spends one visible
phase-blink cycle; a failed probe/projection spends none. This preserves the
three-cycle cue without using an expensive projection as a clock. Continuous
input must continue to respect the wall-clock deadline, and an external commit
just after a probe may wait only until the next configured deadline—the same
bounded race already present after a projection snapshot.

**Excluded.** Optimizing `_claimed_ats()` or the row-level message/unseen
queries would improve initial and changed-state render latency, but it would
not remove unnecessary unchanged-ledger work. That broader projection change
is not required for this v11 TUI correction and must not be folded into it.

## 2026-09-06 — implementation revalidation

**Confirmed.** The bounded correction rule still matched the current tree at
implementation start. Canonical tree and search projections already returned
their in-transaction `snapshot_seq`; `Authority.last_seq()` remained the pure
single-statement sequence read; successful local commands still scheduled the
shared refresh flag; and the event loop still used one monotonic wall-clock
deadline. No later ruling superseded those facts.

The implemented cache records the oldest snapshot token represented in its
current generation. This conservative floor preserves the bounded race while
also ensuring that a commit interleaved between two cache misses is noticed at
the next deadline instead of leaving the older answer cached indefinitely.
Every successful timer probe still leads to a render and owes one phase-cue
cycle. An unchanged render spends that cycle from cached rows; a changed render
spends it only after the required projection succeeds; a failed probe or
projection spends none.

## 2026-09-06 — approver ruling: sequence-gated refresh accepted

**Accepted.** The cheap `Authority.last_seq()` observation is the v11 TUI
freshness boundary. Each configured timer deadline still repaints presentation,
but an unchanged successful observation retains canonical projection caches;
only a changed sequence invalidates and reprojects. Successful local mutations
continue to invalidate immediately. A failed freshness observation or required
projection consumes no phase-cue cycle, while an unchanged successful repaint
may consume its owed presentation cycle from cached rows.

The bounded race is accepted: an external commit immediately after the cheap
observation may wait until the next configured deadline, exactly as a commit
immediately after a full projection snapshot could before this correction.
This ruling does not authorize projection-SQL optimization, a new polling
thread, a new persistence field, or any v12 redesign.
