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

## Targeted provider revalidation review — 2026-09-05

**Observed:** W71918's accepted `integration_checkpoint` is one CUSTODY
eligibility surface. It returns the exact accepted checkpoint/verdict and
checkpoint-evidence digest after re-proving the current line, frozen checkpoint,
accepted verdict, completed review result and live review fence. It deliberately
does not read an Authority proposal or its verification, technical-review and
approval receipts. Authority remains the separate POLICY eligibility surface.

**Confirmed clarification — cross-bind corresponding operands, not unrelated
aggregate digests:** An entry may enqueue only after both surfaces succeed in
one closed validation account. It binds the Authority proposal identity and
receipt identities/digests beside W71918's line, checkpoint, verdict and
checkpoint digest, then re-resolves both sources. Every shared semantic operand
must agree: Authority/Work/assignment provenance, proposal source base and head,
expected target revision, retained proposal object transport, and the reviewed
path set/scope all name the same candidate.

W71918's `checkpoint_digest` is `digest(checkpoint_evidence)`, whose evidence
contains profile, base, head, tree, paths, path-set digest and retained reference.
Authority's current `candidate_digest`, and the worker-control contract's
`proposal_manifest_digest`, are different aggregates with different meanings.
The queue must retain and verify each digest under its own schema; it MUST NOT
require them to be equal merely to manufacture a cross-binding. A future
interface may add one explicit digest over the joined account, but it cannot
silently reinterpret either existing digest.

**Observed correction — accepted custody eligibility is not revocable by line
advancement:** W71918 permits a writer only from `idle` or `correction-ready`.
Only `changes-requested` reaches `correction-ready`, and that verdict creates no
integration-eligibility row. An `accepted` verdict ends the sole review
attachment, moves the line to terminal `accepted`, and no public transition can
record a second verdict or freeze a later checkpoint on that line. Therefore a
previously accepted checkpoint cannot ordinarily become ineligible through a
later changes-requested verdict or freeze. `integration_checkpoint`'s current-
checkpoint checks are integrity revalidation, not an advertised revocation
transition.

**Confirmed queue disposition:** The queue still revalidates both eligibility
surfaces before selection and again under its lease. An ordinary current-policy,
scope or target failure before mutation records one typed terminal refusal for
that immutable entry; an integrity, digest or ambiguous custody failure blocks
the target and retains the fenced account for explicit repair. Neither case is
called checkpoint `revocation` or `supersession` unless a separately reviewed
provider transition later introduces that state. No special revoked-entry state
is required for the accepted W71918 interface.

**Confirmed clarification — line identity is never the queue key:** W71918's
line identity is scoped to `(authority_uuid, work_id)`. The integration lease is
scoped to the stable deployment/profile `canonical_target_id`. The target key
is supplied by trusted target configuration and is never derived from line,
Authority, Work, proposal, checkpoint or mutable target-revision identity.
Distinct Authorities that can reach one checkout therefore contend on one
target lock, while their custody lines and immutable entries remain distinct.

**Disposition:** These corrections complete the W71918 provider revalidation
without changing the previously signed-off ownership, rank, fencing, import,
crash or test-authority boundaries. No owner-level choice remains: implementation
may proceed under the corrected plan. This review approves no candidate bytes.

## The integration capability's seam — DECIDED — 2026-09-05

Pinned before implementation because this record left it open and named it as
something implementation must record: "which component holds the sole
integration capability and how direct/bypass calls without a live queue lease
are refused."

**Observed, from the accepted tree rather than from prose.** The Authority
`Session` contract exposes `proposal`, `receipt`, `receipts`,
`canonical_target` and `integration_attempts` among `SESSION_READS`, and
`integrate` among `SESSION_TRANSITIONS`. The Worker Manager's
`AuthorityPort` — the participant-bound face the Job Manager composes today —
exposes none of them: its surface is `project_work`, `assignment_of`, `cancel`,
`slot_holder`, `claim`, `publish_answer`, `settle_operation` and
`claim_signature`.

So the policy eligibility surface this Work must read, and the integration
receipt it must write after a real import, are **not reachable through the
seam the generic manager already holds**. That is the correct shape and not a
gap to close: W71877's item 2e already refused to widen `AuthorityPort` for a
read it wanted, on the ground that the participant-bound session boundary is
not a convenience surface.

