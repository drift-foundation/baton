"""THE DURABLE ATTRIBUTED WORK MESSAGE, and the one effect it can earn.

W385331, first vertical native communication slice.

WHAT THIS OWNS. Three transitions and five reads over `work_message` and
`work_message_transition`:

  * an implementer's CLARIFICATION or within-scope FINDING request, carried out
    under its own exact assignment and addressed to a configured recipient;
  * the configured reviewer's RESPONSE to exactly one pending request, which
    either resolves it inside accepted scope or ESCALATES it once; and
  * the separate TRANSITION RECEIPT for the ownership effect a response earns.

WHAT IT IS NOT, and each boundary is one the slice states in terms:

  * NOT A SECOND AUTHORITY. The assignment compare-and-swap, the claim event, the
    fence, the capability resolution and the operation journal are the ones this
    package already has. This module composes them; it does not add a parallel
    one, a generic chat system or an activity-log parser.
  * NOT AN APPROVAL. No receipt of any kind is written here. A response is a
    clarification or discovery interpretation and the vocabulary has no word for
    accepting a candidate -- so there is no path from a message to a
    verification, review, approval or integration receipt.
  * NOT A ROUTER. Which route the Work moves to afterwards is the existing
    route transition's, performed by its existing owner. What a message earns is
    a recorded EFFECT, and the Job-side owner is what carries it out.
  * NOT A CONTENT READER. The request and response BODIES are bounded canonical
    text whose shape `baton_v12.native_handoff` owns. This module refuses to
    accept one that is not already that document, and it reads nothing out of it
    beyond the members its own columns bind.

THE ATTRIBUTION IS THE WHOLE POINT. A worker has no host-store access and no
session: the host commits a message THROUGH the participant-bound session of
the assignment that produced it, so the author on every row is the binding's
and never an operand's. A stale or replayed request cannot consume or answer a
newer one, because every write is an assignment-owned act that compares and
swaps, and because a reply names the exact request identity AND its digest.
"""

import json

from .errors import Refusal, label_of, name_of
from .identity import (check_opaque_id, check_participant, check_text,
                       normalize_assignment, signature_of)

__all__ = ["MESSAGE_KINDS", "REQUEST_KINDS", "RESPONSE_KIND",
           "ESCALATION_KIND", "EFFECTS", "CONTINUATION_EFFECT", "HELD_EFFECT",
           "ANSWER_CAPABILITY", "ROUTING_POLICY", "ROUTING_SCHEMA",
           "ROUTING_MEMBERS", "MAX_MESSAGE_BYTES", "check_routing",
           "message_document", "transition_document"]

# WHICH KINDS A ROW MAY CARRY. The first two are the requests an implementer
# yields; `response` is a reviewer's resolution within accepted scope; and
# `escalation` is the ONE record a reviewer that cannot resolve a request
# leaves for the configured decision recipient. The escalation is a separate
# KIND rather than a disposition column, because what distinguishes it is WHO
# it is addressed to and what it leaves held.
REQUEST_KINDS = ("clarification-request", "finding-request")
RESPONSE_KIND = "response"
ESCALATION_KIND = "escalation"
MESSAGE_KINDS = REQUEST_KINDS + (RESPONSE_KIND, ESCALATION_KIND)

# THE TWO EFFECTS A REPLY CAN EARN, and neither of them is ownership. A
# `continuation` says the same admitted task may resume once; `held` says the
# execution stays held for a decision recipient. There is deliberately no
# `accepted`, `approved` or `integrated`.
CONTINUATION_EFFECT = "continuation"
HELD_EFFECT = "held"
EFFECTS = (CONTINUATION_EFFECT, HELD_EFFECT)

# THE NEW CAPABILITY, bound explicitly to the intended native reviewer in the
# relevant Work's own effective scope. Named here because this module is what
# requires it; `core.CAPABILITIES` registers it so a deployment configures it
# from one list.
#
# IT IS A NEW CAPABILITY AND NOT A REUSE. The slice is explicit that existing
# `review` membership or route handling grants no new capability by
# implication: `review` writes a technical review receipt about a candidate,
# and answering a question is not that act.
ANSWER_CAPABILITY = "answer-handoff"

