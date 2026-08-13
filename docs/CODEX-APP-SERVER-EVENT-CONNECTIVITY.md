# Codex app-server event connectivity

## Purpose

One local event bridge dispatches external events to many isolated, persistent
Codex threads through one or more Codex app-server instances. Each logical
agent owns one target thread. For that agent, its TUI and the bridge are peer
clients operating on the same thread ID.

The bridge may manage many agent/thread pairs concurrently. Activity in one
thread must not serialize or block unrelated threads.

The installed Codex schemas are the implementation contract. The upstream
[Codex app-server documentation](https://developers.openai.com/codex/app-server)
describes the integration surface, but app-server and its WebSocket transport
remain experimental.

## Topology

```text
Local event producers
        │
        ▼
 Unix socket 0600
        │
        ▼
┌───────────────────────────────────┐
│ codex-event-bridge                │
│                                   │
│ normalize / validate / limit      │
│ deduplicate / route               │
│                                   │
│ target A queue + state            │
│ target B queue + state            │
│ target C queue + state            │
└────────────────┬──────────────────┘
                 │ app-server protocol
                 ▼
          codex app-server
          /       |       \
         /        |        \
    thread A   thread B   thread C
       ▲          ▲          ▲
       │          │          │
     TUI A      TUI B      TUI C
```

The first version uses one app-server on a loopback WebSocket. Configuration
nevertheless names servers independently so a target can move to another
app-server later without changing event producers or dispatcher logic.

## Configuration model

```json
{
  "baton": {
    "binary": "/absolute/path/to/bin/baton",
    "config": "/absolute/path/to/mailbox/baton.json"
  },
  "servers": {
    "local": {
      "endpoint": "ws://127.0.0.1:4500"
    }
  },
  "targets": {
    "driftquery-reviewer": {
      "server": "local",
      "threadId": "abc123",
      "participant": "dq.reviewer"
    },
    "pushcoin-reviewer": {
      "server": "local",
      "threadId": "def456",
      "participant": "pushcoin.reviewer"
    }
  }
}
```

A target name is a bridge routing identifier. It has no meaning to Codex. A
thread ID may appear under only one target unless an explicit future design
supports aliases; rejecting accidental duplicates avoids two local queues
racing on the same thread. A Baton participant may also appear under only one
target, preserving one readiness path and one deterministic destination.

One foreground invocation starts and supervises the complete configured set:

```text
just codex-baton /absolute/path/to/config.json
    │
    ├── every named loopback app-server
    ├── one shared multi-target event bridge
    └── one read-only Baton monitor per target/participant
```

The TUI remains an independent interactive peer and may attach or reconnect at
any time.

This is a machine-wide service boundary. A team does not launch another bridge
or another `wait` for its participant. Adding a Codex-backed team means adding
one unique participant/target/thread mapping to the shared configuration and
restarting the one supervisor deliberately. The configuration may contain only
the reviewer roles when implementers use another agent runner; product roles
do not have to share one integration mechanism.

The bridge socket is not the readiness boundary. Before any Baton monitor is
started, the supervisor queries bridge status and requires every configured
thread to have completed its initial `thread/resume`. A thread still owned by
an older per-session Codex backend produces an active-writer conflict and keeps
the target unavailable. The supervisor reports those targets and tears down the
partial stack; the operator closes the old TUI/backend, restarts the stack, and
then runs `codex resume --remote ENDPOINT THREAD_ID`.

After migration, a reviewer's routine invocation changes from:

```text
codex resume THREAD_ID
```

to:

```text
codex resume --remote ws://127.0.0.1:4500 THREAD_ID
```

The endpoint is shared; the thread ID is the unique session selector. The
participant is not passed on the Codex command line because the supervisor
configuration already binds that thread ID to exactly one Baton participant.

## How a session receives its own Baton readiness

Routing is explicit and deterministic:

```text
baton.reviewer wait reports message M
    │ monitor owns participant baton.reviewer
    ▼
event target baton-reviewer
    │ bridge target maps to thread T1
    ▼
turn/start(threadId=T1, message=M)

dq.reviewer wait reports message N
    │ monitor owns participant dq.reviewer
    ▼
event target driftquery-reviewer
    │ bridge target maps to thread T2
    ▼
turn/start(threadId=T2, message=N)
```

The event contains the participant and exact Baton message ID. The Codex turn
on T1 claims M; the turn on T2 claims N. App-server events also carry their
thread ID, so bridge state and attached TUI visibility remain thread-scoped.
There is no global readiness broadcast and no inference from cwd or project
name.

Baton readiness uses a compact one-line turn input rather than the generic
external-event envelope:

```text
[BATON READY] Baton message M is ready for baton.reviewer. Apply standing Baton policy.
```

The exact message ID remains visible, while duplicated JSON, timestamps,
routing fields, and the generic inspect/fix paragraph are omitted. Baton
readiness is trusted local metadata from the user's Baton process and contains
no mailbox body. Other producer types retain the full safety envelope because
their summaries and details are the actual evidence the agent must evaluate.

## Component boundaries

### Event producers

- Know only the local Unix event socket and a configured target name.
- Send normalized JSON through `codex-event send`.
- Do not know thread IDs, server endpoints, or app-server protocol details.
- Include `run-and-notify`, build-result watchers, and arbitrary local
  applications or adapters.

The Baton adapter is a read-only readiness producer, not a mailbox consumer.
One `baton-codex-monitor` owns one participant's sole `wait`, forwards the
reported message ID or notice readiness through the Unix socket, and suppresses
the unchanged queue head. The Codex turn performs the exact `claim` or `see`
and resolves claims. The adapter never consumes on the agent's behalf.

An event carries its destination explicitly:

```json
{
  "target": "driftquery",
  "source": "build",
  "type": "build-failed",
  "summary": "planner tests failed"
}
```

Producer identity or producer-specific configuration may supply the target,
but routing never belongs inside `CodexClient`.

### EventBridge dispatcher

- Owns target lookup, event validation, size limits, deduplication, and queues.
- Treats all external event fields as untrusted data.
- Maintains one FIFO and one dispatch state machine per target.
- Dispatches independent idle targets concurrently.
- Retains queued events across app-server disconnections while the bridge
  process remains alive.
- Never changes sandboxing, approval policy, or approval reviewer as a routing
  shortcut.

Deduplication includes the target:

```text
hash(target + source + type + normalized summary + normalized details)
```

Identical payloads sent to two targets are two distinct events.

Memory is bounded at three levels. Defaults remain configurable:

```text
maximum encoded event:     64 KiB
maximum events per target: 100
maximum events globally:   1000
```

### CodexClient

`CodexClient` is the only app-server protocol-aware module. Target names never
cross this boundary. Its conceptual operations are:

```text
connect(server)
initialize()
resume(threadId)
readThread(threadId)
startTurn(threadId, input)
consume notifications and server requests
```

For each configured server, the preferred first implementation uses one
initialized connection subscribed to all of that server's configured threads.
The official protocol says starting or resuming a thread subscribes the current
connection to its events, and every relevant notification includes a
`threadId`. The acceptance tests must determine whether approval routing or
other connection-scoped behavior requires one connection per target instead.

The installed generated schemas determine request fields and payload shapes.
For the observed `codex-cli 0.147.0`, `thread/resume` returns runtime status,
`thread/read` reads status without subscribing, and
`thread/status/changed` reports later transitions.

### Codex app-server

- Owns persistent conversations and authoritative thread state.
- Arbitrates requests from TUIs and the bridge.
- Executes independent turns for different threads concurrently, subject to
  server capacity.
- Rejects requests when a target thread is already active or the server is
  overloaded.

The bridge must verify, not assume, how a resumed thread resolves or retains:

```text
model
working directory
AGENTS.md and other instructions
sandbox policy
approval policy and reviewer
```

The protocol permits configuration at thread resume and turn start, and some
turn overrides become defaults for later turns. The bridge initially supplies
no override. Acceptance tests compare effective settings before and during an
externally initiated turn.

### Codex TUI

- Connects with `codex --remote ws://127.0.0.1:4500`.
- Resumes the thread for one logical agent.
- Displays interactive and externally initiated work for that agent.
- Does not serve as the automation API and is never driven by injected
  keystrokes, PTY automation, `expect`, or tmux commands.

## Routing and per-target lifecycle

```text
Producer sends event
        │
        ▼
validate / normalize / route
        │
        ├── invalid or unknown target ──> reject
        ├── duplicate for target ───────> suppress
        ├── target or global limit ─────> reject with backpressure
        └── accepted
                │
                ▼
        selected target FIFO
                │
        ┌───────┴────────┐
        │                │
 target active     target appears idle
        │                │
       wait         attempt turn/start
                         │
                 accepted by server?
                    │          │
                   yes         no
                    │          │
             one active turn   keep event, reconcile,
                    │          retry with backoff
             turn/completed
                    │
             reconcile target
                    │
             dispatch next
```

Each target has four relevant local states:

- **Unavailable:** its server is disconnected or the thread could not resume.
- **Active:** the thread reports active or a bridge turn is in flight.
- **Apparently idle:** local observations allow a dispatch attempt.
- **Reconciling:** the bridge is refreshing state after reconnect, completion,
  rejection, or ambiguous delivery.

Local state is an optimization. Server acceptance or rejection of
`turn/start` is truth. A TUI can win the race after an idle notification; the
bridge retains the event, reconciles that one target, and retries later.

Every queued event also receives a stable client message ID. The bridge passes
it as the installed protocol's `clientUserMessageId`. If the connection drops
after submission but before the response, delivery is ambiguous: the bridge
must resume/read the thread and look for the matching persisted user-message
`clientId` before deciding whether to dequeue or retry. The field is a
reconciliation key; it is not assumed to make `turn/start` idempotent.

An active turn in target A does not prevent target B or C from dispatching.
Server-wide overload does apply global backpressure and an exponentially
increasing retry delay with jitter.

## Same-thread continuity per target

The bridge never creates a fresh thread for each event. For each logical agent:

```text
TUI A ──────────────> thread A
Event bridge ───────> thread A
```

Configured target threads are persistent, not ephemeral. In the tested
`codex-cli 0.147.0` build, another connection could not resume a newly created
ephemeral thread because no rollout existed. A newly started persistent thread
also became peer-resumable only after its first turn materialized the rollout.
Configure an established TUI conversation containing at least one turn.

The continuity acceptance test is performed separately for every configured
target:

1. The human enters a unique marker through that target's TUI.
2. An external event for that target asks for the marker.
3. The bridge starts a turn on the configured thread.
4. Codex returns the correct marker for that target only.
5. The externally initiated turn appears in the attached TUI.

The test also records effective continuity for working directory, instruction
sources including `AGENTS.md`, sandbox policy, approval policy and reviewer,
and model selection. Conversation continuity alone is insufficient.

## Reconnection and queue lifetime

When an app-server connection drops, the Unix event receiver and unaffected
servers remain available:

```text
disconnect server S
    │
    ├── retain queues for S targets in memory
    ├── continue dispatching targets on other servers
    ├── reconnect with bounded exponential backoff and jitter
    ├── initialize the new connection
    ├── resume every configured thread assigned to S
    ├── reconcile every target independently
    └── resume eligible dispatch
```

The initial queue is not crash-durable. Restarting the bridge loses queued
events. Durable queue storage is a separate product decision.

One app-server is also one initial failure domain: if it crashes, every target
assigned to it pauses. The server/target configuration boundary permits later
sharding without changing the event format.

## Security and trust boundaries

- App-server listens only on `127.0.0.1` in the local MVP.
- The producer interface is a Unix socket with mode `0600`.
- The bridge never replaces an existing non-socket filesystem path.
- Unknown targets and oversized events are rejected before queueing.
- Events are presented to Codex as untrusted data.
- The bridge does not change approval policy, sandbox policy, approval
  reviewer, or execution permissions.
- Full protocol payloads are logged only when debug logging is enabled.

## Approval-routing gate

Approval behavior is a protocol acceptance gate, not an implementation detail.
The app-server sends approvals as server-initiated requests to a client, and
that client must respond with a decision. The bridge never approves
automatically.

Test both ownership directions for each possible topology:

```text
Bridge starts turn
    -> approval needed
    -> can the target's TUI display and answer it?

TUI starts turn
    -> approval needed
    -> does the bridge only observe lifecycle events,
       or receive a server request it would have to answer?
```

The tests must determine whether approvals are connection-scoped,
thread-scoped, turn-owner-scoped, or broadcast. If a bridge-initiated approval
is delivered only to the bridge connection, a supported routing or explicit
human approval-relay design is required. Automatic acceptance, reviewer
replacement, and sandbox weakening are not acceptable workarounds.

## Multi-target acceptance gate

Before durability, systemd units, or elaborate producers, run this topology:

```text
1 app-server
5 isolated threads
5 TUIs
1 bridge
```

Start simultaneous events for A, B, and C; start an interactive TUI turn for D;
leave E idle. Verify:

- A, B, and C execute concurrently.
- D is unaffected by event dispatch.
- E stays untouched.
- Notifications route only to their matching thread state machine.
- Markers, working directories, instructions, and output never cross targets.
- Effective model, sandbox, and approval settings match the target thread.
- Both approval ownership directions are understood and remain actionable.
- A disconnect and reconnect resumes and reconciles all five targets without
  losing in-process queued events.
- A disconnect between `turn/start` submission and response does not create a
  duplicate external turn.

Passing this gate establishes that one app-server can safely support N isolated
event-driven Codex agents for this local workflow.
