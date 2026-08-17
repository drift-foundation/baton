# Finding: render `Held` as capped minutes and seconds

## Confirmed ruling — 2026-08-17

**Confirmed by Slawomir.** The TUI `Held` value uses one `MM:SS`
interpretation for every ordinary value:

- derive elapsed whole seconds from the same canonical handoff or claim instant
  already selected by the current state-dependent Held contract;
- clamp a negative local-clock difference to zero;
- render `00:00` through `99:59` as minutes and seconds;
- at 100 minutes and beyond, render `∞` rather than saturating at `99:59` or
  presenting a value whose units cannot be inferred; and
- retain `-` where the existing contract has no timer origin.

The `Held` header and six-cell responsive column remain. The existing pending
pickup prefix and claimant heartbeat suffix compose with the new timer; the
overflow base value is `∞`, and a stale claimant may therefore display `∞!`.
Padding is presentation only and is not part of the value.

This supersedes only the timer scale and overflow spelling in
`../../FINDING.md`. Handoff/pickup state, the visible reset at claim, heartbeat
semantics, refresh scheduling, and canonical JSON timestamps remain unchanged.
No authority schema or JSON projection change is required.

## Acceptance boundary

- Pure boundaries cover zero, 59 seconds, 60 seconds, 59:59, 99:59, exactly
  100:00, well beyond the cap, and a negative clock correction.
- Scheduled refresh derives the displayed seconds from the current clock; it
  may advance by more than one second when refresh cadence is slower than one
  second and never needs its own timer thread or authority read.
- Pending, overdue, claimed, heartbeat-stale, repassed, unclaimed, and terminal
  rows retain their current origin/prefix/suffix behavior with the new scale.
- Narrow layouts continue to omit the complete Held column atomically.
