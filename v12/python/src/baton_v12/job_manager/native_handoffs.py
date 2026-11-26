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
import os
import stat
from urllib.parse import unquote, urlsplit

from ..contracts import ContractRefusal, digest, digest_of_bytes
from ..contracts.errors import name_value
from ..native_handoff import (ANSWER_DISPOSITION, CLARIFICATION_KIND,
                              ESCALATE_DISPOSITION, FINAL_KIND, FINDING_KIND,
                              HANDOFF_SCHEMA, REQUEST_KINDS, RESPONSE_KIND,
                              check_handoff, handoff_digest)
from ..worker_manager import (attempts, boundaries, frozen_output_of,
                              intake_receipt_of, load_manifest,
                              manager_signature, review_cycles)
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
           "yield_of", "yield_operation_id", "advance_continuation",
           "DELIVERY_KIND", "MAX_RETAINED_CONTINUATION",
           "continuation_custody", "continuation_for_request",
           "delivered_of", "delivery_operation_id", "record_delivery",
           "retained_continuation", "was_asked"]

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
                 "template_version", "continuation")

# THE RETAINED CONTINUATION TRAVELS WITH THE YIELD (review
# 2026-11-20T19-39-15Z R1). The yielding invocation wrote the implementer's
# own account of what remains -- `handoff/continuation.txt` -- and the frozen
# `handoff` output retained it in accepted custody; what the first cut
# delivered to the resumed invocation was the message's DIGEST of it and
# nothing a provider could read. So the exact bytes are resolved out of
# custody when the yield is recorded, proved against the digest the committed
# request names, journalled on the yield record, and re-proved against the
# Authority's digest at delivery. A continuation that cannot be resolved or
# does not match REFUSES the yield rather than silently omitting it.
MAX_RETAINED_CONTINUATION = 1 << 16

