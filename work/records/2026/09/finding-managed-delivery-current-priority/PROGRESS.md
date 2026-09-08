# Progress — W119195

## 2026-09-08 — baton.prompt, owner-authorized emergency exception

Implemented directly under Slawomir's explicit emergency exception to the
routed-claim requirement, recorded in FINDING.md. No ledger claim is implied.

Changed only tools/codex-event-bridge/src/event_bridge.mjs as a product path.
The existing validated canonical readiness read now selects the first current
Work that has a pending delivery for this participant. Selection keeps the
original queue entries and exact identities; dequeue, ambiguous-start recovery
and settlement operate on the selected entry. Withdrawal-only callers do not
select. Claim-slot bypass uses the same selection rule when a fresh read proves
the slot is free. No protocol, config, priority field or v12 path changed.

Added test/current_priority.test.mjs with nine cases: downgrade behind a busy
turn and later retained delivery, absent delivery without starvation, unreadable
readiness, withdrawal, newly claimed recovery, non-Work head, ambiguous selected
start, no preemption of an in-flight start, and exact new-episode identity.
The main inversion failed against the original code (A delivered instead of B).
After correction all nine pass. Existing test assertions were not edited.

Focused priority/claim-slot/stale/event suites passed. Full package verification
found four regressions in an initial stricter absent-offer wait, corrected by
limiting selection to pending deliveries. Subsequent sandboxed package tests
could not run local socket/CLI checks; bridge-tests.log preserves that refusal.
Authorized rerun: npm test, 442 passed, zero failed/skipped, 2.854 seconds;
see bridge-tests-authorized.log. git diff --check passed.

Canonical dispatch was paused with zero claims at snapshot119262. The deployed
infra manifest points at this checkout. Stack restart and operator resume are
still pending at this entry; local tests do not prove live deployment. This is
a Codex dispatcher correction, not a claim of changed ACP delivery semantics.

## 2026-09-08 — operator restart verified; commit before resume

Prompt's stop-drained invocation stopped the app-server hosting its own session,
aborting the remaining restart sequence. Slawomir completed the restart. The
replacement dispatcher pid3085451 started13:11:39Z from this checkout, after
the final source modification13:03:51Z. Snapshot119349 shows fresh non-stale
managed runtimes, no claims, no incidents or obligations, and dispatch still
paused at generation98. This supersedes the pending-stack-restart status above;
live priority selection after resume remains to be observed. Slawomir requested
a WIP commit before resuming and retains Git ownership.