**Decided: the integration capability is a separately injected trusted
profile, on the pattern W71918 established for checkpoints.** The deployment
supplies one object; the Job Manager holds no canonical checkout, runs no Git,
and reaches no Authority transition the generic manager does not already own.
The profile carries, in one place:

- the Git-aware whole-path preflight and import — the settled `baton.merge`
  policy, composed rather than reimplemented;
- the Authority POLICY reads this Work cross-binds against — `proposal`,
  `receipt` for verification, review and approval, and `canonical_target`;
- and the `integrate` transition that records completion after real import.

**Why one object rather than three — and what that does NOT buy.** Splitting
the reads from the import would let a deployment supply a real Authority face
with no importer, or an importer with a stub Authority, and the whole point of
this Work is that the receipt follows the bytes. One capability is therefore
one WIRING unit: it removes a class of misconfiguration.

**Superseded in the same breath it was written:** the first draft of this
section said one capability makes "read the policy, import, then record"
INDIVISIBLE. That is false and the targeted seam review is right to reject it.
Colocation on one object creates no atomicity across three durability domains —
the scheduler's SQLite, the target filesystem, and the Authority's SQLite — and
a reader who took the sentence at face value would build without the
reconciliation those three boundaries actually require. The explicit durable
cutpoints between preflight, import, verification and receipt completion, and
the restart reconciliation over them, are unchanged obligations of this record;
the profile's shape does not discharge any of them.

**How a bypass is refused — a LIVE grant, not a replayable value.** The first
draft said possession of a live lease is an operand of every profile call. An
operand is a value, and a value can be replayed; that is the same mistake
W71918 corrected for its writer grant, which is why its previously minted
boundaries recheck the LIVE grant at adoption and again at mount composition.

So the rule here is the same one: before any canonical mutation and again
before Authority completion, the owner of the target store re-evaluates the
live grant against the exact target, entry, lease and fence, and refuses if it
is not still held. Uncertain work prevents lease release rather than ending it.
A deployment that supplies no such profile refuses the workflow rather than
falling back to an ordinary worker with a canonical-checkout mount, which this
record already rules is not equivalent.

**The integration Session is separate and narrow.** The Worker Manager's
`AuthorityPort` stays exactly as it is. The profile holds its own fixed
participant-bound Authority session for the policy reads and the `integrate`
transition, and validates every proposal and receipt document it returns rather
than trusting the shape.

**What stays outside it.** Slawomir's Git index and history ownership is
untouched: the profile prepares a working-tree diff and records the Authority
receipt, and stages nothing. The generic Worker Manager receives no canonical
checkout and gains no new capability.

## The lock domain — OWNER RULING REQUIRED — 2026-09-05

The seam review found a [P0] that the design above cannot decide for itself,
and it is a genuine contradiction between two accepted rulings rather than an
implementation choice.

**Observed.** W83781 binds each `JobStore` immutably to one Authority UUID and
refuses an open under another. The integration relations were going to live
there. A live-target unique index in that database is therefore unique only
WITHIN one Authority — so two Authorities configured for the same canonical
checkout each hold their own store, each grant their own lease, and both import
into one working tree.

**What that contradicts.** This record's own identity model says every producer
that can reach the same canonical checkout maps to the same queue identity,
"including distinct Authorities if the deployment permits them to share that
checkout", and its acceptance clause requires a queue-key test proving exactly
that. An Authority-bound store cannot satisfy it. The two rulings are both
live and they disagree.

**A — one target-global coordinator, independent of any Authority-bound
store.** The lock, the queue and the lease live in a store keyed by the
configured `canonical_target_id` alone, which every Authority permitted to
reach that checkout opens. It satisfies the cross-Authority acceptance clause
as written. It costs a new durability domain with its own schema, migration,
open/adopt rules and restart reconciliation, and it adds a THIRD SQLite store
to a sequence that already spans two plus a filesystem — so the cutpoints the
[P1] above insists on get harder, not easier, and every one of them must be
proved rather than assumed.

**B — one Authority per canonical target, mechanically enforced.** The
relations stay in the Job store and the deployment is narrowed: a target is
addressable by exactly one Authority, proved at configuration time and refused
otherwise. It costs nothing new structurally and it SUPERSEDES this record's
cross-Authority sentence and its queue-key acceptance clause, which must then
say plainly that two Authorities sharing a checkout is a configuration this
build refuses rather than serializes.

