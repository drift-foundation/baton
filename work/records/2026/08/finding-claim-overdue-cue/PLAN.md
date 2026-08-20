# Plan

**Status — 2026-08-20:** the participant-level contract is implemented and
gated by `baton.claude` under Work `W2938`; awaiting independent review.

1. [done] Revalidate the observed W2780 episode against canonical `pickup`,
   handoff, readiness, phase, Handler, and readiness-bridge evidence.
2. [done] Remove the Jobs-list `New` column without changing canonical unread
   state, Inbox, Threads, Message indexes, Work detail, or explicit reads.
3. [done] Remove the superseded Jobs `Claim` column, Work-detail Claim suffix,
   Work-level `claim_cell`, and their assertions. Only the separately approved
   `New` removal was preserved.
4. [done] Pin the participant-level opportunity start, one-slot capacity,
   authority-only availability test, configurable 360-second default, clearing
   rule, and exact Teams/member presentation.
5. [done] Implement `[Teams *]`, Teams `Pickup`, and member detail from the
   pinned participant-level contract without treating Work `pickup` as its
   authority: one-slot capacity in `claim_work`, the canonical
   `member_pickup` interval at schema 25 swept from the one mutation
   boundary, `instance.pickup_overdue_seconds` policy, and the four surfaces.
6. [done] Focused one/many-Job, busy/idle, route-race, claim-clear, refresh,
   width, JSON/TUI parity, and packaged-app regressions:
   `tests/work/test_w2938_participant_pickup.py`, 39 cases. Full v11 gate:
   2737 parallel, 52 serial, 55 ACP. Returning for independent review.
