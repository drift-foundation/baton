# Agent wakeup integration

Status: **immediate post-checkpoint priority**, promoted by Slawomir on
2026-08-10 after repeated operational stalls. Do not bury this behind the
remaining audience/TUI polish: safe non-claiming monitoring is needed for the
reviewer to remain reachable while those reviews run.

Direction confirmed by Slawomir on 2026-08-10: add a blocking, read-only
readiness wait (working names `peek`/`ready`) that returns when eligible work
exists but does not claim or consume it. Final command naming remains a design
task.

CLI surface ruled by Slawomir on 2026-08-10: protocol-10 plain `wait` is the
read-only readiness operation. Compatibility is not a blocker: only this
deployment uses protocol 10 and all role briefs can adopt the contract
together. Do not also ship `ready` or `scan --wait` as aliases for the same
operation.

## What Baton already does

`baton wait --participant P` with no timeout is one blocking call. It queries,
arms, requeries to close the race, blocks, atomically claims one directed
message when it arrives, prints the delivery, and exits. A shell timeout loop
is not required. After the claim is answered or closed, the consumer invokes
the same blocking call again.

## The actual integration gap

An agent host may yield a long-running terminal into the background. When the
terminal later exits, that event does not necessarily schedule a new model
turn. Baton can therefore claim and print a message correctly while no agent
code runs to read the output and answer the claim. Periodically polling the
terminal from an already-active turn works, but ending the turn does not leave
a reliable autonomous consumer.

This is not fixed by changing Baton's timeout or hiding the shell loop inside
another Baton verb. The host must treat terminal completion as a wake event, or
some external supervisor must schedule the agent.

## Immediate operating rule

While a reviewer turn remains active, use one indefinite `baton wait` command,
poll its terminal session, process the returned claim immediately, then invoke
`wait` again. Do not add a timeout loop unless periodic command exit is needed
for a specific operational reason.

Before yielding a turn, do not leave a claiming waiter unattended. Otherwise
it can create an active claim without a model turn available to answer it.

## Possible Baton-side safety improvement

A read-only blocking `watch`/`ready` mode could exit when eligible work exists
without claiming it. The scheduled agent would then run ordinary `wait` or
`claim`. That prevents an unattended background process from holding work, but
it still cannot schedule a model turn by itself.

The readiness result must distinguish at least directed work from a notice
without returning content, and must preserve the existing query-to-arm requery,
polling fallback and gate behavior. Observation creates no claim, no notice
receipt and no other authority write. Multiple consumers may wake for the same
directed message; ordinary `claim` remains the transaction that decides who
owns it.

A signal, socket, webhook or command hook can bridge the wake event only when
the host explicitly supports and authorizes that integration. It is not a
portable substitute for host scheduling and must not be embedded as an
arbitrary-command execution surface in the core CLI.

## Why not silently change `wait` itself

Today's `wait` is one atomic consumer operation: it claims a directed message
and returns its content, or records a notice receipt and returns that content.
Changing it to readiness-only would make every consumer perform a second
operation and branch between `claim` and `see`. Between the readiness result
and that second operation, another consumer may take the work; all role briefs
and protocol documentation would also change meaning.

Keeping both verbs gives each name one purpose:

- `ready`: block until eligible work exists; metadata/status only; no authority
  write; safe to leave in a background terminal that may not wake its agent;
- `wait`: block and atomically consume one item; use only while an active agent
  is ready to answer the resulting claim immediately.

`ready` does not solve host scheduling, but it converts a missed wake from a
held, unanswered claim into merely delayed work. That is the safety property
needed by the current agent host without weakening the efficient one-step path
for consumers that are actually running.

## Protocol-10 surface ruling

## Readiness queue semantics — ruled 2026-08-10

Slawomir ruled that a read-only readiness wait observes the directed queue in
deterministic FIFO order and returns **the first pending message it encounters**.
It does not scan ahead looking for a healthier or more interesting row:

- when that message verifies, return its metadata as deliverable;
- when its external content is damaged, return that same message as a damage
  event with no content and no claim;
- do not claim, mark seen, quarantine, skip, or otherwise mutate anything.

The caller decides the next operation: claim the deliverable id, inspect or
quarantine the damaged id, or run a broader scan. Existing consuming `claim`
keeps its skip-and-continue behavior so a caller that deliberately proceeds
can still reach healthy work behind damage.

This is deliberately not a complete damage inventory. Readiness reports what
the FIFO observation encountered; it does not inspect the whole queue merely
to prove whether later damage exists.

### Ruled: make `wait` read-only

`wait` blocks until eligible directed work or a notice exists, returns only
readiness metadata, and writes nothing. The active consumer then calls
`claim --message-id` for directed work or an exact notice-open/`see` operation
for a notice. The one-live-consumer policy keeps the readiness-to-claim race
bounded; a lost race simply returns to `wait`.

This makes the natural unattended command safe by default. A missed host wake
delays work but never holds it. It is a breaking CLI/wire behavior change, but
protocol 10 is already the coordinated breaking cutover and there are no
external consumers to preserve.

The exact notice follow-up must be pinned: a readiness result names one notice,
so consuming it must not accidentally drain a different notice that arrived
first.

### Rejected alternative: preserve consuming `wait`; extend `scan`

Keep today's atomic `wait`. Extend existing read-only `scan` with a blocking
mode such as `scan --wait`; plain `scan` remains an immediate snapshot.
`scan --wait` includes eligible notice metadata as well as directed work and
creates no claim or receipt. Agents use it for unattended monitoring and use
consuming `wait` only while active.

This is backward-compatible and keeps the efficient one-step consumer, but the
most obvious command remains unsafe to leave unattended. Every agent brief has
to teach that distinction correctly.

## Live wakeup evidence — 2026-08-10

A coordinated live test separated the authority transition from the human
console display:

- With an already-armed default `wait`, message
  `4b4fcf681bcde7234f903291653f0912` was created at `09:49:27Z` and not claimed
  until `09:50:27Z`: exactly the 60-second safety rescan interval. The waiter
  process remained alive throughout. This is evidence that the event wakeup
  did not fire in this deployment and pure polling recovered it.
- With `wait --interval 1`, K's older FIFO handoff was created at `09:55:05Z`
  and claimed at `09:55:06Z`.
- Slawomir's test message was created at `09:55:18Z` behind that handoff. Once
  the handoff was answered at `09:55:31Z`, a re-armed one-second waiter claimed
  the test at `09:55:34Z`; the TUI then refreshed automatically. That sequence
  does not demonstrate a TUI refresh defect.

The first result is a regression target for the default watch path. A test
must distinguish a real filesystem-event wake from the 60-second safety
rescan; merely asserting eventual delivery hides the failure for a full minute.
