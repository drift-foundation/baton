# Codex app-server event connectivity

## Purpose

One generic event dispatcher routes external events to isolated, persistent
Codex threads through one or more Codex app-server instances. Baton readiness
is one event source: a separate protocol-11 producer reads one participant's
canonical `wait` projection and forwards compact readiness events to that
participant's configured target.

For normal repository operation, one mailbox-local lifecycle controller owns
the explicitly configured backend set. App-server, the dispatcher, and each
readiness client remain separate child processes; none discovers, adopts, or
silently restarts another.

The installed Codex schemas are the executable protocol contract. The
official [Codex app-server documentation](https://developers.openai.com/codex/app-server)
describes the integration surface, loopback WebSocket listener, and remote
TUI. App-server and its WebSocket transport remain experimental.

## Post-v10 topology

```text
Human TUI ───────────────> prompt thread (`baton.prompt`, no readiness)
                                  ▲
Other local producers ─┐          │
                       ▼          │
                    Codex app-server
                       │       ▲
                       ▼       │
                 codex-event-bridge
              validate / dedupe / route
               one queue and runtime
               publisher per target
                       ▲
                       │ Unix socket 0600
Baton wait (`baton.codex`) ─ codex-baton-bridge
                       │
                       └────> reviewer thread (`baton.codex`)
```

The processes have deliberately separate responsibilities:

- `codex app-server` owns conversations, turns, approvals, and authoritative
  thread state.
- `codex-event-bridge` owns the Unix socket, target mapping, event validation,
  deduplication, per-target queues, app-server connections, and configured
  thread resumes.
- One `codex-baton-bridge` process owns the sole readiness path for one Baton
  participant. It reads `wait` and emits events; it never claims Work, answers
  obligations, marks messages seen, or changes authority state.
- A remote Codex TUI is the interactive peer on a dedicated prompt thread. It
  is not driven through keystrokes or terminal automation, and it never
  shares the managed background participant or thread.

No backend process starts or silently restarts another. The lifecycle
controller starts them in declared dependency order and stops only the exact
process identities it recorded. Failure of one component remains visible and
does not imply that the others stopped.

## Normal lifecycle

Copy `conf/infra.example.json` to `MAILBOX/infra.json`, and copy its dispatcher,
Claude ACP, and Gemini ACP templates from `conf/` beside it. Replace every
deployment placeholder with an absolute path or explicit provider setting,
leaving lifecycle-owned context, render, and start-id references intact. The
manifest is strict JSON and is the entire launch contract; the recipes infer
no release, authority, participant, thread, socket, credential, or policy
path.

```bash
just start /absolute/path/to/mailbox
just status /absolute/path/to/mailbox
just stop /absolute/path/to/mailbox
```

`start` brings up the declared services in dependency order and is idempotent
only when the complete owned set is healthy. `status` reports every service,
PID, health state, and log and succeeds only for that complete healthy set.
`stop` sends `SIGTERM` in reverse dependency order to processes whose recorded
Linux start identity and argv still match; it never adopts a process and never
escalates to a force signal.

Logs append beneath `MAILBOX/log/`. Private atomic ownership state lives
beneath `MAILBOX/run/`. A partial, stale, changed, or tampered set refuses a
new start; inspect it with `status`, correct any manifest problem, and use the
bounded `stop`. These commands never start or stop a TUI.

## Configuration model

The dispatcher uses the post-v10 schema in
`tools/codex-event-bridge/config.example.json`:

```json
{
  "roleInstructions": {
    "binary": "/absolute/path/to/bin/baton",
    "config": "/absolute/path/to/baton.json"
  },
  "servers": {
    "local": {
      "endpoint": "ws://127.0.0.1:4500"
    }
  },
  "targets": {
    "baton-tuner": {
      "server": "local",
      "threadId": "019c0000-0000-7000-8000-000000000001",
      "identity": {
        "participant": "baton.tuner",
        "role": "tuner"
      }
    }
  },
  "eventSocket": "/run/user/1000/codex-events.sock"
}
```

A target name is a local routing identifier, not a Codex or Baton identity.
Each server/thread pair belongs to one target. Each Baton participant also
belongs to one target, preserving one runtime publisher and one deterministic
thread destination. Selecting different roles does not make duplicate
participant assignments safe. A target does not imply a readiness producer:
the dedicated interactive participant has a target for role instructions and
runtime reporting, while only managed background participants have readiness
services.

`roleInstructions` identifies the canonical Baton CLI and accepted
configuration. The dispatcher does not read `baton.json` directly. Before it
connects targets, it invokes the participant-relative `instructions` read for
each `identity` — which names both the participant and one explicit role — and
reapplies the accepted text as `developerInstructions` on every configured
thread resume. A target missing a role, or naming one its participant does not
hold, refuses before any connection. There is no inferred role: a participant
holding one role today may hold two tomorrow, and that edit must not silently
change an existing session's persona.

The removed stack-owned `baton` block and legacy target `participant` field
are not part of this schema. Readiness timing and retries belong to each
separately launched readiness producer.

## Manual startup and troubleshooting

The following low-level commands expose each component independently. Use
them for configuration, bootstrap, diagnostics, and the documented acceptance
gates. A manually launched process is deliberately not adopted by
`just start`; stop it before switching to lifecycle ownership.

### 1. Start the loopback app-server

```bash
codex app-server --listen ws://127.0.0.1:4500
```

The repository's `just codex-app-server` recipe is a low-level convenience for
this one process. It does not start the dispatcher or readiness producers.

### 2. Create this start's participant threads

Under `just start` this step is not manual: the manifest declares exactly one
CONTEXT per Codex participant, the controller runs the bootstrap once the
app-server is ready, and the dispatcher's configuration is rendered from a
template with the minted ids substituted in. The interactive prompt and each
managed background participant are separate contexts. See "Fresh agent contexts" in
`docs/BATON-SETUP.md`; `conf/infra.example.json` and
`conf/codex-event-bridge.template.json` are the shipped pair.

Run it by hand only when you are driving the backend without the lifecycle
controller. Either way the thread is created through the bridge bootstrap, so
the accepted Baton role instructions are present from its first turn:

```bash
tools/codex-event-bridge/bin/codex-event-bridge \
    --start-thread \
    --endpoint ws://127.0.0.1:4500 \
    --cwd /absolute/path/to/workspace \
    --baton /absolute/path/to/bin/baton \
    --baton-config /absolute/path/to/baton.json \
    --participant baton.tuner \
    --role tuner
```

The command records one no-tool bootstrap turn and then resumes the thread on
a second connection before printing anything: `thread/start` alone leaves an
id with no durable rollout, which only the creating client can read. It prints
JSON containing the thread ID, selected role, and accepted configuration
generation, and it FAILS — printing no locator — if the thread cannot be
persisted or cannot be resumed.

That covers the handoff this start needs: the bootstrap client disconnects and
the dispatcher you launch next resumes the same thread. Put that ID and
identity into the dispatcher configuration FOR THIS START — which the
lifecycle controller does for you, into private `run/` state, when the
manifest declares the context. A bootstrapped id
belongs to the app-server lifetime that produced it — managed starts create
fresh agent contexts, so bootstrap again rather than carrying an id across a
restart. Existing manually prompted threads are bootstrap compatibility
only; deliberately recreate or resume them through this path when durable role
instructions become authoritative.

### 3. Start the generic dispatcher

```bash
tools/codex-event-bridge/bin/codex-event-bridge \
    --config /absolute/path/to/codex-event-bridge.json
```

Startup validates the configuration and generated Codex schemas, resolves all
role instructions, connects each named app-server, and resumes each configured
thread. It creates the event socket with mode `0600`.

### 4. Start one readiness producer per participant

```bash
tools/codex-event-bridge/bin/codex-baton-bridge \
    --baton /absolute/path/to/bin/baton \
    --config /absolute/path/to/baton.json \
    --participant baton.tuner \
    --target baton-tuner \
    --socket /run/user/1000/codex-events.sock
```

The target and socket must exactly match the dispatcher configuration. Start
exactly one process for each managed participant that consumes routed Work. A
second producer sees the same level-triggered action set and can manufacture
duplicate Codex turns. Start no readiness producer for the interactive prompt:
its dispatcher target exists for its dedicated thread, accepted role
instructions and runtime publisher, not for background Work delivery.

### 5. Attach the interactive TUI to the prompt context

```bash
codex resume --remote ws://127.0.0.1:4500 PROMPT_THREAD_ID
```

The endpoint selects app-server; the thread ID selects the logical agent. Read
`PROMPT_THREAD_ID` from the lifecycle state's context whose participant is the
dedicated interactive identity, never from a managed reviewer's context:

```bash
jq -r '.contexts.prompt.threadId' /absolute/path/to/mailbox/run/infra-state.json
```

Attaching the TUI neither starts nor owns the dispatcher. The prompt target
has no readiness producer; closing the TUI leaves its runtime target visible
and does not affect the managed background reviewer.

## Baton readiness flow

```text
participant-relative `wait`
        │
        ▼
validate protocol, projection, participant and typed action keys
        │
        ▼
one compact event addressed to the configured target
        │
        ▼
target FIFO -> turn/start on the persistent thread
        │
        ▼
agent re-reads detail and claims or resolves through the canonical v11 CLI
```

Readiness is an edge to re-evaluate, never authority to execute. The producer
forwards Work assignment episodes, directed obligations, and due verification
trials using stable action keys. It suppresses a key while it remains present,
forgets it when it disappears, and emits it again if a new episode makes it
actionable later. Restarting the producer deliberately rediscovers the current
set.

The resulting trusted turn input is compact, for example:

```text
[BATON READY] v11 Work W6 (...) is ready and unclaimed for baton.tuner. Act through the canonical v11 CLI (detail work=W6). Apply standing v11 Baton policy.
```

It contains locators, not discussion bodies. The awakened agent must still
perform the atomic claim or other canonical operation; the producer never does
that on its behalf.

## Generic event producers

Other local producers know only the Unix event socket and target name. A
normalized event carries its destination explicitly:

```json
{
  "target": "baton-tuner",
  "source": "build",
  "type": "build-failed",
  "summary": "planner tests failed"
}
```

These fields are untrusted data when presented to Codex. They cannot override
user, developer, repository, sandbox, or approval instructions. Baton events
are a distinct trusted local type because they are produced from the user's
canonical Baton CLI and contain no mailbox or discussion body.

## Dispatcher and per-target lifecycle

The dispatcher validates and normalizes each event, rejects unknown targets
or size/capacity violations, deduplicates within the target, and appends the
event to that target's FIFO. One busy thread does not block unrelated targets.

Each target can be unavailable, active, apparently idle, or reconciling.
App-server acceptance or rejection of `turn/start` is authoritative; local
idle state is only an optimization. If a TUI wins the race, the dispatcher
keeps the event, refreshes that target, and retries with bounded backoff.

Every queued event receives a stable `clientUserMessageId`. When a connection
drops after submission but before response, the dispatcher resumes/reads the
thread and looks for the matching persisted client ID before deciding whether
to dequeue or retry. This is a reconciliation key, not an assumption that
`turn/start` is idempotent.

Queues survive an app-server disconnect while the dispatcher process remains
alive. They are not crash-durable; restarting the dispatcher loses in-memory
events. A disconnected server pauses only its targets, while targets assigned
to other servers continue.

## Security and approval boundaries

- Keep the MVP listener on loopback. Plain WebSockets are only for localhost
  or an explicitly secured forwarding arrangement.
- The producer socket is mode `0600`; the dispatcher never replaces an
  existing non-socket path.
- Unknown targets and oversized events refuse before queueing.
- Debug logging may contain complete event and protocol payloads.
- The bridge never changes sandboxing, approval policy, reviewer, or execution
  permissions.
- Approval requests remain a human-action gate. The dispatcher never approves
  one automatically — and, since W3243, never leaves one unanswered either.
  Dispatcher-owned readiness turns are NON-INTERACTIVE execution: the request
  is explicitly DENIED with a protocol error, which no app-server can read as
  permission, and the turn is interrupted if it has not ended within
  `approvalRecoveryMs` (default 15s). Until that turn actually ends the target
  reports a live `blocked` condition with the participant, thread, turn,
  cause, queue depth and oldest queued age in `control: status`.
  Leaving the request unanswered was the defect: a target sat in
  `waiting-input(approval)` for over ten hours while 24 later readiness events
  queued behind it and the stack reported it healthy, because it was connected
  and loaded.
- **An unexpected approval QUARANTINES that managed context** for the rest of
  the managed-stack start (W99, ruled 2026-08-21). Ending or interrupting the
  turn clears only the live `blocked` condition; it never makes the context
  deliverable again. `control: status` reports a separate sticky `tainted`
  row — cause, safe category, method, the approval's own turn id, the Work and
  action key it was serving, how many requests were refused, and the remedy —
  the target stays `deliverable: false`, the stack stays `ready: false`, and
  the runner publishes `failed` rather than `idle` once its turn ends.
  Readiness events queued behind it are RETAINED and are never delivered on
  that context.

  The remedy is a **full managed-stack stop/start**, which mints a fresh
  context; a dispatcher-only restart resumes the same configured thread and is
  not a remedy. Baton's level-triggered readiness re-offers the still-actionable
  Work to the fresh context. The dispatcher does not create a replacement
  context, which is v12's worker supervisor's job.

  **The fence outlives the dispatcher process**, because otherwise relaunching
  that one process would be exactly the recovery the rule denies. Each
  quarantine is written to a marker under `quarantineDir` (default
  `.codex-quarantine` beside the event socket), keyed by server and thread id
  and restored before any lease opens or any socket listens. A dispatcher-only
  restart resumes the same thread, finds the marker, and stays fenced; a full
  start mints a new thread id, so the old marker is not that context's and the
  fresh one is clean without anything being deleted. Markers hold only what the
  status row publishes plus one durable acknowledgement (below) — never a
  command body, argv, environment value or filesystem operand. If a marker
  cannot be written the fence still holds in memory and the row reports
  `tainted.durable: false`, which is the operator's cue that relaunching the
  dispatcher would clear it.

  A marker that exists but cannot be read or parsed **fails closed**. Only
  `ENOENT` is a clean context: a marker at that exact key is evidence that the
  context was quarantined, and losing its diagnostics destroys what was known
  about why, not the fact that it happened. The damaged bytes are copied aside
  for inspection and the context loads as unknown-but-tainted, so one corrupt
  file fences its own context without stopping the dispatcher or affecting
  another target. "Cannot be read" includes an instant the restore could not
  format: a marker's `since` counts as present only when the same
  `new Date(...).toISOString()` the restore uses accepts it, so a finite value
  outside that range is damaged like any other corruption rather than throwing
  during startup.

  The marker also records whether the durable incident was ever published. The
  fence is committed synchronously before the denial while the incident is a
  later asynchronous report, so a dispatcher can stop in between — and while an
  attribution is deferred, that window lasts as long as `turn/start`. A
  restoring dispatcher cannot infer that a fire-and-forget publication
  completed before its predecessor died, so it files the incident itself
  unless the marker carries the acknowledgement.

  Whether that recovery is Work-correlated depends on what the marker proved,
  not on which process files it. An `exact` marker was written only after the
  request's authoritative turn id matched an immutable delivery attempt, and it
  durably carries the Work, episode and action key that match produced — so the
  recovery keeps them. Every other restored marker files uncorrelated: a
  `pending` attribution was never settled (the attempt that could have proven
  it was process-local), an `unmatched` one was settled against the origin, and
  a damaged one lost its payload.

  Reconstruction also requires the record to be INTERNALLY CONSISTENT and its
  locator text to satisfy the same contract the live event normalizer applies.
  `exact` means the request's authoritative turn id matched an attempt, so a
  record claiming `exact` without that turn id contradicts itself and proves
  nothing. The work, episode and action key must all be well-formed, and their
  text must already be in the trimmed, non-blank form the live path stores —
  blank or padded text was never written by this dispatcher, and repairing it
  here would accept a locator the dispatcher never derived. Anything short of
  that files uncorrelated. The action key is checked for shape only and is
  never parsed.

  That text contract covers the Work and action key alone. The turn id is a
  separate opaque identity: the app-server types it as a plain string, the
  bridge binds whatever non-empty string `turn/start` returned, and the origin
  is proven by exact equality against that stored value. Padding is therefore
  part of the identity rather than damage to repair, and one shared predicate
  is used by the binding, the selection and the recovery so the three cannot
  drift apart — a stricter recovery rule would discard an origin the live path
  had already proven.

  This supersedes, for the approval case only, the earlier rule that retained
  events drain once the target goes idle. Turn completion proves the turn
  stopped; it does not prove the persistent agent context discarded the
  interrupted Work's intent. The observed counterexample: an approval-blocked
  W30 turn was interrupted, and the same context then attempted W30's
  unfinished cleanup during the next Work's readiness episode.
- **Incident correlation is selected by the approval request's own turn id**
  against an immutable delivery attempt recorded before `turn/start`, not from
  mutable current state. A request that races the `turn/start` continuation is
  still attributed to the Work that was delivered; a request naming a turn this
  dispatcher never delivered is reported and filed WITHOUT a Work origin rather
  than attributed to another episode.

  A request naming a turn that nothing has bound yet is UNPROVEN, not assumed:
  one delivery being in flight does not establish that this request's turn id
  is the one `turn/start` is about to bind. Its Work attribution waits for that
  binding and is then either proven exact or filed uncorrelated. Only the
  attribution waits — the quarantine, the denial and the bounded interrupt are
  immediate — and the wait is bounded by the delivery attempt itself, so an
  approval on a target that will never drain again still produces its durable
  incident. Command bodies, argv, environment values and filesystem operands
  stay out of every incident, marker, status row and log line.

Approval ownership must be tested for bridge-originated and TUI-originated
turns. If an approval is delivered only to the initiating connection, a
supported human relay is required; weakening policy is not a workaround.

## Isolation acceptance

Before relying on the topology, test one app-server, five isolated threads,
five TUIs, one dispatcher, and the required readiness producers:

1. Send simultaneous events to A, B, and C.
2. Start an interactive TUI turn for D and leave E idle.
3. Verify A/B/C run independently, D is unaffected, and E remains untouched.
4. Verify thread markers, cwd, instructions, model, sandbox, approval state,
   notifications, and output never cross targets.
5. Verify reconnect reconciliation and ambiguous-delivery handling do not
   create duplicate turns.
6. Verify both approval ownership directions remain human-actionable.
7. Verify every participant maps to one thread and every thread to one
   participant; the interactive prompt has runtime state but no readiness
   process, and a background Handler's `Run` comes from that same background
   thread.

Passing this gate establishes that the local app-server can support the
configured isolated agents. It does not turn the experimental transport into
a production-supported OpenAI interface.
