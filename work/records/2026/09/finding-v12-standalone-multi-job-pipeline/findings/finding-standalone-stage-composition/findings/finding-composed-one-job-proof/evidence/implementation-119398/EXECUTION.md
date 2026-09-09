# Execution account — W119114 claim119398

## What was run, and what it answered

`repro-quiescence-gate.py` is the executable reproduction. It composes the REAL
`tools.stage_execution.operations_from` factory over real local Authority, Job,
Control and Integration stores, three configured roles, the real Git checkpoint
profile over a real Git source, and the accepted deterministic engine seam. It
then drives ORDINARY manager ticks (`job_manager.sweep`) and one real worker
turn through `baton_worker.serve_exchange` over the actual `claude_agent`
workload with an injected child-process provider.

Run it from any directory:

    python3 repro-quiescence-gate.py

## Measured result

The implementation half of the composed one-Job lifecycle runs end to end on
ordinary ticks, with no operator transition after submission:

| Boundary | Measured |
| --- | --- |
| pool activation, offer, claim, attempt, activation | performed by the factory's own operands |
| private line materialization at the declared base | real clone/detach through the accepted checkpoint profile |
| writable line mount for the writer attempt | `<storage>/.baton-review-lines/<line>/checkout` |
| real worker turn | `claude_agent` commits the line, bundles the objects, runs the task's verification argv and emits `baton.git-proposal/1` + `baton.git-ordinary-tests/1` |
| quiesce, reconcile, line-consumable proof | performed over the exact runtime |
| freeze/seal | `output: sealed`, real result manifest |
| intake | real receipt (`intake_receipt_of` non-null) |
| retention | one retained artifact (`retentions_of` length 1) |
| publication | real `retain_proposal` + `publish_candidate` against the Authority, while the producer assignment is still live |
| checkpoint freeze | real checkpoint, which FENCES the producer assignment |
| ordinary cleanup | `execution_runtime: destroyed`, `cleanup: retained` — positive absence of the exact runtime |
| implementation stage | `completed` |

## The blocker the proof exposed

With every step above committed, the Work is left at:

    "phase": "block",
    "gate": {"token": "runtime-quiescence:1", "kind": "runtime-quiescence"},
    "ready": false

and the review stage's admit is refused every tick:

    '0000000a-W1' is 'open'/'block' with handler none and gate a dict;
    an offer is issued only against open, queued, unclaimed, ungated Work

The review stage of a composed Job is another assignment of the SAME Work — the
assembly refuses a review stage naming another Work, and `create_line` binds one
`(authority_uuid, work_id)` pair — so this gate holds the whole lifecycle.

Nothing in this build discharges it. Verified against the current tree:

- `baton_v12.worker_manager.SESSION_OPERATIONS` is
  `('project_work', 'slot_holder', 'claim', 'settle_operation',
  'assignment_of', 'cancel', 'publish_answer')`; `satisfy_gate` is absent, so
  the manager's `AuthorityPort` cannot reach it.
- Searching `src/`, `tools/` and `v12/worker/` for `satisfy_gate` outside
  `src/baton_v12/authority/` returns nothing: no production caller exists.
- `attempts.py` states it deliberately:
  "WHAT THIS DOES NOT DO: it does not satisfy the quiescence gate the authority
  installs."

The manager DOES now hold the evidence the gate requires — `authorize_cleanup`
observed the exact runtime positively absent and recorded
`execution_runtime = destroyed`. What is missing is an accepted operation that
carries that already-held evidence to `Authority.satisfy_gate` as
`{"kind": "runtime-absent", "runtime": <runtime_id>}`. This is reported as
separate accountable Work rather than invented inside the five-path scope: an
assembly that asserted positive absence to the Authority itself would be the
deployment certifying the manager's own observation.

## Deterministic seams, named rather than implied

Two, and both are the allowance this campaign already accepted:

1. The ENGINE is a callable answering `run`, `ps`, `inspect`, `stop` and `rm`
   with no daemon. It models three real facts: a stopped container stops
   running, a removed container is positively absent to a later inspection in
   the engine's own absence sentence, and the custody helper answers the verb
   it was asked for (through `tests.manager.test_custody.reported`).
2. The PROVIDER inside the real `claude_agent` workload is injected, exactly as
   that module's own accepted suite injects it. Version control is real.

Everything else — the factory, the stores, the drivers, the line, the seal, the
intake receipt, the retention decision, the publication and the cleanup — is the
accepted production operation.
