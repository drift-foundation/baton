"""W386365: an ordinary creation asked of an instance whose manager is serving.

A creation's effects belong to the one process that holds the manager-instance
guard. While a manager serves, that process is the manager, so the command
records what the operator asked and the manager performs it. Nothing here
derives, authorizes, binds or submits: `creation.create_template_job` still
does all of that, once, inside the guard.

One row per Job identity. An identical request finds its row; a different
request under the same identity is refused before any Job exists; a refused
request asked again is queued again, because a refusal before the reservation
leaves nothing behind and the direct command may likewise be repeated.
"""
import json

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import creation
from .schema import CREATION_REQUEST_STATES
from .store import job_signature

__all__ = ["ANSWER_KIND", "REQUEST_KIND", "REQUEST_SCHEMA", "attempt_status", "has_pending", "pending", "record", "request_id", "settle", "status"]

REQUEST_KIND = "template_job.request"
ANSWER_KIND = "template_job.request-answer"
REQUEST_SCHEMA = "baton.v12.template-job.creation-request/1"
# Where the serving manager finds the instance the operator named. They are
# the command's own operands, held to the instance again by the manager.
PLACE_MEMBERS = ("instance", "authority", "route")


def _refuse(message):
    raise ContractRefusal("refused", "precondition", message)


def request_id(job_id, request_digest):
    """One request's stable name: the Job identity and the caller's intent."""
    return "creation-request-" + digest([boundaries.identity(job_id, "a Job id"), request_digest])[7:39]


def _snapshot(row):
    return {"schema": REQUEST_SCHEMA, "request_id": row["request_id"], "job_id": row["job_id"],
            "request_digest": row["request_digest"], "state": row["state"], "attempts": row["attempts"],
            "recorded_at": row["recorded_at"], "answered_at": row["answered_at"],
            "answer": None if row["answer"] is None else json.loads(row["answer"])}


def _row(connection, job_id):
    return connection.execute("SELECT * FROM creation_requests WHERE job_id=?", (job_id,)).fetchone()


def _place(place):
    taken = boundaries.document(place, "a creation request's instance operands", required=("instance", "authority"), optional=("route",))
    held = {"instance": boundaries.text(taken["instance"], "the instance root"),
            "authority": boundaries.text(taken["authority"], "the Authority store"), "route": taken.get("route")}
    if held["route"] is not None:
        boundaries.text(held["route"], "the first Work's route")
    return held


def record(store, request, place):
    """Record what was asked, or find it. Answers the request's snapshot.

    W386365 review R1: THE ROW RESERVES THE JOB IDENTITY while its request is
    pending or created, on both paths, so a different intent is refused here
    before anything is created. A REFUSED request reserves nothing -- its
    creation was refused, and a refusal before the reservation leaves the
    identity free, which is what an operator is told to rely on -- so the same
    request asked again is queued again, and a different one replaces it. If
    the refused creation had already reserved the Job, the creation's own
    reservation still refuses a different intent, in its own words.

    `attempts` counts every recording under this Job identity, replacements
    included, so a request asked again after another one replaced it never
    reuses an earlier act's identity.
    """
    intent = creation.intent_of(request)
    place = _place(place)
    named = request_id(intent["job_id"], intent["request_digest"])
    held = status(store, intent["job_id"])
    replacing = held is not None and held["request_digest"] != intent["request_digest"]
    if replacing and held["state"] != "refused":
        _refuse(f"Job {name_value(intent['job_id'])} already has a recorded creation request for a DIFFERENT intent "
                f"({name_value(held['request_digest'])}; this one is {name_value(intent['request_digest'])}). Nothing was "
                f"recorded. Create the changed intent under another Job identity")
    if held is not None and not replacing and held["state"] != "refused":
        return attempt_status(store, intent["job_id"], named, held["attempts"], place=place)
    attempt = 1 if held is None else held["attempts"] + 1
    document = canonical_text({"request": intent["request"], "place": place})

    def perform(connection):
        now = store._now()
        row = _row(connection, intent["job_id"])
        # A COMPLETED CREATION MADE WITHOUT A REQUEST -- every one before
        # requests existed -- holds its identity too. Read inside this
        # transaction, so it cannot complete between the caller's replay and
        # this row. A reservation that never completed is left to the
        # creation's own comparison, which refuses in its own words.
        made = connection.execute("SELECT request_digest FROM template_jobs WHERE job_id=? AND state='created'",
                                  (intent["job_id"],)).fetchone()
        if made is not None and made["request_digest"] != intent["request_digest"]:
            _refuse(f"Job {name_value(intent['job_id'])} is already the creation of a DIFFERENT request "
                    f"({name_value(made['request_digest'])}); nothing was recorded. Create the changed intent under "
                    f"another Job identity")
        if attempt == 1 and row is None:
            connection.execute("INSERT INTO creation_requests (request_id, job_id, request_digest, document, state, attempts, recorded_at) "
                               "VALUES (?,?,?,?,'pending',1,?)", (named, intent["job_id"], intent["request_digest"], document, now))
        elif row is not None and row["state"] == "refused" and row["attempts"] == attempt - 1:
            if row["request_id"] != named:
                connection.execute("DELETE FROM creation_requests WHERE request_id=? AND state='refused'", (row["request_id"],))
                connection.execute("INSERT INTO creation_requests (request_id, job_id, request_digest, document, state, attempts, recorded_at) "
                                   "VALUES (?,?,?,?,'pending',?,?)", (named, intent["job_id"], intent["request_digest"], document,
                                                                      attempt, now))
            else:
                connection.execute("UPDATE creation_requests SET state='pending', attempts=?, document=?, recorded_at=?, answered_at=NULL, "
                                   "answer=NULL WHERE request_id=?", (attempt, document, now, named))
        else:
            _refuse(f"the creation request for Job {name_value(intent['job_id'])} changed while it was being recorded; "
                    f"run the same command again")
        return {"request_id": named, "attempt": attempt, "recorded_at": now}

    store.transact(f"{REQUEST_KIND}:{named}:{attempt}", REQUEST_KIND,
                   job_signature(REQUEST_KIND, {"request_id": named, "attempt": attempt}), perform)
    return attempt_status(store, intent["job_id"], named, attempt, place=place)


