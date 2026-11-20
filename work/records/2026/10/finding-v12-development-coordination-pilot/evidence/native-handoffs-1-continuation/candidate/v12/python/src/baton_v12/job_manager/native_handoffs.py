"""THE HOST'S SIDE OF ONE NATIVE HANDOFF: classify, yield, answer, continue.

W385331, first vertical native communication slice. The reviewer planning
disposition is `work/records/2026/11/
finding-v12-native-agent-handoffs-discovery/FIRST-NATIVE-SLICE.md`.

WHAT THIS OWNS, and the order of the list is the order of the path:

  1. CLASSIFICATION. What a completed worker invocation WAS, read out of its
     own frozen result's declared handoff output and cross-bound to the
     attempt that produced it. Four answers: a final submission, a
     clarification request, a within-scope finding request, or a reviewer
     response.
  2. THE YIELD RECORD. One durable Job-store record per episode saying that
     this stage stopped at a question rather than at a candidate, naming the
     Authority message, the retained checkpoint and the continuation.
  3. THE CONTINUATION. The resolved continuation of the SAME admitted task,
     under its own finite allowance, spending no correction round.
  4. THE HOLD. The record that an escalation leaves the execution held for the
     configured decision recipient.

WHAT IT REFUSES TO DO, and every one of these is a ruling rather than a
preference:

  * A COMPLETED INVOCATION CARRYING A REQUEST IS NOT A COMPLETED STAGE. The
    classification happens BEFORE publication, before review attachment,
    before any `completed` projection and before any dependent stage's
    dependency is satisfied -- which is why it is a separate function the
    ending calls at step six and not a reading of the ending's answer.
  * UNDECLARED, MIXED, MISSING OR FOREIGN OUTPUT HOLDS. A handoff-capable
    attempt that answers no handoff, two handoffs, a handoff from another
    revision, or a handoff beside a competing claim is evidence this manager
    cannot settle. It is never read as the least alarming of the readings, and
    in particular it never falls back to legacy success.
  * A RESPONSE IS NOT A VERDICT AND NEVER MINTS A RECEIPT. The answer earns a
    continuation of unfinished work or a hold; it earns no verification,
    review, approval or integration receipt, and there is no path from here to
    one.
  * A CONTINUATION IS NOT A CORRECTION ROUND. It is journalled under its own
    kind, counted against its own allowance, and invisible to
    `job_control.rounds_used_in` -- so a zero-correction profile stays a
    zero-correction profile. It resets no clock and it moves no deadline.
  * NOTHING HERE DECIDES AUTHORIZATION. Who may ask, who may answer and who an
    unresolved question escalates to are the Authority's, resolved through the
    participant-bound session the host already holds.

NO HOST STORE OR CREDENTIAL REACHES A WORKER. Everything a worker contributes
arrives as a frozen declared artifact and its bounded claim; everything else is
read from the owner that holds it.
"""

import json

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..native_handoff import (ANSWER_DISPOSITION, CLARIFICATION_KIND,
                              ESCALATE_DISPOSITION, FINAL_KIND, FINDING_KIND,
                              HANDOFF_SCHEMA, REQUEST_KINDS, RESPONSE_KIND,
                              check_handoff, handoff_digest)
from ..worker_manager import (attempts, boundaries, frozen_output_of,
                              load_manifest, review_cycles)
from . import documents, episodes, job_control, role_contract
from .store import job_signature

__all__ = ["ANSWER_DISPOSITION", "ESCALATE_DISPOSITION", "HandoffPort",
           "REQUEST_OPERATION", "RESPOND_OPERATION", "commit_answer",
           "commit_request", "message_identity",
           "CONTEXT_SCHEMA", "context_bytes", "cross_bound",
           "delivered_context",
           "AWAITING_STATE", "ANSWERED_STATE", "ANSWER_KIND",
           "CONTINUE_KIND", "HOLD_KIND", "YIELD_KIND", "answer_of",
           "answer_operation_id", "record_answer",
           "ANSWERED_OUTCOME", "ESCALATED_OUTCOME", "YIELD_OUTCOME",
           "HANDOFF_OUTPUT", "RESPONSE_OUTPUT", "YIELD_MEMBERS",
           "classified_handoff", "classified_response", "continuation_of",
           "continuation_operation_id", "handoff_capable", "hold_of",
           "hold_operation_id", "record_hold",
           "record_yield", "response_satisfies_dependency",
           "yield_of", "yield_operation_id", "advance_continuation"]

# THE JOURNAL KINDS. All three are ordinary operations in the Job store's
# existing journal, taken through `transact` under deterministic identities
# derived from the stage and its episode -- `ending`'s own shape and for its
# reason: a second registration replays rather than repeats, and a different
# document under the same identity refuses. No schema change and no second
# journal.
#
# THE EPISODE IS IN EVERY IDENTITY, for `manager.receipt_operation_id`'s
# reason: a continuation opens a fresh episode, and a record keyed by the stage
# alone would let the new round replay the old round's.
YIELD_KIND = "native.yield"
CONTINUE_KIND = "native.continue"
HOLD_KIND = "native.hold"
# THE REVIEW STAGE'S OWN RECORD that its episode ended in a RESPONSE rather
# than a verdict, keyed by the review stage and episode. Without it the
# review stage's completed frozen result would project `completed` and open
# its dependent's gate -- an integration admitted on a question nobody
# answered with a verdict.
ANSWER_KIND = "native.answer"

# THE CONTINUATION OUTCOME, DISTINCT FROM FINAL SUBMISSION. This is the
# explicit held/awaiting-answer state the slice asks for: a stage that stopped
# at a question is neither `completed` (which would satisfy its dependent's
# gate) nor `exceptional` (which would say the Job is over) nor
# `changes-requested` (which is a verdict nobody gave).
AWAITING_STATE = "awaiting-answer"
# AND THE REVIEW STAGE'S COUNTERPART: its live episode ended in a reply,
# which is neither `completed` (that would satisfy the integration's gate on
# a candidate nobody judged) nor `changes-requested` (a verdict nobody gave).
# An answer moves both stages to fresh episodes in the same act, so this is
# what an ESCALATED review stage stays in while the execution is held.
ANSWERED_STATE = "answered"

# WHAT AN ENDING ANSWERS WITH on each of the three new paths. `held` is
# deliberately NOT reused for a yield: `_finished` reads `held` as "the ending
# did not finish" and returns before the obligation settles, and a yield IS a
# finished ending -- the runtime is gone, the outputs are frozen, the message
# is committed and the route has moved.
YIELD_OUTCOME = AWAITING_STATE
ANSWERED_OUTCOME = "answered"
ESCALATED_OUTCOME = "escalated"

# The two declared outputs, imported from the descriptor that declares them
# rather than respelled -- `role_contract` is their owner.
HANDOFF_OUTPUT = role_contract.HANDOFF_OUTPUT
RESPONSE_OUTPUT = role_contract.RESPONSE_OUTPUT

