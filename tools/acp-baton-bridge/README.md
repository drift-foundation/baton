# acp-baton-bridge

The external ACP readiness client (W163, `finding-v11-acp-agent-bridge`):

```text
baton wait JSON -> acp-baton-bridge -> ACP agent over JSON-RPC/stdio
```

Baton stays model-neutral and owns only participant-relative readiness
and canonical JSON. This program owns ACP initialization, session
selection, prompt submission, streamed updates, the ruled permission
boundary, and process supervision. It is agent-generic: Claude, Gemini,
or any conforming ACP agent differ only in deployment configuration —
no Baton parsing or action semantics change per agent. It is read-only
with respect to readiness: it never claims Work, answers obligations,
advances cursors, or closes anything for the agent. It is not part of
Baton core or the immutable Baton client distribution.

## Protocol

Pinned SDK: `@agentclientprotocol/sdk` 1.3.0 (official TypeScript ACP
SDK; ACP v1, NDJSON over the agent subprocess's stdin/stdout). The
schema and transport come from the SDK's exported types and
`ndJsonStream` — no JSON-RPC field is hand-coded. The Baton envelope is
validated by the SAME shared envelope gate as `codex-baton-bridge`
(imported, not re-typed): protocol 11, the projection major that gate
currently pins, participant match, snapshot token, and typed action
kinds — anything else refuses by name and nothing reaches the agent.
The major is deliberately NOT restated here; it moves with the
canonical projection, and a number frozen in prose is a second source
of truth that goes stale silently.

## Configuration

Everything is explicit deployment configuration; no executable, path,
or model identity is inferred:

```json
{
  "baton": {
    "binary": "/home/sl/opt/baton/v11/<CANDIDATE>/bin/baton",
    "config": "/home/sl/baton-v11/baton.json",
    "participant": "baton.claude",
    "role": "impl",
    "waitTimeoutSeconds": 60
  },
  "agent": {
    "command": "/absolute/path/to/claude-agent-acp",
    "args": [],
    "env": {},
    "cwd": "/home/sl/src/baton"
  },
  "session": { "mode": "load", "cwd": "/home/sl/src/baton" },
  "permissionMode": "bypassPermissions",
  "policyResources": [
    "/absolute/path/to/agent-policy/settings.json"
  ],
  "stateDir": "/home/sl/.local/state/acp-baton-bridge/baton.claude"
}
```

- `session.mode` is `new` (bootstrap; the returned session id is
  persisted in `stateDir/session.json`) or `load` (resume exactly the
  persisted session; refused before any session use when the agent does
  not advertise `loadSession`). The bridge persists only its own
  session selection — never agent history, never Baton authority state.
- `baton.role` selects one role held by `baton.participant` and is REQUIRED,
  even when that participant holds exactly one role. Inferring it would mean
  that giving the participant a second role later silently changed the persona
  of every session launched here. Before any session creation or load, the
  bridge resolves the accepted instruction projection through the configured
  Baton executable; a missing or unheld role fails closed. ACP has no
  developer-instruction field, so the resolved text rides every supervised
  readiness prompt, including the first.
- `permissionMode` is the exact operator-selected ACP session mode
  (the ruled trial mode is `bypassPermissions`). The bridge requires it
  among the agent's advertised modes and selects it after new/load; a
  missing or unsupported mode fails visibly with no fallback to
  prompting or any other mode.
- `policyResources` names the deployment-owned prohibition resources
  (for Claude: the Agent-SDK `disallowedTools` settings and blocking
  `PreToolUse` hook configuration). The bridge does not parse or own
  that vocabulary; it verifies each resource exists and is readable and
  REFUSES to start otherwise — prohibitions are hard denials beneath
  the bypass mode, enforced by the agent-side deployment. When the
  deployment uses a sandbox launcher with a protected-paths list, the
  entries must identify ACTUAL Git metadata paths: an ordinary
  checkout's `.git` directory, or — for worktree-style checkouts where
  `.git` is a file — the RESOLVED gitdir
  (`git rev-parse --absolute-git-dir`). An empty or comment-only list
  refuses the launch rather than starting an uncontained agent.
- One configured participant has one readiness path and one session.
  Different agents use separate participant identities, sessions, state
  directories, and bridge processes.

## Behavior

Level-triggered whole-set delivery exactly like the Codex bridge: one
compact `[BATON READY]` prompt per previously unseen action key
(identity: authority uuid + participant + action key), suppressed while
present, forgotten when it disappears, delivered again if it returns.
Busy sessions serialize ordinary wakes — one turn at a time, never
steered. An unexpected ACP permission request while the configured
bypass mode is active is answered `cancelled` and reported as a
policy/protocol failure; it is never auto-approved. Streamed agent
output and genuine elicitation go to the foreground surface. Process
exit, malformed JSON-RPC, unsupported capability, and session-load
failure are visible and retried without discarding current readiness.
The prompt includes the role instructions from the accepted Baton generation;
an operator-authored one-off persona prompt is not part of the normal path.

## Run

From a source checkout:

```bash
tools/acp-baton-bridge/bin/acp-baton-bridge --config /path/to/config.json
```

From a deployed v11 release. The bridge CO-DEPLOYS with the v11
distribution — `just deploy-v11 TARGET` publishes it ready to run —
while the agent adapter itself, its credentials, its session state, and
the deployment's prohibition policy stay DEPLOYMENT-OWNED and are never
packaged here:

```bash
<TARGET>/bin/acp-baton-bridge --config /path/to/config.json
```

The deployed runtime lives in `<TARGET>/lib/acp-baton-bridge` with its
pinned dependencies ALREADY RESOLVED during candidate construction —
the release runs without this checkout, npm, or network access, and
`<TARGET>/conf/` carries the non-secret Claude/Gemini example configs.
Node >= 20 remains the only runtime requirement.

`--once` exits after the first delivered wake (useful for smoke
proofs). Node >= 20 is required (pinned in `package.json` engines).
Tests: `npm test` in this directory — and the repository's single
operator gate `just test-v11` runs the same acceptance through its
`test-acp` sub-gate, installing the pinned SDK deterministically from
the committed lockfile when absent. The suite drives the full
acceptance against a real fake-agent subprocess speaking the same SDK
(lifecycle ordering, compact prompt delivery, level-triggering, busy
serialization, permission-cancel policy, crash/malformed retry with
readiness preserved, participant isolation, session load continuity,
fail-closed mode/capability/policy refusals across repeated retries,
hard-denial-without-side-effect and broken-policy fail-closed paths,
setup deadlines for unresponsive agents, prompt shutdown teardown, and
missing-executable spawn failure).

## Status

Slice A (generic client + fake-agent acceptance), Slice B (live Claude via the
separately installed `claude-agent-acp` adapter with fail-closed bypass policy),
and immutable co-deployment are independently signed off. A live Gemini run
through `gemini --acp` remains roadmap follow-up Work; the shipped Gemini
configuration is deliberately inert and does not claim live certification.
