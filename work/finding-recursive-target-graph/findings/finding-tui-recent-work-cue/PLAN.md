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
