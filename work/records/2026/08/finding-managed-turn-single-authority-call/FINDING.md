# Invoke managed Baton mutations one command at a time

## Observed — 2026-08-23

The managed `baton.codex` readiness path received W2845, started a turn, and
announced that it would claim before review. It then placed two canonical CLI
invocations in one `exec_command` request: read-only `detail`, followed by
mutating `claim` on the next shell line. `detail` succeeded, but `claim`
remained inside the ordinary workspace sandbox and failed with:

```text
sqlite3.OperationalError: attempt to write a readonly database
```

The exact deployment policy was installed and contains the correct standalone
`baton.codex claim` rule. W220 deliberately authorizes exact canonical Baton
invocations while refusing shell wrappers, raw store access and broader shell
capability. A multiline batch is not the one exact invocation the rule names.
The Work therefore remained queued and unclaimed even though readiness and the
dispatcher were healthy.

The same managed session reported the same failure while attempting W2929
twenty minutes earlier. Runtime returned to `idle`, so the visible symptom was
an idle reviewer beside pending Work rather than a dead service.

Evidence is the managed rollout
`/home/sl/.codex/sessions/2026/08/22/rollout-2026-08-22T08-32-29-01a029e3-2ee6-76b3-86dd-7274d06637b0.jsonl`,
turn `01a02cc9-83a3-7230-b729-04a03367ac95`, and the deployed readiness and
dispatcher logs at 2026-08-23T04:03Z.

## Confirmed boundary

This is not fixed by granting a managed turn raw write access to the Baton
home or by broadening its shell policy. Preserve W415/W220's exact-command
boundary.

A managed agent invokes each canonical Baton operation in its own execution
request. In particular, the mandatory `claim` is a standalone direct command;
it is never combined with `detail`, another read, another mutation, a shell
wrapper, or shell control syntax. Later Baton mutations obey the same rule.

An exact operation that still fails after being issued alone is a distinct
deployment/policy incident and must be reported as such rather than retried in
a broader command.

## Acceptance boundary

- Managed-turn instructions state the one-operation-per-execution rule at the
  point where claim-before-work is defined.
- A regression presents a managed agent with a ready Work and proves its
  first mutating execution request is the standalone canonical `claim` shape.
- Existing exact-policy negatives remain unchanged: a batch, shell wrapper,
  alternate identity/config/binary, and raw authority write do not gain
  capability.
- A fresh managed turn claims ready Work without interactive approval or a
  read-only-database failure.

## Reviewer research — 2026-08-23

**Confirmed — the command shape is the cause, not authority health.** This
managed context claimed W7830 with the same deployed binary, config and
participant that had just failed on W2929 and W2845. The difference was only
the execution request: `detail` ran alone, then `claim` ran alone. The claim
committed at authority sequence 7833 with no approval and no writable-root
change. This is a positive reproduction of the confirmed boundary, not yet the
post-change fresh-context gate.

**Confirmed — the owning policy location is `AGENTS.md`.** The repository's
active-work section already says no Route-owned execution begins until claim
succeeds, and the immediately following managed-turn section defines the
non-interactive execution constraints. The one-operation-per-execution rule
belongs there, adjacent to the mandatory claim, rather than in the execution-
policy generator. `tools/codex-event-bridge/src/exec_policy.mjs` is already
right: it grants the exact direct CLI prefix and deliberately does not grant a
shell program containing several commands.

**Confirmed — two different regressions are required.** A deterministic
policy-text case belongs with
`tests/work/test_w101_role_instructions.py::test_the_required_policy_states_the_v11_model`,
because every Baton role is required to read `AGENTS.md`. The behavioral
regression belongs in
`tools/codex-event-bridge/smoke/managed_baton_write.mjs`: its current prompt
hands the model exactly one claim command, so it cannot reproduce the failure.
Have that live proof present a ready Work, require a read-only `detail` followed
by the canonical `claim`, read the completed turn back with
`includeTurns: true`, and prove they are two separate agent-sourced
`commandExecution` items before accepting the committed Handler. The claim
operation id is fixed by the harness so its exact command is assertable.

**Proposed patch boundary.** Add one normative bullet to `AGENTS.md`; extend
the existing W101 positive policy assertion; and strengthen the existing live
managed-write smoke from one supplied claim command to the two-operation
readiness shape. Do not change generated prefix rules, grant a shell wrapper,
or weaken any W220/W415 negative. The smoke must still assert zero approval
requests, an active canonical Handler, an unchanged authority under the raw-
write negative control, and disposal of every temporary home it owns.

Focused baseline before implementation: 24/24 W101+W220 Python cases and 2/2
selected role-instruction/command-oracle Node cases. Evidence:
`evidence/reviewer-research-2026-08-23.txt`.

## Implementation — 2026-08-23

