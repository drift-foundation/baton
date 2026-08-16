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
