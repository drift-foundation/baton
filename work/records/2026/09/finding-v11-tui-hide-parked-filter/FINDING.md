# Finding: V11 Jobs need a quick way to hide parked Work

Ledger Work: W103596

## Observation — 2026-09-06

The Jobs view now contains enough deliberately parked Work that active and
actionable Work is difficult to scan. The existing `:filter` command is an
expert command-entry surface and its inclusive filter grammar does not provide
the requested quick "hide parked" interaction.

## Confirmed decision — 2026-09-06

The v11 TUI gains an extensible, client-local filter chooser on the Jobs view.

1. `f` opens the chooser. Its first option is `[p] Parked`.
2. `p` toggles whether parked Work is hidden. Repeating `f`, then `p`, restores
   parked Work. `Esc` dismisses the chooser without changing the view.
3. The default remains unchanged: parked Work is visible until the operator
   enables this filter.
4. The active state is visibly disclosed; an operator must not unknowingly act
   from a reduced Jobs view.
5. This is transient TUI state. It is not persisted, written to SQLite, added
   to protocol vocabulary, or applied to machine readiness and scheduling.
6. The chooser is a small extension point for later hide/show options. This
   Work implements only the parked toggle and does not speculate about future
   filters.
7. Filtering removes parked Work from the selectable Jobs rows while it is
   enabled. Refresh, navigation, and selection remain deterministic when the
   selected row disappears, and disabling the filter restores the stable
   structural ordering established by W103313.
8. Search, Inbox, Teams, Work detail, dependency pages, and command-mode
   `:filter` retain their current contracts unless a minimal shared disclosure
   correction is required to keep the active quick filter visible.

## Acceptance boundary

- From the Jobs table, `f`, `p` hides every row whose phase is `parked`.
- `f`, `p` again restores those rows in their stable display positions.
- `f`, `Esc` changes nothing.
- The chooser and active filter state are legible in the TUI.
- A parked selected row cannot leave the cursor or selected identity pointing
  at an invisible Work.
- Authority projections, readiness order, persisted state, and JSON command
  behavior are unchanged.
- Focused TUI regressions cover activation, reversal, cancellation, refresh,
  selection repair, and coexistence with the existing closed-Work toggle.

## Independent review — 2026-09-06

**Confirmed:** the two-path candidate implements the recorded chooser contract
as client-local TUI state. The Jobs table alone opens the chooser with `f`;
`p` hides or restores parked rows, `Esc` cancels, and the header and chooser
disclose the active reduction. Selection is repaired by stable Work identity or
by a bounded cursor fallback after filtering and refresh. The existing closed
toggle composes with the parked reduction, and neither the implementation nor
its regressions advance authority state.

The independently recomputed candidate digests are:

- `src/baton_work/tui/app.py`:
  `c3b917ec467f01dc3bc1dc8566274f405d5c3b993b407effd1c133907b387872`
- `tests/work/test_tui.py`:
  `acc328ad0bd341b9214ca107f697c396885ab273c77308115e2629c4bbd4faf3`

**Verified:** all 33 focused TUI tests passed. The complete v11 gate passed its
3,341 primary tests, 54 adversarial terminal tests, and 129 ACP bridge tests.
Both candidate paths compile, and diff/check hygiene is clean. No review
finding remains.
