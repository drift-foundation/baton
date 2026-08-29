# Finding — Codex contexts lack the canonical Baton launcher contract

## Observed — 2026-08-25

After the W10198 reconciliation, the installed `pc.code` ACP template and
Pushcoin policy matched the reviewed successors byte-for-byte. All eight
services were healthy, and the rendered `pc-code-acp.json` proved that
`BATON_BIN`, `BATON_CONFIG`, `BATON_PARTICIPANT`, and `BATON_ROLE` matched its
canonical Baton fields.

The fresh acceptance smoke W12181 nevertheless remained queued at
`pc.rsrch`. The readiness producer repeatedly delivered the exact episode to
the fresh `pc.plan` Codex context. That context completed multiple turns
without claiming and reported that none of `BATON_BIN`, `BATON_CONFIG`,
`BATON_PARTICIPANT`, or `BATON_ROLE` had been supplied.

This is not an ACP or Pushcoin authentication failure. The post-cutover
correction covered the ACP template only; the Codex thread bootstrap still
provides role prose that refers to launcher-supplied values without actually
making the exact executable, config, participant, and role available to the
managed context.

## Confirmed boundary

- Every managed agent context must receive one explicit canonical Baton
  launcher contract: executable, config, participant, and role.
- A context must not infer those values from repository paths, deployment
  symlinks, remembered history, another participant, or filesystem search.
- The contract applies to Codex-backed participants as well as ACP-backed
  participants. Each context receives only its own identity.
- W10198 cannot pass acceptance until a fresh `pc.plan` context claims the
  smoke, hands it to the corrected `pc.code` context, independently reviews
  the result, and returns it to `pc.ops` without locator or credential failure.

## Acceptance

1. Fresh Codex thread bootstrap supplies the exact canonical Baton executable,
   config, participant, and role to each configured context.
2. The values are participant-specific and cannot cross target boundaries.
3. Existing `baton.*` and `pc.*` Codex targets retain their one-to-one context
   mapping and readiness ownership.
4. Focused bridge/bootstrap tests cover presence, identity mismatch refusal,
   and absence of inference.
5. A fresh managed restart lets W12181 complete the canonical
   `pc.rsrch -> pc.impl -> pc.rsrch -> pc.ops` smoke.

## Reviewer revalidation — 2026-08-25

### Confirmed loss boundary

**Confirmed:** `bootstrapThread` in
`tools/codex-event-bridge/src/main.mjs` holds all four launcher inputs in
`options` and successfully validates the participant-relative instruction
envelope, but `thread/start` receives only `resolved.instructions`. The
executable, config, participant, and role are discarded as context inputs
before the thread exists.

**Confirmed:** the long-running dispatcher repeats the same loss.
`resolveTargetInstructions` reads each target with the configured
`roleInstructions.binary`, `roleInstructions.config`,
`identity.participant`, and `identity.role`, then stores only the accepted
role prose as `target.developerInstructions`. `EventBridge` reapplies that
text on every `thread/resume`; none of the four launcher values reaches the
context unless a role author happened to copy them into prose.

**Observed:** the current `baton.codex instructions role=rview` result happens
to include a deployment-specific sentence naming its executable, config, and
participant. That sentence is configuration-authored role text, not an
adapter guarantee. W12181 is the counterexample: the `pc.plan` role text did
not carry the values. Correctness must not depend on every role author copying
host launch data into durable persona prose.

**Confirmed:** `readRoleInstructions` is shared by the Codex and ACP adapters.
Changing its returned `instructions` field globally would also inject a Codex
rendering into ACP prompts, whose ruled launcher contract is already the four
explicit `agent.env` values. The smallest boundary is therefore a Codex-only
composition helper used after the shared instruction read, not a semantic
change to the shared protocol projection.

### Confirmed Codex carrier boundary

**Confirmed:** the installed generated app-server schema exposes
`developerInstructions` on both `ThreadStartParams` and
`ThreadResumeParams`; neither structure exposes a per-thread environment
map. `TurnStartParams` exposes neither. The generic `config` override on
thread start/resume is not an acceptable substitute: the W415 ruling rejected
arbitrary per-thread configuration overrides, and the bridge's
deployment-owned command policy deliberately relies on no such override.

**Confirmed:** one app-server process hosts all six Baton/Pushcoin Codex
targets. Process-global environment would cross participant boundaries even
if the launcher could change it after process start. The already supported,
participant-specific, restart-reapplied carrier is the developer-instruction
text.

