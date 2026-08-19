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

## Reopened UX defect — 2026-08-18: blank Current does not explain timer origin

**Observed by Slawomir on the live projection-9 TUI.** W4 and W5 are both
unclaimed waiting rows with no visible claimant. W4's `Held` clock advances
because it has a historical `handoff_at`; W5 renders `-` because it has no
handoff origin. Nothing visible on either row explains that distinction, so a
user cannot tell why otherwise equivalent rows have different clocks.

This falsifies the 2026-08-17 claim above that blank/nonblank `Current` fully
disambiguates the two timer interpretations. It distinguishes claimed from
unclaimed, but it does not distinguish handed-off unclaimed Work from Work
that was born or became waiting without a handoff.

**Proposed correction, not yet confirmed:** `Held` measures only the interval
held by an actual current handler and renders `-` whenever no handler exists.
If pickup delay remains useful, expose it as a separately and explicitly named
fact rather than overloading `Held` with an origin that the row does not show.

### Confirmed direction — distinguish scheduler conditions

**Confirmed by Slawomir.** Hiding the timer alone is not the complete fix: W4
and W5 are in different scheduler conditions and therefore need different
phases. W4 is waiting for a directed obligation/decision; W5 is blocked by an
unmet Work dependency. Collapsing both into `waiting` hides the reason one can
advance through external input while the other cannot advance until another
Work closes.

The compact names and timer treatment remain to be finalized. The current
recommendation is `wait` for an external obligation and `block` for unmet Work
dependencies. Any timer shown beside either must start at entry into that
visible state, not at an older invisible handoff timestamp.

### Superseding ruling — one blocked phase, typed Wait cause

**The different-phase direction immediately above is superseded by
Slawomir's clarified ruling.** Work has one `block` scheduler phase whenever
an unsatisfied gate prevents progress, regardless of whether the gate is
another Work or a directed Message obligation. The compact `Wait` column names
the typed cause:

- `W4` means the Work is blocked by Work W4; existing `+N` compaction remains
  available for additional Work blockers.
- `M66` means the Work is blocked by the obligation created by Message M66.
  The Message selector is the useful human locator; an internal obligation
  number is not required in the compact row.

The Work detail view exposes the full gate kind, endpoint, obligation state,
and source Message. JSON carries typed fields rather than requiring clients to
parse `W`/`M` presentation strings.

**Proposed timer completion, not yet confirmed:** every `block` row measures
from the instant its currently displayed gate became active, whether the cue
is `W…` or `M…`. Alternatively every blocked row must show `-`; retaining the
current handoff-derived timer for only some blocked rows would preserve the
original unexplained inconsistency.

### Confirmed timer ruling — track every blocked interval

**Confirmed by Slawomir.** Every `block` row runs the timer. Delay caused by
waiting for any gate to clear is operational lag and must remain visible:

- `block W4` times from when W4 became the displayed unsatisfied Work gate;
- `block M66` times from when the Message-derived obligation became the
  displayed unsatisfied gate; and
- changing the displayed gate starts a new interval, while refreshes and
  unrelated events do not reset it.

The canonical projection exposes the gate kind, locator, and start instant.
The TUI derives elapsed display time from that instant. It never substitutes
`handoff_at`, `last_changed_at`, or a client-local observation time.

### Final Held-state clarification

**Confirmed by Slawomir.** `Held` measures the two intervals that represent
real operational time:

- `active`: elapsed time actually held by the current claimant, starting at
  `claimed_at`;
- `block`: elapsed time held by the displayed unsatisfied gate, starting when
  that gate became active.

Queued, parked, and terminal Work render `-`. An unclaimed handoff does not by
itself start a visible Held timer. This makes every advancing clock explainable
from the same row: Handler names active execution; `Wait=W…` or `Wait=M…`
names blocked execution.

## Implementation revalidation — 2026-08-18

