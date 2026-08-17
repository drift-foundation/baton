# Plan

**Status — 2026-08-17:** closure-ready. Slices A and B and immutable
co-deployment are independently signed off. Slawomir superseded the live
Gemini closure gate: Gemini is roadmap follow-up Work, not unfinished W163
scope. Close W163 satisfying after recording this disposition.

1. Inventory the installed Claude ACP entry point and obtain the authoritative
   ACP schema/capability definitions; document Gemini's native ACP entry point
   without requiring its installation in this Work.
2. Specify a small external ACP client boundary that consumes canonical v11
   readiness without importing model behavior into Baton.
3. Define explicit configuration for agent command, participant, workspace and
   persistent session selection.
4. Build a fake ACP agent harness and cover initialization, prompt streaming,
   permissions, busy serialization, restart and isolation failures.
5. Prove Claude continuity and preserve the agent-neutral configuration
   boundary plus inert Gemini example for the roadmap follow-up.
6. Independently review the adapter and live Claude evidence before treating
   v11 as Claude's replacement wake path.

## Proposed implementation slices after the permission ruling

### A — protocol client and fake agent

- Add a small external `acp-baton-bridge` program beside the existing Codex
  bridge, using the pinned official TypeScript ACP-v1 SDK. Package the generic
  executable and its pinned runtime dependencies as a reusable product in the
  immutable Baton distribution; it remains a separate process, not Baton core.
- Ship non-secret Claude and Gemini example configurations with explicit
  placeholders for every deployment-owned path, identity, workspace, state
  directory and policy resource. Examples must fail validation until
  deliberately instantiated; no credentials or permissive live defaults.
- Keep Baton readiness parsing isolated from ACP process/session handling.
  Agent command, arguments, environment, cwd, participant and session policy
  are explicit configuration; no executable or path is inferred.
- Implement a fake ACP agent that proves initialize-before-session,
  capabilities, new/load, prompt streaming, permission requests, malformed
  messages, process exit, busy serialization, retry and participant isolation.
- Persist only bridge-owned session selection and readiness/dedup state in an
  explicit local state directory. Never write agent session history or Baton
  authority state.
- Model permission mode and required policy resources explicitly in deployment
  configuration. Require the negotiated mode, fail closed on missing policy,
  cancel unexpected permission requests, and expose genuine elicitation through
  the foreground operator surface.
- Prove permitted-without-prompt and prohibited-without-side-effect paths in the
  fake harness, including unsupported mode, missing policy, blocking-hook
  failure and no-fallback cases.

### B — real Claude adapter

- Install/version the official `claude-agent-acp` adapter separately from the
  Baton distribution and configure its exact command.
- Prove one existing configured session can be loaded, receives a Baton wake,
  preserves a continuity marker, streams visible output and uses the selected
  explicit bypass mode while deployment `disallowedTools`/`PreToolUse` policy
  still rejects representative forbidden commands such as `git commit`.

### Roadmap follow-up — Gemini by configuration

- Install/version Gemini CLI separately and point the same client at
  `gemini --acp`; no Baton parser or action change is allowed.
- Repeat session continuity, permission, serialization, restart and isolation
  acceptance as separately scheduled follow-up Work. W163 does not claim this
  live proof and does not wait for it to close.
