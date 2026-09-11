"""The integration RESULT: one submission reconciled with one target snapshot.

W131409 replacement slice P, INTEGRATION-CONTRACT-v1 sections 1 to 3.

TWO IMMUTABLE OBJECTS, AND THIS OWNS THE SECOND. An eligible submission is the
producer's ORIGINAL proposal on its ORIGINAL base, with its own frozen result,
its own tests and its own independent review. Nothing here rewrites any of
that: the producer's line, checkpoint, verdict, proposal and base appear in
every record below as references it reads and never touches. An integration
RESULT is a different immutable candidate -- that submission reconciled with
one exact target snapshot -- and it earns its own content, its own tests, its
own review and approval, and its own derived Authority proposal.

AN OLD SUBMISSION BASE IS ALLOWED HERE, and that is the whole point of the
replacement direction: a producer does not chase a target that moved under it.
What is NOT relaxed is the RESULT's own target. A stale result still refuses
before import, and removing that guard is not this design.

THREE LESSONS FROM THE SUPERSEDED SLICE ARE BUILT IN RATHER THAN BOLTED ON.
A committed INTENT is not a settled OUTCOME, so a preparing record RESUMES from
its own recorded operands instead of replaying as though it had finished. The
operands an act is signed under are recovered from the committed intent before
any mutable state is consulted, so an exact retry signs identically. And the
public readers bind a materialized row to the journal by RE-DERIVING its
identity from the row's own immutable operands -- row existence, or agreement
between two documents a caller controls, is not a binding.
"""

import json

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import schema
from .git_profile import PROFILE_NAME, PROFILE_VERSION
from .store import integration_signature

__all__ = ["EVIDENCE_KIND", "INTENT_KIND", "OUTCOME_KIND", "PUBLISH_KIND",
           "prepare_result", "publish_result", "record_result_evidence",
           "resolve_import_account", "result_identity", "result_of"]

INTENT_KIND = "result.prepare"
OUTCOME_KIND = "result.prepared"
EVIDENCE_KIND = "result.evidence"
PUBLISH_KIND = "result.publish"

# THE THREE INDEPENDENT OWNERS A RESULT MUST SATISFY IN ITS OWN RIGHT. The
# producer's verification, review and approval prove the SUBMISSION; they say
# nothing about bytes that did not exist when they were recorded. So a result
# carries its own three, each naming the actor that gave it and the exact
# content it was given about.
_EVIDENCE_KINDS = ("verification", "review", "approval")
_EVIDENCE_MEMBERS = ("kind", "identity", "actor", "disposition",
                     "content_digest")
_DISPOSITIONS = {"verification": "passed", "review": "accepted",
                 "approval": "approved"}

# THE IMMUTABLE OPERANDS ONE RESULT IS DERIVED AND SIGNED FROM. They are the
# submission's identity, the integration role's own assignment, the pinned
# target and the workspace -- every one of them a fact that cannot change
# under a retry. A member that could move is deliberately absent: an identity
# derived from mutable state is one a retry re-derives differently.
_FIXED = ("canonical_target_id", "authority_uuid", "work_id", "job_id",
          "line_id", "source_checkpoint_id", "source_verdict_id",
          "source_proposal_id", "source_result_id", "source_result_digest",
          "source_checkpoint_digest", "source_base", "source_candidate",
          "integration_attempt_id", "integration_assignment", "workspace",
          "profile_name", "profile_version", "target_revision",
          "target_source", "target_reference")


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _object(value, what):
    """One full object name, so no revision expression reaches a record."""
    boundaries.text(value, what)
    if len(value) != 40 or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lowercase object name",
                category="integrity", code="schema")
    return value


def _assignment(value, what):
    held = boundaries.document(value, what,
                               required=("work_ref", "participant",
                                         "generation"))
    ref = boundaries.document(held["work_ref"], f"{what}'s Work reference",
                              required=("authority_uuid", "work_id"))
    boundaries.text(ref["authority_uuid"], f"{what}'s Authority")
    boundaries.text(ref["work_id"], f"{what}'s Work id")
    boundaries.text(held["participant"], f"{what}'s participant")
    boundaries.generation(held["generation"], f"{what}'s generation")
    return held


