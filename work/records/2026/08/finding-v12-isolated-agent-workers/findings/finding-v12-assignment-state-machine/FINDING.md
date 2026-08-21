# Finding: v12 authoritative assignment state machine

Canonical Baton Work: `W151` (`43c55d4b-W151`).

## Status

Design-only decomposition of parent record
`work/records/2026/08/finding-v12-isolated-agent-workers/`. No v11 or v12
application, runtime, schema, dependency, or product-code change is authorized
by this Work.

## Confirmed parent decisions

- The v12 authority owns one monotonically increasing integer assignment
  generation per Work.
- The successful atomic claim increments and returns that generation and
  records it with the live assignment. **Narrowed 2026-08-21 by the
  per-Work contract-progression ruling below:** this applies to claims under
  a v12 assignment contract. A `v11` claim mints no generation, and a Work's
  first positive generation is minted by its first claim after entering the
  v12 contract. The dated supersession lives in the owning parent record
  under "Assignment-generation identity"; the unqualified reading is
  superseded and nothing else in that ruling is.
- The full authoritative assignment identity is `(authority UUID, full Work
  ID, participant, generation)`.
- Clearing the live claim invalidates that assignment without resetting,
  decrementing, or reusing its generation.
- The short-lived pre-claim token is a separate cryptographically random,
  secret, single-use capability to request a claim; it is not assignment
  identity.
- Offer, runtime attempt, assignment, readiness episode, runtime incarnation,
  configuration generation, result, and proposal identities remain distinct.
- Baton Work phase remains the closed scheduler axis
  `queued`/`active`/`block`/`parked`; worker-attempt state must not overload it.

## Design question

Specify the smallest versioned authority and Worker Manager contract that
makes those rulings executable across retries, ambiguous results, manager
restart, cancellation, uncertain quiescence, immediate successor claims, and
late stale publication.

## Acceptance boundary

The design must provide:

1. durable identity shapes and ownership for offers, claims/assignments,
   runtime attempts, results, proposals, and dispositions;
2. a transition table covering offer, accept/decline/expiry, claim,
   activation, cancellation, quiescence, result freeze, proposal publication,
   pass/release/close, plan rejection, and recovery;
3. for every transition, its actor, preconditions, atomic writes, capability
   gained or lost, retry key, settling observation, and failure state;
4. restart and ambiguous-result reconciliation for every manager mutation;
5. invariants proving generation uniqueness/non-reuse, one runtime per live
   assignment, denial of writable/publication capability before claim, stale
   rejection after every claim-releasing transition, and no Work-phase
   overloading; and
6. executable model tests for expired/replayed tokens, competing claims,
   manager restart before and after claim, cancellation races, uncertain
   quiescence, immediate successor claims, and stale publication.

## Exclusions

This Work does not extend the accepted `v12/` proof of concept, alter v11 or
v12 application behavior, freeze the worker-control or manifest schemas, or
choose production runtime, credential, retention, cache, signing, or proposal-
store mechanisms.

## Revalidation result — 2026-08-21

**Confirmed.** V11 has no assignment-generation primitive. The accepted
`v12/` spike's constant generation, local Work selectors, and process-memory
token registry remain valid only inside its explicit `0-spike` boundary.

**Confirmed.** Generation invalidation cannot be patched into `release` alone.
Current Handler-clear paths also include pass, terminal close, explicit
unclaimed phase, blocking request, and dependency-readiness loss. The proposed
authority therefore centralizes assignment end across every Handler-clear
transition.

**Observed.** A current-state check that asks only whether Handler still equals
the participant cannot reconcile an ambiguous claim or mutation. The same
participant may already hold an immediate successor generation. Exact
operation replay/result plus full assignment compare-and-swap are required.

**Observed.** The parent record's statement that current v11 requires a claim
before terminal close is stale at checkpoint `c529b28`: `close_work` is
Route-authorized and has no exact-current-claim check. The v12 recommendation
requires full assignment comparison whenever close ends a live isolated
assignment, while leaving the broader unclaimed-close policy for approval.

**Proposed.** `SPEC.md` defines the authority/control-store/artifact ownership
split, full identities, authority fields, offer and attempt records, complete
transition and restart tables, safety/liveness invariants, and separate
verification/review/approval/integration dispositions.

**Superseded 2026-08-21 by “Cancellation reservation ruling” below.** The
original proposal changed the authority's live assignment from publication
`enabled` to `fenced` under generation compare-and-swap while retaining
Handler and `phase=active` as a recovery reservation. The confirmed ruling
instead ends the assignment and uses a typed scheduler gate.

**Proposed.** The single-use token deadline ends at the durable
`issued -> accepted` compare-and-swap. If that transition commits before
expiry, later retry of its fixed claim operation is reconciliation of already
accepted consent, not revival of the token.

