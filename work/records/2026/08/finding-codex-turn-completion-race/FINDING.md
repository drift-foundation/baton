# Codex turn completion can arrive before its waiter

## Observed code path — 2026-08-19

`CodexClient.waitForTurnCompletion(threadId, turnId)` installs a
`turnCompleted` listener only when the caller invokes it. Every production
caller currently invokes it after awaiting `startTurn`.

If the app-server emits `turn/completed` before the `turn/start` response
continuation installs that listener, the completion is discarded. The waiter
then has no prior-state check and no timeout, so it never settles. W424 adds
another operator-visible caller of this pattern to durable role bootstrap.

The race has not been observed against a live app-server. It is structurally
reproducible with a protocol fake that completes a turn before resolving the
start request, so the Work remains classified suspected until the app-server's
ordering contract is established or a live occurrence is captured.

## Recommended correction

Record each received completion in `CodexClient` before publishing the
`turnCompleted` event. `waitForTurnCompletion` first consumes a matching
record and otherwise installs its listener. The cache must be bounded and
cleaned when consumed; unrelated Thread/turn completions must not satisfy a
waiter.

This is shared transport behavior, not a W424-only special case. W424 remains
responsible for the bootstrap command; W484 owns the race-safe completion
primitive used by bootstrap, one-shot injection, and dispatcher delivery.

## Acceptance boundary

- A completion delivered before `waitForTurnCompletion` is called resolves the
  matching wait immediately.
- A completion delivered after the waiter is installed preserves current
  behavior.
- Thread and turn identity both participate in matching.
- Unrelated and duplicate completions cannot resolve the wrong waiter.
- Cached completions are bounded and consumed/evicted deterministically.
- Disconnect behavior remains fail-closed for an unsettled wait.
- Existing dispatcher, `--once`, and W424 bootstrap paths remain green.
- No Baton protocol, projection, or database change is introduced.

