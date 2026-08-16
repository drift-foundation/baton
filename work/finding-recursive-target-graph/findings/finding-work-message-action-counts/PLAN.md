# Plan

1. Revalidate exact Work/descendant/Thread overlap semantics, obligation route
   eligibility, withdrawal/response transitions, list pagination, and existing
   recursive `New` behavior.
2. Add canonical, viewer-relative `message_count` and
   `my_pending_obligations` projections using distinct-message and pending-`@`
   semantics; do not persist redundant counters or mutate seen state.
3. Render `Msg/My` as `<total>/<mine>` while retaining separate `New` and all
   responsive identity/workflow columns.
4. Add own/descendant/shared-Thread overlap, multiple Threads, unrelated
   messages, `@`/`+`/transfer distinctions, multi-handler resolution,
   withdrawal, answer-increments-total, restart/rebuild, JSON/TUI parity,
   narrow-screen, and read-purity regressions.
5. Run focused coverage and `just test-v11`, then return for review before the
   next immutable release.