**Proposed:** render one explicit launcher block beside the accepted role
instructions, from the same already validated values the bridge used to make
the `instructions` read:

```text
Baton launcher contract (authoritative; do not infer):
BATON_BIN=<JSON-quoted configured binary>
BATON_CONFIG=<JSON-quoted configured config>
BATON_PARTICIPANT=<JSON-quoted validated participant>
BATON_ROLE=<JSON-quoted validated role>
Invoke BATON_BIN with --config BATON_CONFIG and --participant
BATON_PARTICIPANT for every Baton operation.
```

The labels make the ACP/Codex contract vocabulary agree, but for a
Codex-backed context these are developer-instruction values, not a claim that
the shared app-server process has participant-specific environment variables.
JSON quoting keeps spaces, quotes, and control characters data rather than
instruction syntax. The block contains exactly the ruled four values: not
`identity.actionOwner`, `roleInstructions.execPolicyFile`, configuration
contents, credentials, or any ambient environment.

**Proposed patch boundary:** add one pure Codex launcher-contract renderer
(naturally beside the shared instruction reader, but called only by Codex),
then use it in both `resolveTargetInstructions` and `bootstrapThread`.
`thread/start` receives the composed text from the first turn and dispatcher
`thread/resume` reapplies the same shape from current accepted role text and
the configured target identity. Keep `BOOTSTRAP_PROMPT` a no-tool durability
turn and keep `CodexClient` free of Baton-specific policy. No authority,
readiness, routing, runtime, or application-protocol change is needed.

### Existing guards to preserve

**Confirmed:** `validateConfig` already requires an absolute instruction
binary/config, one explicit role per target, one unique participant per
target, and one unique server/thread assignment. `validateRoleInstructions`
then refuses an envelope whose outer participant, result participant, or
selected role differs from the configured identity. The correction should
compose only after those checks and must not widen them.

**Confirmed:** `--start-thread` explicitly requires the endpoint, cwd, Baton
binary, Baton config, and participant, while the role is currently refused
indirectly by `readRoleInstructions`. Make `--role` an explicit required
bootstrap operand so all four contract fields fail before any instruction
read or Codex connection, rather than relying on a downstream reader to catch
one missing field.

**Observed baseline:** the focused
`bootstrap_thread.test.mjs`, `role_instructions.test.mjs`, and
`codex_client.test.mjs` files pass before correction. The existing positive
assertions prove the defect: fresh start and dispatcher resume expect only
the role prose.

### Focused regression matrix

- Bootstrap: exact configured binary/config plus the validated participant
  and role appear once in the developer instructions passed to
  `thread/start`; the accepted role prose and no-tool bootstrap prompt remain
  unchanged.
- Dispatcher: every target receives its own composed block on resume. Two
  targets sharing one binary/config but naming different participants/roles
  cannot receive each other's values.
- Restart/config refresh: dispatcher resolution rebuilds the block from the
  current configured source and accepted role read; no remembered thread text
  or earlier target object is authoritative.
- Missing/refused values: absent binary, config, participant, or role refuses
  before thread creation; non-absolute source paths and participant/role
  mismatches keep their current fail-closed errors.
- No inference: conflicting `process.env` values and plausible repository
  paths do not affect the rendered block. The renderer performs no filesystem
  search and includes neither action owner nor exec-policy path.
- ACP compatibility: `pc.code` keeps its exact four environment values, and
  the shared instruction reader continues to return accepted role prose
  without a Codex-only block silently changing ACP prompt semantics.
- One-to-one ownership: retain the existing duplicate participant and
  duplicate server/thread refusals and the one readiness consumer per managed
  participant deployment assertions.
- Documentation: explain that Codex receives the four labels through durable
  developer instructions while ACP receives them through its isolated agent
  environment; neither context may infer missing values.

### Verification and rollout boundary

The implementation gate is the focused bridge/bootstrap suite plus the full
Codex event-bridge test gate and `git diff --check`. Deployment remains an
operator act: drain, install/restart the managed stack so every Codex target is
fresh, then complete W12181 through `pc.plan -> pc.code -> pc.plan -> pc.slaw`
and return parent W10198 to `pc.ops`/the owning approver route. A live smoke on
an old thread does not satisfy the fresh-context acceptance.

The current working tree also carries unrelated W11910 changes in the Codex
bridge and README. W12229 should not absorb or rewrite that Work; implement
serially, and rebase the small documentation edit on the then-current file.

## Independent implementation review — 2026-08-26

