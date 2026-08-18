# Progress

**Implemented by `baton.claude` and returned to `baton.bug` for independent
review on 2026-08-18.** Presentation only: no authority, projection or schema
change, and no change to when the cue arms or drains.

## Revalidation

Both pinned facts held exactly. `_observe_phases()` still establishes one cold
baseline and arms `phase_blink[work] = 3` only on an observed change;
`_spend_owed_cycle(owed)` still decrements only for a successful scheduled
read, so failed reads, mutation-only refreshes, keystrokes, resizes and cached
redraws already had the ruled semantics. No timer and no authority field were
needed.

W78 is in review but its phase contract is in the tree, so the serial ordering
the finding requires is satisfied — this landed against the current vocabulary,
not a moving one.

## What changed

Three lines of intent, and nothing else:

- `A_BLINK` is composed into the row's BASE attribute while the countdown is
  armed;
- the W81 actionable-Title overpaint already inherited that attribute, so it
  now carries reverse + bold + blink together;
- the Phase-cell blink overpaint is gone.

Composing rather than overpainting is the whole design. It is what makes the
cue survive a layout that drops PHASE, and what lets selection and personal
bold compose with the pulse instead of one replacing another.

## The case that motivated it

The old cue blinked one cell. At widths where the responsive layout omits
PHASE it disappeared completely — so the cue was absent exactly where a row is
hardest to read. `test_the_cue_survives_a_layout_that_drops_phase` asserts the
column is genuinely dropped at its chosen width before checking the row, so it
cannot pass by accident at a width that still keeps PHASE.

## Regressions

`tests/work/test_w105_row_blink.py` (24 tests) works from painted fragments and
their attributes rather than from a screen scrape, so "every visible cell"
is checked literally: every fragment of the changed row blinks — Id, Title,
dependency cue and each retained column — and nothing else on the screen does,
including the header, the footer and the neighbouring row.

Composition: selection composes with the pulse; the actionable Title keeps
reverse, bold AND blink through its second paint; and an unarmed actionable
Title is bold WITHOUT blink, so the composition cannot leak.

Layouts: eight widths from 110 to 44, the PHASE-dropped case, the clipped
visible row as the exact scope, a filtered window, and an indented containment
child.

Arming, unchanged and re-pinned here because this Work must not disturb it:
cold baseline, genuine change, heartbeat-only, steady refresh, an unowed cycle
draining nothing, repainting never draining, and the three-cycle drain.

## Superseded expectation

`test_w336_blink_drain.py` anchored its detection on the blink escape
immediately preceding a phase compact value. The pulse now begins at the row's
Id, so the pattern matches the row instead. Its drain semantics — cold load
clean, armed on change, gone after three scheduled cycles, and not returning —
are untouched; only where the attribute starts moved.

Worth noting: that pattern also still listed `rview` and `rsrch`, phases W38
removed, so it had been partly dead for some time.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Back to the Phase-cell-only overpaint | 14 red |
| The Title overpaint drops the composed attribute | 13 red |
| Painting the table spends the countdown | 1 red |

## Gate

`just test-v11`: **1690 passed**, serial **38 passed**, ACP **41/41**.
