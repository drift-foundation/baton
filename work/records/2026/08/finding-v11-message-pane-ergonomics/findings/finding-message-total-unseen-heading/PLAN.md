# Plan

**Status — independently signed off on 2026-08-18.**
See `review-2026-08-18T13-58-15Z.md`.

**Original status:** handed to `baton.impl` as W29 on 2026-08-18. It returns to
`baton.bug` for independent review. Additive projection/TUI work; no database
schema change.

1. [done] Add a snapshot-consistent whole-Topic Message total beside the existing
   whole-Topic personal `new` count in the canonical Topic read.
2. [done] Render `Messages (total/unseen)` from those two facts, never from the page
   array.
3. [done] Add JSON and wide/narrow TUI regressions for zero, one, exact-limit,
   multi-page, partly seen, fully seen, paging, and explicit mark-seen.
4. [done] Prove page size and navigation do not change either count absent an
   authority mutation.
