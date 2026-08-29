# ACP launcher contract can drift from the managed runtime

## Observed 2026-08-26

After a healthy managed restart of deployment `14aecfb`, the generated Claude
runtime context named `/home/sl/opt/baton/v11/14aecfb/bin/baton` and the exact
`/home/sl/baton-v11.14aecfb/baton.json`.  The fresh Claude turn instead read
`/home/sl/.config/baton/acp/baton.claude/load.json`, whose binary remained
pinned to retired deployment `fc613e3`, and attempted its first `claim` through
that incompatible executable.

The claim failed.  The authority still showed W6629 claimed by
`baton.claude`, while the restarted adapter reported work against a different,
unclaimed Work.  Restarting the managed stack therefore did not restore a
valid claim-first turn.

## Confirmed boundary

The launcher's executable, config, participant and role are one atomic runtime
contract.  A managed turn must receive the exact values rendered for that
incarnation.  It must not rediscover or prefer a persistent participant file
whose deployment pin can diverge from the generated runtime context.

## Required correction

- Deliver the rendered launcher contract directly in every ACP work prompt.
- Remove any need for the model to search persistent bootstrap/load files.
- Fail the adapter before waking the model when the rendered contract is
  absent or internally inconsistent.
- Certify a release rollover followed by a fresh ACP session and successful
  first canonical claim using the new deployment.

## Temporary recovery

An operator may repin the persistent Claude `load.json` to the exact live
deployment before restarting the Claude runner.  This is a stopgap only; it
does not satisfy the required correction.

## Reviewer revalidation — 2026-08-26

### Minimal reproduction and live split

**Observed:** deployment `14aecfb` rendered
`/home/sl/baton-v11.14aecfb/run/context/claude-acp.json` with the correct
absolute executable, config, participant, and role in its top-level `baton`
section.  Its `agent.env` did not contain any of the four `BATON_*` values.
The persistent `/home/sl/.config/baton/acp/baton.claude/load.json` still named
the retired `fc613e3` executable and the stable config symlink.

**Observed:** the fresh ACP model first opened that persistent `load.json` and
then invoked `fc613e3`.  The live bridge log records the stale command and the
resulting configuration refusal.  The same log later records a successful
claim after the model was manually redirected to `14aecfb`.  This establishes
that the generated runtime file was correct but was not a context input the
model could rely on.  The durable command excerpts and current source baseline
are in `evidence/baseline-2026-08-26.md`.

**Confirmed:** the repository reproduces the loss without any live service:

1. `validateConfig` in `tools/acp-baton-bridge/src/config.mjs` retains the four
   validated values in `config.baton`, but returns `agent.env` independently
   from the operator document.
2. `AcpAgentSession.setup` in `src/acp_agent_session.mjs` spawns the agent with
   `{...process.env, ...config.agent.env}`.  It neither derives nor checks the
   four launcher values.  A stale parent environment can therefore become a
   second unvalidated carrier when the operator template omits them.
3. `runBridge` resolves the accepted participant/role instructions and calls
   `promptText(envelope, action, role.instructions)`.  `promptText` in
   `src/baton_readiness.mjs` renders only the readiness locator, accepted role
   prose, and standing-policy cue.  It receives no launcher contract.
4. The shipped `conf/acp-claude.template.json` and
   `conf/acp-gemini.template.json` omit the four environment entries.  The
   live `baton.claude` template has the same shape.  A separately maintained
   `pc.code` template duplicates all four entries manually, demonstrating that
   the workaround is possible but not atomic with the `baton` section.
5. The current working-tree README says `agent.env` is the ACP carrier, but
   neither validation nor session setup synthesizes that carrier.  The live
   rendered file disproves the documentation claim for the managed
   `baton.claude` service.

**Observed baseline:** `npm test` in `tools/acp-baton-bridge` passes 69/69.
The existing compact-prompt test checks the readiness prefix and policy
suffix, but no test requires any launcher field in the prompt or the spawned
agent environment.  Green tests therefore reproduce the missing-coverage
condition rather than refute the defect.

### Clarification of the launcher-carrier ruling

