# Finding: normalize worker telemetry and introspection

**Status:** confirmed v12 hardening/enhancement; independently scheduled and
not on the first-useful-dogfood critical path

**Binding:** `baton:work/records/2026/08/finding-worker-telemetry-introspection`

**Canonical Baton Work:** `W39649`

**Roadmap:** `work/records/2026/08/finding-v12-isolated-agent-workers/`, M4
agent/runtime certification

**Prior contract:**
`work/records/2026/08/finding-v12-manager-agent-session-protocols/`

## Confirmed requirement — 2026-08-29

V12 must preserve the operational telemetry that interactive agent clients
often expose through commands such as `/status`: runtime and session state,
provider and model identity, context consumption, account limits,
authentication state, last contact, and actionable failure information.
Operators should not need to attach to an agent's private console merely to
determine whether it is working, out of context, rate-limited,
unauthenticated, or unreachable.

This extends the already accepted manager-owned `probe`/`inquire` split. A
`probe` is a control-plane observation and consumes no model turn. An `inquire`
is an explicitly requested conversational turn with a separately correlated
answer. Provider telemetry never becomes workflow authority, a claim,
permission, cancellation, or proof that Work is complete.

## Confirmed adapter boundary

The outer Worker Manager contract is provider-neutral. Each agent driver uses
the strongest native structured surface available and translates it into one
bounded status projection. ACP is one driver protocol, not a requirement that
every inner agent must implement.

The normalized projection must be able to represent, with explicit provenance
and observation time:

- runtime and session state;
- agent/provider type, model, session identity, and active Work/attempt identity;
- context used and context limit when reported;
- account or provider quota windows, percentage used, reset time, and a typed
  reached/limited state when reported;
- authentication state and plan/account class when safely reported;
- last contact, last activity, last error, and the adapter/source that observed
  each fact.

Every field admits `unknown` or absence. Unknown means the adapter cannot prove
the fact; it never means healthy. Push notifications are the primary freshness
source. An explicit probe may query the native control plane and return the
latest bounded snapshot. V12 must neither scrape terminal-rendered `/status`
screens nor ask a model to narrate facts its control plane already exposes.

## ACP driver

For native ACP agents, consume stable structured `usage_update` notifications
for session context use (`used`, `size`) and optional cumulative cost. Retain
advertised command updates so the adapter knows which conversational commands
the agent actually supports. If an agent advertises a provider-specific
`/status` command, only an explicit `inquire` may invoke it; the response is
provider text and remains non-authoritative unless a separately versioned
adapter owns and validates individual fields.

ACP does not currently standardize provider quota windows or a stable universal
authentication-status query. Those fields remain unknown unless the provider
driver has another documented structured source. Draft protocol proposals are
not treated as stable contracts merely because an SDK exposes them.

## Codex driver

Codex is integrated through its native App Server, not by pretending it is ACP
and not by sending the interactive `/status` command as a prompt. The driver
runs `codex app-server` over its default JSON-RPC/JSONL stdio transport inside
the worker and owns the version-specific generated schema.

The driver consumes or queries structured native surfaces, including:

- `thread/status/changed` for active, idle/not-loaded, and approval-wait state;
- `thread/tokenUsage/updated` for active-thread context use;
- `account/read` and `account/updated` for authentication and plan facts;
- `account/rateLimits/read` and `account/rateLimits/updated` for quota windows,
  percentage used, reset time, and reached-limit classification;
- `model/list` plus active-thread configuration for model identity; and
- turn completion/failure notifications for actionable last-error state.

The Codex probe therefore does not consume prompt tokens or require model
cooperation. If a Codex version does not expose one expected field, the driver
reports it as unknown with protocol/version provenance rather than scraping
CLI output or guessing.

## Other non-ACP agents

An agent with another native control API receives its own bounded driver. A
CLI-only agent may initially report process/runtime health, exit status, last
contact, and explicitly unknown provider fields. Optional provider commands may
be used only through conversational `inquire` unless they offer a documented
machine-readable control operation. Lack of telemetry is a visible capability
limitation, not permission to fabricate or parse unstable terminal output.

## Scheduling and campaign organization

This is later-pass hardening/enhancement under M4. It does not gate the current
first-useful v12 dogfood Work unless an observed telemetry defect makes that
positive result false.