**What must not happen is the third option**, which is to build A's contract
against B's mechanism: leaving the cross-Authority sentence standing while the
lock lives in an Authority-bound store. That is the state the review found, and
it is the one thing neither ruling permits — the acceptance test would be
unimplementable and a deployment reading the contract would believe it was
protected.

**No recommendation is recorded here beyond the review's own.** The reviewer
recommends A. I have no independent evidence to add: the choice is between
accepting a new coordination domain and narrowing the deployment model, and
both of those are decisions about what the product is rather than about how to
write it. Nothing in the code depends on the answer yet, so whichever is ruled
starts from the same place.

## Independent integration-seam review — changes requested — 2026-09-05

The implementer-pinned seam above is NOT accepted as a confirmed decision.
Its direction—do not widen the generic Worker Manager's `AuthorityPort`, and
use a separately wired trusted integration boundary—is sound. The proposed
persistence location and two claimed enforcement properties contradict the
accepted baseline and must be resolved before production code.

**Observed blocking contradiction — an Authority-bound Job store cannot own a
cross-Authority target lock.** W83781 made `JobStore` belong to exactly one
Authority UUID for its whole life. `JobStore.open` refuses another Authority,
and the store's episode identities deliberately use that namespace. Adding
`integration_targets`, entries and a unique live-target lease in this store
therefore makes the uniqueness constraint local to ONE Authority database.
Two permitted Authorities addressing the same canonical checkout could each
hold their own locally unique lease at once.

That violates this record's required identity model and acceptance test, both
of which require every Authority permitted to address one checkout to contend
on the same `canonical_target_id`. Merely storing an `authority_uuid` column on
an entry does not join two SQLite transaction domains, and trusted configuration
cannot claim the race is serialized when no shared atomic decision exists.

**Observed seam overclaim — one injected object is not transaction atomicity.**
Putting policy reads, filesystem import and `Authority.integrate` methods on one
Python object can make deployment wiring cohesive, but it does not make the
sequence indivisible. Filesystem mutation, scheduler state and Authority state
remain separate durability domains; the record's crash cutpoints and
reconciliation are still required between every one of them. The earlier
"indivisible" rationale is superseded by this narrower wiring claim.

**Observed fence gap — a fence value is evidence, not possession of a live
capability.** A caller can repeat a persisted lease id/generation. Passing those
values to a profile does not prove the lease is still live. The scheduler-owned
target store must mint or supply the live-check boundary, and the integration
path must re-read the exact target/entry/lease/fence under that owner before
each canonical mutation boundary and before Authority completion. Uncertain
execution prevents revocation/release; a stale serialized fence alone cannot
authorize or deny an external effect.

**Required owner ruling:** Choose one architecture and explicitly supersede the
other:

1. **Recommended:** add a target-global integration coordinator/store, with a
   store kind and transaction domain independent of any one Authority-bound Job
   store. It owns `canonical_target_id`, global enqueue rank/selection and the
   unique live target lease; entries remain Authority-namespaced and point back
   to their owning Job/Authority evidence. Each Authority-specific Job Manager
   submits/adopts receipts from that shared coordinator rather than owning the
   target lock.
2. Narrow the deployment contract so a canonical target can be addressed by
   exactly one Authority, reject any duplicate target configuration before work
   is admitted, and explicitly supersede every cross-Authority serialization
   requirement and acceptance case in this record. A convention that two
   Authority-local stores happen not to race is not sufficient.

**Required boundary after that ruling:** Keep the existing Worker Manager
`AuthorityPort` unchanged. Define the integration boundary as its own closed,
typed surface whose Authority side is a participant-bound integration Session,
not the bootstrap/Core configuration face. Bind the fixed integrator actor,
Authority UUID and canonical target; own and validate every returned proposal,
receipt, target and integration document at the crossing. If one composite
profile is retained, describe it as one deployment wiring unit, not one atomic
transaction, and specify the durable preflight/import/verification/Authority-
completion cutpoints and live-lease checks it must reconcile.

**Disposition:** No implementation bytes exist, so no byte verdict is due.
Implementation remains blocked on the owner ruling and the corrected seam
contract. The previously approved queue ordering, refusal, import and crash
requirements remain in force.

## Acceptance

- Accepted proposals for the same canonical target enter a durable FIFO or
  otherwise deterministic queue and at most one holds the integration lease.
  Independent targets need not share that lock.
- Eligibility requires a final immutable checkpoint, its exact base/head and
  durable Git objects, a matching independent-review acceptance, and an
  explicit approved path/test-change scope.
