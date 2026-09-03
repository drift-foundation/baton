# Schedule concurrent v12 implementation and review stages

Ledger Work: W71877

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed scope

Compose pooled stage scheduling for independent implementation and review
work. The first deployment target is at least two concurrent implementation
containers and two independently schedulable review containers. Every offer
names one eligible participant/runtime profile, every successful claim and
attempt keeps its own authority identity, and every runtime has isolated
resources.

This leaf owns eligibility, capacity, soft continuation affinity, hard
independent-opinion separation, stage-scoped dependency checks, slot release,
and failure isolation. It reuses the persistent manager's submission/stage
state and the existing offer, claim, attempt, session, and runtime-lane
operations. It does not own source/workspace semantics, review checkpoint
format, verdict policy, or integration serialization.

## Observed baseline — 2026-09-02

- `worker_manager/offers.py` already owns concrete offer, acceptance, claim,
  expiry, settlement, and restart recovery operations.
- `worker_manager/lanes.py` prevents overlapping execution over one Work's
  assignment material; it is a per-Work execution interlock, not a global
  multi-Job pool scheduler.
- `worker_manager/sessions.py` owns posture-specific agent sessions and slot
  state within an attempt.
- No product component selects among a pool of eligible implementation or
  review runtimes, fills several independent slots, or advances review-ahead
  under stage-scoped dependency gates.

## Acceptance

- Configuration declares at least two implementation slots and two review
  slots with exact participant/runtime identities and capability eligibility.
- Two independent Jobs from one immutable baseline can be offered, claimed,
  and run concurrently without sharing a writable workspace, attempt,
  assignment generation, credential delivery, output, or log sink.
- Review can run concurrently with unrelated implementation. A reviewer is
  different from the candidate-producing runtime, and an explicit independent
  opinion cannot be satisfied by the prior reviewer.
- Ordinary continuation prefers useful context affinity but falls back to any
  eligible healthy slot without turning affinity into ownership.
- Implementation and integration dependency gates are checked at the named
  stage. An unrelated blocked stage does not hide review-ahead work whose
  contract is already knowable.
- A failed, refused, or wedged Job releases or quarantines only its own
  capacity according to recorded policy. Unrelated slots continue without a
  manager or v11 stack restart.
