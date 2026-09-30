# The connected packet proof — actual partial harness and the exact next step

W236087 claim 309871. Review 2026-09-29T22-23-10Z: "If a real interruption
prevents completion, retain the actual partial harness and exact next command."
This is that record. The harness is `connected_packet_trace.py` and it RUNS.

## What already works, measured this claim

`ConnectedPacket` subclasses the accepted `correction_restart_trace.World` and
replaces exactly two things: the configuration and the submission are THIS
PACKET'S generated documents. With that:

    * `correction_packet.stage` and `bind` run against the fixture's world and
      `held_packet` accepts the result -- which means `single_worker._held` and
      `stage_execution.held_configuration` both ran over the generated
      documents inside this fixture.
    * the packet's own preparation runs through the real owner APIs in the
      fixture's DISPOSABLE stores: `configure_workspace_storage`,
      `context_delivery.configure_context_storage`,
      `certify_context_profile`, and `authorize_qualification_run` for the
      CANDIDATE qualification. No deployed store or grant is touched.
    * `stage_execution.operations_from` COMPOSES the generated deployment.
    * `correction_supervisor.supervise` runs over it, submits the packet's
      two-stage submission, and the manager ADMITS a real attempt: the outcome
      names `implementation_attempts` and a real `attempt-7b5e…` identity in its
      cleanup accounting.

## The exact command

    cd /home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python \
    /home/sl/.local/state/baton-v12-venv/bin/python -B -c \
      "import connected_packet_trace as c; w = c.ConnectedPacket(); w.setUp();
       print(w.run_packet(dispositions=['accepted'])[1])"

## Where it stops, exactly

    OUTCOME failed-or-unknown, stopped 'serving-failed'
    turns 0, reviews 0
    stage states {'implementation': 'queued', 'review': 'blocked'}
    uncertainty[0] "the cleanup window's own wait did not complete:
                    AssertionError: the scenario did not converge"

THE SCENARIO HOOK NEVER FIRES. `run_packet` drives the scripted provider from
the supervisor's own injected `sleep`, and it acts when the implementation stage
reads `waiting`. The stage stays `queued` while an attempt identity nevertheless
exists, so the 90-step guard trips. The next step is to establish what `queued`
with an admitted attempt means here -- the accepted trace reaches `waiting` by
calling its own `tick(held)` between checks, and this drives the manager through
`serve` instead, so the difference is in who sweeps and when. That is one
question, not a redesign.

## Five generator faults only the connected run could find, all fixed here

Each was a fact I had wrong, and each was found by a real refusal rather than by
reading:

    1. `required context configuration disagrees with its preconfigured owner` --
       the worker's adapter, image and retention digests must EQUAL the certified
       profile's. They are derived from the profile now, and the input manifest
       is derived from it too.
    2. the private context storage and the workspace storage must be the
       CONFIGURED ones, so they are operands rather than paths derived from the
       instance root.
    3. the stores are deployment facts, so they are operands: a disposable
       fixture puts them where it makes them.
    4. `'baton.reviewer' writes this deployment's review receipt and holds no
       review capability` -- the receipt WRITERS are not the workers. They are
       their own `receipts` block now.
    5. `'baton.merge' … holds no integrate capability` -- the integrator is a
       selection, not the accepted instance's.

AND ONE PACKET FAULT: `deployment.config_path` pointed at the instance's own
record rather than at the generated composition, so `baseline._retention_of`
found no retention policy digest for the cleanup identity. The generated
composition IS the configuration now, and the duplicate `composition.path` member
is gone -- two places for one fact is what the enclosing validator refuses in its
own document, and the rule is no better in mine.

## What is still owed

The four endings, over this harness: accepted-without-correction,
changes-requested then restored correction, rejected, and failure/interrupt,
each deciding its observation from canonical attachments, verdicts and positive
cleanup. `run_packet` already takes `dispositions`, `interrupt_at` and
`provider_status` for exactly those four, and `World.review` records the verdicts
through the real owner API. What is missing is the one convergence question above.