# WHAT A YIELD RECORD CARRIES. Every member is an identity some owner already
# holds, written here so a later incarnation can re-derive the whole state from
# the record alone -- `ending.SELECTORS`' rule applied to this record.
YIELD_MEMBERS = ("stage_id", "job_id", "work_id", "episode", "attempt_id",
                 "kind", "message_id", "handoff_digest", "checkpoint_id",
                 "continuation_digest", "task_digest", "destination",
                 "template_version")

CONTINUATION_MEMBERS = ("job_id", "stage_id", "episode", "message_id",
                        "request_id", "checkpoint_id", "task_digest")

# The effect word a reply must have earned before a continuation is admitted.
# `authority.messages` owns it; the assertion at the foot of this module holds
# this spelling to that owner.
CONTINUATION_EFFECT = "continuation"

HOLD_MEMBERS = ("job_id", "stage_id", "episode", "message_id", "request_id",
                "destination", "checkpoint_id")

ANSWER_MEMBERS = ("job_id", "stage_id", "episode", "attempt_id", "message_id",
                  "request_id", "disposition", "checkpoint_id")


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _authority_effect():
    """The authority's own continuation effect word, read from its owner.

    A FUNCTION BECAUSE THE IMPORT IS DEFERRED. `authority` is a sibling
    package this module may read at call time and must not import at module
    scope: the manager side is what composes an authority session, not the
    other way round, and a module-level import would make the direction of the
    dependency invisible.
    """
    from ..authority.messages import CONTINUATION_EFFECT as held

    return held


# -- is this Job's template handoff-capable at all ---------------------------


def handoff_capable(store, job_id):
    """Whether this Job was admitted under a handoff-capable template.

    READ FROM THE CREATION RECORD, which is where the resolved template version
    durably lives, and ABSENCE IS LEGACY. A Job created before this slice,
    submitted by hand, or resolved against `/1` or `/2` has no handoff branch
    at all -- which is the whole of what preserves every already admitted
    version: the branch cannot be reached for them, so nothing they do can be
    reinterpreted.

    FAIL-CLOSED IN THE DIRECTION THAT MATTERS. A Job this store has no creation
    record for answers `False`: it keeps its existing behaviour exactly, and a
    handoff it somehow produced would be an UNDECLARED output that the frozen
    result boundary already refuses.
    """
    from . import creation

    created = creation.created_job_of(store, job_id)
    if created is None:
        return False
    return role_contract.is_handoff_capable(created["template_version"])


def template_of(store, job_id):
    """The template version this Job resolved, or `None`."""
    from . import creation

    created = creation.created_job_of(store, job_id)
    return None if created is None else created["template_version"]


# -- the classification, out of the frozen result ----------------------------


def _frozen_result(control, attempt_id, what):
    """The retained result manifest of one attempt, cross-bound to it.

    EVERY BINDING `review_verdict_from_result` MAKES, for the same reason it
    makes them: a namespaced claim by itself says only that somebody wrote
    members into an output. What makes it evidence about THIS attempt is that
    the frozen summary and the retained manifest name one result, and that the
    manifest names this attempt's own fixed assignment at its own generation.
    """
    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"attempt {name_value(attempt_id)} has no frozen result; a "
                f"{what} is read from immutable output and never from a "
                f"running one")
    if frozen["disposition"] != "completed":
        _refuse(f"attempt {name_value(attempt_id)} froze a "
                f"{name_value(frozen['disposition'])} result; an invocation "
                f"that did not complete declared no {what}")
    result = load_manifest(control, frozen["manifest_digest"],
                           "resultManifest")
    if result is None:
        _refuse(f"this manager retains no result manifest at "
                f"{name_value(frozen['manifest_digest'])} for attempt "
                f"{name_value(attempt_id)}")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen summary and its retained manifest name different "
                "results", category="integrity", code="schema")
    fixed = attempts.assignment_of(control, attempt_id)
    expected = {"work_ref": {"authority_uuid": fixed["authority_uuid"],
                             "work_id": fixed["work_id"]},
                "participant": fixed["participant"],
                "generation": fixed["generation"]}
    if result["assignment_ref"] != expected:
        _refuse("the frozen result and the attempt do not name one "
                "assignment", category="integrity", code="schema")
    return frozen, result, fixed


def _sole_output(result, name, what):
    """One present, measured, artifact-backed output of a frozen result.

    `review_driver._claim_output`'s rule, restated for this module's own two
    outputs: a document that says it is missing while carrying material is a
    document contradicting itself, and a claim is not read from an output
    nobody measured.
    """
    matches = [one for one in result["outputs"] if one["name"] == name]
    if len(matches) != 1:
        _refuse(f"the frozen result carries {len(matches)} outputs named "
                f"{name_value(name)}; a {what} is read from exactly one",
                category="integrity", code="schema")
    output = matches[0]
    if output["status"] != "present" or output["artifact"] is None \
            or output["content_manifest"] is None:
        _refuse(f"the frozen {name_value(name)} output is not present with "
                f"both its artifact and content manifest; a {what} is not "
                f"read from an output nobody measured")
    return output


def _no_competing_claim(result, name, what):
    """A handoff claim anywhere but on its own output is a MIXED answer.

    `review_driver._review_claim`'s [P1] correction, applied to this
    namespace: the whole output set is scanned rather than the one other
    output a reader happened to think of, because naming the outputs to
    exclude is how the next output added becomes a second answer nobody looks
    for.
    """
    competing = sorted(
        one["name"] for one in result["outputs"]
        if one["name"] != name
        and type(one.get("result_metadata")) is dict
        and HANDOFF_SCHEMA in one["result_metadata"])
    if competing:
        _refuse(f"the frozen result carries a {name_value(HANDOFF_SCHEMA)} "
                f"claim on {', '.join(name_value(one) for one in competing)}; "
                f"a handoff is declared on {name_value(name)} and one "
                f"invocation declares once", category="ambiguous",
                code="collection")


def _claimed_handoff(result, name, kinds, what):
    _no_competing_claim(result, name, what)
    output = _sole_output(result, name, what)
    metadata = output["result_metadata"]
    if type(metadata) is not dict or HANDOFF_SCHEMA not in metadata:
        _refuse(f"the frozen {name_value(name)} output carries no "
                f"{name_value(HANDOFF_SCHEMA)} claim; what an invocation was "
                f"is its own declaration and this manager will not invent one")
    held = check_handoff(metadata[HANDOFF_SCHEMA],
                         what=f"a worker {what}")
    if held["kind"] not in kinds:
        _refuse(f"the {name_value(name)} output declares kind "
                f"{name_value(held['kind'])} and this output carries "
                f"{', '.join(kinds)}; a handoff on the wrong output is a "
                f"declaration about the wrong invocation",
                category="integrity", code="schema")
    return held


