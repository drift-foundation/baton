# Plan

1. [done] Revalidate the Inbox entry and Back paths against the shared bounded
   navigation stack and identify the superseded W292 exception.
2. [done] In `Console._handle_inbox`, follow `_handle_teams`: pass one
   explicit restore frame carrying `_nav_capture()`, `tab="inbox"`,
   `inbox_cursor`, and `inbox_key` into `_enter_detail`, then use Jobs only as
   the live Work-detail handler. Do not change shared push/pop or breadcrumb
   construction.
3. [partly done — two items named in PROGRESS] Replace the superseded W292 exception with obligation/message
   restoration cases; add stable-key reanchoring after row insertion, derived
   scroll restoration, deeper-drill unwind, bounded-history caller retention,
   and PTY bare-Esc/decoded-Left coverage. Preserve poke no-op, fresh detail
   focus, Teams/search/Jobs/graph/poke/Awaiting-me and breadcrumb-focus suites.
4. [done except the PTY flow] Update `docs/BATON-WORK.md:166-172`, run the focused W25, W292,
   W2597, W26331, W29146 and W6814 navigation suites plus real-terminal tests,
   prove authority sequence and seen cursors unchanged, and return for
   independent review.

## Independent review — 2026-08-28

3. [done] Reviewer-added regressions cover actual refreshed row insertion and
   stable-key reanchoring, the cursor-derived window, bounded-history caller
   retention and the previously missing PTY path.
4. [changes requested] 154 focused navigation tests pass and scoped diff check
   is clean. Correct the one stale Inbox-to-Jobs Back rule in the Teams-handler
   production comment, then return for final review.

## Independent re-review — 2026-08-28

4. [done] The stale rule is corrected, the three reviewer cases pass again,
   scoped diff checking is clean, and W34884 is signed off satisfying.
