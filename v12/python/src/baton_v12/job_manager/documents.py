"""The versioned documents this control plane reads and answers with.

W71875. Two documents cross this leaf's boundary and they travel in opposite
directions: a SUBMISSION arrives from an operator or another program, and a
STATUS document leaves for one. Both carry an explicit schema name with its
version in it, because a control plane that accepts "whatever the last build
wrote" cannot tell an old operator from a wrong one.

WHAT IS OWNED HERE AND WHAT IS NOT. The submission is caller input and is
owned member by member: exact built-in data, a closed member set, closed
vocabularies, resolvable stage-scoped dependencies and no cycle. The status
document is this build's own answer and is assembled through closed
constructors, which fix its SHAPE and say nothing about its members' values --
the same split `worker_manager.boundaries` and `worker_manager.documents` make
one layer down, for the same reason.

THE SUBMISSION IS NOT A PLAN OF SHELL COMMANDS. It names Jobs, their immutable
input identities, the stages each Job owes, the runtime profile each stage
requests, the bounded test-change scope the Work was accepted with, and the
terminal policy. Everything else -- which worker runs it, where its workspace
is, what a reviewer decides, what an integrator imports -- belongs to the other
leaves of W71830 and is deliberately absent rather than stubbed.

THE DOCUMENT, WRITTEN OUT ONCE. Two independent Jobs from one baseline, one of
them with a review stage gated on its own implementation:

    {
      "schema": "baton.v12.job-submission/1",
      "submission_id": "sub-1",
      "jobs": [
        {
          "job_id": "job-a",
          "input_digest": "sha256:...",
          "policy_digest": "sha256:...",
          "test_scope": ["v12/python/tests/job_manager"],
          "terminal_policy": "report-and-hold",
          "stages": [
            {"kind": "implementation", "work_id": "0000000a-W1",
             "profile_name": "reference", "profile_digest": "sha256:...",
             "depends_on": []},
            {"kind": "review", "work_id": "0000000a-W2",
             "profile_name": "reviewer", "profile_digest": "sha256:...",
             "depends_on": [{"job_id": "job-a",
                             "kind": "implementation"}]}
          ]
        },
        {
          "job_id": "job-b",
          "input_digest": "sha256:...",
          "policy_digest": "sha256:...",
          "test_scope": [],
          "terminal_policy": "report-and-hold",
          "stages": [
            {"kind": "implementation", "work_id": "0000000a-W3",
             "profile_name": "reference", "profile_digest": "sha256:...",
             "depends_on": []}
          ]
        }
      ]
    }

Every member is required and no other member is admitted, so a document that
grows a field this build does not name is refused rather than half-read. A
stage is identified by its Job and its kind, which is why one Job carries at
most one stage of each kind and why a dependency names exactly that pair.
"""

from ..contracts import (ContractRefusal, canonical_text,
                         check_relative_path, own)
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries

__all__ = ["ACTS", "CONTRACTS", "DEPENDENCY_MEMBERS", "JOB_MEMBERS",
           "MAX_JOBS", "MAX_STAGES", "STAGE_KINDS", "STAGE_MEMBERS",
           "STAGE_STATES", "STATUS_SCHEMA", "SUBMISSION_MEMBERS",
           "SUBMISSION_SCHEMA", "TERMINAL_POLICIES", "TERMINAL_STAGE_STATES",
           "act", "dependency_gate", "job_status", "owned_submission",
           "read_submission", "receipt", "reconciliation", "stage_id",
           "stage_status", "status", "submission_recorded",
           "submission_signature", "sweep_report"]

SUBMISSION_SCHEMA = "baton.v12.job-submission/1"
STATUS_SCHEMA = "baton.v12.job-status/1"

# The three stages this milestone's vertical slice has. They are a CLOSED
# vocabulary rather than free text because the projection below maps each one
# onto the state an operator reads -- `reviewing` is what a claimed review
# stage is, and a kind nobody named could only be projected as a guess.
STAGE_KINDS = ("implementation", "review", "integration")

# W71830's first-slice ruling, as a vocabulary of exactly one member: a wedged
# or failed Job is REPORTED AND CONTAINED, and this leaf does not discard,
# accept or reassign its output. A second policy is a later decision with a
# later record; an enum of one says the decision was made rather than skipped.
TERMINAL_POLICIES = ("report-and-hold",)

# What a stage may be, in the vocabulary the acceptance bullet names. Every
# one of these is DERIVED at read time from persisted receipts plus canonical
# manager state -- none of them is a column this leaf advances on its own.
STAGE_STATES = ("blocked", "queued", "offered", "claimed", "running",
                "reviewing", "integrating", "changes-requested", "completed",
                "exceptional")