def classified_handoff(control, attempt_id):
    """What one completed IMPLEMENTATION invocation declared itself to be.

    Answers `{"kind", "handoff", "handoff_digest", "result_id",
    "manifest_digest", "assignment"}` or REFUSES. The kind is one of the final
    submission and the two request kinds; a `response` on this output is the
    wrong declaration for this role and refuses as one.

    CALLED BEFORE PUBLICATION. That position is the whole of the enforcement:
    the ending has frozen and retained its outputs by then, so there is
    evidence to classify, and it has published nothing, attached no review and
    satisfied no dependency -- so a request can still stop the legacy path
    instead of having to undo it.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    frozen, result, fixed = _frozen_result(control, attempt_id, "handoff")
    held = _claimed_handoff(result, HANDOFF_OUTPUT,
                            (FINAL_KIND, CLARIFICATION_KIND, FINDING_KIND),
                            "handoff")
    return {"kind": held["kind"], "handoff": held,
            "handoff_digest": handoff_digest(held),
            "result_id": frozen["result_id"],
            "manifest_digest": frozen["manifest_digest"],
            "assignment": fixed}


def classified_response(control, attempt_id):
    """What one completed REVIEW invocation declared itself to be.

    A REVIEW ANSWERS ONCE. A result carrying both a `response` claim and a
    `baton.checkpoint-review/1` verdict claim is a reviewer answering a
    question AND judging a candidate in one invocation, which is two answers --
    so it is refused as the ambiguity it is rather than resolved by picking a
    half to believe.
    """
    from .review_driver import REVIEW_CLAIM_NAMESPACE

    boundaries.identity(attempt_id, "a runtime attempt id")
    frozen, result, fixed = _frozen_result(control, attempt_id, "response")
    verdicts = sorted(
        one["name"] for one in result["outputs"]
        if type(one.get("result_metadata")) is dict
        and REVIEW_CLAIM_NAMESPACE in one["result_metadata"])
    if verdicts:
        _refuse(f"the frozen review result declares a response and carries a "
                f"{name_value(REVIEW_CLAIM_NAMESPACE)} verdict claim on "
                f"{', '.join(name_value(one) for one in verdicts)}; a "
                f"response is a clarification interpretation and never an "
                f"accepted technical review, and one invocation answers once",
                category="ambiguous", code="collection")
    held = _claimed_handoff(result, RESPONSE_OUTPUT, (RESPONSE_KIND,),
                            "response")
    return {"kind": held["kind"], "handoff": held,
            "handoff_digest": handoff_digest(held),
            "disposition": held["disposition"],
            "result_id": frozen["result_id"],
            "manifest_digest": frozen["manifest_digest"],
            "assignment": fixed}


def declares_response(control, attempt_id, terminal=None):
    """Whether this review attempt declared a RESPONSE at all, as a BOOLEAN.

    THE DISPATCH QUESTION AND NOTHING MORE. A review attempt whose result
    answers its `response` output `missing-optional` is an ordinary final
    technical review and takes the verdict branch; one that declares a
    response takes the response branch, and whether that response is WELL
    FORMED is then `classified_response`'s refusal rather than a reason to
    silently fall back to reading a verdict that is not there.

    FROM THE FROZEN RESULT WHEN THERE IS ONE, AND FROM THE WORKER'S OWN
    COMPLETION ENVELOPE BEFORE THERE IS ONE. The ending is what freezes the
    result, so on the tick that dispatches the ending nothing is frozen yet;
    the envelope the runtime published is the evidence that exists at that
    moment and it is the same document the ending correlates the frozen
    result against (`_correlated`). Dispatching on it chooses a BRANCH and
    decides nothing: the response branch still freezes, correlates and
    classifies out of the frozen result, and an envelope that declared a
    response the frozen result does not carry is that branch's own refusal.

    A LEGACY RESULT WITH NO SUCH OUTPUT ANSWERS `False`, which is what keeps
    every `/1` and `/2` review reading exactly as it did.
    """
    frozen = frozen_output_of(control, attempt_id)
    if frozen is not None:
        if frozen["disposition"] != "completed":
            return False
        result = load_manifest(control, frozen["manifest_digest"],
                               "resultManifest")
        if result is None:
            return False
        return _declares(result.get("outputs"))
    if type(terminal) is dict and terminal.get("disposition") == "completed":
        return _declares(terminal.get("outputs"))
    return False


def _declares(outputs):
    if type(outputs) is not list:
        return False
    for one in outputs:
        if type(one) is not dict or one.get("name") != RESPONSE_OUTPUT:
            continue
        return (one.get("status") == "present"
                and type(one.get("result_metadata")) is dict
                and HANDOFF_SCHEMA in one["result_metadata"])
    return False


# -- the three durable records -----------------------------------------------


def _operation_id(kind, stage_id, episode):
    boundaries.identity(stage_id, "a stage id")
    boundaries.generation(episode, "an episode number")
    return f"{kind}:{stage_id}:{episode}"


def yield_operation_id(stage_id, episode):
    return _operation_id(YIELD_KIND, stage_id, episode)


def continuation_operation_id(stage_id, episode):
    """The identity one resolved continuation commits under.

    DERIVED FROM THE YIELDING EPISODE, which is the thing a continuation is
    ABOUT -- `episodes.correction_operation_id`'s own reasoning, and its two
    rejected spellings apply here unchanged. The episode numbers the round is
    LEAVING are stable only until the act commits; the ANSWER identity does not
    move, but a caller presenting any other answer would compute a different
    name and open a second continuation on one question. One yielded episode
    earns one continuation.
    """
    return _operation_id(CONTINUE_KIND, stage_id, episode)


def hold_operation_id(stage_id, episode):
    return _operation_id(HOLD_KIND, stage_id, episode)


def answer_operation_id(stage_id, episode):
    return _operation_id(ANSWER_KIND, stage_id, episode)


def _committed(store, kind, operation_id, members, stage_id, episode):
    """One committed record of this store's journal, PROVED to be this
    stage's.

    A SIGNATURE IS NOT OWNERSHIP, which is `ending._committed`'s correction and
    applies here for its reason: a well-made record of ANOTHER stage, copied
    through the public journal to this identity, would otherwise read as this
    stage's own. So the record's own selectors are compared back against the
    stage and episode it was selected by.
    """
    row = store._connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (operation_id, kind)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    record = json.loads(row["result"])
    if type(record) is not dict \
            or any(one not in record for one in members):
        _refuse(f"the committed {kind} record at "
                f"{name_value(operation_id)} is not one this build can read",
                category="integrity", code="schema")
    if record["stage_id"] != stage_id or record["episode"] != episode:
        _refuse(f"the committed {kind} record at "
                f"{name_value(operation_id)} names stage "
                f"{name_value(record['stage_id'])} episode "
                f"{record['episode']} and it was selected as "
                f"{name_value(stage_id)} episode {episode}; a record is "
                f"proved to be this stage's rather than merely well made",
                category="integrity", code="schema")
    return record


def yield_of(store, stage_id, episode):
    """The yield this stage's episode recorded, or `None`."""
    return _committed(store, YIELD_KIND,
                      yield_operation_id(stage_id, episode), YIELD_MEMBERS,
                      stage_id, episode)


