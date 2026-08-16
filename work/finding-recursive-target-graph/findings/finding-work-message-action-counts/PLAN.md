# Plan

**Status — 2026-08-16:** completed and closed satisfying as v11 W36. The
round-two review is signed off in `review-2026-08-16T04-05-27Z.md`; focused
coverage reports 15 passed. The implementation preserves SQLite schema 14 and
advances the canonical projection to 3.2. The full `just test-v11` remains the
release gate.

1. [done] Revalidate exact Work/descendant/Thread overlap semantics, obligation route
   eligibility, withdrawal/response transitions, list pagination, and existing
   recursive `New` behavior.
2. [done] Add canonical, viewer-relative `message_count` and
   `my_pending_obligations` projections using distinct-message and pending-`@`
   semantics; do not persist redundant counters or mutate seen state.
3. [done] Render `Msg/My` as `<total>/<mine>` while retaining separate `New` and all
   responsive identity/workflow columns.
4. [done] Add own/descendant/shared-Thread overlap, multiple Threads, unrelated
   messages, `@`/`+`/transfer distinctions, multi-handler resolution,
   withdrawal, answer-increments-total, restart/rebuild, JSON/TUI parity,
   narrow-screen, and read-purity regressions.
5. [done for focused review] Run focused coverage and return for review. The
   complete `just test-v11` remains due at the immutable release gate.