- Queue admission re-resolves both Authority policy receipts and W71918 custody
  eligibility, binds both exact digest families without conflating them, and
  proves their corresponding proposal/checkpoint operands describe one candidate.
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
- Eligibility-transition tests prove a non-accepted correction checkpoint never
  enters the queue, an accepted W71918 line cannot advance through public
  transitions, ordinary pre-mutation revalidation failure terminally refuses
  only that entry, and integrity/ambiguity retains the target fence for repair.
- The Authority integration receipt is written only after the reviewed bytes
  and expected modes are present and bounded integration verification passes;
  no caller can bypass the live target lease to advance Authority state.

## 2026-09-05 — owner ruling: target-global integration coordinator

The `OWNER RULING REQUIRED` state above is resolved. **Option A is accepted:**
integration ordering and exclusion belong to a target-global coordinator/store
whose transaction domain is independent of every Authority-bound `JobStore`.
Option B, mechanically limiting a canonical target to one Authority, is
rejected and superseded as the answer for this Work.

The coordinator owns each configured `canonical_target_id`, its global enqueue
order and selection, and its unique live target lease. Immutable entries remain
Authority-namespaced and retain the exact Job, proposal, receipt, checkpoint
and path-scope evidence from their owning Authority. Every Authority-specific
Job Manager permitted to address the same canonical target submits to and
adopts results from this one coordinator; it does not create an
Authority-local target lock.

The Worker Manager's generic `AuthorityPort` remains unchanged. Integration
uses a separate, narrow participant-bound integration surface. A composite
integration profile is one deployment wiring unit only; it creates no
atomicity across the coordinator store, target filesystem and Authority store.
Preflight, import, verification and Authority completion remain explicit
durable cutpoints with restart reconciliation.