def continuation_of(store, stage_id, episode):
    return _committed(store, CONTINUE_KIND,
                      continuation_operation_id(stage_id, episode),
                      CONTINUATION_MEMBERS, stage_id, episode)


def hold_of(store, stage_id, episode):
    return _committed(store, HOLD_KIND,
                      hold_operation_id(stage_id, episode), HOLD_MEMBERS,
                      stage_id, episode)


def answer_of(store, stage_id, episode):
    """The reply this REVIEW stage's episode ended in, or `None`."""
    return _committed(store, ANSWER_KIND,
                      answer_operation_id(stage_id, episode), ANSWER_MEMBERS,
                      stage_id, episode)


def _stage_row(store, stage_id):
    from . import submission

    for row in submission.stage_rows(store):
        if row["stage_id"] == stage_id:
            return row
    _refuse(f"this store carries no stage {name_value(stage_id)}; a native "
            f"handoff record belongs to a stage of this Job store")


def record_yield(store, *, stage_id, episode, attempt_id, kind, message_id,
                 handoff_digest, checkpoint_id, continuation_digest,
                 task_digest, destination, now=None):
    """Journal that THIS episode stopped at a question rather than a candidate.

    EVERY SELECTOR IS READ FROM THIS STORE rather than accepted: the Job, the
    Work and the template version come from the stage row and the creation
    record, so a caller cannot file a yield against a stage it names
    incorrectly or claim a handoff-capable template for a Job that resolved a
    legacy one.

    REPLAY IS THE JOURNAL'S. The same operands under the same identity replay
    this record; changed operands collide, which is what stops one yielding
    episode from being recorded as two different questions.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.identity(message_id, "a Work message identity")
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    if kind not in REQUEST_KINDS:
        _refuse(f"a yield is recorded for {', '.join(REQUEST_KINDS)}; this is "
                f"{name_value(kind)}. A final submission is not a yield and "
                f"takes the ordinary publication path",
                category="integrity", code="schema")
    stage = _stage_row(store, stage_id)
    version = template_of(store, stage["job_id"])
    if version is None or not role_contract.is_handoff_capable(version):
        _refuse(f"Job {name_value(stage['job_id'])} resolved template "
                f"{name_value(version)}, which is not handoff-capable; a "
                f"yield is not recorded against an admitted version that has "
                f"no branch for one",
                category="policy", code="denied")
    record = {"stage_id": stage_id, "job_id": stage["job_id"],
              "work_id": stage["work_id"], "episode": episode,
              "attempt_id": attempt_id, "kind": kind,
              "message_id": message_id, "handoff_digest": handoff_digest,
              "checkpoint_id": checkpoint_id,
              "continuation_digest": continuation_digest,
              "task_digest": task_digest, "destination": destination,
              "template_version": version}
    operation_id = yield_operation_id(stage_id, episode)
    return store.transact(
        operation_id, YIELD_KIND, job_signature(YIELD_KIND, record),
        lambda connection: record)


def record_hold(store, *, stage_id, episode, message_id, request_id,
                destination, checkpoint_id):
    """Journal that an ESCALATION left this episode held.

    ONE DURABLE PENDING ESCALATION PER REQUEST, and this record is what makes
    re-entry reread it rather than raise a fresh one: the identity is the
    yielding episode's, so every later tick replays this record instead of
    escalating again. There is no acknowledgement to wait for and no polling
    requirement -- the hold is a fact, not a conversation.
    """
    boundaries.identity(message_id, "a Work message identity")
    boundaries.identity(request_id, "a Work message identity")
    stage = _stage_row(store, stage_id)
    record = {"job_id": stage["job_id"], "stage_id": stage_id,
              "episode": episode, "message_id": message_id,
              "request_id": request_id, "destination": destination,
              "checkpoint_id": checkpoint_id}
    operation_id = hold_operation_id(stage_id, episode)
    return store.transact(
        operation_id, HOLD_KIND, job_signature(HOLD_KIND, record),
        lambda connection: record)


def record_answer(store, *, stage_id, episode, attempt_id, message_id,
                  request_id, disposition, checkpoint_id):
    """Journal that THIS review episode ended in a reply, not a verdict.

    THE REVIEW-SIDE TWIN OF `record_yield`, and it exists for the projection's
    reason: the reviewer's invocation is `completed` and the stage is NOT a
    completed review. Keyed by the review stage and episode, so an answer that
    goes on to open fresh episodes leaves this record on the episode it ended
    and the successor carries none.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.identity(message_id, "a Work message identity")
    boundaries.identity(request_id, "a Work message identity")
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    if disposition not in (ANSWER_DISPOSITION, ESCALATE_DISPOSITION):
        _refuse(f"a reply is recorded as {ANSWER_DISPOSITION} or "
                f"{ESCALATE_DISPOSITION}; this is {name_value(disposition)}",
                category="integrity", code="schema")
    stage = _stage_row(store, stage_id)
    if stage["kind"] != "review":
        _refuse(f"stage {name_value(stage_id)} is a {stage['kind']} stage and "
                f"a reply is recorded against the review stage that gave it",
                category="integrity", code="schema")
    record = {"job_id": stage["job_id"], "stage_id": stage_id,
              "episode": episode, "attempt_id": attempt_id,
              "message_id": message_id, "request_id": request_id,
              "disposition": disposition, "checkpoint_id": checkpoint_id}
    operation_id = answer_operation_id(stage_id, episode)
    return store.transact(
        operation_id, ANSWER_KIND, job_signature(ANSWER_KIND, record),
        lambda connection: record)


# -- the dependency question -------------------------------------------------


def response_satisfies_dependency(stage, predecessor):
    """Whether a REVIEW stage's dependency is satisfied FOR A RESPONSE.

    THIS IS NOT DEPENDENCY SUCCESS AND THE GATE SAYS SO. `completed` means the
    implementation delivered a candidate and the dependent review may judge it;
    this answers a different question -- the implementation stopped at a
    question it addressed to this Job's reviewer, so the reviewer's own
    invocation is what the Work is waiting for. The predecessor is NOT
    completed, publishes nothing, and its dependent earns no acceptance of any
    kind from this.

    WHY IT IS DECIDED HERE RATHER THAN BY A SECOND GATE KIND. SCH-4's
    outcome-naming dependency model is the FOLLOWING slice's; what this slice
    needs is one bounded reading of the existing gate, and it is bounded by
    four conjuncts that are all facts about committed records:

      * the dependent is a REVIEW stage -- nothing else has a response role;
      * the predecessor is in the awaiting-answer state, which only a
        committed yield record produces;
      * that yield is still UNANSWERED as far as this store knows -- once the
        continuation commits, the predecessor owes a fresh episode and this
        answers False again; and
      * the predecessor's yield names a handoff-capable template.

    SO THE WINDOW OPENS WHEN THE MESSAGE IS DURABLE AND CLOSES WHEN IT IS
    ANSWERED. There is no earlier instant at which it is open, which is what
    "no premature queued ownership window" means here: before the yield
    commits the predecessor is `answering` and the gate is shut.
    """
    # `.get`, because `gates_of` is asked about partial stage documents by
    # readers that carry only the dependency member; a stage that does not
    # say it is a review stage is not one.
    if type(stage) is not dict or stage.get("kind") != "review":
        return False
    if predecessor is None or predecessor.get("state") != AWAITING_STATE:
        return False
    held = predecessor.get("handoff")
    if held is None:
        return False
    return predecessor.get("continuation") is None


