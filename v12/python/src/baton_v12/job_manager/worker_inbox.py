"""Job-scoped publication order, independent of main's display order.

Publication and its stable identity mapping share the Job journal transaction.
Only the closed projection below crosses into the worker's read-only exchange.
No worker holds either of the stores used by this library.
"""
import json

from ..contracts import ContractRefusal, digest
from . import main_thread
from .store import job_signature

PUBLICATION = "worker-inbox.publication"
MAX_SEQUENCE = 2**63 - 1
MAX_ENTRIES = 128
MAX_BYTES = 65536
DELIVERY = "worker-inbox.delivery"
FETCHED = "worker-inbox.fetched"
REFUSED = "worker-inbox.refused"
MAX_REASON = 512


def _refuse(message):
    raise ContractRefusal("refused", "precondition", message)


def sequence(value):
    if type(value) is not int or not 0 <= value <= MAX_SEQUENCE:
        _refuse("an inbox sequence is an integer from zero through 2**63 - 1")
    return value


def _entry(entry):
    # Authority envelopes, owner authentication and custody locators stay host
    # side. The conversational text is the same text main displays.
    body = entry["body"]
    if type(body) is dict:
        body = body["body"]
    kind = entry["kind"]
    if kind in (main_thread.RULING, main_thread.DECISION) and "supersedes" in entry:
        kind = main_thread.RULING
        body = {"text": body, "supersedes": entry["supersedes"]}
    return {"message_id": entry["message_id"], "author": entry["author"],
            "kind": kind, "body": body, "phase": None if entry.get("phase") is None else entry["phase"].rsplit("/", 1)[-1]}


def check_ruling_size(record):
    """Even a single heavily escaped ruling must fit the bounded exchange page."""
    entry = dict(_entry(record), sequence=MAX_SEQUENCE, status="superseded")
    page = {"entries": [entry], "last_sequence": MAX_SEQUENCE}
    envelope = {"attempt_id": "attempt-" + "f" * 64, "entry": entry}
    if max(len(json.dumps(document)) for document in (page, envelope)) > MAX_BYTES:
        _refuse("standing ruling exceeds the inbox byte bound")


def read(store, authority, job_id, *, after=0, limit=MAX_ENTRIES):
    """Publish newly visible main entries and fetch one bounded inbox page.

    The manager/library is the publisher, even with every service stopped.
    The transaction sequence orders first inbox publication, not timestamps
    or the display position in main. Concurrent and retried publications of
    the same identity replay the original record.
    """
    sequence(after)
    if type(limit) is not int or not 1 <= limit <= MAX_ENTRIES:
        _refuse("an inbox page holds between 1 and 128 entries")
    main = main_thread.read(store, authority, job_id)
    for entry in main["entries"]:
        operands = {"job_id": job_id, "entry": _entry(entry)}
        operation = PUBLICATION + ":" + digest({"job_id": job_id, "message_id": entry["message_id"]})[7:]

        def publish(connection, operands=operands):
            number = connection.execute("SELECT coalesce(max(rowid), 0) + 1 FROM operations").fetchone()[0]
            sequence(number)
            return dict(operands, sequence=number)

        identity = {"job_id": job_id, "message_id": entry["message_id"]}
        store.transact(operation, PUBLICATION, job_signature(PUBLICATION, identity), publish)
    records = main_thread._records(store, PUBLICATION, job_id)
    records.sort(key=lambda entry: entry["sequence"])
    latest = records[-1]["sequence"] if records else 0
    if after > latest:
        _refuse("the inbox cursor is beyond this Job's published sequence")
    result = {"entries": [], "last_sequence": after}
    for record in records:
        if record["sequence"] <= after:
            continue
        entry = dict(record["entry"], sequence=record["sequence"])
        proposed = {"entries": result["entries"] + [entry], "last_sequence": entry["sequence"]}
        if len(json.dumps(proposed).encode("utf-8")) > MAX_BYTES:
            break
        result = proposed
        if len(result["entries"]) == limit:
            break
    return result


def fetched_of(store, job_id, attempt_id):
    records = main_thread._records(store, FETCHED, job_id)
    numbers = [one["last_sequence"] for one in records if one["attempt_id"] == attempt_id]
    return max(numbers) if numbers else None


