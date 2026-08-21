# Plan

**Status — 2026-08-21:** independently accepted; awaiting approval and
deployment.

1. [done] Record the observed two-tab-row ambiguity and the confirmed
   breadcrumb-scoped navigation model.
2. [done] Revalidate the current TUI view stack, detail rendering, and
   existing Back/Esc semantics against the confirmed decision.
3. [done] Supersede the narrow Work-detail scope: the same model governs every
   drillable TUI page.
4. [done] Revalidate the shared TUI navigation stack beyond Work detail and
   identify the common implementation boundary.
5. [done] Hide parent/global tab rows after every drill-in, render the
   complete breadcrumb path, expose only the current page's local tabs, and
   make Back/Esc pop one level while preserving view state.
6. [done] Add focused virtual-screen and real-terminal regressions.
7. [done] Review round one: a nested re-root re-appended ancestry, and the
   linked drill-through dropped the far Work's ancestry.
8. [done] Seed only the missing descendant scopes of the same page kind, and
   rebuild the far Work's frames from its own canonical breadcrumb.
9. [done] Review round two: the drilled header suppressed W5's active-filter
   disclosure (`review-2026-08-21T06-58-22Z.md`).
10. [done] Paint `Filter:N` on every breadcrumb header from one shared
    definition, reserve both right-edge units when budgeting the trail, keep
    the normalized-clause line, and add detail/re-root/search/narrow coverage
    (21 cases).
11. [done] Independently review before deployment
    (`review-2026-08-21T07-16-52Z.md`): accepted, with the combined focused
    set passing 73/73 and direct narrow-header verification clean.
12. [pending] Approve and deploy the accepted source change, then perform
    terminal verification against the canonical distribution.
