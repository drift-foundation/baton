# Progress — supply the Baton launcher contract to Codex contexts

Implementer: `baton.claude`. Work `W12229`, claimed 2026-08-25.

## Revalidation before editing

Every confirmed fact in the reviewer's research still describes the tree:

- `bootstrapThread` in `tools/codex-event-bridge/src/main.mjs` held
  `--baton`, `--baton-config`, `--participant` and `--role` in `options` and
  passed `resolved.instructions` alone to `thread/start`;
- `resolveTargetInstructions` read each target with the configured binary,
  config, participant and role, then stored only `resolved.instructions` as
  `target.developerInstructions`, which `EventBridge` reapplies on every
  `thread/resume`;
- `readRoleInstructions` is imported by BOTH adapters —
  `tools/acp-baton-bridge/src/acp_baton_bridge.mjs` reaches across for it —
  so a change to the shared projection would have put a Codex rendering into
  ACP prompts;
- `--start-thread` required five operands and refused `--role` only
  indirectly, inside the instruction reader.

The pinned decision therefore holds unchanged and nothing in it is superseded.

## What changed

**One pure renderer, in the shared file and called only by Codex.**
`launcherContract({binary, config, participant, role})` in
`role_instructions.mjs` renders the four labelled values and nothing else, and
`codexDeveloperInstructions` composes it beneath accepted role prose. It reads
nothing, searches nothing and defaults nothing: a blank or missing field
refuses rather than rendering a contract with a hole in it, because a context
told three of four values would infer the fourth and inferring is exactly what
the confirmed boundary forbids. Values are JSON-quoted, so a space or a quote
in a path is data rather than syntax.

**Both Codex carriers.** `resolveTargetInstructions` composes the block for
every target, so every `thread/resume` reapplies it; `bootstrapThread` composes
it for `thread/start`, so a fresh context has the contract from its first turn.
Both compose from the configured source and the participant and role the
instruction read ALREADY PROVED — `validateRoleInstructions` has refused any
disagreement before this point, so those are the values the authority itself
confirmed, and a restart rebuilds the block from current configuration rather
than from anything an old thread remembers.

**`--role` joins the required operands.** All four contract fields now fail in
the same place, before any instruction read or Codex connection, rather than
three failing there and one failing later in somebody else's error.

**Nothing else moved.** The shared instruction projection still returns
accepted role prose alone, ACP keeps its four `agent.env` values,
`BOOTSTRAP_PROMPT` is still a no-tool durability turn, `CodexClient` still
carries no Baton-specific policy, and no authority, readiness, routing,
runtime, command-policy or application-protocol behaviour changed.

## Two existing assertions replaced, and they were the defect

The reviewer's research names them, and both required the composed value to be
role prose and NOTHING else:

- `the accepted role instructions still reach thread/start` — replaced by
  `the accepted role instructions AND the launcher contract reach
  thread/start`;
- the dispatcher-resume assertion in `role_instructions.test.mjs`, whose
  expected `developerInstructions` is now the composed text.

Neither was weakened. Each asserts strictly more than before, and the old form
is what a fresh `pc.plan` context received when it reached W12181 over and over
and could not claim it.

## The focused matrix

`bootstrap_thread.test.mjs` **12 -> 18**, `role_instructions.test.mjs`
**8 -> 13**:

- exact presence of all four values on `thread/start`, and role prose first
  with the block appended exactly once;
- **four fields and no fifth** — no action owner, no exec-policy path,
  measured by counting the `BATON_` lines rather than by reading the block;
- every missing operand refuses with nothing read and no connection opened;
- a blank or absent contract field refuses rather than rendering a hole;
- quoting keeps a spaced or quoted path as data;
- **no inference**: conflicting `BATON_*` values in `process.env` do not reach
  the rendered block;
- **non-crossing**: two targets sharing one binary and one config but naming
  different participants and roles each receive only their own, and neither
  text contains the other's identity;
- **restart recomposition**: a changed configured binary produces a changed
  block, so nothing remembered is authoritative;
- the participant/role mismatch refusal above the composition is untouched;
- a deployment with no `roleInstructions` keeps its old shape rather than
  gaining a block invented from nothing;
- **ACP compatibility**: the shared reader still returns prose with no
  `BATON_BIN` in it.

## Documentation

The Codex README gains a `The Baton launcher contract` section: what the four
values are, why a Codex context receives them through `developerInstructions`
(the start/resume contract has no per-thread environment, the generic `config`
override is W415-ruled-out, and one app-server process hosts every target so
process environment would cross participants), and that the labels make the two
families' vocabulary agree without claiming Codex has real environment
variables. The ACP README says the same contract lives in `agent.env` there,
and both say the shared reader returns prose alone so neither carrier appears
in the other family.