The earlier W12229 decision correctly established the four-field launcher
contract and the no-inference rule.  Its narrower statement that ACP receives
the contract through four explicit `agent.env` values is **superseded for
carrier sufficiency** by this incident and this dossier's confirmed boundary:
every supervised ACP readiness turn receives the authoritative four-field
block directly in its prompt.  Environment delivery remains useful and must
agree, but it is not the model's only locator and may not be independently
maintained.

The accepted `baton` section is the one source for both carriers.  The exact
prompt block is the already established, JSON-quoted form used by Codex:

```text
Baton launcher contract (authoritative; do not infer):
BATON_BIN=<JSON-quoted configured binary>
BATON_CONFIG=<JSON-quoted configured config>
BATON_PARTICIPANT=<JSON-quoted configured participant>
BATON_ROLE=<JSON-quoted configured role>
Invoke BATON_BIN with --config BATON_CONFIG and --participant
BATON_PARTICIPANT for every Baton operation.
```

The block rides every ACP readiness prompt — Work, obligation, trial, and
poke, in both `new` and `load` session modes — because each can require a
canonical Baton operation.  It is rendered from the bridge's validated
configuration, never from agent history, a persistent bootstrap/load file,
ambient environment, the repository, a symlink, or message content.

### Implementation-ready boundary

**Proposed patch boundary:**

- Reuse the pure `launcherContract` renderer in
  `tools/codex-event-bridge/src/role_instructions.mjs`; do not create a second
  textual format and do not change `readRoleInstructions` to return mixed
  role/launcher prose.  Update its now-stale Codex-only carrier comment while
  preserving the reader's shared accepted-role semantics.
- In ACP startup, render the block once from `config.baton` after configuration
  validation and before the first wait or agent/session use.  Pass that block
  explicitly to `promptText` for every delivered action.  A missing field
  remains a startup refusal rather than a partial prompt.
- In `validateConfig`, materialize `BATON_BIN`, `BATON_CONFIG`,
  `BATON_PARTICIPANT`, and `BATON_ROLE` into the returned `agent.env` from the
  same validated `baton` section.  If the operator supplied any of those keys,
  require exact equality; a conflicting value refuses startup by key.  The
  derived values must override an ambient parent-process value at spawn.
- Keep the existing absolute-path, explicit-role, participant/role instruction
  envelope, and readiness participant checks.  Together they reject a missing
  or internally inconsistent contract before a model wake.  Do not inspect a
  persistent participant `bootstrap.json`/`load.json` and do not add CLI
  discovery or authority protocol behavior.
- Update the shipped templates/examples and ACP README to describe `baton` as
  the single source, prompt plus derived environment as the two consistent
  carriers, and explicit conflicting `agent.env` entries as a configuration
  refusal.  Operator templates may omit the derived keys; existing templates
  that spell the same values remain compatible.

This boundary touches only the ACP adapter, its shared pure renderer, tests,
templates/examples, and documentation.  It does not change Baton readiness,
claiming, routing, the ACP protocol, session selection, permission mode,
runtime publication, or persistent conversation state.

### Required regression matrix

- Exact presence: all four JSON-quoted configured values and the invocation
  sentence occur once in the first Work prompt for both `new` and `load`.
- Every action kind: obligation, trial, and poke prompts carry the same block;
  role prose and the existing compact action wording remain unchanged.
- Environment parity: the real fake-agent subprocess observes the exact four
  derived variables even when the template omits them.  A conflicting explicit
  value for each key refuses before instruction read, wait, session, or prompt.
  Conflicting inherited parent values are ignored/overridden, and the child
  still observes the four validated values.
- Identity isolation: two participants/roles sharing one binary/config receive
  their own prompt and environment values, never the other's.
- No inference: plausible stale `process.env`, repository paths, and persistent
  load-file paths do not influence rendering.  The four-field block includes
  no action owner, policy path, config contents, credential, or session id.
- Existing refusals: missing/blank fields, relative binary/config, unheld role,
  wrong-participant instruction/readiness envelopes, malformed policy, and
  unsupported ACP capability/mode continue to fail before use.
- Retry/recovery: a retried or resumed session receives the current run's same
  block on every prompt; failed delivery retains readiness and cannot fall back
  to a persistent launcher file.

### Verification and rollout

Focused verification is the ACP bridge suite plus the shared launcher-renderer
tests, shipped-template/example validation, `just test-v11`, and
`git diff --check`.  The current tree has concurrent W11910/W12229 edits in the
same ACP source, test, and README files; implementation must revalidate and
preserve those changes rather than reconstructing an older baseline.

