# Plan

**Status:** parked until the next schema revision.

1. Rule relevant change acts, tie behavior, animation/accessibility treatment
   and configuration placement/bounds.
2. Add atomic per-Work `last_changed_seq` and millisecond
   `last_changed_at` state in the next fresh schema; never derive authority by
   client event-payload scans.
3. Project the canonical values through all Work-list JSON surfaces.
4. Animate only for the remaining portion of the configured age window
   (default 2000 ms), without moving selection or restarting on keystrokes.
5. Cover multiple writers, linked/multi-labelled messages, clock boundaries,
   delayed client startup, refresh coalescing, filters, narrow terminals,
   restart/rebuild and JSON/TUI parity.
6. Run focused and full v11 gates against the fresh authority before review.

## Superseding plan — 2026-08-16

**Status — 2026-08-16:** W108 is complete; verified unimplemented and queued
for the pre-cutover cleanup batch. The timestamp-age design above is no longer
implementation scope. The live authority item was moved from `parked` to
`queued` at sequence 128.

1. Derive `hot` only from canonical row state: active claimant present, or
   `phase=review && ready=true`, while status is open.
2. Apply restrained slow blink only to the phase/status cell of a hot Work row
   (`actve` or `rview`) without changing selection or layout; every other cell
   remains steady, and ordinary textual state remains when blink is ignored.
3. Prove claimed research/implementation/review Work, ready unclaimed review,
   blocked review, waiting, parked, terminal, narrow-screen, refresh, and
   multiple simultaneously hot rows.
4. Verify the cue needs no timestamp/age read and performs no authority write,
   then run packaged TUI and full v11 gates.
5. Remove W84 from the fresh-authority recreation inventory and update its
   counts/proof after verification.

## Sign-off — 2026-08-16

Complete and accepted in `review-2026-08-16T13-43-54Z.md`. The canonical
hot-state predicate, phase-cell-only blink, selection composition, cold and
narrow states, presentation purity, and recreation removal are all verified.
W84 may close satisfying and is not recreated in the fresh authority.
