# Finding: prove v12 local isolated execution

Work `W1425` (`43c55d4b-W1425`), contained by the v12 isolated-agent-worker
campaign at `work/records/2026/08/finding-v12-isolated-agent-workers/`.

## Assignment boundary

Prepare the M2 implementation boundary for one OCI reference worker, the
trusted host-side Worker Manager and one complete local isolated lifecycle
against the frozen M1 contracts. Decompose independently accountable
implementation and verification deliverables into child Work. This reviewer
assignment owns research, durable findings, planning, coordination and
independent review; it does not authorize this reviewer to implement protocol,
application, authority, runtime or adapter changes.

## Operational finding at intake

- **Observed 2026-08-22:** W1425 became ready after satisfying closure of its
  W1408 dependency but had no repository binding, so there was no exact Work
  dossier to read before execution. The reviewer claimed the ready Work,
  recorded the absence here, and will bind this canonical record before deeper
  contract and implementation research.

## Confirmed prerequisite

- **Confirmed 2026-08-22:** W1408 closed satisfying after all three M1
  contracts and their cross-contract freeze passed independent review. M2
  must implement, not reinterpret, `urn:baton:worker-control:1.0`,
  `urn:baton:agent-session:1.0` and
  `urn:baton:worker-conformance:1.0`, together with W151's authoritative
  assignment identity and effectively-once settlement rules.

## Research status

**Confirmed 2026-08-22:** the frozen contracts and current proof have been
revalidated. The remaining approval question is the placement of the
authority-owned assignment substrate described below; implementation does not
start until that placement is ruled and the exact child boundary is pinned.

## Managed Docker inspection boundary — confirmed 2026-08-22

The first two managed-review attempts failed when the non-interactive Codex
context requested approval for `docker version --format '{{json .}}'`. The
dispatcher correctly denied the interactive escalation and quarantined each
context, but a restart could not correct the missing capability and merely
repeated the same failure.

The approver authorizes read-only host inspection through exactly
`docker version`, `docker info`, `docker inspect`, and
`docker image inspect`. Unrestricted `docker` is not authorized: it can mount
host paths or the runtime socket, run privileged containers, and mutate or
destroy containers, images, networks, and volumes outside the filesystem
sandbox.

Mutable OCI lifecycle operations belong behind the trusted Worker Manager's
validated runtime adapter. The adapter must constrain image identities,
container names, mounts, privileges, output roots and cleanup; models receive
the manager contract rather than an arbitrary Docker shell. The read-only
inspection allowance is a deployment policy prerequisite for M2 research and
does not weaken that implementation boundary.

## Current-tree baseline — observed and confirmed 2026-08-22

- **Observed:** `v12/` is a self-contained Node package whose reviewed proof
  imports no v11 product module and whose disposable state remains under the
  configured external `/tmp/baton-v12-poc` root. `npm test` passes all 78
  current PoC tests, and the read-only placement plan resolves every mutable
  path beneath that external root.
- **Observed:** Docker client and daemon 29.1.3 are reachable. The exact
  approved inspection forms `docker version`, `docker info`, `docker inspect
  node:24-slim`, and `docker image inspect node:24-slim` all complete without
  interactive approval. The local image resolves to
  `node@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03`.
- **Confirmed:** the W151 assignment model passes 54/54. The frozen M1 design
  gates pass 12/12 worker-control, 56/56 agent-session, and 73/73 runtime-
  conformance tests with the recorded system Python environment. The
  repository `.venv` intentionally lacks the design evidence's `jsonschema`
  dependency, so one combined `.venv` invocation fails during collection;
  that is a test-environment prerequisite, not a contract failure.
- **Observed:** W2845 is the one Work bound to the nested managed-Docker-policy
  record and is actively handled by `baton.claude`. It is ledger-top-level
  rather than contained by W1425. No duplicate Work is created and no claim or
  file owned by that implementer is disturbed. The installed read-only policy
  already unblocks M2 research, so W1425 does not gain a scheduler dependency
  on W2845.

## The accepted PoC is evidence, not the M2 implementation

**Confirmed:** the current `v12/` proof is deliberately `0-spike`. In
particular, `v12/src/envelopes.mjs` accepts draft envelopes,
`v12/src/claim_token.mjs` keeps the offer verifier and signing secret in one
process, and `v12/src/manager.mjs` records `generation: 1` with authority-local
`W...` selectors. Its ACP path is Claude-specific. Those were accepted W76
constraints and are not defects to patch in place while pretending they
implement the frozen contracts.

