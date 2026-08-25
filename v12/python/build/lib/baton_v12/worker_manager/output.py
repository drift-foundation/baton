"""THE OUTPUT FREEZE and the sealed artifact receiver.

W6628. `work/records/2026/08/finding-v12-manager-output-receiver/`. Ported from
the frozen Node `output.mjs` by obligation.

The pinned acceptance, in one sentence: freeze requires the exact live
assignment, a terminal disposition compatible with the declared one, and a
POSITIVE writer-quiescence observation; the same digest replays and changed
bytes under the same identity refuse. Filesystem and OCI collection are
somebody else's; this owns the immutable store transition and the validation of
the adapter's sealed observation.

THE FOUR PRECONDITIONS, and where each is actually decided:

  1. the attempt carries a fixed four-part assignment            -- the row
  2. the session is bound to that participant                    -- the port
  3. `worker_disposition` is already TERMINAL and equals the one
     being declared                                              -- the row
  4. `execution_runtime` is positively `quiescent`               -- the row

and then the assignment must still be LIVE at the authority, which is a READ of
somebody else's store and can only ever be a read. That is stated rather than
hidden below.

PRECONDITIONS 3 AND 4 ARE DECIDED TWICE, AND ONLY THE SECOND ONE COUNTS. They
are read from AXES, which move -- so a check made before `transact` takes the
write lock is an optimistic early refusal and nothing more. The decisive one
re-reads the attempt inside the journal transaction, because a newer
`uncertain` observation landing in that window must win over the stale
`quiescent` row the call started from. Precondition 1 is fixed-once and 2 is a
property of the session, so neither can move underneath the act.

NOT ONE OF THEM IS A CLAIM THE CALLER SUPPLIED ABOUT ITSELF. Adapter and engine
status carry no authority meaning at any point here: what an adapter returns is
recorded and validated, and what it asserts about its own success decides
nothing.

TWO THINGS THE FROZEN CONTRACT ALREADY DECIDES, which this module consumes
rather than re-decides:

  MISSING-OPTIONAL IS A STATUS, NOT AN ABSENCE. `artifactOutput.status` is
  closed to `present, missing-optional` with both the content manifest and the
  artifact explicitly nullable. An output the assignment declared as not
  required and which did not appear is REPORTED. A receiver that treated it as
  nothing to record would lose the fact that the worker was asked and answered
  -- which is exactly what a later settlement needs.

  FREEZING IS NOT ACCEPTING. The output axis is
  `open, freeze-requested, frozen, invalid, sealed, discarded`, and `invalid`
  is reachable from `frozen` as well as from `open` and `freeze-requested`.
  Material can be frozen and then found invalid, so this module ends at
  `frozen` and never writes `sealed`.

WHAT IS NOT HERE: filesystem and OCI collection, credentials, retention and
cleanup, and the `sealed` transition itself. In particular the agent TURN
records that gate the disposition are a later item's, which is why this
compares against the RECORDED `worker_disposition` axis rather than accepting a
turn outcome from its caller. A proof the caller can write is not a proof.
"""

from ..contracts import (ContractRefusal, canonical_bytes,
                         check_manifest_structure, digest,
                         verify_manifest_digest)
from ..contracts.errors import name_value
from . import boundaries, documents, manifests, schema
from .attempts import TRANSITIONS, observe
from .store import manager_signature

__all__ = ["freeze_operation", "request_freeze", "record_frozen_result",
           "frozen_output_of"]


def _attempt_of(connection, attempt_id):
    """THE ONE CROSSING out of the attempts table for this module.

    NAMED `_attempt_of` RATHER THAN `_attempt`, and the reason is worth
    writing down: `sessions.py` already has a private `_attempt`, and the
    boundary inventory resolves what a private helper HANDS BACK by the
    helper's NAME rather than by its lexical site -- so two modules sharing
    one private name make one of them invisible to it. That is the same
    name-collapsing defect the inventory's own header describes for functions,
    surviving one level down in its origin resolution. Recorded as an
    operational finding in this Work's dossier; avoided here rather than
    worked around silently.
    """
    found = connection.execute(
        "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if found is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no runtime attempt {name_value(attempt_id)}")
    return boundaries.row(found, "a persisted attempt",
                          schema.ATTEMPT_COLUMNS)