# -- the resolved continuation -----------------------------------------------


def _answered_request(authority, yielded, what, *, head):
    """The committed reply to this episode's request, read from the Authority.

    THE REPLY IS THE AUTHORIZATION AND IT IS READ THROUGH ITS OWN OWNER. This
    store holds no copy of the message, so there is nothing here for a caller
    to assert: the request identity comes from the yield record this store
    committed, and the reply, its author, its disposition and its effect come
    from the Authority that authorized them.
    """
    request = authority.work_message(yielded["message_id"])
    if request is None:
        _refuse(f"the Authority holds no message "
                f"{name_value(yielded['message_id'])}; a {what} follows a "
                f"durable request")
    if request["handoff_digest"] != yielded["handoff_digest"]:
        _refuse(f"request {name_value(yielded['message_id'])} carries handoff "
                f"digest {name_value(request['handoff_digest'])} and this "
                f"store recorded {name_value(yielded['handoff_digest'])}; a "
                f"{what} is about the question that was actually asked",
                category="integrity", code="digest")
    # THE RETAINED HEAD, PROVED THROUGH THE CUSTODY OWNER: the message names
    # the head object it yielded at and the frozen checkpoint this store's
    # yield record names records what was frozen. Both are owners' facts.
    if request["checkpoint_ref"] != head:
        _refuse(f"request {name_value(yielded['message_id'])} names retained "
                f"head {name_value(request['checkpoint_ref'])} and checkpoint "
                f"{name_value(yielded['checkpoint_id'])} froze "
                f"{name_value(head)}",
                category="integrity", code="schema")
    reply = authority.work_message_reply(yielded["message_id"])
    if reply is None:
        _refuse(f"request {name_value(yielded['message_id'])} has no reply; a "
                f"{what} follows an answer and never a silence")
    effect = authority.work_message_transition(reply["message_id"])
    if effect is None:
        _refuse(f"reply {name_value(reply['message_id'])} records no "
                f"transition; what a reply EARNED is a separate receipt and "
                f"this one carries none",
                category="integrity", code="schema")
    # THE ADMITTED TASK IS PRESERVED, COMPARED RATHER THAN ASSUMED. A
    # clarification preserves the task and specification digest; a reply that
    # named another one would be reopening a different task, and reopening an
    # invocation with an answer does not rewrite what was admitted.
    if reply["task_digest"] != yielded["task_digest"]:
        _refuse(f"reply {name_value(reply['message_id'])} names admitted task "
                f"digest {name_value(reply['task_digest'])} and this episode "
                f"yielded under {name_value(yielded['task_digest'])}; a "
                f"continuation is the same admitted task",
                category="integrity", code="digest")
    return request, reply, effect


