# Advice for the remaining W170385 work

Advisory Work W173847, claim 173849, baton.claude via baton.impl.
**Read-only pass. No product or test file was edited, no test was run, no Git
state was touched.** Everything below is a suggestion for baton.tuner, who owns
W170385 and every product, test and dossier file under it. Revalidate each item
before using it: the tree moved while I was reading it.

## 1. Revalidation -- the selection snapshot is already stale

The advisory FINDING pinned "latest recorded step32 passes scheduler/restart
checks" as a point-in-time observation. **It has moved.** `ledger-170385.json`
now records 34 rows, 101.642889 s:

| Step | Label | Result |
| --- | --- | --- |
| 31 | scheduler-restart | fail |
| 32 | scheduler-restart | **pass** |
| 33 | known-preparation-failure | **pass** |
| 34 | apply-failure | **fail** |

So the tuner has already entered the area this advice was requested for.
**Known preparation failure appears done** (step 33 passes) and **apply failure
is in progress** (step 34 fails). Advice that treated either as unstarted would
be wrong. Below I separate what I could confirm already exists from what I could
not find.

## 2. What already exists -- do not rebuild it

All three settlement call sites are present in the current tree:

| Site | Phase | Trigger |
| --- | --- | --- |
| `tools/integration_worker.py:1339` | `prepare` | a start that failed after creating a runtime |
| `tools/stage_execution.py:5129` | `prepare` | `managed_result_of(...)["state"] == "blocked"`, i.e. failed causal verification |
| `tools/stage_execution.py:2580` | `apply` | `not answered["succeeded"]` |

They all call the same existing owner:

    src/baton_v12/job_manager/integration_capacity.py:1554
    settle_failed_integration(store, control, *, orchestration_id, phase,
                              coordinator=None)
    """Retain an owned failure before cancelling plans and releasing capacity."""

The projection side exists too, and is already wired:

- `src/baton_v12/job_manager/projection.py:491` sets
  `entry["managed_failure"] = failed_integration_of(store, stage_id, episode)`
  for integration stages.
- `src/baton_v12/job_manager/integration_capacity.py:1532` `failed_integration_of`
  proves the account against its parent, its ended member and that member's
  ending journal, then returns
  `dict(account, settled=row["lifecycle"] == "ended")`.
- `src/baton_v12/job_manager/projection.py:120`
  `if (entry.get("managed_failure") or {}).get("settled"): return "exceptional"`.

**Nothing new is needed in the projection or in the settlement owner for a
failed apply to read as `exceptional`.**

## 3. The step-34 failure is upstream of settlement, not in it

This is the item I think is worth most, and it follows from ordering alone. In
`_observed_state` the `managed_failure` test at **line 120** runs **before** the
integration observation at **line ~159**
(`integrated = observed.get("integration")` -> `_integrating(...)`). So if the
root lifecycle had reached `ended`, `exceptional` would already win over any
`integrated` account.

Step 34 observes `'completed' != 'exceptional'` with a recorded
`conclude ... {'outcome': 'integrated'}`. Therefore **the settlement at
`stage_execution.py:2580` did not run** -- not that it ran and was ignored.

`settle_failed_integration(phase="apply")` is reached only on
`if not answered["succeeded"]`. So the question to narrow is which branch
answered instead:

1. **`answered["succeeded"]` was truthy.** The step-34 diagnostic shows the
   apply exchange as `{'state': 'unreadable', 'unreadable': {'category':
   'refused', 'code': 'precondition'}, 'terminal': None}`. Worth checking
   whether `active.poll` can answer `succeeded` while its exchange is unreadable
   and its terminal is `None`. An unreadable exchange is not evidence of
   success -- and it is not evidence of failure either.
2. **The already-imported branch won first.** `stage_execution.py:2559-2567`
   returns `{"outcome": "integrated"}` whenever a settled `apply` publication
   and an Authority integration receipt both exist, **before** the failure test
   at 2575. If the fixture's failed apply still produced those, that branch
   answers and the failure is never considered.
3. **`answered is None`** -> `{"outcome": "pending"}` at 2573, and the
   `integrated` conclude came from elsewhere in the tick.

I could not run the case to distinguish these, so this is a reading of source
and of the recorded diagnostic, **not a diagnosis**. Cheapest discriminator:
print `answered` and `publication` immediately before line 2575 in a scratch
run, rather than reasoning further from the report.

## 4. A hazard worth checking while you are in there

