# Finding: compose the local OCI lifecycle

Promoted implementation record for the fifth bounded child of W5. It is W5's
integration Job and remains top-level on disk because the parent dossier is at
maximum nesting depth.
Canonical Work: W6636.

## Confirmed boundary

Compose only reviewed W5 components with completed Python manager receivers.
Exercise the approved two-container consent/execution topology through the
trusted adapter: restricted consent, positive quiescence/destruction, exact
claim and activation, then fresh execution with the private workspace. Compose
effectively-once start/inspect/cancel/freeze/collect/destroy and positive
absence without granting engine observations authority meaning.

This Job owns integration and mutable local-engine evidence, not the component
implementations or W6's independent 109-case conformance certification.

## Acceptance

- Real Docker lifecycle covers consent/decline/activation/execution/success,
  refusal, fault and cancellation with exact durable identities.
- Restart, duplicate start, stale generation, partition/uncertain observation,
  multi-match and cleanup recovery preserve fail-closed ordering.
- No execution workspace exists in consent; consent is absent before execution
  creation; collection follows quiescence; replacement follows positive absence.
- Podman runs the same adapter contract when available; absence is recorded as
  environment evidence rather than changing the vocabulary.
- All component and manager dependencies are closed satisfying before terminal
  integration signoff; W6 remains the separate certification gate.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## 2026-08-27 independent integration review

**Confirmed:** the first-round module is valuable diagnostic evidence, not a
terminal or partial certification result. Its 24 Docker cases expose two
integration-breaking defects and its retained mutation harness reports all 18
targeted rule removals caught. The implementation correctly does not claim the
success/freeze/collect/destroy/positive-absence half or satisfying dependency
closure.

**[P0] Confirmed:** the proposed “certified arc” does not actually avoid
W6634's provisional implementation. W6634 changed the shared
`OciAdapter.start` refusal/settlement path and `OciAdapter.destroy` credential
ending in `v12/python/src/baton_v12/worker_manager/oci.py`; even an adapter
constructed with `outputs=()` and `credential_delivery=None` executes those
paths. `run_vector` also calls W6634's `_credential_mounts` for the empty
delivery. W6634's seventh review requested changes and its terminal outcome
explicitly says the retained code is provisional. The new cases therefore
exercise a provisional combined tree. They may be retained as reproductions,
but no part of their result is independently accepted until replacement
output-custody and credential-delivery Work establishes the shared path.

**[P0] Confirmed:** the accepted OCI adapter and reference worker do not join.
The adapter's `run_vector` supplies no environment, while the worker requires
`BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`, `BATON_WORKER_CONTRACT`, and
`BATON_WORKER_ROLE`. The real-engine evidence records an immediate exit 2 with
no frame. This blocks every successful execution ending.

**[P0] Confirmed:** reconciliation treats membership in `docker ps --all` as a
running runtime. `reconcile_runtime` attaches the sole matching identity
without asking `adapter.observe`; an exited worker is consequently stored as
`execution_runtime=running`. Exact observation must distinguish live,
quiescent, absent, and uncertain before the manager advances lifecycle state.

**[P1] Confirmed:** consent is not composed “through the Python manager” as the
confirmed boundary requires. The test drives a consent-posture adapter and
writes the `consent_runtime` axis directly because no manager operation joins
them. That is a missing production composition seam, not merely later polish.

**[P1] Confirmed:** W6636 consumes W19784's input-root authorization and
assignment-manifest delivery, but the ledger has no dependency edge to W19784.
The same round also found W19784's three `check_input_pair` receiver parameters
missing from the contracts inventory, making the full-tree gate one failure
redder than its six accepted baseline failures. The ownership gap needs a
separate follow-up to the closed Work and W6636 must depend on that correction.

**Open decision:** approve the prior W6634 checkpoint's decomposition into two
independently reviewed successors: output custody and credential delivery. The
shared start/destroy crossing must be assigned explicitly rather than treated
as accepted by either slice. W6636 then needs bounded correction Work for the
worker launch contract, exact runtime observation, and manager-owned consent
composition before this integration can resume.

**Verification limitation:** the reviewer invoked the exact composition module
under the source layout. Import and discovery succeeded, but the managed shell
denied its nested Docker-socket access at `setUpClass`; policy forbids an
escalated retry. A standalone `docker info` independently confirmed Docker
29.1.3 and its daemon are reachable. The implementer's retained real-engine
transcript remains evidence, but it is not an independent reviewer rerun.

## Approver decomposition ruling — 2026-08-27

Do not waive W6634's non-satisfying outcome and do not resume W6636 over its
provisional shared paths. Approve the recorded split into two independently
reviewed provider Works:

1. output custody; and
2. fresh-run credential delivery.

W6636 explicitly owns their shared start/destroy settlement crossing and the
later restart-adoption, reconciliation and orphan-convergence matrix. The two
component successors must not claim that integration acceptance themselves.

Also create four bounded correction Works discovered by composition:

1. deliver the four non-secret `BATON_WORKER_*` launch values through the OCI
   seam and prove the adapter-started reference worker remains runnable;
2. reconcile exact runtime state through `adapter.observe`, preserving
   uncertainty and never recording an exited runtime as running;
3. add the production manager operation that owns consent-runtime creation,
   teardown and ordering; and
4. follow up closed W19784 by registering the three `check_input_pair`
   receiving parameters and restoring the aggregate contracts inventory.

Record W19784 itself as a historical W6636 dependency and make all six new
Works live W6636 blockers. Retain the 24-case module and mutation harness as
diagnostic starting evidence. W6636 resumes integration only after all six
providers close satisfying; then it must replace the current expected-failure
observations with positive real-engine regressions and obtain independent
Docker review.

## Decomposition coordination result — 2026-08-27

**Confirmed:** the approver-authorized decomposition is now durable and
ledger-bound. W26283 owns output custody; W26284 owns fresh-run credential
delivery; W26291 owns the four-value reference-worker launch environment;
W26294 owns exact observation-backed reconciliation; W26295 owns the
manager-composed consent runtime; and W26296 follows W19784 for the missing
`check_input_pair` receiver inventory.

**Confirmed:** W19784 is the historical assignment-identity dependency. Its
closed satisfying result does not substitute for W26296's bounded inventory
correction.

**Operational finding:** the canonical v11 CLI refused the approver-requested
W6636 dependency edge to closed W19784: “a dependency on finished work gates
nothing — depend on follow-up Work instead (WS-2 ruling: new blockers target
only open Work).” No workaround was attempted. W19784 is therefore preserved
as dossier provenance and as W26296's atomic `follow-up-of` relation, while
W26296 is the permitted live gate.

**Confirmed:** all six new Works are required live W6636 blockers. W6636 keeps
ownership of the providers' shared quiescence/output-read/container-removal/
credential-removal/clean-settlement crossing plus restart adoption, recovery,
reconciliation policy, and orphan convergence. No provisional W6634 code is
accepted by creating these successors.
