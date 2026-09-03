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

### Confirmed identity mapping

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
   and exact profile pair, then remove disabled/recovery-required workers and
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
