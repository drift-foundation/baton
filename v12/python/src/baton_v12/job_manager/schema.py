"""The Job manager's own store, and the marker that says whose it is.

W71875. THIS IS A THIRD SQLITE FILE, deliberately. `baton_v12/__init__.py`
already rules that the authority and the Worker Manager keep separate modules,
files, connections, schemas and transactions; a scheduler that wrote its
submissions into the manager's control store would make the manager's schema
version a scheduler concern and give one transaction two owners. The kind
marker below is what makes "is this store mine" answerable at all -- version 1
is true of several stores in this deployment.

WHAT THIS SCHEMA MAY AND MAY NOT HOLD. It holds the submitted intent, the
Jobs and stages derived from it, and the RECEIPT of each act this control
plane delegated. It holds no offer, claim, attempt, session, runtime, output,
intake or retention state: those live in the manager's control store, are
advanced only by the manager's own operations, and are read back through that
package's public readers. A column here recording "this stage is running"
would be the shadow lifecycle this leaf was told not to build -- so the state
an operator reads is DERIVED at projection time and is stored nowhere.
"""

from ..contracts import ContractRefusal
from ..worker_manager.boundaries import Column

__all__ = ["ALLOCATION_COLUMNS", "AFFINITY_COLUMNS", "EPISODE_COLUMNS",
           "DEFERRAL_COLUMNS", "GENERATION_COLUMNS", "MIGRATIONS", "POOL_WORKER_COLUMNS", "SCHEMA", "SCHEMA_VERSION",
           "check_authority",
           "STORE_KIND", "TABLES", "JOB_COLUMNS",
           "JOB_EXECUTION_LIMIT_COLUMNS", "OPERATION_COLUMNS",
           "OPERATION_STATES", "RECEIPT_COLUMNS", "RECEIPT_STATES",
           "STAGE_COLUMNS", "SUBMISSION_COLUMNS"]

STORE_KIND = "baton.v12.python.job-manager"


def check_authority(value, *, what):
    """The Authority UUID rule, REUSED and answered in this leaf's vocabulary.

    W83781. Two things have to be true at once and they pull in opposite
    directions. The RULE must be the Authority package's own -- a second,
    looser spelling of "32 lowercase hex" living in the Job manager is exactly
    the drift the finding forbids, and it is the kind that stays invisible
    until two components disagree about one identity. But the REFUSAL a caller
    of this package catches must be this package's, because everything else
    here raises `ContractRefusal` and a boundary that sometimes raises
    somebody else's exception is a boundary callers have to special-case.

    So the predicate is imported and the refusal is translated. Nothing is
    re-implemented and nothing leaks: `check_authority_uuid` opens no store,
    holds no session and grants nothing -- it is a rule, not a capability, and
    importing a rule is not importing an Authority.
    """
    from ..authority.errors import Refusal
    from ..authority.identity import check_authority_uuid

    try:
        return check_authority_uuid(value, what=what)
    except Refusal as refused:
        raise ContractRefusal("integrity", "schema", str(refused)) from None

# Two. W73629 added the stage EPISODE, because one restart can end a stage's
# offer without ending the stage: the manager abandons an offer whose bearer it
# cannot account for, and the stage then needs a fresh offer and a fresh
# attempt while the abandoned one stays auditable. Schema 1 had one derived
# offer and one derived attempt per stage and no room to say that.
# Three. W83781 bound the store to ONE AUTHORITY. Episode identities were
# derived from the stage id and the episode number alone -- both local to one
# Job store -- so two independent authorities running the same local stage name
# derived the same OCI attempt identity, and a fresh authority's first episode
# collided with a retained container belonging to somebody else entirely. The
# namespace has to come from somewhere globally unique, and the only such thing
# a Job store legitimately knows is which Authority it belongs to.
# Four. W71877 added immutable worker-pool generations, durable virtual workers,
# per-stage-episode allocations and lane-scoped soft affinity. These relations
# reserve canonical-principal capacity transactionally before any offer side
# effect while leaving the offer, claim, runtime and cleanup lifecycles with the
# Worker Manager.
#
# THE 2 -> 3 STEP ADDS NO TABLE, and that is the whole point of doing it as a schema
# version anyway: what changes is a REQUIRED meta row, so a schema-2 store
# opened by this build must be pinned to an Authority in the same transaction
# that stamps the version, and a store that predates the pin must not be read
# as though it had one.
# Five. W156162 added the per-Job execution limits a Job may configure. They
# live in their OWN table rather than as columns on `jobs`, and the reason is
# mechanical as well as tidy: `JobStore._schema_three_shape` derives the
# schema-3 expectation by subtracting what the migrations after 3 CREATE, and a
# step that ALTERED an existing table could not be subtracted from it.
SCHEMA_VERSION = 7

# W197661 review 2026-09-18T02-59-56Z [R2]: `deferrals` was in `SCHEMA` and in
# the migration and NOT here, and `JobStore`'s required-table validation reads
# exactly this tuple -- so a schema-7 store missing the new relation would have
# opened as valid and then faulted at the first deferral. A relation the build
# creates is a relation the build requires.
TABLES = ("meta", "operations", "submissions", "jobs",
          "job_execution_limits", "stages", "episodes",
          "receipts", "deferrals", "pool_generations", "pool_workers",
          "stage_allocations", "worker_affinity")

OPERATION_STATES = ("committed", "refused")

# What a receipt records about the canonical act it names. `performed` is this
# incarnation calling the operation; `adopted` is this incarnation finding the
# operation ALREADY COMMITTED in the manager's journal and recording that fact
# instead of performing it again. They are two rows-worth of different history
# and a restart audit needs to tell them apart.
RECEIPT_STATES = ("performed", "adopted", "refused")