def advance_continuation(store, custody, authority, *, job_id, now=None):
    """Resume ONE yielded implementation episode on its reviewer's answer.

    THE SHAPE IS `episodes.advance_correction`'S, deliberately and down to the
    order of its own corrections, because the SCHEDULING effect is the same one
    and that act's rules were paid for:

      * the two stages and the episodes that advance are READ FROM THIS STORE,
        so a caller cannot pair stages that are not a pair;
      * the REPLAY IS ASKED BEFORE THE PRECONDITIONS, because every one of them
        is about the round this would OPEN -- a committed continuation has
        already moved the stages past them, and proving them first would refuse
        the retry for having succeeded;
      * EVERY GUARD FOR THE WHOLE PAIR RUNS BEFORE THE FIRST ROW MOVES, and
        every refusal inside the transaction is ORDINARY, so a guard that fires
        after a partial write unwinds the savepoint instead of sealing half a
        continuation; and
      * the successors are FRESH episodes with fresh offer and attempt
        identities that have never been offered, which is precisely what lets
        the ordinary sweep offer them.

    WHAT IS DIFFERENT, AND IT IS THE WHOLE POINT:

      * NO VERDICT IS INVOLVED. `advance_correction` proves a recorded
        `changes-requested` disposition; this proves a committed REPLY to this
        episode's own request, and the line proof below requires a continuation
        HOLD that no verdict produces. Forging a changes-requested verdict to
        get a resume is the thing the slice forbids by name, and `reject_plan`
        is inappropriate for an ordinary question because its gate requires a
        DIFFERENT plan digest.
      * IT SPENDS A CONTINUATION, NOT A CORRECTION ROUND. The allowance is
        `job_control.CONTINUATIONS` and the guard runs inside the write
        transaction, so an exhausted Job holds rather than resuming -- and
        because the count is over committed continuation operations, replay
        does not spend twice.
      * THE DEADLINES AND THE FENCE ARE UNTOUCHED. `refuse_closed` is asked
        under this store's own lock with the current clock, so a cancelled Job,
        a Job past its stage or Job deadline, and a Job whose timing is
        uncertain all refuse here rather than resuming -- and no clock is
        reset.
      * AN ESCALATION RESUMES NOTHING. A reply whose effect is `held` leaves the
        execution held for the configured decision recipient, and this refuses
        rather than manufacturing a continuation from it.
    """
    boundaries.identity(job_id, "a Job identity")
    now = store._now() if now is None else now
    stages = episodes._stored_pair(store, job_id)
    implementation = stages["implementation"]
    review = stages["review"]
    live = episodes.live_of(store, implementation["stage_id"])
    if live is None:
        _refuse(f"stage {name_value(implementation['stage_id'])} has no live "
                f"episode, so there is no yielded round to continue; a "
                f"continuation advances the attempt that asked")
    yielded = yield_of(store, implementation["stage_id"], live["episode"])
    if yielded is None:
        _refuse(f"stage {name_value(implementation['stage_id'])} episode "
                f"{live['episode']} recorded no yield; a continuation follows "
                f"a durable request and nothing else")
    frozen = review_cycles.checkpoint_of(custody, yielded["checkpoint_id"])
    request, reply, effect = _answered_request(
        authority, yielded, "continuation", head=frozen["evidence"]["head"])
    if effect["effect"] != CONTINUATION_EFFECT:
        _refuse(f"reply {name_value(reply['message_id'])} earned the effect "
                f"{name_value(effect['effect'])}; an escalation leaves the "
                f"execution held for its configured decision recipient and a "
                f"continuation is not manufactured from it",
                category="policy", code="denied")
    record = {"job_id": job_id, "stage_id": implementation["stage_id"],
              "episode": live["episode"], "message_id": reply["message_id"],
              "request_id": request["message_id"],
              "checkpoint_id": yielded["checkpoint_id"],
              "task_digest": yielded["task_digest"]}
    operation_id = continuation_operation_id(implementation["stage_id"],
                                             live["episode"])
    signature = job_signature(CONTINUE_KIND, record)
    found, recorded = store.replay(operation_id, signature,
                                   kind=CONTINUE_KIND)
    if found:
        return recorded

    review_live = episodes.live_of(store, review["stage_id"])
    if review_live is None:
        _refuse(f"stage {name_value(review['stage_id'])} has no live episode; "
                f"a continuation advances the pair that answered")
    # THE LINE AND THE RETAINED CHECKPOINT, through the custody owner's own
    # readers and nothing else. `_continuation_line` is the one proof this act
    # adds, and what it proves is that the line is held for a CONTINUATION.
    line, checkpoint = _continuation_line(
        custody, line_id=None, checkpoint_id=yielded["checkpoint_id"],
        authority_uuid=store.authority_uuid, work_id=yielded["work_id"])
    episodes._unheld(store, live, "implementation")
    episodes._unheld(store, review_live, "review")
    rounds = {}
    for kind, episode in (("implementation", live), ("review", review_live)):
        number = episode["episode"] + 1
        offer_id, attempt_id = episodes.identities(
            store.authority_uuid, stages[kind]["stage_id"], number)
        rounds[kind] = {"stage_id": stages[kind]["stage_id"],
                        "ended_episode": episode["episode"],
                        "episode": number, "offer_id": offer_id,
                        "attempt_id": attempt_id}

    def act(connection):
        from . import cancellation

        # EVERY FENCE, INSIDE THE WRITE TRANSACTION. The reads above are an
        # optimistic early refusal and nothing more; these are the decisive
        # ones, and `refuse_closed` advances the watermark on this same
        # connection so a continuation that COMMITS carries the instant it was
        # decided against.
        cancellation.refuse_fenced(connection, job_id, "a continuation")
        job_control.refuse_closed(connection, job_id, "a continuation",
                                  now=now,
                                  stage_id=implementation["stage_id"])
        job_control.refuse_continuation(connection, job_id)
        opened = {}
        for kind in ("implementation", "review"):
            round_ = rounds[kind]
            held = episodes.episode_of(store, round_["stage_id"],
                                       round_["ended_episode"])
            if held is None or held["ended_state"] is not None:
                _refuse(f"episode {round_['ended_episode']} of stage "
                        f"{name_value(round_['stage_id'])} is no longer the "
                        f"live one; a continuation advances the pair it "
                        f"observed")
            # THE ALLOCATION PROOF, REPEATED UNDER THE WRITE LOCK, for
            # `advance_correction`'s reason: a reservation committed between
            # the preflight and here would otherwise survive while both
            # successors opened.
            episodes._unheld(store, held, kind)
        for kind in ("implementation", "review"):
            round_ = rounds[kind]
            changed = connection.execute(
                "UPDATE episodes SET ended_state = ?, ended_revision = ?, "
                "ended_at = ? WHERE stage_id = ? AND episode = ? "
                "AND ended_state IS NULL",
                (episodes.CORRECTION_ENDING, round_["episode"], now,
                 round_["stage_id"], round_["ended_episode"])).rowcount
            if changed != 1:
                _refuse(f"episode {round_['ended_episode']} of stage "
                        f"{name_value(round_['stage_id'])} stopped being live "
                        f"inside this transaction; a continuation advances the "
                        f"pair it observed")
            connection.execute(
                "INSERT INTO episodes (stage_id, episode, offer_id, "
                "attempt_id, opened_at, incarnation) VALUES (?, ?, ?, ?, ?, ?)",
                (round_["stage_id"], round_["episode"], round_["offer_id"],
                 round_["attempt_id"], now, store.incarnation))
            opened[kind] = documents.stage_episode(
                stage_id=round_["stage_id"], episode=round_["episode"],
                offer_id=round_["offer_id"], attempt_id=round_["attempt_id"],
                opened_at=now, incarnation=store.incarnation,
                ended_state=None, ended_revision=None, ended_at=None)
        return dict(record, line_id=line["line_id"],
                    revision=checkpoint["revision"], continued_at=now,
                    ended={kind: rounds[kind]["ended_episode"]
                           for kind in ("implementation", "review")},
                    implementation=opened["implementation"],
                    review=opened["review"])

    return store.transact(operation_id, CONTINUE_KIND, signature, act)


def _continuation_line(custody, *, line_id, checkpoint_id, authority_uuid,
                       work_id):
    """The custody proof a continuation makes, through the line provider only.

    WHAT IS PROVED, and what is deliberately NOT. The line must be holding the
    exact retained checkpoint for a CONTINUATION -- which `review_cycles.
    hold_for_continuation` is the only act that records -- and the Authority
    and Work must be this Job's, because a line is keyed by
    `(authority_uuid, work_id)` and a continuation advanced on another Work's
    line would be the same class of defect as adopting another store's offer.

    NO VERDICT IS READ, BECAUSE THERE IS NONE. `episodes._corrected_line`
    proves a recorded `changes-requested` disposition and that is exactly what
    this must not do.
    """
    checkpoint = review_cycles.checkpoint_of(custody, checkpoint_id)
    line = review_cycles.line_of(custody, checkpoint["line_id"])
    if line["authority_uuid"] != authority_uuid or line["work_id"] != work_id:
        _refuse(f"development line {name_value(line['line_id'])} belongs to "
                f"{name_value(line['work_id'])} under another Authority or "
                f"Work; this continuation is for {name_value(work_id)}")
    if line_id is not None and line["line_id"] != line_id:
        _refuse(f"checkpoint {name_value(checkpoint_id)} belongs to line "
                f"{name_value(line['line_id'])} and not to "
                f"{name_value(line_id)}")
    if checkpoint["state"] != "frozen":
        _refuse(f"checkpoint {name_value(checkpoint_id)} is "
                f"{name_value(checkpoint['state'])}; a continuation resumes "
                f"from the exact retained checkpoint the yield froze",
                category="integrity", code="schema")
    held = review_cycles.continuation_hold_of(custody, checkpoint_id)
    if held is None:
        _refuse(f"line {name_value(line['line_id'])} records no continuation "
                f"hold for checkpoint {name_value(checkpoint_id)}; a "
                f"continuation resumes a line that was held for one, and a "
                f"changes-requested verdict is not that record")
    if line["current_checkpoint_id"] != checkpoint_id:
        _refuse(f"development line {name_value(line['line_id'])} is held at "
                f"{name_value(line['current_checkpoint_id'])} and not at "
                f"{name_value(checkpoint_id)}")
    if line["state"] != review_cycles.CONTINUATION_READY:
        _refuse(f"development line {name_value(line['line_id'])} is "
                f"{name_value(line['state'])}; a continuation follows a "
                f"recorded continuation hold")
    return line, checkpoint