Before canonical mutation and again before Authority completion, the
coordinator owner revalidates the exact live grant against target, entry,
lease and monotonic fence. A serialized lease or fence value is evidence, not
possession of a live capability. Uncertain execution retains the lease and
blocks the target rather than releasing it.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` and the bounded integrator-policy test surface needed to
prove this leaf. It explicitly authorizes one planned existing-test behavior
change fixture for the positive integration case and one out-of-scope mutation
fixture for preflight refusal. Any real test deletion or weakening must be
named by path in the proposal and independent review. W71459's owned v11 policy
files remain excluded until its claim and handoff finish.

## 2026-09-06 — item 3 coordinator review: changes requested

Independent review of the bounded working-tree coordinator slice found two
serialization-breaking transitions. First, a caller can release a live lease
while its entry remains unresolved and then grant the next entry. Second, a
caller can block one entry while another entry owns the live lease, then
abandon that lease and strand its real entry as `leased` beside the unrelated
`held` entry. Normal release must be coupled to exact terminal/reconciled entry
state; target blocking and abandonment must share one durable account bound to
the exact target, entry, lease, fence, and holder/recovery identity.

The receiving store also accepts split redundant eligibility evidence,
malformed Authority namespace identity, and an adopted schema missing the
partial unique index claimed as a safety invariant. Every persisted read must
validate complete owned document shape and redundant row/document/relationship
bindings; adoption must validate the complete owned schema; Authority UUIDs
must use the repository identity predicate without treating syntax as
capability.

The exact evidence, reproductions, correction boundaries, and verification
are recorded in `review-2026-09-06T02-15-48Z.md`. That review is not an
immutable proposal approval: no proposal manifest or digest was supplied.

## 2026-09-06 — item 3 correction re-review: changes requested

The original two P0 serialization defects are corrected. Ordinary release can
no longer end an unresolved lease and advance the queue; block and abandonment
now share one exact grant account. The explicit recovery exception is accepted:
an accounted abandonment may end the live lease over a held entry only after
the target is durably blocked and remains unavailable.

The persisted-read correction is incomplete. A blocked target still returns a
block account whose reason, entry, lease, fence, integrator or attempt can
contradict the target, held entry and lease rows. Entry settlements and lease
endings are key-shaped but not state-semantically owned, including an abandoned
lease carrying an `integrated` ending. In addition, `settle_integrated` and
`refuse_entry` discard the fresh document returned by the ownership boundary,
so an injected callback can mutate the caller's original after validation and
make the operation journal sign one account while persisting and replaying
another.

The exact evidence and correction boundaries are recorded in
`review-2026-09-06T02-39-45Z.md`. Item 3 remains changes-requested and this
working-tree re-review approves no immutable proposal bytes.

## 2026-09-06 — third item 3 review: changes requested

The second correction closes the reported present-block relationships,
state-specific variants, and owned-snapshot defect. The state graph still
fails open when the block is absent: after a proper block and abandonment,
changing only the target row to its schema-valid open shape leaves the earlier
entry `held` and lease `abandoned`, yet `target_of` and `lease_of` accept the
contradiction and `grant_lease` leases the next entry.

The target/entry/lease relationship must be adopted from every public read and
before selection, not only when `blocked_account` is present. An open target
cannot coexist with held work in the item-3 model, and an abandoned lease must
cross-check the still-blocked target and exact recovery account. A future
repair transition may reopen only after it durably reconciles those operands.

The exact reproduction and correction boundary are recorded in
`review-2026-09-06T02-53-42Z.md`. Item 3 remains changes-requested and no
immutable proposal bytes are approved.

## 2026-09-06 — fourth item 3 review: changes requested

The erased-block correction works from every named read and selection door.
The new whole-graph pass is still incomplete for ordinary terminal history:
after normal integration and release, changing only the entry back to its
schema-valid queued shape leaves a released `integrated` lease that every
public read accepts, and selection leases the same candidate again.

The state graph must bind every entry state to its complete lease history and
ending, not only live, held, and abandoned subsets. Queued entries have no
lease; each selected entry has exactly one lease in the state/ending allowed by
its entry state; the target fence equals its granted lease history. No item-3
entry returns to queued or receives a second lease. The exact lifecycle matrix,
reproduction, and regressions are recorded in
`review-2026-09-06T03-06-14Z.md`.

Item 3 remains changes-requested and no immutable proposal bytes are approved.

## 2026-09-06 — fifth item 3 review: changes requested

The fourth correction closes the named state/lease lifecycle matrix, but its
journal check starts only from rows that still exist and does not adopt the
originating enqueue or grant. A schema-valid rewrite of a queued entry's
checkpoint and candidate digest is accepted and leased; the original
checkpoint can then enqueue again under another entry id. Deleting an
integrated entry and released lease, resetting the fence, and retaining their
committed journal history is likewise accepted and permits the same checkpoint
to receive a new entry and fence.

Committed activation, enqueue and grant history must cross-bind every
materialized target, immutable entry account, lease, rank and fence in both
directions. Missing materialized rows and rewritten account members are
contradictions when their committed acts remain, not an accepted blind spot.
The exact evidence and correction boundary are recorded in
`review-2026-09-06T03-22-15Z.md`.

Item 3 remains changes-requested and no immutable proposal bytes are approved.

## 2026-09-06 — sixth item 3 review: changes requested

The fifth correction finds missing rows and one-surface rewrites, but does not
bind a journal result to its signed request. Rewriting both a queued entry row
and its enqueue result while retaining the original signed eligibility is
accepted and leased; the original checkpoint then enters again under a second
entry id. Journal operand documents are closed only by member name rather than
typed or cross-bound, terminal acts are recognized by operation identity alone,
and a schema-valid committed SQL-NULL result escapes as a raw `TypeError`.

Every committed operation must be adopted as one exact relationship among its
canonical identity, typed signed operands, typed result, and materialized
effect. Generated rank/fence/instants belong to the result, but the result must
first be proved to answer that exact request. The exact reproduction and
correction boundary are recorded in `review-2026-09-06T03-39-13Z.md`.

Item 3 remains changes-requested and no immutable proposal bytes are approved.

## 2026-09-06 — seventh item 3 review: changes requested

The sixth correction closes the prior signed-request/result and typed-journal
cases in the ordinary history projection, but two P0 boundaries remain.

First, every exact retry bypasses that projection. `IntegrationStore.replay`
checks only raw signature/kind equality and returns the decoded stored result;
both `transact` and the fenced verbs reach it before semantic operation and
materialized-state adoption. A corrupted enqueue result therefore replays a
candidate digest that contradicts its row, and a fabricated committed
`entry.integrated` operation makes `settle_integrated` report success while
the entry remains leased. Replay must preserve its required ordering ahead of
ended-grant checks while adopting and cross-binding the complete operation and
its materialized effect before returning anything.

Second, generated queue decisions have no independent durable witness. A
coordinated rewrite of an enqueue result and its entry row from rank 1 to rank
3 is accepted, reverses the returned FIFO order, and causes selection to grant
the originally second entry. Type-valid generated rank/fence/instant fields
and row/result equality do not prove the allocation or selection produced by
the signed act. Durable ordering evidence must anchor rank and grant selection
against coordinated result/materialized rewrites.

The exact reproductions and correction boundary are recorded in
`review-2026-09-06T11-10-42Z.md`. Item 3 remains changes-requested and no
immutable proposal bytes are approved.

## 2026-09-06 — owner clarification: integration core remains VCS-neutral

The phrase “Git-aware preflight and candidate import” names the configured
integration PROFILE used for Baton's repository; it does not grant Git
vocabulary or behavior to the integration coordinator, Job Manager, Worker
Manager, or protocol. The generic path is: retain an approved result artifact,
serialize it against a stable target, grant one fenced integration attempt,
invoke the target's configured integration profile, and persist that profile's
generic success or refusal account.

For a Git target, the profile alone resolves commits, refs or bundles; checks
base, head, object availability, changed paths, target drift and repository
policy; imports the reviewed bytes into the working tree; and verifies the
result. It does not stage or commit. A non-Git profile may instead integrate a
file transformation or another declared artifact without changing the core
queue, lease, fencing or settlement model.

The current item-3 implementation contradicts this boundary by placing
`base_object`, `head_object`, `tree_object` and `transport_ref` in the core
eligibility schema and `checkout` in the core target document. Those are
profile-shaped operands, not coordinator vocabulary. Before item 3 can be
accepted, replace them with a VCS-neutral, versioned integration-profile
boundary: the coordinator may bind a candidate/artifact identity and digest,
generic target revision and scope evidence, plus a closed profile kind/version
and profile-validated account or digest, but it neither names nor interprets
Git concepts. The selected profile owns validation and interpretation of its
typed account. An opaque, unvalidated document is not an acceptable escape
hatch.

## 2026-09-06 — owner clarification: no required VCS-aware adapter

The preceding wording that the selected profile “owns” Git interpretation is
too strong and is superseded here. V12 does not require Baton to provide a
VCS-aware adapter. An integration profile is generic runtime wiring: it selects
the agent/image, mounts, capabilities, instructions, target access and generic
result contract. When a Work uses Git, the model reads the Work's Git-specific
instructions and uses the ordinary Git tools available inside that runtime.
For non-Git Work, a model follows the corresponding non-Git instructions under
the same runtime and coordination contract.

Baton mechanically owns only the format-neutral safety boundary: serialized
target admission, the live fenced grant, exclusive target write access,
quiescence, and durable success or refusal. It does not parse or validate
commits, refs, branches, trees, ancestry or merge semantics. Git-specific
evidence may be retained in the Work's generic inputs, outputs and logs for
agent review without becoming coordinator schema. A deterministic VCS adapter
may be supplied later as an optional deployment component, but it is neither a
v12 requirement nor core protocol vocabulary.

## 2026-09-06 — item 3 seventh correction: decisions taken

Implementing the seventh review and the two owner clarifications above required
three rulings that outlive this round, so they are recorded here rather than
only in the implementer's progress.

**The durable ORDER of the journal is coordinator evidence.** `operations`
gains `seq`, allocated as `MAX(seq) + 1` inside the act's own transaction and
proved dense from one at every read. A generated decision has no request-side
witness — `enqueue` cannot sign the rank it is about to allocate and
`grant_lease` cannot sign the fence it is about to burn — so rank, fence and
grant selection are now DERIVED from that order and compared to the recorded
result and the materialized row, rather than being believed because those two
agree. The Nth enqueue of a target allocated rank N; its Nth grant that took a
lease burned fence N; and replaying the enqueues and settlements before a grant
says which entry that grant could have selected.

The claim is bounded deliberately. There is no durable secret in this
deployment, so a writer who also rewrites `seq` presents a self-consistent
alternative history that this seam cannot distinguish from the real one. What
is closed is the two-surface rewrite the review demonstrated: it now
contradicts a third surface neither of those surfaces touches, and a deleted
act leaves a hole in a dense sequence.

**A replay is a read, and is proved like one.** `IntegrationStore.replay` takes
a required `witness` and has no default. The store owns the transaction, the
operation identity, the durable order and the adoption of an operation row; it
owns no queue semantics and is no longer permitted to guess them. Every public
mutator, including the preflight retry the fenced verbs use, reaches the one
semantic owner, which adopts the act's operands through their admission owners,
re-derives its identity, adopts its result as that kind's variant, binds the
result to the signed request, and then proves the whole materialized
relationship the act belongs to. The ordering requirement from the earlier
correction is unchanged: the journal is still asked BEFORE a now-ended live
grant is checked. Asked first is not trusted first.

**The profile boundary that replaces the version-control operands.** Under the
owner clarifications, `base_object`, `head_object`, `tree_object` and
`transport_ref` leave the eligibility account and `checkout` leaves the target
document. They are replaced by a closed, versioned binding carried on the
entry: `profile_kind` (text), `profile_version` (counting from one) and
`profile_account_digest` (text). The coordinator retains the DIGEST of the
profile-shaped account and never the account, so it can refuse a changed
profile account without knowing what one is; the operands themselves travel in
the Work's generic inputs, outputs and logs. An opaque unvalidated document was
refused by name as an escape hatch, and a digest is not one.

The target document is now `schema`, `canonical_target_id` and `description`:
the coordinator locks a NAME, and where the named thing lives is the profile's.
`TARGET_SCHEMA` moves to `baton.v12.integration-target/2` and the store's
`SCHEMA_VERSION` to 2, because a document or a store whose members changed is
not the same one. There is no migration and none is invented; version 1 is a
shape this unaccepted candidate carried and nothing else ever held.

Not decided here, and left to the records that own it: which profile kinds a
deployment offers, what a profile account contains, and how a profile is
selected. The coordinator neither names nor interprets any of it.

## 2026-09-06 — owner ruling: interrupted integration recovers manually

Automatic integration recovery is outside the first usable v12 path. The
ordinary uninterrupted path still records verification, the Authority receipt,
terminal entry state and lease release. If the manager or integration runtime
stops between those operations, or any observed target/account state is
missing, mixed, divergent or otherwise inconsistent, the coordinator preserves
the evidence, keeps the target unavailable and reports one typed operator-held
condition.

Restart may observe and classify that state, but it does not automatically
retry an import, accept retained output, finish an Authority receipt, release a
lease, clean a workspace, discard output or reassign the Work. An operator must
inspect the target, logs, output and durable accounts and then explicitly choose
the permitted recovery action. Before another writer receives the target, the
operator path must establish that the prior runtime can no longer mutate it.

This supersedes the earlier requirement that the first implementation
automatically recognize all-base or all-candidate bytes and retry or resume the
cross-domain sequence. Idempotent automated recovery may be designed later if
operational experience proves it valuable; it is not on W71878's critical
path.

## 2026-09-06 — owner disposition: finish item 3, then decompose

The eighth item-3 review leaves two related P1 corrections in one replay and
transaction boundary: prove semantic replay from one coherent SQLite snapshot,
and adopt refused journal rows through the same typed operation and dense-order
witness as committed rows. W71878 returns for one implementation round limited
to those findings and their focused regressions, followed by one independent
review that returns to operations rather than continuing implementation.

Items 3b and 4 through 9 do not continue as another W71878 implementation
episode. After item 3 is accepted, W71878 remains the integration umbrella and
the remaining runtime boundary, candidate admission, fenced model-driven
integration, manual recovery settlement, and end-to-end verification become
bounded child Work with explicit dependencies. This is the stopping point for
the growing single-thread correction loop.

## 2026-09-06 — owner ruling: K owns shared integration boundaries

Parallel decomposition does not create multiple owners for a shared contract.
`baton.claude` (K) owns every shared integration boundary: public interfaces,
cross-component documents and schemas, common exports and registries, and the
final assembly between coordinator, runtime, admission and settlement.

`baton.tuner` may implement a bounded leaf behind an already recorded boundary
with an explicitly disjoint path set. It does not independently change or
reinterpret that boundary. If its leaf demonstrates that the boundary is
insufficient, it returns the finding to K for the boundary change before
continuing. This preserves parallel capacity without allowing two agents to
evolve the seam from opposite sides or collide in the shared working tree.

## 2026-09-06 — eighth item 3 review: changes requested

The seventh correction fixes both preceding P0s and carries the VCS-neutral
owner rulings correctly, but two P1 receiving/transaction boundaries remain.

First, the semantic replay witness runs before `BEGIN IMMEDIATE` and reads the
target, entries, leases and journal through separate autocommit statements. A
valid grant committed between those component reads makes a sound exact
enqueue retry combine target fence 0 with durable grant fence 1 and report
false `integrity.schema` corruption. An exact replay must be proved against one
database snapshot while retaining its required ordering before an ended-grant
check.

Second, refused operation rows never reach that witness: `replay` revives them
first and `_history` skips them before semantic act adoption. An exact refused
retry therefore returns its policy outcome across a journal hole that the next
ordinary read detects, while an ordinary read accepts a refused operation kind
this build does not own. Refused acts have no materialized effect, but their
kind, typed signed operands, derived identity, dense order and sealed outcome
remain owned journal evidence and must be proved.

The deterministic reproduction and correction boundary are recorded in
`review-2026-09-06T11-45-47Z.md`. Item 3 remains changes-requested only for
these two P1s and their independent re-review. Per the owner review-stop
instruction, W71878 returns to operations for disposition rather than directly
to implementation or tuning.

## 2026-09-06 — item 3 eighth correction: decisions taken

Two rulings, both about the same thing the seventh round got half right: a
proof is only as good as the state it observed.

**A semantic proof observes ONE snapshot.** `IntegrationStore.snapshot` is a
re-entrant read transaction, and every semantic proof runs inside one: the
relationship pass, the lease and entry projections, and the replay witness
including the operation row it decides on. Inside `transact` the write
transaction the caller already holds IS the observation, so no second one is
opened. The required ordering for the fenced verbs is unchanged — an exact
replay is still decided before a now-ended live grant is checked — because the
snapshot changes what a read observes, not when it happens.

The read transaction is `BEGIN DEFERRED` rather than `BEGIN IMMEDIATE`: it
writes nothing, and taking the coordinator write lock would serialize two
coordinators' reads against each other for no coherence gain. The store also
asks for WAL, and this is a deployment-visible decision rather than a tuning
detail: under a rollback journal a reader's snapshot blocks every writer for
its duration, which in a store whose whole premise is two Authorities
contending for one target turns one coordinator's ordinary read into the
other's timeout. WAL is requested after the ownership decision and never
before, because a database this build refuses must be left exactly as it was
found. It is NOT required: coherence belongs to the read transaction and holds
in either journal mode, so a filesystem that cannot provide WAL yields a
correct store with a narrower concurrency story rather than a refusal to open.

**A refused act is coordinator evidence and is adopted whole.** `replay` no
longer branches on the recorded outcome at all; both go to the witness, which
owns the act's kind, its typed operands, its derived identity and its dense
position, and proves the relationship it was refused against, before the sealed
refusal is revived. A refused act has no materialized effect to be bound to —
it changed nothing, which is what makes it a refusal — but everything it says
about what was asked for, under which operands, at which position, remains
this store's history. `_history` adopts refused rows the same way and keeps
them out of the committed projection, which is what makes "a kind this build
does not own refuses the read" true of the whole journal rather than of its
committed half.

Neither ruling adds automatic recovery of any kind, and neither reopens a
blocked target: both are read-side proofs.

## 2026-09-06 — ninth item 3 review: bounded sign-off

Independent re-review accepts the item 3 coordinator slice after the eighth
correction. The replay operation row, its target/entry/lease relationship and
the history evidence it relies on are observed through one re-entrant SQLite
snapshot. The deterministic two-connection regression proves a concurrent
writer can commit a valid grant while the reader retains a coherent earlier
view and returns the original sound retry outcome. A write transaction remains
its own snapshot rather than opening a nested transaction.

Refused rows now pass generic row/seal validation and the same owned kind,
typed operand, derived identity and dense-order adoption as committed rows
before either exact replay or ordinary projection returns. They remain outside
the committed semantic projection, and an exact refused retry proves its
surrounding relationship before reviving the sealed refusal. Unknown,
ill-typed and noncanonical refused acts, and a journal hole beside a refused
act, are rejected without mutation.

Requesting WAL after the ownership decision is compatible with this contract:
the `BEGIN DEFERRED` read transaction supplies coherence in either journal
mode, while WAL permits the intended concurrent-writer regression. The change
does not make WAL a schema-ownership precondition. No automatic recovery is
introduced and no blocked target is reopened.

This is a bounded item 3 sign-off, not approval of immutable proposal bytes.
No proposal manifest or digest was supplied. Item 3b and items 4-9 remain
outside this review and unimplemented; under the owner disposition they return
to operations for ordered child-Work decomposition while W71878 remains their
umbrella.
