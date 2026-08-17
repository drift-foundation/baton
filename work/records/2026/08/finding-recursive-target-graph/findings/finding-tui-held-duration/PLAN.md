# Plan

**Status:** implementation-ready as W226; queued behind W202 after reviewer
revalidation on 2026-08-17. Its approved scope includes structured pending
pickup state and is no longer presentation-only.

## Revalidation — 2026-08-17

- The current renderer still labels the field `Age`, switches from `MM:SS` to
  `HH:MM` at one hour, derives it only from `claimed_at`, and displays `-`
  between pass and pickup. The defect remains live.
- Canonical projections expose only `claimed_at` and `heartbeat_at`; they do
  not expose the committed handoff instant or structured pending-pickup and
  overdue-pickup facts required by the superseding ruling.
- The pass event already records the destination phase and committed event
  time. Extend the ordinary batched projection from authoritative events;
  do not add a TUI-side authority read, infer handoff from `last_changed_at`,
  or encode `>`/`!` in JSON.
- This changes the canonical JSON projection contract and therefore requires
  an honest projection-version bump and a fresh trial authority. It does not
  require a new workflow mutation or an automatic timeout transition.

1. Revalidate the current `age_cell`, `age_field`, Work-table column metadata,
   responsive layout and W33/W47 tests against the current tree.
2. Expose structured handoff-held and pickup/claim facts in canonical JSON;
   glyphs remain a TUI-only projection.
3. Rename the compact TUI header from `Age` to `Held`. Before pickup, render
   floored `HH:MM` from the handoff instant with the pending prefix; on claim,
   reset the displayed interval to canonical `claimed_at`. Render through
   `99:59`, retaining `99h+` and the negative-clock clamp in both states.
4. Prefix an unclaimed operational destination Phase with `>`, replacing it
   with `!` after six minutes. Claim removes the pickup prefix and starts the
   claim-held display; no timeout mutates workflow authority. The existing
   trailing heartbeat `!` remains claimant-only and does not reset that timer.
5. Update focused authority, projection, renderer, refresh, heartbeat and
   packaged-TUI tests, including pass-before-claim, overdue pickup, the visible
   reset at claim, heartbeat without reset, repass, terminal and structured-
   JSON/no-glyph boundaries.
6. Run focused tests and `just test-v11`, then return for independent review.

## Follow-up — 2026-08-17

The completed W226 authority/pickup work remains historical. The confirmed
presentation follow-up in
`findings/finding-held-mmss-overflow/{FINDING,PLAN}.md` supersedes only the
timer scale: `MM:SS` through `99:59`, then `∞`. It requires no schema or JSON
projection change.

After that overlapping formatter change, implement
`findings/finding-unclaimed-work-cue/{FINDING,PLAN}.md`: unclaimed `>` is the
primary state cue; elapsed pickup and heartbeat `!` alerts are removed, and
blocked/waiting/parked Work never projects an overdue pickup obligation.
