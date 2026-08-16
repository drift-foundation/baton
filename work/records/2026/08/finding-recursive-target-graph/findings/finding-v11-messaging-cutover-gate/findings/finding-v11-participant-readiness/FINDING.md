# Finding: v11 readiness must be participant-relative

## Parent

`finding-v11-messaging-cutover-gate` — this is the first implementation child
of the v10-retirement gate.

## Observed

`projection.wait_actionable()` accepts `viewer_team` only and delegates to the
team-wide `obligations()` projection. It omits ready routed Work and includes
obligations or due rounds whose handlers do not include the waiting member.
The TUI header similarly renders `len(obligations(team))` beside one member's
identity. This contradicts the viewer-relative Work cue and lets an agent miss
its handoff or wake for another member's load.

## Confirmed semantic boundary

Existing operator rules determine readiness; this feature invents no new
message operator:

- `=>`/`pass` transfers Current. An open, ready, unclaimed Work is actionable
  for every member resolved by its Current endpoint; after the atomic claim it
  remains actionable only for that claimant. The stable action identity is the
  Work ID, so claiming does not manufacture a second wake. A restarted monitor
  may rediscover the claimant's still-open Work.
- `@` creates one response or verification obligation. It is actionable only
  for members currently resolved by the obligation's endpoint. Its stable
  action identity is the obligation sequence.
- A due verification round is actionable only for members currently resolved
  by that Work's Current endpoint. Its stable identity includes Work, round and
  deadline generation, so extension retires the old alarm and a later due
  generation is new.
- `+`, plain contextual messages and personal New remain visible attention,
  not actionable wakeups. A sender who needs action uses `@` or passes Current.

One canonical participant-action projection owns these rules. JSON and `wait`
consume it; the TUI's personal obligation/due counters consume the same facts.
The team-wide summary remains team-wide and clearly separate.

## Acceptance

- `wait` passes both viewer team and member and returns a deterministic set of
  structured actions with stable `action_key` values plus `snapshot_seq`.
- Unclaimed routed Work wakes all eligible handlers; one successful claim
  leaves only the claimant actionable without changing its Work action key.
  Another member's claim removes it from every loser.
- Own active Work is rediscoverable after restart; unchanged actions are
  level-triggered facts and are not duplicated by the projection itself.
- Pending `@` and due-round entries are filtered by live route resolution.
  Rerouting changes the eligible participants without rewriting history.
- `+`, plain posts and New-only messages never enter the action set.
- Timeout, concurrent pass/claim/respond, reroute, restart and deadline
  extension races return one coherent snapshot and create no read-side write.
- Wide/narrow TUI coverage proves `oblig`/`due` name the viewer's actionable
  counts, not the whole team's; JSON/TUI parity covers the underlying facts.
- Focused and full v11 gates pass. No authority-schema change is required.