SCHEMA = """
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE operations (
  operation_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  signature TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('committed', 'refused')),
  result TEXT,
  refusal TEXT,
  settled_at TEXT NOT NULL,
  CHECK ((state = 'committed' AND refusal IS NULL)
         OR (state = 'refused' AND result IS NULL AND refusal IS NOT NULL))
);

CREATE TABLE submissions (
  submission_id TEXT PRIMARY KEY,
  signature TEXT NOT NULL,
  document TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);

CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  submission_id TEXT NOT NULL REFERENCES submissions(submission_id),
  ordinal INTEGER NOT NULL,
  input_digest TEXT NOT NULL,
  policy_digest TEXT NOT NULL,
  test_scope TEXT NOT NULL,
  terminal_policy TEXT NOT NULL
);

-- W73629: THE STAGE NO LONGER CARRIES AN OFFER OR AN ATTEMPT. It carries what
-- was SUBMITTED about it, which never changes; which offer and which attempt
-- are currently trying to satisfy it is the episode's, and a stage that held a
-- copy of the live episode's identities would be two accounts of one fact the
-- moment a second episode opened.
-- W156162: WHAT ONE JOB ASKED FOR, and nothing about what it got.
--
-- The requested settings are the Job's immutable intent, stored exactly as the
-- submission stated them. The EFFECTIVE per-boundary seconds are derived at
-- read time from these plus this build's compatibility defaults, and are
-- deliberately NOT stored: a stored resolution would be a second account of a
-- fact the defaults already own, and it would go stale the moment a default
-- moved -- while the Job's own choice must never be reinterpreted.
--
-- A Job that configured nothing has NO ROW here, which is the same statement
-- as a /1 submission: every boundary keeps its runner default.
CREATE TABLE job_execution_limits (
  job_id TEXT PRIMARY KEY REFERENCES jobs(job_id),
  requested TEXT NOT NULL,
  -- W156162 review 2026-09-13T01:13:49Z R1: AND THE FROZEN DEFAULTS IT WAS
  -- ADMITTED UNDER. Resolution is derived from the Job's own settings plus this
  -- generation's table, never from whatever the constants happen to say at read
  -- time -- so a later default change is a new generation for new Jobs and
  -- reinterprets nothing already admitted.
  compatibility_generation INTEGER NOT NULL CHECK (compatibility_generation >= 0)
);

CREATE TABLE stages (
  stage_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(job_id),
  ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL,
  work_id TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  depends_on TEXT NOT NULL,
  UNIQUE (job_id, kind)
);

-- ONE STAGE'S SUCCESSIVE ATTEMPTS AT BEING ADMITTED, append-only.
--
-- An episode is opened with its own offer and attempt identities and is never
-- rewritten except to record the ONE canonical ending it was observed to
-- reach. That ending is what makes a wedged stage recoverable and auditable at
-- the same time: the abandoned episode keeps its identities, its receipts and
-- its ending, and the replacement is a new row rather than an overwrite.
--
-- `ended_revision` is the publisher's monotonic rank for the state that ended
-- it, kept so a later, staler assertion about the same offer can be recognised
-- as older than what is already recorded rather than applied over it.
CREATE TABLE episodes (
  stage_id TEXT NOT NULL REFERENCES stages(stage_id),
  episode INTEGER NOT NULL CHECK (episode >= 1),
  offer_id TEXT NOT NULL UNIQUE,
  attempt_id TEXT NOT NULL UNIQUE,
  opened_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  ended_state TEXT,
  ended_revision INTEGER,
  ended_at TEXT,
  PRIMARY KEY (stage_id, episode),
  -- AN ENDING IS ALL THREE OR NONE. A row naming a state without the revision
  -- that asserted it is an ending nobody can order against the next assertion.
  CHECK ((ended_state IS NULL AND ended_revision IS NULL
          AND ended_at IS NULL)
      OR (ended_state IS NOT NULL AND ended_revision IS NOT NULL
          AND ended_at IS NOT NULL))
);

-- ONE LIVE EPISODE PER STAGE. A partial index, because ended episodes are
-- history and history does not hold the slot. This is what makes "one
-- abandoned episode gets at most one replacement" a fact about the table
-- rather than a rule a handler remembers: a duplicate abandonment notice
-- cannot open a second live episode, whatever order it arrives in.
CREATE UNIQUE INDEX episodes_one_live_per_stage
    ON episodes (stage_id) WHERE ended_state IS NULL;

-- ONE RECEIPT PER (STAGE, EPISODE, ACT), and the primary key is what enforces
-- it. A second row for one act is exactly the repeated act restart
-- reconciliation exists to prevent, so it is refused by the table rather than
-- by a rule somebody remembers to apply. The EPISODE is in the key because a
-- replacement legitimately performs its own `admit`: without it the fresh
-- episode's receipt would collide with the abandoned one's and the stage
-- could never be re-admitted.
CREATE TABLE receipts (
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  act TEXT NOT NULL CHECK (act IN ('admit', 'claim')),
  operation_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('performed', 'adopted', 'refused')),
  detail TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, episode, act),
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);

CREATE TABLE pool_generations (
  generation INTEGER PRIMARY KEY CHECK (generation >= 1),
  variant TEXT NOT NULL,
  separation_class TEXT NOT NULL,
  document TEXT NOT NULL,
  -- NOT UNIQUE; see the note in SCHEMA.  W71877 review [P2].
  digest TEXT NOT NULL,
  activated_at TEXT NOT NULL
);

CREATE TABLE pool_workers (
  generation INTEGER NOT NULL REFERENCES pool_generations(generation),
  worker_id TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  eligible_kinds TEXT NOT NULL,
  PRIMARY KEY (generation, worker_id),
  UNIQUE (generation, participant),
  UNIQUE (generation, worker_id, lane, participant, canonical_principal)
);

CREATE TABLE stage_allocations (
  assignment_id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  generation INTEGER NOT NULL,
  worker_id TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  preferred_worker_id TEXT,
  selection_outcome TEXT NOT NULL CHECK (selection_outcome IN
    ('initial', 'preferred', 'fallback')),
  allocation_state TEXT NOT NULL CHECK (allocation_state IN
    ('reserved', 'recovery-required', 'released')),
  reserved_at TEXT NOT NULL,
  recovery_required_at TEXT,
  released_at TEXT,
  release_reason TEXT,
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode),
  FOREIGN KEY (generation, worker_id, lane, participant, canonical_principal)
    REFERENCES pool_workers(generation, worker_id, lane, participant,
                            canonical_principal),
  CHECK ((allocation_state = 'reserved' AND recovery_required_at IS NULL
          AND released_at IS NULL AND release_reason IS NULL)
      OR (allocation_state = 'recovery-required'
          AND recovery_required_at IS NOT NULL AND released_at IS NULL
          AND release_reason IS NULL)
      OR (allocation_state = 'released' AND released_at IS NOT NULL
          AND release_reason IS NOT NULL))
);

CREATE UNIQUE INDEX allocations_one_live_per_worker
  ON stage_allocations(worker_id)
  WHERE allocation_state IN ('reserved', 'recovery-required');
CREATE UNIQUE INDEX allocations_one_live_per_principal
  ON stage_allocations(canonical_principal)
  WHERE allocation_state IN ('reserved', 'recovery-required');
CREATE UNIQUE INDEX allocations_one_live_per_stage_episode
  ON stage_allocations(stage_id, episode)
  WHERE allocation_state IN ('reserved', 'recovery-required');

CREATE TABLE integration_capacity_roots (
  -- W161230 slice1. ONE INTEGRATION STAGE ALLOCATION, AND THE ORCHESTRATION
  -- THAT RUNS INSIDE IT. The root does not add capacity: it NAMES the capacity
  -- the scheduler already reserved, so the phases that execute under it are
  -- accounted rather than hidden. A second `stage_allocations` row would have
  -- had to evade the live worker/principal indexes, which is exactly what this
  -- relation exists to avoid.
  orchestration_id TEXT PRIMARY KEY,
  -- THE ACTUAL ALLOCATION, by foreign key. A root for an allocation nobody
  -- reserved is not a root.
  root_assignment_id TEXT NOT NULL UNIQUE
    REFERENCES stage_allocations(assignment_id),
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  job_id TEXT NOT NULL,
  authority_uuid TEXT NOT NULL,
  work_id TEXT NOT NULL,
  -- THE POOL GENERATION THE ALLOCATION WAS MADE UNDER, and never the
  -- Authority's assignment generation: they are different axes and are never
  -- compared with one another.
  pool_generation INTEGER NOT NULL CHECK (pool_generation >= 1),
  worker_id TEXT NOT NULL,
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('open', 'ending', 'ended')),
  registered_operation_id TEXT NOT NULL,
  ending_operation_id TEXT,
  registered_at TEXT NOT NULL,
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);
CREATE TABLE integration_capacity_members (
  -- ONE EXECUTION, and its own real identity. `execution_attempt_id` is the
  -- attempt a Worker Manager claim actually produced; a membership never
  -- invents one, and a planned membership carries no claimed assignment
  -- because no claim has happened yet.
  execution_attempt_id TEXT PRIMARY KEY,
  orchestration_id TEXT NOT NULL
    REFERENCES integration_capacity_roots(orchestration_id),
  phase TEXT NOT NULL CHECK (phase IN ('prepare', 'apply')),
  execution_work_id TEXT NOT NULL,
  execution_offer_id TEXT NOT NULL,
  participant TEXT NOT NULL,
  task_digest TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  -- WHAT THE APPLY IMPORTS, BY DIGEST. An apply exists to import content a
  -- preparation collected, so it names that content here and its admission
  -- compares this against what the preparation's own ending recorded. A
  -- preparation imports nothing and carries none -- which is the CHECK below,
  -- not a convention a writer is trusted to follow.
  parent_content_digest TEXT,
  -- THE CLAIMED ASSIGNMENT, FIXED ONCE, from the actual successful claim. Its
  -- absence is legal only while the membership is planned.
  assignment TEXT,
  -- `cancelled` IS NOT `ended`. An execution that ran and finished is ended
  -- and carries its outcome; a plan that never ran at all is cancelled and
  -- carries none, because there is nothing it did. Collapsing the two would
  -- make "this failed" and "this never happened" one word.
  state TEXT NOT NULL
    CHECK (state IN ('planned', 'admitted', 'recovery-required', 'ended',
                     'cancelled')),
  -- WHAT THE EXECUTION DID, retained SEPARATELY from whether it is excluded.
  -- A failure that is over and a success that is over are both ended; only the
  -- outcome says which, and neither says anything about the target.
  outcome TEXT CHECK (outcome IS NULL OR outcome IN ('succeeded', 'failed')),
  -- HOW THIS MEMBER WAS PROVED EXCLUDED, BY NAME. Review 2026-09-13T17:38:55Z:
  -- the ending took free TEXT, so "I stopped it" excluded capacity. The named
  -- proof is resolved from the Worker Manager's own readers at the ending and
  -- `ending_evidence` retains the exact document it answered with.
  exclusion TEXT CHECK (exclusion IS NULL OR exclusion IN
                        ('fenced-before-start', 'runtime-destroyed')),
  -- WHAT A PREPARATION COLLECTED, RESOLVED FROM THE WORKER MANAGER'S OWN
  -- FROZEN OUTPUT by its ending and read by the apply's admission. The digest
  -- is the manifest's; the report beside it retains the whole answer -- result
  -- id, disposition and freeze operation -- so a later reader re-derives the
  -- judgment instead of trusting a bare digest. NULL for an apply and for
  -- anything that did not succeed.
  collected_digest TEXT,
  collected_report TEXT,
  -- WHY THIS MEMBER IS UNCERTAIN. `recovery-required` holds capacity, and the
  -- reason it was entered is not the evidence that ends it.
  recovery_reason TEXT,
  -- THE CANDIDATE THIS APPLY WAS AUTHORIZED TO RUN, retained rather than
  -- merely checked. Review 2026-09-14T00:55:37Z: the owner's answer was
  -- compared and then discarded, so nothing durable said WHICH candidate had
  -- been approved -- and a later reader could not tell an admission over an
  -- approved candidate from one over any other. NULL for a preparation, which
  -- has no candidate and needs no authorization.
  authorized_proposal_id TEXT,
  authorized_result_id TEXT,
  authorized_result_digest TEXT,
  ending_evidence TEXT,
  registered_operation_id TEXT NOT NULL,
  ended_operation_id TEXT,
  UNIQUE (orchestration_id, phase),
  -- THE ASSIGNMENT ARRIVES WITH ADMISSION, so the states that precede or
  -- replace admission have none and the ones that follow it must.
  CHECK ((state IN ('planned', 'cancelled') AND assignment IS NULL)
      OR (state IN ('admitted', 'recovery-required', 'ended')
          AND assignment IS NOT NULL)),
  CHECK ((state = 'ended' AND outcome IS NOT NULL)
      OR (state <> 'ended' AND outcome IS NULL)),
  -- AN ENDING NAMES ITS PROOF, and nothing else may. A cancelled plan was
  -- never excluded from anything because it never ran.
  CHECK ((state = 'ended' AND exclusion IS NOT NULL)
      OR (state <> 'ended' AND exclusion IS NULL)),
  -- AND ONLY AN APPLY BINDS A PARENT. Review 2026-09-13T18:02:07Z: requiring
  -- it at REGISTRATION made a plan predeclare a digest that the preparation
  -- has not produced yet, so the only value a caller could supply was one it
  -- invented. It is written by the APPLY'S ADMISSION from what the
  -- preparation's own ending resolved, which is the only moment it exists.
  CHECK (parent_content_digest IS NULL OR phase = 'apply'),
  CHECK (collected_digest IS NULL OR phase = 'prepare'),
  -- AND ONLY AN APPLY CARRIES AN AUTHORIZED CANDIDATE, all three members or
  -- none: a proposal without its result and digest is not a candidate.
  CHECK ((authorized_proposal_id IS NULL AND authorized_result_id IS NULL
          AND authorized_result_digest IS NULL)
      OR (phase = 'apply' AND authorized_proposal_id IS NOT NULL
          AND authorized_result_id IS NOT NULL
          AND authorized_result_digest IS NOT NULL))
);
CREATE UNIQUE INDEX capacity_one_active_member
  -- SERIAL PHASES, STRUCTURALLY. At most one membership of a root may be live
  -- at a time, so a parent apply and its preparation can never both be running
  -- under one reservation. This is the enforcement point, not a rule stated in
  -- prose and checked by whoever remembers.
  --
  -- THE COMMENT LIVES INSIDE THE STATEMENT: the migration splitter hands whole
  -- statements to `_created_name`, which reads the leading word, so a comment
  -- BEFORE a `CREATE` makes the step look like an unrecognised verb and every
  -- schema-3 store refuses to migrate. Measured, step 13.
  ON integration_capacity_members (orchestration_id)
  WHERE state IN ('admitted', 'recovery-required');
CREATE TABLE worker_affinity (
  development_line TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  worker_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  PRIMARY KEY (development_line, lane)
);

CREATE TABLE deferrals (
  -- W197661: A DEFERRED ACT'S OWN REASON, and deliberately NOT a receipt.
  --
  -- `manager._delegate` performs each owed act. An ordinary non-durable refusal
  -- is an ANSWER rather than a failure -- the worker has not accepted its offer
  -- yet, the ending cannot re-enter, the runtime is still quiescing -- and until
  -- now that answer persisted NOWHERE: `_record` writes only when the Worker
  -- Manager journalled a row, so the reason lived for exactly one tick. A real
  -- deployment then sat at `answering` for the whole of an incident with a
  -- healthy-looking manager and a fresh snapshot, and the only place the reason
  -- existed was a reconcile report nobody had kept.
  --
  -- WHY NOT `receipts`. That table's `act` is closed to ('admit','claim') and its
  -- `state` to ('performed','adopted','refused') -- and `projection` reads ANY
  -- refused receipt as `exceptional`. A deferral is re-enterable and not refused,
  -- so recording one there would turn a recoverable condition into a terminal
  -- one, which is a worse falsehood than the silence it replaces.
  --
  -- ONE ROW PER (STAGE, EPISODE, ACT), updated in place. A deferral repeats on
  -- every tick; a row per occurrence would be an unbounded write driven by a
  -- condition that is not changing. `first_seen_at` is when it started and
  -- `last_seen_at` is how an operator tells "still" from "stale".
  --
  -- AND IT IS DELETED WHEN THE ACT SETTLES. A reason left behind after the act
  -- succeeded would be worse than none at all.
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  act TEXT NOT NULL,
  -- THE EXACT ATTEMPT, which is the half the owner asked for by name: a
  -- deferral an operator cannot attribute to one attempt is a reason without
  -- a subject.
  attempt_id TEXT NOT NULL,
  -- NULLABLE, because not every owed act HAS a canonical operation identity.
  -- `admit` and `claim` are delegated under one this build derives; `conclude`
  -- is the composed ending's own re-entry and has none. Review
  -- 2026-09-18T02-59-56Z: "do not invent an unrelated canonical operation
  -- identity merely to satisfy the new table" -- so absence is recorded as
  -- absence.
  operation_id TEXT,
  category TEXT NOT NULL,
  code TEXT NOT NULL,
  message TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, episode, act),
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);
"""

