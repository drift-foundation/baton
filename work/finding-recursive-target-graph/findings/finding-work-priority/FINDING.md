# Finding: v11 Work has no priority

## Observed

The fresh second v11 trial began with eight independent open Work items. All
were ready, dependency-free, and presented without an ordering signal. Phase,
readiness, ownership, and personal `New` counts answer different questions;
none expresses which otherwise-actionable Work the owning team considers more
important.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** Work has one team-local
priority with exactly three canonical values:

- `high`
- `normal`
- `low`

`normal` is the natural default. There is deliberately no `urgent`, numeric,
or finer-grained priority tier: extra levels invite escalation and destroy the
signal.

Priority is an ordering signal only. It does not change readiness,
dependencies, Current or Next, route resolution, handler authority, phase,
status, closure, or any other lifecycle transition. The owning team may revise
its Work priority through an audited authoritative operation. Members of other
teams may discuss urgency in a Thread but cannot reprioritize that team's Work.

The JSON surface exposes the full canonical value. The compact TUI column is
`Pri`, rendering `High`, `Norm`, or `Low`. Within a priority tier, the existing
stable canonical ordering remains the tie-breaker; priority must not create an
unstable or client-private order.

This is queued trial feedback, not authorization to modify the currently
deployed immutable distribution or activated authority in place.
