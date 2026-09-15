"""Recording one submitted intent, atomically and effectively once.

W71875. THE WHOLE SUBMISSION IS ONE ACT. A submission that recorded two of its
three Jobs and then failed would leave a pipeline nobody described, so the
Jobs, their stages and the submission row are written inside one transaction
and journalled under one operation identity.

IDEMPOTENCE AND CONFLICT ARE THE SAME MECHANISM, seen from two sides. The
operation identity is derived from the submission id, and the signature is the
canonical text of the NORMALIZED document -- so replaying the same intent
returns the first outcome, and reusing a submission id for a different intent
collides at the journal instead of rewriting durable rows. A Job id already
recorded under ANOTHER submission is refused durably, because the conflict is
a fact about the store rather than a transient condition a retry could clear.
"""

import json

from ..contracts import ContractRefusal
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from . import documents, episodes, execution_limits, schema
from .store import job_signature

__all__ = ["job_of", "job_rows", "jobs_of", "stage_rows", "stages_of",
           "submission_of", "submission_rows", "submit"]

_KIND = "submission.record"


def operation_id(submission_id):
    """The one derived identity a submission's record is journalled under.

    Derived rather than supplied, so an operator resubmitting the same
    document cannot make it a new act by forgetting what the last one was
    called.
    """
    return f"{_KIND}:{submission_id}"


def submit(store, document):
    """Record one submission, or replay the outcome of recording it.

    Answers a `submission.recorded` document naming the stage ids this
    submission created, which is what a caller needs to ask for status
    afterwards.
    """
    owned = documents.owned_submission(document)
    submission_id = owned["submission_id"]
    # THE NORMALIZED DOCUMENT IS THE OPERANDS, not a member wrapping it. The
    # canonical serialization is bounded by depth, and one decorative level of
    # nesting is the difference between a submission this build can sign and
    # one it refuses for a reason that has nothing to do with the operator.
    signature = job_signature(_KIND, owned)

    def act(connection):
        _unclaimed(connection, submission_id, owned)
        recorded_at = store._now()
        connection.execute(
            "INSERT INTO submissions (submission_id, signature, document, "
            "incarnation, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (submission_id, signature,
             json.dumps(owned, sort_keys=True, ensure_ascii=False),
             store.incarnation, recorded_at))
        stages = []
        for ordinal, job in enumerate(owned["jobs"]):
            _job(connection, submission_id, ordinal, job)
            for position, stage in enumerate(job["stages"]):
                stages.append(_stage(connection, store, job["job_id"],
                                     position, stage, recorded_at))
        return documents.submission_recorded(
            submission_id=submission_id, signature=signature,
            jobs=[job["job_id"] for job in owned["jobs"]], stages=stages,
            recorded_at=recorded_at)

    return store.transact(operation_id(submission_id), _KIND, signature, act)


def _unclaimed(connection, submission_id, owned):
    """Refuse a Job identity another submission already holds, BEFORE writing.

    THE ORDER IS WHAT KEEPS THE SUBMISSION ATOMIC. A durable refusal is itself
    a committed outcome, so `transact` keeps the writes that preceded it --
    which is right for an act whose partial effect IS the outcome and exactly
    wrong for this one: a submission that recorded its first Job and refused
    its second would leave half a pipeline behind a sealed refusal. So the
    whole conflict is decided in one read before the first insert, and the
    refusal it raises has nothing to keep.

    DURABLE, because it is not a race a caller can retry out of. Two intents
    claim one identity and the first one recorded is the one the pipeline is
    running, so the resubmission is told the same thing every time rather than
    something new once the store has moved on.

    The read decides INSIDE the write lock `transact` already holds, so no
    concurrent submission can insert between this check and the inserts below.
    """
    wanted = [job["job_id"] for job in owned["jobs"]]
    taken = sorted(
        row[0] for row in connection.execute(
            "SELECT job_id FROM jobs WHERE submission_id != ? AND job_id IN "
            "(" + ", ".join("?" * len(wanted)) + ")",
            (submission_id,) + tuple(wanted)))
    if taken:
        raise ContractRefusal(
            "refused", "precondition",
            f"{sample_of(taken)} is already recorded by another submission; "
            f"one Job identity names one pipeline, and a second submission "
            f"reusing it would silently take over the first one's stages",
            durable=True)