def _fixed_assignment(attempt):
    if attempt["assignment_generation"] is None:
        return None
    return documents.assignment(
        work_ref=documents.work_ref(
            authority_uuid=attempt["authority_uuid"],
            work_id=attempt["work_id"]),
        participant=attempt["assignment_participant"],
        generation=attempt["assignment_generation"])


def freeze_operation(attempt):
    """THE WHOLE freeze operation identity: the id AND its signature.

    Derived, like every other act in this manager, so a restart names what it
    already did rather than sealing a second time.

    THE ID IS THE RETRY KEY; THE SIGNATURE IS THE BINDING over the kind and
    every effective operand. The frozen host's review [P1]: only the id reached
    the adapter and only the id was compared when the result came back, so any
    schema-shaped digest was accepted in `freeze_operation.signature_digest`.
    Comparing the key alone compares the weaker half.

    The disposition is read from the ATTEMPT rather than taken as an operand,
    because by the time this is derived the freeze has already proved the
    declared one equals the recorded axis.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    assignment = _fixed_assignment(taken)
    operation_id = "output.freeze:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": assignment,
    })[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "output.freeze",
            "operands": {"attempt_id": taken["runtime_attempt_id"],
                         "expect": assignment,
                         "disposition": taken["worker_disposition"],
                         "operation_id": operation_id}}))


def _record_operation_id(attempt):
    """The record operation is FIXED PER ATTEMPT, not per digest.

    This is the whole mechanism behind "the same digest replays; changed bytes
    under the same identity refuse". If the identity varied with the bytes, two
    different results would be two different operations and BOTH would commit
    -- which is the opposite of what an immutable record means. The identity is
    the ACT; the signature carries the bytes.
    """
    return "output.record:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
    })[len("sha256:"):]


def request_freeze(store, port, adapter, *, attempt_id, disposition):
    """Step 1: prove the preconditions, request the freeze, then hand the
    adapter the exact act it is settling.

    Every precondition is read from DURABLE state. The liveness read is inside
    the write and is still only a read: the authority is a different store, so
    nothing this manager does can make "still live" and "recorded frozen" one
    atomic fact. The window is made as small as it can be, and the design does
    not depend on it being zero -- material from an assignment that ended
    anyway is quarantined at intake rather than trusted here.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    _disposition(disposition)
    boundaries.capability(getattr(adapter, "seal", None),
                          "the runtime adapter's seal")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _fixed_assignment(attempt)
    if expect is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no fixed assignment; a "
            f"result belongs to an exact generation and there is none")
    if port.participant != expect["participant"]:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for {name_value(port.participant)} and attempt "
            f"{name_value(attempt_id)} is assigned to "
            f"{name_value(expect['participant'])}")
    # OPTIMISTIC, and it says so. The same rules are decided again inside the
    # journal transaction, from a row re-read under the write lock; this
    # answers the ordinary case without taking one and refuses early enough
    # that a caller with a plainly unready attempt never reaches the journal.
    _provable(attempt, attempt_id, disposition)
    operation = freeze_operation(attempt)
    signature = manager_signature(
        "output.freeze", {"attempt_id": attempt_id, "expect": expect,
                          "disposition": disposition,
                          "operation": dict(operation)})
    store.transact(
        operation["operation_id"], "output.freeze", signature,
        lambda connection: _request(store, port, connection, attempt_id,
                                    expect, operation, disposition))
    # THE WHOLE IDENTITY crosses the boundary. An adapter handed only the retry
    # key cannot echo the binding, and a manager that asks for an echo it never
    # supplied is asking the adapter to guess.
    sealed = adapter.seal({"attempt_id": attempt_id, "assignment": expect,
                           "disposition": disposition,
                           "operation": dict(operation)})
    return record_frozen_result(store, attempt_id=attempt_id, sealed=sealed)


