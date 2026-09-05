# Observe a faulted v12 exchange after its container exits

Ledger Work: W85500

## Confirmed defect — 2026-09-04

The W71917 run6 worker wrote a durable correlated terminal document with
`ending: faulted` and `fault_code: output`, then its Docker container exited
with code 1 at `2026-09-04T09:10:41Z`. More than a minute later the live
persistent Job Manager still projected the stage as `starting`, the runtime as
`running`, and `exchange: null`. Docker independently reported the exact
runtime as exited, while the manager process remained alive and continued its
one-second sweep.

The durable terminal was present under the attempt's launch exchange before
the status read. Losing it because the runtime is no longer live contradicts
the accepted file-exchange boundary: the manager may die or restart, and a
terminal file must remain observable without stdin/stdout ownership or a live
container.

## Decision

Exchange observation is reconstructed from the durable attempt exchange and
does not require successful adoption of a live runtime. A correlated faulted
terminal is not a successful answer and authorizes no freeze, intake, pass, or
cleanup. It does, however, make the stage truthfully exceptional under the
existing `report-and-hold` policy instead of leaving it apparently starting.

Runtime truth and exchange truth remain separate axes. Observing the terminal
must not manufacture quiescence, while observing the exact container as exited
must not continue to publish it as running. Repeated sweeps and a manager
restart replay the same facts idempotently and do not invoke the provider or
publish the command again.

## Acceptance

- A worker writes a correlated faulted terminal and exits before the next
  manager sweep; the next status reports the stage exceptional with the typed
  exchange fault.
- The same result is reconstructed after a fresh Job Manager incarnation.
- No freeze, intake, Authority pass, cleanup, replacement attempt, duplicate
  command, or duplicate provider invocation follows from the fault alone.
- Exact exited-runtime truth is no longer projected as running.
- One faulted stage does not prevent observation or progress of another stage.
- Focused tests cover the race where the terminal appears and the container
  exits between sweeps.

## Reviewer revalidation — 2026-09-04

### Confirmed — exchange adoption is already durable-file-only

`tools.single_worker._SingleWorker.observed_exchange` reconstructs the launch
delivery with `_adopted(attempt_id)` and passes its exchange roots directly to
`worker_manager.exchange.observation`. `launch.adopt` validates the immutable
launch document and its two on-disk namespaces; it neither lists nor inspects
the OCI runtime. A stopped container therefore cannot by itself make this
reader return `None`.

This corrects the initial hypothesis in the plan: the word *adopt* here means
adopting durable launch material, not adopting a live runtime. The run6
`exchange: null` has a separate, confirmed source. `tools.job_manager status`
deliberately constructs `_ReadOnly`, whose `ManagerOperations` has no
`observe_exchange` capability, so that command always reports `exchange:
null` even while a production serving deployment can reconstruct the files.
The terminal was not lost by the exchange parser; the operator-facing reader
was never given a way to look.

### Confirmed — an attached runtime is never observed again on a fault

The production composition calls `reconcile_runtime` from
`_SingleWorker._prepared` while launching or recovering a stage that still
projects `claimed`, and from `_SingleWorker.ending` after an `answered`
terminal. Once a start attaches a runtime, ordinary sweeps only read the
persisted attempt row. No serving pass asks the OCI adapter about that exact
runtime again.

That omission is permanent on the fault path. The existing projection already
maps a correlated `faulted` exchange to `exceptional`; `owed_exchange` grants
no act for an exceptional stage, correctly preventing the successful ending.
Consequently the answering-only ending cannot incidentally refresh the
runtime either. An engine-observed exit therefore remains persisted and
reported as `execution_runtime: running` indefinitely.

`worker_manager.reconcile_runtime` is the existing public owner of the needed
transition. It lists by the complete immutable assignment labels, observes the
exact attached identity even when the listing is empty, maps a stopped
container to `quiescent`, positive absence to `destroyed`, and observation
failure to `uncertain`, then records the result. A second runtime start is not
part of this operation.

### Confirmed — projection and successful-ending policy already contain the fault

`job_manager.projection._EXCHANGE_STATES` maps `faulted`, `lost`, and
`unreadable` to `exceptional`. `EXCHANGE_OWED` contains only `starting ->
dispatch` and `answering -> conclude`, while `_SingleWorker.ending` independently
requires a correlated `answered` terminal before quiescence, freeze, intake,
retention, Authority pass, or cleanup. The core projection needs no new fault
state and a fault must not be translated into an answered disposition.

