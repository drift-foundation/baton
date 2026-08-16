# Codex app-server external-event bridge

## Status

Confirmed for implementation on 2026-08-12.

## Goal

Allow a local external event to start a serialized turn in the same persistent
Codex thread that a human uses through the normal Codex TUI. The integration
uses the Codex app-server protocol directly; it does not automate a terminal,
start a separate `codex exec`, or create one thread per event.

The independently reviewable, durable connectivity design is in
[`docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`](../../docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md).

## Confirmed decisions

- The installed Codex release is authoritative. The observed release is
  `codex-cli 0.147.0`; generated JSON Schema and TypeScript definitions are
  retained under `tools/codex-event-bridge/.codex-app-server-schema/`.
- The foreground MVP lives entirely under `tools/codex-event-bridge/` so it is
  independently reviewable and does not alter Baton's release-product work.
- `CodexClient` is the only module that understands the experimental app-server
  JSON-RPC protocol.
- The app-server uses a loopback WebSocket. External producers use a local Unix
  socket restricted to the current user.
- A configured existing thread is resumed. Events start turns only while that
  thread is idle; busy events remain in a FIFO queue. `turn/steer` is not used.
- Inputs are normalized, size-limited, clearly labelled as untrusted external
  event data, and deduplicated over a configurable five-second window.
- Connection loss does not discard queued events. Reconnection repeats the
  initialize handshake and resumes the configured thread with bounded
  exponential backoff.
- The bridge never changes sandbox or approval policy and never answers an
  approval request. A server request requiring human action is logged clearly.

## Installed protocol observations

**Confirmed:** `initialize` requires `clientInfo` plus `capabilities`; this
release's `initialized` notification has no `params`. Text input requires
`text_elements`. `thread/resume` returns `thread.status`, whose variants are
`notLoaded`, `idle`, `systemError`, and `active`. Runtime state is also reported
by `thread/status/changed`, `turn/started`, and `turn/completed`.

**Open acceptance boundary:** Protocol-level same-thread continuity can be
automated, but the normal TUI must be driven by the human. No test may use
keystroke, PTY, `expect`, or tmux injection. The final manual acceptance test is
to attach `codex --remote`, place a marker in the selected thread, submit a
question through the event bridge, and observe the answer in that TUI.

## Acceptance

- A minimal client initializes, resumes a known thread, starts a turn, and
  observes its completion.
- The daemon accepts newline-delimited JSON events over a permission-restricted
  Unix socket, queues while busy, deduplicates, reconnects, and logs lifecycle
  events without streaming token deltas by default.
- A sender accepts flags or stdin. A command wrapper emits bounded failure
  output. A build-result watcher demonstrates a producer without firing on
  every editor save.
- Unit tests cover normalization, size limits, deduplication, serialization,
  busy transitions, and reconnect queue preservation. A local installed-server
  smoke test verifies the wire protocol.
- Documentation gives exact startup, thread selection, event submission,
  same-thread proof, and troubleshooting commands.

## 2026-08-12 multi-target supersession

The singular-thread language in the original goal, confirmed decisions, open
acceptance boundary, and acceptance list above is **superseded**. It described
one useful agent path but incorrectly made that path the bridge-wide unit of
serialization.

The confirmed product model is now:

- One bridge dispatches to N isolated logical targets. Each target maps to one
  server name and one existing persistent thread ID.
- Each target owns its own bounded FIFO, deduplication namespace, observed
  state, active-turn state, and retry/reconciliation path. Independent targets
  may dispatch concurrently.
- Events identify a target; `CodexClient` receives only server and thread IDs
  and does not interpret target names.
- Deduplication includes the target. Memory has an encoded event-size bound,
  a per-target queue bound, and a global queue bound.
- Configuration separates named servers from named targets, although the MVP
  uses one loopback app-server. Reconnect resumes and reconciles every target
  assigned to the reconnected server.
- Cached status is only a dispatch optimization. The response to `turn/start`
  is authoritative; rejection retains the event and initiates reconciliation
  and bounded retry.
- Each event has a stable `clientUserMessageId`. Ambiguous delivery after a
  disconnect is reconciled against persisted user-message `clientId` before
  retry; no idempotence guarantee is inferred from the field itself.
- Model, cwd, instruction, sandbox, approval-policy, and reviewer inheritance
  are not assumed. Effective continuity for each is an acceptance test against
  the installed app-server build.
- Approval behavior is tested in both directions to establish whether requests
  are connection-, thread-, turn-owner-scoped, or broadcast. Automatic
  approval, reviewer substitution, and sandbox weakening remain prohibited.

The partially written single-thread bridge code predates this supersession and
is not an implementation of the current plan. It must be refactored before any
end-to-end acceptance claim.

Current acceptance requires one app-server, five isolated threads, five TUIs,
and one bridge. Three event targets must execute concurrently while a fourth
has an interactive turn and the fifth remains untouched, with no cross-thread
context, notification, cwd, instruction, model, sandbox, or approval leakage.

## 2026-08-12 installed-server observations

**Observed:** On `codex-cli 0.147.0`, a second initialized connection attempting
to `thread/resume` a newly created `ephemeral: true` thread received
`-32600: no rollout found for thread id`. Ephemeral threads therefore cannot be
used to prove the required TUI/bridge peer reconnection path in this build.
Acceptance uses persistent test threads with exact-ID cleanup.

**Observed:** `thread/start` with `ephemeral: false` did not make a brand-new,
zero-turn thread resumable by another connection. Its first completed turn
materialized the rollout, after which peer `thread/resume` succeeded. Target
configuration therefore selects an established TUI conversation, not an empty
thread that has never had a turn.

