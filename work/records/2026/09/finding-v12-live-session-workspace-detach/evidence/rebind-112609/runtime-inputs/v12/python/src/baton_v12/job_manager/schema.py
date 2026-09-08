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
           "GENERATION_COLUMNS", "MIGRATIONS", "POOL_WORKER_COLUMNS", "SCHEMA", "SCHEMA_VERSION",
           "check_authority",
           "STORE_KIND", "TABLES", "JOB_COLUMNS", "OPERATION_COLUMNS",
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
SCHEMA_VERSION = 4

TABLES = ("meta", "operations", "submissions", "jobs", "stages", "episodes",
          "receipts", "pool_generations", "pool_workers",
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

CREATE TABLE worker_affinity (
  development_line TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('implementation', 'review')),
  worker_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  PRIMARY KEY (development_line, lane)
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