# THE DELIVERY RECORD, in the CONTROL store (review 2026-11-20T19-39-15Z R3).
# What one attempt was delivered beside its task is a host fact about THAT
# attempt, journalled under its identity at preparation: a reviewer's reply is
# then bound to the exact pending request this attempt was asked, and an
# invocation that was delivered no question -- an ordinary final review --
# cannot answer one.
DELIVERY_KIND = "native-handoff.delivered"

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
    from .review_driver import REVIEW_CLAIM_NAMESPACE, REVIEW_UNCERTAINTY_CLAIM

    boundaries.identity(attempt_id, "a runtime attempt id")
    frozen, result, fixed = _frozen_result(control, attempt_id, "response")
    verdicts = sorted(
        one["name"] for one in result["outputs"]
        if type(one.get("result_metadata")) is dict
        and any(name in one["result_metadata"] for name in (REVIEW_CLAIM_NAMESPACE, REVIEW_UNCERTAINTY_CLAIM)))
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
                 task_digest, destination, continuation, now=None):
    """Journal that THIS episode stopped at a question rather than a candidate.

    EVERY SELECTOR IS READ FROM THIS STORE rather than accepted: the Job, the
    Work and the template version come from the stage row and the creation
    record, so a caller cannot file a yield against a stage it names
    incorrectly or claim a handoff-capable template for a Job that resolved a
    legacy one.

    REPLAY IS THE JOURNAL'S. The same operands under the same identity replay
    this record; changed operands collide, which is what stops one yielding
    episode from being recorded as two different questions.

    `continuation` IS THE RETAINED TEXT ITSELF, proved here against the
    digest the committed request names: a record that carried a continuation
    its own digest does not vouch for would deliver the resumed invocation
    something nobody asked for.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.identity(message_id, "a Work message identity")
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    if type(continuation) is not str or not continuation \
            or len(continuation.encode("utf-8")) > MAX_RETAINED_CONTINUATION:
        _refuse("a yield records the retained continuation as bounded "
                "non-empty text", category="integrity", code="schema")
    if digest_of_bytes(continuation.encode("utf-8")) != continuation_digest:
        _refuse(f"the retained continuation of attempt "
                f"{name_value(attempt_id)} digests to "
                f"{name_value(digest_of_bytes(continuation.encode('utf-8')))} "
                f"and the committed request names "
                f"{name_value(continuation_digest)}; a yield records the "
                f"exact continuation the request was about",
                category="integrity", code="digest")
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
              "template_version": version, "continuation": continuation}
    operation_id = yield_operation_id(stage_id, episode)
    return store.transact(
        operation_id, YIELD_KIND, job_signature(YIELD_KIND, record),
        lambda connection: record)


def record_hold(store, *, stage_id, episode, message_id, request_id,
                destination, checkpoint_id, question=None):
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
    if question is not None:
        record["question"] = question
    operation_id = hold_operation_id(stage_id, episode)
    previous = hold_of(store, stage_id, episode)
    if previous is not None and "question" not in previous and previous == {key: value for key, value in record.items() if key != "question"}:
        # Pre-main holds have no display text. Re-enter their exact original
        # operation rather than colliding with additive observation metadata.
        return previous
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
      * AN ESCALATION ALONE RESUMES NOTHING. A held reply requires a distinct
        targeted owner decision and the custody transition for that checkpoint.
        The original escalation and its held effect remain immutable.
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
    episode, yielded = _yielding_episode(store, implementation["stage_id"],
                                         live)
    frozen = review_cycles.checkpoint_of(custody, yielded["checkpoint_id"])
    request, reply, effect = _answered_request(
        authority, yielded, "continuation", head=frozen["evidence"]["head"])
    from . import main_thread
    owner_decision = main_thread.decision_of(store, job_id, request["message_id"])
    if owner_decision is not None:
        hold = hold_of(store, implementation["stage_id"], episode)
        if (effect["effect"] != "held" or hold is None
                or owner_decision["phase"] != implementation["stage_id"]
                or owner_decision["checkpoint_id"] != yielded["checkpoint_id"]
                or owner_decision["checkpoint_ref"] != frozen["evidence"]["head"]
                or owner_decision["escalation_id"] != reply["message_id"]
                or owner_decision["author"] != reply["destination"]
                or hold["request_id"] != request["message_id"]):
            _refuse("owner decision does not bind this request, phase and held checkpoint")
    if effect["effect"] != CONTINUATION_EFFECT and owner_decision is None:
        _refuse(f"reply {name_value(reply['message_id'])} earned the effect "
                f"{name_value(effect['effect'])}; an escalation leaves the "
                f"execution held for its configured decision recipient and a "
                f"continuation is not manufactured from it",
                category="policy", code="denied")
    record = {"job_id": job_id, "stage_id": implementation["stage_id"],
              "episode": episode, "message_id": reply["message_id"],
              "request_id": request["message_id"],
              "checkpoint_id": yielded["checkpoint_id"],
              "task_digest": yielded["task_digest"]}
    if owner_decision is not None:
        record["owner_decision"] = owner_decision
    operation_id = continuation_operation_id(implementation["stage_id"],
                                             episode)
    signature = job_signature(CONTINUE_KIND, record)
    found, recorded = store.replay(operation_id, signature,
                                   kind=CONTINUE_KIND)
    if found:
        return recorded
    if episode != live["episode"]:
        # UNREACHABLE WHEN THE JOURNAL IS WHOLE: `_yielding_episode` names a
        # prior episode only because its continuation is committed, and the
        # replay above answers it or collides. Said anyway, because the
        # alternative is opening a second continuation on an ended episode.
        _refuse(f"stage {name_value(implementation['stage_id'])} episode "
                f"{episode} is no longer live and its continuation did not "
                f"replay; a continuation advances the pair it observed")

    review_live = episodes.live_of(store, review["stage_id"])
    if review_live is None:
        _refuse(f"stage {name_value(review['stage_id'])} has no live episode; "
                f"a continuation advances the pair that answered")
    if owner_decision is not None:
        # Do not release custody for a closed Job. The decisive admission
        # fences are repeated in the Job transaction below after this
        # replay-safe cross-store transition.
        closed = job_control.closed_of(store, job_id, now, stage_id=implementation["stage_id"])
        if closed is not None:
            _refuse(job_control.closed_message(closed, "an owner continuation"))
        job_control.refuse_continuation(store._connection, job_id)
        episodes._unheld(store, live, "implementation")
        episodes._unheld(store, review_live, "review")
        review_cycles.hold_owner_continuation(custody, checkpoint_id=yielded["checkpoint_id"], decision=owner_decision, response_digest=reply["handoff_digest"])
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


def _yielding_episode(store, stage_id, live):
    """The episode a continuation is ABOUT, and its yield record.

    REVIEW 2026-11-20T19-39-15Z R2. The first cut derived the retry from the
    LIVE episode and required its yield -- and after a continuation commits
    the live episode is the successor it opened, which asked nothing. So the
    exact second invocation of the public act, the one a crashed ending's
    re-entry makes, refused with "recorded no yield" instead of returning the
    receipt it had committed.

    THE RETRY IS BOUND TO THE ORIGINAL YIELD. A live episode that yielded is
    the ordinary case; a live episode that did not, whose predecessor BOTH
    yielded AND carries a committed continuation, is the retry of that
    continuation, and the record is rebuilt from the predecessor's own yield
    and the Authority's reply so the journal can answer it -- or collide on
    changed operands. Anything else is a continuation following nothing.
    """
    yielded = yield_of(store, stage_id, live["episode"])
    if yielded is not None:
        return live["episode"], yielded
    prior = live["episode"] - 1
    if prior >= 1 and continuation_of(store, stage_id, prior) is not None:
        yielded = yield_of(store, stage_id, prior)
        if yielded is not None:
            return prior, yielded
    _refuse(f"stage {name_value(stage_id)} episode {live['episode']} "
            f"recorded no yield; a continuation follows a durable request "
            f"and nothing else")


def continuation_for_request(store, *, job_id, request_id):
    """The COMMITTED continuation that answered this request, or `None`.

    THE SERVING SIDE'S RETRY QUESTION (review 2026-11-20T19-39-15Z R2): a
    deployment that guards the continuation allowance BEFORE it asks the act
    must first know whether the act already happened, or an exact retry of a
    committed continuation reads as a second one and is declined for
    exhaustion. Keyed by the REQUEST, which is the one identity the reply the
    deployment holds and the yield record both name.
    """
    boundaries.identity(job_id, "a Job identity")
    boundaries.identity(request_id, "a Work message identity")
    stage_id = episodes._stored_pair(store, job_id)["implementation"]["stage_id"]
    live = episodes.live_of(store, stage_id)
    if live is None:
        return None
    for episode in (live["episode"], live["episode"] - 1):
        if episode < 1:
            continue
        yielded = yield_of(store, stage_id, episode)
        if yielded is None or yielded["message_id"] != request_id:
            continue
        return continuation_of(store, stage_id, episode)
    return None


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
            # THE RETAINED CONTINUATION ITSELF, re-proved against the
            # Authority's digest at the moment of delivery: the yield record
            # journalled the text, the committed request says what the text
            # must digest to, and a record that no longer agrees with the
            # message delivers nothing rather than something else.
            yielded = yield_of(store, stage_id, episode - 1)
            text = None if yielded is None else yielded.get("continuation")
            if type(text) is not str or digest_of_bytes(
                    text.encode("utf-8")) != request["continuation_digest"]:
                _refuse(f"the retained continuation of stage "
                        f"{name_value(stage_id)} episode {episode - 1} is "
                        f"missing or does not digest to "
                        f"{name_value(request['continuation_digest'])}, "
                        f"which request {name_value(request['message_id'])} "
                        f"committed; a resumed attempt is delivered the exact "
                        f"continuation it yielded or it is not resumed",
                        category="integrity", code="digest")
            held["continuation"] = {"request": request, "reply": reply,
                                    "checkpoint_id": prior["checkpoint_id"],
                                    "text": text}
            if prior.get("owner_decision") is not None:
                held["continuation"]["owner_decision"] = prior["owner_decision"]
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


def retained_continuation(result, receipt, classified):
    """The exact continuation bytes the yielding invocation retained, read out
    of ACCEPTED CUSTODY and proved three ways.

    THREE OWNERS AND ONE TEXT. The frozen result's `handoff` output names the
    artifact and measures its entries; the intake receipt says where this
    manager keeps that artifact; the classified handoff says what the
    continuation must digest to. The bytes are read no-follow out of the
    custody directory the receipt names, held to the entry's measured size and
    content digest, and then to the handoff's own continuation digest. A
    missing, moved, oversized or tampered continuation REFUSES -- the yield is
    not recorded and the ending stays unfinished with its evidence intact --
    rather than being omitted from what the resumed invocation is told.
    """
    held = classified["handoff"]
    reference = held["continuation"]["reference"]
    prefix = HANDOFF_OUTPUT + "/"
    name = reference[len(prefix):] if reference.startswith(prefix) else ""
    if not name or "/" in name or name in (".", ".."):
        _refuse(f"the handoff names its continuation at "
                f"{name_value(reference)}; a retained continuation is one "
                f"member of the {name_value(HANDOFF_OUTPUT)} output",
                category="integrity", code="schema")
    output = _sole_output(result, HANDOFF_OUTPUT, "continuation")
    entries = [one for one in output["content_manifest"]["entries"]
               if one["path"] == name]
    if len(entries) != 1:
        _refuse(f"the frozen {name_value(HANDOFF_OUTPUT)} output measures "
                f"{len(entries)} entries named {name_value(name)}; the "
                f"retained continuation is exactly one measured entry",
                category="integrity", code="schema")
    entry = entries[0]
    if entry["bytes"] > MAX_RETAINED_CONTINUATION:
        _refuse(f"the retained continuation measures {entry['bytes']} bytes "
                f"and this manager delivers at most "
                f"{MAX_RETAINED_CONTINUATION}", category="integrity",
                code="schema")
    if type(receipt) is not dict or receipt.get("custody") != "accepted":
        _refuse("the retained continuation is read out of ACCEPTED custody "
                "and this attempt's intake receipt records none")
    wanted = output["artifact"]["artifact_id"]
    artifacts = [one for one in receipt.get("artifacts") or ()
                 if type(one) is dict and one.get("artifact_id") == wanted]
    if len(artifacts) != 1:
        _refuse(f"the intake receipt holds {len(artifacts)} custody entries "
                f"for artifact {name_value(wanted)}; the retained "
                f"continuation is read from exactly one",
                category="integrity", code="schema")
    locator = urlsplit(artifacts[0].get("custody_locator") or "")
    if locator.scheme != "file" or locator.netloc or locator.query \
            or locator.fragment or not locator.path:
        _refuse("the retained continuation is read from local accepted "
                "custody and this receipt's locator is not one")
    try:
        holding = os.open(unquote(locator.path),
                          os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as refused:
        _refuse(f"the custody directory of the retained "
                f"{name_value(HANDOFF_OUTPUT)} output is not readable "
                f"({type(refused).__name__})")
    try:
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW
                                 | os.O_NONBLOCK, dir_fd=holding)
        except OSError as refused:
            _refuse(f"the retained continuation {name_value(reference)} is "
                    f"not in accepted custody ({type(refused).__name__}); a "
                    f"resumed invocation is delivered the exact continuation "
                    f"or the yield is not recorded",
                    category="integrity", code="digest")
    finally:
        os.close(holding)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            _refuse("the retained continuation is not a regular file",
                    category="integrity", code="schema")
        raw = os.read(descriptor, entry["bytes"] + 1)
    finally:
        os.close(descriptor)
    if len(raw) != entry["bytes"] \
            or digest_of_bytes(raw) != entry["content_digest"]:
        _refuse(f"the retained continuation {name_value(reference)} differs "
                f"from the frozen custody that measured it; a tampered "
                f"continuation is not delivered",
                category="integrity", code="digest")
    if digest_of_bytes(raw) != held["continuation"]["digest"]:
        _refuse(f"the retained continuation digests to "
                f"{name_value(digest_of_bytes(raw))} and the handoff names "
                f"{name_value(held['continuation']['digest'])}; the "
                f"continuation delivered is the one the request was about",
                category="integrity", code="digest")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        _refuse("the retained continuation is UTF-8 text",
                category="integrity", code="schema")


def continuation_custody(control, attempt_id, classified):
    """`retained_continuation` over the control store's own account of one
    yielding attempt: its frozen result, cross-bound to the attempt, and its
    intake receipt."""
    boundaries.identity(attempt_id, "a runtime attempt id")
    _frozen, result, _fixed = _frozen_result(control, attempt_id,
                                             "continuation")
    receipt = intake_receipt_of(control, attempt_id)
    if receipt is None:
        _refuse(f"attempt {name_value(attempt_id)} has no intake receipt; the "
                f"retained continuation is read out of accepted custody")
    return retained_continuation(result, receipt, classified)


def delivery_operation_id(attempt_id):
    boundaries.identity(attempt_id, "a runtime attempt id")
    return f"{DELIVERY_KIND}:{attempt_id}"


def record_delivery(control, *, attempt_id, document):
    """Journal, in the control store, WHAT THIS ATTEMPT WAS DELIVERED.

    ONE RECORD PER ATTEMPT, UNDER ITS IDENTITY, and the operands are the
    delivered document itself: a restart that recomposes the same delivery
    replays, and a different document under one attempt collides -- an
    attempt is told one thing. Written by the composition that composes the
    document, at preparation, before the task is admitted; read by the
    answer commit, which binds a reviewer's reply to the exact pending
    request THIS attempt was asked and refuses every other.
    """
    if type(document) is not dict or document.get("schema") != CONTEXT_SCHEMA:
        _refuse(f"a delivery record carries one "
                f"{name_value(CONTEXT_SCHEMA)} document",
                category="integrity", code="schema")
    record = {"attempt_id": attempt_id, "document": document}
    return control.transact(delivery_operation_id(attempt_id), DELIVERY_KIND,
                            manager_signature(DELIVERY_KIND, record),
                            lambda _connection: dict(record))


def delivered_of(control, attempt_id):
    """The document this attempt was delivered beside its task, or `None`."""
    row = control.operation_record(delivery_operation_id(attempt_id))
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    record = json.loads(row["result"])
    if type(record) is not dict or record.get("attempt_id") != attempt_id \
            or type(record.get("document")) is not dict:
        _refuse(f"the committed delivery record of attempt "
                f"{name_value(attempt_id)} is not one this build can read",
                category="integrity", code="schema")
    return record["document"]


def was_asked(control, attempt_id):
    """Whether this attempt was DELIVERED A PENDING REQUEST, as a boolean.

    THE DISPATCH FACT FOR A REVIEW ENDING, read from the delivery record
    rather than recomposed: a review attempt that was asked a question takes
    the response ending whatever its result declares, and one that was asked
    nothing is an ordinary final technical review. Recomposing the context at
    ending time answered differently once the continuation had moved the
    implementation episode on, which is exactly when a deferred response
    ending re-enters.
    """
    delivered = delivered_of(control, attempt_id)
    return (delivered is not None and delivered.get("role") == "review"
            and type(delivered.get("request")) is dict)


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


def commit_answer(control, session, *, attempt_id, response, job_id):
    """Commit ONE reviewer's reply through the configured answering session.

    THE REQUEST IT ANSWERS IS THE ONE THIS ATTEMPT WAS DELIVERED, and the
    reviewer's own claim is held to it before anything reaches the Authority
    (review 2026-11-20T19-39-15Z R3). The first cut let the Authority check
    the named request's recipient, capability, digest and head -- all facts
    about the REQUEST -- and nothing bound the reply to the review invocation
    that was making it, so a frozen result on Work A could answer Work B's
    question when one reviewer held grants on both. Now, before the commit:

      * the review attempt's FIXED assignment names the Work and participant
        this reply is made for;
      * the control store's own delivery record says which pending request
        THIS attempt was asked -- an attempt delivered none is an ordinary
        final review, and its declared response is refused as unsolicited;
      * the delivered request's Work, Job and destination must be this
        assignment's, this port's Job and this participant; and
      * the reviewer's claimed request identity, request digest and checkpoint
        reference must be the delivered ones -- a stale request, a newer
        version of it, or another checkpoint refuses.

    The Authority then binds the same Work and Job again under its own rules,
    with the capability in the requested Work's effective scope, so the
    signed reply records which Work and Job it was authorized against.

    THE EFFECT IS DERIVED FROM THE DISPOSITION AND IS NOT A SECOND CHOICE. An
    answer within accepted scope earns a continuation; an escalation earns a
    hold. There is no disposition here that earns ownership, acceptance or a
    receipt of any kind.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.identity(job_id, "a Job id")
    held = response["handoff"]
    fixed = attempts.assignment_of(control, attempt_id)
    acting = getattr(session, "participant", None)
    if acting != fixed["participant"]:
        _refuse(f"the answering session acts for {name_value(acting)} and "
                f"attempt {name_value(attempt_id)} is fixed to "
                f"{name_value(fixed['participant'])}; a reply is committed "
                f"through the answering assignment's own session",
                category="refused", code="capability")
    delivered = delivered_of(control, attempt_id)
    request = None if delivered is None else delivered.get("request")
    if delivered is None or delivered.get("role") != "review" \
            or type(request) is not dict:
        _refuse(f"attempt {name_value(attempt_id)} was delivered no pending "
                f"request; a response from an invocation that was asked no "
                f"question is unsolicited and is not committed")
    if delivered.get("job_id") != job_id or request.get("job_id") != job_id:
        _refuse(f"attempt {name_value(attempt_id)} was delivered a request "
                f"of Job {name_value(request.get('job_id'))} and this reply "
                f"is committed for Job {name_value(job_id)}; a reply answers "
                f"the Job that asked", category="integrity", code="schema")
    if request.get("work_id") != fixed["work_id"]:
        _refuse(f"the request delivered to attempt {name_value(attempt_id)} "
                f"belongs to {name_value(request.get('work_id'))} and the "
                f"attempt is fixed to {name_value(fixed['work_id'])}; a "
                f"reply answers its own Work's request",
                category="integrity", code="schema")
    if request.get("destination") != fixed["participant"]:
        _refuse(f"the request delivered to attempt {name_value(attempt_id)} "
                f"is addressed to {name_value(request.get('destination'))} "
                f"and the attempt is fixed to "
                f"{name_value(fixed['participant'])}; a reply is made by the "
                f"participant the question was addressed to",
                category="refused", code="capability")
    if held["request"]["reference"] != request.get("message_id"):
        _refuse(f"this response answers request "
                f"{name_value(held['request']['reference'])} and attempt "
                f"{name_value(attempt_id)} was delivered "
                f"{name_value(request.get('message_id'))}; a reply answers "
                f"the exact pending request it was asked and never "
                f"another", category="integrity", code="schema")
    if held["request"]["digest"] != request.get("handoff_digest"):
        _refuse(f"this response binds request digest "
                f"{name_value(held['request']['digest'])} and the delivered "
                f"request carries "
                f"{name_value(request.get('handoff_digest'))}; a reply is "
                f"about the version of the question it was delivered",
                category="integrity", code="digest")
    checkpoint = (delivered.get("checkpoint") or {}).get("reference")
    if held["checkpoint"]["reference"] != checkpoint \
            or request.get("checkpoint_ref") != checkpoint:
        _refuse(f"this response names checkpoint "
                f"{name_value(held['checkpoint']['reference'])} and attempt "
                f"{name_value(attempt_id)} was delivered "
                f"{name_value(checkpoint)}; an answer preserves the exact "
                f"retained checkpoint it was asked about",
                category="integrity", code="digest")
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
                   "attempt_id": attempt_id},
        "work_id": fixed["work_id"], "job_id": job_id})


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
                             attempt_id=attempt_id, response=response,
                             job_id=self.job_id)
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
