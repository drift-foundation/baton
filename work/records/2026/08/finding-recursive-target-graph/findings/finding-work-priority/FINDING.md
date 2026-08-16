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

## Revalidation against schema 15 — 2026-08-16

**Confirmed.** The fresh-authority cutover already supplied the persisted
groundwork without implementing the feature surface: `work.priority` is
required, constrained to `high|normal|low`, defaults to `normal`, and the
canonical row projection exposes it. The activated schema-15 authority can
therefore receive this feature without another fresh database or migration.

**Confirmed.** No public operation currently changes priority, creation does
not accept it, Work-list projections still order only by `created_seq`, and
the TUI has no `Pri` column. W3 remains open; the persisted default alone is
not the approved feature.

**Proposed implementation boundary.** Add one audited, effectively-once
`prioritize work=... as=high|normal|low` operation. Authorization follows the
confirmed team-local rule: any configured member of the Work's owning team
may change priority, independent of Current route, claimant, phase, and
readiness. Closed Work refuses mutation. A successful change advances the
ordinary Work change identity; an exact retry replays, and a same-value new
operation refuses.

Canonical list ordering should preserve containment: order root siblings by
priority rank then `created_seq`, and independently order each parent's child
siblings by the same keys. Never pull a child away from its parent to create a
global priority sort. Links, Threads, obligations, and other non-Work-list
projections retain their existing relation-specific ordering.

## Open rulings before implementation — 2026-08-16

1. Should `create` accept optional `priority=...` atomically, defaulting to
   `normal`, or should every new Work begin normal and use `prioritize` as a
   separate act?
2. At narrow terminal widths, where should the four-cell `Pri` column enter
   the existing whole-column drop order? The conservative proposal is to drop
   `Pri` first, preserving every existing narrow layout while showing it at
   comfortable widths.

## Creation and compact-display rulings — 2026-08-16

**Confirmed by Slawomir; this resolves both open rulings above and supersedes
the earlier `Pri` / `High|Norm|Low` TUI spelling.** `create` accepts an
optional canonical priority and defaults it to `normal`. Omitting the operand
therefore preserves the natural default; callers that already know the Work
is high or low priority may record that fact atomically at birth.

The compact TUI column is two cells: header `Pr`, values `Hi`, `No`, and `Lo`.
Canonical JSON and mutation input remain the full strings `high`, `normal`,
and `low`; the abbreviations are presentation only. `Pr` is the first whole
column omitted under width pressure, preserving every existing narrow layout.
