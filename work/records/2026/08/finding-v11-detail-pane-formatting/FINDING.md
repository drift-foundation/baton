# Finding: the v11 detail indexes and Event payload are visually unstable

## Observed

The projection-9 TUI concatenates Event and Message index fields into free-form
strings. Variable Event kinds and participant names therefore move later
fields from row to row, making both indexes feel floaty rather than tabular.
The Event reader appends the complete payload as one sorted JSON line and then
terminal-wraps it, so nested payloads are difficult to scan. Claim duration is
available, but the Events play-by-play does not say how long each scheduler
phase episode lasted.

## Confirmed decisions — 2026-08-18

**Confirmed by Slawomir during the live projection-9 trial.** This is one
presentation track with three independently reviewable children:

1. The Event index uses stable fixed-width columns and shows the elapsed time
   of scheduler-phase episodes as `MM:SS`.
2. The Event reader renders the complete payload as two-space-indented JSON.
3. The Message index uses stable fixed-width columns as well.

Fixed-column means every visible field starts at the same cell in every row.
At narrower widths, a whole lower-priority column may be omitted according to
one deterministic responsive layout; values never make neighboring columns
drift. The index and selected-row attributes, newest-first order, paging,
pane navigation, focus cues, Message seen state, and event completeness remain
unchanged.

The children are:

- `findings/finding-event-index-phase-duration/`
- `findings/finding-event-payload-pretty-json/`
- `findings/finding-message-index-fixed-columns/`

This is an additive projection and TUI refinement. It does not require a new
persisted-authority schema or a fresh coordination home.