**Confirmed by installed-server smoke:** One initialized connection resumed two
persistent threads created by another connection. It started turns on both
threads concurrently; the original subscribed connection received both
thread-scoped lifecycle and message streams. Distinct remembered markers were
returned only on their matching threads. The exact two test threads were
deleted after the passing test. For both test threads, the resume response
matched the creation response for model, cwd, instruction-source paths,
sandbox, approval policy, and approval reviewer.

This smoke validates multi-thread peer protocol behavior and response-level
setting continuity in this controlled case. It does not validate the normal
TUI, actual sandbox enforcement, approval ownership, later turn overrides, or
the five-target load gate. Those remain open acceptance work.

**Confirmed by external-event dispatcher smoke:** `baton.reviewer` sent message
`690ffc547ba112737f8b12b4955a0a08` to `baton.implementer`. The reply
`e5a03965373cd779b8d51557911f2293` supplied a real external PONG payload. After
the Baton claim was acknowledged and closed, that payload was normalized and
sent through the bridge's permission-restricted Unix socket to target A while a
synthetic event was sent to target B. Both socket submissions were
acknowledged, both target turns ran concurrently, and the original TUI-like
peer connection observed both completions and isolated responses. The
dispatcher reconciled both queues to empty and stopped normally. The exact two
persistent smoke threads were automatically deleted.

The first post-completion run exposed a deterministic shutdown defect:
`CodexClient.disconnect()` did not emit the lifecycle event awaited by the
server reconnect loop. The test completed all event turns but hung during
shutdown. `disconnect()` now emits exactly once for an established connection;
the same Baton-payload smoke then exited successfully.

## 2026-08-12 Codex Baton operating decision

The confirmed Codex integration uses three persistent local processes with
separate responsibilities:

1. `codex app-server` owns Codex threads and turns.
2. `codex-event-bridge` owns target routing and per-thread event queues.
3. One read-only `baton-codex-monitor` per participant owns that participant's
   sole Baton readiness path and forwards readiness to the configured Codex
   target without claiming messages or seeing notices.

The awakened Codex turn claims the exact message ID carried by the event, or
calls `see` for a notice batch, then resolves any claim. It does not start a
second `wait`; the monitor remains the one readiness path. Claude keeps its own
runner-specific monitor mechanism and does not use Codex app-server.

The repository supplies a fixed-loopback `just codex-app-server` recipe. It
does not accept an arbitrary bind address because the local MVP must not expose
the experimental app-server transport publicly.

**Verified:** `just codex-app-server` started the installed app-server on
`ws://127.0.0.1:4500`; its `/readyz` endpoint returned success. The monitor's
unit tests confirm that message and notice readiness become target-scoped
events without invoking a consume operation.

## 2026-08-12 stack-launch supersession

The preceding recipe decision is **superseded as the normal operator entry
point**. Starting only app-server does not make Baton wake Codex. The required
entry point is one foreground supervisor that starts and watches:

1. every loopback app-server named by the bridge configuration;
2. one event bridge managing all configured targets;
3. one read-only Baton monitor for every configured participant and target.

Participant and server/thread assignments must each be unique. A monitor's
participant determines which Baton readiness it observes; its target resolves
to exactly one Codex thread. The `codex-app-server` recipe may remain as a low-level development component,
but documentation must direct normal operation to `just codex-baton ...`. The
supervisor waits for each app-server `/readyz` endpoint and for the bridge Unix
socket before starting the monitor. If any child exits unexpectedly, it stops
the rest and exits nonzero. SIGINT/SIGTERM stops the children in reverse order.
The interactive TUIs are not children; operators attach them separately with
`codex --remote`.

## 2026-08-12 all-reviewer deployment clarification

The shared deployment has one Codex reviewer for each of the ten team reviewer
participants. Its configuration is machine-level rather than repository-local:
one supervisor reads all participant/target/thread mappings and starts one
monitor per mapping.

Installed app-server verification found that `thread/resume` refuses a thread
still owned by an older per-session Codex backend with a `thread-store
conflict: ... already has an active writer` error. The event socket becoming
available is therefore not sufficient evidence that every configured reviewer
is wired. Before starting any Baton monitor, the supervisor must query bridge
status and require every target to have completed an initial resume. Startup
timeout must identify the targets that remain unavailable and stop the partial
stack. Operators migrate by closing the old session, starting the shared
stack, and resuming that thread through `codex --remote`; they do not create a
replacement thread merely to avoid the writer conflict.

## 2026-08-12 compact Baton wakeup ruling

The generic external-event rendering is unnecessarily noisy for Baton
readiness: it repeats target, source, type, timestamp, the complete `wait` JSON,
and a generic inspect/fix paragraph even though the agent needs only the exact
message readiness or notice readiness. Baton-originated wakeups must render as
one compact line containing a Baton readiness label, the monitor's fixed
readiness summary, and a direction to apply standing Baton policy. The
full generic envelope remains appropriate for arbitrary build, watcher, and
webhook events. Baton wakeups cannot be text-free because `turn/start` requires
input and the exact message ID is what lets the agent claim deterministically.

**Same-day clarification:** the preceding requirement for an
`untrusted-metadata` label is superseded. This deployment's Baton readiness is
trusted local metadata emitted by the user's own Baton process over a
user-restricted Unix socket, and it contains no mailbox message body. Render it
as `[BATON READY]`. Arbitrary producer summaries and details remain untrusted
and continue to use the generic external-event safety framing.
