# Finding: non-Codex agents need one ACP readiness bridge

## Parent

`finding-v11-messaging-cutover-gate` — this sibling follows the Codex-specific
W148 bridge and reuses the canonical v11 participant-relative `wait` contract.

## Decision — 2026-08-16

Claude must receive v11 Baton readiness through Agent Client Protocol (ACP),
using JSON-RPC over the agent process's standard input and output. The adapter
must be ACP-generic rather than Claude-specific so that another conforming
agent, including Gemini, can be configured without adding another Baton
protocol adapter.

This does not move model machinery into Baton. The boundaries are:

```text
baton wait JSON -> external ACP readiness client -> ACP agent over stdio
```

- Baton remains model-neutral and owns only participant-relative readiness and
  canonical JSON.
- The external client owns ACP initialization, session selection, prompt
  submission, streamed updates, permissions and process supervision.
- Agent command, arguments, environment, participant and session selection are
  deployment configuration. No filesystem path or model executable is inferred.
- One configured participant has one readiness path. Different ACP agents use
  separate participant identities and sessions even when one supervisor owns
  several subprocesses.
- The bridge is read-only with respect to readiness. It does not claim Work,
  answer obligations, advance cursors or close anything for the agent.
- Sandbox and approval requests remain on the ACP permission path; automatic
  approval is not a compatibility mechanism.
- Codex continues to use `codex-baton-bridge` and Codex app-server. ACP is the
  shared path for Claude and other ACP-capable agents, not a replacement forced
  onto Codex during this cutover.

ACP currently defines local agents as subprocesses communicating with their
client through JSON-RPC over stdin/stdout. Gemini CLI exposes that mode with
`gemini --acp`; Claude is available through the ACP project's Claude Agent
adapter. Those executable details remain replaceable deployment choices, not
part of the Baton contract.

## Open implementation questions

- Select the ACP SDK and pin the exact stable schema supported by the installed
  agent adapters; do not hand-code fields from an example.
- Decide how configured sessions are loaded or resumed after bridge restart.
  Session continuity must be proven rather than assumed across agents.
- Define whether one supervisor hosts several ACP subprocesses or each
  participant launches an independent bridge. Either shape must preserve
  participant/session isolation and visible failure.
- Name the external program after its protocol boundary. The public name must
  not imply that it is part of Baton core or tied only to Claude.

## Acceptance boundary

The first implementation must prove:

1. ACP initialize and capability negotiation complete before any session use.
2. A v11 readiness action prompts the already configured Claude session.
3. The same client code can drive a Gemini ACP process by changing deployment
   configuration, without changing Baton parsing or action semantics.
4. Two participants cannot cross-deliver readiness or conversation context.
5. Busy sessions serialize ordinary Baton wakes; they are not steered by
   default.
6. Permission requests remain visible and require the configured human/runner
   decision path.
7. Process exit, malformed JSON-RPC, unsupported capability and session-load
   failure are visible and retried without discarding current readiness.
8. A live continuity marker survives an external Baton-triggered turn in the
   intended session.

Protocol references used to establish the transport boundary:

- <https://agentclientprotocol.com/get-started/architecture>
- <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/acp-mode.md>
- <https://github.com/agentclientprotocol/claude-agent-acp>

## Revalidation — 2026-08-17

### Observed locally

- `/home/sl/.local/bin/claude` is Claude Code 2.1.231. Its installed command
  exposes stream-JSON print mode but no native ACP-agent mode.
- No `claude-agent-acp` executable is installed. The official external adapter
  is the npm package `@agentclientprotocol/claude-agent-acp`; its published
  executable is `claude-agent-acp`.
- No `gemini` executable is installed on this machine.

The live two-agent acceptance therefore cannot be claimed from the current
host. A fake ACP agent can prove the generic client, and Claude can be the
first real integration after its separately versioned adapter is deliberately
installed. Gemini remains a live acceptance gate rather than something a
Claude-shaped fake may silently satisfy.

### Confirmed protocol facts

ACP v1 is the current stable protocol and v2 is draft. The official TypeScript
SDK provides the schema and NDJSON/stdio transport; implementation must import
those types and methods rather than reproduce JSON-RPC field names from this
record. Initialization negotiates the protocol version and capabilities before
session use. Both the Claude adapter and Gemini ACP implementation expose
session lifecycle operations, including load/resume support that must be
confirmed from the negotiated capability before use.