**A RULE ABOUT THE CLAIM BELONGS WHERE THE CLAIM IS DEFINED.** The bullet is
the first rule of the managed-turn section, immediately after the active-work
claim, and its regression asserts that POSITION as well as its text. Text a
regression only greps for can drift to the bottom of a file and still pass —
which is how a rule about the mandatory first act comes to be missed by
everyone reading the mandatory first act.

**AN OUTCOME CANNOT PROVE A SHAPE.** "The Work is claimed" is equally true of
one batched command that happened to work, of a claim issued before the read,
and of three attempts of which one landed. So the live proof's verdict is the
ORDERED LIST of agent command items — exactly two, read then claim, both
completed, neither asking approval — and the deterministic regressions include
the defect itself, one item containing both operations.

**THE LIVE PROOF IS RED AND STAYS RED.** Two operational findings block it,
and both are recorded rather than asserted around:

`thread/read` with `includeTurns` on codex-cli 0.149.0 returned NO
`commandExecution` item for a turn that demonstrably ran a command — the agent
message was a real traceback from the deployed executable. A minimal probe
reproduces it with one `/bin/echo`. The item type IS in the installed schema.
**That is the premise W2845's command oracle rests on**, so every command-item
verdict in that matrix carries the same exposure.

And the managed invocation ended in an unhandled Python traceback rather than
the typed JSON error every other refusal uses — consistent with the read-only
database this Work is about, and not reproducible outside the sandbox, where
the same commands succeed cleanly.

Relaxing the assertion to accept zero command items, or falling back to the
committed Handler alone, would have produced a green live proof that
established nothing. That is precisely the failure mode the oracle exists to
remove, and reaching for it while implementing the fix for an invisible defect
would have been the same mistake twice.

## Independent implementation review — 2026-08-23

**Confirmed P1 — the live prompt contradicts itself.** The unchanged
developer instruction says to perform "exactly the one canonical Baton
operation" and has higher priority than the turn that now requires two
operations. The W7830 change updated only the turn prompt. A compliant model
cannot satisfy both, so this smoke is not yet a valid proof that the managed
agent ignored the one-operation rule, and the contradiction must be corrected
before the app-server's missing-item behavior is diagnosed further.

**Confirmed P1 — `readinessClaimOutcome` does not prove the read succeeded.**
It accepts any `completed` item without checking `exitCode`. A direct pure
reproduction with a completed read at exit 7 and a completed claim at exit 0
returns `{ok:true}` and reports both operations completed. The later Handler
check can catch a failed claim, but it cannot catch a failed read followed by
a successful claim. The official app-server item contract exposes the exit
code separately from terminal status, and this repository's adjacent W2845
ruled-command oracle already requires both `completed` and exit 0.

**Required correction:** align the developer instruction with the exact
two-operation/two-request contract; require exit code 0 for both the read and
claim; add regressions for nonzero completed read and claim items; and rerun
the deterministic gates. Only then rerun the live smoke. If the corrected
prompt still produces no `commandExecution` item, retain and route that as a
separate deployment/provider integration defect (cross-reference W2845)
rather than weakening the oracle. The unhandled CLI traceback likewise stays
an operational finding and is not accepted as the typed refusal boundary.

Review: `review-2026-08-23T04-30-59Z.md`; evidence:
`evidence/review-2026-08-23.txt`.

## Corrected — 2026-08-23

**A PROOF WHOSE TWO HALVES DISAGREE CANNOT DIAGNOSE ANYTHING.** The smoke's
thread-level instruction still demanded exactly ONE canonical operation while
its turn asked for two, and developer instructions outrank the turn input. I
changed the turn and did not re-read the thread it runs in — so a failure
there could not distinguish a model ignoring the new rule from a model obeying
the instruction that outranked it.

**COMPLETED IS THAT IT RAN, NOT THAT IT WORKED.** The shape accepted a `detail`
exiting 7 beside a claim exiting 0. What makes that more than an oversight:
the Handler assertion afterwards catches a claim that did not commit, and
NOTHING caught a failed read — while the read is precisely the half that
SUCCEEDED in the batched defect this Work exists for. The one item the proof
could not check was the one the original failure left looking healthy.

**AND A CORRECTION TO MY OWN REPORT.** I attributed the server finding partly
to the live smoke, which was confounded by the contradiction above. It stands
on the two probes instead — single command, no contradictory instruction, and
a nonce a turn cannot answer without executing. Saying which evidence survives
a confound is part of reporting the confound.

### Recorded

One mutation is not mechanically checkable: a thread-level instruction is
prose to a model, and no deterministic case can witness a model obeying the
wrong half of a contradiction. What can be checked is that the two halves are
written from the same rule, and they are.

## Final v11 disposition — 2026-08-23

The operator discontinued this strict live certification under W7989's second
decision. The one-command-at-a-time rule, deterministic oracle, smoke shape,
and regressions remain valid defensive safeguards, but the current managed
custom-tool deployment cannot expose the structured live evidence the
acceptance gate requires. The Work closes cancelled rather than claiming a
live pass. V11 remains the interim coordination system; v12's external Worker
Manager owns the replacement execution boundary.