# WHERE THE CONFIGURED ROUTING LIVES, and it is deployment POLICY rather than
# anything a request can state. `core.policy` is the generic durable key/value
# and this is the semantic accessor for one key, exactly as `canonical_target`
# is for its own -- generic storage plus a specific meaning is where a type has
# to be asserted.
ROUTING_POLICY = "native_handoff_routing"
ROUTING_SCHEMA = "baton.native-handoff-routing/1"
ROUTING_MEMBERS = ("schema", "reviewer", "decision_recipient")

# The encoded ceiling for one retained message body. It is the handoff
# contract's own bound; a document wider than that never validated, so a row
# wider than that cannot be one this authority admitted.
MAX_MESSAGE_BYTES = 16384

_DIGEST_PREFIX = "sha256:"
_DIGEST_LENGTH = len(_DIGEST_PREFIX) + 64


def _digest(value, what):
    # The LABEL is caller text at every helper here, so it is bound by the
    # rule, once, where it is accepted -- `errors.label_of`'s own statement of
    # why, applied at every boundary in this module that renders one.
    what = label_of(what)
    check_text(value, what)
    if not value.startswith(_DIGEST_PREFIX) or len(value) != _DIGEST_LENGTH \
            or any(one not in "0123456789abcdef"
                   for one in value[len(_DIGEST_PREFIX):]):
        raise Refusal(f"{what} is a {_DIGEST_PREFIX} digest of 64 lowercase "
                      f"hex characters; this is {name_of(value)}")
    return value


def check_routing(document, *, what="the configured native handoff routing"):
    """The one policy document this module reads SEMANTICALLY.

    TWO CONFIGURED ADDRESSES AND THEY MAY NOT BE THE SAME ONE. The reviewer is
    who an implementer's request may be addressed to; the decision recipient is
    who an unresolved request escalates to. A deployment that configured one
    address for both would be routing a decision back to the same reviewer
    under another label, which is the thing the planning disposition forbids by
    name -- so it is refused HERE, at configuration read, rather than
    discovered at the escalation.
    """
    what = label_of(what)
    if type(document) is not dict:
        raise Refusal(f"{what} is one object; this is {name_of(document)}")
    missing = [one for one in ROUTING_MEMBERS if one not in document]
    # BOUNDED THROUGH THE LABEL RULE, because the member names a rejected
    # policy document carries are the WRITER'S text and a policy value is any
    # owned JSON -- so an object with a one-million-character member name would
    # otherwise render one.
    extra = sorted(one for one in document if one not in ROUTING_MEMBERS)
    if missing or extra:
        raise Refusal(f"{what} is exactly {', '.join(ROUTING_MEMBERS)}"
                      + (f"; missing {label_of(', '.join(missing))}"
                         if missing else "")
                      + (f"; unexpected {label_of(', '.join(extra))}"
                         if extra else ""))
    if document["schema"] != ROUTING_SCHEMA:
        raise Refusal(f"{what} is {name_of(ROUTING_SCHEMA)}; this says it is "
                      f"{name_of(document['schema'])}")
    for member in ("reviewer", "decision_recipient"):
        check_participant(document[member],
                          what=f"{what}'s {member} is one endpoint address")
    if document["reviewer"] == document["decision_recipient"]:
        raise Refusal(
            f"{what} configures {name_of(document['reviewer'])} as both the "
            f"reviewer and the decision recipient; an escalation goes to a "
            f"HIGHER authority, and routing a decision back to the same "
            f"reviewer under another label is not one")
    return {member: document[member] for member in ROUTING_MEMBERS}


def message_document(row):
    """One retained message as a fresh built-in document.

    THE SAME RECORD SERVES HUMANS AND AGENTS, which is the slice's own rule:
    there is one read model and not a second rendering for operators.
    """
    return {"message_id": row["message_id"], "work_id": row["work_id"],
            "job_id": row["job_id"], "author": row["author"],
            "generation": row["generation"], "claim_seq": row["claim_seq"],
            "kind": row["kind"], "body": json.loads(row["body"]),
            "handoff_digest": row["handoff_digest"],
            "reply_to": row["reply_to"],
            "checkpoint_ref": row["checkpoint_ref"],
            "continuation_digest": row["continuation_digest"],
            "task_digest": row["task_digest"],
            "destination": row["destination"],
            "operation_id": row["operation_id"],
            "recorded_at": row["recorded_at"]}


