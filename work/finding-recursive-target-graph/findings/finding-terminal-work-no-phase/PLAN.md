# Plan

**Status — 2026-08-16:** completed and review-clean as W77; see
`review-2026-08-16T04-27-05Z.md`. The focused gate reports 15 passed and the
change preserves SQLite schema 14.

1. [done] Revalidate close storage, audit, projection, JSON-schema and TUI paths at
   SQLite schema 14.
2. [done] Project `phase: null` for every closed Work while preserving the required
   canonical phase for open Work and the recorded transition history.
3. [done] Render closed Phase as `-`; never expose the stale final open phase or
   invent `done`.
4. [done] Cover every terminal outcome, open/closed list and detail parity, restart,
   event-history preservation, narrow rendering and refusal of phase changes
   after closure.
5. [done for focused review] Run focused coverage and return for review. The
   complete `just test-v11` remains due at the final batch gate.
