# Plan

**Status — signed off by `baton.codex` on 2026-08-18. See
`review-2026-08-18T14-49-19Z.md`.** Both compound transitions now record their
authoritative `phase_now`, every phase write in `transitions.py` was swept for
the same class, and the ledger/authority agreement is now an enforced
invariant rather than a per-site convention.

**Round-1 status — changes requested in independent review 2026-08-18.**

The fixed-column rendering is present, but the phase ledger is not yet
complete. `request` with its default blocking semantics and the provider Work
created by `accept create=true` are both scheduler transitions outside the
seven paths originally enumerated. The additive review regressions in
`tests/work/test_w47_event_phase_intervals.py` currently fail: the former
leaves `active` open instead of entering `waiting`, and the latter creates no
initial `queued` episode. W47 returns to implementation until both compound
transitions record their authoritative `phase_now` state and the complete
matrix is green.

**Original status:** handed to `baton.impl` 2026-08-18 as W47. This is the first
runnable child of W46 and returns to `baton.bug` for independent review.

1. [done] Revalidate every scheduler transition and define the phase-entry/boundary
   matrix, including creation, claim, pass, release, dependency/child gates,
   explicit waiting/parked moves, and terminal close.
2. [done] Project canonical open and completed `phase_interval` objects from the
   immutable ledger without changing authority schema.
3. [done] Replace the free-form Event row with fixed, responsive columns and the
   shared `MM:SS`/`∞` formatter.
4. [done] Cover column offsets and omission at wide/narrow widths, every phase
   boundary, open snapshot timing, completed stability, heartbeat non-reset,
   zero/59/60/5999/6000-second edges, paging, resize, and JSON/TUI parity.
5. [done] Run focused projection/TUI tests and `just test-v11`, then return for
   independent review.
