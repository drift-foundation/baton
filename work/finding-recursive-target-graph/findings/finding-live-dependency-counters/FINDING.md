# Finding: the v11 Work table exposes only the reverse dependency count

## Observed

While assembling the second-trial release gate, each command of the form:

```text
block RELEASE --on CORRECTION
```

increased `Dep` on the correction while the release row remained `Dep 0`.
This is internally consistent with the current projection—`dep` counts live
dependents—but contradicts the ordinary reading of “dependencies” and hides
the release Work's growing open-blocker count from the table.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** Work projections and
the TUI expose both directions as separate live counters:

- `Blk`: the number of **open blockers** this Work currently depends on;
- `Dpts`: the number of **open dependents** currently depending on this Work.

These are active-work counters, never historical totals. Adding
`block CONSUMER on=PROVIDER` increments `CONSUMER.Blk` and `PROVIDER.Dpts`.
When the provider closes with any explicit terminal outcome, it stops being an
open blocker and the consumer's `Blk` decreases. When the consumer closes, it
stops being an open dependent and the provider's `Dpts` decreases. Historical
edges, outcomes, and the acts explaining each change remain available through
links/events rather than inflating either live counter.

The canonical JSON surface uses unambiguous full names such as
`open_blockers` and `open_dependents`; the ambiguous row field `dep` must not
remain the only machine-facing description. The compact TUI headings are
exactly `Blk` and `Dpts`. Recomputed projections, restart, and ledger rebuild
must yield the same two counts.

This is queued for the next immutable revision. The current trial's graph is
correct and is not rewritten; the finding concerns projection and UX clarity.

## Compact-label clarification — 2026-08-15

**Confirmed by Slawomir after reviewing the paired columns.** The compact
dependent label is `Dep`, not the earlier proposed `Dpts`. Paired with `Blk`,
its direction is clear while remaining familiar and narrow:

- `Blk` — open blockers this Work waits on;
- `Dep` — open Work depending on this Work.

This supersedes only the compact `Dpts` spelling above. Canonical JSON remains
the unambiguous `open_blockers` and `open_dependents` pair.