The accepted correction is therefore observation composition, not terminal
semantics: refresh exact runtime truth in the serving loop, and let the
durable exchange reader run independently even if runtime observation is
inconclusive. A per-stage refusal must be contained so another live stage is
still refreshed and projected.

### Decision clarification — operator status gains a read-only deployment observation

This Work's acceptance that the next status carries the typed exchange fault
supersedes only the narrower W81857 decision that the standalone read-only
status command always preserve `exchange: null` because it has no deployment
factory. It does **not** supersede the read-only command's prohibition on
Authority acts or durable mutation.

The status surface may be supplied a deployment observation capability which
can reconstruct the immutable launch/exchange files. It must not construct the
full serving operations object: `tools.single_worker.operations_from`
configures durable state, opens an Authority session, and carries mint,
dispatch, ending, and pass capabilities. The observation-only composition
gets no such capabilities and performs no runtime reconciliation. Runtime
freshness in a standalone status comes from the serving loop's preceding
canonical reconciliation; if no serving loop advances the control store, the
status remains exactly as stale as that store and says so rather than writing.

### Proposed implementation boundary

- Add one explicit serving-only runtime-refresh member to the Job Manager
  operations seam and invoke it for each live attempt before the first stage
  projection in every sweep. Keep the refresh out of `status()`.
- In the single-worker deployment, implement that member with the existing
  naming-only OCI adapter and public `reconcile_runtime`. It must not read or
  register credentials, rebuild launch material, publish a command, or invoke
  the provider.
- Keep runtime refresh and exchange-file observation as two calls. Failure or
  uncertainty on the engine axis must not suppress a readable terminal, and a
  malformed exchange must not suppress exact runtime observation.
- Give `tools.job_manager status` an optional observation-only factory and
  compose the single-worker implementation from immutable configuration and
  the already-open control store. The default without that operand remains
  `exchange: null`; the supplied path must expose only canonical reads plus
  the durable exchange reader.
- Do not add Job-store receipts, copy terminal facts into the control store,
  change the status schema, or grant a recovery/replacement act. The existing
  file is the exchange record and the existing runtime axis is the runtime
  record.

### Baseline

Before implementation, the current tree passes 74
`tests.tools.test_single_worker` cases and 70 combined
`tests.job_manager.{test_exchange,test_sweep,test_tool}` cases. Those suites do
not currently drive the sequence `faulted terminal -> engine exit -> next
serving sweep`, which is why both stale axes survive them.

## Test-change authority

This Work authorizes additive cases and the bounded editing of existing
expectations in these files for the observation-seam change:

- `v12/python/tests/job_manager/test_delegation.py`
- `v12/python/tests/job_manager/test_sweep.py`
- `v12/python/tests/job_manager/test_tool.py`
- `v12/python/tests/tools/test_single_worker.py`

The authorized expectations are limited to the new serving runtime-refresh
member, the optional status observation factory, and the fault/exit race,
restart, replay, no-success-act, and stage-isolation properties above. No
existing success, correlation, custody, or failure-containment expectation may
be weakened or deleted.

### Review scope clarification — 2026-09-04

The implementation disclosed a necessary additive shared-fixture edit at
`v12/python/tests/job_manager/fixtures.py`. That path is added to this Work's
bounded test-change authority only for forwarding supplied operation members
through `operations(**supplied)` and for modelling `refresh_runtime` with
separate refresh state and call capture. Existing `calls` semantics and all
existing assertions remain binding; this clarification authorizes no weakening
or unrelated fixture redesign.

## Review ruling — 2026-09-04 (review-2026-09-04T19-08-40Z)

Pinned before implementation, because it reverses a boundary the previous
candidate took by omission and a reader who found only that candidate's
reasoning would restore it.

### The refresh answer is a closed exact document

`isinstance(answer, dict)` plus `.get` is a floor, not a contract. The
deployment's runtime refresh answers `None` or ONE exact built-in document
carrying exactly `execution_runtime`, whose value is in the closed
`REFRESH_STATES` vocabulary. An undeclared member is refused rather than
discarded, and a `dict` subclass is refused rather than read — a subclass's
own `.get` running inside the validation is caller code executing in the seam
that exists to stop exactly that. The owner is the repository's existing
document boundary, which takes a fresh built-in copy and requires exactly the
named members.

