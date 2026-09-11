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
from .admission import source_submission
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
                     "result_id", "content_digest", "candidate", "target")
_DISPOSITIONS = {"verification": "passed", "review": "accepted",
                 "approval": "approved"}

# WHO IS ASKED, AND WITH WHICH CAPABILITY. Review 2026-09-10T05:14:36Z [P1]:
# these three used to be dictionaries a caller wrote, so a caller could name
# an unconfigured verifier, name the preparer as its own reviewer, and reach a
# real derived publication on judgements nobody made. They are now INJECTED
# OWNERS -- the shape CONTRACT-v1 section 3 asks for when it says exact
# signatures pin injected owners -- and the actor recorded is the owner's own
# participant rather than a string beside it. `driver._receipt` asks the
# configured sessions the same way for the SUBMISSION's receipts.
_EVIDENCE_VERBS = {"verification": "verify", "review": "review",
                   "approval": "approve"}

# THE THREE CAUSAL OBSERVATIONS, RETAINED IN CUSTODY RATHER THAN BESIDE IT.
# CONTRACT-v1 section 4, and section 3's requirement that a record cannot omit
# its original causal observation references. Review [P1]: a dossier JSON is
# useful evidence and is not runtime custody, so the verification owner hands
# these over and this record keeps them, cross-bound to the content they were
# observed against.
_OBSERVATIONS = ("base", "isolated", "combined")
_OBSERVATION_MEMBERS = ("command", "test_identity", "input_commit",
                        "input_tree", "test_digest", "environment",
                        "status", "output", "execution", "harness_added")

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


def prepare_result(store, profile, manager, jobs, authority, *, line_id,
                   proposal_id, workspace, target_source, target_reference,
                   integration_attempt_id, integration_assignment,
                   canonical_target_id, target_revision=None):
    """Reconcile one eligible submission with one pinned target snapshot.

    THE SUBMISSION IS RESOLVED, NOT ACCEPTED. Review 2026-09-10T05:14:36Z [P1]:
    this used to take a `submission` document from its caller, so a caller
    could name a proposal the Authority never published and a checkpoint and
    verdict nobody ever created, and reach a real derived publication on them.
    `line_id` and `proposal_id` are SELECTORS now -- which is what
    CONTRACT-v1 section 3's own signature says -- and
    `admission.source_submission` re-reads the accepted checkpoint, its
    writer's assignment and frozen output, the Authority proposal with its
    three policy receipts and the Job that owns the input, policy and scope.
    Every member of the submission comes back from those producers.

    IT IS SOURCE ELIGIBILITY AND NOT FRESHNESS, deliberately: the target has
    moved, which is why there is a reconciliation at all.

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
    submission = source_submission(manager, jobs, authority, line_id=line_id,
                                   proposal_id=proposal_id)
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
    retry compares against what this owner actually committed -- and from the
    state that act SETTLED rather than whatever the record has reached since,
    which is review [P2]'s correction. An exact `prepare_result` retry after
    authorization now replays the prepared outcome instead of refusing an
    operation-collision against a signature nothing ever recorded.
    """
    held = _row(store, result_id)
    return _signature(OUTCOME_KIND, {
        "result_id": result_id, "state": _settled_state(held),
        "prepared": held["prepared"], "content_digest": held["content_digest"],
        "reason": held["reason"], **{name: operands[name] for name in _FIXED}})


# -- the result's OWN independent evidence -----------------------------------


def _basis(held):
    """WHAT AN OWNER IS ASKED ABOUT, derived here and never accepted.

    An owner that is handed the question can only answer this result. The
    content digest now names the prepared bytes themselves, so an answer about
    another tree over the same paths no longer matches.
    """
    return {"result_id": held["result_id"],
            "content_digest": held["content_digest"],
            "candidate": held["prepared"]["head"],
            "tree": held["prepared"]["tree"],
            "target": held["target_revision"]}