def _job(connection, submission_id, ordinal, job):
    # NO LOCAL CONSTRAINT HANDLER. `_unclaimed` decided the one conflict this
    # table can have, inside the same lock, so an integrity error reaching
    # here would be a defect in that decision rather than a caller's mistake
    # -- and `transact` rolls a fault back whole, which is what a defect
    # deserves and what a durable refusal would not do.
    connection.execute(
        "INSERT INTO jobs (job_id, submission_id, ordinal, input_digest, "
        "policy_digest, test_scope, terminal_policy) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job["job_id"], submission_id, ordinal, job["input_digest"],
         job["policy_digest"],
         json.dumps(job["test_scope"], ensure_ascii=False),
         job["terminal_policy"]))
    # W156162: ITS REQUESTED CEILINGS AND THE GENERATION IT IS ADMITTED UNDER.
    #
    # EVERY Job gets a row, including one that configured nothing, and review
    # 2026-09-13T01:13:49Z R1 is why: the preserved DEFAULTS are as much a part
    # of a Job's admitted configuration as an override is. A Job with no row
    # would have nothing pinning its 3600, and a later default change would
    # reinterpret it -- which is the exact defect the probe demonstrated.
    requested = job.get(documents.JOB_LIMIT_MEMBER) or {}
    connection.execute(
        "INSERT INTO job_execution_limits (job_id, requested, "
        "compatibility_generation) VALUES (?, ?, ?)",
        (job["job_id"],
         json.dumps(requested, sort_keys=True, ensure_ascii=False),
         execution_limits.CURRENT_GENERATION))


def _stage(connection, store, job_id, ordinal, stage, recorded_at):
    """One submitted stage, and the first episode that will try to admit it.

    THE STAGE AND ITS FIRST EPISODE ARE ONE ACT. W73629 moved the offer and
    attempt identities onto the episode, because a stage can outlive the offer
    that was trying to admit it -- but a stage with no episode at all would be
    one nothing could ever admit, so the first one is opened here rather than
    waiting for a sweep to notice it is missing.

    New identities are DERIVED once in `open_first`, then stored on the
    episode. Schema migration separately preserves the plain identities an
    old store already used; new stores use bounded worker-contract identities
    from their first episode onward.
    """
    stage_id = documents.stage_id(job_id, stage["kind"])
    connection.execute(
        "INSERT INTO stages (stage_id, job_id, ordinal, kind, work_id, "
        "profile_name, profile_digest, depends_on) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (stage_id, job_id, ordinal, stage["kind"], stage["work_id"],
         stage["profile_name"], stage["profile_digest"],
         json.dumps(stage["depends_on"], sort_keys=True, ensure_ascii=False)))
    episodes.open_first(connection, store, stage_id, recorded_at)
    return stage_id


# -- the owned reads ---------------------------------------------------------
#
# One crossing per table. The store is a receiving trust domain like any
# other: this process did not write the bytes it is reading, and a durable
# value that no longer round-trips is exactly the case a control store exists
# to survive.

def submission_rows(store):
    return [boundaries.row(record, "a persisted submission",
                           schema.SUBMISSION_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM submissions ORDER BY recorded_at, "
                "submission_id").fetchall()]


