"""Durable development lines, immutable review checkpoints and corrections.

The Worker Manager owns this lifecycle above disposable runtime attempts.  A
line is keyed by Authority and Work, while every writable or read-only
attachment is fenced to one activated assignment generation.  Source-specific
commands live behind an injected checkpoint profile; this component persists
only its closed evidence.
"""

import json
import os

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from . import (attempts, boundaries, custody, intake, manifests, output, schema,
               source_boundary, workspaces)
from .attempts import assignment_of
from .store import manager_signature

__all__ = ["ATTACH_KIND", "DISPOSITIONS", "GRANT_KIND", "LINE_HOME",
           "VERDICT_KIND",
           "attach_review", "audit_checkpoint", "checkpoint_of",
           "create_line", "freeze_checkpoint", "grant_writer",
           "integration_checkpoint", "line_of", "line_status",
           "record_progress", "record_verdict", "review_boundary",
           "review_for_attempt", "review_of", "verdict_of", "writer_boundary",
           "writer_for_attempt", "writer_of"]

DISPOSITIONS = ("accepted", "changes-requested", "rejected")

# W103076: THE TWO OPERATION KINDS THIS MODULE COMMITS ITS ATTACHMENTS AND
# VERDICTS UNDER. They are named here because the readers below cross-bind a
# materialized row against the act that wrote it, and because a consumer that
# had to spell them for itself would be keeping a copy of this module's
# journal shape -- which is exactly what the readers exist to stop.
ATTACH_KIND = "review-line.attach-review"
VERDICT_KIND = "review-line.verdict"
# W124331: the writer grant's kind, named beside the other two for the reason
# they are named -- the readers below cross-bind a materialized row against
# the act that wrote it, and a consumer spelling this for itself would be
# keeping a copy of this module's journal shape.
GRANT_KIND = "review-line.grant-writer"
LINE_HOME = ".baton-review-lines"


def _id(prefix, value):
    return prefix + "-" + digest(value).split(":", 1)[1]


def _profile(profile, methods):
    name = getattr(profile, "name", None)
    boundaries.text(name, "a checkpoint profile name")
    for method in methods:
        boundaries.capability(getattr(profile, method, None),
                              f"a checkpoint profile's {method} capability")
    return name