# Where a stage stops being something this control plane owes an act for.
# `changes-requested` is terminal FOR THIS LEAF and not for the pipeline: the
# same-line correction cycle is W71918's, and inventing a second offer here
# would be this leaf building the state machine it was told not to build.
TERMINAL_STAGE_STATES = ("changes-requested", "completed", "exceptional")

# The two acts this leaf derives and delegates. Both are control-plane acts on
# the admission half of a stage; starting a runtime, freezing an output,
# deciding a review and importing a proposal are other leaves' operations and
# are absent here rather than represented by a placeholder.
ACTS = ("admit", "claim")

# Bounds on one submission. A control plane that accepts an unbounded document
# accepts an unbounded amount of durable work from one call.
MAX_JOBS = 64
MAX_STAGES = len(STAGE_KINDS)

SUBMISSION_MEMBERS = ("schema", "submission_id", "jobs")
JOB_MEMBERS = ("job_id", "input_digest", "policy_digest", "test_scope",
               "terminal_policy", "stages")
STAGE_MEMBERS = ("kind", "work_id", "profile_name", "profile_digest",
                 "depends_on")
DEPENDENCY_MEMBERS = ("job_id", "kind")


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def stage_id(job_id, kind):
    """The one spelling of a stage's identity, derived from what names it.

    A stage is one Job's one attempt at one kind, so its identity is those two
    facts and nothing else. Deriving it means a resubmission of the same
    intent addresses the same rows without an operator having to keep an id
    stable by hand -- which is what makes the submission idempotent from the
    caller's side rather than only from the store's.
    """
    return f"{job_id}/{kind}"


def read_submission(payload):
    """Decode submission TEXT and own it.

    The decode is where the trust domain is crossed, so the decode is where
    the owner lives -- `boundaries.adopted`'s rule, applied to a document that
    arrives on a file handle or a pipe instead of out of our own store.
    """
    return owned_submission(boundaries.adopted(payload, "a job submission"))


def owned_submission(document):
    """One submission, proved and returned in this build's own member order.

    THE ORDER IS THE POINT of returning a new document rather than the
    caller's. The submission's canonical text is its durable identity, and two
    spellings of one intent must not be two identities -- so the normalized
    document is what is signed, stored and compared, and a caller that spells
    its members in another order or pretty-prints its JSON resubmits the same
    submission rather than a conflicting one.
    """
    taken = boundaries.document(document, "a job submission",
                                required=SUBMISSION_MEMBERS)
    if taken["schema"] != SUBMISSION_SCHEMA:
        _refuse(f"a job submission is {name_value(SUBMISSION_SCHEMA)}; this is "
                f"{name_value(taken['schema'])}. The version is IN the schema "
                f"name because a control plane that reads an unrecognised "
                f"document as its own turns an old operator into a wrong one")
    submission_id = boundaries.identity(taken["submission_id"],
                                        "a submission id")
    jobs = _sequence(taken["jobs"], "a job submission's jobs", MAX_JOBS)
    owned = [_job(entry) for entry in jobs]
    _unique([one["job_id"] for one in owned], "job id", "a job submission")
    _resolvable(owned)
    return {"schema": SUBMISSION_SCHEMA, "submission_id": submission_id,
            "jobs": owned}


def _sequence(value, what, limit):
    if type(value) is not list or value == []:
        _refuse(f"{what} is a non-empty list; this is {name_value(value)}")
    if len(value) > limit:
        _refuse(f"{what} carries {len(value)} entries and this build admits "
                f"{limit}; an unbounded submission is an unbounded amount of "
                f"durable work from one call")
    return value


def _unique(values, what, where):
    seen = set()
    repeated = set()
    for one in values:
        if one in seen:
            repeated.add(one)
        seen.add(one)
    if repeated:
        repeated = sorted(repeated)
        _refuse(f"{where} names {what} {sample_of(repeated)} more than once; "
                f"one identity naming two things is the conflict this control "
                f"plane refuses rather than resolves")


