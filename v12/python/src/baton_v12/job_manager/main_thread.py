"""The implicit main conversation and targeted local-owner decisions.

Authority owns requests and reviewer replies. The Job journal owns notes and
owner decisions; none is a second reply or an execution act. Manager admission
consumes a decision through native_handoffs' existing continuation transaction.
"""
import json

from ..contracts import ContractRefusal, digest
from ..worker_manager import boundaries
from .store import job_signature

RULING = "main.ruling"
NOTE = "main.note"
DECISION = "main.owner-answer"


def _refuse(text):
    raise ContractRefusal("refused", "precondition", text)


def identity(job_id, thread=None):
    boundaries.identity(job_id, "Job")
    if thread not in (None, "main"):
        _refuse("only the default main conversation is supported")
    return "main-" + digest({"job_id": job_id})[7:]


def _job(store, job_id):
    rows = store._connection.execute("SELECT * FROM stages WHERE job_id = ? ORDER BY stage_id", (job_id,)).fetchall()
    if not rows and store._connection.execute("SELECT 1 FROM jobs WHERE job_id = ? UNION ALL SELECT 1 FROM manual_jobs WHERE job_id = ?", (job_id, job_id)).fetchone() is None:
        _refuse("no such Job: " + job_id)
    return rows


def _records(store, kind, job_id):
    rows = store._connection.execute("SELECT result FROM operations WHERE kind = ? AND state = 'committed' ORDER BY rowid", (kind,)).fetchall()
    return [record for row in rows if row["result"] is not None
            for record in [json.loads(row["result"])] if record.get("job_id") == job_id]


def decision_of(store, job_id, request_id):
    return next((one for one in _records(store, DECISION, job_id) if one["request_id"] == request_id), None)


def _messages(store, authority, job_id):
    if authority.authority_uuid != store.authority_uuid:
        _refuse("conversation stores belong to different Authorities")
    works = dict.fromkeys(row["work_id"] for row in _job(store, job_id))
    return sorted((one for work in works for one in authority.work_messages(work) if one["job_id"] == job_id),
                  key=lambda one: one["sequence"])


def _yields(store, job_id):
    from . import native_handoffs
    return _records(store, native_handoffs.YIELD_KIND, job_id)


def read(store, authority, job_id, *, thread=None):
    """One read API for clients, including stores predating thread metadata."""
    thread_id = identity(job_id, thread)
    messages = _messages(store, authority, job_id)
    yields = {one["message_id"]: one for one in _yields(store, job_id)}
    entries = []
    questions = []
    for index, message in enumerate(messages):
        request_id = message.get("reply_to") or message["message_id"]
        yielded = yields.get(request_id)
        phase = None if yielded is None else yielded["stage_id"]
        origin = phase
        if message.get("reply_to"):
            origin = next((row["stage_id"] for row in _job(store, job_id) if row["kind"] == "review"), None)
        entries.append(((index, 0, 0), dict(message, phase=origin, thread_id=thread_id)))
        if message["kind"] in ("finding-request", "clarification-request"):
            reply = authority.work_message_reply(message["message_id"])
            decision = decision_of(store, job_id, message["message_id"])
            if reply is None or reply["kind"] == "escalation":
                from . import native_handoffs
                delivered = None if yielded is None else native_handoffs.continuation_of(store, phase, yielded["episode"])
                questions.append({"request_id": message["message_id"], "job_id": job_id,
                                  "phase": phase, "question": message["body"].get("body", ""),
                                  "checkpoint_ref": message["checkpoint_ref"],
                                  "checkpoint_id": None if yielded is None else yielded["checkpoint_id"],
                                  "state": "delivered" if delivered else "answer-recorded" if decision else "open",
                                  "decision": decision})
    for kind in (NOTE, DECISION, RULING):
        for record in _records(store, kind, job_id):
            entries.append(((record["after_messages"] - 1, 1, record["sequence"]), record))
    ordered = [entry for _, entry in sorted(entries, key=lambda pair: pair[0])]
    rulings = [entry for entry in ordered if entry["kind"] in (DECISION, RULING) and "supersedes" in entry]
    replaced = {target for ruling in rulings for target in ruling["supersedes"]}
    return {"rulings": [dict(ruling, status="superseded" if ruling["message_id"] in replaced else "active") for ruling in rulings],
            "job_id": job_id, "name": "main", "thread_id": thread_id,
            "entries": ordered,
            "requests": questions, "open_requests": [one for one in questions if one["state"] == "open"]}


def _actor(store, authority, actor):
    actor = boundaries.document(actor, "authenticated local owner", required=("authority_uuid", "participant", "principal", "uid"))
    if actor["authority_uuid"] != store.authority_uuid or authority.authority_uuid != store.authority_uuid:
        _refuse("owner and Job must belong to the same Authority")
    if type(actor["uid"]) is not int or actor["uid"] < 0 or authority.principal_of(actor["participant"]) != actor["principal"]:
        _refuse("invalid authenticated local owner")
    return actor


def _text(text):
    if type(text) is not str or not text.strip() or len(text.encode("utf-8")) > 16384:
        _refuse("conversation text must be nonempty and at most 16384 UTF-8 bytes")
    return text


