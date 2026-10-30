# How this turn ends, and when. READ THIS BEFORE YOU DESIGN ANYTHING.

Recorded by `baton.claude`, claim341637, read from the current worker protocol
rather than described loosely. This is a **worker-visible pinned input** because
two consecutive runs before yours were killed by the lease with nothing frozen,
and the cause was not scope — it was that the turn never stopped working.

## Three runs, and the only number that matters

| run | provider served | ended | result |
| --- | --- | --- | --- |
| parent run340016 | 869.45s | **on its own** | candidate `433692c5` retained, **`verification-failed`** |
| parent run340352 | 904.78s | **lease, signal 15** | **nothing frozen** |
| run341360 (yours is the next) | 905.18s | **lease, signal 15** | **nothing frozen** |

The campaign has **one retained candidate and zero accepted ones.** The two runs
that produced nothing were not short of scope or ability; they were still editing
when the lease killed them. **Do not be the third.**

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

## The cutoffs. Planning targets inside unchanged limits.

**Record a monotonic start as your first act** and check elapsed time against it
as you go. The lease is **900 seconds** and enforced.

| elapsed | do this |
| --- | --- |
| **0s** | record the monotonic start; validate and apply the sealed recovery inputs |
| **immediately after** | **run the focused gate.** Before any further design, before expanding tests. See `TASK.md` — this is the whole shape of the turn |
| **by 600s** | **stop optional edits and iterations.** Summarise the exact state: what you changed, what the gate said, what is unfixed |
| **by 720s** | **the provider turn ENDS.** Stop working and let it return, so the adapter has its ~180s to verify, revalidate, commit and publish |
| **≥180s** | the margin that remains for the existing verifier and collector |

**What these are not.** Not a lease change, not a renewal, not a controller
modification, not automatic termination, not a runtime guarantee, and not
authorization to fabricate success. They are planning cutoffs inside the limits
already selected: provider 3600, verifier 30, total 4800, cleanup 60, lease 900,
one invocation, no retry.

## If the gate fails or time is short

**Return an honest incomplete or failing result.** Say exactly which cases
failed and how, which changes are retained and where, and what is unfixed. Do
not keep writing until expiry hoping to convert a failure into a pass — that
trade has now been taken twice and returned nothing both times.

Do not weaken a test, delete a case or relax an assertion to obtain a green
gate. The review checks for exactly that, and a bought pass is worse than the
honest failure it replaced.
