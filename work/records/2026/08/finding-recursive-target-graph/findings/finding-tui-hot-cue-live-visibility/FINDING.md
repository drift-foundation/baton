# Finding: the hot-zone cue is not visible in the live terminal

## Observed — 2026-08-16

In the fresh projection-4.1 authority, W2 was visibly `active`, claimed by
`baton.claude`, and routed through `baton.impl`. Slawomir's real v11 TUI showed
the correct textual row but no visible blink in the phase cell.

This is a new acceptance failure after completed W84; W84 is not reopened.
The prior implementation remains useful history and is linked by this
regression.

## Confirmed

`src/baton_work/tui/app.py` applies `curses.A_BLINK` only to the phase cell for
rows selected by `hot_work()`. `tests/work/test_w84_hot_cue.py` proves that a
PTY transcript contains the terminal blink escape attribute immediately
before `actve` and `rview`. That test proves emission, not that a real terminal
renders the attribute visibly.

Terminal blink may be disabled, ignored, or rendered without an observable
animation. The ruled purpose is a visible hot-zone cue for what is happening
now; emitting an optional escape attribute without a visible result does not
satisfy that UX purpose.

## Boundary

- Preserve the canonical hot predicate: claimed open Work and ready unclaimed
  review Work are hot; blocked, waiting, parked, queued-unclaimed, and terminal
  Work remain cold.
- Preserve the phase-cell-only scope; do not animate or restyle the whole row.
- Do not infer workflow state from presentation or mutate authority state.
- Determine a restrained cue that is visibly reliable in the supported live
  terminal while retaining readable steady text.
- Cover both emitted terminal behavior and an operator-visible acceptance path;
  an escape-stream assertion alone is insufficient evidence of visibility.

The exact replacement or fallback treatment remains a review decision after
focused terminal investigation. No implementation is authorized by this
observation alone.

## Disposition — 2026-08-16

Shortly after the initial report, Slawomir confirmed that the same live W2
phase cell did begin blinking. The terminal therefore renders the emitted
slow-blink attribute; the first observation occurred before its visible
cadence made the state apparent.

The reported failure is not reproducible and no product change is warranted.
This record remains as evidence of the acceptance check; no v11 Work was
created and completed W84 remains authoritative.

## Superseding ruling — 2026-08-16: bold Title is the reliable cue

**The no-change disposition above is superseded.** Slawomir subsequently
confirmed that blink is not reliable enough on the live terminal to carry the
hot-zone signal by itself. Its delayed or absent rendering makes current work
too easy to miss even though Baton emits the correct terminal attribute.

Preserve the existing hot predicate exactly: claimed open Work and ready,
unclaimed review Work are hot; blocked review, waiting, parked, queued,
unclaimed non-review, and terminal Work are cold. For every hot row:

- retain the slow blink on the phase cell as an optional attention cue;
- render the Title cell bold as the reliable steady cue;
- do not bold or animate the rest of the row.

Selection/highlight attributes must compose with bold Title rather than erase
it. Terminals that ignore blink must still present the same hot rows clearly
through bold titles. No authority state or schema changes are involved.

## Superseding final treatment — 2026-08-16: bold Title plus claim Age

**The instruction above to retain slow blink indefinitely is superseded.**
Slawomir ruled that once the claim-age column lands, bold Title plus the live
claim timer is sufficient and more reliable than terminal animation.

Sequence the correction so there is no visibility gap:

1. W23 adds bold Title for the canonical hot predicate while existing blink
   remains available.
2. W33 adds claim `Age` and removes `curses.A_BLINK` from Work rows in the same
   reviewed change.

The final state is therefore: hot rows have bold Title; claimed rows also show
their age; ready unclaimed review remains bold with `Age` rendered `-`; no Work
cell blinks. Do not weaken or duplicate the canonical hot predicate.

## Narrow supersession — 2026-08-16: short Phase-change blink remains

**The “no Work cell blinks” sentence immediately above is superseded.** W33
still removes blink as an indefinite hot-state treatment. It retains only the
separately approved client-local Phase-cell blink for three scheduled refresh
ticks after an observed genuine Phase change. Initial load is cold and
keystrokes/redraws/immediate refreshes do not consume or restart that cue.

Bold Title plus claim Age remain the steady hot-zone treatment. The short
change cue is not derived from `hot_work`, does not weaken W23, and carries no
authority or schema state.

## Superseding ruling — 2026-08-16: bold is personal actionability

**The global hot-zone use of bold Title above is superseded.** Slawomir's live
approval handoff exposed that a ready Work assigned to him through Current was
not visually distinct unless he scanned the Current column. At the same time,
bold titles for Work being handled by somebody else competed with the stronger
question an operator must answer first: “what am I supposed to handle?”

Bold Title is therefore reserved for Work actionable by the current viewer:

- the viewer holds its active claim;
- the Work is open, ready and unclaimed, and its Current endpoint resolves to
  the viewer; or
- the viewer has an unresolved directed `@` obligation on the Work.

For a multi-handler Current endpoint, every eligible handler sees the ready,
unclaimed Work as actionable until one handler claims it. After a successful
claim, only the claimant retains the bold execution cue. Dependency-blocked,
waiting, parked and terminal Work is not bold merely because its Current still
names the viewer; an `@` response obligation remains independently actionable.

Other participants' activity remains visible through Phase, Current and claim
Age. The separately approved three-scheduled-tick Phase-cell blink remains a
brief observed-change cue, not an ownership cue. This is a viewer-relative
projection/presentation correction; it must not mutate authority state or
change who is authorized to act.
