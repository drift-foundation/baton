# Finding: make unclaimed execution the primary Work cue

## Observation — 2026-08-17

W2 displayed an overdue `!` while in review. Canonical detail showed that it
was unclaimed, dependency-blocked, and not ready; adding its blockers had
correctly released the reviewer claim. The pickup projection nevertheless
continued aging the old handoff and rendered `!` even though authority rules
made a new claim impossible.

Separately, a claimed agent can remain alive and busy in one model/tool turn
without an opportunity to call `heartbeat`. Treating six minutes without a
protocol call as execution failure therefore creates false alerts.

## Confirmed ruling — 2026-08-17

**Confirmed by Slawomir.** The important operational signal is whether open
Work is unclaimed, because unclaimed means no participant is executing it.

- Render `>` for open Work with no active claimant. This is a state marker,
  not an overdue assertion, and applies independently of elapsed time.
- Claiming removes `>`. Release, pass, or a dependency/readiness change that
  releases the claimant restores it while Work remains open.
- Dependency readiness, waiting, and parking remain separate structured/table
  facts. They explain why unclaimed Work may not currently be claimable; they
  do not hide the unclaimed fact or convert it into an alert.
- Remove the six-minute `!` switch for pending pickup and the claimant
  heartbeat `!` suffix from the TUI. Held elapsed time is sufficient; silence
  does not infer failure.
- Heartbeat events and timestamps may remain available as structured
  diagnostics. Agents are not required to interrupt a busy turn merely to
  keep presentation from alarming.
- Closed Work has no execution claim and receives no `>` cue.

The current `pickup: overdue` result for blocked W2 is not a valid execution
obligation. Canonical projection must not describe dependency-blocked,
waiting, parked, or terminal Work as overdue for pickup. Glyphs remain TUI
presentation only.

## Acceptance boundary

- Ready/unclaimed, blocked/unclaimed, waiting, parked, claimed, released,
  passed, and terminal rows prove the exact marker independently of timer age.
- Crossing six minutes changes neither the unclaimed marker nor a claimed
  row's suffix.
- A heartbeat or its absence never changes the marker or Held duration.
- JSON keeps claimant/readiness/phase facts structured and carries no glyph.
- The MM:SS/overflow follow-up composes without changing these semantics.