The `--start-thread` section records that all six operands are required and why
`--role` is among them.

## Verification

`evidence/gate-2026-08-25.txt`.

- `bootstrap_thread` **18/18**, `role_instructions` **13/13**,
  `codex_client` unchanged and green.
- Full Codex event-bridge suite **395**, ACP **64/64**, whitespace check clean.
- Two of the 395 fail and **neither is this Work's**: see below.

## Reported and not fixed

`tests.claim_slot` — `an unclaimed delivery promoted to claimed while queued
becomes its own recovery turn` and `a non-Work obligation is not held behind
the participant's claim`. Both are reviewer regressions on **W11910**, added
after this participant passed that Work back, and both are real defects in that
correction:

- the claim-slot gate reads `claimed` from the QUEUED EVENT, so when the
  claimed Work in the live projection is that same Work it is held behind its
  own claim instead of becoming the recovery turn;
- the gate tests `claimed !== true`, and a non-Work obligation carries no
  `claimed` field at all, so it is deferred although the ruling keeps
  obligations, trials, pokes and refreshes on their existing rule.

**Measured rather than assumed**: both reproduce in a copy of the tree with
every W12229 change reverted to `HEAD`, so neither is caused by this Work.
W11910 is routed to `baton.feat` and not held by this claim; fixing them here
would be executing Work nobody claimed. Reported on T11910 with the correction
I would make.

## Not done, and it is the operator's

PLAN item 6: drain, deploy, restart with fresh contexts, and complete W12181
through `pc.rsrch -> pc.impl -> pc.rsrch -> pc.ops`. **A live smoke on an
existing thread does not satisfy the fresh-context acceptance**, and nothing
here was verified against the running deployment.

## State

**Awaiting independent review.** The claim is not released and no Git operation
was performed.


## Review correction — 2026-08-26

The finding is exact and the fix is one guard in the operand gate: both paths
must be absolute, checked beside the rule that refuses a missing operand and
before the instruction read or any client factory. A launcher operand is wrong
the moment it arrives, not once somebody has tried to use it. The renderer is
untouched — absoluteness is a property of the operand a launcher supplies,
which is exactly where the dispatcher checks it too.

## Three doors into one contract, and only one was closed

Correcting the second made the third visible.
`tools/acp-baton-bridge/src/config.mjs` required `baton.binary` and
`baton.config` to be non-empty strings and said nothing about absoluteness —
and those two become `BATON_BIN` and `BATON_CONFIG` in the agent's own
environment. The confirmed boundary says in as many words that this contract
applies to ACP-backed participants as well as Codex-backed ones, and that a
context must not infer these values from repository paths, deployment symlinks
or filesystem context.

So the Codex dispatcher required it, the Codex bootstrap did not, and the ACP
door did not. All three refuse the same shape for the same reason now, and a
case drives BOTH Codex doors with the same two spellings so they cannot drift
apart again.

**This is beyond the review's literal ask and I am flagging it rather than
folding it in.** The review scoped its correction to `bootstrapThread` and said
to keep the dispatcher validation and the renderer unchanged, which this does.
It did not ask for the ACP door because that door had not been looked at.
Leaving a known instance of the exact defect just named would be the
fix-only-what-was-named shape this campaign keeps being corrected for — but
whether it belongs in this Work or its own is the reviewer's to rule.

## Verification

`evidence/gate-after-review-correction-2026-08-26.txt`.

- `bootstrap_thread` **22** (19 before): the review's regression kept as
  written, plus the two-door case, the looks-rooted case (`./bin/baton`,
  `~/baton/bin/baton`, `$BATON_HOME/bin/baton` — the values a launcher
  template produces when a variable did not expand), and the
  ordinary-absolute-pair case so the guard refuses a shape rather than the
  normal path.
- ACP **67** (66 before), with four relative spellings at the third door.
- **Both guards measured to fail without them**, restored byte for byte.
- Codex **399/399** and ACP **67/67**. **Both Node suites are fully green** —
  the one failure the previous W12229 evidence recorded was this review's own
  regression, and the two before it were W11910's, corrected since under its
  own claim. Nothing is reported as somebody else's this time because there is
  nothing left to report.
- Whitespace check clean.

## Still the operator's

PLAN item 6: drain, deploy, fresh contexts, W12181 through `pc.ops`, and
W10198 returned. A smoke on an existing thread does not satisfy the
fresh-context acceptance, and nothing here was verified against the running
deployment.

## State

**Awaiting independent review.** The claim is not released and no Git
operation was performed.
