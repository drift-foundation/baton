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

## Superseding presentation ruling — 2026-08-17

**Confirmed by Slawomir.** The earlier ruling to render `>` for every open
unclaimed Work is superseded. Projection 8 makes `Current` authoritative: a
blank `Current` cell already states that nobody has claimed the Work. Repeating
the same fact in `Phase` and `Held` adds noise and makes the operational stage
harder to scan.

- Remove the `>` prefix from both the Phase and Held cells.
- Phase displays only the compact operational phase.
- Held keeps its elapsed value: since `claimed_at` while claimed, since the
  handoff while unclaimed, `-` when no timer origin exists, and `∞` at the
  existing cap. `Current` disambiguates claimed from unclaimed.
- Keep structured `current`, `claimed_at`, `handoff_at`, `pickup`, readiness,
  waiting, and parking facts unchanged in JSON.
- Do not restore the removed `!` timeout/heartbeat alarms.

This supersedes only the `>` presentation. The earlier diagnosis that
heartbeat silence is not failure, and that readiness/wait/park are independent
facts, remains authoritative.