def submission_of(store, submission_id):
    boundaries.identity(submission_id, "a submission id")
    found = store._connection.execute(
        "SELECT * FROM submissions WHERE submission_id = ?",
        (submission_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted submission",
                          schema.SUBMISSION_COLUMNS)


def job_rows(store):
    return [boundaries.row(record, "a persisted Job", schema.JOB_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM jobs ORDER BY submission_id, ordinal"
            ).fetchall()]


def execution_limits_of(store, job_id):
    """One Job's admitted execution configuration: what it asked for, and the
    frozen compatibility generation its preserved defaults come from.

    W156162. The public immutable reader: a Job's own intent, owned on the way
    out of the store exactly as it was owned on the way in, with absence as an
    ordinary answer rather than a refusal. Resolution to effective per-boundary
    seconds belongs to `execution_limits.resolved`, which this deliberately
    does not do -- what a Job asked for and what a boundary gets are two facts,
    and a reader that conflated them could not report a preserved default as
    one.
    """
    boundaries.identity(job_id, "a Job id")
    found = store._connection.execute(
        "SELECT * FROM job_execution_limits WHERE job_id = ?",
        (job_id,)).fetchone()
    if found is None:
        # A JOB ADMITTED BEFORE THIS FEATURE. It configured nothing and ran
        # under the four numbers generation 0 freezes, and saying so is what
        # keeps it meaning what it meant rather than inheriting a later default.
        return {"requested": None,
                "compatibility_generation":
                    execution_limits.LEGACY_GENERATION}
    row = boundaries.row(found, "a persisted Job execution limit",
                         schema.JOB_EXECUTION_LIMIT_COLUMNS)
    held = row["requested"]
    return {"requested": execution_limits.requested_from_row(
                held if isinstance(held, str)
                else json.dumps(held, sort_keys=True, ensure_ascii=False)),
            "compatibility_generation": execution_limits.owned_generation(
                row["compatibility_generation"])}


def job_execution_context(store, job_id, *, attempt_id,
                          runtime_input_digest, runtime_policy_digest):
    """The launch carrier's `job_execution`, composed by the JOB'S OWN OWNER.

    W156162 PLAN item 3: "resolve through the immutable public Job reader at
    launch preparation". This is that reader. The Worker Manager's launch
    carrier states what a container is running; deciding WHICH configuration
    that is belongs here, where the Job's admitted settings and the generation
    it was admitted under are held -- and a Worker Manager composing it from
    parts would be a second party resolving a Job's configuration.

    THE JOB'S IDENTITIES AND THE RUNTIME'S ARE BOTH STATED. A review or a
    derived judgment legitimately runs over a frozen input that is not the
    Job's original one, so the runtime's actual input and policy identities are
    the caller's to supply and are carried beside the Job's rather than
    compared with them. What this owner will not do is invent either.

    IT READS AND WRITES NOTHING ELSE. No store mutation, no resolution stored:
    the effective values are derived from the Job's own settings under its own
    frozen generation every time, which is what makes a later default change
    unable to reinterpret it.
    """
    held = execution_limits_of(store, job_id)
    return {"job_id": boundaries.identity(job_id, "a Job id"),
            "attempt_id": boundaries.identity(attempt_id,
                                              "a runtime attempt id"),
            "job_input_digest": job_of(store, job_id)["input_digest"],
            "job_policy_digest": job_of(store, job_id)["policy_digest"],
            "runtime_input_digest": boundaries.text(
                runtime_input_digest, "a runtime's input digest"),
            "runtime_policy_digest": boundaries.text(
                runtime_policy_digest, "a runtime's policy digest"),
            "execution_limits": execution_limits.resolved(
                held["requested"], held["compatibility_generation"]),
            "execution_limits_digest": _sealed(execution_limits.resolved(
                held["requested"], held["compatibility_generation"]))}


def boundary_seconds(store, job_id, boundary):
    """One Job's effective ceiling at ONE boundary, from its own owner.

    W156162. Not every consumer of a Job's ceilings is composing a launch: the
    host-side reconciled owners run the deployment's required test in THIS
    process, so there is no container, no delivery and no document -- and
    `job_execution_context` would oblige a caller with none of those to invent
    an attempt id and two runtime digests it has no fact for.

    WHAT IT WILL NOT DO IS LET A CALLER NAME A BOUNDARY NOBODY OWNS. The
    boundary set is this owner's, so an unknown one is a refusal here rather
    than a `KeyError` in whichever assembly asked -- and, like every other
    reader on this path, the answer is resolved through the generation the Job
    was ADMITTED under rather than today's defaults.
    """
    if boundary not in execution_limits.BOUNDARIES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(boundary)} is not an execution boundary this build "
            f"owns; a ceiling can only be asked for where one is defined")
    # AND THE JOB MUST EXIST BEFORE ITS CONFIGURATION IS RESOLVED. Review
    # 2026-09-13T03:27:43Z [P2]: `execution_limits_of`'s missing-row answer is a
    # COMPATIBILITY answer for a Job admitted before this table existed, and it
    # cannot tell that apart from a Job nobody ever submitted -- so a misspelled
    # or foreign id came back with the preserved defaults and a host path ran
    # under ceilings belonging to nothing. `job_execution_context` already asks
    # `job_of`; this reader did not.
    #
    # THE COMPATIBILITY ANSWER IS UNTOUCHED. A Job this store HOLDS with no
    # limits row still resolves through generation 0 exactly as it did; what is
    # refused is a name the store does not hold at all.
    job_of(store, job_id)
    held = execution_limits_of(store, job_id)
    return execution_limits.resolved(
        held["requested"],
        held["compatibility_generation"])["boundaries"][boundary]["seconds"]


def _sealed(document):
    """The canonical digest the launch carrier compares against.

    One spelling, written here because the Job owner is what produces the
    document and the carrier is what checks it; two spellings of one digest
    would be two components disagreeing about a seal neither could debug.
    """
    import hashlib

    return "sha256:" + hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False)
        .encode("utf-8")).hexdigest()


def job_of(store, job_id):
    """The one Job a stage row names.

    Stage rows carry the Job id and nothing the Job owns, so every reader that
    needs the immutable input identity, the policy digest or the bounded scope
    comes back here for it. A stage naming a Job this store does not hold is a
    refusal rather than an absence: the two tables are written in one
    transaction, so reaching that state means the rows were changed underneath
    the process rather than that the caller asked for something optional.
    """
    boundaries.identity(job_id, "a Job id")
    found = store._connection.execute(
        "SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if found is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"stage rows name Job {name_value(job_id)} and this store holds "
            f"no such Job")
    return boundaries.row(found, "a persisted Job", schema.JOB_COLUMNS)


def jobs_of(store, submission_id):
    boundaries.identity(submission_id, "a submission id")
    return [boundaries.row(record, "a persisted Job", schema.JOB_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM jobs WHERE submission_id = ? ORDER BY ordinal",
                (submission_id,)).fetchall()]


def stage_rows(store):
    return [boundaries.row(record, "a persisted stage", schema.STAGE_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM stages ORDER BY job_id, ordinal").fetchall()]


def stages_of(store, job_id):
    boundaries.identity(job_id, "a Job id")
    return [boundaries.row(record, "a persisted stage", schema.STAGE_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM stages WHERE job_id = ? ORDER BY ordinal",
                (job_id,)).fetchall()]