# version already recorded -> the statements that carry it to the next one.
#
# A MIGRATION RATHER THAN A REFUSAL, and the reason is the store's contents. A
# persisted submission is a pipeline somebody is running; discarding it because
# the next slice added a relation would be this build deciding an operator's
# work is disposable. Every existing stage becomes episode 1 carrying exactly
# the identities its own row already held, so a migrated store's canonical
# operation ids are unchanged and its receipts still reconcile against the
# manager journal rows they already named.
# THE 2 -> 3 STEP IS DELIBERATELY EMPTY DDL. Its whole content is the Authority
# binding, which is a value the OPENER supplies rather than anything derivable
# from the store -- so it is written by `_migrate` inside the same transaction
# that stamps the version, and there is no statement here to write it with.
# An entry that does not exist is a version this build refuses to migrate, so
# the key has to be present even though its text is empty.
MIGRATIONS = {
    # W161230 slice1, CREATE ONLY for the same reason the 4 -> 5 step is:
    # `_schema_three_shape` subtracts what every step after 3 creates, and an
    # ALTER of `stage_allocations` could not be subtracted at all.
    5: """CREATE TABLE integration_capacity_roots (
  -- W161230 slice1. ONE INTEGRATION STAGE ALLOCATION, AND THE ORCHESTRATION
  -- THAT RUNS INSIDE IT. The root does not add capacity: it NAMES the capacity
  -- the scheduler already reserved, so the phases that execute under it are
  -- accounted rather than hidden. A second `stage_allocations` row would have
  -- had to evade the live worker/principal indexes, which is exactly what this
  -- relation exists to avoid.
  orchestration_id TEXT PRIMARY KEY,
  -- THE ACTUAL ALLOCATION, by foreign key. A root for an allocation nobody
  -- reserved is not a root.
  root_assignment_id TEXT NOT NULL UNIQUE
    REFERENCES stage_allocations(assignment_id),
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  job_id TEXT NOT NULL,
  authority_uuid TEXT NOT NULL,
  work_id TEXT NOT NULL,
  -- THE POOL GENERATION THE ALLOCATION WAS MADE UNDER, and never the
  -- Authority's assignment generation: they are different axes and are never
  -- compared with one another.
  pool_generation INTEGER NOT NULL CHECK (pool_generation >= 1),
  worker_id TEXT NOT NULL,
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('open', 'ending', 'ended')),
  registered_operation_id TEXT NOT NULL,
  ending_operation_id TEXT,
  registered_at TEXT NOT NULL,
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);
CREATE TABLE integration_capacity_members (
  -- ONE EXECUTION, and its own real identity. `execution_attempt_id` is the
  -- attempt a Worker Manager claim actually produced; a membership never
  -- invents one, and a planned membership carries no claimed assignment
  -- because no claim has happened yet.
  execution_attempt_id TEXT PRIMARY KEY,
  orchestration_id TEXT NOT NULL
    REFERENCES integration_capacity_roots(orchestration_id),
  phase TEXT NOT NULL CHECK (phase IN ('prepare', 'apply')),
  execution_work_id TEXT NOT NULL,
  execution_offer_id TEXT NOT NULL,
  participant TEXT NOT NULL,
  task_digest TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  -- WHAT THE APPLY IMPORTS, BY DIGEST. An apply exists to import content a
  -- preparation collected, so it names that content here and its admission
  -- compares this against what the preparation's own ending recorded. A
  -- preparation imports nothing and carries none -- which is the CHECK below,
  -- not a convention a writer is trusted to follow.
  parent_content_digest TEXT,
  -- THE CLAIMED ASSIGNMENT, FIXED ONCE, from the actual successful claim. Its
  -- absence is legal only while the membership is planned.
  assignment TEXT,
  -- `cancelled` IS NOT `ended`. An execution that ran and finished is ended
  -- and carries its outcome; a plan that never ran at all is cancelled and
  -- carries none, because there is nothing it did. Collapsing the two would
  -- make "this failed" and "this never happened" one word.
  state TEXT NOT NULL
    CHECK (state IN ('planned', 'admitted', 'recovery-required', 'ended',
                     'cancelled')),
  -- WHAT THE EXECUTION DID, retained SEPARATELY from whether it is excluded.
  -- A failure that is over and a success that is over are both ended; only the
  -- outcome says which, and neither says anything about the target.
  outcome TEXT CHECK (outcome IS NULL OR outcome IN ('succeeded', 'failed')),
  -- HOW THIS MEMBER WAS PROVED EXCLUDED, BY NAME. Review 2026-09-13T17:38:55Z:
  -- the ending took free TEXT, so "I stopped it" excluded capacity. The named
  -- proof is resolved from the Worker Manager's own readers at the ending and
  -- `ending_evidence` retains the exact document it answered with.
  exclusion TEXT CHECK (exclusion IS NULL OR exclusion IN
                        ('fenced-before-start', 'runtime-destroyed')),
  -- WHAT A PREPARATION COLLECTED, RESOLVED FROM THE WORKER MANAGER'S OWN
  -- FROZEN OUTPUT by its ending and read by the apply's admission. The digest
  -- is the manifest's; the report beside it retains the whole answer -- result
  -- id, disposition and freeze operation -- so a later reader re-derives the
  -- judgment instead of trusting a bare digest. NULL for an apply and for
  -- anything that did not succeed.
  collected_digest TEXT,
  collected_report TEXT,
  -- WHY THIS MEMBER IS UNCERTAIN. `recovery-required` holds capacity, and the
  -- reason it was entered is not the evidence that ends it.
  recovery_reason TEXT,
  -- THE CANDIDATE THIS APPLY WAS AUTHORIZED TO RUN, retained rather than
  -- merely checked. Review 2026-09-14T00:55:37Z: the owner's answer was
  -- compared and then discarded, so nothing durable said WHICH candidate had
  -- been approved -- and a later reader could not tell an admission over an
  -- approved candidate from one over any other. NULL for a preparation, which
  -- has no candidate and needs no authorization.
  authorized_proposal_id TEXT,
  authorized_result_id TEXT,
  authorized_result_digest TEXT,
  ending_evidence TEXT,
  registered_operation_id TEXT NOT NULL,
  ended_operation_id TEXT,
  UNIQUE (orchestration_id, phase),
  -- THE ASSIGNMENT ARRIVES WITH ADMISSION, so the states that precede or
  -- replace admission have none and the ones that follow it must.
  CHECK ((state IN ('planned', 'cancelled') AND assignment IS NULL)
      OR (state IN ('admitted', 'recovery-required', 'ended')
          AND assignment IS NOT NULL)),
  CHECK ((state = 'ended' AND outcome IS NOT NULL)
      OR (state <> 'ended' AND outcome IS NULL)),
  -- AN ENDING NAMES ITS PROOF, and nothing else may. A cancelled plan was
  -- never excluded from anything because it never ran.
  CHECK ((state = 'ended' AND exclusion IS NOT NULL)
      OR (state <> 'ended' AND exclusion IS NULL)),
  -- AND ONLY AN APPLY BINDS A PARENT. Review 2026-09-13T18:02:07Z: requiring
  -- it at REGISTRATION made a plan predeclare a digest that the preparation
  -- has not produced yet, so the only value a caller could supply was one it
  -- invented. It is written by the APPLY'S ADMISSION from what the
  -- preparation's own ending resolved, which is the only moment it exists.
  CHECK (parent_content_digest IS NULL OR phase = 'apply'),
  CHECK (collected_digest IS NULL OR phase = 'prepare'),
  -- AND ONLY AN APPLY CARRIES AN AUTHORIZED CANDIDATE, all three members or
  -- none: a proposal without its result and digest is not a candidate.
  CHECK ((authorized_proposal_id IS NULL AND authorized_result_id IS NULL
          AND authorized_result_digest IS NULL)
      OR (phase = 'apply' AND authorized_proposal_id IS NOT NULL
          AND authorized_result_id IS NOT NULL
          AND authorized_result_digest IS NOT NULL))
);
CREATE UNIQUE INDEX capacity_one_active_member
  -- SERIAL PHASES, STRUCTURALLY. At most one membership of a root may be live
  -- at a time, so a parent apply and its preparation can never both be running
  -- under one reservation. This is the enforcement point, not a rule stated in
  -- prose and checked by whoever remembers.
  --
  -- THE COMMENT LIVES INSIDE THE STATEMENT: the migration splitter hands whole
  -- statements to `_created_name`, which reads the leading word, so a comment
  -- BEFORE a `CREATE` makes the step look like an unrecognised verb and every
  -- schema-3 store refuses to migrate. Measured, step 13.
  ON integration_capacity_members (orchestration_id)
  WHERE state IN ('admitted', 'recovery-required');
""",
    # W156162. CREATE ONLY, which `_created_name` requires of every step the
    # schema-3 expectation subtracts, and which is why the limits are a table
    # rather than two columns on `jobs`. An existing store's Jobs configured
    # nothing, so an empty table is exactly their meaning -- no backfill, and
    # no rewriting of the submission journals that recorded them.
    4: """
CREATE TABLE job_execution_limits (
  job_id TEXT PRIMARY KEY REFERENCES jobs(job_id),
  requested TEXT NOT NULL,
  compatibility_generation INTEGER NOT NULL CHECK (compatibility_generation >= 0)
);
""",
    3: """
CREATE TABLE pool_generations (
  generation INTEGER PRIMARY KEY CHECK (generation >= 1),
  variant TEXT NOT NULL,
  separation_class TEXT NOT NULL,
  document TEXT NOT NULL,
  -- NOT UNIQUE, and W71877's review [P2] is why.  The digest identifies the
  -- immutable CONFIGURATION, not the activation act: an operator returning
  -- deliberately to a historical variant is choosing that configuration for
  -- NEW work, which is a new generation.  A unique digest made the second
  -- activation answer the first generation while a later one stayed active,
  -- which is the opposite of what the ruling asks for.  Exact retry is still
  -- effectively-once, through the journalled operation identity rather than
  -- through a column.
  digest TEXT NOT NULL,
  activated_at TEXT NOT NULL
);
CREATE TABLE pool_workers (
  generation INTEGER NOT NULL REFERENCES pool_generations(generation),
  worker_id TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  eligible_kinds TEXT NOT NULL,
  PRIMARY KEY (generation, worker_id),
  UNIQUE (generation, participant),
  UNIQUE (generation, worker_id, lane, participant, canonical_principal)
);
CREATE TABLE stage_allocations (
  assignment_id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  generation INTEGER NOT NULL,
  worker_id TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  participant TEXT NOT NULL,
  canonical_principal TEXT NOT NULL,
  preferred_worker_id TEXT,
  selection_outcome TEXT NOT NULL CHECK (selection_outcome IN
    ('initial', 'preferred', 'fallback')),
  allocation_state TEXT NOT NULL CHECK (allocation_state IN
    ('reserved', 'recovery-required', 'released')),
  reserved_at TEXT NOT NULL,
  recovery_required_at TEXT,
  released_at TEXT,
  release_reason TEXT,
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode),
  FOREIGN KEY (generation, worker_id, lane, participant, canonical_principal)
    REFERENCES pool_workers(generation, worker_id, lane, participant,
                            canonical_principal),
  CHECK ((allocation_state = 'reserved' AND recovery_required_at IS NULL
          AND released_at IS NULL AND release_reason IS NULL)
      OR (allocation_state = 'recovery-required'
          AND recovery_required_at IS NOT NULL AND released_at IS NULL
          AND release_reason IS NULL)
      OR (allocation_state = 'released' AND released_at IS NOT NULL
          AND release_reason IS NOT NULL))
);
CREATE UNIQUE INDEX allocations_one_live_per_worker
  ON stage_allocations(worker_id)
  WHERE allocation_state IN ('reserved', 'recovery-required');
CREATE UNIQUE INDEX allocations_one_live_per_principal
  ON stage_allocations(canonical_principal)
  WHERE allocation_state IN ('reserved', 'recovery-required');
CREATE UNIQUE INDEX allocations_one_live_per_stage_episode
  ON stage_allocations(stage_id, episode)
  WHERE allocation_state IN ('reserved', 'recovery-required');
CREATE TABLE worker_affinity (
  development_line TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  worker_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  PRIMARY KEY (development_line, lane)
);
""",
    2: "",
    1: """
CREATE TABLE episodes (
  stage_id TEXT NOT NULL REFERENCES stages(stage_id),
  episode INTEGER NOT NULL CHECK (episode >= 1),
  offer_id TEXT NOT NULL UNIQUE,
  attempt_id TEXT NOT NULL UNIQUE,
  opened_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  ended_state TEXT,
  ended_revision INTEGER,
  ended_at TEXT,
  PRIMARY KEY (stage_id, episode),
  CHECK ((ended_state IS NULL AND ended_revision IS NULL
          AND ended_at IS NULL)
      OR (ended_state IS NOT NULL AND ended_revision IS NOT NULL
          AND ended_at IS NOT NULL))
);

CREATE UNIQUE INDEX episodes_one_live_per_stage
    ON episodes (stage_id) WHERE ended_state IS NULL;

-- The identities the stage row already held, and the submission instant this
-- store already recorded. Nothing is invented: a migrated episode 1 asserts
-- exactly what schema 1 asserted about the same stage.
INSERT INTO episodes (stage_id, episode, offer_id, attempt_id, opened_at,
                      incarnation)
SELECT stages.stage_id, 1, stages.offer_id, stages.attempt_id,
       submissions.recorded_at, submissions.incarnation
  FROM stages
  JOIN jobs ON jobs.job_id = stages.job_id
  JOIN submissions ON submissions.submission_id = jobs.submission_id;

CREATE TABLE stages_2 (
  stage_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(job_id),
  ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL,
  work_id TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  depends_on TEXT NOT NULL,
  UNIQUE (job_id, kind)
);

INSERT INTO stages_2 (stage_id, job_id, ordinal, kind, work_id, profile_name,
                      profile_digest, depends_on)
SELECT stage_id, job_id, ordinal, kind, work_id, profile_name, profile_digest,
       depends_on FROM stages;

CREATE TABLE receipts_2 (
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  act TEXT NOT NULL CHECK (act IN ('admit', 'claim')),
  operation_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('performed', 'adopted', 'refused')),
  detail TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, episode, act),
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);

INSERT INTO receipts_2 (stage_id, episode, act, operation_id, state, detail,
                        recorded_at, incarnation)
SELECT stage_id, 1, act, operation_id, state, detail, recorded_at, incarnation
  FROM receipts;

DROP TABLE receipts;

DROP TABLE stages;

ALTER TABLE stages_2 RENAME TO stages;

ALTER TABLE receipts_2 RENAME TO receipts;
""",
    # W197661, CREATE ONLY: a new relation adds nothing to migrate and
    # `_schema_three_shape` subtracts exactly what every step after 3 creates.
    #
    # THE KEY IS THE VERSION THIS STEP RUNS *FROM*. `JobStore._migrate` reads
    # `MIGRATIONS[at]` and then increments, so a step to schema 7 is keyed 6.
    # A first cut of this keyed it 7 and left a store at 6 with no step to
    # take -- an infinite loop in the migration driver rather than a refusal.
    6: """
CREATE TABLE deferrals (
  -- W197661: A DEFERRED ACT'S OWN REASON, and deliberately NOT a receipt.
  --
  -- `manager._delegate` performs each owed act. An ordinary non-durable refusal
  -- is an ANSWER rather than a failure -- the worker has not accepted its offer
  -- yet, the ending cannot re-enter, the runtime is still quiescing -- and until
  -- now that answer persisted NOWHERE: `_record` writes only when the Worker
  -- Manager journalled a row, so the reason lived for exactly one tick. A real
  -- deployment then sat at `answering` for the whole of an incident with a
  -- healthy-looking manager and a fresh snapshot, and the only place the reason
  -- existed was a reconcile report nobody had kept.
  --
  -- WHY NOT `receipts`. That table's `act` is closed to ('admit','claim') and its
  -- `state` to ('performed','adopted','refused') -- and `projection` reads ANY
  -- refused receipt as `exceptional`. A deferral is re-enterable and not refused,
  -- so recording one there would turn a recoverable condition into a terminal
  -- one, which is a worse falsehood than the silence it replaces.
  --
  -- ONE ROW PER (STAGE, EPISODE, ACT), updated in place. A deferral repeats on
  -- every tick; a row per occurrence would be an unbounded write driven by a
  -- condition that is not changing. `first_seen_at` is when it started and
  -- `last_seen_at` is how an operator tells "still" from "stale".
  --
  -- AND IT IS DELETED WHEN THE ACT SETTLES. A reason left behind after the act
  -- succeeded would be worse than none at all.
  stage_id TEXT NOT NULL,
  episode INTEGER NOT NULL,
  act TEXT NOT NULL,
  -- THE EXACT ATTEMPT, which is the half the owner asked for by name: a
  -- deferral an operator cannot attribute to one attempt is a reason without
  -- a subject.
  attempt_id TEXT NOT NULL,
  -- NULLABLE, because not every owed act HAS a canonical operation identity.
  -- `admit` and `claim` are delegated under one this build derives; `conclude`
  -- is the composed ending's own re-entry and has none. Review
  -- 2026-09-18T02-59-56Z: "do not invent an unrelated canonical operation
  -- identity merely to satisfy the new table" -- so absence is recorded as
  -- absence.
  operation_id TEXT,
  category TEXT NOT NULL,
  code TEXT NOT NULL,
  message TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, episode, act),
  FOREIGN KEY (stage_id, episode) REFERENCES episodes(stage_id, episode)
);
""",
}

