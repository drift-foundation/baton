# Plan: expose agent runtime state beside the Handler

1. [done — decision] Separate participant runtime state from Work Phase and
   Handler, and reserve the dedicated Jobs `Agent` column.
2. [done — research] Revalidated Codex/ACP event sources, W25's current roster
   projection, lease ownership, and assignment-episode correlation.
3. [done and reviewed 2026-08-19] The fresh-schema authoritative
   runtime-state write/read surface and projections, without permitting
   workflow mutation. Schema 23 adds `runtime_leases` and
   `runtime_events`; `runtime-start`/`runtime-state`/`runtime-end`
   publish, `runtime`/`runtime-history` read. W25 closed, which
   unblocked this. See `PROGRESS.md`.
4. [done and reviewed 2026-08-19] Publish explicit runner events from the
   Codex dispatcher and ACP bridge; derive only `unknown`/`offline` from
   silence. One shared publisher, no new configuration, and no provider query.
   See `PROGRESS.md`.
5. [done and reviewed 2026-08-19 — TUI] Render `Agent` in Jobs; add Teams/Member rows and details for
   role, provider/agent type, model, session locator, state, Work, and age; add
   actionable waiting-input entries in Inbox.
6. [done and reviewed 2026-08-19 — diagnostics] Add safe operational inventory fields with explicit
   provenance/freshness, secret-redaction boundaries, and an on-demand refresh
   path for facts that are impractical to maintain continuously.
7. [done and reviewed 2026-08-19 — verification and operator docs] Cover explicit approval recovery, slow work,
   disconnects, stale publishers, provider limits, claimed/unclaimed Work,
   stale diagnostic data, and secret-bearing launcher configuration. Add the
   operator-facing runtime command reference to `docs/BATON-WORK.md` before
   W93 closes.