M2 must instead implement these frozen deltas:

1. authority-owned per-Work contract selection, monotonically increasing v12
   assignment generations, the full `(authority UUID, canonical Work ID,
   participant, generation)` identity, fenced generations, typed
   `runtime-quiescence`/`contract-runtime` gates, and exact assignment-aware
   claim/end/close/transition settlement;
2. a shared durable Worker Manager control store for offer, fixed claim
   operation, runtime-attempt identity, orthogonal runtime/output/disposition
   observations, output freeze, intake and cleanup; process memory is only a
   cache;
3. exact `urn:baton:worker-control:1.0` envelopes and manifests, exact
   negotiation, limits, canonical digests, the closed error taxonomy, and
   effectively-once operation signatures/results/retirements;
4. a provider-neutral `urn:baton:agent-session:1.0` boundary with separate
   consent and execution postures, one fresh session per posture/epoch,
   supervised turns, denial of unexpected approvals, normalized bounded
   events, and cancellation observations that never masquerade as runtime
   quiescence; and
5. one local OCI adapter and `baton-worker` entry point using pinned image and
   policy inputs, read-only Git or directory sources, one private writable
   workspace/result boundary, no authority/canonical repository/runtime
   socket/nested runtime, positive runtime identity and destruction evidence,
   and the complete applicable `local-oci` conformance core.

The reusable concepts are narrow: the existing strict input containment,
manifest hashing, trace redaction, container argv construction and positive
absence checks in `v12/src/{input_source,manifest,trace,runtime,container}.mjs`
are candidates to revalidate and adapt. The orchestration, token, envelope and
ACP modules are behavioral references only until replaced by 1.0-compliant
implementations.

**Observed:** there is currently no Dockerfile/Containerfile or packaged
`baton-worker` entry point. `v12/src/container.mjs` invokes Docker directly,
has no Podman/runtime-neutral adapter boundary, and performs mutable engine
operations itself. The proof materializes one directory input and one
directory result only; it has no read-only Git-source implementation. No 1.0
schema is consumed by the Node package, and neither the manager nor token
issuer has a shared durable database. These are M2 deliverables, not existing
reuse.

## Scope clarifications for M2

- **Confirmed:** the later W1425 ruling supersedes the remote tail of parent
  PLAN item 6. M2 implements and proves local OCI only. Remote transport and
  provider-specific Claude/Gemini/Codex certification belong to M4/W1429.
- **Confirmed:** M2 may use the deterministic scripted agent required by the
  conformance contract. A live model-provider run is neither needed nor
  sufficient for the model-free local conformance verdict.
- **Confirmed:** proposal refresh/rebase, clean verification, technical
  review, approval and canonical integration remain M3/W1427. M2 may freeze
  and collect a declared non-Git result or immutable local artifact only as
  needed to prove the worker-control lifecycle; it does not build the proposal
  pipeline.
- **Proposed:** keep root packaging, deployment and production rollout outside
  M2. The final proof uses a disposable authority, fixture repositories and
  explicit external state, just as W76 did, while exercising the frozen 1.0
  contracts rather than the draft spike.

## Proposed implementation slices and ownership

1. **V12 assignment authority substrate.** Implement the additive W151
   authority fields, exact generation-bearing operations, typed gates and
   operation retirement/reconciliation, with positive, negative, legacy-v11,
   retry and race tests. This slice owns authority/schema/transition/projection
   code only; it owns no runtime or manager code.
2. **Durable Worker Manager core.** Implement the shared control store,
   worker-control 1.0 codec/validation, offer/settlement/restart machinery,
   agent-session normalization and a runtime-neutral adapter interface. This
   slice owns manager/control-store/session modules and contract tests; it
   does not issue Docker mutations directly.
3. **OCI reference worker and runtime adapter.** Implement the constrained
   mutable adapter, pinned `baton-worker` image/entry point, source
   materialization, private workspace/output, runtime identity labels,
   inspect/cancel/collect/destroy and positive-absence evidence. This slice
   owns OCI/container/worker modules and fixtures, not authority semantics.
4. **Local lifecycle and conformance proof.** Compose the three preceding
   slices against a disposable authority and run every applicable `local-oci`
   portable case. This is verification/evidence ownership: it may add harness,
   fixtures and retained evidence but does not silently repair implementation
   while certifying it.

**Proposed dependency order:** authority -> manager -> OCI worker/adapter ->
local proof. This deliberately leaves only one implementation child runnable
at a time and avoids overlapping file ownership.