OPERATION_COLUMNS = {
    "operation_id": Column("identity"),
    "kind": Column("text"),
    "signature": Column("text"),
    "state": Column("text", allowed=OPERATION_STATES),
    "result": Column("json", nullable=True),
    "refusal": Column("refusal", nullable=True),
    "settled_at": Column("instant"),
}

SUBMISSION_COLUMNS = {
    "submission_id": Column("identity"),
    "signature": Column("text"),
    "document": Column("json"),
    "incarnation": Column("text"),
    "recorded_at": Column("instant"),
}

JOB_EXECUTION_LIMIT_COLUMNS = {
    "job_id": Column("identity"),
    "requested": Column("json"),
    "compatibility_generation": Column("count"),
}

JOB_COLUMNS = {
    "job_id": Column("identity"),
    "submission_id": Column("identity"),
    "ordinal": Column("count"),
    "input_digest": Column("text"),
    "policy_digest": Column("text"),
    "test_scope": Column("json"),
    "terminal_policy": Column("text"),
}

STAGE_COLUMNS = {
    "stage_id": Column("identity"),
    "job_id": Column("identity"),
    "ordinal": Column("count"),
    "kind": Column("text"),
    "work_id": Column("text"),
    "profile_name": Column("text"),
    "profile_digest": Column("text"),
    "depends_on": Column("json"),
}