def _place(value, what):
    return boundaries.document(value, what,
                               required=("path", "device", "inode"))


def result_identity(operands):
    """The identity one result is derived from, and only from what cannot move.

    Deriving it here, from the closed fixed-operand set, is what lets a reader
    RE-DERIVE it from a materialized row and refuse a row whose recorded
    identity does not follow from its own contents.
    """
    held = {name: operands[name] for name in _FIXED}
    return "result-" + digest(held).split(":", 1)[1]


def _fixed_operands(given):
    """The closed operand set, each member owned before it is signed."""
    held = {}
    for name in ("canonical_target_id", "line_id", "source_checkpoint_id",
                 "source_verdict_id", "source_proposal_id",
                 "source_result_id", "integration_attempt_id", "job_id",
                 "work_id"):
        held[name] = boundaries.identity(given[name], f"a result's {name}")
    for name in ("authority_uuid", "source_result_digest",
                 "source_checkpoint_digest", "profile_name",
                 "target_reference"):
        held[name] = boundaries.text(given[name], f"a result's {name}")
    for name in ("source_base", "source_candidate", "target_revision"):
        held[name] = _object(given[name], f"a result's {name}")
    held["integration_assignment"] = _assignment(
        given["integration_assignment"], "the integration assignment")
    held["workspace"] = _place(given["workspace"], "the private workspace")
    held["target_source"] = _place(given["target_source"],
                                   "the nominated target source")
    boundaries.generation(given["profile_version"], "a profile version")
    held["profile_version"] = given["profile_version"]
    if held["integration_assignment"]["work_ref"] != {
            "authority_uuid": held["authority_uuid"],
            "work_id": held["work_id"]}:
        _refuse("the integration assignment names another Work; a result is "
                "prepared under the assignment of the Work it belongs to",
                code="operation-collision")
    if held["source_base"] == held["target_revision"]:
        _refuse(f"the submission is already based on "
                f"{name_value(held['target_revision'])}; a reconciliation "
                f"answers a target that moved and there is nothing here to "
                f"re-express")
    return held


# -- the intent, the outcome, and the resume between them --------------------


