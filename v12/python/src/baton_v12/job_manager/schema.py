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

__all__ = ["SCHEMA", "SCHEMA_VERSION", "STORE_KIND", "TABLES",
           "JOB_COLUMNS", "OPERATION_COLUMNS", "OPERATION_STATES",
           "RECEIPT_COLUMNS", "RECEIPT_STATES", "STAGE_COLUMNS",
           "SUBMISSION_COLUMNS"]

STORE_KIND = "baton.v12.python.job-manager"

# One. There is no earlier shape to guess across, and the store refuses any
# version it does not recognise rather than adopting it.
SCHEMA_VERSION = 1

TABLES = ("meta", "operations", "submissions", "jobs", "stages", "receipts")

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

CREATE TABLE stages (
  stage_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(job_id),
  ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL,
  work_id TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_digest TEXT NOT NULL,
  depends_on TEXT NOT NULL,
  offer_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  UNIQUE (job_id, kind)
);

-- ONE RECEIPT PER (STAGE, ACT), and the primary key is what enforces it. A
-- second row for one act is exactly the repeated act restart reconciliation
-- exists to prevent, so it is refused by the table rather than by a rule
-- somebody remembers to apply.
CREATE TABLE receipts (
  stage_id TEXT NOT NULL REFERENCES stages(stage_id),
  act TEXT NOT NULL CHECK (act IN ('admit', 'claim')),
  operation_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('performed', 'adopted', 'refused')),
  detail TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  incarnation TEXT NOT NULL,
  PRIMARY KEY (stage_id, act)
);
"""

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
    "offer_id": Column("identity"),
    "attempt_id": Column("identity"),
}

RECEIPT_COLUMNS = {
    "stage_id": Column("identity"),
    "act": Column("text"),
    "operation_id": Column("identity"),
    "state": Column("text", allowed=RECEIPT_STATES),
    "detail": Column("json"),
    "recorded_at": Column("instant"),
    "incarnation": Column("text"),
}