**Confirmed current-code facts.** This is not a presentation-only rename.
Authority currently stores the single `waiting` phase plus either the aggregate
`gates` condition or one obligation. Two same-phase changes are intentionally
silent today:

- satisfying a Message obligation while a Work dependency remains retargets
  the condition from `obligation` to `gates` without an event; and
- closing or removing the displayed Work blocker while another remains changes
  `first_open_blocker` without changing readiness or phase.

Both silences contradict the confirmed timer ruling. A client cannot invent a
new start instant for either change, and `last_changed_at`, the older edge's
creation time, or the later edge's original creation time are not substitutes.
The authority must therefore commit a typed current-gate episode and its start
instant whenever the displayed gate changes, even when the Work remains in the
same `block` phase.

**Pinned gate-selection rule.** The displayed Work gate remains the existing
deterministic oldest open blocker by permanent creation order. Adding another
open blocker while that blocker remains displayed does not change the episode
or reset Held. When the displayed blocker closes or its edge is authoritatively
removed, the next oldest open blocker becomes displayed in that transaction and
starts a new episode then; its earlier edge-creation time is not reused. When a
Message obligation clears while Work blockers remain, the oldest open Work
blocker becomes displayed and starts its episode in the obligation-resolution
transaction.

The canonical JSON state must expose one structured current gate rather than
requiring clients to combine `waiting_on`, `first_open_blocker`, and journal
timestamps. It includes at least:

- gate kind (`work` or `message`);
- the canonical Work or source-Message locator and its local `W…`/`M…`
  selector;
- the gate episode's canonical `started_at`; and
- for a Message gate, the pending obligation identity/state and resolved
  endpoint needed by Work detail.

The TUI `Wait` and `Held` cells are pure renderings of that structure. Work
dependency compaction may still show `W4+N`, but the timer belongs only to the
displayed `W4` episode. Handoff and pickup fields remain history and do not
drive Held.

**Compatibility boundary.** `waiting` is replaced by the public scheduler
phase `block`; this protocol is still under intentional v11 evolution, so old
projection spelling is not a compatibility constraint. If persisting the
current gate and episode start adds authority columns, use a fresh schema
version rather than migration or event-history inference. The implementation
must keep phase-event playback honest: a gate change within `block` is a new
gate episode but not a fabricated phase transition.

## Revalidated acceptance boundary

- A queued or active Work acquiring its first dependency enters `block`,
  releases any claimant atomically, displays `W…`, and starts Held at that
  transaction.
- Adding a non-displayed dependency does not reset the displayed gate episode.
- Closing or removing the displayed dependency selects the next blocker and
  resets Held even though phase remains `block`; clearing the last one queues
  the Work and stops Held.
- A blocking directed request enters `block M…` at publication. Its response or
  disposition either queues the Work or retargets it to `block W…` with a new
  episode start.
- Refresh, heartbeat, priority/category edits, ordinary Messages, and other
  unrelated events do not reset the gate episode.
- Claim starts active Held from `claimed_at`; release/pass without a gate,
  queued, parked, unclaimed handoff, and terminal states render `-`.
- Work detail, list JSON, TUI `Wait`, TUI `Held`, Events phase duration, and
  JSON/TUI parity agree without parsing presentation strings.

## Supersession — 2026-08-18: blocked time is not `Held`

**Confirmed by Slawomir during the `7bea055` live cutover.** The earlier
"Final Held-state clarification" is superseded only where it makes `block`
advance the `Held` column. A Work with no Handler is not held by a recipient;
showing an advancing Held clock beside W2 while it merely waits on W3 makes
the column claim that somebody is executing or failing to pick up the Work.

`Held` now measures only current Handler ownership, from `claimed_at`, and
renders `-` for every unclaimed state including `block`. The structured gate
and its episode timestamps remain authoritative and useful in `Wait` and the
Events play-by-play; removing their compact Held rendering does not remove
blocked-duration evidence. The corrective Work is recorded separately at
`work/records/2026/08/finding-blocked-held-display/`.
