# Plan

**Status — signed off 2026-08-18.** W47, W48, and W49 are independently
reviewed and closed satisfying; the umbrella acceptance is complete. See
`review-2026-08-18T19-53-56Z.md`.

1. [done] Add canonical scheduler-phase intervals and the fixed-column Event index.
2. [done] Pretty-print the complete Event payload with two-space JSON indentation.
3. [done] Convert the Message index to fixed columns without changing seen or paging
   semantics.
4. [done] Verify wide, narrow, empty, exact-page, overflow-page, resize, focus,
   newest-first, open-phase, completed-phase, and duration-overflow cases.
5. [done] Run the focused projection/TUI tests and `just test-v11`, then return the
   track for independent review.
