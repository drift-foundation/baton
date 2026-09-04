# Serialize accepted v12 proposals through integration

Ledger Work: W71878

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

Related: W65212, W62098, and W71459.

## Confirmed scope

Compose one scheduler-owned integration queue per canonical target. Only an
immutable proposal checkpoint with a bound independent-review acceptance may
enter it. The distinct Git-aware integrator validates base/head/object
availability, review and proposal digests, approved path scope, current-target
drift, and repository policy before importing one proposal at a time into the
working tree. Conflict, overlap, missing provenance, stale review, or policy
ambiguity refuses the whole import and schedules no hidden correction.

The generic Worker Manager remains artifact-neutral. It retains and hands off
the frozen result; it does not run Git or interpret proposal ancestry. The
integrator does not redesign, auto-merge, mutate Git history, or approve its
own result. Slawomir retains final Git ownership.

## Observed baseline — 2026-09-02

- V12 authority already records proposals, verification/review/approval
  receipts, and integration attempts, but no persistent scheduler serializes
  integration work for a shared target.
- W65212 established and deployed the distinct `baton.merge` role and its
  bounded working-tree import/refusal contract. It is a v11 deployment proof,
  not the v12 queue/control-plane composition.
- W62098 rules ordinary Git base/head ancestry and explicit Work dependencies;
  no Baton-specific path-lineage or merge algorithm may be introduced.
- W71459 owns the current v11 integrator test-change preauthorization policy.
  This leaf must consume the settled rule after that ownership ends and must
  not edit the same files concurrently.

## Review-ahead scheduling ruling — 2026-09-04

The dependency on W71918 is an IMPLEMENTATION dependency, not a contract-
review dependency. Its accepted checkpoint and correction-line model must be
revalidated before this leaf changes production code, but the integration
queue's ownership, eligibility, serialization, refusal, and handoff contract
can be independently reviewed now. W71459 is already terminal and its settled
test-change rule is available to that review.

Protocol 11 cannot express this stage-scoped edge directly. Its bounded
ceremony is therefore: the eligible reviewer temporarily removes the W71918
edge, claims and completes contract review, restores the edge before leaving
review, and reroutes the still-gated Work to implementation. Restoring the
edge atomically releases the review claim, so this is deliberately a
`block`-then-`reroute` ceremony rather than a `pass`. Closing W71918 then wakes
implementation without an operator having to notice and reroute this Work.
The early review approves the contract and plan only; implementation review
still binds the eventual candidate bytes.

## Review-ahead contract review — 2026-09-04

**Observed:** The accepted Job Manager currently recognizes an `integration`
stage and projects a claimed runtime as `integrating`, but deliberately owns
only stage admission and claim receipts. Its delegation contract says verdict
and proposal import operands are W71918/W71878's and does not invent them.
There is no target queue, integration lease, import journal, or completion
composition in the accepted baseline.

**Observed:** Authority's current `proposal.target` and `canonical_target()`
are a MUTABLE EXPECTED TARGET REVISION, not a stable target identity.
`Authority.integrate` requires passed verification, accepted technical review,
and an explicit `approved` approval receipt; it then compares that revision,
advances it to the proposal candidate digest, and writes an immutable
integration receipt. It performs no Git or working-tree import. A queue keyed
by that mutable revision would split one repository into a new lock whenever
its head advanced, so it cannot enforce this Work's same-target serialization.

**Observed:** The settled `baton.merge` contract owns the trusted working-tree
side: newest-review and digest binding, whole-path authority/type/base/mode and
overlap preflight before mutation, content import without custody-mode
propagation, bounded verification, and handoff to Slawomir without Git index or
history mutation. W71459 confirms that scheduled bounded test scope grants
case-specific authority, while independent review must enumerate and evaluate
the actual existing test changes. W71878 composes this boundary; it does not
replace it with an ordinary artifact-neutral worker or a second importer.

**Required ownership split:**

- The scheduler owns durable enqueue order, one live lease per stable target,
  lease fencing, restart reconciliation, and the decision of when an exact
  eligible entry is offered to the trusted integrator.
- Authority remains the source of the immutable proposal and verification,
  review, approval, integration and target-revision receipts. Its existing
  pre-integration `approved` receipt is policy authorization to attempt import;
  it is distinct from Slawomir's post-import ownership of the canonical Git
  commit.
- The Git-aware integration profile owns object/base/head validation,
  whole-candidate working-tree preflight, import, and bounded post-import
  verification. The generic Worker Manager receives no canonical checkout,
  runs no Git, and records no competing target or receipt state.
- Slawomir alone decides and performs Git index/history mutation after the
  prepared working-tree diff is handed off.

**Required identity and eligibility model:**

- A `canonical_target_id` is a stable deployment/profile identity for the
  repository and target line being mutated. It is separate from the expected
  base/current-target revision. Every producer that can reach the same
  canonical checkout maps to the same queue identity, including distinct
  Authorities if the deployment permits them to share that checkout;
  independent targets map to different identities and locks.
- A queue entry is immutable and Authority-namespaced. It binds the Authority
  UUID, Work and assignment generation, final W71918 checkpoint/proposal
  identity and digest, base/head and durable object transport, stable target
  identity plus expected target revision, verification/review/approval receipt
  identities and dispositions, newest review evidence, exact reviewed path-set
  digest, and scheduled test-change scope evidence.