def _job(entry):
    taken = boundaries.document(entry, "a submitted Job", required=JOB_MEMBERS)
    job_id = boundaries.identity(taken["job_id"], "a Job id")
    input_digest = boundaries.text(taken["input_digest"],
                                   "a Job's input digest")
    policy_digest = boundaries.text(taken["policy_digest"],
                                    "a Job's policy digest")
    if taken["terminal_policy"] not in TERMINAL_POLICIES:
        _refuse(f"a Job's terminal policy is one of "
                f"{', '.join(TERMINAL_POLICIES)}; this is "
                f"{name_value(taken['terminal_policy'])}")
    # THE BOUNDED TEST-CHANGE SCOPE TRAVELS WITH THE JOB. AGENTS.md makes an
    # accepted Work's explicit test scope the case-specific authority a later
    # reviewer and integrator check a proposal against, so a submission that
    # could not carry it would push that authority back into a message thread.
    # This leaf STORES it and enforces nothing with it: what a reviewer and an
    # integrator do with the scope is W71918's and W71878's.
    scope = _paths(taken["test_scope"], job_id)
    stages = _sequence(taken["stages"], f"Job {job_id}'s stages", MAX_STAGES)
    owned = [_stage(job_id, one) for one in stages]
    _unique([one["kind"] for one in owned], "stage kind", f"Job {job_id}")
    return {"job_id": job_id, "input_digest": input_digest,
            "policy_digest": policy_digest, "test_scope": scope,
            "terminal_policy": taken["terminal_policy"], "stages": owned}


def _paths(value, job_id):
    """The scope as a PATH SET, in one spelling each.

    Review [P1]: this owned each entry as text alone, and text alone accepted
    `../outside.py`, `/absolute.py` and `v12//dup.py` unchanged. That is not
    input tolerance here: the scope IS the bounded test-change authority a
    later reviewer and integrator check a proposal against, so an entry that
    climbs out of the repository or names one place twice is an authority
    nobody can evaluate against a changed-path list.

    `check_relative_path` is the contract that already says what a repository
    path is -- absolute, backslash, NUL, and empty, `.` or `..` segments are
    all refused there -- and reaching for it rather than restating it keeps one
    rule for every v12 path. Duplicates are refused on top of it, because two
    spellings of one authority set are two things a reviewer could be reading.
    """
    if type(value) is not list:
        _refuse(f"a Job's test scope is a list of repository-relative paths, "
                f"empty when the Work changes none; this is "
                f"{name_value(value)}")
    if len(value) > MAX_JOBS:
        _refuse(f"a Job's test scope names {len(value)} paths and this build "
                f"admits {MAX_JOBS}")
    scope = [check_relative_path(one, "a test-scope path") for one in value]
    _unique(scope, "test-scope path", f"Job {job_id}")
    return scope


def _stage(job_id, entry):
    taken = boundaries.document(entry, f"a stage of Job {job_id}",
                                required=STAGE_MEMBERS)
    if taken["kind"] not in STAGE_KINDS:
        _refuse(f"a stage kind is one of {', '.join(STAGE_KINDS)}; this is "
                f"{name_value(taken['kind'])}")
    kind = taken["kind"]
    work_id = boundaries.text(taken["work_id"], f"the Work {kind} stage names")
    profile_name = boundaries.text(taken["profile_name"],
                                   "a requested profile name")
    profile_digest = boundaries.text(taken["profile_digest"],
                                     "a requested profile digest")
    depends = _sequence_or_empty(taken["depends_on"],
                                 f"Job {job_id}'s {kind} dependencies")
    gates = [_dependency(job_id, kind, one) for one in depends]
    _unique([stage_id(one["job_id"], one["kind"]) for one in gates],
            "dependency", f"Job {job_id}'s {kind} stage")
    return {"kind": kind, "work_id": work_id, "profile_name": profile_name,
            "profile_digest": profile_digest, "depends_on": gates}


def _sequence_or_empty(value, what):
    # A stage with no predecessor is the ordinary case -- it is what lets two
    # Jobs fork from one baseline and run at once -- so an empty list is a
    # legitimate answer here and a missing member is still not.
    if type(value) is not list:
        _refuse(f"{what} is a list of stage-scoped dependencies, empty when "
                f"the stage has none; this is {name_value(value)}")
    if len(value) > MAX_JOBS * MAX_STAGES:
        _refuse(f"{what} names more dependencies than this build admits")
    return value


def _dependency(job_id, kind, entry):
    taken = boundaries.document(entry, f"a dependency of Job {job_id}'s "
                                       f"{kind} stage",
                                required=DEPENDENCY_MEMBERS)
    named = boundaries.identity(taken["job_id"], "a depended-on Job id")
    if taken["kind"] not in STAGE_KINDS:
        _refuse(f"a dependency names a stage kind out of "
                f"{', '.join(STAGE_KINDS)}; this is "
                f"{name_value(taken['kind'])}")
    if named == job_id and taken["kind"] == kind:
        _refuse(f"Job {name_value(job_id)}'s {kind} stage depends on itself; a "
                f"stage that gates on its own completion is never eligible")
    return {"job_id": named, "kind": taken["kind"]}


