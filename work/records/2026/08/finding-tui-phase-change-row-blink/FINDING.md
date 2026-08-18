# Finding: phase-change attention should cover the Work row

## Observed

The deployed v11 TUI's short phase-change blink is useful: it briefly draws
attention to Work whose scheduler state changed. It currently applies only to
the Phase cell, making the cue easy to miss while scanning Titles or narrow
layouts.

## Confirmed decision — 2026-08-18

Retain the existing client-local, short-duration phase-change pulse and extend
its blink attribute across the complete visible Work row. This changes only
presentation: the canonical phase, handler, Held, readiness, and Work event
facts remain unchanged.

The first loaded snapshot still establishes a cold baseline. Only a genuine
subsequent phase change arms the pulse, and it still drains after the existing
bounded scheduled-refresh count. Selection, personal bold, and other row
attributes compose with the pulse rather than being replaced by it. Terminals
that ignore blink remain fully usable from textual state.

## Acceptance

- A phase change blinks every visible cell belonging to that Work row,
  including layouts where the Phase column is dropped.
- The initial load, heartbeat-only changes, ordinary keystrokes, failed reads,
  and steady-state refreshes do not arm or prolong the cue.
- The pulse drains after the same existing three successful scheduled refresh
  cycles.
- Row selection and personal-action emphasis remain visible and semantically
  unchanged.

## Implementation revalidation — 2026-08-18

**Confirmed current-code facts.** `Console._observe_phases()` still establishes
one cold baseline and arms `phase_blink[work_id] = 3` only after an observed
phase change. `_spend_owed_cycle()` still decrements that state only after a
successful scheduled canonical read. Failed reads, mutation-only refreshes,
keystrokes, resizes, and cached redraws therefore already have the ruled
countdown semantics and do not need a new timer or authority field.

The remaining presentation boundary is narrow. `_render_table()` paints the
complete visible row with its selection attribute, then separately overpaints
the actionable Title with bold and the Phase cell with blink. Compose
`A_BLINK` into the base row attribute while the row's existing countdown is
armed; the Title overpaint must inherit that composed attribute plus `A_BOLD`.
Remove the Phase-only blink overpaint. This makes the cue survive responsive
layouts that omit Phase and keeps the clipped visible row, not off-screen
columns, as the exact painted scope.

W78 changes the scheduler phase vocabulary and the same TUI/test surfaces.
Implement these serially: W105 must land against W78's current phase contract,
not concurrently against a moving `app.py` or phase regression suite.

## Revalidated acceptance boundary

- Model rendering proves every painted fragment of the changed Work row
  carries blink, including Id, Title, dependency cue, and every retained
  column; no neighboring row, header, or footer does.
- A selected changed row composes reverse+blink, and actionable Title composes
  reverse when selected plus bold+blink without losing any attribute.
- Narrow layouts that omit Phase still blink the complete visible row.
- Cold load/reconnect, heartbeat-only mutation, ordinary keystrokes, resize,
  mutation refresh, failed scheduled refresh, and steady scheduled refresh do
  not arm or prolong the cue.
- Main, re-rooted, and search tables consume the same three successful
  scheduled cycles; real-PTY evidence proves the row pulse appears and drains.