def _request(store, port, connection, attempt_id, expect, operation,
             disposition):
    # THE DECISIVE CHECK IS THIS ONE, from a row re-read under the write lock.
    #
    # Review [P1]: the runtime and disposition preconditions were proved from
    # an attempt row adopted BEFORE `transact` took the lock, and nothing
    # re-read them inside. A newer `uncertain` or `destroyed` observation
    # committing in that window left the transaction recording
    # `freeze-requested` from a stale `quiescent` row -- the output axis
    # claiming a freeze was requested after the durable evidence had stopped
    # proving the writer stopped.
    #
    # The check outside remains and is now what it always was: an OPTIMISTIC
    # early refusal that answers the ordinary case without taking a write
    # lock. It does not authorize the write. This does.
    _provable(_attempt_of(connection, attempt_id), attempt_id, disposition)
    live = port.assignment_of(expect["work_ref"]["work_id"],
                              expect["work_ref"]["authority_uuid"])
    if live is None:
        raise ContractRefusal(
            "stale-assignment", "ended",
            f"{name_value(expect['work_ref']['work_id'])} holds no live "
            f"assignment; a result is never published on a dead generation")
    if live != expect:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the live assignment is {name_value(live)} and this attempt is "
            f"fixed to {name_value(expect)}")
    observe(store, attempt_id=attempt_id, axis="output",
            value="freeze-requested")
    return documents.freeze_requested(
        attempt_id=attempt_id, operation=dict(operation),
        disposition=disposition)


def _provable(attempt, attempt_id, disposition):
    """The two preconditions that are read from the RUNTIME axes, in one place.

    Written once because they are decided twice -- optimistically before the
    lock and decisively under it -- and two spellings of one rule is how the
    outer and inner answers come to differ. Which of the two calls a caller's
    refusal came from is not a distinction it needs, so the text is the same
    either way.

    MEASURED: ONLY THE QUIESCENCE HALF CAN CHANGE IN THAT WINDOW. The
    `worker_disposition` axis is terminal-once -- every disposition beyond
    `none` has an empty successor set -- so a disposition proved terminal and
    equal by the outer call is still both by the inner one, and that half of
    this function is inert when it runs under the lock. It is kept anyway,
    because factoring the pair is what stops the quiescence rule from being
    written in two places, and a case pins the transition map this relies on:
    if that axis ever stops being terminal-once, the gate says so rather than
    leaving the inner check inert by an assumption nobody re-checks.

    POSITIVE QUIESCENCE, AND NOTHING WEAKER. A seal describes a tree that has
    stopped changing. `uncertain` is not quiescence -- it is a failure to look
    -- and `destroyed` is not either: a writer that is gone was never observed
    to have finished. The pinned pair for this exact question says what is
    MISSING rather than blaming the caller's request.

    THE DISPOSITION IS COMPARED, NOT ACCEPTED. The turn outcome gates the
    disposition and never chooses it, and turn records are a later item's. What
    this slice can decide is that a terminal disposition was RECORDED before
    the freeze and that the freeze declares that same one.
    """
    if attempt["execution_runtime"] != "quiescent":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution is "
            f"{attempt['execution_runtime']}; a freeze describes a tree the "
            f"writer has stopped changing, and only a positive quiescent "
            f"observation says that")
    if attempt["worker_disposition"] == "none":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no recorded worker "
            f"disposition; the handled turn outcome gates it and none has been "
            f"observed")
    if attempt["worker_disposition"] != disposition:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} recorded disposition "
            f"{attempt['worker_disposition']} and this freeze declares "
            f"{disposition}")


def _disposition(disposition):
    """One of the four terminal answers, and the type is established with the
    membership."""
    boundaries.text(disposition, "a declared worker disposition")
    if disposition not in schema.DISPOSITIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(disposition)} is not a worker disposition; the "
            f"frozen four are {', '.join(schema.DISPOSITIONS)}")
    return disposition