def _observation(value, what):
    """One causal observation, with everything section 4 requires named."""
    held = boundaries.document(value, what, required=_OBSERVATION_MEMBERS)
    if type(held["command"]) is not list or not held["command"]:
        _refuse(f"{what} names the command that produced it",
                category="integrity", code="schema")
    for one in held["command"]:
        boundaries.text(one, f"{what}'s command word")
    for name in ("test_identity", "test_digest", "environment", "output",
                 "execution"):
        boundaries.text(held[name], f"{what}'s {name}")
    for name in ("input_commit", "input_tree"):
        _object(held[name], f"{what}'s {name}")
    if type(held["status"]) is not int or type(held["status"]) is bool:
        _refuse(f"{what} carries the actual exit status it observed",
                category="integrity", code="schema")
    # SECTION 4, SAID OUT LOUD RATHER THAN IMPLIED: a harness that did not
    # exist in the content it ran against was ADDED there, and the observation
    # records that instead of letting a reader assume the state carried it.
    if type(held["harness_added"]) is not bool:
        _refuse(f"{what} says whether its harness was added to the content it "
                f"ran against", category="integrity", code="schema")
    return held


def _causal(given, held, actor):
    """The three observations, cross-bound to the content they are about.

    SECTION 4, ENFORCED RATHER THAN DESCRIBED. The defect reproduction failed
    on the submission's ORIGINAL base, the same pinned harness passed with the
    isolated fix, and the third observation is what that harness did on the
    COMBINED result -- which is this record's own tree, so a combined
    observation about some other content is not this result's.

    ONE HARNESS, PINNED ONCE. Three different test digests would be three
    different questions, and section 4 asks for one question asked three times.

    AND A COMBINED FAILURE STAYS VISIBLE. It does not erase the isolated
    positive and it does not become a passed verification; it blocks.
    """
    observations = boundaries.document(given, "the causal observations",
                                       required=_OBSERVATIONS)
    taken = {name: _observation(observations[name],
                                f"the {name} causal observation")
             for name in _OBSERVATIONS}
    digests = {one["test_digest"] for one in taken.values()}
    if len(digests) != 1:
        _refuse("the three causal observations name different harnesses; one "
                "pinned harness is run against three content states",
                category="integrity", code="digest")
    if taken["base"]["input_commit"] != held["source_base"]:
        _refuse(f"the base observation ran against "
                f"{name_value(taken['base']['input_commit'])} and this "
                f"submission's original base is "
                f"{name_value(held['source_base'])}",
                category="integrity", code="digest")
    if taken["isolated"]["input_commit"] != held["source_candidate"]:
        _refuse(f"the isolated observation ran against "
                f"{name_value(taken['isolated']['input_commit'])} and this "
                f"submission's candidate is "
                f"{name_value(held['source_candidate'])}",
                category="integrity", code="digest")
    if taken["combined"]["input_commit"] != held["prepared"]["head"] \
            or taken["combined"]["input_tree"] != held["prepared"]["tree"]:
        _refuse("the combined observation ran against other content than this "
                "result prepared", category="integrity", code="digest")
    if not taken["base"]["harness_added"]:
        _refuse("the base observation does not say the harness was added; a "
                "regression harness the submission brings with it did not "
                "exist on the original base, and section 4 records that "
                "rather than pretending the base ran it",
                category="integrity", code="schema")
    for name in ("isolated", "combined"):
        if taken[name]["harness_added"]:
            _refuse(f"the {name} observation added its harness; that content "
                    f"carries the submission's own harness and an added one "
                    f"is a different question",
                    category="integrity", code="schema")
    if taken["base"]["status"] == 0:
        _refuse("the base observation PASSED on the original base; a causal "
                "witness is a reproduction that fails there",
                category="policy", code="denied")
    if taken["isolated"]["status"] != 0:
        _refuse("the isolated observation did not pass with the submission's "
                "own fix", category="policy", code="denied")
    if taken["combined"]["status"] != 0:
        _refuse(f"the combined result FAILED its own causal observation with "
                f"status {taken['combined']['status']}; a combined failure "
                f"blocks integration and is not verified away. The isolated "
                f"positive is retained and unaffected",
                category="policy", code="denied")
    for name in _OBSERVATIONS:
        if taken[name]["execution"] != actor:
            _refuse(f"the {name} observation was produced by "
                    f"{name_value(taken[name]['execution'])} and this "
                    f"result's verification owner is {name_value(actor)}",
                    category="policy", code="denied")
    return taken