def prepare_result(store, profile, *, submission, workspace, target_source,
                   target_reference, integration_attempt_id,
                   integration_assignment, canonical_target_id,
                   target_revision=None):
    """Reconcile one eligible submission with one pinned target snapshot.

    THE INTENT COMMITS BEFORE ANY PROFILE EFFECT, which is what makes a death
    in the middle answerable rather than invisible. A committed intent says
    this exact submission is being reconciled onto this exact target revision
    in this exact workspace, under this exact integration assignment, and every
    one of those is fixed for the life of the record.

    AND A COMMITTED INTENT RESUMES RATHER THAN REPLAYING. This is the
    correction the superseded slice's review named: an exact retry of a
    preparing record used to answer "already done" and call the profile zero
    times, leaving a record that could never finish. Here the intent's own
    recorded operands are recovered and the profile is asked again -- with the
    ORIGINAL target revision, never a freshly selected one -- and the profile
    validates and reuses whatever it already retained instead of reconciling
    twice. Only the OUTCOME replays.
    """
    _profile_capabilities(profile)
    # THE TARGET IS PINNED HERE, from the dedicated target's own configured
    # reference, and then it is an IMMUTABLE operand of this result. A caller
    # may name one explicitly to resume or re-derive an existing record; it
    # supplies no default, because a result whose target its caller chose
    # freely would be one nothing pinned.
    #
    # AND A MOVED TARGET IS A NEW RESULT, not a silent continuation of an old
    # one: the revision is part of the derived identity, so pinning a later
    # revision yields a different record and leaves the earlier one exactly as
    # it was. That is the contract's rule rather than an accident of hashing.
    if target_revision is None:
        target_revision = profile.revision(target_source["path"],
                                           target_reference)
    operands = _fixed_operands(dict(
        submission, workspace=workspace, target_source=target_source,
        target_reference=target_reference,
        integration_attempt_id=integration_attempt_id,
        integration_assignment=integration_assignment,
        canonical_target_id=canonical_target_id,
        target_revision=target_revision,
        profile_name=getattr(profile, "name", None),
        profile_version=getattr(profile, "version", None)))
    if operands["profile_name"] != PROFILE_NAME \
            or operands["profile_version"] != PROFILE_VERSION:
        _refuse(f"this owner composes {PROFILE_NAME}/{PROFILE_VERSION} and the "
                f"supplied profile is "
                f"{name_value(operands['profile_name'])}/"
                f"{operands['profile_version']}",
                category="policy", code="profile-uncertified")
    result_id = result_identity(operands)
    intent_id = INTENT_KIND + ":" + result_id
    outcome_id = OUTCOME_KIND + ":" + result_id
    intent_signature = _signature(INTENT_KIND, operands)

    # 1. THE OUTCOME FIRST. A settled result is settled; nothing below it runs
    #    again, and this is the only branch that may answer without asking the
    #    profile anything.
    settled, _held = store.replay(outcome_id, _outcome_signature(
        store, result_id, operands), kind=OUTCOME_KIND, witness=_witness) \
        if _recorded(store, outcome_id) else (False, None)
    if settled:
        return result_of(store, result_id)

    # 2. THE INTENT. Committed already means RESUME; absent means commit it.
    recorded = _recorded(store, intent_id)
    if recorded is None:
        def intend(connection):
            now = store._now()
            connection.execute(
                "INSERT INTO integration_results (result_id, operation_id, "
                + ", ".join(_FIXED) + ", state, recorded_at) VALUES (?, ?, "
                + ", ".join("?" for _ in _FIXED) + ", 'preparing', ?)",
                (result_id, intent_id)
                + tuple(_stored(operands[name]) for name in _FIXED) + (now,))
            return {"result_id": result_id, "state": "preparing"}

        store.transact(intent_id, INTENT_KIND, intent_signature, intend,
                       witness=_witness)
    elif recorded["signature"] != intent_signature:
        _refuse(f"result {name_value(result_id)} is already being prepared "
                f"under different operands; an identity derived from these "
                f"operands cannot describe others",
                code="operation-collision")

    # 3. THE OPERANDS THE PROFILE IS ASKED WITH ARE THE RECORD'S OWN, recovered
    #    rather than recomputed -- so a resume cannot select a later target.
    held = _row(store, result_id)
    answer = profile.prepare(
        held["workspace"]["path"], result_id=result_id,
        base=held["source_base"], candidate=held["source_candidate"],
        target=held["target_revision"],
        candidate_source=held["workspace"]["path"],
        target_source=held["target_source"]["path"])
    return _settle(store, result_id, operands, answer)


