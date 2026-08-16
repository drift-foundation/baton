# Plan

**Status — 2026-08-16:** completed and review-clean as W74; see
`review-2026-08-16T04-33-25Z.md`. The focused PTY gate reports 21 passed and
the change preserves SQLite schema 14.

1. [done] Revalidate the root and drilled header paths against the current TUI.
2. [done] Remove only the redundant `— top-level work` root-view suffix; preserve the
   participant identity, live summary, and drilled breadcrumbs.
3. [done] Update root/drill rendering tests, including a narrow terminal assertion.
4. [done] Run focused TUI coverage and return for review without interrupting the
   active serial item.
