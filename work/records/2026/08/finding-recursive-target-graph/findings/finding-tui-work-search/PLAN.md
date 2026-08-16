# Plan

**Status — 2026-08-16:** implementation-ready after fresh-authority
revalidation; reviewer research is active and ready for the next serial
implementer handoff.

1. Add a read-only, viewer-team-scoped canonical `search query=...` projection
   over Work title and canonical/local identifiers. Apply the existing Work
   filter semantics, closed visibility, a stable continuation cursor and one
   snapshot token; expose it through JSON.
2. Add `/` query entry and a flat TUI search-result mode. Query only on Enter,
   reuse the ordinary refresh/cache path, anchor by Work ID, and restore the
   exact prior table state on Esc.
3. Keep Work detail unchanged: Enter on a result opens it, and leaving detail
   returns to the search results. Name all navigation in the footer.
4. Cover empty/refused, no-match, exact/full/local/prefix and case-folded title
   matches, nonmatching fields, filters, closed visibility, nested Work,
   paging, timer refresh races, stable selection, narrow terminals and
   read-only/seen-state invariants. Break-sweep against per-keystroke reads and
   current-window-only matching.
5. Run focused JSON/TUI parity and PTY coverage plus `just test-v11`; return
   for independent review before the next trial deployment.
