"""Claim-255518: the gate discharge composed, and the routed path proved."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255518; RETURNED INCOMPLETE

Review 2026-09-24T09:12:54Z accepted the narrow single-worker evidence and
named the gate discharge first: "Implement the selected composed discharge and
remove the marker once that expectation passes."

Done, with the routed path that had no case at all.

## The discharge is composed

`tools/single_worker.py` gained `_discharged_abandonment`, called at the end of
`abandon_attempt`. It is deliberately `StageExecution._discharged`'s three
steps in the same order:

  1. REPLAY a committed discharge before anything mutable is read;
  2. owedness from what THIS act FENCED (`answered["fenced"]["gate"]`), never
     from today's projection — a lost receipt leaves the gate already cleared,
     so the projection would say nothing is owed;
  3. the committed cleanup as the precondition, READ from the durable record:
     an interrupted settlement journals nothing, and this gate "is discharged
     on the abandonment this manager committed and never on the absence of
     one".

A refusal from the discharge propagates. The cleanup is committed and durable,
and a retry replays it and then discharges — which is better than an answer
that hides an obligation nobody holds a receipt for.

## The routed proof — `test_routed_abandonment.py`, 5 cases

Built on the product's own `ComposedOneJobCase`, whose accepted `quiescing`
engine ALREADY models a removal, an identity-bound absence sentence and a
custody helper answering its own verb through
`tests.manager.test_custody.reported`. **No engine of mine is substituted on
this path**; the routed act runs against the same deterministic seam the
accepted lifecycle cases run against. A real submitted Job is carried by
ordinary `sweep` ticks to a STARTED runtime and the worker turn is never run —
which is the abandonment's subject exactly.

  * **the stage's own mounts, proved positively AND negatively**:
    `_SingleWorker._mounted` is called once with this attempt and
    `adopted_assignment_workspace` is never called. That is the branch the
    single-worker fixture cannot reach, because its `stage` is `None`;
  * the whole ending commits — fence, `state: absent`, both custody roots,
    `cleanup: retained` — and the discharge's gate equals the gate this act
    fenced;
  * **a FRESH composition replays it**: a second deployment over the same
    stores, which is what a restart is, returns the same operation and removes
    nothing again;
  * the router's boundaries: no recorded allocation, an allocation naming an
    uncomposed worker, and malformed or mismatched stages refused BEFORE any
    worker is reached.

## `test_abandonment.py` — 8 cases, no expected failures

The discharge case is ordinary now and the marker is gone, with a negative
beside it: no discharge is claimed over an unsettled cleanup. The replay case
counts what the world was ASKED for — removals, custody acts, credential roots
— and asserts the counts are non-zero before comparing, so the comparison
cannot pass over a fixture that performed nothing.

## An operational finding, NOT mine

`tests.tools.test_stage_execution` — 424 tests, **12 errors**, in
`AFreshPortReentersANeverStartedDelivery` and
`TheIntegrationStageConsumesTheAcceptedPort`:
`AttributeError: 'types.SimpleNamespace' object has no attribute 'reconciles'`
at `stage_execution.py:3008`, which is not code either of my claims touched.
**Reproduced against the PINNED snapshot's unmodified `tools/`** — same 12
errors — so it is a pre-existing disagreement between the committed fixture and
the committed product, not a regression from this Work. Reported rather than
absorbed or worked around.

## REMAINING

  1. positive proof that the launch and credential ROOTS are gone — a fake
     custody report is not that, and the review is right to say so;
  2. prior cancellation fence; changed reason, policy or stage context;
     adapter refusal and uncertain absence; an unaffected successful output;
  3. the supervisor's explicit shutdown declaration;
  4. the two operator grants documents with pure and fake-boundary validation
     and readback;
  5. the executed-image fault diagnosis;
  6. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution. The accepted composed fixture initialises a
throwaway version-controlled source under `BATON_V12_DISK_ROOT`; nothing in
this checkout is written by it.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255518

### The discharge is composed and the marker is gone

You said the expected failure was not an acceptance pass, and it was not meant
to be one — it was the gap stated as a property so it could not be forgotten.
It passes now. `_discharged_abandonment` is `StageExecution._discharged`'s
shape deliberately: replay first, owedness from what THIS act fenced rather
than from today's projection, and the committed cleanup read from the durable
record as the precondition. A refusal propagates; the cleanup is committed
either way, and a retry replays it and then discharges.

### And the routed path, which had no case at all

`test_routed_abandonment.py` runs on `ComposedOneJobCase` — and that base's
accepted `quiescing` engine already answers a removal, an identity-bound
absence AND a custody helper, through `tests.manager.test_custody.reported`.
So the routed proof substitutes NO engine of mine. Worth saying plainly: an
accepted custody-answering seam existed in this file all along, and had I
found it two claims ago I would not have re-derived one in `test_abandonment`.

What it proves is the branch the single-worker fixture structurally cannot
reach: a pooled worker holds a `StageComposition`, so root recovery must take
the stage's own mounts. `_mounted` is watched and called once with this
attempt; `adopted_assignment_workspace` is watched and never called. Both
directions, because an absence proof alone would also pass over a call that
recovered nothing.

A fresh composition over the same stores — a restart — replays the committed
ending and removes nothing again.

### A finding I am not claiming as mine, and did not absorb

`tests.tools.test_stage_execution` has 12 errors:
`'types.SimpleNamespace' object has no attribute 'reconciles'` at
`stage_execution.py:3008`. I ran the same two case classes against the PINNED
snapshot's unmodified `tools/` and got the identical 12. It is a pre-existing
fixture/product disagreement. I have not touched it.

### Verification spending

`test_abandonment` — 8 cases, all passing, no expected failures: 0.428s,
0.439s this claim, on top of 0.269s, 0.312s, 0.352s, 0.364s, 0.388s.
`test_routed_abandonment` — 5 cases: 0.163s, 0.193s, 0.201s, 0.292s, 0.335s,
0.366s, 0.366s. Both together: **0.747s**, clean under
`-W error::ResourceWarning`.

`tests.tools.test_single_worker` — 162 tests, OK, **10.041s**.
`tests.tools.test_stage_execution` — 424 tests, 12 pre-existing errors,
**159.910s**; a SECOND full run to list those errors was not separately timed
and I am not quoting a number for it. `AFreshPortReentersANeverStartedDelivery`
alone, 0.966s. The pinned-product comparison run, 1.170s.

Named suite subtotal unchanged at **1047.869180986s** (`verification-27.json`,
85 checks, 0 failures, pins agree). Earlier product-suite time stands: 9.955s,
335.453s, 172.937s, 10.135s, 10.116s, 10.100s, the untimed diagnostic reads,
the unmeasured ~120s command-timeout run and the earlier unknowns.

State: returned INCOMPLETE through baton.bug, with the discharge composed, the
routed path proved and one pre-existing defect reported.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255518" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
