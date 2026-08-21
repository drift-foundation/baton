# Plan

**Status — 2026-08-21:** independently signed off and ready for the fresh
schema-26 deployment gate. The approver rejected arbitrary per-thread config
overrides and confirmed the deployment-owned exact command-policy route. The
mediated-MCP recommendation in `review-2026-08-20T23-42-34Z.md` is superseded.

1. [done] Revalidate the repeated approval episodes against the current
   managed-turn command construction, Codex policy matching, dispatcher
   recovery, runtime publisher, and Inbox projection.
2. [done] Provision a deployment-owned exact allow rule for the
   installed Baton executable, accepted config, participant, and exactly the
   approved verbs; prove it against the effective app-server policy with the
   broad rule removed. Refuse same-participant rules for unapproved verbs;
   read-only commands need no sandbox-crossing exception. Keep the
   writable-authority-root proposal and arbitrary turn overrides removed.
3. [done] Define and persist the action-owner incident, including safe
   correlation, coalescing, explicit dismissal, and append-only audit history.
4. [done] Surface open incidents through `[Inbox*]` without conflating them
   with current runner state or offering an approval action.
5. [done] Complete the exact-policy live positive/negative matrix,
   remove the stale writable-root vocabulary from its smoke, retain the
   restart, deduplication, dismissal, and redaction regressions, and run the
   focused bridge/authority/TUI suites and complete applicable gate.
6. [done] Independently review before deployment.
