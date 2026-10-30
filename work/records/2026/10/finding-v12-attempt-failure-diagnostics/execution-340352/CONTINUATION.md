# The retained candidate this packet continues from

Recorded by `baton.claude`, claim340352, read-only against the completed run and
the committed base. **This is the first packet in this campaign that does not
start from committed bytes alone.** Run `attempt-diagnostics-w333486-340016`
actually executed, produced real work, failed its gate, and retained a
candidate; `decisions/review-340349.md` rejected that candidate with three
static blockers. The continuation starts from the candidate, not from zero.

## What the run did

| fact | value |
| --- | --- |
| run | `attempt-diagnostics-w333486-340016`, authority `b8bc9fc36b784826b0c9915ae550994b` |
| launched | 2026-10-20T16:17:37Z, ended on its own at **869.3s** |
| attempt | `attempt-00cdd1a06d6322b016a3e78799dd6206811be6d00b1159ecdd8f719d6914886b` |
| controller | `state: held`, `faults: []`, `child_status: 1`, elapsed 869.2875s |
| workload | `state: held`, `stopped: exceptional`, served 869.4529s, stage `implementation: exceptional` |
| attempt disposition | **`unable`** — no proposal published |
| candidate | **retained**, head `433692c5003d7f3a91a1acab7efdb471d5597235` on base `bc925cf5`, 127315 bytes, `sha256:67b6d96e…` |
| candidate verification | **failed**, the sealed gate exited 1 |
| patch | `change.patch`, `sha256:3af1822dc0d08851466105f17cbf5e9e26248ff75dc3d9352a9a43b979058e3e` |

**The 900-second lease did not fire.** `provider.status 0`,
`failure_reason null`: the turn ended on its own with 30.5 seconds of margin
against the lease. Every earlier packet in this campaign — all by this author —
predicted enforced expiry cutting the turn short. It did not happen, and it must
not be narrated as though it had. The runtime destruction afterwards was
ordinary teardown, not expiry reclaim.

**Why the gate failed is still unknown, and that is the point of item 6 below.**
`candidate-verification.txt` records the argv and `exit: 1` and deliberately
withholds the stdout and stderr, because that output is code from the candidate
tree running with the attempt's credential mount readable. A generated
instruction in that file suggests the operator rerun it on the host.
**`decisions/review-340349.md` is explicit that this is not authority**: AGENTS
v11-preparation/v12-execution applies, there is no product-test exception for
W333486, and owner340145's one invocation is consumed. So **the classification
has to happen inside the next isolated v12 run**, by the turn that owns it.

## What the candidate already delivers, and keeps

1621 insertions across 8 files. This is real work and the continuation
**preserves its useful cases rather than restarting**:

| path | lines | what |
| --- | --- | --- |
| `worker_manager/failure_cause.py` | 619 new | `token_bound_runtime`, `record_and_raise_cessation_intent`/`_outcome`, `cessation_intent_operation_id`, `attempt_cessation_intent_of`/`_outcome_of`, `_known`/`_unknown`, composed `attempt_failure_cause_of` with explicit `unknown` and `absent_records` |
| `worker_manager/intake.py` | +103 | capture on the reclaim and settlement paths |
| `worker_manager/attempts.py` | +63 | capture on Authority-fenced cancellation |
| `worker_manager/documents.py` | +68 | projection members |
| `tools/attempt_diagnostics.py` | 314 new | the read-only report, allowlisted, with `_typed` refusing nested-object forwarding |
| `tools/stack_command.py` | +19 | `attempt-diagnostics` in `COMMANDS`, with the rebuilt-bundle obligation in its own docstring |
| `tests/manager/test_attempt_failure_cause.py` | 266 new | the owed gate module |
| `tests/tools/test_attempt_diagnostics.py` | 170 new | the owed gate module |

Several accepted obligations are visibly honoured in it: the token-bound
identity rule, intent-before-effects as a *design*, `_known`/`_unknown` with no
third shape, a missing count never reported as a zero, the absence of a
start/preparation-failure record described as *expected* rather than as evidence,
and the revocation reported beside an unknown cause. Keep all of that.

## The three blockers, each re-verified against the candidate this claim

I read the candidate's own bytes before writing this; the reviewer is right on
all three and these are not paraphrases.

### 1. The production seam is not connected

`result.json`'s `changed_paths` contains **no `job_manager` file at all**. At the
base, `job_manager/projection.py:_stage_status` emits no `attempt_diagnostics`
member, `failure_cause.attempt_failure_cause_of` has **no production caller**
anywhere in the patch, and `tools/attempt_diagnostics.py:_diagnostic_of` reads
**only** `stage["attempt_diagnostics"]`:

```python
def _diagnostic_of(stage):
    held = stage.get("attempt_diagnostics") if isinstance(stage, dict) else None
    return held if isinstance(held, dict) else None
```

So ordinary status cannot carry the new account, and the report can only ever see
a hand-built fixture. **Hand-built fixtures on both sides of an unconnected seam
prove nothing about the seam.** This is the single most important correction.

### 2. The producer and the report disagree about shape

Even if the member were attached verbatim, the two sides do not meet:

- the producer wraps facts: `_known(value, source)` → `{"known": True, "value":
  …, "source": …}`, and `start_failure`, `preparation_failure`, `revocation`,
  `completion`, `token`, `domain`, `generation` are all wrappers;
- the report's `EXECUTION_MEMBERS`, `WORKSPACE_MEMBERS` and `_typed` want **raw
  scalars**, and `_typed` deliberately refuses nested objects — so a recorded
  **known** value arrives as **unknown**;
- `CAUSE_MEMBERS` expects `("outcome", (str,))` and a top-level `operation_id`.
  The composition sets `outcome` to the **nested outcome document**, puts the
  scalar in `outcome_state`, and exposes `correlation_id` rather than
  `operation_id`;
- the token, renewal, completion, start-failure and preparation-failure facts
  are composed by the producer and **are not in the report's member lists at
  all**.

### 3. The durable pre-effect intent is best-effort and silent

`record_cessation_intent` is documented "NEVER RAISES" and returns a prose
sentence on failure. **All four acting call sites discard that return**, and two
of them order effects immediately afterwards:

- `attempts._order_quiescence` (candidate line 3584) → `agent.cancel` then
  `adapter.stop`;
- `intake.settle_revoked_resource` (candidate line 6018) → `govern.release`.

So under a recording failure the effect still happens with no durable intent —
which is exactly the property the design promised. `record_cessation_outcome`
likewise swallows collisions, and because outcome identity is fixed by
attempt/assignment/start/component/generation, an **uncertain** first observation
followed by a **later positive** one collides under the same id and the first is
retained: a historical uncertainty becomes an enduring substitute for better
later evidence.

## What this packet does about it

It pins the candidate patch as a task input, by digest, and `TASK.md` makes
applying it the turn's first act. Nothing is restored into the private checkout
and no host Git object is created: the patch travels as bytes on the read-only
mount, exactly like every other pinned input, and the turn applies it inside its
own workspace. `PROVENANCE.json`'s `checkpoint.paths` stays **empty** and
`prepare.py` still refuses a declared restored buffer — the continuation does not
need one and the refusal keeps its meaning.

The milestone is the reviewer's: **one real failed-attempt status row and a
supported report carrying the same owned facts, with durable and replay-safe
capture, and a classified gate result.** Not a second invented shape on either
side of a seam that was never joined.
