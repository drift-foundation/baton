# How this turn ends, and when. READ THIS BEFORE YOU DESIGN ANYTHING.

Recorded by `baton.claude`, claim341637; **amended at claim348718 to retire
the 900-second lease**, which no longer bounds this run. Read from the current
worker protocol rather than described loosely.

## THE 900-SECOND LEASE IS GONE. Read this before the history below.

W333485 supplied an accepted host permission correction and the owner closed it
**satisfying** at348699. Permission is now derived from the **persisted
authoring envelope** rather than from a fixed 900-second token:

| fact | value |
| --- | --- |
| origin | the persisted `authoring.envelope` `started_at`, before acquisition |
| execution stop | **origin + 4740 seconds** |
| permission expiry | **origin + 4800 seconds** |
| latest full invocation admission | origin + 1110 (remaining execution must fit 3600 + 30) |
| remaining at an acquisition 120s in | 4680 permission seconds |

Replay does **not** reset origin, and restart is cancellation-only. These are
the accepted controlled-clock facts from
`decisions/host-policy.json`; read them there rather than trusting this prose.
They are **not** a claim that a live run has exercised this permission.

## What the earlier runs showed, now as history

| run | provider served | ended | result |
| --- | --- | --- | --- |
| parent run340016 | 869.45s | on its own | candidate retained, `verification-failed` |
| parent run340352 | 904.78s | **900s lease, signal 15** | nothing frozen |
| run341360 | 905.18s | **900s lease, signal 15** | nothing frozen |
| run345039 | 461.10s | on its own | first candidate, first gate measurement |
| run345388 | 789.14s | on its own | gate measured, 16 storage errors |
| run345822 | 733.29s | on its own | **the gate PASSED** |

Those two killed runs are **why the old lease was corrected**, and they are the
reason this document exists. **They are no longer a constraint on you.** The
last three runs all returned on their own well inside the old limit; you have
far more permission than any of them had.

## Ending the provider turn IS freezing. There is nothing else to call.

Read from `claude_agent.ClaudeAgent.work` and `baton_worker`:

1. **You stop. The provider process returns.** That is the only trigger.
2. The adapter then measures the line delta against the declared base.
3. It runs **the task's own verification command** — separately bounded, 30
   seconds — and writes `verification.txt`.
4. It revalidates the measurement, then chooses a disposition through
   `_disposition`: `candidate`, `verification-failed`, `no-candidate` or
   `provider-failed`.
5. **It commits the line whatever the disposition is.** Deliberately: the
   manager freezes a checkpoint after every ending and its profile refuses a
   dirty worktree, so a turn that produced changes and declined to commit would
   leave the line unfreezable.
6. It publishes the proposal, and `baton_worker.publish_completion` writes
   `/output/output.json` **last and atomically** — *"its presence under its final
   name is the completion signal, so no separate signal is needed and none is
   invented."*

**Consequences, and they are the point:**

- **There is no submit call, and nothing to submit twice.** You do not freeze a
  result; you *finish*, and the adapter freezes. Repeated terminal submissions
  are neither possible nor wanted.
- **Steps 2 to 6 need wall-clock time after you stop** — the verification
  command alone may take up to 30 seconds — and **none of it happens if the
  lease kills you first.** That is exactly what happened twice.
- **`verification-failed` is a real, published, committed result.** A failing
  gate honestly returned is worth incomparably more than a better candidate that
  never existed. Both prior failures produced *nothing*.

## What bounds you now, and what you still owe the adapter

**Record a monotonic start as your first act** and check elapsed time against
it. The old **600/720 cutoffs are HISTORICAL PLANNING, not your permission** —
they existed to survive a 900-second lease that no longer applies, and nothing
in this packet restates them as policy.

| fact | value |
| --- | --- |
| provider turn | **3600 seconds** |
| verification command | 30 seconds, separately bounded |
| total | 4800 seconds |
| cleanup reserve | 60 seconds |
| execution stop | origin + 4740 |
| permission expiry | origin + 4800 |
| invocations | one, no retry, `report-and-hold` |

**The one timing obligation that has not changed.** Steps 2 to 6 above happen
**after you stop**, and the verification command alone may take up to 30
seconds. **Leave the adapter room to finish**: stop with a comfortable margin
before the execution stop, summarise what you changed, what the gate said and
what is unfixed, and let the provider return. A turn that works until expiry
still produces nothing, and that is true under any limit.

**What this is not.** Not a renewal, not a controller modification, not
automatic termination, not a runtime guarantee, and not authorization to
fabricate success. Existing tokens keep their old policy and are not
converted.

## If the gate fails or time is short

**Return an honest incomplete or failing result.** Say exactly which cases
failed and how, which changes are retained and where, and what is unfixed. Do
not keep writing until expiry hoping to convert a failure into a pass — that
trade has now been taken twice and returned nothing both times.

Do not weaken a test, delete a case or relax an assertion to obtain a green
gate. The review checks for exactly that, and a bought pass is worse than the
honest failure it replaced.
