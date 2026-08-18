# Finding: the Codex documents describe a stack that does not exist yet

## Context

Split out of W103 (`Rewrite public docs and architecture for v11`) at its
round-one review, which ruled that W103 "cannot close until those required
surfaces are rewritten after W101, or until an explicit separately tracked
child contract owns them and keeps this parent open."

## The blocked surface

- `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`
- `tools/codex-event-bridge/README.md`

Both still present the combined `just codex-baton` protocol-10 monitor stack
as normal operation, with a stack-owned Baton configuration and
`baton-codex-monitor` vocabulary.

## Why it cannot be written yet

W103's own finding requires these documents to describe the shape that exists
AFTER W101 removes `src/baton_source.mjs`, `src/stack.mjs`,
`bin/baton-codex-monitor`, and `bin/codex-baton-stack`. Writing that prose
against today's tree would document a system nobody can run — precisely the
hybrid W103 forbids.

W101 is itself blocked by its own superseding execution order: it must not
remove those paths until W102 completes the standalone-app-server cutover and
verifies every v10 consumer is gone. As of 2026-08-17 that constraint is live
rather than theoretical — processes are running `stack.mjs` and
`baton_source.mjs` directly from the working tree, alongside the deployed v10
CLI, and they own the app server for the reviewing Codex session.

## Acceptance boundary

- Rewritten around a standalone loopback app server, the generic event
  dispatcher, and the separately launched v11 `codex-baton-bridge` readiness
  producer.
- No v10 overlap procedure, stack-owned Baton config, or
  `baton-codex-monitor`/`codex-baton-stack` vocabulary survives.
- Configuration examples validate against the post-W101 generic bridge schema.
- Covered by the same standing active-document scan the rest of the cutover
  uses, so the surfaces cannot silently regress.

## Ordering

W102 -> W101 -> this record. Nothing here may land before W101 has actually
removed the paths; a documentation change that anticipates a removal is the
same defect as one that lags it.

## Revalidation — 2026-08-18 (implementation start)

The prerequisite is satisfied: W4 closed satisfying after removing the
combined v10 monitor/supervisor, its stack-only configuration, and its launch
recipe. The current tree retains three independently launched pieces:

- `codex app-server --listen ws://127.0.0.1:4500` (or the low-level
  `just codex-app-server` recipe);
- `bin/codex-event-bridge --config ...` as the generic multi-target event
  dispatcher;
- one `bin/codex-baton-bridge` per participant as the read-only protocol-11
  readiness producer feeding that dispatcher's Unix socket and configured
  target.

W101 additionally made accepted Baton role instructions part of Codex thread
creation and every configured resume. The generic bridge configuration now
uses `roleInstructions` plus each target's `identity`; the removed top-level
`baton` and legacy target `participant` fields are not part of this model.

The official Codex app-server page still identifies app-server as the deep
integration surface, documents the loopback WebSocket listener and remote TUI,
and marks WebSocket/app-server operation experimental. Repository schema
checks and the installed generated schemas remain the executable contract for
the exact methods and fields this bridge consumes.

## Implemented — 2026-08-18

- Rewrote the architecture document around independently supervised
  app-server, generic dispatcher, v11 readiness producers, and remote TUIs.
- Rewrote the bridge README as an executable startup sequence, preserving
  W101 thread bootstrap and resume-time durable role instructions.
- Added both documents to the standing active v11 documentation scan and made
  the checked-in JSON example execute through the real bridge validator.
- Removed all combined-supervisor, overlap, stack-owned configuration, retired
  monitor, and obsolete projection-5 guidance from the two active surfaces.

Evidence: focused W4/W103 documentation checks pass 49/49; the complete Codex
bridge suite passes 6/6 files; the checked-in example validates; installed
`codex app-server --help` and `codex resume --help` confirm the documented
commands; the retired-vocabulary scan is empty; and `git diff --check` is
clean.
