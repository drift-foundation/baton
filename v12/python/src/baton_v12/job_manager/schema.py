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

from ..worker_manager.boundaries import Column

__all__ = ["EPISODE_COLUMNS", "MIGRATIONS", "SCHEMA", "SCHEMA_VERSION",
           "STORE_KIND", "TABLES", "JOB_COLUMNS", "OPERATION_COLUMNS",
           "OPERATION_STATES", "RECEIPT_COLUMNS", "RECEIPT_STATES",
           "STAGE_COLUMNS", "SUBMISSION_COLUMNS"]

STORE_KIND = "baton.v12.python.job-manager"

# Two. W73629 added the stage EPISODE, because one restart can end a stage's
# offer without ending the stage: the manager abandons an offer whose bearer it
# cannot account for, and the stage then needs a fresh offer and a fresh
# attempt while the abandoned one stays auditable. Schema 1 had one derived
# offer and one derived attempt per stage and no room to say that.
SCHEMA_VERSION = 2

TABLES = ("meta", "operations", "submissions", "jobs", "stages", "episodes",
          "receipts")

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
MIGRATIONS = {
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