An ACP client also receives bidirectional permission requests. The upstream
Claude adapter's simple-client example auto-selects an allow option, but that
is explicitly outside this Work's accepted boundary. A headless readiness
client needs an explicit human/runner approval surface, or it must refuse the
request visibly; it may never infer approval merely because the prompt came
from Baton.

### Open decision before implementation handoff

Choose the first approval surface. This is not an implementation detail:

1. a foreground operator console that displays each ACP permission request and
   accepts an explicit response; or
2. a separate local control channel/command suitable for a supervised daemon.

Either design must preserve a pending request across ordinary readiness
polling, time out/refuse visibly, and never auto-approve. Until one is selected,
W163 remains in research rather than being handed to the implementer.

## Permission and prohibition ruling — 2026-08-17

**Confirmed by Slawomir.** Preserve today's autonomous Claude operation without
conflating two independent controls:

1. `bypassPermissions` is the explicit operator-selected ACP session mode for
   commands that are otherwise permitted. The client negotiates available
   modes, requires the configured exact mode, selects it after new/load, and
   fails visibly rather than falling back to prompts or another mode.
2. Prohibited operations remain hard denials beneath that mode. Repository
   instructions explain policy but are not the enforcement boundary. For
   Claude, deployment supplies Agent-SDK `disallowedTools` and a blocking
   `PreToolUse` hook; an OS sandbox/read-only `.git` boundary may add defense in
   depth. Other ACP agents use their corresponding deployment controls.

The ACP client remains agent-generic and does not parse shell commands or own
the prohibition vocabulary. It validates that its configured policy resources
exist and launches the configured adapter; missing/unreadable required policy
causes startup to fail. Agent-specific settings are explicit opaque deployment
configuration, never Baton protocol fields.

An unexpected ACP permission request while the configured bypass mode is
active is cancelled and reported as a policy/protocol failure; it is never
silently allowed. The foreground console remains useful for streamed activity
and genuine agent elicitation/questions, not repetitive command approvals.

Acceptance must prove both halves together: representative permitted commands
run without a prompt, while every configured prohibited operation (including
Git-history/index mutations such as `git commit`) is denied without side
effect or approval prompt. Missing policy, unsupported bypass mode, hook
failure and attempted fallback all fail closed.

## Distribution ruling — 2026-08-17

**Confirmed by Slawomir.** The generic `acp-baton-bridge` is a reusable Baton
deployment product and is co-deployed with the Baton distribution. It remains
a separate executable and process boundary rather than Baton protocol/core
logic, but an operator installing Baton must not have to build or obtain this
generic bridge from the source checkout.

Agent-specific ACP servers/adapters, models, credentials and prohibition
policies are not bundled into Baton. Claude installs a pinned
`claude-agent-acp` adapter and deployment-owned policy; Gemini supplies its
native ACP entry point and corresponding policy. Separate participant/team
bridge instances select those dependencies through explicit configuration.

The distribution includes non-secret example bridge configurations for Claude
and Gemini. Each example shows the complete supported shape while using
deliberate placeholders for the Baton executable/config, participant, agent
executable, workspace, state directory and required policy resources. Examples
must not contain credentials, host-specific inferred paths, or permissive
defaults that can run before the operator supplies and validates the real
deployment values. Agent-policy examples may document the required boundary,
but the active policy remains deployment-owned.

This supersedes any Slice A wording that says the generic bridge is not part
of the immutable Baton client distribution. It does not supersede the boundary
that ACP remains outside Baton core or the decision to install agent-specific
adapters separately.

## Acceptance supersession — 2026-08-17

**Confirmed by Slawomir.** A live Gemini run is roadmap work, not a W163
acceptance requirement. W163 may close satisfying once the ACP-generic client,
fake-agent protocol matrix, real Claude integration, permission/prohibition
boundary, immutable co-deployment, and inert Claude/Gemini configuration
examples are independently signed off.

This explicitly supersedes acceptance item 3 above only as a CLOSURE GATE, the
Revalidation statement that Gemini “remains a live acceptance gate,” the Plan's
Slice C statement that W163 cannot close without a real Gemini substitute, and
the equivalent forward-looking statements in earlier append-only reviews.
Those records remain accurate history of the former boundary. The architecture
continues to be ACP-generic and the Gemini example continues to ship, but an
installed Gemini CLI and its live continuity/policy proof will be scheduled as
new follow-up Work when that roadmap item is taken up.