def transition_document(row):
    return {"message_id": row["message_id"], "work_id": row["work_id"],
            "effect": row["effect"], "detail": json.loads(row["detail"]),
            "operation_id": row["operation_id"],
            "recorded_at": row["recorded_at"]}


# -- the reads ----------------------------------------------------------------


def messages_of(core, work_id):
    """Every message of ONE Work, in the order they committed."""
    work = core._work(work_id)
    return [message_document(row) for row in core._store.all(
        "SELECT * FROM work_message WHERE work_id = ? ORDER BY seq",
        work["work_id"])]


def message_of(core, message_id):
    check_opaque_id(message_id, "a message id")
    row = core._store.get(
        "SELECT * FROM work_message WHERE message_id = ?", message_id)
    return None if row is None else message_document(row)


def reply_of(core, message_id):
    """The ONE reply to this request, or `None`.

    `None` IS AN ORDINARY ANSWER. A request nobody has answered yet is the
    whole reason the requesting execution is held, and treating absence as an
    error would make every pending request a fault.
    """
    check_opaque_id(message_id, "a message id")
    row = core._store.get(
        "SELECT * FROM work_message WHERE reply_to = ?", message_id)
    return None if row is None else message_document(row)


def transition_of(core, message_id):
    check_opaque_id(message_id, "a message id")
    row = core._store.get(
        "SELECT * FROM work_message_transition WHERE message_id = ?",
        message_id)
    return None if row is None else transition_document(row)


def pending_requests_of(core, work_id):
    """The requests of this Work that nothing has replied to, in order.

    DERIVED FROM THE ROWS AND NOT FROM A FLAG. A `pending` column would be a
    second account of the same fact, and the reply index already answers it
    exactly.
    """
    held = []
    for one in messages_of(core, work_id):
        if one["kind"] in REQUEST_KINDS and reply_of(core, one["message_id"]) \
                is None:
            held.append(one)
    return held


def escalations_of(core, work_id):
    return [one for one in messages_of(core, work_id)
            if one["kind"] == ESCALATION_KIND]


# -- the transitions ----------------------------------------------------------