Release acceptance remains operator-owned: drain the managed stack, publish a
successor build, start a fresh ACP session with a fresh start-scoped state
directory, deliberately leave the stale persistent `load.json` present, and
route one bounded smoke Work to `baton.claude`.  The first delivered prompt
must name the successor's exact four values and the first canonical mutation
must be a successful standalone claim through that pair.  A repinned
persistent file or an already-running session does not satisfy the smoke.

## Independent implementation review — 2026-08-26

**Confirmed:** the runtime correction implements the ruled one-source,
two-carrier boundary. Every ACP action prompt receives the shared launcher
block, the real child receives the same four derived environment values,
explicit conflicts refuse, and the full repository gate is green.

**Observed, P2:** the shared renderer's adjacent source comment still says it
is “CODEX-ONLY,” that ACP is environment-only, and that only Codex paths may
compose the block. W14828 has superseded those carrier statements and ACP now
imports and composes that exact renderer. The implementation-ready boundary
explicitly required updating this comment. Full analysis is in
`review-2026-08-26T08-11-35Z.md`.

## Independent correction re-review — 2026-08-26

**Confirmed:** the source paragraph beside `launcherContract` now records the
correct shared-renderer contract and preserves the chronological W12229
supersession. Its added source-comment gate passes.

**Observed, P2:** the user-facing Codex bridge README still publishes the same
superseded rule. It describes ACP as receiving only four environment variables,
then says the launcher block is Codex-only and that rendering it in an ACP
prompt would leak one family mechanism into another. The adjacent existing
role-instruction test comment and failure message repeat that stale premise.
This directly contradicts the implemented one-source, two-carrier boundary and
the corrected source paragraph.

The additive documentation regression and full analysis are in
`review-2026-08-26T10-20-48Z.md`.

## Independent final re-review — 2026-08-26

**Confirmed:** all prior review findings are corrected. The shared renderer,
Codex bridge README, ACP bridge README, and role-reader test prose now agree on
the chronological rule: W12229 established explicit ACP environment delivery;
W14828 superseded its carrier sufficiency; every ACP readiness prompt carries
the authoritative shared block and the spawned child receives the same four
derived environment values from the one validated `baton` source.

**Confirmed:** runtime and documentation gates are green: 420 Codex bridge
tests, 77 ACP bridge tests, template parsing, and whitespace validation. The
reviewer added one passing additive assertion that requires every published
launcher surface to name both ACP carriers; this closes a weakness in the new
all-surfaces gate, whose implementation checked only for the prompt despite
claiming both.

No implementation finding remains. The fresh-release rollover and successful
first canonical claim are still operator-owned acceptance, not evidence this
repository review can manufacture. Final review and evidence are recorded in
`review-2026-08-26T12-21-49Z.md` and
`evidence/review-final-2026-08-26T12-21-49Z.txt`.

## Operator rollout decision — 2026-08-26

Do not interrupt a healthy managed stack solely to certify this correction.
Park live acceptance until the next independently necessary full-stack
restart, such as recovery from a wedged runner. At that boundary, deploy the
successor containing W14828 instead of restarting `14aecfb`, deliberately
leave the stale persistent Claude `load.json` present, start a fresh ACP
session, and run the bounded first-claim smoke before normal dispatch resumes.

This changes scheduling only. It does not waive, weaken or replace the
fresh-release acceptance boundary.

## Operator acceptance — 2026-08-28

**Accepted:** the successor `dd1dc3e` stack is healthy with a fresh
start-scoped Claude ACP context.  Its rendered launcher contract names
`/home/sl/opt/baton/v11/dd1dc3e/bin/baton`, the exact live
`/home/sl/baton-v11.14aecfb/baton.json`, `baton.claude`, and `impl`, while the
deliberately untouched persistent `baton.claude/load.json` still names the
older `14aecfb` executable and the stable config symlink.

The fresh ACP session used the rendered `dd1dc3e` pair for its first recorded
standalone claim and has continued to claim and hand off Work through that
pair.  It did not rediscover or repin the stale persistent launcher file.
This satisfies the operator-owned rollover boundary; no implementation or
deployment gate remains on W14828.
