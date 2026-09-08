# Port and assembly handoff contract — 2026-09-08

Work W110774 owns this contract; W103083 consumes it. Prepared by baton.prompt
under Slawomir's instruction to accelerate W71830. This is coordination and
implementation preparation, not independent review, code delivery or live-run
authority. Existing provider gates remain in force.

## Revalidated facts

- stage_execution.Integration.run delegates to admit_accepted and currently has
  no production port. StageExecution.launch and conclude both call that run.
- integrate_next requires a recorded, activated, not-started manager attempt
  before port.run. Preparing it inside port.run is too late.
- integrate_next returns a running observation rather than waiting for a model.
- driver.admit_accepted deliberately routes re-entry over a started delivery
  through hold_interrupted. Repeating it is not normal in-process polling.
- execution.settle_observed checks result correlation, live grant and positive
  quiescence. Its integrated answer is a settlement awaiting the Authority
  receipt; it does not complete or release the integration.
- The receipt construction/read-back and complete_integrated ordering are
  currently owned inside driver.admit_accepted. The public package exports no
  normal-continuation driver. A composer that only calls settle_observed would
  leave receipt/completion uncomposed, while copying private driver helpers
  would duplicate the owner boundary.
- StageObservation currently delegates to ordinary worker exchange readers.
  The integration workload publishes its own typed result, not that exchange.

These facts were checked in tools/stage_execution.py, integration/driver.py,
integration/execution.py, integration/__init__.py and job_manager/delegation.py.
No runtime, test, store mutation or provider invocation was used for this check.

## Required behavior and division of responsibility

| Boundary | W110774 port/driver | W103083 assembly |
| --- | --- | --- |
| Construction | Accept explicitly resolved stores, identity/profile, engine/image/network, isolated credentials, group/storage and typed evidence/target bindings; reject missing/foreign inputs | Resolve configuration before durable setup; construct and release the port with other deployment handles |
| Attempt preparation | Provide prepare(stage, job) over public record_attempt/activate_assignment; replay exact identity, refuse mismatches; no runtime launch | Call preparation before first admission, using the scheduler's claimed integrator stage |
| Initial start | run(delivery, assignment) revalidates the exact live grant, typed delivery, accepted bundle and isolated writable target through accepted OCI owners | Invoke admission once for a newly prepared stage; do not block the scheduler until model completion |
| Runtime refresh | Observe through accepted adapter operations and reconcile_runtime; no start, replacement credentials or guessed quiescence | Use the serving mutation path to refresh; unrelated stages continue on later ticks |
| Normal continuation | Compose correlated result, positive quiescence, current live grant, Authority receipt/read-back and coordinator settlement/release through the driver owner | Invoke only for the exact delivery started/adopted as not-started by this still-live serving execution; no automatic restart adoption of a running writer |
| Restart/uncertainty | Preserve existing hold_interrupted and terminal receipt/release-tail rules; never launch a duplicate | A new serving incarnation has no in-process continuation permission; use the existing restart path |
| Status | Supply correlated read-only delivery/result observations and safe locators | Report through the existing observation-only surface without activation, refresh writes, settlement or synthetic ordinary-worker completion |
| Ending | Return the driver's measured state; never manufacture integrated results or repair target bytes | Map accepted terminal evidence to the Job's normal ending; preserve held exclusions and independent work progress |

Method names prepare and refresh are deployment seams to finalize during
implementation; their ordering and ownership above are binding requirements.
Normal continuation needs the approved public driver seam below. Do not introduce
a second coordination ledger or parse a private database to implement any row.

A live-continuation marker is local execution bookkeeping, not authority:
it binds the whole assignment and delivery, is created only after the validated
start path, is lost on restart or uncertain start, and never substitutes for
current durable owner checks. A result while the writer is still running is
pending, not successful; do not release the target. Unknown runtime is not stopped.

## Bounded public-driver extension — approved 2026-09-08

Add an explicit normal-continuation entry point (working name continue_accepted)
to integration/driver.py and export it from integration/__init__.py. Reuse the
driver's existing accepted-account, receipt and finalization owners. The default
admit_accepted restart behavior must remain unchanged. Do not add an unvalidated
resume switch or expose private receipt helpers for deployment to copy.

Approved additional W110774 paths, relative to v12/python:
- src/baton_v12/integration/driver.py
- src/baton_v12/integration/__init__.py
- tests/integration/test_driver.py, additive regressions only

Slawomir explicitly approved this operation after discussion of its normal-tick,
receipt/completion and restart boundaries. This supersedes the earlier pending
scope decision and extends W110774's prior three-path inventory to six paths.
Keep it in W110774; no separate prerequisite is needed. Revalidate accepted
provider bytes and claim before implementation, then obtain independent review.

continue_accepted must never start a worker or retry an import. It revalidates
the exact assignment/delivery/live target lease, returns running while normal
completion is pending, and completes only after valid result plus positive
quiescence, with Authority receipt/read-back before settlement/release. Preserve
held outcomes on uncertainty/inconsistency and the unchanged restart path.
The public name/signature may be finalized by the implementer at this boundary;
any behavioral or path expansion returns for explicit scope disposition.

## Focused acceptance matrix

1. A valid real bundle reaches the real worker entry with a deterministic
   provider/engine seam and imports exact disposable target bytes/modes.
2. Initial start returns running; an unrelated stage advances before integration
   completion. Later refresh supplies positive quiescence, then continuation
   issues/read-checks the exact receipt before settlement and lease release.
3. Repeated normal ticks cannot duplicate start, receipts, settlement or release.
4. A complete result with a live writer never releases the target; uncertainty,
   foreign result or lost assignment/fence/account holds/refuses appropriately.
5. Reconstructed serving state with a started delivery takes the existing hold;
   exact accepted terminal release-tail replay retains its existing behavior.
6. Wrong attempt/fence/profile/bundle and unavailable credentials refuse before
   writable exposure. Pre-mutation refusal leaves the whole target unchanged and
   supplies positive reconciliation before another writer is admitted.
7. Read-only status neither performs any of those acts nor fabricates a worker
   exchange terminal.

Keep existing driver assertions unchanged. Add direct continuation tests using
the real driver and measured target/receipt observations. Reuse W110934 OCI and
W110935 workload acceptance at their exact hashes; do not repeat their unchanged
suites. The original canonical Python-subtree implementation gate remains
required; run it for the assembled candidate with its question/budget recorded,
not once per handoff. Historical reds remain explicit, never relabelled passed.

## Serial ownership and acceptance handoff

W110774 owns integration_worker.py, tests/tools/test_integration_worker.py and
its additive parallel_test.py registry entry, plus the approved driver extension.
W103083 retains its five-path factory/observer/test scope.
parallel_test.py is shared: W110774 finishes its one registration before W103083
edits that file. No concurrent edits to that path.

W110935 technical joined acceptance is in review-2026-09-08T01-11-08Z.md;
author documentation completion and final disposition are still in progress.
Re-read its terminal acceptance before implementing against it.

The W110774 delivery must name: exact public constructor and continuation
signatures; configuration fields and refusal rules; selected entry/image
contract; candidate hashes; focused and required-gate evidence; and the precise
W103083 call sites to change. Independent review evaluates this composed seam,
then supplies an exact operator acceptance/closure command. W103083 adds only
its remaining one-Job lifecycle and custody evidence; it does not recertify
unchanged providers. No change here authorizes a live image/model or production
canonical-target run.
