# Plan

**Status — focused implementation is clean, but review is blocked on expanded
W101.** See `review-2026-08-18T15-35-04Z.md`. Do not churn the same launcher
documentation concurrently; revalidate explicit role-selection wording after
W101 closes, then return for final review.

1. [done] Rewrite
   `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` around the standalone
   app-server, generic dispatcher, and independently launched v11 readiness
   producers, preserving the multi-target isolation and safety design.
2. [done] Rewrite `tools/codex-event-bridge/README.md` as a runnable
   post-v10 operator sequence while preserving W101 role-instruction setup.
3. [done] Add both documents to the active v11 documentation regression,
   validate the checked-in bridge example through the real config validator,
   and run focused docs plus bridge tests.
4. [done] Return W6 to `baton.feat` for independent review; the parent W5
   remains open until this child closes.
5. [pending; blocked on W101] Re-read the final complete-role launcher
   contract, remove any implication that a sole role may be inferred, rerun
   the focused documentation/bridge gates, and return for final review.
