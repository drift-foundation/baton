# Current plan

1. DONE: Implement read-only attention polling, persistent deduplication, and an
   explicitly configured existing prompt target. No shell execution or SQL.
2. DONE: Add advisory event formatting and prompt-only, idle-only admission without
   changing managed approval policy. Coalesce at the watcher, not a second queue.
3. DONE: Run focused Python and bridge tests; exercise read-only dry-run locally.
4. DONE: Independent review; bounded implementation signed off in
   `review-2026-09-07T13-34-37Z.md`.
5. APPROVED, awaiting operator execution: Owner-controlled dispatcher restart
   and one live UI notification proof. Attach to the newly minted configured
   prompt thread after full start. No new Baton/TUI build or schema activation
   needed; the dispatcher uses the source checkout. Close only after visible
   notification evidence. Review itself enabled/restarted no infrastructure.

Ownership: tools/codex_copilot_notifier.py, tools/test_codex_copilot_notifier.py,
tools/CODEX-COPILOT-NOTIFIER.md; tools/codex-event-bridge/src/event_types.mjs,
src/event_bridge.mjs, and additive tests in that bridge; this dossier only.
