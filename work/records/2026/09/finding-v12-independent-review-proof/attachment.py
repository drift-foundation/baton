"""The supported arrangement binding W239533's review to W239528's proposal.

This is the answer to G2 in W244180's `INPUTS.md`, which recorded the gap in
exactly these terms: "the reviewed procedure mapping the separate W239533
execution to W239528's retained checkpoint and exact proposal bytes ... A
brand-new unrelated line has no accepted producer checkpoint; copying the
proposal file or supplying a new Work ID does not create that provenance."

WHAT THE ARRANGEMENT IS, in one sentence: the reviewer Job brings its OWN Job
store, submission, stage, attempt, task document and outcome, and RECOVERS the
producer's line through `review_cycles.create_line`'s own identity rule rather
than creating anything.

WHY THAT IS THE SUPPORTED PATH AND NOT A WORKAROUND. `create_line` derives
`line_id` from `(authority_uuid, work_id)` alone and, finding the row already
there, replays the committed creation instead of making a second line.
`StageDeployment.line_for` calls it with the deployment's own `authority_uuid`
and the binding's `job_work_id`, so a second deployment that names the SAME v12
Authority and Work reaches the SAME line, and `StageComposition._prepare` then
takes that line's current checkpoint. Nothing here copies a row, manufactures a
writer or checkpoint, or relaxes a validator: the recovery is the product's own
replay, and every refusal below is the product's own.

THE THREE THINGS THAT ARE THE SAME, AND WHY EACH ONE HAS TO BE.

  * THE v12 AUTHORITY AND WORK. They are the line's identity. W239533 and
    W239528 are distinct *v11* Work items -- distinct claims, distinct
    dossiers, distinct evidence -- and that distinction is real and preserved.
    It is not the same axis as the v12 Work a line belongs to, and treating it
    as one is how a reviewer ends up judging a line nobody produced.
  * THE CONTROL STORE. The line, its writer, its frozen checkpoint and the
    review attachment are records in the control store. A review that opened a
    different control store would be reviewing a line that does not exist.
  * THE WORKSPACE STORAGE AND THE NOMINATED SOURCE. `create_line` recomputes
    `line_path` from the control store's own configured workspace storage and
    compares `(profile_name, declared_base, source_path, source_device,
    source_inode, line_path)` against the recorded row, refusing an
    `operation-collision` on any difference; `_validate_line_object` then
    re-proves that `line_path` still names the same device and inode. A copy
    of the retained tree at another path has other inodes and fails that, so
    "run the review against a copy" is not available and is not proposed here.

WHAT IS THE REVIEWER'S OWN, and this is where the separation actually lives:
its Job store, Job identity, submission, stage, attempt, generation, task
document and criteria, launch home, credential home, private-context storage,
deployment state root, outcome document -- and its worker, participant and
principal, which `attach_review` compares against the producer's writer and
refuses when any of the three matches.

HOW IT READS, AND THIS IS THE CORRECTION REVIEW 2026-09-23T04:40:30Z REQUIRED.
The first version of this module opened the store with `sqlite3.connect` and
issued its own `SELECT`s. That is not the supported interface, and AGENTS.md
says so without qualification: "Never read it directly either: if a question
about the coordination state can only be answered by opening the store, that
inability is the finding." `mode=ro` does not exempt raw SQL from that rule,
and the reviewer was right that the premise I built it on -- that
`ControlStore.open` might migrate -- was true but incomplete, because
`ControlStore.open_readonly` already exists and refuses an empty or
unrecognized store without initializing it.

So this module now opens `ControlStore.open_readonly`, takes ONE coherent
`snapshot()` and reads `line_of`, `checkpoint_of` and `writer_of` inside it.
Three consequences follow, and they are improvements rather than costs:

  * THE LINE AND CHECKPOINT ARE NAMED, NOT SEARCHED FOR. No public reader
    answers "the line for this Authority and Work", so the packet NAMES the
    line identity it intends to review, and this module proves that the named
    line really carries the named Authority and Work. A named identity that is
    checked is better evidence than a search that could quietly find something
    else.
  * `STALE` AND `WRONG` ARE DECIDED FROM THE CHECKPOINT'S OWN ROW rather than
    from a listing: `checkpoint_of` answers the checkpoint's line and revision,
    which is all the distinction ever needed.
  * THE READS ARE COHERENT. One `snapshot()` spans the line, the checkpoint
    and the writer, so the three cannot be an account of three different
    moments. The previous version had no such boundary, and the reviewer was
    right that sequential cases do not demonstrate one.

`GAPS` below records the public lookups that do not exist, exactly, rather than
routing around them.
"""