**Superseded 2026-08-21 by “Per-Work contract progression ruling” below.** The
original proposal required a globally drained v12 schema activation and then
incremented the generation counter for every legacy or isolated claim. The
confirmed ruling uses one additive superset schema and explicit per-Work
contract progression instead.

## Open approval decisions

1. **Resolved below:** reject the publication-fenced/Handler-retained
   cancellation cross-product and use an authority-native typed gate.
2. **Resolved below:** accepted-before-expiry is the token deadline boundary
   for later exact claim reconciliation.
3. **Resolved below:** reject a global drained activation in favor of
   authoritative per-Work contract progression.
4. **Resolved below:** preserve unclaimed authorized closure while requiring
   exact assignment comparison for a close that ends a live assignment.

## Cancellation reservation ruling — confirmed 2026-08-21

The publication-fenced/Handler-retained cross-product is rejected. Once an
isolated assignment must stop, the authority first fences its exact generation
and then ends the live assignment, clears Handler, and places the Work behind
a typed `runtime-quiescence` scheduler gate. The Work is `block`, never
`active`, while no participant is authorized to execute it. This preserves the
meaning of Handler and frees the participant's one global claim slot for
unrelated Work.

The Worker Manager continues to own and observe the old runtime attempt after
the Baton assignment ends. It may force-stop and destroy that assignment's
isolated container. Positive proof that the exact runtime is absent satisfies
the gate. If positive quiescence remains unavailable, a pinned certified-
isolation policy may satisfy it only when the old generation cannot publish,
has no shared writable state or reusable credentials, and cannot affect the
canonical checkout or accepted artifacts. The policy decision and evidence
are journalled before a successor receives a fresh generation.

Discarding an abandoned worker's private checkout or unaccepted output is
safe: no worker output becomes canonical merely because it was produced. A
late runtime using the ended generation is refused, including after a
successor claims. Offer issue and claim must also check the participant's
one-live-claim capacity so a token is not knowingly consumed for an
unavailable slot.

### Output-retention clarification — confirmed 2026-08-21

The preceding statement that discard is safe describes an available terminal
disposition, not an automatic consequence of fencing, cancellation, or forced
stop. It is narrowed accordingly. Recoverable declared output and draft
findings are sealed or quarantined with their source Work, assignment
generation, cancellation reason, and policy provenance. Trusted intake may
judge that material good enough to preserve, revise, or submit through the
normal proposal path; inspecting or retaining it does not accept it or make it
canonical.

The pinned route/runtime policy controls retention and may explicitly permit
discard for disposable attempts. Without such a policy or a deliberate intake
decision, cancellation does not silently delete recoverable work. Cleanup of
the private checkout occurs only after the configured collection, quarantine,
and disposition boundary is satisfied. Output retention is independent of
clearing Handler: the participant slot can be freed and the Work can remain
blocked on runtime quiescence while trusted intake evaluates already-stashed
material.

## Token-offer expiry ruling — confirmed 2026-08-21

Token expiry is the deadline for the worker to accept the offer. A durable
`issued -> accepted` compare-and-swap before that deadline consumes the token,
fixes one exact claim operation identity, and ends the bearer-token timing
question. The Worker Manager may submit or reconcile that same claim operation
after wall-clock expiry; doing so is not a late token use or a new acceptance.

Timely acceptance does not reserve the Work or guarantee a successful claim.
The eventual authority transaction still rechecks the current Route,
participant capacity, gates, Work state, and every other claim precondition.
If any has changed, the fixed claim refuses normally. A separate visible
claim-settlement timeout or recovery policy may govern an accepted offer that
does not settle, but it must not reinterpret or revive the consumed token.

## Per-Work contract progression ruling — confirmed 2026-08-21

One additive authority schema supports multiple explicit assignment-contract
versions. Each Work has an authoritative typed contract selector such as
`v11` or `v12-assignment-1`; it is not an informational free-form tag and is
not the assignment generation. Existing Work initially retains `v11`. A Work
keeps its identity, dossier, history, containment, and relationships as its
contract advances during its lifetime.

The current Handler may advance the Work contract only through an atomic
compare-and-swap against its exact live assignment and the expected current
contract. That transaction records the new contract and rationale, ends the
old assignment, and derives the unclaimed scheduler state. It never changes
constraints underneath a running worker. Prior assignments and artifacts keep
the contract version under which they were produced; the next claim inherits
the new contract and, on first entry into the v12 assignment contract, mints
the Work's first positive assignment generation.

The target contract establishes requirements for every future Handler until a
later explicit contract transition. Claim, runtime-profile eligibility,
capabilities, input/output validation, fencing, and publication all derive
from it. Contract transitions follow a configured, audited transition policy;
an arbitrary tag edit or silent downgrade has no authority.