### Containment is for named conditions only; a defect escapes

**This supersedes the previous candidate's `except Exception` containment,
recorded in PROGRESS.md on 2026-09-04 as "containment with disclosure".** That
argument does not hold on the serving path: `manager.serve` overwrites its
report every tick and answers only the last one, so a defect contained on an
earlier tick is raised nowhere, recorded nowhere, and gone as soon as one tick
succeeds. Disclosure that a successful tick erases is not disclosure.

The serving refresh pass therefore contains exactly two conditions:

- `ContractRefusal` — malformed evidence a deployment answered with, reported
  as the stage's refusal category and code and never its prose.
- `delegation.RefreshUnavailable` — the condition a DEPLOYMENT raises for its
  own known engine-reachability failures, reported as `uncertain /
  engine-unreachable` with the originating failure's type name, recording
  nothing on the runtime axis.

Everything else ends the tick and reaches whoever runs the loop.

The deployment owns the translation because only it knows which of its
failures mean the engine could not be reached. For the single-worker
composition that is `OSError` and `subprocess.TimeoutExpired` around
`reconcile_runtime` — one operational fact in two Python types, and the second
was reaching the blanket branch.

This **clarifies rather than supersedes** the acceptance sentence "One faulted
stage does not prevent observation or progress of another stage". That
sentence binds faulted stages and malformed deployment evidence, which stay
contained per stage. It was never a licence to convert this control plane's
own defects into transient report data.

### Proposal metadata states the fixture authority correctly

The 2026-09-04 scope clarification above authorizes the additive
`v12/python/tests/job_manager/fixtures.py` edit. Any further proposal
describes it as authorized by that clarification, retaining its narrow scope
and no-weakening constraints, rather than repeating the superseded claim that
the path is unauthorized.

## Review ruling — 2026-09-04 (review-2026-09-04T21-52-30Z)

Pinned because both statements it corrects were prose a reader would have
believed, and one of them told an operator to look for the wrong symptom.

### A dead daemon reads `policy / denied`, and no typed adapter failure is added

Measured through the real single-worker composition rather than reasoned
about. The runner is the Docker CLI, and a daemon that is not listening does
not stop the CLI from running: it runs and exits non-zero, `OciAdapter.list`
refuses the listing `policy / denied`, and `_SingleWorker.refresh_runtime`
deliberately does not translate that refusal. The stage carries `state: null`
with `detail: {"category": "policy", "code": "denied"}`.

**This corrects a promise, not a behaviour.** The containment boundary
accepted above is unchanged and still met: the refusal stays on its own stage,
nothing is recorded on the runtime axis, and the durable exchange is still
read and still projected. What was false was the previous candidate's operator
documentation and source comment, which named a dead daemon socket as an
`OSError` reported `uncertain / engine-unreachable`.

`uncertain / engine-unreachable` is therefore limited to what this boundary
can actually distinguish: an engine invocation that could not be made at all
(`OSError`) and one that hit its deadline (`TimeoutExpired`). Wrapping every
OCI `ContractRefusal` is explicitly rejected — that category also owns policy
and integrity refusals, such as a runtime the engine reports running a
different image, and calling those an unreachable engine would be a second
false promise in place of the first. Separating an unreachable daemon from
them needs a typed adapter failure, which is deliberately NOT added here and
must be designed and pinned before it exists.

### The fault/exit regression reproduces the race, not run6's fault code

The `AFaultedTerminalSurvivesTheContainerThatWroteIt` cases drive a real
`baton_worker` terminal whose fixture agent fails its turn, so the correlated
code is `fault_code: agent`. Run6's `output` code is raised when a well-formed
answer cannot name the completion envelope, which needs a broken publication
rather than a failing provider: a different defect, and not this Work's. What
these cases reproduce is the race itself — a correlated faulted terminal on
disk, the container gone, and nothing having asked — and the projection maps
every member of `exchange.FAULT_CODES` identically because it is the
terminal's `ending` that reaches `exceptional`. Test descriptions say that
rather than claiming an exact run6 reproduction.
