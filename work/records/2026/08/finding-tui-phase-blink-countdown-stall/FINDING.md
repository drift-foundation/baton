# Finding: phase-change blink countdown stalls in the main Work table

## Observed — 2026-08-17

After Work W24 automatically woke from `waiting` to `queued`, its `queue`
Phase cell continued blinking for hours in the deployed v11 TUI instead of
stopping after the ruled three scheduled refresh cycles.

The authority behaved correctly. Events 315–316 closed the final contained
Work and recorded W24's `waiting` to `queued` wake. W24 is open, unclaimed,
ready, and queued; the persistent animation is client-local presentation.

## Confirmed cause

`Console.render()` obtains the main table through `self.view()`. The scheduled
phase-blink countdown and phase observation, however, live in `Console.rows()`.
The timer calls `tick()` and then `render()`, so the table's direct `view()`
read consumes the refresh request without executing the countdown in `rows()`.
A later interaction can observe and arm a real Phase change, but subsequent
timer paints never drain it.

The deployed `38f52ed` artifact and current source both contain this split.
Restarting the TUI clears the ephemeral blink map, but that is only a
workaround and the next observed Phase change can reproduce the defect.

## Related record

The intended three-refresh contract is owned by:

```text
work/records/2026/08/finding-recursive-target-graph/findings/finding-tui-claim-age/
```

This independent record captures the live defect because it is separately
scheduled for the pre-cutover v11 rerelease.

## Acceptance boundary

- The first loaded table remains cold.
- A genuine observed Phase change arms only that row's Phase cell.
- Each successful scheduled canonical refresh consumes exactly one cycle,
  including the ordinary full `render()` path used by the live TUI.
- The cue is absent after exactly three successful scheduled refreshes.
- Keystrokes, redraws, resize, navigation, and mutation-only refreshes neither
  consume nor restart the countdown.
- Failed scheduled reads consume nothing.
- Search and re-rooted Work tables obey the same rule without duplicating
  authority reads or changing cursor/selection state.
- A PTY regression drives the real timer/render loop far enough to prove that
  the blink attribute disappears; a model-only `_render_table()` test is not
  sufficient evidence.

