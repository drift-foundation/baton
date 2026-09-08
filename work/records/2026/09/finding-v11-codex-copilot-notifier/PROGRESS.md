# Progress

2026-09-07 baton.prompt, executing owner-authorized work under baton.slaw's
claim: revalidated dispatcher and canonical projection contracts; bounded
implementation begun. Other agents' v12 files remain untouched.

2026-09-07 baton.prompt: implemented the Python standard-library notifier,
operator-filtered obligations/trials, paginated actionable Work, hash cursor,
single-state-file flock, atomic private cursor saves, bounded Unix-socket calls,
dry-run/once/foreground modes, and launch documentation. The bridge adds a
separate copilot-status projection, advisory formatter and prompt-only idle
admission bound to exact thread and bridge incarnation. Ordinary status output,
worker readiness, role identity and managed approval policy remain unchanged.

Verification: all 13 focused Python tests passed (local socket bind required
explicit sandbox escalation); both Node test modules passed (23 bridge tests
and 7 event-format tests). Existing assertions were not edited. git diff
--check passes. CLI --help works. The real read-only dry-run returned exactly
work:2b077949-W105982 and work:2b077949-W106673. It did not touch the event
socket, create a cursor, send a notification, claim either item, or run a model.
Preview configuration retained at
/tmp/baton-copilot-notifier-preview.cxwtwI/config.json for operator inspection.

Ready for independent review. No live enablement, stack restart, Git index or
history changes. Live UI visibility and deployment remain unproved and require
the documented owner-controlled rollout. Socket acceptance is intentionally
not proof of completed analysis; failure recovery remains manual.
