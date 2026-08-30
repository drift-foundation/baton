# Progress: Codex system-error target stays healthy and never drains

2026-08-30 — Live incident recorded. No implementation has started. The
authority has no active claim; W36540 and W39357 remain safely queued in the
broken reviewer target pending managed restart.

2026-08-30 — `baton.tuner` claimed W43539 and delivered the bounded v11
correction. Revalidated the installed/current app-server thread-status model,
pinned `systemError` as a sticky terminal configured-context failure, and
kept automatic live context replacement in v12 worker-supervisor scope.

Implementation and operator polish:

- `tools/codex-event-bridge/src/event_bridge.mjs` now distinguishes reusable
  `idle`/`active` status from terminal `systemError`, publishes
  `failed(internal)` only after the authoritative status refresh, keeps a
  sticky terminal fence, retains queued and in-flight readiness identities,
  and exposes participant/session/failed-turn/status/queue/remedy diagnostics
  through `control: status` so managed lifecycle health becomes false.
- `tools/codex-event-bridge/test/system_error_target.test.mjs` separately
  covers completed/idle, failed/idle, failed/systemError, sticky late status,
  duplicate completion, retained/duplicate readiness, reconnect, and a fresh
  managed-context restart.
- `docs/BATON-SETUP.md` and `tools/codex-event-bridge/README.md` document the
  health rule and the one safe v11 recovery: stop/start the managed stack;
  restarting only the dispatcher resumes the same failed thread.
- Existing W39868 changes already present in
  `event_bridge.mjs`/`failed_turn_settlement.test.mjs` were preserved and the
  combined settlement suite passes.

Verification:

- `node --test tools/codex-event-bridge/test/system_error_target.test.mjs` —
  passed.
- `npm test` in `tools/codex-event-bridge` — 426 passed.
- `just test-v11` — 3,323 main tests and 54 adversarial/PTY tests passed;
  the ACP bridge gate also passed 89 tests.
- `git diff --check` — clean across the shared dirty checkout.

State: implementation is complete and awaits independent review. No deploy or
managed-stack restart was performed by this Work episode.