import json
from datetime import datetime, timezone

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, checkpoint_of, line_of,
                                      writer_of)

__all__ = ["SUBJECT_SCHEMA", "GAPS", "AttachmentRefusal", "now", "reading",
           "survey", "subject", "refusals", "attachable"]

SUBJECT_SCHEMA = "baton.independent-review-subject/2"

# The public reader this module wanted and did not find. Recorded rather than
# bypassed, per review 2026-09-23T04:40:30Z. None of these is a blocker for the
# arrangement -- each has a supported alternative named beside it -- and none
# was worked around with a private connection.
GAPS = (
    "No public function answers 'the line for this Authority and Work' "
    "without creating one: `create_line` derives the identity and WRITES, and "
    "the derivation itself is private. SUPPORTED ALTERNATIVE, and the one "
    "used here: the packet NAMES `line_id`, and `line_of` then proves that "
    "line carries the expected Authority and Work. An operator reads the "
    "identity from the producer's retained `outcome.json`, which is a file "
    "rather than a store.",
    "No public reader lists a line's checkpoints. SUPPORTED ALTERNATIVE: "
    "`checkpoint_of` answers one checkpoint's own line and revision, which is "
    "what separates a superseded revision of THIS line from a checkpoint of "
    "another line; a listing was never needed for the decision.",
    "No public reader lists a line's writers or its review attachments. "
    "SUPPORTED ALTERNATIVE: `line_of` answers the line's state, and "
    "`review-ready` versus `writing` versus `reviewing` is the signal the "
    "validator itself acts on. `test_attachment` establishes that "
    "`attach_review`'s writer-coexistence branch is unreachable from "
    "`review-ready`, so the state is not a weaker signal here -- it is the "
    "reachable one.",
)

# The line state from which a review may be attached, and the checkpoint state
# it requires. `attach_review` spells both: "a review attachment requires a
# frozen checkpoint" and "review attaches only to the current review-ready
# checkpoint".
ATTACHABLE_LINE = "review-ready"
ATTACHABLE_CHECKPOINT = "frozen"

# The three identities independence is decided on. `attach_review` names them
# in this order in its refusal and this module reports them the same way, so an
# operator reading either message is reading about the same three things.
INDEPENDENT = ("worker", "participant", "principal")

# This module never writes, so its incarnation exists only to satisfy the
# opener's own contract. It names what it is.
INCARNATION = "w239533-attachment-survey"