def _judgement(owner, kind, held, basis):
    """Ask ONE injected owner for its judgement, and hold it to the question.

    The actor is the OWNER's own participant. A deployment that wires an
    unconfigured or absent owner here fails at the capability rather than
    contributing a string that looks like a judgement.
    """
    verb = _EVIDENCE_VERBS[kind]
    boundaries.capability(getattr(owner, verb, None),
                          f"the configured {kind} owner's {verb} capability")
    actor = boundaries.text(getattr(owner, "participant", None),
                            f"the configured {kind} owner's participant")
    if actor == held["integration_assignment"]["participant"]:
        _refuse(f"{name_value(actor)} prepared this result and cannot also "
                f"give its {kind}; the integration owner does not review its "
                f"own composition", category="policy", code="denied")
    answer = getattr(owner, verb)(dict(basis, kind=kind))
    document = boundaries.document(answer, f"the result's {kind}",
                                   required=_EVIDENCE_MEMBERS)
    if document["kind"] != kind:
        _refuse(f"the result's {kind} names kind "
                f"{name_value(document['kind'])}",
                category="integrity", code="schema")
    boundaries.identity(document["identity"], f"a {kind} identity")
    if document["actor"] != actor:
        _refuse(f"the {kind} owner acts for {name_value(actor)} and answered "
                f"for {name_value(document['actor'])}",
                category="policy", code="denied")
    if document["disposition"] != _DISPOSITIONS[kind]:
        _refuse(f"the result's {kind} is "
                f"{name_value(document['disposition'])} and an authorized "
                f"result carries {name_value(_DISPOSITIONS[kind])}",
                code="denied", category="policy")
    for member in ("result_id", "content_digest", "candidate", "target"):
        expected = basis["candidate"] if member == "candidate" else basis[member]
        if document[member] != expected:
            _refuse(f"the result's {kind} was given about {member} "
                    f"{name_value(document[member])} and this result's is "
                    f"{name_value(expected)}; evidence about anything else is "
                    f"not this result's",
                    category="integrity", code="digest")
    return document