def published(store, job_id, attempt_id, page):
    operands = {"job_id": job_id, "attempt_id": attempt_id,
                "sequences": [entry["sequence"] for entry in page["entries"]],
                "last_sequence": page["last_sequence"]}
    operation = DELIVERY + ":" + digest(operands)[7:]
    return store.transact(operation, DELIVERY, job_signature(DELIVERY, operands), lambda _: operands)


def record_fetched(store, job_id, attempt_id, evidence):
    """Validate untrusted evidence against this attempt's publication history."""
    if type(evidence) is not dict or set(evidence) != {"attempt_id", "last_sequence"}:
        _refuse("inbox evidence has exactly attempt_id and last_sequence")
    if evidence["attempt_id"] != attempt_id:
        _refuse("inbox evidence names a foreign attempt")
    last = sequence(evidence["last_sequence"])
    deliveries = [one for one in main_thread._records(store, DELIVERY, job_id) if one["attempt_id"] == attempt_id]
    if not any(last in [0, *one["sequences"]] for one in deliveries):
        _refuse("inbox evidence names a sequence not published to this attempt")
    previous = fetched_of(store, job_id, attempt_id)
    if previous is not None and last <= previous:
        return {"job_id": job_id, "attempt_id": attempt_id, "last_sequence": previous}
    operands = dict(evidence, job_id=job_id)
    operation = FETCHED + ":" + digest(operands)[7:]
    return store.transact(operation, FETCHED, job_signature(FETCHED, operands), lambda _: operands)


def phase_start(store, authority, job_id, attempt_id):
    """Freeze the first page once; retries cannot change delivered bytes."""
    if authority.authority_uuid != store.authority_uuid:
        _refuse("inbox stores belong to different Authorities")
    main_thread._job(store, job_id)
    operation = "worker-inbox.start:" + attempt_id
    old = store.operation_record(operation)
    if old is not None and old["state"] == "committed":
        record = json.loads(old["result"])
        if record["job_id"] != job_id:
            _refuse("phase-start inbox belongs to another Job")
        page = record["page"]
        published(store, job_id, attempt_id, page)
        return page
    page = read(store, authority, job_id)
    operands = {"job_id": job_id, "attempt_id": attempt_id, "page": page}
    held = store.transact(operation, "worker-inbox.start",
                          job_signature("worker-inbox.start", {"job_id": job_id, "attempt_id": attempt_id}), lambda _: operands)
    published(store, job_id, attempt_id, held["page"])
    return held["page"]


def exchange_tick(store, authority, job_id, delivery):
    """Replay immutable publications before ingesting untrusted evidence."""
    from ..worker_manager import exchange
    initial = phase_start(store, authority, job_id, delivery.attempt_id)
    after = 0
    while True:
        page = read(store, authority, job_id, after=after)
        # Journal first: a crash before file publication is safely replayed.
        published(store, job_id, delivery.attempt_id, page)
        exchange.publish_inbox(delivery, page, initial=initial)
        if not page["entries"]:
            break
        after = page["last_sequence"]
    # W386413 R1: the acknowledgement is the least trusted input here, so its
    # refusal belongs to this attempt alone. Validation stays strict and the
    # cursor stays where it was; the refusal is journalled against the attempt
    # and the caller's sweep continues for every other attempt and Job.
    try:
        evidence = exchange.observed_inbox(delivery)
        if evidence is not None:
            record_fetched(store, job_id, delivery.attempt_id, evidence)
    except ContractRefusal as refusal:
        _refused(store, job_id, delivery.attempt_id, refusal)


def _refused(store, job_id, attempt_id, refusal):
    reason = str(refusal)[:MAX_REASON]
    operands = {"job_id": job_id, "attempt_id": attempt_id, "reason": reason}
    operation = REFUSED + ":" + digest(operands)[7:]
    return store.transact(operation, REFUSED, job_signature(REFUSED, operands), lambda _: operands)


def refused_of(store, job_id, attempt_id):
    """The most recently first-journalled acknowledgement refusal, or None."""
    reasons = [one["reason"] for one in main_thread._records(store, REFUSED, job_id) if one["attempt_id"] == attempt_id]
    return reasons[-1] if reasons else None