def _bounded_body(body, what):
    """The handoff document this row retains, bounded at its own ceiling.

    NOT RE-VALIDATED AGAINST THE HANDOFF CONTRACT HERE, and that is
    deliberate rather than an omission: `baton_v12.native_handoff` is the owner
    of that shape and this package is standard-library only and imports nothing
    from the manager side. What this boundary owes is that the retained bytes
    are canonical, bounded owned JSON -- which is what makes the digest beside
    them reproducible and the row readable back.
    """
    from .identity import own

    what = label_of(what)
    taken = own(body, what=what)
    if type(taken) is not dict:
        raise Refusal(f"{what} is one object; this is {name_of(body)}")
    encoded = json.dumps(taken, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise Refusal(f"{what} is {len(encoded)} encoded bytes and this "
                      f"authority retains at most {MAX_MESSAGE_BYTES}")
    return taken, encoded


def _free_message_id(core, message_id, kind):
    kind = label_of(kind)
    held = core._store.get(
        "SELECT kind, work_id FROM work_message WHERE message_id = ?",
        message_id)
    if held is not None:
        raise Refusal(
            f"message identity {name_of(message_id)} is already the "
            f"{name_of(held['kind'])} of {name_of(held['work_id'])}; a {kind} "
            f"needs its own")


def request(core, expect, *, operation_id, message_id, job_id, kind, body,
            handoff_digest, task_digest, checkpoint_ref, continuation_digest,
            destination):
    """An implementer's clarification or in-scope finding request.

    EVERY ATTRIBUTION FACT IS THE AUTHORITY'S. `expect` is the exact assignment
    this act is carried out under, compared and swapped by `_expect`, and the
    author and generation written below come from it -- so a worker that
    produced the handoff cannot name itself, name another participant, or act
    under a generation that has been fenced.

    THE DESTINATION IS AUTHENTICATED AGAINST THE CONFIGURED ROUTING and not
    against the document. A request may be addressed only to the configured
    reviewer: a deployment that configured none admits no request at all, which
    is the fail-closed direction -- an unconfigured destination is not "send it
    anywhere".

    AND A REQUEST IS NOT ADDRESSED TO ITS OWN AUTHOR. A participant asking
    itself a question is a self-route, and one durable pending request per
    requesting assignment is the bound the slice sets; a second pending request
    from the same assignment refuses rather than queueing.
    """
    expect = normalize_assignment(expect)
    check_opaque_id(message_id, "a message id")
    check_opaque_id(job_id, "a Job id")
    if kind not in REQUEST_KINDS:
        raise Refusal(f"a native request is one of {', '.join(REQUEST_KINDS)}; "
                      f"this is {name_of(kind)}")
    _digest(handoff_digest, "a request's handoff digest")
    _digest(task_digest, "a request's admitted task digest")
    check_text(checkpoint_ref, "a request's retained checkpoint reference")
    _digest(continuation_digest, "a request's continuation digest")
    check_participant(destination,
                      what="a request names one permitted recipient")
    taken, encoded = _bounded_body(body, "a native request body")

    def body_():
        work = core._expect(expect)
        routing = core.native_routing()
        if routing is None:
            raise Refusal(
                "this deployment configures no native handoff routing; a "
                "request is authenticated against its configured allowed "
                "destinations, and an unconfigured destination admits nothing")
        if destination != routing["reviewer"]:
            raise Refusal(
                f"a native request may be addressed to the configured "
                f"reviewer {name_of(routing['reviewer'])} and this names "
                f"{name_of(destination)}; a permitted recipient is the "
                f"deployment's fact and not the requester's")
        if destination == expect["participant"]:
            raise Refusal(
                f"{name_of(destination)} is the requesting assignment's own "
                f"participant; a request is not addressed to its own author")
        _free_message_id(core, message_id, kind)
        standing = [one for one in pending_requests_of(core, work["work_id"])
                    if one["author"] == expect["participant"]
                    and one["generation"] == expect["generation"]]
        if standing:
            raise Refusal(
                f"assignment {name_of(expect['participant'])} already holds "
                f"the unanswered request "
                f"{name_of(standing[0]['message_id'])} on "
                f"{name_of(work['work_id'])}; one durable pending request per "
                f"assignment, and a second is not queued behind it")
        claim_seq = core._live_claim_seq(expect)
        core._store.run(
            "INSERT INTO work_message (message_id, work_id, job_id, author, "
            "generation, claim_seq, kind, body, handoff_digest, reply_to, "
            "checkpoint_ref, continuation_digest, task_digest, destination, "
            "operation_id, recorded_at) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)",
            message_id, work["work_id"], job_id, expect["participant"],
            expect["generation"], claim_seq, kind, encoded, handoff_digest,
            checkpoint_ref, continuation_digest, task_digest, destination,
            operation_id, core._now())
        return message_of(core, message_id)

    return core._replay(
        operation_id,
        signature_of("work-message.request",
                     {"expect": expect, "message_id": message_id,
                      "job_id": job_id, "kind": kind, "body": taken,
                      "handoff_digest": handoff_digest,
                      "task_digest": task_digest,
                      "checkpoint_ref": checkpoint_ref,
                      "continuation_digest": continuation_digest,
                      "destination": destination}), body_)


def respond(core, *, operation_id, message_id, reply_to, actor, disposition,
            body, handoff_digest, request_digest, checkpoint_ref, effect,
            detail):
    """The configured reviewer's ONE reply to ONE pending request.

    AUTHORIZED BY A CAPABILITY IN THE REQUESTED WORK'S OWN EFFECTIVE SCOPE, and
    the scope is derived from the request's Work row rather than from an
    operand. `_require_capability` is the existing seam and it answers the
    decision, which is recorded under this message's identity -- so who
    answered, as which principal, in which scope and by which grant is all one
    durable fact.

    THE REPLY BINDS THE REQUEST BY IDENTITY AND BY DIGEST. Naming the identity
    alone would let a reply arrive for a request whose body was something else;
    naming the digest alone would not say which request. Both, so a stale or
    replayed request cannot be answered as a newer one and a newer one cannot
    be answered by an older reply.

    AND THE EFFECT IS RECORDED SEPARATELY, in one transaction with the message
    but in its own relation: an answer earns a `continuation` and an escalation
    earns a `held`, and no reply of any disposition earns a receipt.
    """
    check_opaque_id(message_id, "a message id")
    check_opaque_id(reply_to, "a replied-to message id")
    if disposition not in (RESPONSE_KIND, ESCALATION_KIND):
        raise Refusal(f"a reply is a {RESPONSE_KIND} or an {ESCALATION_KIND}; "
                      f"this is {name_of(disposition)}")
    if effect not in EFFECTS:
        raise Refusal(f"a reply's effect is one of {', '.join(EFFECTS)}; this "
                      f"is {name_of(effect)}")
    _digest(handoff_digest, "a reply's handoff digest")
    _digest(request_digest, "the request digest a reply binds")
    check_text(checkpoint_ref, "the checkpoint a reply names")
    taken, encoded = _bounded_body(body, "a native reply body")
    held, detail_text = _bounded_body(detail, "a reply's effect detail")

    def body_():
        asked = message_of(core, reply_to)
        if asked is None:
            raise Refusal(
                f"there is no message {name_of(reply_to)} in this authority; a "
                f"reply names the exact pending request it answers")
        if asked["kind"] not in REQUEST_KINDS:
            raise Refusal(
                f"message {name_of(reply_to)} is a {name_of(asked['kind'])} "
                f"and a reply answers a request; one reply chain and no "
                f"answers to answers")
        if asked["handoff_digest"] != request_digest:
            raise Refusal(
                f"request {name_of(reply_to)} carries handoff digest "
                f"{name_of(asked['handoff_digest'])} and this reply binds "
                f"{name_of(request_digest)}; a reply is about the request it "
                f"names")
        if asked["checkpoint_ref"] != checkpoint_ref:
            raise Refusal(
                f"request {name_of(reply_to)} retained checkpoint "
                f"{name_of(asked['checkpoint_ref'])} and this reply names "
                f"{name_of(checkpoint_ref)}; an answer preserves the exact "
                f"retained checkpoint")
        work = core._work(asked["work_id"])
        decision = core._require_capability(
            actor, ANSWER_CAPABILITY, f"a native {disposition}",
            scope=work["scope"])
        if actor != asked["destination"]:
            raise Refusal(
                f"request {name_of(reply_to)} was addressed to "
                f"{name_of(asked['destination'])} and {name_of(actor)} is "
                f"answering it; a capability is not an invitation to answer "
                f"somebody else's correspondence")
        if reply_of(core, reply_to) is not None:
            raise Refusal(
                f"request {name_of(reply_to)} is already answered; one "
                f"request earns one reply, and a second answer to one "
                f"question is two answers")
        _free_message_id(core, message_id, disposition)
        destination = actor
        if disposition == ESCALATION_KIND:
            routing = core.native_routing()
            if routing is None:
                raise Refusal(
                    "this deployment configures no native handoff routing; an "
                    "escalation is addressed to a configured decision "
                    "recipient and this authority holds none")
            destination = routing["decision_recipient"]
            if destination == actor:
                raise Refusal(
                    f"{name_of(actor)} is the configured decision recipient "
                    f"as well as the answering reviewer; an escalation goes to "
                    f"a higher authority and never recursively to itself")
        core._store.run(
            "INSERT INTO work_message (message_id, work_id, job_id, author, "
            "generation, claim_seq, kind, body, handoff_digest, reply_to, "
            "checkpoint_ref, continuation_digest, task_digest, destination, "
            "operation_id, recorded_at) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            message_id, work["work_id"], asked["job_id"], actor,
            asked["generation"], asked["claim_seq"], disposition, encoded,
            handoff_digest, reply_to, checkpoint_ref,
            asked["continuation_digest"], asked["task_digest"], destination,
            operation_id, core._now())
        core._store.run(
            "INSERT INTO work_message_transition (message_id, work_id, "
            "effect, detail, operation_id, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            message_id, work["work_id"], effect, detail_text, operation_id,
            core._now())
        core._record_decision(disposition, message_id, decision)
        return {"message": message_of(core, message_id),
                "request": asked,
                "transition": transition_of(core, message_id)}

    return core._replay(
        operation_id,
        signature_of("work-message.respond",
                     {"message_id": message_id, "reply_to": reply_to,
                      "actor": actor, "disposition": disposition,
                      "body": taken, "handoff_digest": handoff_digest,
                      "request_digest": request_digest,
                      "checkpoint_ref": checkpoint_ref, "effect": effect,
                      "detail": held}), body_)
