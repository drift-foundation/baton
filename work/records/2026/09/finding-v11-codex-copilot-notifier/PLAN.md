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

Current 2026-09-21 owner-selected recovery: rebind rendered baton-prompt to existing interactive thread; restart dispatcher only with tracked identity; verify mapping and start one notifier. Full-stack restart still replaces this mapping. In progress.

Reattachment verified. Pending: run notifier from owner terminal because agent launch approval failed; confirm UI advisory after this conversation becomes idle.

Blocked delivery confirmed 2026-09-21T04:52Z: interactive setup approval quarantined this prompt. W202663 is detected by dry-run. Investigate prompt interactive-approval ownership before another reattachment/restart; preserve quarantine and managed-turn protections.

Current action (2026-09-21, supersedes earlier reattachment/restart hold): restore the owner-selected original fresh prompt `01a0c245-7084-7450-aa08-18c41190d3ee` using the bounded recovery in FINDING.md. Existing notifier is already running. Verify exact mapping, no fence on selected prompt, and other mappings preserved; then await idle UI advisory. Keep the interactive-approval ownership defect open; no product-policy change is part of this operational recovery.