def record_result_evidence(store, verification, reviewer, approver, *,
                           result_id, observations):
    """Consume three INJECTED owners' judgements about THESE exact bytes.

    NO CALLER SUPPLIES AN APPROVAL AS A BOOLEAN, no producer receipt is copied,
    and -- review 2026-09-10T05:14:36Z [P1] -- no caller writes the judgement
    itself. Each owner is asked, with a question this record derives, and the
    recorded actor is the owner's own participant.

    FOUR BINDINGS, NOT ONE. Each answer names this RESULT, the content digest
    of its prepared bytes, the combined candidate and the pinned target. The
    content digest now names the objects in the tree, so evidence given about
    a passing combined result no longer fits a failing one over the same file
    names -- which is the exact reuse the review reproduced.

    THE CAUSAL OBSERVATIONS ARE CUSTODY, not a document beside it. Section 4's
    three observations are recorded here, cross-bound to the base, candidate
    and combined tree they were produced against, and a combined FAILURE
    blocks rather than being verified away.

    IT IS RECORDED ONLY ONTO A PREPARED RESULT. Evidence about a held or
    still-preparing record would be evidence about content that does not exist.

    AND AN EXACT RETRY REPLAYS. Review [P2]: an identical call after this
    result had already been authorized used to refuse before it ever reached
    the journal. A settled act is settled; what an identical retry gets is the
    record that act made.
    """
    held = result_of(store, result_id)
    operation_id = EVIDENCE_KIND + ":" + result_id
    if held["prepared"] is None:
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; independent evidence is recorded about prepared content "
                f"and never about content that does not exist yet")
    basis = _basis(held)
    given = {"verification": verification, "review": reviewer,
             "approval": approver}
    evidence = {kind: _judgement(given[kind], kind, held, basis)
                for kind in _EVIDENCE_KINDS}
    actors = {evidence[kind]["actor"] for kind in _EVIDENCE_KINDS}
    if len(actors) != len(_EVIDENCE_KINDS):
        _refuse("one actor gave more than one of this result's three "
                "independent judgements; independence is what they are for",
                category="policy", code="denied")
    causal = _causal(observations, held, evidence["verification"]["actor"])
    signature = _signature(EVIDENCE_KIND, {
        "result_id": result_id, "content_digest": held["content_digest"],
        "evidence": evidence, "causal_observations": causal})
    if held["state"] not in ("prepared", "awaiting-evidence"):
        # A RECORD THAT HAS MOVED ON, AND WHAT AN IDENTICAL CALL DESERVES.
        # Review [P2]: this used to refuse before it reached the journal, so
        # an exact retry after authorization failed. It replays now -- but the
        # comparison is made against the operands THESE owners just answered
        # with, not against whatever the row holds, so a call that changed an
        # owner or an observation still collides instead of quietly replaying
        # somebody else's settled act.
        recorded = _recorded(store, operation_id)
        if recorded is not None and recorded["signature"] == signature:
            settled, _held = store.replay(operation_id, signature,
                                          kind=EVIDENCE_KIND,
                                          witness=_witness)
            if settled:
                return held
        _refuse(f"result {name_value(result_id)} is already "
                f"{name_value(held['state'])} under other evidence; an "
                f"authorized result is not re-judged in place",
                code="operation-collision")

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
            "evidence = ?, causal_observations = ?, operation_id = ? "
            "WHERE result_id = ?",
            (canonical_text(evidence), canonical_text(causal), operation_id,
             result_id))
        return {"result_id": result_id, "state": "authorized"}

    store.transact(operation_id, EVIDENCE_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


def _evidence_signature(held):
    """The signature the EVIDENCE act was recorded under, re-derived from the
    row it made rather than from whatever state the row has reached since."""
    return _signature(EVIDENCE_KIND, {
        "result_id": held["result_id"],
        "content_digest": held["content_digest"],
        "evidence": held["evidence"],
        "causal_observations": held["causal_observations"]})


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


def resolve_import_account(store, profile, manager, jobs, authority, *,
                           result_id):
    """Revalidate everything an import admission needs, at the moment it asks.

    A RESULT IS NOT ELIGIBLE BECAUSE IT ONCE WAS. Its content is re-proved
    against the workspace it was prepared in, its own evidence is re-read, and
    the dedicated target's CURRENT revision is compared with the snapshot it
    was prepared onto. A target that moved again refuses HERE, before the
    queue, with the stale-result guard the contract keeps rather than removes.

    AND THE ORIGINAL ELIGIBILITY IS RE-READ THROUGH ITS OWNERS. Review
    2026-09-10T05:14:36Z [P1]: this could not reach the accepted producers
    through its old signature, so a record whose source stopped being an
    accepted candidate -- a withdrawn checkpoint, a receipt that no longer
    agrees, a Job whose scope moved -- resolved an import account anyway.
    `source_submission` answers from those producers now, and every member it
    answers must be the one this record was prepared from. A submission that
    no longer resolves refuses; a submission that resolves DIFFERENTLY refuses
    with the member that moved.
    """
    held = result_of(store, result_id)
    if held["state"] != "published":
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; an import account is resolved for a published result")
    resolved = source_submission(manager, jobs, authority,
                                 line_id=held["line_id"],
                                 proposal_id=held["source_proposal_id"])
    for member, value in sorted(resolved.items()):
        if held[member] != value:
            _refuse(f"this result was prepared from {member} "
                    f"{name_value(held[member])} and its accepted producers "
                    f"now say {name_value(value)}; a result whose source "
                    f"moved is not imported on the strength of what was true "
                    f"then", category="stale-assignment", code="precondition")
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
            "causal_observations": held["causal_observations"],
            "integration_assignment": held["integration_assignment"]}


# -- the public reader -------------------------------------------------------


def result_of(store, result_id):
    """One custody record, bound to the journal by EVERY act that made it.

    WHAT MAKES THIS A BINDING. The row is adopted against its closed column
    contract, its nested documents are adopted against theirs, its identity is
    RE-DERIVED from the fixed operands the row itself carries, and the journal
    is asked for each act this record's state says it passed through -- whose
    recorded signature must be the one the row's own current contents produce.

    REVIEW 2026-09-10T05:14:36Z [P1]: ONLY THE LATEST ACT USED TO BE CHECKED,
    and every earlier one was taken on trust the moment the record moved on.
    So an AUTHORIZED row could have its prepared head and tree replaced with
    object names nothing holds, a PUBLISHED row could have its evidence
    emptied, and both still read -- because the evidence act, and then the
    publish act, were the only signatures anyone compared. An earlier valid
    write is not a current typed read. Every act in `_CHAIN_FOR_STATE` is
    re-derived from the row as it stands NOW, so tampering with what an
    earlier act settled breaks that act's signature whatever the row has
    become since.

    AND THE STATE'S OWN REQUIRED FIELDS ARE STRUCTURAL. `imported` with no
    entry is not a terminal linkage, and the schema and this reader both say
    so.
    """
    held = _row(store, result_id)
    operands = {name: held[name] for name in _FIXED}
    if result_identity(operands) != held["result_id"]:
        _refuse(f"result {name_value(result_id)} does not derive its own "
                f"identity from its recorded operands",
                category="integrity", code="digest")
    chain = _CHAIN_FOR_STATE[held["state"]]
    if held["operation_id"] != _operation_id(chain[-1], result_id):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f" and names operation {name_value(held['operation_id'])}, "
                f"which is not the act that reaches that state",
                category="integrity", code="schema")
    for kind in chain:
        operation_id = _operation_id(kind, result_id)
        recorded = _recorded(store, operation_id)
        if recorded is None or recorded["kind"] != kind:
            _refuse(f"result {name_value(result_id)} is "
                    f"{name_value(held['state'])}, which this store's journal "
                    f"does not hold as a committed {kind}",
                    category="integrity", code="schema")
        expected = _expected_signature(kind, result_id, held, operands)
        if recorded["signature"] != expected:
            _refuse(f"result {name_value(result_id)} does not match the "
                    f"operands its own {kind} was signed under",
                    category="integrity", code="digest")
    if held["state"] == "imported" and held["entry_id"] is None:
        _refuse(f"result {name_value(result_id)} is imported and names no "
                f"entry; a terminal result carries the linkage it was "
                f"imported through", category="integrity", code="schema")
    return held


