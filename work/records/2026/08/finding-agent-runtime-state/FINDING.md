# Finding: expose agent runtime state beside the Handler

## Observation — 2026-08-19

`baton.tuner` held W22 while its Codex turn waited on an interactive command
approval. The dispatcher logged the exact
`item/commandExecution/requestApproval` event, but Baton exposed only the Work
claim: W22 remained active with `baton.tuner` as Handler. The operator could
not distinguish productive execution from a turn waiting for input without
opening dispatcher logs and attaching to the Codex session.

Work Phase and Handler cannot carry this information. Phase is the Work
scheduler state; Handler identifies the participant holding the claim. Neither
answers what that participant's runner is doing now.

## Confirmed decisions — 2026-08-19

1. Agent runtime state is a distinct participant-level fact. It never mutates
   Work Phase, Route, Handler, claim ownership, or assignment.
2. Jobs lists have a dedicated `Agent` column beside `Handler`. It reports the
   current Handler's runtime state. An unclaimed Work shows `-`; a claimed Work
   with no current runner evidence shows `unknown` in JSON and a compact TUI
   rendering.
3. The same canonical state feeds the Teams view. Operator-actionable states,
   such as an interactive approval request, also surface in Inbox with the
   participant, related Work/action episode, reason, age, and a session locator
   when one exists.
4. Explicit adapter events are authoritative: turn start/completion,
   interactive input requests, authentication failure, provider overload or
   rate limiting, retry, disconnect, and process exit. Silence may derive only
   `unknown` or `offline`; Baton must not diagnose silence as `stuck`.
5. The initial semantic states are `offline`, `idle`, `working`,
   `waiting-input`, `retrying`, `failed`, and `unknown`. JSON uses semantic
   strings. The TUI may use compact labels without changing their meaning.
6. A runner publishes state under one participant plus a runner/lease identity
   and assignment episode where applicable. A superseded runner must not
   overwrite its replacement's state.
7. Runtime diagnostics never auto-release, transfer, block, close, or reassign
   Work. Recovery remains an explicit operator or Handler action.
8. The Teams surface exposes a Members view that is sufficient to locate and
   diagnose every configured participant without running a vendor-specific
   thread-listing command. Each member shows its participant identity, held
   role, agent/provider type (`codex`, `claude`, `gemini`, or another configured
   adapter), current session id/locator, runtime state, related Work, and state
   age. A details view preserves the full session identifier even when the
   table uses a compact prefix.
9. Provider, model, and session are distinct fields. The agent/provider type
   identifies the runner family; the model is optional runtime metadata; the
   session id identifies the exact live or last-observed session. Missing
   evidence is explicit `unknown`, never inferred from a participant name.
10. Member details are the operational inventory for that participant, not
    merely a roster entry. Where available they include:
    - configured identity, roles, endpoints, and selectable routes;
    - runner/adapter family and version, provider, model, and session locator;
    - runtime state, reason, transition time, last contact, retry/reset time,
      and state provenance (`configured`, `reported`, or `derived`);
    - current claimed Work, queued readiness/action count, pending obligations
      and pokes;
    - service/process identity, dispatcher target, readiness path, working
      directory/root, and the configured log locator; and
    - advisory context and provider-limit information when the runner reports
      it.

    The surface never publishes credentials, tokens, policy secrets, raw
    environment values, or an agent's private prompt merely to aid debugging.
    Every runtime field carries freshness; stale facts remain visibly stale
    rather than looking current.
11. Keeping every diagnostic continuously live is not required. Configured
    identity and the last canonical runner state remain cheap projections.
    Expensive, provider-specific, or agent-supplied diagnostics may be fetched
    explicitly from the selected Member. An on-demand refresh asks the adapter
    for machine-observable facts; `poke` is the conversational path when the
    agent itself must inspect its state and answer. The UI shows when each
    field was obtained and never represents a last-known answer as live.

## Required presentation

The Jobs table answers both questions without inference:

```text
Handler       Agent
baton.tuner   input
baton.claude  work
-             -
```

The Teams Members view carries the full participant-relative state and age.
Its compact table is conceptually:

```text
Member        Role   Agent   State   Work  Session       Since
baton.codex   rview  codex   work    W93   019ff3f9…     00:42
baton.tuner   tuner  codex   input   W22   01a01552…     04:31
baton.claude  impl   claude  idle    -     72a241a9…     01:08
```

