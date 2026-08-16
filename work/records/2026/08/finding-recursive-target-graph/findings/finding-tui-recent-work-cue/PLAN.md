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

**Status:** queued after W108 claimant projection; the timestamp-age design
above is no longer implementation scope.

1. Derive `hot` only from canonical row state: active claimant present, or
   `phase=review && ready=true`, while status is open.
2. Apply restrained slow blink to the whole hot Work row without changing
   selection or layout; retain ordinary textual state when blink is ignored.
3. Prove claimed research/implementation/review Work, ready unclaimed review,
   blocked review, waiting, parked, terminal, narrow-screen, refresh, and
   multiple simultaneously hot rows.
4. Verify the cue needs no timestamp/age read and performs no authority write,
   then run packaged TUI and full v11 gates.
