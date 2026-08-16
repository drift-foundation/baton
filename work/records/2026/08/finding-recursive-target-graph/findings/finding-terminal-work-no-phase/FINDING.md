# Finding: closed Work incorrectly retains an operational phase

## Observed

The second v11 trial displays closed satisfying Work as `c/sat` while its
Phase column still says `queue`. The authority currently preserves the final
open phase on closure. Although status/outcome and phase were designed as
separate axes, `queue` visibly implies remaining work and contradicts the
terminal disposition.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the live v11 trial.** Phase applies only while
Work is open:

- open Work exposes exactly one non-null canonical phase;
- closed Work exposes `phase: null` in canonical JSON and `-` in the TUI;
- no redundant `done` phase is introduced;
- audit/event history preserves the final open phase and close transition.

This explicitly and narrowly supersedes the earlier globally non-null phase
wording. `null` here means “not applicable,” not “unknown.” Omitting the JSON
field would make the canonical shape conditional and is therefore rejected.

The change is a same-schema projection and presentation correction. It must
not rewrite stored history or the existing authority merely to erase the
internal last-phase value.
