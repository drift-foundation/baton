# Finding: Work State is redundant in the default list

## Status

UX simplification proposed by Slawomir during the projection-11 v11 trial on
2026-08-18.

## Observed

The normal Work list hides terminal rows. Every row in view therefore has
canonical `status: open`, yet each repeats that invariant in the `St` column.
The column consumes scarce horizontal space without helping an operator
distinguish any two visible rows. Closed outcomes—including rejection—remain
hidden until the operator deliberately reveals or filters for them.

## Confirmed decision — approved 2026-08-18

- Remove `St` from the normal open-only Work table. Keep canonical `status` in
  JSON, filtering, detail, and Events; this is presentation simplification,
  not a data-model change.
- When a view can contain terminal Work—closed rows revealed with `z`, or a
  closed-status filter—show terminal **Outcome**, not the redundant word
  `closed`. Open rows in a mixed view show `-` for Outcome.
- Do not overload Phase with terminal outcome. Phase remains the open Work
  scheduler axis and terminal Work continues to have no phase.
- Detail continues to state lifecycle and outcome explicitly.

Use one compact `Out` column with these TUI spellings:

- `sat` — satisfying;
- `nsat` — non-satisfying;
- `rej` — rejected;
- `cancl` — cancelled;
- `-` — no outcome because the Work remains open.

Detail and JSON retain the full canonical outcome spellings. `rejected` and
`non-satisfying` are outcomes of closed Work, never lifecycle states.

## Acceptance boundary

- Default open-only views contain no status column or repeated `open` cells.
- Revealed/filtered terminal rows make satisfying, non-satisfying, rejected,
  and cancelled outcomes distinguishable without conflating them with Phase.
- Narrow-width drop order remains deterministic and preserves Id/Title before
  optional terminal outcome.
- `z`, filters, containment, selection, resize, and JSON/TUI parity retain
  their current lifecycle semantics.
- Focused screen and real-terminal tests cover open-only, mixed, closed-only,
  narrow, and resized views.