If no certified runtime profile can execute the target contract, the same
transition installs a typed `contract-runtime` gate and leaves the Work in
`phase=block` with no Handler. Deploying and certifying a matching environment
satisfies that gate and makes the Work claimable under the already-selected
contract. Thus a Work may intentionally advance to v12 before the v12 runtime
is deployed: it remains the same Work and is visibly held for that environment
rather than being recreated, misclaimed under v11, or manually parked.

## Terminal-close ruling — confirmed 2026-08-21

Authorized unclaimed closure remains possible. An approver or other actor
holding the configured close capability may reject, cancel, or otherwise close
unclaimed Work without manufacturing a pointless execution claim merely to
reach a terminal state.

A close that ends a live v12 assignment must supply and compare-and-swap its
full exact assignment identity. Omitting the identity, naming only the
participant, or supplying a stale generation refuses. The exact close commits
the terminal Work outcome and centralized assignment end atomically, including
publication invalidation and an event naming the ended assignment. An operator
may instead use the explicit fencing/recovery path first and then close the
resulting unclaimed Work.

This ruling does not retroactively claim that v11 already enforces the rule.
The parent statement saying v11 requires a claim before terminal close is
stale and must be corrected. Executable evidence must cover an unclaimed
authorized close, refusal without identity while an assignment is live,
refusal of a stale generation, and successful close with the exact current
assignment before this contract is accepted for implementation.

## Contract-revision ownership — confirmed 2026-08-21

The bounded post-ruling revision is assigned to `baton.impl`. The four rulings
are already authoritative, so this round is implementation of the design
record and executable model rather than new product discretion. Claude updates
`SPEC.md`, the evidence model/tests, and her existing `PROGRESS.md`; she does
not change v11/v12 runtime or application code.

`baton.codex` performs the independent focused review after its current W99
review. This keeps the pipeline moving without making the reviser certify her
own corrections. W151 closes only after that review confirms the ruled
contract, evidence defects, and supersessions are complete.

## Post-ruling contract revision — 2026-08-21 (`baton.claude`)

`SPEC.md` is now version `1-ruled`. The four rulings above are folded into the
contract, and the two `0-design` proposals they rejected — the
publication-`fenced`/Handler-retained cancellation cross-product and the
globally drained v12 activation that minted a generation for every claim — are
explicitly marked superseded in `SPEC.md` §1 rather than deleted.

Two consequences of the rulings are worth pinning here because they change
what earlier text meant:

- **Generation minting is now contract-conditional.** A claim mints a
  generation only under a v12 assignment contract; a `v11` claim mints none.
  This follows from ruling 3 and replaces the `0-design` statement that every
  claim, legacy included, mints one. Recorded as an explicit dated scoped
  supersession in the parent record and in "Confirmed parent decisions" above
  after the focused review of 2026-08-21T21:06:44Z asked for it: the earlier
  unqualified text was still live beside the narrowed one, and two live rules
  that disagree are worse than either alone.
- **Review finding P2a is dissolved, not accepted.** It warned that
  `fenced` + `phase=active` would narrow the pinned `docs/EFFECTIVE-BATON.md`
  guarantee that there is no window where the board shows work in progress
  that nobody is doing. Ruling 1 ends the assignment instead, so no Work is
  ever `active` without an executor and that guarantee stands unnarrowed. No
  supersession of `docs/EFFECTIVE-BATON.md` is required or made.

Review findings P1a (one-live-claim capacity as an explicit offer and claim
precondition), P1b (immutable, replay-only workflow receipts), P2b (executable
close scenarios) and P3 (per-Work offer uniqueness over a shared control
store) are corrected in `SPEC.md` and the evidence.

**Residual, non-blocking.** Ruling 3 gives contract advancement to the current
Handler, so unclaimed Work advances by being claimed under its current
contract first. That is ordinary for `queued` Work and unavailable for Work
already gated or parked. This contract deliberately proposes no unclaimed
contract-transition path; if one is wanted it is a separate ruling.

The stale parent close statement is corrected in place at
`work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md` under
"V11 enforcement boundary", as a dated partial supersession that leaves the
original claim-before-`pass` statement standing.

## Verification

`evidence/test_assignment_state_model.py` passes 54 scenarios under Python's
standard `unittest` runner, covering all four rulings, the corrected evidence
defects, and the effectively-once, settlement and restart boundaries the four
focused reviews of 2026-08-21 opened; the superseded `0-design` package ran
13. The model imports
no Baton implementation and changes no application or runtime behavior. The
focused independent review by `baton.codex` signed off the design contract in
`review-2026-08-21T21-52-09Z.md`. Implementation remains separate Work.