# EVERY ACT A RECORD IN EACH STATE MUST HAVE PASSED THROUGH, in order.
#
# Review 2026-09-10T05:14:36Z [P1] replaced a `_KIND_FOR_STATE` map that named
# only the LAST one. A record does not stop being the thing its intent
# committed and its outcome settled just because it has since been authorized:
# each of those acts signed particular contents, and each signature is
# re-derived from the row as it stands now.
_CHAIN_FOR_STATE = {
    "preparing": (INTENT_KIND,),
    "prepared": (INTENT_KIND, OUTCOME_KIND),
    "held": (INTENT_KIND, OUTCOME_KIND),
    "awaiting-evidence": (INTENT_KIND, OUTCOME_KIND),
    "authorized": (INTENT_KIND, OUTCOME_KIND, EVIDENCE_KIND),
    "published": (INTENT_KIND, OUTCOME_KIND, EVIDENCE_KIND, PUBLISH_KIND),
    "imported": (INTENT_KIND, OUTCOME_KIND, EVIDENCE_KIND, PUBLISH_KIND),
}


def _operation_id(kind, result_id):
    return kind + ":" + result_id


def _settled_state(held):
    """WHICH STATE THE OUTCOME ACT SETTLED, recovered rather than read off the
    row's current one.

    Review [P2]: `_outcome_signature` derived the outcome's signature from
    whatever state the record had reached SINCE, so an exact retry after
    authorization compared against a signature that act never used and refused
    an operation-collision on an identical call. A held outcome stays held; any
    record that went further settled as `prepared`.
    """
    return "held" if held["state"] == "held" else "prepared"


def _expected_signature(kind, result_id, held, operands):
    if kind == INTENT_KIND:
        return _signature(INTENT_KIND, operands)
    if kind == OUTCOME_KIND:
        return _signature(OUTCOME_KIND, {
            "result_id": result_id, "state": _settled_state(held),
            "prepared": held["prepared"],
            "content_digest": held["content_digest"],
            "reason": held["reason"], **operands})
    if kind == EVIDENCE_KIND:
        return _evidence_signature(held)
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
    if held["causal_observations"] is not None:
        held["causal_observations"] = json.loads(held["causal_observations"])
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
    for path, entry in content.items():
        boundaries.text(path, "a prepared content path")
        if path.startswith("/") or ".." in path.split("/"):
            _refuse("a prepared content path is relative and canonical",
                    category="integrity", code="path")
        # REVIEW [P1]: A PATH SET IS NOT CONTENT. Each entry names the OBJECT
        # its bytes are as well as its mode, so this record's content digest
        # is a statement about bytes rather than about file names -- which is
        # what let two different combined trees share one digest, and one
        # result's evidence authorize another's.
        taken = boundaries.document(entry, f"the prepared entry at {path!r}",
                                    required=("mode", "object"))
        if taken["mode"] not in ("100644", "100755"):
            _refuse(f"a prepared content path carries mode "
                    f"{name_value(taken['mode'])}; this import owns ordinary "
                    f"file content", category="integrity", code="file-type")
        _object(taken["object"], f"the prepared object at {path!r}")
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