Member details expose the full session locator, configured runner, provider,
model when reported, last state transition, last contact, and actionable
reason. They also expose the participant's current Work/action inventory and
safe local diagnostics such as the readiness target and log locator. Inbox
contains only runtime states that require the viewer to act;
ordinary `working` and `idle` transitions do not create notification noise.

For the motivating incident, the visible sequence is:

```text
baton.tuner  working        W22
baton.tuner  waiting-input  W22  command approval required
baton.tuner  working        W22
baton.tuner  idle           -
```

## Acceptance boundary

- The Codex dispatcher maps its existing interactive-request event into
  `waiting-input` without answering or approving it.
- ACP adapters map equivalent explicit session/provider events through the
  same vendor-neutral authority surface.
- A lease expiry yields `unknown` or `offline`, never `failed` or `stuck`.
- Jobs, Teams, and Inbox consume one canonical projection rather than parsing
  bridge logs independently.
- Members exposes the full session locator and enough runner metadata that an
  operator does not need `codex-event-bridge --list-threads` or ACP logs merely
  to identify the active session.
- Member diagnostics identify their source and freshness, refuse stale runner
  overwrite, and omit secrets even when the launcher configuration contains
  them.
- On-demand refresh and poke paths can enrich a Member without making the
  basic Teams/Jobs projections dependent on slow provider calls.
- Regression coverage includes approval wait/recovery, slow silent work,
  disconnect/reconnect, stale-runner replacement, rate limiting, no Handler,
  and a terminal Work whose former runner is still alive.

## Revalidation against the current tree — 2026-08-19

The in-flight W25 Teams projection already provides the configured roster,
roles, route coverage, canonical held Work, and the member's most recent
structured poke answer. That answer is an on-demand agent report; it is not a
live runner state and must remain independently visible as such.

The Codex dispatcher already observes target load/idle/active status, turn
start and completion, disconnect, protocol errors, and exact interactive
requests such as `item/commandExecution/requestApproval`. Its status snapshot
is process-local and currently writes none of those facts to Baton. The ACP
bridge likewise owns exact session and child-process lifecycle but has no
vendor-neutral authority surface on which to publish it.

Schema 22 has no participant runtime/session table. W93 therefore requires a
fresh authority schema; it is not a compatible projection-only change and no
live database migration is part of this Work.

## Implementation boundary

### Canonical runtime session

One configured participant has at most one current runtime lease. Starting a
runner records an opaque runner incarnation, agent/adapter family, optional
provider/model, exact session locator, optional operational action owner, and
safe configured diagnostics. State updates name the exact lease; after a new
incarnation supersedes it, the old runner's writes fail closed rather than
restoring stale state.

The current row is a projection aid, while every meaningful state transition
is retained in the append-only event journal. A replacement is explicit and
reasoned. Ordinary state reports never claim, heartbeat, release, pass,
re-phase, block, or close Work.

### State and freshness

Adapters publish explicit transitions into `idle`, `working`,
`waiting-input`, `retrying`, and `failed`. They publish last contact and a
bounded lease deadline. Reads may derive `unknown` or `offline` after the
deadline, but expiry performs no background write and is never described as
failure or a stuck agent.

An update may correlate the runner with one current Work/action episode, but
the canonical Handler remains the Work table. Any disagreement is shown; the
runtime report never overwrites workflow authority.

### Actionable input

A `waiting-input` report carries a closed reason category, short safe
explanation, and optional session locator. When the runner configuration names
an exact operational action owner, that participant sees one owed runtime item
in Inbox. With no action owner it remains visible in Teams and the Jobs
`Agent` cell but creates no guessed team-wide obligation.

Resolving the provider request advances the same leased runtime session back
to `working`, `idle`, `retrying`, or `failed`; it does not require a Work
message. The adapter never approves the request itself.

### Live versus requested facts

The runtime lease carries only facts the adapter can publish cheaply and
continuously. The existing `poke`/`poke-answer` path remains the on-demand
agent report for model, provider, context, auth, limits, believed Work, and a
human explanation. A later adapter-only refresh command may request fresh
machine facts without waking the model, but W93 must not duplicate poke state
or turn every optional diagnostic into a heartbeat write.

### Delivery slices

1. Fresh-schema runtime lease, strict transitions, read projections, and
   stale-writer/refusal tests.
2. Codex and ACP publishers mapped onto the same semantic state vocabulary.
3. Jobs `Agent`, Teams Member details, and actionable Inbox projection, built
   after W25's Jobs/Teams/Inbox foundation is reviewed and stable.
4. End-to-end tests for the motivating approval wait plus disconnect,
   replacement, rate-limit, slow-work, on-demand poke, and secret-redaction
   cases.