def line_of(store, line_id):
    boundaries.identity(line_id, "a development line identity")
    row = store._connection.execute(
        "SELECT * FROM review_lines WHERE line_id = ?", (line_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no development line {name_value(line_id)}")
    return boundaries.row(row, "a persisted development line",
                          schema.REVIEW_LINE_COLUMNS)


def writer_of(store, writer_id):
    boundaries.identity(writer_id, "a line writer identity")
    row = store._connection.execute(
        "SELECT * FROM line_writers WHERE writer_id = ?", (writer_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no line writer {name_value(writer_id)}")
    return boundaries.row(row, "a persisted line writer",
                          schema.LINE_WRITER_COLUMNS)


def checkpoint_of(store, checkpoint_id):
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    row = store._connection.execute(
        "SELECT * FROM line_checkpoints WHERE checkpoint_id = ?",
        (checkpoint_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no line checkpoint {name_value(checkpoint_id)}")
    taken = boundaries.row(row, "a persisted line checkpoint",
                           schema.LINE_CHECKPOINT_COLUMNS)
    if taken["evidence"] is not None:
        taken["evidence"] = _evidence(json.loads(taken["evidence"]))
    if taken["fence"] is not None:
        taken["fence"] = _fence(json.loads(taken["fence"]),
                                "a persisted checkpoint fence")
        if taken["fence_digest"] != digest(taken["fence"]):
            raise ContractRefusal(
                "integrity", "digest",
                "persisted checkpoint fence does not match its digest")
        _committed_fence(store, taken["fence"],
                         "the persisted checkpoint fence")
    if taken["state"] == "frozen":
        evidence = taken["evidence"]
        recorded = (taken["profile_name"], taken["base_object"],
                    taken["head_object"], taken["tree_object"],
                    taken["path_set_digest"], taken["reference_name"],
                    taken["checkpoint_digest"])
        derived = (evidence["profile"], evidence["base"], evidence["head"],
                   evidence["tree"], evidence["path_set_digest"],
                   evidence["reference"], digest(evidence))
        if recorded != derived:
            raise ContractRefusal(
                "integrity", "digest",
                "persisted checkpoint columns do not match their sealed evidence")
    return taken


def _evidence(value):
    taken = boundaries.document(
        value, "persisted checkpoint evidence",
        required=("base", "head", "path_set_digest", "paths", "profile",
                  "reference", "tree"))
    for member in ("base", "head", "path_set_digest", "profile", "reference",
                   "tree"):
        boundaries.text(taken[member],
                        f"persisted checkpoint evidence's {member}")
    paths = taken["paths"]
    if type(paths) is not list:
        raise ContractRefusal("integrity", "schema",
                              "persisted checkpoint evidence's paths is a list")
    for path in paths:
        boundaries.text(path, "a persisted checkpoint evidence path")
        if path.startswith("/") or ".." in path.split("/"):
            raise ContractRefusal("integrity", "path",
                                  "a persisted checkpoint path is relative and canonical")
    if paths != sorted(set(paths)) or taken["path_set_digest"] != digest(paths):
        raise ContractRefusal("integrity", "digest",
                              "persisted checkpoint paths do not match their digest")
    return taken


def _committed_operands(store, kind, operation_id, what):
    """The OPERANDS one of this module's own acts was authorized with.

    W103076 second re-review [P0]. `_committed_act` answers what an act
    RETURNED, and for `attach_review` that is three members -- so a reader
    comparing only those left `runtime_attempt_id`, the generation and the
    reviewer identity unbound, and a rewritten attempt row was answered without
    refusal. The operands are the whole of what the act was authorized with,
    they are in the signature this module built, and they are read here rather
    than by anybody else because a journal's shape is the owner's.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    document = json.loads(record["signature"])
    if not isinstance(document, dict) or document.get("kind") != kind \
            or not isinstance(document.get("operands"), dict):
        raise ContractRefusal(
            "integrity", "schema",
            f"the committed {kind} act for {what} carries no operands this "
            f"build can read")
    return document["operands"]


def _bound_to_act(operands, held, what, kind):
    """Every member of a row that its act fixed, compared with what it fixed.

    A DISAGREEMENT REFUSES RATHER THAN BEING RECONCILED, because two accounts
    of one decision have no tie-break and inventing one here would be this
    module choosing which of its own records to believe.
    """
    for member, (source, value) in held.items():
        if operands.get(source) != value:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} and the {kind} act that wrote it disagree about "
                f"{member}")


def _committed_act(store, kind, operation_id, what):
    """The committed journal row for one of THIS module's own acts.

    W103076. WHY THE READERS BELOW DO THIS AT ALL. A materialized row says what
    this store currently holds; the journal says which committed act put it
    there. Cross-binding them is what makes a reader's answer evidence rather
    than a projection -- a row that no committed act of the right kind explains
    is a row this build must not hand out as though somebody had decided it.

    It is the same discipline `_committed_fence` already applies to a
    persisted fence, and it belongs at the OWNER: a consumer that reconstructed
    this module's operation identities and parsed its journal for itself would
    be keeping a second account of a shape only this module gets to change.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    return json.loads(record["result"]) if record["result"] else None


def _verdict_row(store, verdict_id):
    """THE ONE CROSSING out of `checkpoint_verdicts`, or absence.

    W103076 extracted it. Two readers now answer about a recorded verdict --
    integration eligibility and `verdict_of` -- and a table adopted in two
    places is two column contracts that can drift, which is the shape the
    manager's own boundary inventory exists to prevent. One site, one
    adoption, and each caller decides what absence means for it.
    """
    boundaries.identity(verdict_id, "a checkpoint verdict identity")
    row = store._connection.execute(
        "SELECT * FROM checkpoint_verdicts WHERE verdict_id = ?",
        (verdict_id,)).fetchone()
    if row is None:
        return None
    return boundaries.row(row, "a persisted checkpoint verdict",
                          schema.CHECKPOINT_VERDICT_COLUMNS)


def review_of(store, attachment_id):
    """One review attachment, bound to the act that attached it.

    W103076. WHAT A CONSUMER NEEDS FROM THIS and could not get before: WHICH
    RUNTIME ATTEMPT a reviewer attachment belongs to. A composite that ends a
    review has an attachment identity and must not take the attempt as a
    second, independently chosen operand -- two live lines would otherwise let
    it freeze one reviewer's output and record a verdict about another's.

    THE ANSWER IS THE ROW, PROVED BY THE ACT. `attach_review` commits under an
    identity derived from the attachment and journals the checkpoint it
    attached to, so the row's own `checkpoint_id` is compared with what that
    act recorded. A row and an act that disagree refuse rather than being
    reconciled here.
    """
    attachment = _attachment(store, attachment_id)
    what = f"review attachment {name_value(attachment_id)}"
    operands = _committed_operands(store, ATTACH_KIND,
                                   ATTACH_KIND + ":" + attachment_id, what)
    _bound_to_act(operands, {
        "attachment_id": ("attachment_id", attachment_id),
        "checkpoint_id": ("checkpoint_id", attachment["checkpoint_id"]),
        # THE ONE THE SECOND RE-REVIEW REWROTE. Without it a
        # foreign-key-valid attempt from another lane was answered as this
        # attachment's, and a composite that trusts the answer stops and
        # freezes the wrong runtime.
        "runtime_attempt_id": ("attempt_id",
                               attachment["runtime_attempt_id"]),
        "assignment_generation": ("generation",
                                  attachment["assignment_generation"]),
        "reviewer_worker_id": ("reviewer_worker_id",
                               attachment["reviewer_worker_id"]),
        "reviewer_participant": ("participant",
                                 attachment["reviewer_participant"]),
        "reviewer_principal": ("principal", attachment["reviewer_principal"]),
    }, what, ATTACH_KIND)
    # AND THE LINE, WHICH THE ACT DID NOT NAME AND THE CHECKPOINT DOES. An
    # attachment whose line is not its checkpoint's line is a row no act of
    # this module could have written.
    if attachment["line_id"] != checkpoint_of(
            store, attachment["checkpoint_id"])["line_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names a line its checkpoint does not belong to")
    return attachment


# W124331 review 2026-09-09T03:05Z [P1]. THE CLOSED JOURNAL SHAPE each
# historical reader proves its row against. Naming the members is what turns
# `.get` from a guess into a read: an operand that may legitimately be null --
# `based_checkpoint_id` on a first round -- is indistinguishable from a MISSING
# one under `.get` equality, and the reader would then answer a truncated act
# as though it agreed.
_SIGNATURE_MEMBERS = ("kind", "operands")
_GRANT_OPERANDS = ("writer_id", "line_id", "attempt_id", "generation",
                   "worker_id", "profile_name", "participant", "principal",
                   "based_checkpoint_id")
_GRANT_RESULT = ("writer_id", "line_id", "generation", "state")
_ATTACH_OPERANDS = ("attachment_id", "checkpoint_id", "attempt_id",
                    "generation", "reviewer_worker_id", "participant",
                    "principal")
_ATTACH_RESULT = ("attachment_id", "checkpoint_id", "state")


def _requested_pair(attempt_id, generation):
    """The exact pair a historical lookup selects on, typed before selection.

    W124331. `boundaries.generation` excludes `bool` in its own words, and that
    matters here twice: a boolean would select generation 1's row and would
    then compare equal to it. Owning both operands before the query is what
    stops a lookup from answering somebody else's history.
    """
    return (boundaries.identity(attempt_id, "a runtime attempt id"),
            boundaries.generation(generation, "an assignment generation"))


def _one_by_attempt(store, table, columns, attempt_id, generation, what):
    """The one row for this attempt and generation, or absence.

    THE UNIQUENESS IS THE SCHEMA'S AND IS REUSED RATHER THAN RESTATED. Both
    tables carry `UNIQUE (runtime_attempt_id, assignment_generation)`, so a
    pair selects one row or none and this reader never has to choose between
    two. A second row cannot exist for the query to find.
    """
    found = store._connection.execute(
        f"SELECT * FROM {table} WHERE runtime_attempt_id = ? "
        f"AND assignment_generation = ?", (attempt_id, generation)).fetchall()
    if not found:
        return None
    if len(found) > 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selects {len(found)} rows for one attempt and "
            f"generation; the table's own uniqueness says there is one")
    return boundaries.row(found[0], what, columns)


def _journalled(text, what):
    """One committed journal document, refused in THIS domain's words.

    W124331 review [P1]: both new readers reached `json.loads` directly and a
    damaged signature escaped as `JSONDecodeError`. A parser error is not a
    refusal -- it carries no category, no code and no pairing, so a consumer
    that handles this manager's refusals does not handle it at all, and the
    one thing the reader exists to say ("this history cannot be trusted") is
    the one thing it fails to say.
    """
    if type(text) is not str or not text:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is not journalled text; a row whose act recorded nothing "
            f"is not evidence about anything")
    try:
        document = json.loads(text)
    except ValueError:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is not readable as a journal document") from None
    return document


def _committed_history(store, kind, operation_id, what, operand_members,
                       result_members):
    """This module's own committed act behind a historical row, read WHOLE.

    W124331 review [P1]. `_committed_operands` answers what an act was
    authorized with and is left exactly as it is -- the existing readers'
    behaviour is not this Work's to change. What a HISTORICAL reader needs on
    top of it is everything a damaged journal can be: unparseable, a document
    of another shape, an act that recorded no result, or a result belonging to
    something else. Each of those was answered with the honest row before this,
    which is the worst possible outcome for a reader whose whole purpose is
    telling a resuming consumer that its history is intact.

    So the signature, its operands and the act's own result are each adopted
    against a CLOSED member contract, and the generation the act was authorized
    with is typed rather than compared -- a journalled `true` would otherwise
    satisfy an equality against generation one, for `_requested_pair`'s reason
    one layer down.

    Kept private to the new boundary, as the approved proposal requires.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    signed = f"the committed {kind} signature for {what}"
    signature = boundaries.document(_journalled(record["signature"], signed),
                                    signed, required=_SIGNATURE_MEMBERS)
    if signature["kind"] != kind:
        raise ContractRefusal(
            "integrity", "schema",
            f"{signed} was signed as {name_value(signature['kind'])}")
    operands = boundaries.document(
        signature["operands"], f"the committed {kind} operands for {what}",
        required=operand_members)
    answered = f"the committed {kind} result for {what}"
    result = boundaries.document(_journalled(record["result"], answered),
                                 answered, required=result_members)
    boundaries.generation(operands["generation"],
                          f"the committed {kind} generation for {what}")
    return operands, result


def _derived_identity(prefix, operands, members, held, what):
    """The identity re-minted from the very operands that minted it.

    W124331 review [P1]. Comparing an act's members one by one says they agree;
    it does not say the act's IDENTITY follows from them. These identities are
    deterministic digests, so re-deriving is the whole proof -- and a row filed
    under an identity its own operands do not produce is one no act of this
    module could have written, however well its members read.
    """
    derived = _id(prefix, {member: operands[source]
                           for member, source in members})
    if derived != held:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is filed under {name_value(held)}, which its committed "
            f"operands do not derive")


def _assignment_agrees(store, attempt_id, line, held, what, kind):
    """The WHOLE fixed assignment the act read, checked against its own owner.

    W124331 review [P1]: participant and principal alone left the generation
    and the Work/Authority correlation unbound, so an attempt whose fixed
    generation had been moved to 99 still answered generation one's writer.
    The assignment is a four-part identity and the schema keeps its columns
    together; reading three quarters of one is how a row outlives the
    authorization it was made under without saying so.
    """
    assignment = assignment_of(store, attempt_id)
    boundaries.generation(assignment["generation"],
                          f"{what}'s fixed assignment generation")
    disagreements = sorted(member for member, value in held.items()
                           if assignment[member] != value)
    if disagreements:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} and the fixed assignment its {kind} act read disagree "
            f"about {', '.join(disagreements)}")
    if assignment["work_id"] != line["work_id"] \
            or assignment["authority_uuid"] != line["authority_uuid"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} belongs to a line held for another Work or Authority "
            f"than the assignment its {kind} act read")


def writer_for_attempt(store, *, attempt_id, generation):
    """The line writer this attempt was granted, whatever became of it.

    W124331, `work/records/2026/09/finding-v12-composed-ending-consumer/
    findings/finding-attempt-history-readers/`.

    WHAT COULD NOT BE ASKED BEFORE. Every historical reader here takes a writer
    or attachment identity, and those identities are DERIVED inside
    `grant_writer` and `attach_review` from facts a consumer holds -- so a
    deployment recovering its own ended attempt could reach its writer only by
    copying that derivation or by reading the line's CURRENT checkpoint. The
    first keeps a second copy of an identity only this module may change; the
    second is a mutable pointer that every later round moves, which is exactly
    how an honest recovery of an earlier ending became impossible. This answers
    from the attempt and its generation, which do not move.

    HISTORY IS THE POINT, so no state filter. A revoked writer is what a
    finished round leaves behind, and its row is returned with the state it
    actually has rather than the `active` its grant returned and its result
    still records. Absence is absence: an attempt nobody granted, or another
    generation of one that was, answers `None` rather than refusing.

    OWNERSHIP IS ESTABLISHED HERE AND NOT ASSUMED FROM `writer_of`. That reader
    owns the row's SHAPE; what it does not do is bind the row to the committed
    grant that fixed it. So the act is read whole -- signature, closed operands
    and its own recorded result -- its identity is re-derived from the operands
    that minted it, every immutable member is compared, and the two facts the
    act took from their own owners are checked against those owners: the line's
    profile and the attempt's fixed assignment. A row and an act that disagree
    refuse rather than being reconciled.

    IT READS AND DOES NOTHING ELSE. No insert, no update, no transaction, no
    profile call, no line revalidation, no port and no adapter.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the line writer for attempt {name_value(attempt_id)} "
            f"generation {generation}")
    writer = _one_by_attempt(store, "line_writers", schema.LINE_WRITER_COLUMNS,
                             attempt_id, generation, what)
    if writer is None:
        return None
    # THE SELECTED ROW MUST BE THE REQUESTED PAIR'S. The query says so, and
    # saying it again costs nothing next to answering somebody else's writer.
    if writer["runtime_attempt_id"] != attempt_id \
            or writer["assignment_generation"] != generation:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selected a row for attempt "
            f"{name_value(writer['runtime_attempt_id'])} generation "
            f"{writer['assignment_generation']}")
    held = writer_of(store, writer["writer_id"])
    if held != writer:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} reads differently through its own identity than through "
            f"its attempt")
    line = line_of(store, writer["line_id"])
    operands, result = _committed_history(
        store, GRANT_KIND, GRANT_KIND + ":" + writer["writer_id"], what,
        _GRANT_OPERANDS, _GRANT_RESULT)
    _derived_identity("writer", operands,
                      (("line_id", "line_id"), ("attempt_id", "attempt_id"),
                       ("generation", "generation")),
                      writer["writer_id"], what)
    # EVERY MEMBER THE ACT FIXED. `.get` is a read rather than a guess now:
    # `_committed_history` has already proved each of these members present.
    _bound_to_act(operands, {
        "writer_id": ("writer_id", writer["writer_id"]),
        "line_id": ("line_id", writer["line_id"]),
        "runtime_attempt_id": ("attempt_id", attempt_id),
        "assignment_generation": ("generation", generation),
        "worker_id": ("worker_id", writer["worker_id"]),
        "participant": ("participant", writer["participant"]),
        "principal": ("principal", writer["principal"]),
        # THE BASE THIS ROUND WAS BUILT ON, which is the member the consumer
        # came for: a correction writer names the checkpoint it corrected, and
        # a first writer names none. A changed base refuses here rather than
        # being handed out as the operand a later grant would replay under.
        "based_checkpoint_id": ("based_checkpoint_id",
                                writer["based_checkpoint_id"]),
    }, what, GRANT_KIND)
    # AND THE RESULT THE ACT ITSELF RECORDED, on its IMMUTABLE members only.
    # `state` is deliberately not compared: the grant returned `active` and
    # history is precisely what came after it, so requiring the act's original
    # state would refuse every writer this reader exists to answer.
    _bound_to_act(result, {
        "writer_id": ("writer_id", writer["writer_id"]),
        "line_id": ("line_id", writer["line_id"]),
        "assignment_generation": ("generation", generation),
    }, f"{what}'s recorded result", GRANT_KIND)
    if operands["profile_name"] != line["profile_name"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} was granted under profile "
            f"{name_value(operands['profile_name'])} and its line is kept "
            f"under {name_value(line['profile_name'])}")
    _assignment_agrees(store, attempt_id, line,
                       {"participant": writer["participant"],
                        "principal": writer["principal"],
                        "generation": generation}, what, GRANT_KIND)
    return writer