EPISODE_COLUMNS = {
    "stage_id": Column("identity"),
    "episode": Column("count"),
    "offer_id": Column("identity"),
    "attempt_id": Column("identity"),
    "opened_at": Column("instant"),
    "incarnation": Column("text"),
    # Nullable HERE because the CHECK above decides that the three travel
    # together; what each one IS is this table's to say.
    "ended_state": Column("text", nullable=True),
    "ended_revision": Column("count", nullable=True),
    "ended_at": Column("instant", nullable=True),
}

RECEIPT_COLUMNS = {
    "stage_id": Column("identity"),
    "episode": Column("count"),
    "act": Column("text"),
    "operation_id": Column("identity"),
    "state": Column("text", allowed=RECEIPT_STATES),
    "detail": Column("json"),
    "recorded_at": Column("instant"),
    "incarnation": Column("text"),
}

DEFERRAL_COLUMNS = {
    "stage_id": Column("identity"), "episode": Column("count"),
    "act": Column("text"), "attempt_id": Column("identity"),
    "operation_id": Column("identity", nullable=True),
    "category": Column("text"),
    "code": Column("text"), "message": Column("text"),
    "first_seen_at": Column("instant"), "last_seen_at": Column("instant"),
    "incarnation": Column("text"),
}

GENERATION_COLUMNS = {
    "generation": Column("count"), "variant": Column("text"),
    "separation_class": Column("text"), "document": Column("json"),
    "digest": Column("text"), "activated_at": Column("instant"),
}

POOL_WORKER_COLUMNS = {
    "generation": Column("count"), "worker_id": Column("identity"),
    "lane": Column("text"), "participant": Column("text"),
    "canonical_principal": Column("text"), "profile_name": Column("text"),
    "profile_digest": Column("text"), "eligible_kinds": Column("json"),
}

ALLOCATION_COLUMNS = {
    "assignment_id": Column("identity"), "stage_id": Column("identity"),
    "episode": Column("count"), "generation": Column("count"),
    "worker_id": Column("identity"), "lane": Column("text"),
    "participant": Column("text"), "canonical_principal": Column("text"),
    "preferred_worker_id": Column("identity", nullable=True),
    "selection_outcome": Column("text"), "allocation_state": Column("text"),
    "reserved_at": Column("instant"),
    "recovery_required_at": Column("instant", nullable=True),
    "released_at": Column("instant", nullable=True),
    "release_reason": Column("text", nullable=True),
}

AFFINITY_COLUMNS = {
    "development_line": Column("text"), "lane": Column("text"),
    "worker_id": Column("identity"), "recorded_at": Column("instant"),
}
