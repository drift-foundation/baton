# Plan

**Status — signed off by `baton.codex` on 2026-08-18.** All five steps are
done; see `review-2026-08-18T19-31-19Z.md` for the independent review.

**Prior status — implementation-ready 2026-08-18 as W49.** W48 closed satisfying;
the fixed-column contract was revalidated against the current detail panes and
the configured six-cell identity grammar.

1. [done] Revalidated configured identity widths and the wide/narrow Message
   layouts after the Event children landed.
2. [done] Replace the free-form Message index row with the page-stable,
   responsive columns and compact headings pinned in `FINDING.md`.
3. [done] Preserve selection/new attributes and bounded newest-first paging
   exactly; keep W228's later action cue outside this patch.
4. [done] Cover short/maximum handles, decimal growth of Message ids,
   stable offsets, whole-column wide/narrow omission, empty/exact/overflow
   pages, focus, selection, resize, and seen state.
5. [done] Run focused TUI tests and `just test-v11`, then return for
   independent review.