def review_for_attempt(store, *, attempt_id, generation):
    """The review attachment this attempt was given, whatever became of it.

    W124331, and the writer reader's twin. `review_of` binds an attachment to
    the act that attached it and to its checkpoint's line, and that is reused
    rather than repeated; what this adds is finding it from the attempt and
    generation rather than from an identity the consumer no longer holds, and
    the committed-history ownership `review_of` does not carry.

    WHY IT DOES NOT SIMPLY DELEGATE. Review [P1] measured the difference: a
    journalled boolean generation, a damaged signature and a foreign recorded
    result all passed straight through the inherited binding -- ordinary
    equality accepts `true` against generation one, and `review_of` never reads
    the act's result at all. So the strict read runs FIRST, before the
    inherited one, and the inherited binding is then taken on a record already
    proved readable.

    AN ENDED ATTACHMENT IS ORDINARY HISTORY. A recorded verdict ends it and a
    correction round then advances the line; the row is returned with the state
    it has. Absence stays absence, and this repeats none of `attach_review`'s
    current eligibility, independence or profile admission -- those decide
    whether a review MAY be attached, which is a different question from which
    one was.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the review attachment for attempt {name_value(attempt_id)} "
            f"generation {generation}")
    attachment = _one_by_attempt(store, "review_attachments",
                                 schema.REVIEW_ATTACHMENT_COLUMNS,
                                 attempt_id, generation, what)
    if attachment is None:
        return None
    if attachment["runtime_attempt_id"] != attempt_id \
            or attachment["assignment_generation"] != generation:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selected a row for attempt "
            f"{name_value(attachment['runtime_attempt_id'])} generation "
            f"{attachment['assignment_generation']}")
    operands, result = _committed_history(
        store, ATTACH_KIND, ATTACH_KIND + ":" + attachment["attachment_id"],
        what, _ATTACH_OPERANDS, _ATTACH_RESULT)
    _derived_identity("review", operands,
                      (("checkpoint_id", "checkpoint_id"),
                       ("attempt_id", "attempt_id"),
                       ("generation", "generation")),
                      attachment["attachment_id"], what)
    _bound_to_act(result, {
        "attachment_id": ("attachment_id", attachment["attachment_id"]),
        "checkpoint_id": ("checkpoint_id", attachment["checkpoint_id"]),
    }, f"{what}'s recorded result", ATTACH_KIND)
    _assignment_agrees(store, attempt_id,
                       line_of(store, attachment["line_id"]),
                       {"participant": attachment["reviewer_participant"],
                        "principal": attachment["reviewer_principal"],
                        "generation": generation}, what, ATTACH_KIND)
    # AND THE BINDING `review_of` ALREADY OWNS, on a record now proved
    # readable. Repeating it here would be a second account of one decision.
    held = review_of(store, attachment["attachment_id"])
    if held != attachment:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} reads differently through its own identity than through "
            f"its attempt")
    return held


def verdict_of(store, verdict_id):
    """One recorded checkpoint verdict, bound to the act that recorded it.

    W103076. A CONSUMER MAY BE HANDED A VERDICT IDENTITY AND MUST NOT BELIEVE
    IT. `record_verdict` journals the exact operands it bound -- verdict,
    attachment, line, checkpoint, Authority, Work, disposition and the sealed
    evidence -- so this reads the materialized row and proves every member of
    it against that committed act before answering.

    THE JOURNAL IS REACHED THROUGH THE ATTACHMENT, because that is the identity
    the act was named by. A verdict row whose attachment names a different
    verdict, or whose disposition or bindings differ from what was committed,
    refuses: two accounts of one decision have no tie-break and this module
    does not invent one.
    """
    verdict = _verdict_row(store, verdict_id)
    if verdict is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no checkpoint verdict {name_value(verdict_id)}")
    what = f"checkpoint verdict {name_value(verdict_id)}"
    operands = _committed_operands(
        store, VERDICT_KIND, VERDICT_KIND + ":" + verdict["attachment_id"],
        what)
    # THE RETAINED EVIDENCE, PARSED THROUGH ITS OWN OWNERS. Second re-review
    # [P0]: the row's `review_result_digest` was rewritten to another
    # well-formed digest and answered, so a correction could be scheduled on a
    # verdict whose retained evidence contradicted its act.
    verdict["review_result"] = _review_result(
        json.loads(verdict["review_result"]))
    verdict["review_fence"] = _fence(json.loads(verdict["review_fence"]),
                                     "a persisted review fence")
    if verdict["review_result_digest"] != digest(verdict["review_result"]) \
            or verdict["review_fence_digest"] != digest(verdict["review_fence"]):
        raise ContractRefusal(
            "integrity", "digest",
            f"{what} does not match the digests of the evidence it retains")
    _bound_to_act(operands, {
        "verdict_id": ("verdict_id", verdict["verdict_id"]),
        "attachment_id": ("attachment_id", verdict["attachment_id"]),
        "line_id": ("line_id", verdict["line_id"]),
        "checkpoint_id": ("checkpoint_id", verdict["checkpoint_id"]),
        "authority_uuid": ("authority_uuid", verdict["authority_uuid"]),
        "work_id": ("work_id", verdict["work_id"]),
        "disposition": ("disposition", verdict["disposition"]),
        "checkpoint_digest": ("checkpoint_digest",
                              verdict["checkpoint_digest"]),
        "revision": ("revision", verdict["revision"]),
        # THE REVIEWER'S OWN IDENTITY, which is the half of a verdict that
        # says WHO decided it and was entirely unbound.
        "review_assignment_generation": ("review_generation",
                                         verdict["review_assignment_generation"]),
        "reviewer_worker_id": ("reviewer_worker_id",
                               verdict["reviewer_worker_id"]),
        "reviewer_participant": ("reviewer_participant",
                                 verdict["reviewer_participant"]),
        "reviewer_principal": ("reviewer_principal",
                               verdict["reviewer_principal"]),
        # AND THE SEALED ACCOUNT OF WHAT WAS REVIEWED.
        "base_object": ("base", verdict["base_object"]),
        "head_object": ("head", verdict["head_object"]),
        "tree_object": ("tree", verdict["tree_object"]),
        "path_set_digest": ("path_set_digest", verdict["path_set_digest"]),
        "review_result": ("review_result", verdict["review_result"]),
        "review_result_digest": ("review_result_digest",
                                 verdict["review_result_digest"]),
        "review_fence": ("review_fence", verdict["review_fence"]),
        "review_fence_digest": ("review_fence_digest",
                                verdict["review_fence_digest"]),
    }, what, VERDICT_KIND)
    return verdict


def _attachment_row(store, attachment_id):
    row = store._connection.execute(
        "SELECT * FROM review_attachments WHERE attachment_id = ?",
        (attachment_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no review attachment {name_value(attachment_id)}")
    return boundaries.row(row, "a persisted review attachment",
                          schema.REVIEW_ATTACHMENT_COLUMNS)


def _attachment(store, attachment_id):
    boundaries.identity(attachment_id, "a review attachment identity")
    return _attachment_row(store, attachment_id)


def _same_assignment(assignment, line, generation):
    boundaries.generation(generation, "an assignment generation")
    if (assignment["authority_uuid"] != line["authority_uuid"]
            or assignment["work_id"] != line["work_id"]
            or assignment["generation"] != generation):
        raise ContractRefusal(
            "stale-assignment", "generation",
            "the runtime attempt is not the named generation of this line's "
            "Authority and Work")


def _within(child, parent):
    try:
        return os.path.commonpath((child, parent)) == parent
    except ValueError:
        return False


def _line_place(storage, line_id, source):
    boundaries.text(storage, "the manager's workspace storage")
    if not os.path.isabs(storage) or os.path.realpath(storage) != storage:
        raise ContractRefusal("integrity", "path",
                              "review-line storage is one canonical absolute path")
    root = os.path.join(storage, LINE_HOME)
    home = os.path.join(root, line_id)
    path = os.path.join(home, "checkout")
    if source == path or _within(source, path) or _within(path, source):
        raise ContractRefusal(
            "policy", "denied",
            "the nominated source and persistent development line contain one another")
    for place in (root, home):
        try:
            os.mkdir(place, 0o700)
        except FileExistsError:
            if os.path.islink(place) or not os.path.isdir(place) \
                    or os.path.realpath(place) != place:
                raise ContractRefusal(
                    "integrity", "path",
                    f"review-line custody {name_value(place)} is not its own directory")
    return path


def _object(place, what):
    if os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != place:
        raise ContractRefusal("integrity", "path",
                              f"{what} is no longer its own directory")
    held = os.stat(place, follow_symlinks=False)
    return held.st_dev, held.st_ino


def _consumable_line(store, line_id):
    """The line row as it is NOW, with its recorded object proved again.

    One function because the two halves are one question: a pathname is only
    evidence while the object it names is the object the lifecycle recorded,
    and a row read before an external call is a memory rather than a fact.
    """
    line = line_of(store, line_id)
    _validate_line_object(line)
    return line


def _validate_line_object(line):
    held = _object(line["line_path"], "the durable development line")
    if held != (line["line_device"], line["line_inode"]):
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            "the durable development line pathname now names another object")


def _storage(store):
    return workspaces.configured_workspace_storage(store).place


def _attempt(store, attempt_id):
    return attempts._require_attempt(store, attempt_id)


def _quiescent_completed(store, attempt_id, *, review=False):
    attempt = _attempt(store, attempt_id)
    if attempt["runtime_id"] is None or attempt["execution_runtime"] != "quiescent":
        raise ContractRefusal(
            "refused", "precondition",
            "review completion requires the exact attached runtime to be "
            "positively quiescent" if review else
            "checkpoint completion requires the exact attached runtime to be "
            "positively quiescent")
    required = "completed" if review else None
    if (required is not None and attempt["worker_disposition"] != required) \
            or (required is None and attempt["worker_disposition"] == "none"):
        raise ContractRefusal(
            "refused", "precondition",
            "review completion requires a completed worker disposition" if review else
            "checkpoint completion requires a terminal worker disposition")
    return attempt


def _fence(value, what):
    taken = boundaries.document(value, "a persisted assignment fence",
                                required=("intent", "fenced"))
    return taken


def _committed_fence(store, fence, what):
    held = _fence(fence, what)
    intent = attempts.adopt_finalization_record(held["intent"])
    operation_id = "attempt.finalize-quiescent:" + digest({
        "attempt_id": intent["attempt_id"],
        "assignment": intent["assignment"],
    }).split(":", 1)[1]
    signature = manager_signature("attempt.finalize-quiescent", {
        "attempt_id": intent["attempt_id"], "expect": intent["assignment"],
        "runtime_id": intent["runtime_id"],
        "worker_disposition": intent["worker_disposition"],
        "authority_operation_id": intent["authority_operation_id"],
        "reason": intent["reason"]})
    found, record = store.replay(operation_id, signature,
                                 kind="attempt.finalize-quiescent")
    if not found or record != intent:
        raise ContractRefusal("integrity", "schema",
                              f"{what} has no exact committed manager decision")
    return held, intent


def _current_fence(store, attempt, fence, what):
    held, intent = _committed_fence(store, fence, what)
    assignment = intent["assignment"]
    current = {"participant": attempt["assignment_participant"],
               "generation": attempt["assignment_generation"],
               "work_ref": {"work_id": attempt["work_id"],
                            "authority_uuid": attempt["authority_uuid"]}}
    if intent["attempt_id"] != attempt["runtime_attempt_id"] \
            or intent["runtime_id"] != attempt["runtime_id"] \
            or intent["worker_disposition"] != attempt["worker_disposition"] \
            or assignment != current:
        raise ContractRefusal("integrity", "schema",
                              f"{what} is not the current attempt's committed fence")
    return held


def _review_result(value):
    taken = boundaries.document(
        value, "a frozen review result",
        required=("attempt_id", "result_id", "disposition", "manifest_digest",
                  "freeze_operation_id", "frozen_at", "artifacts"))
    for member in ("attempt_id", "result_id", "manifest_digest",
                   "freeze_operation_id"):
        boundaries.identity(taken[member], f"a frozen review result's {member}")
    boundaries.instant(taken["frozen_at"], "a frozen review result's frozen_at")
    if taken["disposition"] != "completed":
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires a completed frozen result")
    if type(taken["artifacts"]) is not list:
        raise ContractRefusal("integrity", "schema",
                              "a frozen review result's artifacts is a list")
    names = []
    for artifact in taken["artifacts"]:
        held = boundaries.document(
            artifact, "a frozen review artifact",
            required=("output_name", "artifact_id", "media_type", "bytes",
                      "content_digest", "locator"))
        boundaries.identity(held["output_name"], "a frozen review output name")
        names.append(held["output_name"])
    if not {"findings", "logs"}.issubset(names):
        raise ContractRefusal(
            "refused", "precondition",
            "a review verdict requires separately frozen findings and logs outputs")
    return taken


def create_line(store, *, source, declared_base, profile,
                authority_uuid, work_id):
    """Create or recover the one persistent line for Authority and Work."""
    boundaries.text(authority_uuid, "a line's authority UUID")
    boundaries.identity(work_id, "a line's Work identity")
    boundaries.text(declared_base, "a line's declared base")
    storage = _storage(store)
    profile_name = _profile(profile, ("materialize", "validate"))
    if type(source) is not source_boundary.NominatedSource:
        raise ContractRefusal("integrity", "schema",
                              "a line source is a manager-nominated source")
    manager_signature("review-line.create.prepare", {
        "storage": storage, "source_path": source.place,
        "source_device": source.device, "source_inode": source.inode,
        "declared_base": declared_base, "profile_name": profile_name,
        "authority_uuid": authority_uuid, "work_id": work_id})
    line_id = _id("line", {"authority_uuid": authority_uuid,
                           "work_id": work_id})
    path = _line_place(storage, line_id, source.place)
    expected = (profile_name, declared_base, source.place, source.device,
                source.inode, path)
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = connection.execute(
            "SELECT * FROM review_lines WHERE line_id = ?", (line_id,)).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO review_lines (line_id, authority_uuid, work_id, "
                "profile_name, declared_base, source_path, source_device, "
                "source_inode, line_path, line_device, line_inode, state, "
                "revision, current_checkpoint_id, created_at) VALUES (?, ?, ?, "
                "?, ?, ?, ?, ?, ?, NULL, NULL, 'materializing', 0, NULL, ?)",
                (line_id, authority_uuid, work_id, profile_name, declared_base,
                 source.place, source.device, source.inode, path, store._now()))
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    held = line_of(store, line_id)
    recorded = (held["profile_name"], held["declared_base"],
                held["source_path"], held["source_device"],
                held["source_inode"], held["line_path"])
    if recorded != expected:
        raise ContractRefusal(
            "refused", "operation-collision",
            "this Authority and Work already own a line under different immutable operands")
    if held["state"] != "materializing":
        operands = {member: held[member] for member in (
            "line_id", "authority_uuid", "work_id", "profile_name",
            "declared_base", "source_path", "source_device", "source_inode",
            "line_path", "line_device", "line_inode")}
        signature = manager_signature("review-line.create", operands)
        found, result = store.replay("review-line.create:" + line_id,
                                     signature, kind="review-line.create")
        if found:
            _validate_line_object(held)
            return result
        raise ContractRefusal("integrity", "schema",
                              "a materialized line has no committed creation operation")
    materialized = profile.materialize(source.place, path, declared_base)
    if type(materialized) is not dict or set(materialized) != {
            "profile", "base", "head"} or materialized["profile"] != profile_name \
            or materialized["base"] != declared_base:
        raise ContractRefusal("integrity", "schema",
                              "line materialization returned malformed evidence")
    boundaries.text(materialized["head"], "a materialized line head")
    device, inode = _object(path, "the materialized development line")
    operands = {"line_id": line_id, "authority_uuid": authority_uuid,
                "work_id": work_id, "profile_name": profile_name,
                "declared_base": declared_base, "source_path": source.place,
                "source_device": source.device, "source_inode": source.inode,
                "line_path": path, "line_device": device, "line_inode": inode}
    signature = manager_signature("review-line.create", operands)

    def act(connection):
        current = line_of(store, line_id)
        if current["state"] != "materializing":
            raise ContractRefusal("integrity", "schema",
                                  "line materialization changed state before completion")
        if _object(path, "the materialized development line") != (device, inode):
            raise ContractRefusal("runtime-observation", "identity-mismatch",
                                  "the materialized development line changed before publication")
        workspaces._provision_line_access(
            path, (device, inode), workspaces.configured_workspace_group(store).gid)
        connection.execute(
            "UPDATE review_lines SET line_device = ?, line_inode = ?, "
            "state = 'idle' WHERE line_id = ? AND state = 'materializing'",
            (device, inode, line_id))
        return {"line_id": line_id, "state": "idle", "revision": 0,
                "path": path}

    result = store.transact("review-line.create:" + line_id,
                            "review-line.create", signature, act)
    _validate_line_object(line_of(store, line_id))
    return result


def grant_writer(store, *, line_id, attempt_id, generation, worker_id, profile,
                 based_checkpoint_id=None):
    """Attach exactly one generation-fenced writer to the durable line."""
    profile_name = _profile(profile, ("validate",))
    boundaries.identity(worker_id, "a writer worker identity")
    if based_checkpoint_id is not None:
        boundaries.identity(based_checkpoint_id, "a based checkpoint identity")
    line = line_of(store, line_id)
    if line["state"] == "materializing":
        raise ContractRefusal("refused", "precondition",
                              "the development line is still materializing")
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    _validate_line_object(line)
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and writer profile do not match")
    writer_id = _id("writer", {"line_id": line_id, "attempt_id": attempt_id,
                               "generation": generation})
    operands = {"writer_id": writer_id, "line_id": line_id,
                "attempt_id": attempt_id, "generation": generation,
                "worker_id": worker_id, "profile_name": profile_name,
                "participant": assignment["participant"],
                "principal": assignment["principal"],
                "based_checkpoint_id": based_checkpoint_id}
    signature = manager_signature("review-line.grant-writer", operands)
    operation_id = "review-line.grant-writer:" + writer_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.grant-writer")
    if found:
        return result
    if line["state"] == "idle":
        if based_checkpoint_id is not None:
            raise ContractRefusal("refused", "precondition",
                                  "the first writer is not based on a checkpoint")
    elif line["state"] == "correction-ready":
        if based_checkpoint_id != line["current_checkpoint_id"]:
            raise ContractRefusal("stale-assignment", "generation",
                                  "a correction writer must name the current checkpoint")
        checkpoint = checkpoint_of(store, based_checkpoint_id)
        if checkpoint["line_id"] != line_id or checkpoint["state"] != "frozen":
            raise ContractRefusal("integrity", "schema",
                                  "a correction checkpoint is not this line's frozen checkpoint")
        profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    else:
        raise ContractRefusal("refused", "precondition",
                              f"line state {line['state']!r} does not admit a writer")

    def act(connection):
        current = line_of(store, line_id)
        if current["state"] not in ("idle", "correction-ready"):
            raise ContractRefusal("refused", "precondition",
                                  "the line acquired another active attachment")
        current_assignment = assignment_of(store, attempt_id)
        _same_assignment(current_assignment, current, generation)
        if (current_assignment != assignment
                or current["state"] != line["state"]
                or current["current_checkpoint_id"] != line["current_checkpoint_id"]):
            raise ContractRefusal("stale-assignment", "generation",
                                  "writer admission changed after its checkpoint validation")
        _validate_line_object(current)
        workspaces._prove_line_access(
            current["line_path"], (current["line_device"], current["line_inode"]),
            workspaces.configured_workspace_group(store).gid)
        now = store._now()
        connection.execute(
            "INSERT INTO line_writers (writer_id, line_id, runtime_attempt_id, "
            "assignment_generation, worker_id, participant, principal, "
            "based_checkpoint_id, state, granted_at) VALUES (?, ?, ?, ?, ?, ?, "
            "?, ?, 'active', ?)",
            (writer_id, line_id, attempt_id, generation, worker_id,
             assignment["participant"], assignment["principal"],
             based_checkpoint_id, now))
        connection.execute("UPDATE review_lines SET state = 'writing' "
                           "WHERE line_id = ?", (line_id,))
        return {"writer_id": writer_id, "line_id": line_id,
                "generation": generation, "state": "active"}

    return store.transact(operation_id,
                          "review-line.grant-writer", signature, act)


def record_progress(store, *, writer_id, generation, sequence, document):
    boundaries.generation(generation, "a progress assignment generation")
    boundaries.generation(sequence, "a progress sequence")
    body = canonical_text(document)
    writer = writer_of(store, writer_id)
    if writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "progress belongs to the active writer generation")
    operands = {"writer_id": writer_id, "generation": generation,
                "sequence": sequence, "document": document}
    signature = manager_signature("review-line.progress", operands)
    operation_id = f"review-line.progress:{writer_id}:{sequence}"
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.progress")
    if found:
        return result

    def act(connection):
        if writer_of(store, writer_id)["state"] != "active":
            raise ContractRefusal("stale-assignment", "generation",
                                  "the writer was revoked before progress arrived")
        connection.execute(
            "INSERT INTO line_progress (writer_id, sequence, "
            "assignment_generation, progress_digest, document, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (writer_id, sequence, generation, digest(document), body,
             store._now()))
        return {"writer_id": writer_id, "sequence": sequence,
                "progress_digest": digest(document)}

    return store.transact(operation_id,
                          "review-line.progress", signature, act)


def freeze_checkpoint(store, *, writer_id, generation, profile, port):
    """Revoke and authority-fence the quiescent writer before freezing."""
    profile_name = _profile(profile, ("freeze", "validate"))
    boundaries.generation(generation, "a checkpoint assignment generation")
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and checkpoint profile do not match")
    if writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "checkpoint completion names a stale writer generation")
    existing = store._connection.execute(
        "SELECT checkpoint_id FROM line_checkpoints WHERE writer_id = ?",
        (writer_id,)
    ).fetchone()
    if existing is None:
        revision = line["revision"] + 1
        checkpoint_id = _id("checkpoint", {"line_id": line["line_id"],
                                           "revision": revision})
    else:
        existing_id = boundaries.identity(
            existing["checkpoint_id"], "a persisted line checkpoint identity")
        held = checkpoint_of(store, existing_id)
        revision = held["revision"]
        checkpoint_id = held["checkpoint_id"]
        if held["state"] == "frozen":
            evidence = held["evidence"]
            operands = {"writer_id": writer_id, "generation": generation,
                        "checkpoint_id": checkpoint_id, "evidence": evidence,
                        "fence": held["fence"]}
            signature = manager_signature("review-line.freeze", operands)
            found, result = store.replay("review-line.freeze:" + checkpoint_id,
                                         signature, kind="review-line.freeze")
            if found:
                return result
    attempt = _quiescent_completed(store, writer["runtime_attempt_id"])
    if attempt["assignment_participant"] != getattr(port, "participant", None):
        raise ContractRefusal("refused", "capability",
                              "the writer fence session acts for another participant")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        current = writer_of(store, writer_id)
        found = connection.execute(
            "SELECT * FROM line_checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,)).fetchone()
        if found is None:
            if current["state"] != "active":
                raise ContractRefusal("refused", "precondition",
                                      "checkpoint preparation has no active writer")
            _quiescent_completed(store, current["runtime_attempt_id"])
            now = store._now()
            connection.execute(
                "UPDATE line_writers SET state = 'revoked', revoked_at = ?, "
                "revocation_reason = 'checkpoint' WHERE writer_id = ? "
                "AND state = 'active'", (now, writer_id))
            connection.execute(
                "INSERT INTO line_checkpoints (checkpoint_id, writer_id, line_id, revision, "
                "profile_name, state, path_set_digest, prepared_at) VALUES (?, ?, "
                "?, ?, ?, 'preparing', NULL, ?)",
                (checkpoint_id, writer_id, line["line_id"], revision,
                 profile_name, now))
            connection.execute("UPDATE review_lines SET state = 'freezing' "
                               "WHERE line_id = ?", (line["line_id"],))
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    checkpoint = checkpoint_of(store, checkpoint_id)
    if checkpoint["fence"] is None:
        fenced = _fence(attempts.finalize_quiescent_assignment(
            store, port, attempt_id=writer["runtime_attempt_id"],
            reason="review checkpoint writer completed"),
            "the checkpoint writer fence")
        fence_operands = {"checkpoint_id": checkpoint_id,
                          "writer_id": writer_id, "fence": fenced}
        fence_signature = manager_signature("review-line.fence-writer",
                                            fence_operands)

        def record_fence(connection):
            current = checkpoint_of(store, checkpoint_id)
            if current["state"] != "preparing" or current["fence"] is not None:
                raise ContractRefusal("integrity", "schema",
                                      "a checkpoint writer fence changed before recording")
            connection.execute(
                "UPDATE line_checkpoints SET fence = ?, fence_digest = ? "
                "WHERE checkpoint_id = ? AND state = 'preparing' AND fence IS NULL",
                (canonical_text(fenced), digest(fenced), checkpoint_id))
            return fenced

        store.transact("review-line.fence-writer:" + checkpoint_id,
                       "review-line.fence-writer", fence_signature,
                       record_fence)
        checkpoint = checkpoint_of(store, checkpoint_id)
    fenced = checkpoint["fence"]
    # THE PIN IS RE-PROVED HERE, AT THE CONSUMING BOUNDARY. W105982 candidate
    # review 2026-09-07 kept the reproduction: the early adapter gate runs
    # before sealing, retention, publication and an EXTERNAL Authority fence,
    # and a checkout directory replaced during that fence call reached
    # `profile.freeze` and was frozen as this line's checkpoint. Re-resolving
    # after the early walk cannot protect a read this far downstream, so the
    # object is proved again against the durable row immediately before the
    # profile is handed the path.
    #
    # THE ROW IS RE-READ RATHER THAN REUSED, because `line` was loaded before
    # the fence and a stale copy proves only that it once agreed with itself.
    # NO WRITER IS REQUIRED TO STILL BE ACTIVE: this runs after the checkpoint
    # legitimately revoked it, so the question asked here is about the LINE'S
    # object identity and nothing else -- which is also what keeps the
    # preparing/frozen replay paths working exactly as they did.
    line = _consumable_line(store, line["line_id"])
    evidence = profile.freeze(line["line_path"], line_id=line["line_id"],
                              revision=revision,
                              declared_base=line["declared_base"])
    required = {"profile", "base", "head", "tree", "paths",
                "path_set_digest", "reference"}
    if type(evidence) is not dict or set(evidence) != required \
            or evidence["profile"] != profile_name:
        raise ContractRefusal("integrity", "schema",
                              "checkpoint profile returned malformed evidence")
    evidence = _evidence(evidence)
    if evidence["base"] != line["declared_base"]:
        raise ContractRefusal("integrity", "digest",
                              "checkpoint evidence does not use the line's declared base")
    profile.validate(line["line_path"], evidence, current=True)
    checkpoint_digest = digest(evidence)
    operands = {"writer_id": writer_id, "generation": generation,
                "checkpoint_id": checkpoint_id, "evidence": evidence,
                "fence": fenced}
    signature = manager_signature("review-line.freeze", operands)

    def act(connection):
        checkpoint = checkpoint_of(store, checkpoint_id)
        if checkpoint["state"] == "preparing":
            now = store._now()
            connection.execute(
                "UPDATE line_checkpoints SET state = 'frozen', evidence = ?, "
                "checkpoint_digest = ?, base_object = ?, head_object = ?, "
                "tree_object = ?, path_set_digest = ?, reference_name = ?, "
                "frozen_at = ? WHERE checkpoint_id = ? AND state = 'preparing'",
                (canonical_text(evidence), checkpoint_digest, evidence["base"],
                 evidence["head"], evidence["tree"],
                 evidence["path_set_digest"], evidence["reference"], now,
                 checkpoint_id))
            connection.execute(
                "UPDATE review_lines SET state = 'review-ready', revision = ?, "
                "current_checkpoint_id = ? WHERE line_id = ?",
                (revision, checkpoint_id, line["line_id"]))
        return {"checkpoint_id": checkpoint_id, "line_id": line["line_id"],
                "revision": revision, "checkpoint_digest": checkpoint_digest,
                "evidence": evidence, "fence": fenced}

    return store.transact("review-line.freeze:" + checkpoint_id,
                          "review-line.freeze", signature, act)


def attach_review(store, *, checkpoint_id, attempt_id, generation,
                  reviewer_worker_id, profile):
    """Attach an independent reviewer to the exact current checkpoint."""
    profile_name = _profile(profile, ("validate",))
    boundaries.identity(reviewer_worker_id, "a reviewer worker identity")
    checkpoint = checkpoint_of(store, checkpoint_id)
    line = line_of(store, checkpoint["line_id"])
    if checkpoint["state"] != "frozen":
        raise ContractRefusal("integrity", "schema",
                              "a review attachment requires a frozen checkpoint")
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and review profile do not match")
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    producer = writer_of(store, checkpoint["writer_id"])
    if producer["line_id"] != line["line_id"]:
        raise ContractRefusal("integrity", "schema",
                              "a checkpoint writer belongs to another line")
    same = []
    if reviewer_worker_id == producer["worker_id"]:
        same.append("worker")
    if assignment["participant"] == producer["participant"]:
        same.append("participant")
    if assignment["principal"] == producer["principal"]:
        same.append("principal")
    if same:
        raise ContractRefusal("refused", "precondition",
                              "review is not independent at: " + ", ".join(same))
    attachment_id = _id("review", {"checkpoint_id": checkpoint_id,
                                   "attempt_id": attempt_id,
                                   "generation": generation})
    operands = {"attachment_id": attachment_id,
                "checkpoint_id": checkpoint_id, "attempt_id": attempt_id,
                "generation": generation, "reviewer_worker_id": reviewer_worker_id,
                "participant": assignment["participant"],
                "principal": assignment["principal"]}
    signature = manager_signature("review-line.attach-review", operands)
    operation_id = "review-line.attach-review:" + attachment_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.attach-review")
    if found:
        return result
    if line["state"] != "review-ready" \
            or line["current_checkpoint_id"] != checkpoint_id:
        raise ContractRefusal("refused", "precondition",
                              "review attaches only to the current review-ready checkpoint")
    if store._connection.execute(
            "SELECT 1 FROM line_writers WHERE line_id = ? AND state = 'active'",
            (line["line_id"],)).fetchone() is not None:
        raise ContractRefusal("refused", "precondition",
                              "read-only review cannot coexist with a writer")
    profile.validate(line["line_path"], checkpoint["evidence"], current=True)

    def act(connection):
        current = line_of(store, line["line_id"])
        if current["state"] != "review-ready" \
                or current["current_checkpoint_id"] != checkpoint_id:
            raise ContractRefusal("refused", "precondition",
                                  "the checkpoint acquired another attachment")
        connection.execute(
            "INSERT INTO review_attachments (attachment_id, line_id, "
            "checkpoint_id, runtime_attempt_id, assignment_generation, "
            "reviewer_worker_id, reviewer_participant, reviewer_principal, "
            "state, attached_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)",
            (attachment_id, line["line_id"], checkpoint_id, attempt_id,
             generation, reviewer_worker_id, assignment["participant"],
             assignment["principal"], store._now()))
        connection.execute("UPDATE review_lines SET state = 'reviewing' "
                           "WHERE line_id = ?", (line["line_id"],))
        return {"attachment_id": attachment_id, "checkpoint_id": checkpoint_id,
                "state": "active"}

    return store.transact(operation_id,
                          "review-line.attach-review", signature, act)


def _custodied_review(store, attempt, result):
    """A review whose output was TAKEN INTO CUSTODY, proved through its receipt.

    W110772, owner ruling M111752 and `FIRST-PROOF-PLAN.md`. The measured
    blocker: an ending that actually performs intake and retention leaves the
    output axis at `sealed`, and this precondition admitted only `frozen` -- so
    the very custody the lifecycle requires made the first verdict impossible.
    Two real proofs failed on it and nothing else was wrong with them.

    SEALED IS ADMITTED ONLY WITH THE RECEIPT THAT MADE IT SEALED, which is the
    whole difference between relaxing a check and moving it. `frozen` says the
    manager sealed the bytes; `sealed` says it also collected them, and the
    evidence for the second is the intake receipt, not the axis word. So the
    receipt is read from its owner and cross-bound to the exact frozen result:
    same attempt, same result id, same manifest digest, and every artifact the
    result declares present in it.

    AND THE RETENTION DECISIONS MUST EXIST. `authorize_cleanup` refuses without
    them and the whole point of admitting `sealed` is that this attempt went
    through custody; an attempt sealed with nothing retained is one whose
    material nobody decided about, which is not evidence a verdict may rest on.

    THIS IS NOT A TRANSITION. Nothing here moves `sealed` back to `frozen` or
    writes any axis; the axis is read and the receipt is what is believed.
    """
    manifest = manifests.load_manifest(store, result["manifest_digest"], "resultManifest")
    if manifest is None:
        raise ContractRefusal("refused", "precondition",
                              "the custodied review has no retained result manifest")
    assignment = {"participant": attempt["assignment_participant"],
                  "generation": attempt["assignment_generation"],
                  "work_ref": {"work_id": attempt["work_id"], "authority_uuid": attempt["authority_uuid"]}}
    artifacts = [dict(output_name=one["name"], **one["artifact"])
                 for one in manifest["outputs"] if one["artifact"] is not None]
    if manifest["result_id"] != result["result_id"] \
            or manifest["disposition"] != result["disposition"] \
            or manifest["assignment_ref"] != assignment \
            or manifest["input_manifest_digest"] != attempt["input_digest"] \
            or manifest["policy_digest"] != attempt["policy_digest"] \
            or manifest["freeze_operation"]["operation_id"] != result["freeze_operation_id"] \
            or sorted(artifacts, key=lambda one: one["output_name"]) != result["artifacts"]:
        raise ContractRefusal("integrity", "digest",
                              "the retained review manifest differs from its frozen result and assignment")
    receipt = intake.intake_receipt_of(store, attempt["runtime_attempt_id"])
    if receipt is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt['runtime_attempt_id'])} reports "
            f"sealed output and this manager holds no intake receipt for it; "
            f"the axis is a claim and the receipt is the evidence")
    if receipt["attempt_id"] != attempt["runtime_attempt_id"] \
            or receipt["result_id"] != result["result_id"] \
            or receipt["manifest_digest"] != result["manifest_digest"]:
        raise ContractRefusal(
            "integrity", "schema",
            "the intake receipt and the frozen review result name different "
            "results; a verdict rests on one account of one output")
    if receipt["custody"] != "accepted":
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires accepted intake custody")
    collected = {one["artifact_id"] for one in receipt["artifacts"]}
    declared = {one["artifact_id"] for one in result["artifacts"]}
    if not declared <= collected:
        raise ContractRefusal(
            "refused", "precondition",
            f"the frozen review result declares "
            f"{', '.join(sorted(name_value(one) for one in declared - collected))} "
            f"and the intake receipt collected neither; a verdict rests on "
            f"material this manager took custody of")
    measured = {(one["artifact_id"], one["bytes"], one["content_digest"])
                for one in result["artifacts"]}
    received = {(one["artifact_id"], one["bytes"], one["content_digest"])
                for one in receipt["artifacts"]}
    if measured != received or len(receipt["artifacts"]) != len(result["artifacts"]):
        raise ContractRefusal("integrity", "digest",
                              "review intake artifacts differ from the frozen measurements")
    retained = intake.retentions_of(store, attempt["runtime_attempt_id"])
    if {one["artifact_id"] for one in retained if one["disposition"] == "retain"} != declared:
        raise ContractRefusal(
            "refused", "precondition",
            "every frozen review artifact requires its retained decision")
    return receipt


def _cleaned_review(store, attachment, attempt, result, verdict):
    """Historical completion is exact committed evidence, never an axis alone."""
    proved = verdict_of(store, verdict["verdict_id"])
    operation_id = VERDICT_KIND + ":" + attachment["attachment_id"]
    if _committed_act(store, VERDICT_KIND, operation_id, "the historical verdict") \
            != _committed_operands(store, VERDICT_KIND, operation_id, "the historical verdict"):
        raise ContractRefusal("integrity", "schema",
                              "historical verdict answer differs from its committed operands")
    if proved != verdict or review_of(store, attachment["attachment_id"]) != attachment \
            or attachment["state"] != "ended" \
            or attempt["runtime_id"] is None \
            or attempt["worker_disposition"] != "completed" \
            or attempt["output"] != "sealed" \
            or attempt["cleanup"] != "retained" \
            or result != verdict["review_result"]:
        raise ContractRefusal("refused", "precondition",
                              "historical review completion requires its ended verdict and retained cleanup")
    for member in ("attachment_id", "line_id", "checkpoint_id", "reviewer_worker_id",
                   "reviewer_participant", "reviewer_principal"):
        if attachment[member] != verdict[member]:
            raise ContractRefusal("integrity", "schema",
                                  "historical review verdict belongs to another attachment")
    if attachment["assignment_generation"] != verdict["review_assignment_generation"] \
            or attempt["assignment_generation"] != verdict["review_assignment_generation"] \
            or attempt["assignment_participant"] != verdict["reviewer_participant"] \
            or attempt["assignment_principal"] != verdict["reviewer_principal"]:
        raise ContractRefusal("integrity", "schema",
                              "historical review verdict belongs to another assignment")
    fence = _current_fence(store, attempt, verdict["review_fence"],
                           "the historical review fence")
    receipt = _custodied_review(store, attempt, result)
    retained = intake.retentions_of(store, attempt["runtime_attempt_id"])
    policies = {one["retention_policy_digest"] for one in retained}
    if len(policies) != 1:
        raise ContractRefusal("refused", "precondition",
                              "historical review cleanup requires one exact retention policy")
    policy = next(iter(policies))
    operation = intake.destroy_operation(attempt, receipt["receipt_digest"], policy)
    record = store.operation_record(operation["operation_id"])
    if record is None or record["kind"] != "runtime.destroy" or record["state"] != "committed":
        raise ContractRefusal("refused", "precondition",
                              "historical review has no committed positive cleanup")
    signature = manager_signature("runtime.destroy", {
        "attempt_id": attempt["runtime_attempt_id"], "expect": fence["intent"]["assignment"],
        "runtime_id": attempt["runtime_id"], "intake_receipt_digest": receipt["receipt_digest"],
        "retention_policy_digest": policy})
    found, cleaned = store.replay(operation["operation_id"], signature, kind="runtime.destroy")
    cleaned = boundaries.document(cleaned, "a historical review cleanup",
        required=("attempt_id", "cleanup", "state", "why", "kept", "operation", "directory_custody"))
    if not found or cleaned["attempt_id"] != attempt["runtime_attempt_id"] \
            or cleaned["cleanup"] != "retained" or cleaned["state"] != "absent" \
            or cleaned["operation"] != operation \
            or cleaned["kept"] != sorted(one["artifact_id"] for one in retained) \
            or cleaned["directory_custody"] is None:
        raise ContractRefusal("refused", "precondition",
                              "historical review cleanup does not prove positive absence and retained custody")
    adopted = {which: custody.historical_directory_custody(store, attempt["runtime_attempt_id"], which)
               for which in ("result", "workspace")}
    if cleaned["directory_custody"] != adopted:
        raise ContractRefusal("integrity", "schema",
                              "historical review cleanup differs from its committed directory custody")


def _completed_review(store, attachment, *, verdict=None):
    attempt = _attempt(store, attachment["runtime_attempt_id"])
    historical = attempt["execution_runtime"] == "destroyed" and verdict is not None
    if not historical:
        attempt = _quiescent_completed(store, attachment["runtime_attempt_id"], review=True)
    # THE REVIEWER'S OWN VERIFICATION AXIS IS NO LONGER A PREREQUISITE, and
    # that is an owner ruling rather than a relaxation this module chose.
    # M111752: for this milestone the implementer runs the ordinary required
    # tests and an independent reviewer assesses the checkpoint; there is no
    # separate producer that could write `passed` into a REVIEW attempt's axis,
    # so requiring one made every honest review unsettleable. The axis stays
    # exactly as it is -- nothing here writes it, resets it, or reinterprets a
    # `failed` or `unable` value somebody else recorded.
    #
    # WHAT REPLACES IT IS NOT NOTHING. A verdict still requires the exact
    # attached runtime positively quiescent, a `completed` worker disposition,
    # a frozen result naming this attempt, separately frozen findings and logs,
    # and -- below -- custody evidence when the output has been sealed. Custody
    # alone never proves a review happened; it proves the output a review is
    # about is one this manager holds.
    if attempt["output"] not in ("frozen", "sealed"):
        raise ContractRefusal(
            "refused", "precondition",
            f"a review verdict requires frozen or sealed output and this "
            f"attempt reports {name_value(attempt['output'])}")
    result = output.frozen_output_of(store, attachment["runtime_attempt_id"])
    if result is None:
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires a frozen review result")
    result = _review_result(result)
    if result["attempt_id"] != attachment["runtime_attempt_id"]:
        raise ContractRefusal("integrity", "schema",
                              "the frozen review result names another attempt")
    if attempt["output"] == "sealed":
        _custodied_review(store, attempt, result)
    if historical:
        _cleaned_review(store, attachment, attempt, result, verdict)
    return attempt, result


def record_verdict(store, *, attachment_id, disposition, profile, port):
    """Bind one disposition to all immutable checkpoint and reviewer evidence."""
    profile_name = _profile(profile, ("validate",))
    if disposition not in DISPOSITIONS:
        raise ContractRefusal("integrity", "schema",
                              f"a review disposition is one of {DISPOSITIONS!r}")
    attachment = _attachment(store, attachment_id)
    checkpoint = checkpoint_of(store, attachment["checkpoint_id"])
    line = line_of(store, attachment["line_id"])
    if checkpoint["line_id"] != line["line_id"] \
            or checkpoint["state"] != "frozen":
        raise ContractRefusal("integrity", "schema",
                              "a verdict attachment does not name its line's frozen checkpoint")
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and verdict profile do not match")
    if attachment["state"] == "active" and (
            line["state"] != "reviewing"
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]):
        raise ContractRefusal("refused", "precondition",
                              "a verdict applies only to the active current review")
    if _attempt(store, attachment["runtime_attempt_id"])["execution_runtime"] == "destroyed":
        verdict = verdict_of(store, _id("verdict", {"attachment_id": attachment_id,
                                                    "disposition": disposition}))
        attempt, _ = _completed_review(store, attachment, verdict=verdict)
        if attempt["assignment_participant"] != getattr(port, "participant", None):
            raise ContractRefusal("refused", "capability",
                                  "the review fence session acts for another participant")
        return _committed_act(store, VERDICT_KIND, VERDICT_KIND + ":" + attachment_id,
                              "the historical review verdict")
    attempt, review_result = _completed_review(store, attachment)
    if attempt["assignment_participant"] != getattr(port, "participant", None):
        raise ContractRefusal("refused", "capability",
                              "the review fence session acts for another participant")
    if attachment["state"] == "active":
        profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    review_fence = _fence(attempts.finalize_quiescent_assignment(
        store, port, attempt_id=attachment["runtime_attempt_id"],
        reason="independent checkpoint review completed"),
        "the checkpoint review fence")
    _current_fence(store, attempt, review_fence,
                   "the checkpoint review fence")
    evidence = checkpoint["evidence"]
    verdict_id = _id("verdict", {"attachment_id": attachment_id,
                                 "disposition": disposition})
    operands = {"verdict_id": verdict_id, "authority_uuid": line["authority_uuid"],
                "work_id": line["work_id"], "line_id": line["line_id"],
                "checkpoint_id": checkpoint["checkpoint_id"],
                "checkpoint_digest": checkpoint["checkpoint_digest"],
                "revision": checkpoint["revision"], "base": evidence["base"],
                "head": evidence["head"], "tree": evidence["tree"],
                "path_set_digest": evidence["path_set_digest"],
                "attachment_id": attachment_id,
                "review_generation": attachment["assignment_generation"],
                "reviewer_worker_id": attachment["reviewer_worker_id"],
                "reviewer_participant": attachment["reviewer_participant"],
                "reviewer_principal": attachment["reviewer_principal"],
                "disposition": disposition,
                "review_result": review_result,
                "review_result_digest": digest(review_result),
                "review_fence": review_fence,
                "review_fence_digest": digest(review_fence)}
    signature = manager_signature("review-line.verdict", operands)
    operation_id = "review-line.verdict:" + attachment_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.verdict")
    if found:
        return result
    if attachment["state"] != "active" or line["state"] != "reviewing" \
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ContractRefusal("refused", "precondition",
                              "a verdict applies only to the active current review")
    def act(connection):
        _completed_review(store, attachment)
        current_attachment = _attachment(store, attachment_id)
        current_line = line_of(store, line["line_id"])
        if current_attachment["state"] != "active":
            raise ContractRefusal("refused", "precondition",
                                  "the review attachment has already ended")
        if current_attachment["line_id"] != current_line["line_id"] \
                or current_attachment["checkpoint_id"] != checkpoint["checkpoint_id"] \
                or current_line["state"] != "reviewing" \
                or current_line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
            raise ContractRefusal("integrity", "schema",
                                  "the active review no longer names the current checkpoint")
        now = store._now()
        connection.execute(
            "INSERT INTO checkpoint_verdicts (verdict_id, line_id, checkpoint_id, "
            "attachment_id, authority_uuid, work_id, review_assignment_generation, "
            "reviewer_worker_id, reviewer_participant, reviewer_principal, "
            "disposition, checkpoint_digest, revision, base_object, head_object, "
            "tree_object, path_set_digest, review_result, review_result_digest, "
            "review_fence, review_fence_digest, recorded_at) VALUES (?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (verdict_id, line["line_id"], checkpoint["checkpoint_id"],
             attachment_id, line["authority_uuid"], line["work_id"],
             attachment["assignment_generation"], attachment["reviewer_worker_id"],
             attachment["reviewer_participant"], attachment["reviewer_principal"],
             disposition, checkpoint["checkpoint_digest"], checkpoint["revision"],
             evidence["base"], evidence["head"], evidence["tree"],
             evidence["path_set_digest"], canonical_text(review_result),
             digest(review_result), canonical_text(review_fence),
             digest(review_fence), now))
        connection.execute("UPDATE review_attachments SET state = 'ended', "
                           "ended_at = ? WHERE attachment_id = ?", (now, attachment_id))
        next_state = {"accepted": "accepted", "changes-requested":
                      "correction-ready", "rejected": "rejected"}[disposition]
        connection.execute("UPDATE review_lines SET state = ? WHERE line_id = ?",
                           (next_state, line["line_id"]))
        if disposition == "accepted":
            connection.execute(
                "INSERT INTO integration_eligibility (checkpoint_id, line_id, "
                "verdict_id, eligible_at) VALUES (?, ?, ?, ?)",
                (checkpoint["checkpoint_id"], line["line_id"], verdict_id, now))
        return dict(operands)

    return store.transact(operation_id,
                          "review-line.verdict", signature, act)


def integration_checkpoint(store, line_id):
    line = line_of(store, line_id)
    eligibility_row = store._connection.execute(
        "SELECT * FROM integration_eligibility WHERE line_id = ?", (line_id,)
    ).fetchone()
    if eligibility_row is None:
        return None
    owned = boundaries.row(eligibility_row, "persisted integration eligibility",
                           schema.INTEGRATION_ELIGIBILITY_COLUMNS)
    checkpoint = checkpoint_of(store, owned["checkpoint_id"])
    evidence = checkpoint["evidence"]
    if owned["line_id"] != line_id or line["state"] != "accepted" \
            or checkpoint["line_id"] != line_id \
            or checkpoint["state"] != "frozen" \
            or checkpoint["checkpoint_id"] != line["current_checkpoint_id"]:
        raise ContractRefusal("integrity", "schema",
                              "integration eligibility is not the line's accepted checkpoint")
    verdict = _verdict_row(store, owned["verdict_id"])
    if verdict is None:
        raise ContractRefusal("integrity", "schema",
                              "integration eligibility has no exact accepted verdict")
    verdict["review_result"] = _review_result(
        json.loads(verdict["review_result"]))
    verdict["review_fence"] = _fence(
        json.loads(verdict["review_fence"]), "a persisted review fence")
    recorded = (verdict["line_id"], verdict["checkpoint_id"],
                verdict["authority_uuid"], verdict["work_id"],
                verdict["disposition"], verdict["checkpoint_digest"],
                verdict["revision"], verdict["base_object"],
                verdict["head_object"], verdict["tree_object"],
                verdict["path_set_digest"])
    expected = (line_id, checkpoint["checkpoint_id"], line["authority_uuid"],
                line["work_id"], "accepted", checkpoint["checkpoint_digest"],
                checkpoint["revision"], evidence["base"], evidence["head"],
                evidence["tree"], evidence["path_set_digest"])
    if recorded != expected \
            or verdict["review_result_digest"] != digest(verdict["review_result"]) \
            or verdict["review_fence_digest"] != digest(verdict["review_fence"]):
        raise ContractRefusal("integrity", "digest",
                              "integration eligibility has no exact accepted verdict")
    verdict = verdict_of(store, verdict["verdict_id"])
    attachment = review_of(store, verdict["attachment_id"])
    attempt, current_result = _completed_review(store, attachment, verdict=verdict)
    _current_fence(store, attempt, verdict["review_fence"],
                   "the persisted review fence")
    if attachment["state"] != "ended" \
            or attachment["assignment_generation"] != verdict["review_assignment_generation"] \
            or attachment["reviewer_worker_id"] != verdict["reviewer_worker_id"] \
            or attachment["reviewer_participant"] != verdict["reviewer_participant"] \
            or attachment["reviewer_principal"] != verdict["reviewer_principal"] \
            or attempt["assignment_generation"] != verdict["review_assignment_generation"] \
            or current_result != verdict["review_result"]:
        raise ContractRefusal(
            "integrity", "schema",
            "integration eligibility is not bound to its completed review attempt")
    return {"line_id": line_id, "checkpoint_id": owned["checkpoint_id"],
            "verdict_id": owned["verdict_id"],
            "checkpoint_digest": checkpoint["checkpoint_digest"],
            "evidence": checkpoint["evidence"]}


def audit_checkpoint(store, checkpoint_id, profile):
    """Re-resolve an older immutable checkpoint without requiring current HEAD."""
    profile_name = _profile(profile, ("validate",))
    checkpoint = checkpoint_of(store, checkpoint_id)
    if checkpoint["state"] != "frozen":
        raise ContractRefusal("refused", "precondition",
                              "only a frozen checkpoint is audit evidence")
    line = line_of(store, checkpoint["line_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and audit profile do not match")
    return profile.validate(line["line_path"], checkpoint["evidence"],
                            current=False)


def line_status(store, line_id, storage_usage):
    """Operator status including externally metered accumulated line storage."""
    boundaries.capability(storage_usage,
                          "the deployment's development-line storage meter")
    line = line_of(store, line_id)
    usage = storage_usage(line["line_path"])
    if (type(usage) is not dict or set(usage) != {"bytes", "entries"}
            or any(type(value) is not int or type(value) is bool or value < 0
                   for value in usage.values())):
        raise ContractRefusal("integrity", "schema",
                              "line storage usage is exact non-negative bytes and entries")
    return {"line_id": line_id, "state": line["state"],
            "revision": line["revision"],
            "current_checkpoint_id": line["current_checkpoint_id"],
            "storage": dict(usage)}


def _writer_grant(store, writer_id, line_id, generation):
    writer = writer_of(store, writer_id)
    line = line_of(store, line_id)
    return (writer["line_id"] == line_id and writer["state"] == "active"
            and writer["assignment_generation"] == generation
            and line["state"] == "writing")


def _writer_access(store, writer_id, generation, roots, gid, labels):
    """Bind actual launch roots to the current durable writer and assignment."""
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    assignment = assignment_of(store, writer["runtime_attempt_id"])
    _same_assignment(assignment, line, generation)
    if (not _writer_grant(store, writer_id, line["line_id"], generation)
            or writer["participant"] != assignment["participant"]
            or writer["principal"] != assignment["principal"]
            or any(labels.get(name) != value for name, value in assignment.items())
            or gid != workspaces.configured_workspace_group(store).gid):
        raise ContractRefusal("stale-assignment", "generation",
                              "the launch is not this development line's current writer assignment")
    _validate_line_object(line)
    expected = workspaces.line_assignment_workspace(
        _storage(store), writer["runtime_attempt_id"], line["line_path"],
        (line["line_device"], line["line_inode"]))
    if dict(roots) != dict(expected):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the actual launch roots differ from the durable writer line")
    return workspaces._prove_line_access(
        roots["workspace"], (line["line_device"], line["line_inode"]), gid)


def consumption_subject(store, *, attempt_id, generation):
    """WHICH line this attempt may be consumed from, resolved from durable
    state and from nothing else.

    W105982. The defect this exists for is a subject defect rather than a
    permission one: `custody._derived_root` addresses `S/<attempt>/workspace`
    while a writer attempt was mounted at `S/.baton-review-lines/<line>/
    checkout`, so an ordinary receipt was accurate about directories that had
    nothing to do with the tree the manager actually read. Naming the right
    tree is therefore the whole of this function.

    RESOLVED, NOT ACCEPTED. Nothing here takes a host path from a caller and
    nothing consults an adapter's held root map -- `AllocatedRoots` disclaims
    being durable authority in its own words, and a map composed at launch is
    a memory of what was true then. The chain is entirely inside the control
    store: this attempt's ACTIVE writer at this exact generation, that writer's
    line, the assignment the line is bound to, and the object identity the line
    recorded when it was materialized.

    THE CUSTODY SIBLING IS DERIVED THE SAME WAY. It is the parent of the line
    checkout plus `custody/<attempt>`, which is what `OciAdapter._home` reaches
    by taking the dirname of a mounted workspace -- the difference being that
    this one is computed from the RECORDED line path, so a comparison against
    the adapter's own answer is a comparison of two independent derivations
    rather than of one value with itself.

    EXCLUSIVITY IS ALREADY THE SCHEMA'S. `line_one_active_writer` makes a
    second active writer per line impossible, so this asks the question it can
    actually answer -- which line is THIS attempt's -- and does not re-count
    what the store cannot let happen. The caller is expected to ask again after
    its filesystem proof: this answers what is true now, and the interval
    between two reads is exactly where a fence belongs.
    """
    boundaries.identity(attempt_id, "a runtime attempt identity")
    boundaries.generation(generation, "an assignment generation")
    rows = store._connection.execute(
        "SELECT writer_id FROM line_writers WHERE runtime_attempt_id = ? "
        "AND assignment_generation = ? AND state = 'active'",
        (attempt_id, generation)).fetchall()
    if len(rows) != 1:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} holds {len(rows)} active line "
            f"writers at generation {generation}; consumption names exactly "
            f"the one line a live writer was granted")
    # THE COLUMN IS NOT OWNED HERE. `writer_of` is the one crossing out of
    # this table and it owns the identity and the row; a second owner for the
    # same value is exactly what the boundary inventory refuses.
    writer = writer_of(store, rows[0]["writer_id"])
    line = line_of(store, writer["line_id"])
    if line["state"] != "writing":
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(line['line_id'])} is "
            f"{name_value(line['state'])}; only the line its own live writer "
            f"is still writing may be consumed for that writer's result")
    # EXCLUSIVITY IS NOT RE-ASKED HERE. `line_one_active_writer` is a UNIQUE
    # INDEX over `line_writers(line_id) WHERE state = 'active'`, so a second
    # active writer cannot exist to be counted -- and a count that can never
    # come back other than one is a boundary nobody reaches. The dependency is
    # not left implicit: a case pins that the schema carries the rule, so if it
    # ever stops, the gate says so.
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    # AND THE GRANT'S OWN IDENTITIES, which `_same_assignment` does not reach.
    # W105982 candidate review 2026-09-07: Authority, Work and generation can
    # all agree while the attempt's assignment names a different participant or
    # principal from the one the writer was granted to -- and the accepted
    # launch boundary `_writer_access` already requires both equalities, so a
    # consumption gate that did not would authorize a subject the launch would
    # have refused.
    if writer["participant"] != assignment["participant"] \
            or writer["principal"] != assignment["principal"]:
        raise ContractRefusal(
            "stale-assignment", "generation",
            "the granted writer and this attempt's current assignment name "
            "different participants or principals; consumption follows the "
            "grant rather than the row that happens to share its generation")
    _validate_line_object(line)
    home = os.path.dirname(line["line_path"].rstrip("/"))
    return {"attempt_id": attempt_id, "generation": generation,
            "writer_id": writer["writer_id"], "line_id": line["line_id"],
            "line_path": line["line_path"],
            "pinned": (line["line_device"], line["line_inode"]),
            "custody_path": os.path.join(home, "custody", attempt_id),
            "storage": _storage(store)}


def writer_boundary(store, *, writer_id, generation):
    """Compose the direct writable line mount for the active writer attempt."""
    boundaries.generation(generation, "an assignment generation")
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    if writer["state"] != "active" or writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "only the active writer generation mounts the line writable")
    assignment = assignment_of(store, writer["runtime_attempt_id"])
    _same_assignment(assignment, line, generation)
    _validate_line_object(line)
    nominated = source_boundary.nominate_source(line["source_path"])
    if (nominated.device, nominated.inode) != (line["source_device"],
                                               line["source_inode"]):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the nominated source pathname now names another object")
    roots = workspaces.line_assignment_workspace(
        _storage(store), writer["runtime_attempt_id"], line["line_path"],
        (line["line_device"], line["line_inode"]))
    roots = workspaces._granted_roots(
        roots, lambda: _writer_grant(store, writer_id,
                                     line["line_id"], generation),
        line_proof=lambda actual, gid, labels: _writer_access(
            store, writer_id, generation, actual, gid, labels))
    return {"roots": roots,
            "boundary": source_boundary.compose_runtime_storage_boundary(
                nominated, roots)}


def _review_grant(store, attachment_id, line_id, checkpoint_id):
    attachment = _attachment(store, attachment_id)
    line = line_of(store, line_id)
    return (attachment["line_id"] == line_id
            and attachment["checkpoint_id"] == checkpoint_id
            and attachment["state"] == "active"
            and line["state"] == "reviewing"
            and line["current_checkpoint_id"] == checkpoint_id)


def review_boundary(store, *, attachment_id, profile):
    """Compose read-only current-checkpoint input and separate review output."""
    profile_name = _profile(profile, ("validate",))
    attachment = _attachment(store, attachment_id)
    line = line_of(store, attachment["line_id"])
    if attachment["state"] != "active" or line["state"] != "reviewing":
        raise ContractRefusal("refused", "precondition",
                              "only the active review attachment mounts a checkpoint")
    if store._connection.execute(
            "SELECT 1 FROM line_writers WHERE line_id = ? AND state = 'active'",
            (line["line_id"],)).fetchone() is not None:
        raise ContractRefusal("integrity", "schema",
                              "a read-only review checkpoint has an active writer")
    checkpoint = checkpoint_of(store, attachment["checkpoint_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and review-mount profile do not match")
    if checkpoint["line_id"] != line["line_id"] \
            or checkpoint["state"] != "frozen" \
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ContractRefusal("integrity", "schema",
                              "the review mount is not the line's current checkpoint")
    profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    roots = workspaces.adopted_assignment_workspace(
        _storage(store), attachment["runtime_attempt_id"])
    roots = workspaces._granted_roots(
        roots, lambda: _review_grant(
            store, attachment_id, line["line_id"], checkpoint["checkpoint_id"]))
    nominated = source_boundary.nominate_source(line["line_path"])
    if (nominated.device, nominated.inode) != (line["line_device"],
                                               line["line_inode"]):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the review checkpoint line is no longer its recorded object")
    return {"roots": roots,
            "boundary": source_boundary.compose_runtime_storage_boundary(
                nominated, roots)}
