# Finding: recent Work changes need a transient attention cue

## Observed

Automatic refresh can update a Work row without moving selection or otherwise
showing the operator which line changed. In a long table the new state is easy
to miss even though refresh itself is working correctly.

The current schema cannot implement an honest age-based cue. Events carry
second-resolution timestamps, Work has no canonical last-change timestamp,
and reconstructing one by scanning event payloads on every refresh would make
the client infer authority history.

## Confirmed direction — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** The most recently
changed visible Work receives a transient animated attention cue while its
canonical change age is below a configurable interval, default 2000
milliseconds. The authority exposes at least a stable change sequence and a
millisecond-precision `last_changed_at`; the TUI calculates current time minus
that timestamp rather than starting a fresh full-duration animation merely
because it observed a row.

The cue is presentation-only and never moves the cursor, changes selection,
restarts on ordinary keystrokes, alters filters, or mutates authority state. A
newer change supersedes the prior cue. Work hidden by the active filter stays
hidden. The exact animation treatment (for example a restrained pulse rather
than terminal blink), the set of acts that update Work recency, and tied
multi-Work changes remain to be ruled with accessibility and terminal
capability in mind.

Persisted per-Work change identity and millisecond time require a schema
revision. This Work is deliberately `parked` until the next schema change; it
has no automatic wake condition and must not widen the current schema-14
iteration.

## Superseded by the live hot-zone cue — 2026-08-16

**Confirmed by Slawomir during the fresh-authority gate. This supersedes the
age-based 2000 ms animation above.** The first trial should instead animate
the Work that is operationally hot, using canonical state already needed for
workflow coordination:

- any open Work with a non-null active claimant;
- any open, `ready=true` Work whose phase is `review`, including the short
  interval before its reviewer claims it.

Blocked (`ready=false`) review Work and waiting, parked, or closed Work do not
animate. The cue is a slow terminal blink and is presentation-only: it never
moves selection, changes filters, marks Messages seen, or mutates authority.
Phase, readiness, Current, and claimant remain the authoritative visible
facts because terminals may ignore blink attributes.

This rule intentionally highlights both sides of the hot zone: claimed Work
that somebody is executing and runnable review Work that somebody needs to
claim. It requires W108's canonical claimant projection but no recency clock,
age calculation, or timestamp-derived client inference. Persisted change
identity may remain useful for other features; it no longer gates this cue.

## Superseded steady animation — 2026-08-16

**Confirmed by Slawomir during the fresh v11 trial. This supersedes indefinite
hot-state blink above, but not the canonical hot predicate or Title emphasis.**
Bold Title and claim Age become the steady hot-zone presentation. Blink is
retained only as the client-local three-scheduled-tick Phase-change cue owned
by `finding-tui-claim-age`; it is no longer continuously derived from active
claim or ready-review state.

## Presentation clarification — 2026-08-16

**Confirmed by Slawomir while auditing the pre-cutover Work.** The slow blink
applies only to the row's phase/status cell (`actve` or `rview`), not to the
whole row. Title, identifiers, counters, routing fields, selection treatment,
and every other cell remain steady. This narrows the presentation rule above;
the canonical definition of hot Work is unchanged.

## Pre-cutover audit — 2026-08-16

**Confirmed by source and live-authority inspection.** No blink treatment is
implemented. W108 now provides the canonical claimant projection required by
the superseding hot-zone design, so the old schema/timestamp reason for
parking no longer applies. The same live Work remains the authority item even
though its historical title says “recently changed”; its current scope is the
active/review hot-zone cue ruled above. The item was moved from `parked` to
`queued` at authority sequence 128. This is a TUI presentation/test change and
must be completed before fresh cutover, not recreated afterward.