# -- the delivered context: what an attempt is told, read from owners --------
#
# W385331. A WORKER HAS NO HOST-STORE ACCESS, so what it needs to know about a
# handoff reaches it the way the task does: as one read-only document the
# deployment publishes beside the task before the runtime starts. This is the
# ONE composer of that document, and every member of it is read from the owner
# that holds it -- the Job store's own yield and continuation records, the
# Authority's committed messages and configured routing, the custody owner's
# frozen checkpoint. Nothing here is the deployment's own account of any of
# them, and nothing here decides anything: whether a request may be sent or
# answered is still the Authority's, at the commit.
#
# THREE SHAPES AND ONE SCHEMA. A fresh or resumed IMPLEMENTATION attempt is
# told the configured recipient it may address a request to and, when it is a
# continuation, the exact question it stopped at and the exact reply it
# resumes on. A REVIEW attempt over a yielded checkpoint is told the pending
# request and the checkpoint it is about. An ordinary review over a submitted
# candidate is told nothing, because there is nothing to answer -- and a Job
# admitted under a legacy template is never composed one at all, which is what
# keeps every older delivery byte for byte what it was.

CONTEXT_SCHEMA = "baton.native-handoff-context/1"


def delivered_context(store, custody, authority, *, role, job_id, stage_id,
                      episode):
    """The native handoff context one attempt is delivered, or `None`.

    FAIL-CLOSED ON AN UNCONFIGURED DEPLOYMENT. A Job admitted under a
    handoff-capable template in a deployment that configures no native routing
    could yield a question nobody is permitted to receive; the Authority would
    refuse that request at the commit, after the provider had spent a turn.
    Refusing at preparation is the same answer given before anything is spent.

    A CONTINUATION CARRIES THE EXACT MESSAGES, read back from the Authority by
    the identities the committed continuation record names -- never the
    deployment's memory of them. The reply's task digest was already proved
    equal to the yield's when the continuation was admitted, so what is
    delivered here is the same admitted task's own correspondence.
    """
    boundaries.identity(job_id, "a Job identity")
    boundaries.identity(stage_id, "a stage id")
    boundaries.generation(episode, "an episode number")
    if not handoff_capable(store, job_id):
        return None
    routing = authority.native_routing()
    if routing is None:
        _refuse(f"Job {name_value(job_id)} is admitted under a handoff-capable "
                f"template and this deployment configures no native handoff "
                f"routing; a request would have no permitted recipient, so "
                f"the attempt is refused before a provider turn is spent",
                category="policy", code="denied")
    if role == "implementation":
        held = {"schema": CONTEXT_SCHEMA, "role": role, "job_id": job_id,
                "recipient": routing["reviewer"], "continuation": None}
        prior = (continuation_of(store, stage_id, episode - 1)
                 if episode > 1 else None)
        if prior is not None:
            request = authority.work_message(prior["request_id"])
            reply = authority.work_message(prior["message_id"])
            if request is None or reply is None:
                _refuse(f"the committed continuation of stage "
                        f"{name_value(stage_id)} episode {episode - 1} names "
                        f"messages this Authority does not hold; a resumed "
                        f"attempt is delivered the exact correspondence it "
                        f"continues on", category="integrity", code="schema")
            held["continuation"] = {"request": request, "reply": reply,
                                    "checkpoint_id": prior["checkpoint_id"]}
        return held
    if role != "review":
        return None
    stages = episodes._stored_pair(store, job_id)
    implementation = stages["implementation"]
    live = episodes.live_of(store, implementation["stage_id"])
    if live is None:
        return None
    yielded = yield_of(store, implementation["stage_id"], live["episode"])
    if yielded is None or continuation_of(
            store, implementation["stage_id"], live["episode"]) is not None:
        return None
    request = authority.work_message(yielded["message_id"])
    if request is None:
        _refuse(f"the yield of stage {name_value(implementation['stage_id'])} "
                f"episode {live['episode']} names a message this Authority "
                f"does not hold", category="integrity", code="schema")
    checkpoint = review_cycles.checkpoint_of(custody, yielded["checkpoint_id"])
    return {"schema": CONTEXT_SCHEMA, "role": role, "job_id": job_id,
            "request": request,
            "checkpoint": {"reference": request["checkpoint_ref"],
                           "digest": digest(checkpoint["evidence"])}}