- Eligibility requires all of those operands to validate together, including
  `verification=passed`, `review=accepted`, and `approval=approved`. An
  accepted verdict on an earlier correction checkpoint, a generic review
  without actual path evaluation, or scope for different candidate bytes does
  not enqueue anything.
- The enqueue operation allocates one durable monotonic rank only after full
  eligibility succeeds. An exact retry returns the same entry/rank; reuse of
  an operation or entry identity with any changed operand refuses. Selection
  is the smallest eligible rank for that target under the one atomic lease
  transaction; wall-clock order and row-order accident are not policy.
- A lease binds target, entry, integrator assignment/attempt, and a monotonic
  fence generation. A unique live-target constraint decides the race in the
  store. Timeout or process absence alone never authorizes a second writer;
  recovery proves the prior holder can no longer mutate before advancing the
  fence or granting another lease.

**Required execution order:**

1. Under the live lease, re-read and validate the immutable eligibility
   snapshot and prove the Authority's expected target revision still equals
   the proposal base.
2. The trusted Git-aware integrator completes its existing whole-path preflight
   before the first target mutation. Any provenance, object, digest, review,
   scope, type, base-byte, owner-write, overlap, conflict, or target failure
   records a typed refusal and imports nothing.
3. Import only the reviewed path bytes without propagating custody modes, then
   verify final bytes/modes and run the Work's bounded integration gate.
4. Only after successful import and verification may the scheduler record the
   Authority integration receipt/target-revision advance. Calling
   `Authority.integrate` before the real import would publish a canonical
   target state the filesystem has not reached.
5. Release the lease only after a terminal, reconciled account. Success exposes
   exact queue/lease/Authority/proposal/checkpoint/review/approval/integration
   identities, imported paths and verification evidence in the approver
   handoff. Refusal returns for explicit correction and never creates an
   accepted receipt or hidden merge.

**Required crash semantics:** Every enqueue, lease, preflight outcome, import
boundary, verification and Authority completion act is restart-reconcilable
from durable state and canonical reads. After interruption, all-base target
bytes may retry the same fenced entry; all-candidate bytes with expected modes
resume verification/completion without a second import; a mixed, missing or
third-byte state is a typed partial/diverged condition that retains or blocks
the target lease for explicit repair and never exposes the next entry. An
implementation may provide a stronger all-or-nothing import primitive, but it
must still prove interruption recovery. No uncertain import releases the lock
or advances Authority state.

**Implementation prerequisite:** Re-read W71918's accepted implementation,
tests and newest review before production edits. Reuse its final checkpoint,
current-revision, verdict and integration-eligibility identities. Material
changes to checkpoint immutability, path-set binding, verdict operands,
eligibility revocation or correction-line advancement return the affected
W71878 contract for targeted review rather than being adapted silently.

**Proposed patch boundary:** Extend the Job Manager's persisted stage/
integration composition and public documents with the stable target queue,
eligibility snapshot, lease/fence and reconciliation state; extend the trusted
integration/Authority seam only as required to make possession of the live
lease an unavoidable precondition and to record completion after real import.
Reuse the settled `baton.merge` policy rather than duplicating its filesystem
import rules. Exact production and test paths remain contingent on W71918's
accepted interface and must be enumerated in the eventual proposal.

**Open, not blocking this review:** The concrete integration adapter may be a
dedicated host service or another explicitly trusted profile, but an ordinary
Worker Manager runtime with a canonical-checkout mount is not equivalent to
`baton.merge`. Implementation must record which component holds the sole
integration capability and how direct/bypass calls without a live queue lease
are refused.

## Acceptance

- Accepted proposals for the same canonical target enter a durable FIFO or
  otherwise deterministic queue and at most one holds the integration lease.
  Independent targets need not share that lock.
- Eligibility requires a final immutable checkpoint, its exact base/head and
  durable Git objects, a matching independent-review acceptance, and an
  explicit approved path/test-change scope.
- The integrator preflights the whole candidate before any canonical target
  path changes. Missing/mismatched provenance, target movement, overlapping
  divergence, conflict, or out-of-scope paths refuse with a typed result.
- A scheduled existing-test modification inside the bounded Work/plan scope
  imports non-interactively after review. A companion unscheduled or
  out-of-scope test mutation refuses before any canonical target path changes.
- A failed integration leaves the queue and canonical target recoverable and
  does not block unrelated implementation/review capacity.
- Successful import exposes the exact proposal/review identities, imported
  paths, verification evidence, and prepared working-tree diff to Slawomir;
  neither manager nor integrator stages or commits it.
- Restart and two-ready-proposal races prove single-target serialization and
  idempotent recovery without duplicate or partial import.
- Queue-key tests prove one stable target remains serialized across target
  revision changes and across every Authority allowed to address the same
  checkout, while two independent target identities can progress concurrently.
- The Authority integration receipt is written only after the reviewed bytes
  and expected modes are present and bounded integration verification passes;
  no caller can bypass the live target lease to advance Authority state.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` and the bounded integrator-policy test surface needed to
prove this leaf. It explicitly authorizes one planned existing-test behavior
change fixture for the positive integration case and one out-of-scope mutation
fixture for preflight refusal. Any real test deletion or weakening must be
named by path in the proposal and independent review. W71459's owned v11 policy
files remain excluded until its claim and handoff finish.