- Race tests prove one offer/claim winner per Job and no global slot leak on
  launch failure, normal completion, review completion, or process restart.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/` only for scheduler eligibility, capacity, affinity,
independence, stage-gate, race, and failure-isolation behavior described here.
Any deletion or weakened expectation must be explicit and independently
reviewed. Unrelated test mutations remain out of scope.

## Reviewer revalidation — 2026-09-03

### Observed current contracts

- The integrated W71875 package passes all 146 focused Job-manager tests at
  `efbad19`. `job_manager.manager.sweep` evaluates every stage in stable order
  and continues after an ordinary deferred act, while
  `projection.gates_of` opens each dependency from the named predecessor
  stage. Pool exhaustion on one kind therefore need not become a global queue
  head: it can defer that stage and continue to review-ahead work in the same
  sweep.
- A stage currently persists one derived `offer_id` and one derived
  `attempt_id`. `ManagerOperations` holds one participant-bound
  `AuthorityPort`, so it cannot choose among workers. `issue_offer` takes its
  participant only from that port and checks the authority claim slot, but an
  offer does not occupy that claim slot. Two stages could consequently issue
  offers to one participant before either claim unless this leaf reserves the
  logical worker before admission.
- `runtime_lanes` are acquired atomically at `request_runtime_start` and are
  keyed by authority, Work, principal, and effective scope. They prevent two
  attempts from executing over one Work's material; they do not limit a
  logical worker across independent Works. `posture_slots` are likewise
  attempt-local. Neither relation is a pool-capacity substitute.
- `attempt_runtime_of` already exposes the canonical `runtime_id`,
  `execution_runtime`, `cleanup`, and fixed assignment. Cleanup `complete` or
  `retained` follows positive runtime absence and releases the Work runtime
  lane; cleanup `failed` does not. Those are the safe canonical facts from
  which the scheduler may release or quarantine its own capacity. Frozen
  output alone is not a release condition.
- The existing CLI's `--operations module:attribute` factory is the trusted
  deployment seam for participant-bound sessions, bearer mint/delivery, and
  runtime adapters. Pool configuration belongs behind that seam and in the
  Job store's durable projection; it must not add a CLI that mints authority
  sessions or accepts per-transition worker choices.

### Proposed identity mapping

The parent ruling's three identities map onto existing canonical ownership
without inventing aliases:

- `worker_id` is new scheduler-owned durable identity for the reusable logical
  context and affinity target;
- `assignment_id` is the active stage episode's Worker Manager
  `runtime_attempt_id` (the current `attempt_id`); and
- `incarnation_id` is the Worker Manager's attached `runtime_id`, the exact
  container/process identity returned by the adapter.

The status surface should name all three meanings explicitly. It must not mint
a second assignment or incarnation id beside the Worker Manager's owner. A
later assignment may keep `worker_id` while receiving a new attempt and
runtime id.

### Proposed pool document and durable relations

Trusted deployment supplies one closed, versioned pool document. Each worker
entry carries `worker_id`, exact participant, `(profile_name,
profile_digest)`, and a closed set of eligible stage kinds. Several workers
may instantiate the same profile; names such as `impl2` or duplicated profiles
created only to manufacture capacity are forbidden. Eligibility may overlap
between implementation and review. Worker ids and participants are unique in
the document, and construction proves that each supplied `AuthorityPort` is
bound to the participant its entry names.

Distinct participant strings are not proof of distinct authority capacity:
the authority intentionally keys claim slots by principal. The two-slot
acceptance fixture must therefore demonstrate two distinct returned claim
principals. Participant aliases that resolve to one principal are reported as
one effective claim capacity after the canonical refusal; the scheduler must
not count them as two successful concurrent workers.

Persist the normalized document or its complete rows, not its digest alone.
The minimum deployment fixture has at least two implementation-eligible and
two review-eligible workers; the general component need not turn that
milestone size into a universal lower bound.

Add scheduler-owned relations to the Job store rather than to the Worker
Manager control store:

- immutable configured worker rows;
- append-only allocation rows keyed by `assignment_id`, carrying stage,
  worker, participant, preferred worker (when any), selection outcome,
  reservation/release instants, and the scheduler occupancy;
- one partial unique index for a live allocation per worker and one for a live
  allocation per stage episode; and
- an affinity row from the private development-line identity (the Work id in
  this slice) to its preferred `worker_id`.

Scheduler occupancy is a real owned axis, not shadow runtime state:
`occupied`, `recovery-required`, or `released`. `recovery-required` continues
to consume capacity. Silence and elapsed time never move either occupied
state to released.

### Proposed selection and settlement order

1. Start only from an `admit` act already derived as owed by the persisted
   stage/dependency projection. Compute eligible workers by exact stage kind
   and exact profile pair, then remove occupied/recovery-required workers and
   every hard independence exclusion.
2. Prefer the recorded worker affinity. If it is unavailable, select a stable
   eligible healthy worker and record both the preferred and actual worker;
   do not rewrite affinity or present the replacement as the same context.
3. Reserve the worker in one `BEGIN IMMEDIATE` Job-store transaction before
   `issue_offer`. The unique indexes decide competing managers and competing
   stages. A temporary capacity miss is an ordinary deferred act, so the
   sweep continues to unrelated stages. A static no-eligible-worker result is
   projected as exceptional with the exact missing kind/profile, rather than
   deferred forever.
4. Issue and claim through the selected worker's participant-bound operations.
   Adoption of any existing `offer.issue` record must additionally compare
   its signed `participant` operand with the persisted allocation. The current
   intent binding compares only stage/job operands and is insufficient once
   participant selection becomes scheduler state.
5. Keep the allocation through offer, claim, runtime, output, intake, and
   cleanup. Release it idempotently only after canonical offer settlement
   proves no assignment exists, or canonical attempt cleanup is `complete` or
   `retained`. Canonical `uncertain`/surviving-runtime or cleanup `failed`
   moves only that allocation to `recovery-required`; explicit positive
   recovery evidence may later release it. A crash before this Job-store act
   leaks capacity conservatively until the next sweep; a crash after it
   replays the same release.

For review selection, exclude the implementation allocation that produced the
checkpoint and every reviewer allocation already recorded for the same
independent-opinion request. The hard comparison is on logical `worker_id`
and participant, not merely on runtime id: restarting the same logical context
does not create an independent opinion. W71918 supplies checkpoint and review
round identity; this leaf owns applying those exclusions once supplied.

### Patch boundary

The expected production boundary is a new `job_manager` pool/scheduling module
plus deliberate updates to `job_manager/schema.py`, `store.py`,
`delegation.py`, `manager.py`, `projection.py`, `documents.py`, package
exports, and `tools/job_manager.py`. The tool continues to load a trusted
deployment factory; read-only status obtains pool/allocation facts from the Job
store and receives no authority capability.

Focused tests belong under `v12/python/tests/job_manager/` and cover document
closure, duplicate identities, exact profile eligibility, two simultaneous
implementation reservations, review beside unrelated implementation,
affinity preference/fallback, producer/prior-reviewer exclusion, reservation
races, participant-bound offer adoption, every release/quarantine ending, and
restart replay. Existing Worker Manager tables and private lane/slot helpers
are not scheduler patch targets. W71917 owns concrete source/workspace mounts,
W71918 owns checkpoint/correction history, and W71879 owns the real combined
container demonstration.

### Confirmed blocking defect discovered during revalidation

W73629 is the causally tied child record at
`findings/finding-abandoned-stage-offer-recovery/`. A different Worker Manager
incarnation currently abandons an unaccepted issued offer while the Job
manager retains its `admit` receipt, projects `offered`, and retries `claim`
against the terminal offer forever. The retained reproduction is
`/tmp/w71877-abandoned-offer-repro.py`.

W71877 must wait for W73629's append-only stage-episode recovery contract.
Deleting the old receipt, treating the abandoned offer as live, or merely
freeing the pool slot would hide the defect and still leave the Job wedged.

### Proposed schema cutover

Pool configuration, allocation history, and affinity require a Job-store
schema bump and a status schema bump. The recommended first-slice rule is an
explicit schema-1-to-schema-2 migration performed transactionally after the
schema-1 object set and metadata are validated; a valid persisted submission
must not be discarded merely because the next milestone adds scheduler-owned
relations. If the operator instead chooses a clean-store cutover, that is a
product decision to record here before implementation, including how existing
schema-1 Jobs are reported and retired.

## Reviewer revalidation after W73629 integration — 2026-09-03

### Confirmed current baseline

- W73629 closed satisfying and is integrated at `4876751`. The Job store is
  now schema 2, with append-only execution episodes and episode-aware receipts;
  the abandoned-offer reproduction no longer wedges a stage. The focused
  Job-manager discovery runs **188 tests, all passing** at this checkpoint.
  This explicitly resolves and supersedes the present-tense defect/blocking
  statements in “Confirmed blocking defect discovered during revalidation”;
  that section remains chronological evidence of why the child was required.
- The migration mechanism is now a GENERAL ordered loop over `MIGRATIONS`, not
  a one-off schema-1 special case. This leaf therefore needs a transactional
  **schema-2-to-schema-3** step for scheduler-owned relations. A valid schema-1
  store can advance transitively through 1 -> 2 -> 3 under the already accepted
  migration rule. The earlier schema-1-to-schema-2 wording above is historical
  proposal context and is superseded for implementation by this fact; a
  clean-store cutover is no longer the recommended branch.
- W71917 is open at `baton.ops`, awaiting human acceptance of the immutable
  source and persistent workspace contract. W71918 remains blocked on W71917.
  W71877 may implement scheduler-owned eligibility, reservation, affinity and
  settlement without inventing either leaf's semantics, but its real
  launch/checkpoint composition remains pending those outputs.

### Proposed first-slice settlement table for operator acceptance

The pool allocation and the stage episode are separate durable axes. The
scheduler should apply this closed table rather than infer release from a broad
"terminal" label:

- `issued` and `accepted`: allocation stays `occupied`;
- `claimed`: allocation stays `occupied` through runtime, output, intake and
  cleanup;
- `abandoned-after-restart`, `declined`, `expired`, `claim-refused`, and
  `settlement-expired`: once the canonical ending is durably applied to the
  episode, no assignment exists, so release that allocation idempotently;
- canonical attempt cleanup `complete` or `retained`: release idempotently;
- surviving/uncertain runtime evidence or cleanup `failed`: move only that
  allocation to `recovery-required`, which continues to consume capacity until
  explicit positive recovery evidence permits release.

**Proposed retry policy:** keep `REPLACEABLE_ENDINGS` limited to
`abandoned-after-restart` in this first slice. `declined`, `expired`,
`claim-refused`, and `settlement-expired` release pool capacity but leave the
stage visibly `exceptional`; they do not silently create another episode.
Retrying them needs a separately bounded retry budget and worker-exclusion
policy. Neither exists in the accepted Job contract, so inventing both inside
capacity management would expand this leaf and could loop forever across a
finite pool.

### Proposed principal-capacity correction for operator acceptance

The earlier review-selection sentence saying the hard comparison is on
`worker_id` and participant is INCOMPLETE and is superseded by this section.
The Authority keys claim capacity by canonical principal, and several
participant endpoints may resolve to the same principal. Two aliases would
therefore evade a worker/participant-only independence exclusion even though
they are one actor and one effective claim slot.

At pool attachment, trusted deployment must resolve and prove each entry's
canonical principal through the Authority-owned mapping; the scheduler never
derives a principal from the participant spelling. Persist that resolved
principal with the normalized worker row and allocation, revalidate it on a
later attachment, and compare the claim's returned authorization principal to
the reserved one before adopting the claim. Add a partial unique index for one
live allocation per principal as well as per worker and stage episode. Aliased
workers may remain explicit configuration entries, but they contribute one
effective concurrent capacity and cannot reserve simultaneously.

Producer and prior-reviewer exclusion is consequently a hard comparison over
all three durable identities: logical `worker_id`, participant endpoint, and
canonical principal. A different endpoint or restarted worker resolving to the
same principal is not an independent opinion. W71918 still owns which review
rounds and prior opinions supply the exclusion set; this leaf owns applying
that set without identity aliasing.

“Healthy” in the earlier affinity prose adds no separate worker-health or
disabled-worker state. It means an entry whose configuration/principal mapping
still validates and which has no `occupied` or `recovery-required` allocation.

### Decisions now requested

Before implementation, the operator should accept or revise:

1. the proposed identity mapping, pool document, durable allocation/affinity
   relations, canonical-principal capacity/independence correction,
   participant-bound adoption check, and reserve-before-offer order recorded
   above;
2. the closed settlement and first-slice no-retry policy in this revalidation;
   and
3. schema 3 as a transactional 2 -> 3 migration, with schema 1 advancing
   transitively through the already integrated 1 -> 2 step.

Acceptance authorizes the bounded scheduler patch described above. It does not
authorize W71917 mounts, W71918 checkpoint/verdict semantics, or W71879's real
two-Job demonstration.

## Operator acceptance of decision 1 — 2026-09-03

The operator accepted the identity, pool, capacity, affinity,
participant-bound adoption, and reserve-before-offer direction with the
following clarifications. These clarifications supersede the earlier statement
that implementation and review eligibility may overlap, the bare
development-line-to-worker affinity row, and any reading of `worker_id` as an
ACP or provider session.

`worker_id` is a durable virtual capacity/persona owned by the scheduler. It is
neither a runtime profile, provider session, assignment, nor running process.
An assignment may create a new container incarnation while retaining its
logical worker. The provider-neutral Baton term is `AgentSession`; a driver
maps it to an ACP session, Codex app-server thread, or another provider-native
context without exposing that transport choice to scheduler code.

Logical workers have immutable lanes. Implementation and review workers are
distinct virtual workers with distinct participants, canonical principals,
and agent sessions. A runtime image, adapter, credential provider, or provider
may be reused, but an implementation session can never be adopted or resumed
as a review session. The first review opinion starts fresh relative to the
implementation context; an implementation correction may resume its own
implementation session, and a reviewer rechecking its requested correction
may resume that opinion's review session. A new independent opinion requires a
different eligible reviewer and fresh review session.

Affinity is subordinate to lane eligibility and hard independence exclusions.
The scheduler first selects the required lane, excludes the producer,
conflicting principal and any prior reviewer disallowed for the requested
opinion, and only then applies affinity among the remaining workers.
Implementation affinity cannot select a reviewer, review affinity cannot
select an implementer, and a new-opinion requirement overrides prior-reviewer
affinity. The durable keys are at least development line plus lane for worker
affinity and development line plus lane/opinion plus worker for agent-session
continuity. W71877 owns worker selection and affinity; W71918 owns the durable
provider-neutral session binding and correction/review continuation mechanics.

The normal deployment posture uses disjoint provider/model profiles for
implementation and review, preserving the proven v11 separation. A named
degraded posture may use the same provider for both roles, but it still uses
distinct lane workers, principals, exact role/model/skill profiles, and fresh
cross-lane sessions. Separation is recorded as provider-diverse,
same-provider/different-model, or same-provider/same-model with fresh context.
Deliberately supplied immutable implementation evidence may be reviewed;
hidden conversational state is never inherited across lanes.

Pool configuration is immutable per generation rather than for the lifetime
of the store. An explicit activation may select a different named posture and
creates a new configuration generation; existing assignments remain bound to
the generation under which they began, while only new offers use the new
generation. Unannounced document or identity drift refuses. This makes an
emergency provider fallback a configuration operation, not a code change or a
silent reinterpretation of live work.

The first acceptance deployment must prove four simultaneously reservable
effective capacities: two implementation workers and two review workers, each
with the distinct canonical principal required by the Authority claim-slot
rule. Profiles may be reused across workers, but aliases do not manufacture
capacity. Status and review evidence expose the pool generation, lane,
worker, participant/principal, exact profile/model when observable, normalized
agent session, assignment and incarnation so the active separation posture is
auditable.

This acceptance covers decision 1 only. The settlement/no-retry policy and
schema-3 migration remain separate operator decisions.


## Implementer revalidation of accepted decision 1 — 2026-09-03 (`baton.claude`)

Review only, at baseline `4876751`; no production or test file was changed and
no implementation was begun. Decision 1's direction is sound and most of it is
grounded in contracts that exist today. Four gaps and two naming contradictions
stand between it and a bounded patch, and one of them makes this leaf's
headline acceptance proof vacuous on the current fixtures.

### Grounded, and confirmed against the code

- **Principal-keyed claim capacity is real.** `authority/core.py`'s claim slot
  is keyed by `principal_id` with `ON CONFLICT (principal_id)`, and refuses
  with "a principal holds ONE active claim at a time, across every endpoint
  address it acts through". The correction requiring FOUR distinct canonical
  principals is therefore necessary, not defensive.
- **The Authority owns a resolution.** `authority.api.principal_of` and
  `slot_holder_of_principal` exist, and `principal_for_endpoint` is the
  authority's own default for an unbound endpoint. "The scheduler never derives
  a principal from the participant spelling" is enforceable in principle.
- **Reserve-before-offer remains correct.** `issue_offer` still takes its
  participant only from the bound port, and an offer still does not occupy the
  authority claim slot, so two stages can still issue offers to one participant
  before either claim.

### Contradiction 1 — `posture` already names a different closed vocabulary

`worker_manager/schema.py` defines `POSTURES = ("consent", "execution")` and
says explicitly that posture "says WHICH CONTAINER this is" and is "a third
vocabulary rather than a subdivision of either axis". Decision 1 uses "posture"
for the deployment SEPARATION stance -- normal versus a named degraded
provider-sharing mode. One product would carry one word over two closed sets.

Recommend renaming the scheduler concept (for example "separation posture" is
still colliding; "separation stance" or "pool generation posture" is not) before
it reaches code, docs and status output.

### Contradiction 2 — scheduler occupancy collides with `SLOT_OCCUPANCY`

`worker_manager/schema.py` defines `SLOT_OCCUPANCY = ("available", "occupied",
"recovery-required")` for the attempt-local posture slot. This leaf's scheduler
occupancy is `occupied` / `recovery-required` / `released`. Two of three
members are spelled identically on a different axis and the third differs.

This is the more dangerous of the two, because this FINDING already insists
scheduler occupancy "is a real owned axis, not shadow runtime state" -- and an
implementer or reader meeting `recovery-required` cannot tell which axis it
belongs to without checking. Recommend distinct member spellings for the
scheduler axis.

### Gap 1 — the canonical principal has no contracted surface to be proved on

No module in `worker_manager` or `job_manager` references `principal_of` or
`slot_holder_of_principal`, and `AuthorityPort.SESSION_OPERATIONS` does not
name any principal read. `slot_holder(participant)` answers WHICH WORK an
endpoint's slot holds, not which principal that endpoint is.

`AuthorityPort.__init__` checks only that the named members exist and are
callable, so a deployment CAN supply a session that also carries a principal
read without touching `worker_manager` -- but that member would be uncontracted
and unvalidated, which is exactly what this codebase refuses everywhere else.

The ordering makes this load-bearing rather than cosmetic: the authorization
principal is only RETURNED by the claim, while reserve-before-offer and the
proposed per-principal unique index both need it at reservation time. So
resolution at pool attachment is the only place it can come from.

**Decide one:** name a principal read in the port's contract -- a deliberate
`worker_manager` change that the recorded patch boundary currently excludes --
or have trusted deployment supply the resolved principal as configuration and
record here how it is proved and revalidated.

### Gap 2 — the pool generation appears in no recorded relation

Decision 1 makes configuration immutable per generation, binds existing
assignments to the generation they began under, and refuses unannounced drift.
The recorded durable relations name worker rows, allocation rows, an affinity
row and three unique indexes -- and no generation column on any of them.
Without a generation on both the worker row and the allocation, "assignments
remain bound to their generation" cannot be enforced and "drift refuses" has
nothing to compare against.

### Gap 3 — the relation list still shows superseded shapes

Decision 1 supersedes the bare development-line-to-worker affinity row with
lane-scoped keys (development line plus lane for worker affinity; development
line plus lane/opinion plus worker for session continuity), and the principal
correction adds a per-principal live-allocation index. Both supersessions exist
only in prose; the relation list an implementer reads still describes the old
affinity row and the two-index set. Restate the durable relations once, in
their accepted final shape.

### Gap 4 — the durable `AgentSession` identity does not exist, and the
### W71877/W71918 boundary is inverted

`agent_sessions` is keyed by `(runtime_attempt_id, posture, session_epoch)`:
sessions are ATTEMPT-LOCAL. `adopt_provider_session` records the PROVIDER's own
session id, once and never rewritten. So the only cross-assignment continuity
handle that exists today is provider-native -- precisely what Decision 1 says
must not reach scheduler code.

PLAN item 5 nevertheless asks W71877 to "expose a provider-neutral
`AgentSession` boundary to W71918", while Decision 1 assigns "the durable
provider-neutral session binding and correction/review continuation mechanics"
to W71918. There is nothing yet for W71877 to expose: the neutral durable
identity IS the thing W71918 is said to own, so as written each leaf waits on
the other.

**Decide one:** W71877 mints the provider-neutral session identity and W71918
consumes it, or W71877 persists only lane and worker and W71918 introduces the
session identity when it lands. The prohibition on cross-lane session reuse is
enforceable under either, because it is a lane/worker comparison and does not
need the session identity.

### Gap 5 — the separation stance is not mechanically checkable

Decision 1 records separation as provider-diverse, same-provider/different-model
or same-provider/same-model, and asks status to expose "exact profile/model when
observable". `certify_profile(kind, name, digest)` carries free text and a
digest; no provider or model structure exists anywhere in v12. The stance is
therefore an operator-ASSERTED configuration label, not a fact derived from
canonical state.

That may be perfectly acceptable for this slice, but it should be recorded as a
declared auditable label rather than implied to be proved -- otherwise a
same-provider/same-model deployment could record itself as provider-diverse and
nothing would notice.

### Test-boundary gap — the four-capacity proof is vacuous on current fixtures

`tests/job_manager/fixtures.py` defines one `PRINCIPAL = "principal:org-a"`, and
`decision(participant)` returns that same principal for EVERY participant. The
fake models the exact aliasing case Decision 1 says must count as one effective
capacity, and it enforces no slot at all.

A four-worker reservation test written on this fixture would observe four
successful claims, while the real authority would refuse three. This leaf's
headline acceptance -- "four simultaneously reservable effective capacities" --
would pass for the wrong reason.

The acceptance fixture must give each worker a DISTINCT canonical principal and
the fake session must enforce the principal-keyed claim slot, so that the
aliasing case fails and the four-principal case passes for the reason the
Authority actually gives.

### Is the implementation bounded?

**Not yet, but narrowly so, and no redesign is implied.** The selection,
reservation, settlement and affinity design is coherent and rests on contracts
that exist. Bounded once: the two vocabulary collisions are renamed; gaps 1-3
are decided and the durable relations restated in final shape; gap 4's
ownership is settled either way; gap 5 is accepted as a declared label; and the
fixture gains distinct principals with a principal-keyed slot.

Independently of that, decisions 2 and 3 are still open, so implementation
cannot start regardless of these corrections.

## Operator clarification of implementer preflight — 2026-09-03

For a large or complex accepted plan, Baton may ask the selected implementer
for a review-only preflight before the implementation handoff. This is an
implementation-lifecycle signal, not an independent review verdict or a move
through the review Route. The implementer inspects the current plan and code,
confirms whether the patch boundary is executable, and reports contradictions,
missing decisions, or test-boundary gaps without claiming implementation Work
or changing production or test files.

The operator resolves any reported gaps and updates the durable decision record
before making the real implementation handoff. A clear preflight may establish
the implementation lane's intended affinity, but it never satisfies the later
independent review requirement and never permits an implementation session to
be reused as a review session.

## Operator resolution of implementer-preflight naming conflicts — 2026-09-03

The scheduler vocabulary must not reuse Worker Manager `posture` or
`SLOT_OCCUPANCY`. A named immutable deployment choice is a **pool variant**,
for example `primary` or `fallback-claude`; activating a variant creates a new
pool generation. Its independently recorded **separation class** is one of
`provider-diverse`, `same-provider/different-model`, or
`same-provider/same-model-fresh-context`. In the first slice this class is an
operator-declared, auditable assertion rather than a fact inferred from free-
text profile metadata.

The scheduler-owned axis is **allocation state**, with the closed members
`reserved`, `recovery-required`, and `released`. A reserved allocation or one
requiring recovery consumes capacity. This vocabulary is deliberately distinct
from the attempt-local posture-slot occupancy owned by the Worker Manager.

## Operator resolution of canonical-principal persistence — 2026-09-03

Each participant-bound `AuthorityPort` exposes one read-only
`canonical_principal()` operation backed by the Authority-owned participant-to-
principal mapping. Pool activation obtains the principal through that port;
trusted deployment does not duplicate or derive it from participant spelling.
This narrow Worker Manager contract extension is part of W71877.

The Job store persists each configured worker's participant, canonical
principal, lane, exact profile and pool generation, and persists the same
worker, principal and generation on every allocation. Restart loads those
immutable rows, recreates the participant-bound ports, and re-resolves every
principal before admitting work. An unexpected mismatch refuses attachment and
never rewrites the persisted association. An affected live allocation remains
bound to its original generation and requires explicit recovery; a deliberate
configuration change instead activates a new pool generation for new offers.

Claim adoption compares the claim's returned authorization principal with the
reserved principal. Two participant aliases resolving to one principal therefore
share one effective live capacity across restart as well as within one process.
Runtime incarnations may change on restart; logical worker, participant,
principal, lane, generation and allocation identities do not.

## Operator resolution of final scheduler relations — 2026-09-03

The scheduler persists the accepted model in four relation families:

- `pool_generations` records the generation, pool variant, declared separation
  class, complete normalized configuration and digest, and activation time;
- `pool_workers` records generation, durable `worker_id`, immutable lane,
  participant, canonical principal, exact profile name/digest, and eligible
  stage kinds;
- `stage_allocations` records the assignment/stage episode, generation,
  selected worker, participant, principal, preferred worker, selection outcome,
  allocation state, and reservation/recovery/release instants; and
- `worker_affinity` records development line plus lane to preferred `worker_id`
  as a soft preference.

Partial unique indexes permit at most one live allocation per `worker_id`, per
canonical principal, and per stage episode. `reserved` and
`recovery-required` are live; `released` remains durable history without
consuming capacity. These constraints apply across generations. Both configured
worker rows and allocation rows carry the pool generation, so activating a new
variant affects only new assignments and never silently reinterprets existing
allocations.

W71877 persists lane and logical-worker affinity but does not mint or persist a
durable provider-neutral `AgentSession`. W71918 owns that later session identity
and its correction/review continuity relations. Cross-lane session reuse is
already forbidden by W71877's disjoint lane, worker, participant and principal
rules and does not wait for the session relation.

## Operator resolution of the capacity acceptance fixture — 2026-09-03

The four-capacity acceptance fixture must model Authority behavior rather than
merely return successful canned claims. Its positive path assigns four distinct
canonical principals to two implementation and two review workers and proves
all four reservations can be live concurrently. The fake Authority enforces
one active claim per principal across participant aliases.

A negative fixture maps multiple participants to one principal and proves they
contribute one effective live capacity, not one capacity per endpoint spelling.
Restart coverage reloads the persisted worker/principal associations and
revalidates them through the contracted Authority port. This correction changes
no product behavior; it prevents the headline concurrency test from succeeding
under conditions the real Authority would refuse.

## Operator acceptance of decision 2 — 2026-09-03

The first scheduler slice uses the closed settlement table proposed after
W73629. `issued`, `accepted`, and `claimed` keep the allocation `reserved`.
After its canonical ending is durably applied, `abandoned-after-restart`,
`declined`, `expired`, `claim-refused`, and `settlement-expired` release the
allocation because no assignment exists. Canonical attempt cleanup `complete`
or `retained` also releases it. Surviving or uncertain runtime evidence and
cleanup `failed` move only that allocation to `recovery-required`, which keeps
consuming capacity until explicit positive recovery evidence permits release.

Only `abandoned-after-restart` automatically creates a replacement episode in
this slice, using W73629's accepted recovery contract. Other pre-assignment
endings release capacity but leave the stage visibly exceptional. An operator
may explicitly retry later; W71877 does not invent a retry budget, worker-
exclusion loop, or silent pool-wide fallback.

## Operator acceptance of decision 3 — 2026-09-03

The v12 Job store advances to schema 3 through one transactional `2 -> 3`
migration. The existing ordered migration loop advances a valid schema-1 store
transitively through `1 -> 2 -> 3`; this cutover preserves existing Jobs,
stages, receipts, and execution episodes rather than requiring a clean store.
The new scheduler relations begin empty, and an existing unallocated stage
receives an allocation only when it is subsequently admitted.

Migration first validates the complete schema-2 object set. Any failure rolls
back the whole step, leaving no partial scheduler relations or indexes. Schema
transitions are expected and may be frequent while v12 remains experimental;
each still has an explicit ordered migration and fail-closed validation. This
v12 Job-store migration has no v11 schema or deployment consequence.