def _settle(store, result_id, operands, answer):
    """Record what the profile answered, once, under this same intent."""
    if type(answer) is not dict or answer.get("state") not in ("prepared",
                                                               "held"):
        _refuse("a reconciliation profile answers a prepared or held outcome",
                category="integrity", code="schema")
    prepared = None
    content_digest = None
    reason = None
    if answer["state"] == "prepared":
        prepared = _prepared(answer["prepared"], operands["target_revision"])
        content_digest = digest(prepared["content"])
    else:
        reason = boundaries.text(answer.get("reason"), "a hold reason")
        conflicts = answer.get("conflicts")
        if type(conflicts) is not list:
            _refuse("a held reconciliation answers the paths it conflicted on",
                    category="integrity", code="schema")
        for one in conflicts:
            boundaries.text(one, "a conflicted path")
        if conflicts:
            reason = reason + " (" + ", ".join(conflicts) + ")"
    outcome_id = OUTCOME_KIND + ":" + result_id
    signature = _signature(OUTCOME_KIND, {
        "result_id": result_id, "state": answer["state"],
        "prepared": prepared, "content_digest": content_digest,
        "reason": reason, **{name: operands[name] for name in _FIXED}})

    def act(connection):
        current = connection.execute(
            "SELECT state FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if current is None or current["state"] != "preparing":
            _refuse(f"result {name_value(result_id)} is no longer preparing",
                    code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = ?, reason = ?, "
            "prepared = ?, content_digest = ?, operation_id = ? "
            "WHERE result_id = ? AND state = 'preparing'",
            (answer["state"], reason,
             None if prepared is None else canonical_text(prepared),
             content_digest, outcome_id, result_id))
        return {"result_id": result_id, "state": answer["state"]}

    store.transact(outcome_id, OUTCOME_KIND, signature, act, witness=_witness)
    return result_of(store, result_id)


def _outcome_signature(store, result_id, operands):
    """The signature a SETTLED outcome was recorded under, re-derived.

    Read from the materialized row rather than from the caller, so an exact
    retry compares against what this owner actually committed.
    """
    held = _row(store, result_id)
    return _signature(OUTCOME_KIND, {
        "result_id": result_id, "state": held["state"],
        "prepared": held["prepared"], "content_digest": held["content_digest"],
        "reason": held["reason"], **{name: operands[name] for name in _FIXED}})


# -- the result's OWN independent evidence -----------------------------------


def record_result_evidence(store, *, result_id, verification, review,
                           approval):
    """Consume the three independent owners' evidence ABOUT THESE BYTES.

    NO CALLER SUPPLIES AN APPROVAL AS A BOOLEAN and no producer receipt is
    copied here. Each document names its own kind, its own identity, the actor
    that gave it, its disposition and -- the binding that matters -- the
    CONTENT DIGEST it was given about. A document whose content digest is not
    this result's prepared content is evidence about something else, and it
    refuses rather than being filed under this result.

    IT IS RECORDED ONLY ONTO A PREPARED RESULT. Evidence about a held or
    still-preparing record would be evidence about content that does not exist.
    """
    held = result_of(store, result_id)
    if held["state"] not in ("prepared", "awaiting-evidence"):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; independent evidence is recorded about prepared content "
                f"and never about content that does not exist yet")
    given = {"verification": verification, "review": review,
             "approval": approval}
    evidence = {}
    for kind in _EVIDENCE_KINDS:
        document = boundaries.document(given[kind], f"the result's {kind}",
                                       required=_EVIDENCE_MEMBERS)
        if document["kind"] != kind:
            _refuse(f"the result's {kind} names kind "
                    f"{name_value(document['kind'])}",
                    category="integrity", code="schema")
        boundaries.identity(document["identity"], f"a {kind} identity")
        boundaries.text(document["actor"], f"a {kind} actor")
        if document["disposition"] != _DISPOSITIONS[kind]:
            _refuse(f"the result's {kind} is "
                    f"{name_value(document['disposition'])} and an authorized "
                    f"result carries {name_value(_DISPOSITIONS[kind])}",
                    code="denied", category="policy")
        if document["content_digest"] != held["content_digest"]:
            _refuse(f"the result's {kind} was given about content "
                    f"{name_value(document['content_digest'])} and this "
                    f"result's prepared content is "
                    f"{name_value(held['content_digest'])}; evidence about "
                    f"other bytes is not this result's",
                    category="integrity", code="digest")
        evidence[kind] = document
    actors = {evidence[kind]["actor"] for kind in _EVIDENCE_KINDS}
    if len(actors) != len(_EVIDENCE_KINDS):
        _refuse("one actor gave more than one of this result's three "
                "independent judgements; independence is what they are for",
                category="policy", code="denied")
    operation_id = EVIDENCE_KIND + ":" + result_id
    signature = _signature(EVIDENCE_KIND, {
        "result_id": result_id, "content_digest": held["content_digest"],
        "evidence": evidence})

    def act(connection):
        current = connection.execute(
            "SELECT state, content_digest FROM integration_results "
            "WHERE result_id = ?", (result_id,)).fetchone()
        if current is None or current["state"] not in ("prepared",
                                                       "awaiting-evidence") \
                or current["content_digest"] != held["content_digest"]:
            _refuse(f"result {name_value(result_id)} changed while its "
                    f"evidence was being proved", code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = 'authorized', "
            "evidence = ?, operation_id = ? WHERE result_id = ?",
            (canonical_text(evidence), operation_id, result_id))
        return {"result_id": result_id, "state": "authorized"}

    store.transact(operation_id, EVIDENCE_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


# -- the derived Authority proposal ------------------------------------------


def publish_result(store, publisher, *, result_id, input_digest,
                   policy_digest):
    """Publish the authorized result as its OWN Authority proposal.

    W133117's gate proved this expressible with no Authority change: the
    proposal is an ordinary one under the INTEGRATION role's own live
    assignment, carrying a frozen result identity this record owns, the
    combined candidate, and the pinned snapshot as its target. The producer's
    proposal is untouched and its result identity is never borrowed -- the
    Authority refuses that itself, which is why this derives its own.

    ONLY AN AUTHORIZED RESULT PUBLISHES. Content that nobody verified,
    reviewed and approved is content, not a candidate.
    """
    held = result_of(store, result_id)
    if held["state"] not in ("authorized", "published"):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; a result is published after its own verification, review "
                f"and approval and never before them")
    if getattr(publisher, "participant", None) != held[
            "integration_assignment"]["participant"]:
        _refuse(f"the publishing session acts for "
                f"{name_value(getattr(publisher, 'participant', None))} and "
                f"this result's assignment names "
                f"{name_value(held['integration_assignment']['participant'])}",
                code="capability")
    derived_result_id = "derived-" + result_id
    derived_result_digest = digest({"result_id": derived_result_id,
                                    "content": held["prepared"]["content"],
                                    "head": held["prepared"]["head"]})
    proposal_id = "proposal-" + result_id
    operation_id = PUBLISH_KIND + ":" + result_id
    signature = _signature(PUBLISH_KIND, {
        "result_id": result_id, "proposal_id": proposal_id,
        "derived_result_id": derived_result_id,
        "derived_result_digest": derived_result_digest,
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})
    proposal = publisher.publish({
        "expect": held["integration_assignment"],
        "operation_id": "integration-publish:" + result_id,
        "proposal_id": proposal_id, "result_id": derived_result_id,
        "result_digest": derived_result_digest,
        "candidate_digest": held["prepared"]["head"],
        "input_digest": boundaries.text(input_digest, "an input digest"),
        "policy_digest": boundaries.text(policy_digest, "a policy digest"),
        "target": held["target_revision"]})
    _published(proposal, held, proposal_id, derived_result_id,
               derived_result_digest)

    def act(connection):
        current = connection.execute(
            "SELECT state FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if current is None or current["state"] not in ("authorized",
                                                       "published"):
            _refuse(f"result {name_value(result_id)} is no longer authorized",
                    code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = 'published', "
            "derived_proposal_id = ?, derived_result_id = ?, "
            "derived_result_digest = ?, operation_id = ? WHERE result_id = ?",
            (proposal_id, derived_result_id, derived_result_digest,
             operation_id, result_id))
        return {"result_id": result_id, "state": "published",
                "derived_proposal_id": proposal_id}

    store.transact(operation_id, PUBLISH_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


def _published(proposal, held, proposal_id, result_id, result_digest):
    """The Authority's own answer, held to what this result requires."""
    document = boundaries.document(proposal, "the derived proposal",
                                   required=("proposal_id", "assignment_ref",
                                             "result_id", "result_digest",
                                             "candidate_digest",
                                             "input_digest", "policy_digest",
                                             "target"))
    if document["proposal_id"] != proposal_id \
            or document["result_id"] != result_id \
            or document["result_digest"] != result_digest:
        _refuse("the derived proposal does not name this result's own frozen "
                "identity", category="integrity", code="digest")
    if document["assignment_ref"] != held["integration_assignment"]:
        _refuse("the derived proposal was published under another assignment",
                category="stale-assignment", code="generation")
    if document["candidate_digest"] != held["prepared"]["head"]:
        _refuse("the derived proposal names other bytes than this result "
                "prepared", category="integrity", code="digest")
    if document["target"] != held["target_revision"]:
        _refuse("the derived proposal names another target than the snapshot "
                "this result was prepared onto",
                category="integrity", code="digest")
    return document


# -- what admission may act on -----------------------------------------------


def resolve_import_account(store, profile, *, result_id):
    """Revalidate everything an import admission needs, at the moment it asks.

    A RESULT IS NOT ELIGIBLE BECAUSE IT ONCE WAS. Its content is re-proved
    against the workspace it was prepared in, its own evidence is re-read, and
    the dedicated target's CURRENT revision is compared with the snapshot it
    was prepared onto. A target that moved again refuses HERE, before the
    queue, with the stale-result guard the contract keeps rather than removes.
    """
    held = result_of(store, result_id)
    if held["state"] != "published":
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; an import account is resolved for a published result")
    profile.validate(held["workspace"]["path"], held["prepared"],
                     target=held["target_revision"])
    current = profile.revision(held["target_source"]["path"],
                               held["target_reference"])
    if current != held["target_revision"]:
        _refuse(f"this result was prepared onto "
                f"{name_value(held['target_revision'])} and the dedicated "
                f"target now holds {name_value(current)}; a result whose "
                f"target moved is reconciled again rather than imported",
                category="stale-assignment", code="target")
    return {"result_id": result_id,
            "canonical_target_id": held["canonical_target_id"],
            "authority_uuid": held["authority_uuid"],
            "work_id": held["work_id"], "job_id": held["job_id"],
            "source_proposal_id": held["source_proposal_id"],
            "source_checkpoint_id": held["source_checkpoint_id"],
            "derived_proposal_id": held["derived_proposal_id"],
            "derived_result_id": held["derived_result_id"],
            "derived_result_digest": held["derived_result_digest"],
            "candidate_digest": held["prepared"]["head"],
            "expected_target_revision": held["target_revision"],
            "content": dict(held["prepared"]["content"]),
            "content_digest": held["content_digest"],
            "evidence": held["evidence"],
            "integration_assignment": held["integration_assignment"]}


# -- the public reader -------------------------------------------------------


def result_of(store, result_id):
    """One custody record, bound to the journal by its OWN operands.

    WHAT MAKES THIS A BINDING. The row is adopted against its closed column
    contract, its nested documents are adopted against theirs, its identity is
    RE-DERIVED from the fixed operands the row itself carries, and the journal
    is asked for the operation the row names -- whose recorded signature must
    be the one those same operands produce. A row whose target revision was
    edited no longer derives its own identity, and a row pointed at somebody
    else's operation no longer matches that operation's signature. Existence
    of a journal row proves neither and is not what is checked.
    """
    held = _row(store, result_id)
    operands = {name: held[name] for name in _FIXED}
    if result_identity(operands) != held["result_id"]:
        _refuse(f"result {name_value(result_id)} does not derive its own "
                f"identity from its recorded operands",
                category="integrity", code="digest")
    kind = _KIND_FOR_STATE[held["state"]]
    recorded = _recorded(store, held["operation_id"])
    if recorded is None or recorded["kind"] != kind:
        _refuse(f"result {name_value(result_id)} names operation "
                f"{name_value(held['operation_id'])}, which this store's "
                f"journal does not hold as a committed {kind}",
                category="integrity", code="schema")
    expected = _expected_signature(kind, result_id, held, operands)
    if recorded["signature"] != expected:
        _refuse(f"result {name_value(result_id)} does not match the operands "
                f"its own operation was signed under",
                category="integrity", code="digest")
    return held


# WHICH ACT LAST MOVED A RESULT INTO EACH STATE. The reader binds a row to
# THAT act's signature, so a row whose state and operation disagree is refused
# rather than read as whichever of the two a caller preferred.
_KIND_FOR_STATE = {"preparing": INTENT_KIND, "prepared": OUTCOME_KIND,
                   "held": OUTCOME_KIND, "awaiting-evidence": OUTCOME_KIND,
                   "authorized": EVIDENCE_KIND, "published": PUBLISH_KIND,
                   "imported": PUBLISH_KIND}


def _expected_signature(kind, result_id, held, operands):
    if kind == INTENT_KIND:
        return _signature(INTENT_KIND, operands)
    if kind == OUTCOME_KIND:
        return _signature(OUTCOME_KIND, {
            "result_id": result_id, "state": held["state"],
            "prepared": held["prepared"],
            "content_digest": held["content_digest"],
            "reason": held["reason"], **operands})
    if kind == EVIDENCE_KIND:
        return _signature(EVIDENCE_KIND, {
            "result_id": result_id, "content_digest": held["content_digest"],
            "evidence": held["evidence"]})
    return _signature(PUBLISH_KIND, {
        "result_id": result_id, "proposal_id": held["derived_proposal_id"],
        "derived_result_id": held["derived_result_id"],
        "derived_result_digest": held["derived_result_digest"],
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})


def _row(store, result_id):
    boundaries.identity(result_id, "an integration result identity")
    found = store._connection.execute(
        "SELECT * FROM integration_results WHERE result_id = ?",
        (result_id,)).fetchone()
    if found is None:
        _refuse(f"no integration result {name_value(result_id)}")
    held = boundaries.row(found, "a persisted integration result",
                          schema.RESULT_COLUMNS)
    held["integration_assignment"] = _assignment(
        json.loads(held["integration_assignment"]),
        "a persisted integration assignment")
    held["workspace"] = _place(json.loads(held["workspace"]),
                               "a persisted workspace")
    held["target_source"] = _place(json.loads(held["target_source"]),
                                   "a persisted target source")
    if held["prepared"] is not None:
        held["prepared"] = _prepared(json.loads(held["prepared"]),
                                     held["target_revision"])
        if held["content_digest"] != digest(held["prepared"]["content"]):
            _refuse("a persisted result's content digest does not match its "
                    "own path and mode set",
                    category="integrity", code="digest")
    if held["evidence"] is not None:
        held["evidence"] = json.loads(held["evidence"])
    return held


def _prepared(value, target_revision):
    """The profile's closed prepared-evidence shape, adopted as its own."""
    held = boundaries.document(value, "prepared result evidence",
                               required=("profile", "version", "base", "head",
                                         "tree", "reference", "content"))
    if held["profile"] != PROFILE_NAME or held["version"] != PROFILE_VERSION:
        _refuse("prepared evidence names another profile",
                category="integrity", code="schema")
    for name in ("base", "head", "tree"):
        _object(held[name], f"prepared evidence's {name}")
    boundaries.text(held["reference"], "a prepared reference")
    if held["base"] != target_revision:
        _refuse("prepared evidence names another target snapshot than the "
                "record it belongs to", category="integrity", code="digest")
    content = held["content"]
    if type(content) is not dict or not content:
        _refuse("prepared evidence carries its target-relative content set",
                category="integrity", code="schema")
    for path, mode in content.items():
        boundaries.text(path, "a prepared content path")
        if path.startswith("/") or ".." in path.split("/"):
            _refuse("a prepared content path is relative and canonical",
                    category="integrity", code="path")
        if mode not in ("100644", "100755"):
            _refuse(f"a prepared content path carries mode {name_value(mode)}; "
                    f"this import owns ordinary file content",
                    category="integrity", code="file-type")
    return held


# -- the pieces the acts above are composed from -----------------------------


def _signature(kind, operands):
    """This store's own signature text, so a journal row round-trips.

    `integration_signature` is the coordinator's constructor: it sweeps for a
    durable secret and answers CANONICAL TEXT, which is what the operations
    table's `signature` column is contracted to decode. A digest would compare
    just as well and would not be a persisted JSON value.
    """
    return integration_signature(kind, operands)


def _stored(value):
    return canonical_text(value) if isinstance(value, (dict, list)) else value


def _recorded(store, operation_id):
    found = store._connection.execute(
        "SELECT * FROM operations WHERE operation_id = ?",
        (operation_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted operation record",
                          schema.OPERATION_COLUMNS)


def _witness(store, row):
    """This owner's semantic proof of one recorded act.

    `IntegrationStore.replay` requires a witness because presence of a journal
    row is not proof of what it materialized. For these two kinds the proof is
    the record itself: an act named `<kind>:<result_id>` must have materialized
    a result whose own operands derive that identity, which is exactly what
    `result_of` establishes.
    """
    kind = row["kind"]
    if kind not in (INTENT_KIND, OUTCOME_KIND, EVIDENCE_KIND, PUBLISH_KIND):
        _refuse(f"this owner does not witness {name_value(kind)} acts",
                category="integrity", code="schema")
    _prefix, _, result_id = row["operation_id"].partition(":")
    return result_of(store, result_id)


def _profile_capabilities(profile):
    for name in ("prepare", "validate", "content", "revision"):
        boundaries.capability(getattr(profile, name, None),
                              f"a reconciliation profile's {name} capability")
    return profile
