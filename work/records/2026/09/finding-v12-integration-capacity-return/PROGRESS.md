# Progress

Implementation entries belong to the participant making changes under its claim.

No implementation has started. The record was created together with its ledger
Work at filing time.

## claim131279 — the capacity comes back, and only the capacity

Evidence: `evidence/provider-131279.json`. Candidate, all mode 0664 relative to
v12/python:

- src/baton_v12/job_manager/scheduler.py `aec56f1fe1d78bd50798403b46648c63c6c6231678971399da339246a7901194`
- tests/job_manager/test_scheduling.py `79ba448c1f21a6c92bc9230291b5bfd04273024280b00ea197d1fa700066c103`
- tests/tools/test_stage_execution.py `86610e63bb64260502a1cb1a2bb2b77aa41b9a3efee338364cb46c78dedad737`

`tools/stage_execution.py` is UNCHANGED at `2b1a4324…`; it is outside this
Work's edit scope. All four pinned base hashes were revalidated byte-identical
before any edit.

**The correction, in one branch.** `reconcile_allocations` gains
`_completed_integration(allocation, entry)`, which answers this allocation's
own validated completed integration account or absence. It reads only the
projection `stage_states` already hands in — no integration store, no Authority
store, no new schema, no mutation by status. `delegation.observation_of` has
already bound that document to the stage, episode, attempt, claimed offer and
the runtime's own fixed assignment; what this adds is the one binding that
layer cannot make, that the account belongs to the allocation being settled:
the stage KIND, the validated projected state, the EPISODE and ATTEMPT, the
PARTICIPANT, and the RUNTIME IDENTITY the completion reports it excluded. The
pool generation is deliberately not compared against the Authority assignment
generation — two different numbers, and comparing them would refuse every
ordinary completion.

**Decided before the quarantine, and why.** A validated completion is
historical committed evidence; the accepted observation contract is explicit
that a later runtime-axis uncertainty does not revoke it, and quarantining an
assignment that is already over would hold a worker against an attempt nothing
can still be running. The terminal-cleanup branch still decides first.

**What it does not do.** `completed` is not added to `RELEASE_ENDINGS`, so an
ordinary implementation or review attempt still owes its intake and its
cleanup. No cleanup authorization is invented and no receipt is fabricated: the
runtime cleanup axis is left exactly where it was, the release reason is its
own word `integration-completed`, and no reader is told the container,
credential or workspace was destroyed. What comes back is logical worker and
principal capacity.

**The consumer witness turns over.** The case that measured the defect becomes
the case that proves the fix: Job A's real terminal integration releases its
exact allocation under the new reason with cleanup still `pending`, and the
eligible Job B then reserves the SAME integration worker on ordinary ticks and
records its canonical admit receipt. Job B acquires the worker; it does not
integrate — this deployment composes no runtime port for it, and whether its
already published proposal is still current against the canonical target Job
A's integration moved stays W130224's acceptance. Capacity return does not make
a stale candidate good, and the case says so.

**Verification.** The whole `tests/job_manager` package — the scheduler's own
blast radius — passes at 629 tests. `test_scheduling` passes whole at 59,
including the 16 new controls. The accepted one-Job terminal lifecycle and
review traversal pass at 21, and the two-Job consumer class at 29. The assembly
module was not re-run whole, as the research and PLAN direct.

**Budget.** 25.52s against the 25s increment — **0.52s over**, every run
wall-timed with no untimed run. The last run is the whole job_manager package
at 7.90s, which found nothing and is the direct blast radius of a scheduler
change. Reported rather than rounded down. Nothing was borrowed from W119405's
450s campaign; the 5s independent review allocation is unspent.

**For the consumer.** W130224's frozen candidate includes
`tests/tools/test_stage_execution.py` at `a5b0e048…`; that file is now
`86610e63…` under this Work's approved scope and needs rebinding at acceptance.

State: awaiting independent review through baton.bug.