## Required regressions and evidence

The implementation handoffs must require, at minimum:

- positive Git and directory input lifecycles from offer through consent,
  canonical claim/generation mint, activation, bounded activity, quiescence,
  freeze/collect and return;
- expired, replayed, forged and cross-bound token refusals; moved Git ref,
  directory digest mismatch, path traversal/symlink/overlap, undeclared or
  missing output, pre-claim write/tool attempt, authority/canonical/runtime-
  socket reachability, policy drift and unexpected approval refusals;
- stale generation activity/result/publication refusal after pass, release,
  close, cancellation and immediate successor claim;
- ambiguous claim and mutation reconciliation by exact operation signature,
  operation-id collision refusal, manager restart before/after acceptance,
  claim, runtime start and output freeze, duplicate runtime start, duplicate or
  regressing observation, and immutable replayed result;
- cancellation fence-before-stop ordering, distinction between agent and
  runtime quiescence, force-stop/positive absence, uncertain runtime gating,
  retained/sealed output intake, and cleanup blocked until intake policy; and
- immutable evidence naming full assignment, runtime attempt, image/policy/
  adapter/input/output digests and exact workflow receipts, with canary scans
  over every required durable surface and no credential-bearing locator.

Focused verification is the 54-test W151 gate, all 141 frozen M1 design tests,
the self-contained v12 gate, new implementation unit/integration/race/restart
tests, and an independently assessed local-OCI conformance run. A count alone
does not certify: every applicable portable case must carry its required facts
and exact evidence, and the derived verdict must be `certified`.

## Open placement decision

**Open for approver ruling 2026-08-22:** W151 requires the Baton authority to
own assignment contracts, generations and gates. The campaign also says
existing v11 product paths (`src/baton_work/`, root tests/recipes and release
surfaces) remain outside the isolated `v12/` edit boundary until separately
approved integration Work. Decide whether W1425 is that approval for an
additive mixed-v11/v12 authority slice in `src/baton_work/`, or whether M2 must
first implement a self-contained disposable v12 authority under `v12/` and
defer product integration. The first is recommended because a sidecar or
manager-local generation counter would contradict W151's authority ruling;
the change must remain additive and preserve every v11 contract by default.

## Authority placement ruling — confirmed 2026-08-22

The open placement proposal above is resolved by approver message 2914, and
its recommendation to modify `src/baton_work/` is rejected for M2. W1425 must
implement a **self-contained disposable v12 authority under `v12/`**. It does
not modify `src/baton_work/`, v11 behavior, root tests/recipes, deployment, or
current release surfaces.

Within the proof, that v12 authority is the exclusive owner of per-Work
contract selection, assignment-generation allocation, live and fenced
generations, typed scheduler gates, and authoritative operation settlement
under W151. The Worker Manager may submit and reconcile operations but cannot
own, mirror or repair those facts. A sidecar generation counter is forbidden.
Reuse of v11 concepts or copied implementation is allowed only without import,
runtime or storage coupling to the v11 product.

The four implementation slices below proceed under that boundary. Product
integration, migration into the existing Baton authority, and release-surface
adoption require separately approved later Work.

## Child execution order — confirmed 2026-08-22

The four proposed slices are approved in the recorded order:

1. W2928, disposable v12 assignment authority;
2. W2929, durable Worker Manager core;
3. W2930, OCI reference worker and runtime adapter; and
4. W2931, independently assessed local lifecycle/conformance proof.

Each receives its own child dossier and ledger Work. Explicit dependency edges
serialize them, and W1425 itself waits on the final proof. Only the authority
slice is initially routed runnable to implementation; later slices return to
review when their predecessor closes so their implementation boundary is
revalidated against the landed tree before handoff.

## M2 host implementation replanned in Python — confirmed 2026-08-23

The campaign's host-language ruling supersedes M2's assumption that the
host-side Node proof would grow into the authority, Worker Manager, or OCI
runtime adapter implementation. The existing Node modules remain executable
reference evidence only. V12 host-side authority, scheduler, Worker Manager,
durable control store, and runtime adapters are Python; provider-native code
may use Node or another practical language only inside the isolated worker.

The child sequence remains conceptually authority, manager, worker/runtime,
and local proof, but its implementation boundaries must be revised before
more execution. W4 is replanned as the Python Worker Manager. W5 must separate
the Python host OCI adapter from the opaque provider-native worker image. W6
must certify the language-neutral contracts against that composition. No
reviewed state-machine or conformance decision is discarded merely because
its first executable reference was Node.