def attempt_status(store, job_id, named, attempt, *, place=None):
    """Read this submission attempt even if a retry has replaced its row."""
    row = _row(store._connection, job_id)
    if row is not None and (row["request_id"], row["attempts"]) == (named, attempt):
        if place is not None and row["state"] == "pending" and json.loads(row["document"])["place"] != place:
            _refuse(f"creation request {name_value(named)} is pending with different instance operands or Work route; "
                    "repeat the recorded command")
        return _snapshot(row)

    # Only a refusal frees a row for replacement. Keep answering the caller
    # that submitted it from that attempt's immutable settlement receipt.
    signature = job_signature(ANSWER_KIND, {"request_id": named, "attempt": attempt, "state": "refused"})
    found, receipt = store.replay(f"{ANSWER_KIND}:{named}:{attempt}:refused", signature, kind=ANSWER_KIND)
    if found and receipt.get("answer"):
        answer = receipt["answer"]
        raise ContractRefusal(answer["category"], answer["code"], answer["message"])
    _refuse(f"creation request {name_value(named)} attempt {attempt} is no longer current")



def status(store, job_id):
    """The one request recorded for this Job identity, or `None`. A reader."""
    boundaries.identity(job_id, "a Job id")
    row = _row(store._connection, job_id)
    return None if row is None else _snapshot(row)


def pending(store):
    """Every request the serving manager has not answered, oldest first."""
    return [dict(_snapshot(row), **json.loads(row["document"])) for row in store._connection.execute(
        "SELECT * FROM creation_requests WHERE state='pending' ORDER BY recorded_at, request_id")]


def has_pending(store):
    return store._connection.execute("SELECT 1 FROM creation_requests WHERE state='pending' LIMIT 1").fetchone() is not None


def settle(store, held, state, answer):
    """The answer to one attempt of one request, once per state.

    `created` may replace a `refused` answer to the SAME attempt: two
    performers of one request can race, the loser be refused as concurrent,
    and the winner then finish. A Job that exists is the outcome. Nothing
    replaces `created`.
    """
    if state not in CREATION_REQUEST_STATES or state == "pending" or type(answer) is not dict or not answer:
        _refuse("a creation request is answered created or refused, with the answer")
    named, attempt = held["request_id"], held["attempts"]
    encoded = canonical_text(answer)

    def perform(connection):
        now = store._now()
        replaceable = "('pending','refused')" if state == "created" else "('pending')"
        changed = connection.execute("UPDATE creation_requests SET state=?, answered_at=?, answer=? WHERE request_id=? AND attempts=? "
                                     f"AND state IN {replaceable}", (state, now, encoded, named, attempt)).rowcount
        if changed != 1:
            _refuse(f"creation request {name_value(named)} attempt {attempt} is not pending; it was answered once already")
        receipt = {"request_id": named, "attempt": attempt, "state": state, "answered_at": now}
        if state == "refused":
            receipt["answer"] = answer
        return receipt

    return store.transact(f"{ANSWER_KIND}:{named}:{attempt}:{state}", ANSWER_KIND,
                          job_signature(ANSWER_KIND, {"request_id": named, "attempt": attempt, "state": state}), perform)
