# Finding: Work rows need a visible claim-age timer

## Confirmed direction — 2026-08-16

**Confirmed by Slawomir during the fresh v11 trial.** Active implementation
and review claims need a visible age so the team can tell whether current work
has just started or may be stalled. Add a final `Age` column to Work tables.

The value measures elapsed time since the current participant claim committed,
not time since the Work entered its phase and not time since its last message.
A handoff followed by a new claim resets the timer. Release, an unclaimed
review phase, and terminal Work render `-`.

Use one fixed five-cell value that scales without changing table alignment:

- below one hour: `MM:SS`;
- from one hour through 99 hours: `HH:MM`;
- beyond the display range: `99h+`;
- no current claim: `-`.

The TUI advances the display on its existing automatic refresh cadence
(default two seconds); the timer must not create a second scheduler or trigger
extra authority polling. The canonical JSON projection exposes the committed
claim timestamp (`claimed_at`), not a continuously changing client-derived age.
The TUI derives the presentation from that timestamp and its local current
time. Negative elapsed values caused by clock correction clamp to zero.

The claim timestamp already exists in the append-only claim event, so this is
same-schema work. Implementation must project it without inventing a second
claim authority or trusting `last_changed_at`, which can move for unrelated
Work activity. A projection-version increment may be required for the added
JSON fact, but no fresh database is required.

At narrow widths, `Age` is omitted as one whole responsive column. It is never
truncated or allowed to consume Title space below the table's minimum.

## Final hot-zone composition — 2026-08-16

**Confirmed by Slawomir after the timer format ruling.** W33 removes the
existing phase-cell blink in the same change that introduces `Age`. The final
steady presentation is bold Title for the canonical hot predicate plus claim
age where a claimant exists. Ready unclaimed review remains bold and shows
`-`; cold Work remains steady.

W33 depends on W23 so blink is never removed before bold Title exists.

## Phase-change blink refinement — 2026-08-16

**Confirmed by Slawomir; this narrowly supersedes removing all phase-cell
blink above.** W33 removes the indefinite blink derived from hot Work state,
but retains a short client-local blink when a refresh observes that a Work's
Phase value changed.

The first loaded snapshot establishes the baseline and blinks nothing. A
subsequent genuine Phase change arms blink on that row's Phase cell for three
scheduled refresh ticks—approximately six seconds at the default two-second
cadence. Keystrokes, redraws, resize, and immediate mutation-triggered
refreshes neither consume nor restart the countdown. A later genuine Phase
change restarts it. Only successful scheduled refresh ticks consume it.

This attention state is deliberately ephemeral and presentation-only. It is
not persisted, reconnecting starts cold, and it neither reads nor requires a
high-resolution authority timestamp. Bold Title plus claim `Age` remain the
steady hot-work indicators after the short change cue expires.