The corresponding Job title deliberately describes the capability rather than
carrying a `V12` prefix. When generic Work labels are available, label `v12`
is the natural campaign organizer. The current v11 authority cannot store that
label, so no title prefix is treated as a substitute for it.

## Independent schema baseline — 2026-08-29

**Observed — ACP 1.3.0 stable schema.** The repository-pinned
`@agentclientprotocol/sdk` stable schema defines `usage_update` with required
`used` and `size` token counts and optional cumulative `cost`; it also defines
`available_commands_update`. This supports the proposed ACP mapping without
adopting the SDK's separately marked unstable schema.

**Observed — installed Codex App Server stable generated schema.** A schema
generated without `--experimental` exposes all of the named structured
surfaces: `thread/status/changed`, `thread/tokenUsage/updated`,
`account/read`, `account/updated`, `account/rateLimits/read`,
`account/rateLimits/updated`, `model/list`, and `turn/completed`. The default
App Server transport is `stdio://`. `turn/completed` itself carries
`completed`, `interrupted`, or `failed` status and a structured error on
failure; a separate guessed `turn/failed` method is neither needed nor named
by this record.

**Confirmed refinement — sparse updates are not replacement documents.** The
stable `account/rateLimits/updated` schema explicitly describes a sparse
rolling update. The driver must merge present values into the last complete
`account/rateLimits/read` snapshot or refetch it. An absent nullable member in
an update does not clear a previously observed value, and a process restart
with no full snapshot begins at unknown rather than reconstructing one from a
delta.

**Confirmed refinement — provider identity is not operator telemetry.**
`account/read` may include the ChatGPT account email. The normalized projection
must discard email, workspace/account identifiers, tokens, auth URLs, credit
balances and backend-provided free-form account metadata. Authentication mode
and bounded plan class may be mapped; the identity that authenticates them
must not be persisted as diagnostics.

**Confirmed refinement — status variants stay distinct.** Codex thread status
distinguishes `notLoaded`, `idle`, `systemError`, and `active`; active status
can separately flag `waitingOnApproval` and `waitingOnUserInput`. The outer
projection must not collapse user-input wait into approval wait or report
`systemError` as merely offline. Unknown remains the answer when a certified
version lacks one of these variants.

## Confirmed coarse liveness telemetry — 2026-09-02

The normalized projection also carries privacy-preserving evidence that a
running worker is still making progress. Where the runtime adapter can observe
it, one bounded sample reports:

- CPU use over a named sample interval;
- cumulative and interval network receive/send byte counts; and
- agent-log byte size, byte growth since the prior sample, and last-change
  time.

Each value carries the same source, observation time and unknown/stale
semantics as the other telemetry. An adapter that cannot observe one of these
facts reports it as unknown; it does not infer zero. Counters and deltas are
bounded non-negative quantities, and a restart or counter reset begins a new
sample series rather than manufacturing a negative delta.

This is deliberately metadata, not log disclosure. The status projection
does not include log content, credential content, environment values, command
arguments, authentication identity, or an implicit credential/log locator.
An operator can use changing CPU, network counters or log size as evidence
that a quiet worker remains alive without opening its private transcript.
Conversely, one quiet sample is not proof of a wedge and never authorizes an
automatic kill, release, reassignment or acceptance. A later automated
"likely wedged" policy, if added, must name its sampling window and thresholds
explicitly; these measurements remain non-authoritative observations.

## Acceptance boundary

- One provider-neutral, bounded, provenance-bearing status projection.
- ACP usage and command capability updates mapped without depending on draft
  fields as stable protocol.
- Codex App Server structured state, usage, auth, quota, model, and failure
  surfaces mapped through a version-owned driver over stdio.
- `probe` remains control-plane-only; `inquire` remains conversational and
  correlated; neither changes workflow state by implication.
- Unknown, stale, unsupported, unauthenticated, limited, failed, and offline
  remain distinguishable.
- CPU, network traffic and agent-log growth are available as bounded,
  provenance-bearing metadata where supported, without exposing log or
  credential content and without becoming an automatic wedge verdict.
- No terminal-screen scraping, credential persistence, secret-bearing durable
  diagnostics, or provider-specific fields leaked into the outer contract.
- Focused conformance covers replay, restart, stale updates, unsupported
  capabilities, sparse-update merge/refetch, redaction, version drift, and
  provider loss.