def _resolvable(jobs):
    """Every dependency names a stage this submission actually carries, and
    the graph has no cycle.

    BOTH, AND IN THIS ORDER. An unresolvable dependency is the likelier
    operator mistake and has the clearer diagnostic; a cycle is the one that
    would otherwise be discovered as "nothing is ever eligible", which reads
    as the scheduler being broken rather than as the submission being wrong.
    """
    present = {stage_id(job["job_id"], stage["kind"]): stage["depends_on"]
               for job in jobs for stage in job["stages"]}
    missing = sorted({stage_id(gate["job_id"], gate["kind"])
                      for gates in present.values() for gate in gates
                      if stage_id(gate["job_id"], gate["kind"])
                      not in present})
    if missing:
        _refuse(f"this submission gates on {sample_of(missing)}, which it does "
                f"not carry; a dependency on a stage outside the submission "
                f"is a gate nothing in it can ever open")
    _acyclic(present)


def _acyclic(present):
    # Kahn's ordering, over a graph whose size this document's own bounds have
    # already fixed. What survives with unmet gates is exactly the cycle.
    pending = {one: {stage_id(gate["job_id"], gate["kind"])
                     for gate in gates} for one, gates in present.items()}
    settled = set()
    moved = True
    while moved:
        moved = False
        for one in sorted(pending):
            if pending[one] <= settled:
                settled.add(one)
                del pending[one]
                moved = True
    if pending:
        _refuse(f"this submission's stage dependencies form a cycle through "
                f"{sample_of(sorted(pending))}; no stage in a cycle is ever "
                f"eligible, and refusing it at submission is the only moment "
                f"an operator can be told which stages are involved")


def submission_signature(owned):
    """The durable identity of one submitted intent.

    The canonical text of the NORMALIZED document, so an exact resubmission
    replays and a submission that changes any member of the intent collides
    rather than quietly rewriting durable rows.
    """
    return canonical_text(own(owned, what="a job submission"))


# -- the outbound half -------------------------------------------------------
#
# name -> (required, optional). One table, so "what does this control plane
# answer with" has a written answer rather than a survey of return statements.
CONTRACTS = {
    "submission.recorded": (("submission_id", "signature", "jobs", "stages",
                             "recorded_at"), ()),
    "stage.act": (("stage_id", "job_id", "kind", "act", "operation_id",
                   "offer_id", "attempt_id", "work_id"), ()),
    "stage.receipt": (("stage_id", "act", "operation_id", "state",
                       "recorded_at", "detail"), ()),
    "stage.dependency-gate": (("stage_id", "state", "open"), ()),
    "stage.status": (("stage_id", "job_id", "kind", "state", "work_id",
                      "profile_name", "profile_digest", "offer_id",
                      "attempt_id", "gates", "receipts", "runtime",
                      "artifacts"), ()),
    "job.status": (("job_id", "submission_id", "input_digest",
                    "policy_digest", "test_scope", "terminal_policy",
                    "stages"), ()),
    "status": (("schema", "observed_at", "incarnation", "canonical",
                "jobs"), ()),
    "reconciliation": (("stage_id", "act", "outcome", "operation_id"),
                       ("detail",)),
    # `recovered` is the manager's OWN restart report and is null on an
    # ordinary tick, so a reader can tell a resumed process from a running
    # one without keeping count of ticks.
    "sweep": (("observed_at", "recovered", "acts"), ()),
}


def _emit(name, members):
    required, optional = CONTRACTS[name]
    missing = [member for member in required if member not in members]
    if missing:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build assembled a {name} document without "
            f"{', '.join(missing)}; an answer that does not match its "
            f"contract is one no receiver can own")
    allowed = frozenset(required) | frozenset(optional)
    extra = sorted(member for member in members if member not in allowed)
    if extra:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build assembled a {name} document carrying "
            f"{', '.join(extra)}, which its contract does not name")
    ordered = tuple(required) + tuple(member for member in optional
                                      if member in members)
    return {member: members[member] for member in ordered}


def submission_recorded(**members):
    return _emit("submission.recorded", members)


def act(**members):
    return _emit("stage.act", members)


def receipt(**members):
    return _emit("stage.receipt", members)


def dependency_gate(**members):
    return _emit("stage.dependency-gate", members)


def stage_status(**members):
    return _emit("stage.status", members)


def job_status(**members):
    return _emit("job.status", members)


def status(**members):
    return _emit("status", members)


def reconciliation(**members):
    return _emit("reconciliation", members)


def sweep_report(**members):
    return _emit("sweep", members)
