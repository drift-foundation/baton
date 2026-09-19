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

## The turn deadline and the process domain (W28681)

`turnTimeoutMs` is REQUIRED and has no default. It is the wall-clock bound
on one delivered turn, and it must be at most **2147483647** ms (about 24.8
days) -- the longest interval this runtime's timers hold. A larger value is
REFUSED rather than clamped: Node truncates it to one millisecond, so the
longest deadline an operator can express would silently become the shortest
there is, and substituting a number of this repository's choosing is exactly
what giving the operand no default was meant to avoid.

Every other timeout here has a default because a wrong guess is merely
slow. A wrong guess here either kills legitimate long work or leaves a
managed lane held indefinitely, so the value is deployment policy and a
configuration that has not chosen one does not start.

It is wall-clock rather than an activity reset, deliberately. A legitimate
tool may be silent for a long time, and an infinite but talkative one can
produce ACP updates forever -- so streamed updates are diagnostics and never
extend the deadline.

**One agent process domain serves at most one delivered turn.** On success,
failure, deadline, cancellation, session replacement and shutdown, the bridge
destroys that domain and positively awaits its exit BEFORE anything is
settled: no `idle` beside a live domain, and no replacement started beside
one. A deadline is terminal for the delivery and is reported through the
existing typed `failed`/`cause=internal` with its `(work, episode, session)`
correlation; there is no second runtime state for it.

If the exit cannot be proved, the bridge FAILS CLOSED: the readiness key is
retained, the lane is fenced, no `idle` is published and no replacement
process starts.

ACP session continuity is not process continuity. The run retains one session
id and a replacement process resumes it with `loadSession`; no rotation rule
changes.

**The configured `agent.command` must be a descendant-owning process
domain.** This program is ACP-generic and does not parse the configured
command, so it cannot check that -- the deployment's own verifier does. The
incident behind this Work found five tool process groups outliving their
managed agent by 34-36 hours; four had called `setsid`, so they were in
neither the bridge's process group nor its session. A `setsid` call escapes a
process group and a session and does not escape a PID namespace, so the
shipped Claude/pc.code launcher runs bubblewrap with `--unshare-pid`
(bubblewrap becomes the namespace's PID 1 reaper) and `--die-with-parent` in
addition to its mount boundary. A direct executable, or a mount-only
bubblewrap command, is not an accepted managed configuration.

Whether a given host permits an unprivileged PID namespace is a property of
the SERVICE LAUNCH CONTEXT and cannot be established from inside a nested
sandbox. Run `preflight-process-domain.sh` from that context before
installing; it exits non-zero and names the refusal rather than passing
vacuously.

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
  "runtime": {
    "actionOwner": "baton.slaw"
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
  "stateDir": "/home/sl/.local/state/acp-baton-bridge/baton.claude",
  "turnTimeoutMs": 3600000
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
- The Baton launcher contract — `BATON_BIN`, `BATON_CONFIG`,
  `BATON_PARTICIPANT`, `BATON_ROLE` — has ONE source and TWO carriers, and the
  source is the accepted `baton` section above. A context may not infer any of
  the four from a repository path, a deployment symlink, remembered history,
  another participant, a persistent bootstrap or load file, or a filesystem
  search.

  **The prompt carries it.** Every supervised readiness prompt — Work,
  obligation, trial and poke, in both `new` and `load` — ends with the same
  JSON-quoted block the Codex family renders, from the same shared pure
  renderer. This is the carrier a fresh model actually reads, and it exists
  because it once did not: after a healthy restart the rendered runtime
  context held the correct four values, the prompt named none of them, and
  the model went looking and found a persistent participant `load.json` still
  pinned to a retired deployment. Its first claim went through the wrong
  executable and failed while the authority still showed Work claimed by that
  participant (W14828).

  **The spawned environment carries it too**, DERIVED from the same `baton`
  section rather than supplied beside it. `agent.env` need not spell the four
  keys — templates may omit them entirely — and the derived values also
  override anything the parent process exported, because a stale ambient
  `BATON_BIN` is the same untrusted carrier as a stale file. An operator may
  still spell them for legibility, but only to the SAME values: a conflicting
  entry refuses startup by key rather than being resolved in favour of either
  side. Two spellings of one contract is the drift, not the fix.

  The Codex-backed adapter carries the same four values through
  `developerInstructions`, because one app-server process hosts every Codex
  target and its start/resume contract has no per-thread environment — see
  that bridge's README (W12229). The shared role-instruction reader both
  families use returns accepted role prose ALONE, so the launcher block is
  composed beside it rather than inside it.
- `runtime.actionOwner` is REQUIRED and names the explicit recovery or
  operations participant that receives this runner's actionable incidents.
  It must be a `team.member` address different from `baton.participant`.
  The bridge refuses a missing or self-addressed owner during configuration
  validation; it never infers one from the runner, Route, role, ACP session,
  or runtime telemetry. This matters after every action kind, including a
  poke: if an ACP turn returns while the participant still holds a canonical
  Work claim, the bridge publishes `failed`, retains a durable settlement
  fence, and files one incident instead of publishing `idle` over that claim.
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

Level-triggered whole-set delivery exactly like the Codex bridge, and
level-triggered against CANONICAL state: one compact `[BATON READY]`
prompt per actionable key (identity: authority uuid + participant +
action key).

An obligation, trial or poke is suppressed while present, forgotten when
it disappears, and delivered again if it returns.

A **ready unclaimed Work is an OFFER**, and the exact successful atomic
`claim` is what clears it (W11910,
`work/records/2026/08/finding-readiness-offer-cleared-before-claim/`). A
returned prompt is TRANSPORT acknowledgement: the wake reached the
agent, and the agent may well have finished the turn without claiming
anything. So:

- the offer stays armed while canonical state reports `ready &&
  unclaimed`, and is presented again under a bounded exponential retry
  (from `retryMs`, capped at 60s) — recovery never needs a restart;
- canonical `claimed:true` for that key acknowledges it, and no second
  turn is spent on it while the claim stands;
- while the participant holds ANY claim, unclaimed offers wait locally
  rather than interrupting a busy agent, and the first retained offer
  becomes eligible when the slot frees;
- at most one unclaimed Work is admitted per poll, in canonical order,
  and here presentation happens AFTER the prompt returns — so the head's
  claim-slot outcome is already known and the next offer may rotate in;
- a Work first seen ALREADY claimed is delivered once, which is the
  claimed-Work restart recovery contract — and once means once it has
  actually been delivered: a recovery prompt that FAILED stays eligible,
  because the claim it was going to recover cannot acknowledge a wake
  nobody received;
- a key that stops being actionable — blocked, rerouted, parked,
  superseded, closed, or a changed episode/configuration generation —
  withdraws the retained offer.

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
proofs). It proves the TRANSPORT path — configuration, session
selection, prompt delivery — and deliberately not the claim loop:
acceptance of one prompt is not claim acknowledgement, so `--once`
certifies nothing about the retained-offer retry the production loop
runs. Node >= 20 is required (pinned in `package.json` engines).
Tests: `npm test` in this directory — and the repository's single
operator gate `just test-v11` runs the same acceptance through its
`test-acp` sub-gate, installing the pinned SDK deterministically from
the committed lockfile when absent. The suite drives the full
acceptance against a real fake-agent subprocess speaking the same SDK
(lifecycle ordering, compact prompt delivery, claim-based offer
clearing and one-at-a-time Work admission, level-triggering, busy
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
