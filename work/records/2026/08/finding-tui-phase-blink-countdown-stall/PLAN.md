# Plan

**Status:** W336 independently reviewed and signed off 2026-08-17; ready to
close satisfying and include in the pre-cutover v11 rerelease.

1. Revalidate the ruled W33 phase-change cue against the current one-refresh
   scheduler and all full-render modes.
2. Make the main and search table render paths pass through one countdown and
   observation boundary without adding authority reads.
3. Preserve cold-load, failed-read, mutation-only refresh, selection, cache,
   and navigation behavior.
4. Add focused unit coverage plus a real PTY timer/render regression that
   proves the Phase cell loses `A_BLINK` after three successful cycles.
5. Run focused regressions and the complete v11 gate, then return for
   independent review before rerelease.