def context_bytes(document):
    """The delivered document as the exact bytes it is published and
    re-proved as: canonical, sorted, compact."""
    if document is None:
        return None
    return json.dumps(document, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


# -- the participant-bound seam the endings reach the Authority through -------
#
# W385331. WHY A PORT AND NOT AN AUTHORITY HANDLE. `review_driver` holds the
# control store and an adapter; it must not hold the Authority or a session for
# any participant but the one whose attempt it is ending. So the two directions
# are composed here from sessions the deployment already minted -- exactly how
# `integration.driver`'s publication seam already works -- and each direction's
# authorization is its own:
#
#   * `request` is carried out UNDER the requesting assignment, which the
#     Authority compares and swaps. A worker-supplied author identity cannot
#     substitute for it, and there is nowhere in the call for one.
#   * `answer` is authorized by the configured `answer-handoff` capability in
#     the requested Work's own effective scope. The reviewer holds no
#     assignment on the Work it is answering about, which is why it is an actor
#     transition and not an assignment-owned one.
#
# BOTH OPERATION IDENTITIES ARE DERIVED FROM THE ATTEMPT, so a resumed ending
# replays its own committed message instead of committing a second one -- which
# is what makes the yield and the answer re-enterable at every cut.

REQUEST_OPERATION = "work-message.request"
RESPOND_OPERATION = "work-message.respond"


def message_identity(prefix, operands):
    """One deterministic message identity, derived from what it is about.

    DERIVED RATHER THAN ALLOCATED, for the reason every identity in this
    distribution is: two managers reaching the same act agree on the name, and
    the journal then replays rather than minting a second message for one
    question. The grammar is the frozen `opaqueId`'s, which is what every
    durable identity here is held to.
    """
    return f"{prefix}-{digest(operands)[len('sha256:'):][:24]}"


def cross_bound(classified, checkpoint):
    """The worker's claimed head, held to the checkpoint actually frozen.

    THE ONE CROSS-BINDING THIS SLICE ADDS, and WHERE it is made is the whole
    correction of the first cut. The request is committed under the LIVE
    producer assignment -- the Authority compares and swaps it, and the
    checkpoint freeze is the act that fences and ends that assignment -- so
    the message is committed BEFORE the freeze and names the head object the
    worker says it yielded at. The freeze then records what was actually
    frozen, and this is asked immediately after it: a request about a head the
    line does not stand at is refused, the ending stays unfinished with its
    evidence intact, and nothing is recorded as a yield.

    It is the same cross-binding `review_verdict_from_result` makes for a
    reviewer's claimed base, head and tree, and for its reason: a namespaced
    claim alone says only that somebody wrote members into an output.
    """
    held = classified["handoff"]
    evidence = checkpoint["evidence"]
    if held["checkpoint"]["reference"] != evidence["head"]:
        _refuse(f"this invocation says it yielded at "
                f"{name_value(held['checkpoint']['reference'])} and the "
                f"checkpoint this manager froze records head "
                f"{name_value(evidence['head'])}; a request is about the "
                f"checkpoint that was actually retained",
                category="integrity", code="digest")
    return checkpoint


def _request_operands(control, attempt_id, classified):
    """Everything a request commits, derived from owners rather than claimed.

    THE CHECKPOINT REFERENCE IS THE RETAINED HEAD OBJECT, not a manager
    checkpoint identity: at the moment this commits the checkpoint has not
    been minted yet (see `cross_bound`), and the head object is the one name
    both the worker's own claim and the later frozen evidence spell. The
    reply must name the same reference, and the continuation proves it
    against the frozen checkpoint's head.
    """
    held = classified["handoff"]
    # THE ADMITTED TASK AND SPECIFICATION DIGEST IS THE ATTEMPT'S OWN RECORDED
    # INPUT IDENTITY. `record_attempt` fixes it at the start and the frozen
    # result is compared against it, so it is the one durable value that says
    # which admitted task this invocation was serving -- and an attempt that
    # records none cannot be continued as the same task, so it refuses here
    # rather than committing a question nobody could bind an answer to.
    task_digest = attempts.recorded_input_of(control, attempt_id)
    if task_digest is None:
        _refuse(f"attempt {name_value(attempt_id)} records no input identity; "
                f"a clarification preserves the admitted task and "
                f"specification digest, and this attempt names none")
    return {
        "kind": classified["kind"],
        "body": held,
        "handoff_digest": classified["handoff_digest"],
        "task_digest": task_digest,
        "checkpoint_ref": held["checkpoint"]["reference"],
        "continuation_digest": held["continuation"]["digest"],
        "destination": held["recipient"],
    }


def commit_request(control, session, *, attempt_id, job_id, classified):
    """Commit ONE implementer's request through its own assignment's session.

    THE ASSIGNMENT IS READ FROM THE CONTROL STORE AND NOT FROM AN OPERAND. What
    the Authority authorizes this act by is the exact four-part assignment the
    attempt is fixed to, and the host hands it over verbatim -- so the author,
    the generation and the claim event on the durable row are the binding's.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.identity(job_id, "a Job id")
    fixed = attempts.assignment_of(control, attempt_id)
    expect = {"work_ref": {"authority_uuid": fixed["authority_uuid"],
                           "work_id": fixed["work_id"]},
              "participant": fixed["participant"],
              "generation": fixed["generation"]}
    operands = _request_operands(control, attempt_id, classified)
    message_id = message_identity("message", dict(operands, expect=expect))
    return session.request_handoff(dict(
        operands, expect=expect, job_id=job_id, message_id=message_id,
        operation_id=f"{REQUEST_OPERATION}:{attempt_id}"))


def commit_answer(control, session, *, attempt_id, response):
    """Commit ONE reviewer's reply through the configured answering session.

    THE REQUEST IT ANSWERS COMES OUT OF THE REVIEWER'S OWN CLAIM, and both
    halves of that claim are checked by the Authority against the stored
    request: the identity says WHICH question and the digest says which
    VERSION of it, so a stale or replayed request cannot be answered as a newer
    one and an older reply cannot consume a newer request.

    THE EFFECT IS DERIVED FROM THE DISPOSITION AND IS NOT A SECOND CHOICE. An
    answer within accepted scope earns a continuation; an escalation earns a
    hold. There is no disposition here that earns ownership, acceptance or a
    receipt of any kind.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    held = response["handoff"]
    effect = ("continuation" if held["disposition"] == ANSWER_DISPOSITION
              else "held")
    message_id = message_identity("reply", {
        "reply_to": held["request"]["reference"],
        "handoff_digest": response["handoff_digest"]})
    return session.answer_handoff({
        "operation_id": f"{RESPOND_OPERATION}:{attempt_id}",
        "message_id": message_id,
        "reply_to": held["request"]["reference"],
        "disposition": ("response" if held["disposition"] == ANSWER_DISPOSITION
                        else "escalation"),
        "body": held,
        "handoff_digest": response["handoff_digest"],
        "request_digest": held["request"]["digest"],
        "checkpoint_ref": held["checkpoint"]["reference"],
        "effect": effect,
        "detail": {"disposition": held["disposition"],
                   "response_digest": response["handoff_digest"],
                   "attempt_id": attempt_id}})


class HandoffPort:
    """The two-verb seam `review_driver.HANDOFF_SEAM` names.

    ONE OBJECT PER ENDING, holding the control store, the ONE session this
    direction is authorized through and the Job the stage belongs to. It keeps
    no operand of either act and decides nothing: every fact either commits is
    derived from an owner inside the functions above.
    """

    def __init__(self, control, session, *, job_id):
        self.control = control
        self.session = session
        self.job_id = job_id
        self.requested = []
        self.answered = []

    def request(self, *, attempt_id, handoff):
        held = commit_request(self.control, self.session,
                              attempt_id=attempt_id, job_id=self.job_id,
                              classified=handoff)
        self.requested.append(held)
        return held

    def answer(self, *, attempt_id, response):
        held = commit_answer(self.control, self.session,
                             attempt_id=attempt_id, response=response)
        self.answered.append(held)
        return held


# -- what this module is held to at import ------------------------------------
#
# The two dispositions this module branches on are the handoff contract's own,
# and the two effects are the Authority's. Asserted rather than described,
# because each is a place where two owners could drift apart silently.
assert (ANSWER_DISPOSITION, ESCALATE_DISPOSITION) == (
    "answer", "escalate"), (ANSWER_DISPOSITION, ESCALATE_DISPOSITION)
assert ANSWER_DISPOSITION == review_cycles.RESPONSE_DISPOSITIONS[0]
assert ESCALATE_DISPOSITION == review_cycles.RESPONSE_DISPOSITIONS[1]
# AND THE EFFECT WORD IS THE AUTHORITY'S OWN. A continuation admitted on an
# effect this build spelled differently from the authority that recorded it
# would be a continuation nobody authorized.
assert CONTINUATION_EFFECT == _authority_effect(), CONTINUATION_EFFECT