def _write(store, kind, operation, operands, count):
    def act(connection):
        _job(store, operands["job_id"])
        if "supersedes" in operands:
            for target in operands["supersedes"]:
                prior = store.operation_record(target)
                if prior is None or prior["state"] != "committed" or prior["kind"] not in (RULING, DECISION):
                    _refuse("replacement must name an earlier standing ruling of this Job")
                record = json.loads(prior["result"])
                if record["job_id"] != operands["job_id"] or "supersedes" not in record:
                    _refuse("replacement must name an earlier standing ruling of this Job")
            from . import worker_inbox
            worker_inbox.check_ruling_size(dict(operands, kind=kind, message_id=operation))
        sequence = connection.execute("SELECT count(*) FROM operations").fetchone()[0] + 1
        return dict(operands, kind=kind, message_id=operation, recorded_at=store._now(),
                    after_messages=count, sequence=sequence)
    return store.transact(operation, kind, job_signature(kind, operands), act)


def note(store, authority, job_id, body, *, actor, operation_id, thread=None):
    """Append a note. It has no scheduling effect, including on held Jobs."""
    thread_id = identity(job_id, thread)
    actor = _actor(store, authority, actor)
    messages = _messages(store, authority, job_id)
    boundaries.identity(operation_id, "note operation")
    return _write(store, NOTE, NOTE + ":" + operation_id,
                  dict(job_id=job_id, thread_id=thread_id, author=actor["participant"], actor=actor, body=_text(body), phase=None), len(messages))


def _targets(supersedes):
    if type(supersedes) not in (list, tuple) or any(type(target) is not str or not target for target in supersedes):
        _refuse("replacement targets must be stable message IDs")
    if len(set(supersedes)) != len(supersedes):
        _refuse("duplicate ruling replacement target")
    return sorted(supersedes)


def ruling(store, authority, job_id, body, *, actor, operation_id, supersedes=(), thread=None):
    thread_id = identity(job_id, thread)
    actor = _actor(store, authority, actor)
    messages = _messages(store, authority, job_id)
    boundaries.identity(operation_id, "ruling operation")
    operation = RULING + ":" + digest({"job_id": job_id, "operation": operation_id})[7:]
    return _write(store, RULING, operation, dict(job_id=job_id, thread_id=thread_id,
                  author=actor["participant"], actor=actor, body=_text(body), phase=None,
                  supersedes=_targets(supersedes)), len(messages))


def answer(store, authority, job_id, request_id, body, *, phase, checkpoint_id, actor, thread=None, standing=False, supersedes=()):
    """Record one exact decision; an identical retry replays, a conflict refuses.

    The trusted installation boundary authenticates actor, as for MANUAL finish.
    Immutable Authority evidence is read before the Job write transaction.
    """
    from . import native_handoffs
    thread_id = identity(job_id, thread)
    actor = _actor(store, authority, actor)
    messages = _messages(store, authority, job_id)
    request = next((one for one in messages if one["message_id"] == request_id), None)
    if request is None or request["kind"] not in ("finding-request", "clarification-request"):
        _refuse("the identified request does not belong to this Job")
    reply = authority.work_message_reply(request_id)
    if reply is None or reply["kind"] != "escalation" or reply["destination"] != actor["participant"]:
        _refuse("the request must be escalated to this authenticated owner")
    yielded = next((one for one in _yields(store, job_id) if one["message_id"] == request_id), None)
    if yielded is None or yielded["stage_id"] != phase or yielded["checkpoint_id"] != checkpoint_id:
        _refuse("owner answer must name the requesting phase and held checkpoint")
    hold = native_handoffs.hold_of(store, phase, yielded["episode"])
    if hold is None or hold["request_id"] != request_id or hold["message_id"] != reply["message_id"] or hold["checkpoint_id"] != checkpoint_id:
        _refuse("the request has no matching durable escalation hold")
    operation = DECISION + ":" + digest({"job_id": job_id, "request_id": request_id})[7:]
    if type(standing) is not bool or (not standing and supersedes):
        _refuse("only an explicitly standing answer can replace rulings")
    designation = {"supersedes": _targets(supersedes)} if standing else {}
    return _write(store, DECISION, operation,
                  dict(job_id=job_id, thread_id=thread_id, request_id=request_id, phase=phase,
                       checkpoint_id=checkpoint_id, checkpoint_ref=request["checkpoint_ref"],
                       escalation_id=reply["message_id"], author=actor["participant"], actor=actor,
                       body=_text(body), **designation), len(messages))


def outstanding(store, job_id):
    """Status reads the question retained by the manager with its hold."""
    from . import native_handoffs
    found = []
    for hold in _records(store, native_handoffs.HOLD_KIND, job_id):
        if native_handoffs.continuation_of(store, hold["stage_id"], hold["episode"]) is not None:
            continue
        decision = decision_of(store, job_id, hold["request_id"])
        found.append(dict(request_id=hold["request_id"], phase=hold["stage_id"],
                          question=hold.get("question", "Owner decision requested"),
                          state="answer-recorded" if decision else "open"))
    return found


def reconcile(store, custody, authority):
    """Every manager tick revisits recorded decisions; admission remains fenced."""
    from . import episodes, native_handoffs
    jobs = store._connection.execute("SELECT job_id FROM jobs ORDER BY job_id").fetchall()
    for job in jobs:
        job_id = job["job_id"]
        for decision in _records(store, DECISION, job_id):
            live = episodes.live_of(store, decision["phase"])
            if live is None:
                continue
            yielded = native_handoffs.yield_of(store, decision["phase"], live["episode"])
            if yielded is None or yielded["message_id"] != decision["request_id"]:
                continue
            try:
                native_handoffs.advance_continuation(store, custody, authority, job_id=job_id)
            except ContractRefusal:
                # Cancellation, expiry, budget and allocation fences keep the
                # answer durable and pending; one held Job cannot stop others.
                continue
