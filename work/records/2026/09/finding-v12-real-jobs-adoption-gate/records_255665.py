"""Claim-255665: the P1 traced to a concrete gap, and a hazard fixed."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255665; RETURNED INCOMPLETE

Review 2026-09-24T09:35:15Z raised a P1 and corrected two of my coverage
claims. Both are answered with measurements rather than argument.

## P1 — POSITIVE PRIOR-FENCE RECOVERY REMAINS **OPEN**, and now has a cause

**`GAP-255665.md` is the concrete product gap**, with exact affected paths and
an exact proposal. Established from the preserved run's own control store,
opened read-only, and reproduced deterministically at fake boundaries.

The preserved run's two attempts: `execution_runtime: quiescent`,
`cleanup: pending`, `output: open`, `worker_disposition: none`, runtime
attached; `attempt.cancel` committed with its own `authority_operation_id`; and
`runtime.deadline-pin` whose document reads **`policy: null`** — because
`tools/single_worker.py:2051` starts without a `deadline_policy`.

All three supported endings were tried against that exact shape:

  * **`intake.abandon_attempt`** refuses at the Authority — it derives its OWN
    fence identity, so over a generation the cancellation already fenced it
    issues a SECOND cancel instead of replaying the first;
  * **`intake.authorize_cleanup`** does not refuse: with no intake receipt it
    answers `_block_on_intake`, moves the axis to `blocked-on-intake`, calls no
    adapter and commits no cleanup;
  * **`deadlines.advance_deadline`** — the one place this build DOES recover a
    fenced generation, and it does it by retrying the committed cancellation's
    own authority operation — refuses because the pin carries no policy.

So the runtime, its two roots and the installed gate stay unsettled with no
operation that can settle them. The proposal is Correction A in the gap page:
replay the committed cancellation's authority operation in the abandonment's
fence step, exactly as `deadlines._cancel_for_deadline` already does.
`intake.py` is **not an owned path**, so it is a proposal for coordination and
not a change. Nothing was worked around: no refusal caught into success, no
fence relaxed, no replacement assignment, no coverage removed.

## The coverage corrections, both accepted and both measured

**The stage IS a caller operand and I was wrong to say otherwise.** Measured:
an altered `job_id` refuses through adoption; an altered `stage_id`, `episode`
or `kind` was **ACCEPTED**. `kind` decides MOUNTS — a review `kind` over an
implementation attempt recovers the frozen checkpoint where the private line
belongs — so that was a live hazard.

**Fixed where a durable record exists.** `tools/stage_execution.py` —
an owned path — now binds `stage_id`, `episode` and `kind` against the recorded
allocation's own columns, and the routed case proves each refuses without
reaching the engine while the recorded stage still works. The unpooled
composition has no allocation; inventing a second source of truth for it is a
proposal on the gap page rather than something done here.

**A restart carrying a different retention policy is refused**, with the first
policy's ending untouched and no second one settled.

**The discharge-severed case is NOT remote-commit-with-lost-receipt**, and the
distinction is kept: the accepted
`test_remote_discharge_replays_after_local_receipt_commit_interruption` in
`tests.manager.test_runtime_deadlines` is that shape, and an equivalent for the
abandoned gate is still owed.

## REMAINING

  1. positive prior-fence recovery — OPEN, pending the ruling on Correction A;
  2. a remote-commit/local-receipt-loss case for the ABANDONED gate discharge;
  3. first-call crash and launch-absent alternate recovery; unaffected
     successful-output coverage;
  4. the supervisor's explicit shutdown declaration;
  5. the two operator grants documents with validation and readback;
  6. the executed-image fault diagnosis;
  7. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

## Standing constraints

The deployed snapshot and the preserved instance are read-only and were read
read-only. No live rerun, deployed-store mutation, container deletion or
cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255665

### The P1, traced to a cause I could not have guessed

You were right that characterizing one refusal is not acceptance. So I opened
the preserved run's control store read-only and asked it what shape it is in,
then drove that exact shape at fake boundaries and tried every supported
ending.

The answer is a real gap and it has three parts. The abandonment refuses
because it derives its OWN fence identity over a generation the cancellation
already fenced. The ordinary ending does not refuse at all — it answers
`blocked-on-intake` and moves the axis there, which is a door onto a room with
no exit, and is a different fact from a refusal. And the deadline owner — which
IS the one place this build recovers a fenced generation, by retrying the
committed cancellation's own authority operation — refuses because the pin's
policy is null, since this composition starts without a deadline policy.

That last one I would not have found by reasoning; it came out of the pin
document in the preserved store. `GAP-255665.md` carries the exact paths, the
proposal that mirrors `deadlines._cancel_for_deadline`, and the corrections I
deliberately did NOT propose.

### And a hazard in my own file, found by being corrected

You said the stage is caller-supplied, and I had claimed the context could not
vary. Measured: `stage_id`, `episode` and `kind` were all accepted, and `kind`
decides which tree the ending recovers. That is the "ordinary pair for a
different stage tree" failure, reachable by a caller.

`stage_execution.abandon_attempt` now binds all three against the recorded
allocation's own columns. The routed case proves each refusal stops before the
engine and that the recorded stage still works. The unpooled composition has no
such record, so that half is a proposal rather than a guess at a second source
of truth.

### Verification spending

`test_abandonment` and `test_routed_abandonment` together — 23 cases, all
passing, **1.334s**, clean under `-W error::ResourceWarning`; earlier runs this
claim at 0.772s, 0.800s, 0.803s, 0.917s, 1.364s, 1.378s and routed-only 0.480s.
`tests.tools.test_single_worker` — 162 tests, OK, **9.966s**.
`tests.manager.test_runtime_deadlines` — 46 tests, OK, **0.348s**.
`tests.tools.test_stage_execution.TheDeploymentRoutesACancellationToItsOwner` —
3 tests, OK, **0.130s**. Two probes (`probe_cancel_path_255665.py`,
`probe_context_255665.py`) ran in a few seconds each and were not timed.

The 424-case suite was NOT repeated, as directed. Everything prior stands:
159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s, the combined 1.090s
and 0.632/0.701/0.371s focused runs, the earlier focused and product-suite
times, the untimed diagnostic reads, the unmeasured ~120s command-timeout run
and the earlier unknowns, alongside named **1047.869180986s**.

State: returned INCOMPLETE through baton.bug with the P1 traced to a concrete
gap and marked OPEN, and one caller-reachable hazard closed in an owned path.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255665" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