**Observed — fresh bootstrap accepts relative launcher sources.** Dispatcher
configuration passes `roleInstructions.binary` and `roleInstructions.config`
through `validateConfig`, which requires absolute paths. The standalone
`bootstrapThread` path checks only that `--baton` and `--baton-config` are
truthy before handing them to the instruction read and later rendering them
as authoritative. A relative executable is resolved through process execution
rules, and a relative config is interpreted from ambient working context. The
new focused regression demonstrates the executable branch reaching the
read/connection path; its loop exercises the config branch after that first
failure is corrected.

**Confirmed — both Codex entry paths require the same absolute-source gate.**
Fresh bootstrap must reject a relative executable or config before any
instruction read or Codex connection, just as dispatcher configuration does.
This is the already-recorded no-inference and non-absolute-source acceptance
boundary, not a new product decision. The four-field renderer, accepted
participant/role composition, Codex-only carrier, and ACP isolation otherwise
match the confirmed implementation boundary in the focused review.

## Independent review finding — 2026-08-26

**Observed, P1.** `bootstrapThread` checked only truthiness for `--baton` and
`--baton-config`, so a relative executable or config was accepted and rendered
into the block as "authoritative; do not infer" — an inferred location wearing
the shape of an explicit value. The dispatcher path was never exposed to this,
because `validateConfig` has always required both `roleInstructions` paths to
be absolute. Full analysis in `review-2026-08-26T01-31-59Z.md`.

## Implementation decision — 2026-08-26: three doors, one admission rule

Recorded by the implementer under the claim that answered that review.

**Absoluteness belongs in the operand gate**, beside the check that refuses a
missing operand and before the instruction read or any client factory: a
launcher operand is wrong the moment it arrives, not once somebody has tried
to use it. The renderer stays pure and still reads nothing.

**There were THREE doors into this one contract and only one was closed.** The
Codex dispatcher required absolute paths; the Codex bootstrap did not; and
`tools/acp-baton-bridge/src/config.mjs` required `baton.binary` and
`baton.config` to be non-empty and not to be absolute — although those two
become `BATON_BIN` and `BATON_CONFIG` in the agent's own environment, and the
confirmed boundary says in as many words that the contract applies to
ACP-backed participants as well as Codex-backed ones. All three refuse the
same shape for the same reason now.

**The ACP door is beyond the review's literal ask and is flagged rather than
folded in.** The review scoped its required correction to `bootstrapThread`
and said to keep the dispatcher validation and the renderer unchanged, which
this does; it did not ask for the ACP door because that door had not been
looked at. Leaving a known instance of the exact defect just named would be
the fix-only-what-was-named shape this campaign keeps being corrected for —
but whether it belongs here or in its own Work is the reviewer's ruling.

## Independent correction review — 2026-08-26

**Confirmed:** the prior [P1] is corrected. Fresh Codex bootstrap refuses both
relative launcher paths before the instruction read or client factory, and
the existing dispatcher absolute-path guard and pure four-field renderer are
unchanged.

**Scope ruling:** the ACP absolute-path admission check belongs in this Work.
The confirmed boundary above explicitly applies to ACP-backed contexts, and
ACP `baton.binary`/`baton.config` are the values it already supplies as
`BATON_BIN`/`BATON_CONFIG`. Applying the same gate closes a known third entry
to this one contract without changing its carrier or protocol semantics.

**Signed off for implementation.** PLAN item 6 remains an operator deployment
and fresh-context acceptance smoke. The current shared tree's aggregate Codex
gate has a concurrent, untracked W11910 claim-slot regression failure; that
other Work must be green before deployment, but it is not a W12229 finding.
See `review-2026-08-26T02-49-05Z.md`.

## Fresh-context operator acceptance — 2026-08-28

**Observed:** The deployed fresh-context smoke W12181 completed the required
`pc.plan -> pc.code -> pc.plan -> pc.ops` path. The new `pc.code` context
received exact absolute `BATON_BIN` and `BATON_CONFIG` values, its own
`BATON_PARTICIPANT=pc.code` and `BATON_ROLE=impl`, and the configured
`/home/sl/src/pushcoin` working directory. Standalone canonical `detail`,
`thread`, `claim`, `home`, and `resolve` operations succeeded without a
credential failure, while the no-`--config` negative control refused rather
than using ambient state.

**Confirmed:** Independent `pc.plan` review signed off the smoke and found no
application changes. W12181 is the fresh-context acceptance evidence required
by PLAN item 6; an existing context was not substituted. Once `pc.slaw` closes
that provider Work, W12229 has no remaining implementation or operational
gate.