`stage_execution.py:2578` refuses before settling:

    if publication is not None:
        _refuse("the failed apply has a target publication requiring manual
                 inspection")

That refusal is right -- a failed apply that already published to the target is
not something to settle automatically. But note the consequence: **that path
settles nothing and releases nothing**, so the root stays held and the stage
keeps whatever state it had. If the selected acceptance wants a distinct
observable outcome for "failed apply with a target publication", it needs its
own case; the current code reaches an operator refusal, not a settled failure.
Worth confirming that is the intended selected behaviour rather than a gap.

## 5. Remaining already-selected bounded acceptance

Only items already in the selected packet, as bounded cases:

1. **Failed apply settles exceptionally** -- the step-34 case. Assert
   `failed_integration_of(...)["settled"] is True`, root `lifecycle == "ended"`,
   stage `exceptional`, **and no target effect**: target bytes, canonical
   revision and porcelain status unchanged.
2. **Failed apply with a target publication** -- refuses for manual inspection,
   settles nothing, releases nothing, root still held (see section 4). Assert
   the refusal and that lifecycle is *not* `ended`.
3. **Known preparation failure** -- step 33 already passes; add the negative
   pairing if absent, proving `failed_integration_of` REFUSES when the account
   disagrees with its parent or its ended member, rather than only proving the
   success path.
4. **Restart across each settlement** -- reopen the composition and both stores
   after the failure and before the settling sweep, then assert exactly one
   settlement: one committed `integration-capacity.failed:<orchestration>`
   record, and the member's `ended_operation_id` unchanged.
5. **Root settlement releases exactly once** -- assert the scheduler
   allocation's final state and that a second sweep neither re-releases nor
   re-settles.

For 4 and 5 the reversal that matters is the one that catches a vacuous case:
delete the settlement call and confirm the case fails. In W170382 two of my
cases passed their own reversals until I added exactly that check, and a third
passed with its restart removed. It is worth the extra run.

## 6. Proposed documentation wording

For the deployment draft, describing actual behaviour rather than intent:

> **Failure settlement.** A managed integration that fails is *settled*, not
> retried. `settle_failed_integration` retains the failure account, cancels the
> remaining phase plans and releases the capacity root; the stage then projects
> `exceptional` and its successors stay blocked. The control plane does not
> reopen an exceptional stage -- an operator decides what happens next.
>
> **Preparation failures** are settled at three points: a start that failed
> after creating a runtime, a preparation that failed causal verification, and a
> parent that cannot continue because its preparation never ended successfully.
> In each case the child runtime is destroyed, its credential and launch
> delivery roots are removed, and the result directory is *retained* -- kept on
> purpose, because material from a failed run is untrusted but may be the only
> evidence of what happened.
>
> **Apply failures** refuse the queue entry and settle the orchestration without
> touching the target.
>
> **The one case that is not settled automatically** is a failed apply that had
> already published to the target. It refuses with "the failed apply has a target
> publication requiring manual inspection" and leaves the root held. This is
> deliberate: the target has been changed, and no automatic rule can know
> whether that change should stand.

### Manual recovery limitations -- state these plainly

- **A held root is not a stuck system, and it is also not self-healing.** An
  allocation left `recovery-required` stays that way until an owner acts. There
  is no automatic reset, and widening the narrow pre-intent recovery to cover
  post-intent failures would reset failures rather than recover them.
- **An uncertain start is not a failed start.** Where the manager identified the
  runtime, the failure is known and is ended. Where observation is genuinely
  inconclusive, the hold is preserved and nothing is relaunched; a later exact
  observation is new recovery evidence, not a permanent verdict.
- **Retained material is never deleted by a failure ending.** Cleanup of a
  retained result directory is a separate, explicit act.
- **The evidence is deterministic-simulation evidence.** The current cases use
  the selected simulated engine with a real local worker process. They are not
  evidence about a real container engine, a live provider or an image build, and
  the draft should say so wherever it describes cleanup and termination.

## 7. Assumptions, and what I could not check

- I ran nothing. Every claim about *behaviour* comes from reading source and the
  recorded step-33/34 logs and ledger; every claim about *structure* is a
  file/symbol citation that can be verified directly.
- The tree is moving under a live tuner claim (173788 active at my read). Line
  numbers are from my read and may have shifted.
- Section 3 is a narrowing, not a diagnosis. I deliberately did not guess which
  of the three branches fired.
- I did not audit the eight bounded acceptance groups in
  `SLICE3-SCOPE-172905.md` against what is already implemented. Section 5 lists
  only what follows from the failure and settlement path I actually read.
- Nothing here is acceptance of W170385, and none of it is a gate.
