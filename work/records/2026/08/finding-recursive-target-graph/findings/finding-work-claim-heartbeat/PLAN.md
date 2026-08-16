# Plan

**Status:** implementation-ready after 2026-08-16 source revalidation; active
reviewer research is ready to pass to the implementer.

1. Revalidate claim storage, claim/release/pass/close races, automatic refresh,
   claim Age, JSON/TUI parity, and recovery procedures.
2. Add an audited claimant-only `heartbeat work=Wn` transition using the
   existing generic event journal; the claim event is the initial beat.
   Recheck open status and the exact live claimant inside the committing
   transaction. Support ordinary operation-id replay. Do not call
   `_touch_work()`.
3. Project the latest qualifying claim/heartbeat for all active Work in one
   batched read—never an N+1—scoped strictly to each current claim epoch, and
   expose `heartbeat_at` through canonical JSON. Old-claim beats must not
   survive a release/re-claim boundary.
4. Add `heartbeat` to the shared CLI/TUI grammar as a deliberate claimant act;
   do not infer it from client presence, keystrokes, messages or filesystem
   activity. Derive the fixed two-minute cadence / six-minute stale boundary
   consistently in operating guidance and presentation.
5. Render a reserved-width Age suffix: blank while healthy, `!` after six
   minutes without a successful beat, and clear it on the next beat. Do not
   reset claim Age or trigger Phase-change blink.
6. Cover exact threshold boundaries, delayed/duplicate beats, claimant races,
   release/pass/close, restart/rebuild, clock correction, long-running healthy
   work, stale recovery, narrow omission, read purity, and source/package
   parity. Prove stale state never releases or transfers Work.
7. Run focused workflow coverage and `just test-v11`; return for independent
   review before deploying the next v11 trial.

**Supersession — 2026-08-16:** no fresh schema is required. A projection
version bump is allowed; a future materialized field/index is only an
optimization if journal volume later proves the batched read inadequate.