def now():
    """One instant in the grammar the public boundary accepts.

    `ControlStore.open_readonly` requires a clock and calls it; the operator
    page printed `clock=lambda: "now"`, and the instant boundary rejects that
    string, so the documented survey could not run as printed. Review
    2026-09-23T11:30:47Z R1. This module exports the formula so the page can
    name it instead of inventing one, and `test_attachment` runs that exact
    block.
    """
    moment = datetime.now(timezone.utc)
    return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{moment.microsecond // 1000:03d}Z")


class AttachmentRefusal(Exception):
    """This module refuses rather than answering a subject it cannot hold."""


def _refuse(message):
    raise AttachmentRefusal(message)


def reading(path, *, clock):
    """The producer's control store, through the opener that cannot change it.

    `ControlStore.open_readonly` recognizes the schema and refuses an empty or
    unsupported store WITHOUT migrating it, which is the whole reason the first
    version of this module reached for a private connection. It was already
    there, including in the selected `manager-source-242687` snapshot.

    SQLITE STILL OWNS ITS COORDINATION FILES, and the opener's own docstring
    says so: a `wal` database opened read-only gets its `-shm` and `-wal`
    companions if they are absent. This claim's earlier survey created exactly
    those two beside W239528's retained control store; they are DISCLOSED in
    `PROGRESS.md` and left in place. Using the supported opener does not undo
    that and does not relabel it as a clean read.

    `clock` is an operand rather than a default because the opener requires one
    and a module that invented a clock would be deciding an instant source on
    the caller's behalf.
    """
    try:
        return ControlStore.open_readonly(path, incarnation=INCARNATION,
                                          clock=clock)
    except ContractRefusal as failure:
        _refuse(f"the producer's control store at {path!r} did not open "
                f"through its non-writing opener: {failure}. This is an "
                f"operational finding, not a reason to open it another way.")


def _read(thunk, what):
    try:
        return thunk()
    except ContractRefusal as failure:
        _refuse(f"{what}: {failure}")


def survey(store, *, line_id, checkpoint_id=None):
    """The line, its current checkpoint and that checkpoint's writer.

    ONE `snapshot()` SPANS ALL OF IT. The three records are one account of one
    moment or they are not evidence, and the public snapshot boundary is the
    supported way to say so.

    `checkpoint_id` is read too when the caller names one that is not the
    current checkpoint, because deciding whether a named checkpoint is a
    superseded revision of THIS line or a checkpoint of another line is a
    question about that checkpoint's own record.
    """
    with store.snapshot():
        line = _read(lambda: line_of(store, line_id),
                     f"line {line_id!r} is not readable")
        current = None
        producer = None
        if line["current_checkpoint_id"] is not None:
            current = _read(
                lambda: checkpoint_of(store, line["current_checkpoint_id"]),
                f"the current checkpoint of line {line_id!r} is not readable")
            producer = _read(
                lambda: writer_of(store, current["writer_id"]),
                f"the writer of checkpoint "
                f"{line['current_checkpoint_id']!r} is not readable")
        named = current
        if checkpoint_id is not None and (
                current is None
                or checkpoint_id != current["checkpoint_id"]):
            try:
                named = checkpoint_of(store, checkpoint_id)
            except ContractRefusal:
                # ABSENCE IS AN ANSWER, not a failure. A checkpoint identity
                # this store does not hold is exactly the `WRONG` case, and
                # reporting it as a refusal here would hide it behind an
                # exception the caller cannot act on.
                named = None
        return {"line": line, "checkpoint": current, "producer": producer,
                "named_checkpoint": named}


def subject(store, *, line_id, authority_uuid, work_id, checkpoint_id=None):
    """The immutable subject of the review, named the way a packet names it.

    Every member is read through a supported reader inside one snapshot. The
    Authority and Work are PROVED against the named line rather than used to
    find it, for the reason `GAPS` gives.
    """
    found = survey(store, line_id=line_id, checkpoint_id=checkpoint_id)
    line = found["line"]
    if line["authority_uuid"] != authority_uuid or line["work_id"] != work_id:
        _refuse(f"line {line_id!r} belongs to Authority "
                f"{line['authority_uuid']!r} and v12 Work "
                f"{line['work_id']!r}, and this deployment names "
                f"{authority_uuid!r} and {work_id!r}. A review Job names the "
                f"producer's own v12 Authority and Work, which is what makes "
                f"it the same line.")
    checkpoint = found["checkpoint"]
    if checkpoint is None:
        _refuse(f"line {line_id!r} is {line['state']!r} and holds no current "
                f"checkpoint; there is no proposal to review yet")
    producer = found["producer"]
    # THE PUBLIC READER DECODES IT. `checkpoint_of` answers `evidence` as the
    # object the profile froze, not as the stored text -- the raw-SQL version
    # of this module saw the text and called `json.loads` on it, which is one
    # more way that version was reading something other than what the
    # supported interface answers. Both shapes are accepted so a caller that
    # hands over a row read some other way is not silently misread.
    evidence = checkpoint["evidence"]
    if isinstance(evidence, (str, bytes, bytearray)):
        evidence = json.loads(evidence)
    named = found["named_checkpoint"]
    return {
        "schema": SUBJECT_SCHEMA,
        "authority_uuid": line["authority_uuid"],
        "work_id": line["work_id"],
        "line_id": line["line_id"],
        "line_state": line["state"],
        "line_revision": line["revision"],
        "line_path": line["line_path"],
        "line_device": line["line_device"],
        "line_inode": line["line_inode"],
        "profile_name": line["profile_name"],
        "declared_base": line["declared_base"],
        "source_path": line["source_path"],
        "source_device": line["source_device"],
        "source_inode": line["source_inode"],
        "checkpoint_id": checkpoint["checkpoint_id"],
        "checkpoint_state": checkpoint["state"],
        "checkpoint_revision": checkpoint["revision"],
        "checkpoint_digest": checkpoint["checkpoint_digest"],
        "base_object": checkpoint["base_object"],
        "head_object": checkpoint["head_object"],
        "tree_object": checkpoint["tree_object"],
        "path_set_digest": checkpoint["path_set_digest"],
        "reference_name": checkpoint["reference_name"],
        "paths": list(evidence.get("paths") or []),
        "producer": {
            "writer_id": producer["writer_id"],
            "attempt_id": producer["runtime_attempt_id"],
            "generation": producer["assignment_generation"],
            "worker_id": producer["worker_id"],
            "participant": producer["participant"],
            "principal": producer["principal"],
            "state": producer["state"]},
        # ONLY WHAT WAS ASKED ABOUT. A named checkpoint that is neither the
        # current one nor a record this store holds is absent here, and the
        # refusal below says which of the two it was.
        "named_checkpoint": None if named is None else {
            "checkpoint_id": named["checkpoint_id"],
            "line_id": named["line_id"],
            "revision": named["revision"],
            "state": named["state"]}}


def refusals(held, *, checkpoint_id, reviewer_worker_id, reviewer_participant,
             reviewer_principal, profile_name=None):
    """Every reason this attachment would be refused, in this module's words.

    An EMPTY list means the manager's own `attach_review` has no precondition
    left to fail on the facts read here. It does not mean the attachment has
    happened, and it cannot: the snapshot is one moment and the act is another,
    which is why `attach_review` re-reads the line inside its own transaction.
    This is a preflight, and it says so.

    THE ORDER IS THE VALIDATOR'S ORDER where the validator has one, so the
    first entry is the first thing a caller would have hit.
    """
    found = []
    if held.get("schema") != SUBJECT_SCHEMA:
        _refuse("a refusal check reads a subject this module composed")
    if profile_name is not None and profile_name != held["profile_name"]:
        found.append(
            f"PROFILE: the line's profile is {held['profile_name']!r} and the "
            f"reviewer deployment names {profile_name!r}; `attach_review` "
            f"refuses when the line and review profile do not match.")
    if held["checkpoint_state"] != ATTACHABLE_CHECKPOINT:
        found.append(
            f"NOT FROZEN: checkpoint {held['checkpoint_id']!r} is "
            f"{held['checkpoint_state']!r}; a review attachment requires a "
            f"frozen checkpoint.")
    if checkpoint_id != held["checkpoint_id"]:
        named = held["named_checkpoint"]
        if named is None:
            found.append(
                f"WRONG: this control store holds no checkpoint "
                f"{checkpoint_id!r}. The current checkpoint of line "
                f"{held['line_id']!r} is {held['checkpoint_id']!r}.")
        elif named["line_id"] != held["line_id"]:
            found.append(
                f"WRONG: checkpoint {checkpoint_id!r} belongs to line "
                f"{named['line_id']!r}, not to {held['line_id']!r}. It is a "
                f"real frozen checkpoint of somebody else's proposal.")
        else:
            found.append(
                f"STALE: checkpoint {checkpoint_id!r} is revision "
                f"{named['revision']} of this line and the line's current "
                f"checkpoint is {held['checkpoint_id']!r} at revision "
                f"{held['checkpoint_revision']}. Review attaches only to the "
                f"current review-ready checkpoint, so a superseded one is "
                f"refused rather than reviewed.")
    if held["line_state"] != ATTACHABLE_LINE:
        found.append(
            f"LINE STATE: line {held['line_id']!r} is {held['line_state']!r} "
            f"and review attaches only to a {ATTACHABLE_LINE!r} line. "
            + ("A reviewing line already holds an attachment. "
               if held["line_state"] == "reviewing" else
               "A writing line is under correction and its current checkpoint "
               "is the one being corrected. "
               if held["line_state"] == "writing" else "")
            + "This is a state to report, not one to reset.")
    producer = held["producer"]
    same = [axis for axis, mine, theirs in (
        ("worker", reviewer_worker_id, producer["worker_id"]),
        ("participant", reviewer_participant, producer["participant"]),
        ("principal", reviewer_principal, producer["principal"]))
        if mine == theirs]
    if same:
        found.append(
            f"NOT INDEPENDENT AT: {', '.join(same)}. The producer is worker "
            f"{producer['worker_id']!r}, participant "
            f"{producer['participant']!r}, principal "
            f"{producer['principal']!r}, and a review that shares any of the "
            f"three is the producer grading itself.")
    return found


def attachable(store, *, line_id, authority_uuid, work_id, checkpoint_id,
               reviewer_worker_id, reviewer_participant, reviewer_principal,
               profile_name=None):
    """The subject, with its refusals -- the whole preflight in one call.

    Returns `(subject, refusals)`. The caller decides what to do with a
    non-empty refusal list; this module never decides to proceed.
    """
    held = subject(store, line_id=line_id, authority_uuid=authority_uuid,
                   work_id=work_id, checkpoint_id=checkpoint_id)
    return held, refusals(
        held, checkpoint_id=checkpoint_id,
        reviewer_worker_id=reviewer_worker_id,
        reviewer_participant=reviewer_participant,
        reviewer_principal=reviewer_principal, profile_name=profile_name)