def record_frozen_result(store, *, attempt_id, sealed):
    """Step 2: validate the adapter's sealed observation and record it, ONCE.

    `check_manifest_structure` already carries the portable rules -- schema,
    the manifest digest recomputed over its own canonical bytes, well-formed
    refs, and every content manifest's sorted-unique paths, counts, byte totals
    and tree digest. What it CANNOT know is whether this document belongs to
    THIS attempt, and that is the whole of what is added below.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _fixed_assignment(attempt)
    owned = check_manifest_structure(sealed, "resultManifest",
                                     what="a sealed result")
    # THE IMMUTABLE IDENTITY FIRST, before anything about today. RECOMPUTED
    # rather than copied: the validator above already refused any document
    # whose declared digest does not recompute, so this is not an extra guard
    # and is not counted as one. What it buys is PROVENANCE -- the number
    # stored beside the result is derived from the bytes rather than lifted
    # from a member the document filled in about itself.
    recomputed = verify_manifest_digest(owned, what="a sealed result")
    operation_id = _record_operation_id(attempt)
    signature = manager_signature(
        "output.record", {"attempt_id": attempt_id, "recomputed": recomputed})
    # REPLAY IS A FACT ABOUT AN IDENTITY THAT ALREADY SETTLED, and nothing
    # about today is a precondition for reproducing the answer it produced.
    # The frozen host was corrected for this twice: first the output axis was
    # consulted ahead of the journal, so an exact retry refused once `output`
    # reached `frozen`; then the correction left the DECLARATION lookup ahead
    # of it, so removing an old input row made an exact retry refuse too.
    found, already = store.replay(operation_id, signature,
                                  kind="output.record")
    if found:
        return already
    # Every check below this line applies to a genuinely NEW record.
    bound = owned["assignment_ref"]
    if bound != expect:
        raise ContractRefusal(
            "stale-assignment", "target",
            f"the sealed result names {name_value(bound)} and this attempt is "
            f"fixed to {name_value(expect)}")
    # The pinned digests, COMPARED rather than trusted. A result naming a
    # different input or policy would be a result for a different job wearing
    # this assignment's reference.
    for what, stored, seen in (
            ("input", attempt["input_digest"],
             owned["input_manifest_digest"]),
            ("policy", attempt["policy_digest"], owned["policy_digest"])):
        if stored != seen:
            raise ContractRefusal(
                "integrity", "digest",
                f"the sealed result declares {what} digest {name_value(seen)} "
                f"and this attempt was recorded with {name_value(stored)}")
    if owned["disposition"] != attempt["worker_disposition"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the sealed result declares {owned['disposition']} and this "
            f"attempt recorded {attempt['worker_disposition']}")
    operation = freeze_operation(attempt)
    if owned["freeze_operation"]["operation_id"] != operation["operation_id"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the sealed result settles "
            f"{name_value(owned['freeze_operation']['operation_id'])} and this "
            f"attempt's freeze is {name_value(operation['operation_id'])}")
    # AND THE SIGNATURE, which is the half that BINDS.
    if owned["freeze_operation"]["signature_digest"] \
            != operation["signature_digest"]:
        raise ContractRefusal(
            "integrity", "digest",
            f"the sealed result echoes freeze signature "
            f"{name_value(owned['freeze_operation']['signature_digest'])} and "
            f"this attempt's freeze was journalled under "
            f"{name_value(operation['signature_digest'])}")
    # THE DECLARED OUTPUTS, against the declaration this attempt names. A
    # validator can prove a document is internally well formed; it cannot
    # compare it with a document it never sees.
    declaration = manifests.load_manifest(store, attempt["input_digest"],
                                          "inputManifest")
    if declaration is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} names input manifest "
            f"{name_value(attempt['input_digest'])} and this manager does not "
            f"hold it; declared outputs cannot be compared against a document "
            f"nobody retained")
    _compare_declared(declaration, owned, attempt_id)
    if attempt["output"] != "freeze-requested":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} output is {attempt['output']}; "
            f"a result is recorded against a requested freeze")
    return store.transact(
        operation_id, "output.record", signature,
        lambda connection: _record(store, connection, attempt_id, owned,
                                   recomputed, operation))


def _record(store, connection, attempt_id, owned, recomputed, operation):
    # THE SEALED OBSERVATION IS RETAINED, NOT SUMMARIZED. The frozen host kept
    # a summary row and the artifact references and nothing else -- every
    # content tree, every explicitly missing output, the evidence and the
    # freeze operation disappeared when the call returned, leaving intake,
    # publication and restart with a digest and nothing to replay.
    manifests._retain_canonical(connection, store._now(), recomputed,
                                owned["schema"], owned)
    connection.execute(
        "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
        "manifest_digest, freeze_operation_id, frozen_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (attempt_id, owned["result_id"], owned["disposition"], recomputed,
         operation["operation_id"], store._now()))
    for output in owned["outputs"]:
        # A MISSING-OPTIONAL OUTPUT GETS NO ARTIFACT ROW AND IS NOT LOST. The
        # answer it gave is in the retained result document, which preserves
        # every output whole; this table is the indexed half of that record
        # rather than the record.
        if output["artifact"] is None:
            continue
        artifact = output["artifact"]
        connection.execute(
            "INSERT INTO output_artifacts (runtime_attempt_id, output_name, "
            "artifact_id, media_type, bytes, content_digest, locator) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, output["name"], artifact["artifact_id"],
             artifact["media_type"], artifact["bytes"],
             artifact["content_digest"], artifact["locator"]))
    observe(store, attempt_id=attempt_id, axis="output", value="frozen")
    return documents.result_frozen(
        attempt_id=attempt_id, result_id=owned["result_id"],
        manifest_digest=recomputed, disposition=owned["disposition"],
        outputs=[documents.output_answer(
            name=output["name"], type=output["type"], status=output["status"])
            for output in owned["outputs"]])


def _compare_declared(declaration, result, attempt_id):
    """The result's outputs, against the input manifest's DECLARATIONS.

    The pinned rule: a Job may declare several outputs; an undeclared path is
    never collected merely because the agent wrote there. And: missing or
    invalid required output prevents a successful result, while an inability
    disposition may return evidence without pretending the requested result
    exists.

    SO THE COMPARISON RUNS BOTH WAYS. Every result output must be declared, and
    every declaration must be answered -- a declaration silently dropped from
    the result is not an answer to it, it is a question the result pretends was
    never asked.
    """
    declared = {output["name"]: output for output in declaration["outputs"]}
    answered = {}
    for output in result["outputs"]:
        name = output["name"]
        if name in answered:
            raise ContractRefusal(
                "integrity", "schema",
                f"the sealed result answers output {name_value(name)} twice; "
                f"two answers to one declaration is not an answer")
        answered[name] = output
        expect = declared.get(name)
        if expect is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"the sealed result carries output {name_value(name)}, which "
                f"the input manifest does not declare; an undeclared path is "
                f"never collected merely because the agent wrote there")
        if expect["type"] != output["type"]:
            raise ContractRefusal(
                "integrity", "schema",
                f"output {name_value(name)} is declared {expect['type']} and "
                f"the sealed result reports {output['type']}")
    for name, expect in declared.items():
        seen = answered.get(name)
        if seen is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"the input manifest declares output {name_value(name)} and "
                f"the sealed result does not answer it")
        _check_limits(name, expect, seen)
        # A REQUIRED OUTPUT THAT IS NOT THERE IS NOT A COMPLETION -- and an
        # inability disposition may return evidence without pretending the
        # requested result exists, which is why this is conditioned on the
        # disposition rather than refused outright.
        if expect["required"] and seen["status"] != "present" \
                and result["disposition"] == "completed":
            raise ContractRefusal(
                "integrity", "schema",
                f"attempt {name_value(attempt_id)} declares output "
                f"{name_value(name)} required and the sealed result reports "
                f"{seen['status']} under a completed disposition")


def _check_limits(name, expect, seen):
    """The declared LIMITS, against what the sealed observation already proves.

    Whether the artifact's BYTES are what it claims is a collection-time fact
    this layer cannot reach; the counts, totals and media type are already
    inside the document the validator accepted, and a limit that is decidable
    here and not decided here is a limit nobody enforces.
    """
    if seen["status"] != "present":
        # AN OUTPUT THAT SAYS IT IS MISSING MUST BE MISSING. The schema permits
        # `missing-optional` beside a content manifest or an artifact, and that
        # combination is a document contradicting itself -- refused as the
        # contradiction it is rather than resolved by picking a half to
        # believe.
        if seen["content_manifest"] is not None or seen["artifact"] is not None:
            raise ContractRefusal(
                "integrity", "schema",
                f"output {name_value(name)} reports {seen['status']} and "
                f"carries material; a missing output is missing")
        return
    # AND `present` MUST BE PRESENT -- the other direction of the same rule. A
    # status word is not material. Both representations, because a frozen
    # result binds every declared output's content tree AND its artifact
    # reference; the nullable members exist so a MISSING output can say so, not
    # so a present one can choose which half to supply.
    if seen["content_manifest"] is None or seen["artifact"] is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"output {name_value(name)} reports present and carries "
            f"{'no content manifest' if seen['content_manifest'] is None else 'a content manifest'}"
            f" and "
            f"{'no artifact reference' if seen['artifact'] is None else 'an artifact reference'}"
            f"; a frozen result binds both for every declared output")
    limits = expect["constraints"]
    content = seen["content_manifest"]
    # BOTH SIZES, because the declaration bounds the output and a present
    # output has two representations of it. Measuring only whichever one
    # happened to be there leaves the other unbounded.
    for what, size in (("tree", content["total_bytes"]),
                       ("artifact", seen["artifact"]["bytes"])):
        if size > limits["max_bytes"]:
            raise ContractRefusal(
                "integrity", "limit",
                f"output {name_value(name)} declares at most "
                f"{limits['max_bytes']} bytes and its {what} carries {size}")
    if content["entry_count"] > limits["max_entries"]:
        raise ContractRefusal(
            "integrity", "limit",
            f"output {name_value(name)} declares at most "
            f"{limits['max_entries']} entries and the sealed result carries "
            f"{content['entry_count']}")
    # LITERALLY, including the empty list. An allow-list that permits
    # everything when it names nothing is a fail-open reading of a rule written
    # to close.
    if seen["artifact"]["media_type"] not in limits["allowed_media_types"]:
        raise ContractRefusal(
            "policy", "denied",
            f"output {name_value(name)} carries media type "
            f"{name_value(seen['artifact']['media_type'])}, which its "
            f"declaration does not allow")


def frozen_output_of(store, attempt_id):
    """The frozen result this attempt recorded, or None.

    The indexed half: the summary row and its artifact references. The whole
    sealed observation is the retained manifest at `manifest_digest`, which is
    where a reader goes for the content trees, the explicitly missing outputs
    and the evidence.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    found = store._connection.execute(
        "SELECT * FROM outputs WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if found is None:
        return None
    row = boundaries.row(found, "a persisted frozen output",
                         schema.OUTPUT_COLUMNS)
    artifacts = [boundaries.row(entry, "a persisted output artifact",
                                schema.OUTPUT_ARTIFACT_COLUMNS)
                 for entry in store._connection.execute(
                     "SELECT * FROM output_artifacts WHERE "
                     "runtime_attempt_id = ? ORDER BY output_name",
                     (attempt_id,)).fetchall()]
    return documents.frozen_output(
        attempt_id=row["runtime_attempt_id"], result_id=row["result_id"],
        disposition=row["disposition"], manifest_digest=row["manifest_digest"],
        freeze_operation_id=row["freeze_operation_id"],
        frozen_at=row["frozen_at"],
        artifacts=[documents.output_artifact(
            output_name=entry["output_name"],
            artifact_id=entry["artifact_id"],
            media_type=entry["media_type"], bytes=entry["bytes"],
            content_digest=entry["content_digest"], locator=entry["locator"])
            for entry in artifacts])
