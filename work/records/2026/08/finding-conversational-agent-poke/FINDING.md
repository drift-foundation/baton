# Finding: conversational agent poke

## Status

Confirmed feature direction on 2026-08-18. This is distinct from Baton's
automatic scheduler wake and from readiness redelivery.

Authoritative Baton Work: `W197` (`bec445ce-W197`).

## Problem

An operator may see an apparently idle or stalled participant and need to ask
the live agent what is happening. Creating a Work dependency, workflow
transition, or directed Work obligation merely to wake that agent falsifies
the coordination record. Restarting a runner is also too strong when the
session may be healthy but quiet.

## Confirmed behavior

Provide a conversational `poke` for one named participant. It wakes that
participant's runner with the equivalent of "what's up?" and expects a short
state report such as:

- what Work, if any, the agent believes it is handling;
- what it is currently doing or waiting on;
- whether it needs an operator decision or recovery action.

`poke` is operational conversation, not workflow authority. It does not
claim, release, pass, reprioritize, re-phase, block, close, or make Work
actionable. It does not substitute for correcting stale scheduler state. The
response must report canonical Baton state separately from the agent's own
explanation so disagreement remains visible.

The interaction is deliberately friendly and ordinary: a lightweight request
for status between collaborators. It is not an alarm, escalation, accusation,
failure declaration, or automated health verdict, and its wording and UI must
not imply otherwise.

Answering a poke includes a fresh read of canonical Baton state. An agent that
believed itself idle may therefore notice actionable Work or an obligation it
missed, report that discovery, and claim or answer it through the ordinary
protocol. The poke does not perform that claim or answer on the agent's behalf
and does not bypass eligibility, gates, or compare-and-swap checks.

## Boundary to retain

- Automatic gate satisfaction and Work readiness remain authority behavior.
- Readiness redelivery asks a runner to re-read already-actionable state.
- Heartbeat is liveness evidence from a participant already holding a claim.
- Poke wakes a participant for a conversational status answer even when it
  has no actionable Work.

## Open design questions

- Whether the request/reply is persisted as an operational event or remains a
  runner-control exchange.
- Timeout, retry, rate-limit, and duplicate-poke behavior.
- How CLI/TUI status presents `delivered`, `answered`, `timed out`, and
  `runner unavailable` without pretending the agent itself is healthy.
- Whether only exact participants are targetable or routes may be resolved to
  one participant under an explicit selection rule.

## 2026-08-18 persistent poke contract — approved

Implement poke as a small persistent Baton primitive rather than a transient
runner-control socket. A Baton-level record survives an offline participant,
reaches Codex and ACP agents through the same participant-relative `wait`, and
gives the operator one vendor-neutral place to retrieve the answer. A private
runner socket would require separate Codex/ACP control implementations and
would lose the request or response when either endpoint was absent.

Proposed contract:

- `poke` targets exactly one configured `team.member`, never a route or
  wildcard, and records friendly request text with a safe default;
- participant-relative `wait` exposes the pending poke as a distinct action
  kind, without attaching it to Work or changing any Work projection;
- the awakened agent first reads its canonical obligations and Work, then
  answers with structured state (`idle`, `working`, `waiting`, or `needs-help`),
  optional Work identifiers, and a short human explanation;
- exactly one response terminally answers the poke; repeated delivery is
  idempotent and an offline participant may answer after reconnecting;
- unanswered, answered, timed-out, and cancelled states remain operational
  history outside Work Messages and Work Events;
- runner adapters only translate the common poke action and response. They do
  not define separate vendor-specific semantics.

The response has two independently observable layers:

1. **Runner/provider diagnostics.** A live runner acknowledges delivery and,
   where its adapter exposes the facts, reports provider, model, session state,
   authentication state, rate-limit/overload state, and a retry or reset time.
   This layer can explain why the model itself cannot answer—for example, a
   provider rate limiter or authentication failure.
2. **Agent status.** If the model can run, it reports canonical Baton state,
   its current activity or wait, and optional model telemetry such as context
   or token limit/usage/remaining values.

All model telemetry is capability-based and advisory. Unsupported or
unavailable fields are explicitly `unknown`, never guessed. Diagnostics must
not expose credentials, account secrets, or unrestricted vendor payloads, and
neither diagnostic layer may mutate Work.

If the runner itself is unreachable, no component may invent a provider
explanation: the poke remains unacknowledged or times out, while the separate
infrastructure status surface may report that the runner process is down.

Slawomir approved this boundary on 2026-08-18. It is the actionable W197
implementation contract and deliberately requires a schema/projection change.
