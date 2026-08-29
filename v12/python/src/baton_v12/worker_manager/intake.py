"""INTAKE, RETENTION AND CLEANUP: taking custody, deciding what stays, and
authorizing destruction.

W6629. `work/records/2026/08/finding-v12-manager-intake-retention-cleanup/`.

W6628 ends at `frozen` and says so: "FREEZING IS NOT ACCEPTING ... this module
ends at `frozen` and never writes `sealed`", and lists "retention and cleanup,
and the `sealed` transition itself" among what is not there. This is that
slice. Freezing is the worker's material stopping; INTAKE is this manager
taking custody of it, and `sealed` is the record of that act.

THE ORDER IS THE CONTENT, and the frozen contract already fixes it:

  1. `output.collect` asks for the material the frozen result declared;
  2. the collection is COMPARED against what the freeze recorded -- identity,
     content digest and byte count -- and only then does `output` reach
     `sealed`, under an intake receipt this manager produces;
  3. `output.retain` records a disposition per artifact, under the retention
     policy digest that decided it;
  4. `runtime.destroy` carries `intake_receipt_digest` AND
     `retention_policy_digest`, which is the contract stating in its own body
     that cleanup is authorized by proof that intake happened and by the policy
     that decided what stays.

THE RETENTION POLICY IS CONSUMED BY DIGEST AND NEVER INTERPRETED, and this
resolves the open question this dossier was returned with.

The finding recorded on claiming was that the frozen schema states no shape for
the retention policy document, so "retention policy" named something that was
not a contract anywhere in the tree -- and that consuming it was therefore
impossible and inventing it was forbidden. The premise is right and the
conclusion was wrong. `retention_policy_digest` is one of TEN `*_policy_digest`
members of the assignment manifest -- resource, network, mount, tool,
credential, and the rest -- and the frozen schema states the shape of NOT ONE
of them. That is not an omission about retention; it is how this contract
treats policy documents uniformly. A manager binds a policy by IDENTITY and
acts on the operation that cites it. Interpreting one here would be the
boundary violation, not the fix.

The intake receipt is the other direction and so it is this module's to shape.
The contract names `intake_receipt_digest` and states no shape for what it
digests -- but a receipt is PRODUCED here, and a producer owns the shape of
what it produces. Consumed by digest, produced by construction: the same rule
read from its two ends.

WHAT IS NOT HERE: moving bytes. This manager does not read a filesystem, run
an engine or copy an artifact; the adapter does that and returns what it did,
and every claim in that answer is compared against the freeze rather than
adopted. What an adapter asserts about its own success decides nothing, which
is the same rule the freeze receiver was written under.

THE FROZEN AXIS SAYS ONE THING THIS SLICE CANNOT WORK AROUND. `uncertain` may
never become `destroyed`, on the axis's own stated reasoning -- destruction is
a fact about the world, and inferring it from a failure to look would report a
cleaned-up runtime that is still executing somebody's code. So an attempt whose
`execution_runtime` is `uncertain` cannot have its cleanup settled, even when
the engine answers positive absence, until reconciliation returns the axis to a
positive observation. That is refused with the reason stated, rather than
worked around by writing the terminal value some other way.
"""

from ..contracts import (ContractRefusal, check_no_durable_secret, digest,
                         own)
from ..contracts.errors import name_value
from . import boundaries, documents, lanes, schema
from .attempts import observe
from .output import frozen_output_of
from .store import manager_signature

__all__ = ["collect_operation", "intake_operation", "request_intake",
           "record_intake", "intake_receipt_of", "retain_operation",
           "decide_retention", "retentions_of", "destroy_operation",
           "authorize_cleanup", "failed_start_destroy_operation",
           "authorize_failed_start_cleanup",
           "refused_session_destroy_operation",
           "authorize_refused_session_cleanup"]

# The two dispositions that mean the material STAYS. `retain` is policy keeping
# it; `quarantine` is doubt keeping it. Cleanup ends `retained` for either,
# because `retained` and `complete` are different endings and reporting kept
# material as cleaned up would erase the reason it still exists.
KEEPS_MATERIAL = ("retain", "quarantine")

# The dispositions a WORKER answer of `cancelled` makes recoverable. Material
# from a cancelled attempt is kept for recovery, which is a different reason
# from a policy deciding to keep it -- and the acceptance for this Job requires
# the two to stay distinguishable rather than merged into "still there".
_CANCELLED = "cancelled"


def _disposition(disposition):
    """THE FROZEN THREE, established as text in the same expression.

    Written once because it is one question: `x in mapping` on a value that is
    not text RAISES rather than answering, so the type is proved before the
    membership -- the rule this package has followed since a list escaped a
    closed set as a raw `TypeError`.
    """
    boundaries.text(disposition, "a retention disposition")
    if disposition not in schema.RETENTION_DISPOSITIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(disposition)} is not a retention disposition; the "
            f"frozen three are {', '.join(schema.RETENTION_DISPOSITIONS)}")
    return disposition


# WHAT AN ADAPTER'S `destroy` MAY ANSWER, and nothing else. The OCI core
# answers exactly these four and documents them; a fifth is an answer this
# build cannot read, and reading it would mean guessing which side of
# "positively gone" it falls on.
_DESTROY_STATES = ("absent", "quiescent", "running", "uncertain")

# W6636: the two delivery providers' endings, as they arrive on the destroy
# answer. `destroy` removes the container and then settles each mounted root
# on that same absence evidence, so a manager reading only the RUNTIME state
# is reading one third of what the adapter just told it.
#
# THE TERMINAL ONES AND THE ONE THAT IS NOT. `not-delivered` means this
# attempt never had that provider and there is nothing to end; `torn-down`
# means the root is proved gone. `unresolved` is the adapter saying it could
# not establish either, and it is the whole reason these are read: a launch
# root that survives its runtime is manager storage nobody will ever free.
_PROVIDER_ENDINGS = ("not-delivered", "torn-down", "unresolved")
_PROVIDER_SETTLED = ("not-delivered", "torn-down")
# Named where they arrive, because each provider answers its own shape:
# credentials carry the attempt and the slots they released, launch carries
# neither, and both explain an unresolved ending.
_PROVIDER_MEMBERS = ("lifecycle_state",), ("why", "attempt_id", "slots")

# The destroy answer's own member contract, named ONCE and CLOSED.
#
# Re-review [P0]: the two provider endings were OPTIONAL, and optional is
# exactly the hole. A first answer of runtime `absent` with launch
# `unresolved` correctly left cleanup pending; a later answer that simply
# OMITTED `launch` then settled it `complete`, because an absent member reads
# as "no such provider" and the manager remembers nothing. The adapter was
# called -- what was lost was the knowledge that a launch teardown was owed.
#
# THE MANAGER CANNOT REMEMBER APPLICABILITY WITHOUT INVENTING DURABLE STATE
# FOR IT, so the contract says it instead: every provider answers on every
# destroy, and an attempt that has no such provider says so with the explicit
# `not-delivered` ending. `authorize_cleanup` is a generic public boundary and
# `OciAdapter` always answering both is a habit of one implementation, not an
# invariant -- and a durable invariant that rests on a habit is not one.
_DESTROY_MEMBERS = ("runtime_id", "state", "why", "credentials", "launch"), ()


def _chosen(artifact_ids):
    """THE CANONICAL ARTIFACT SET a retention command names.

    Written once because two callers need the identical answer: the operation
    identity is derived from it and the command body carries it, and a set that
    differed between them would make the identity name an act the body does not
    describe.
    """
    names = own(artifact_ids, what="retained artifact ids")
    if type(names) is not list or not names:
        raise ContractRefusal(
            "integrity", "schema",
            f"a retention decision names at least one artifact; this is "
            f"{name_value(artifact_ids)}")
    return sorted({boundaries.identity(name, "an artifact id")
                   for name in names})


def _committed(store, operation, kind, what):
    """THE COMMITTED ANSWER behind a persisted decision, or a refusal.

    Review [P1]: a stored row and the digest beside it can be edited TOGETHER.
    `intake_receipt_of` recomputed the receipt and compared it against
    `intakes.receipt_digest`, which proves the row is self-consistent and
    nothing else; `retentions_of` compared nothing at all. Either row then
    authorizes a destroy.

    This is the durability class W4 already closed for intake decisions, and
    retention rows joined it the moment cleanup authorization started reading
    them. The independent evidence is the operation this manager COMMITTED:
    its identity is derived from the attempt's own immutable context, and what
    it RECORDED is the one account of the decision a store edit cannot reach.

    THE COMMITTED RESULT RATHER THAN THE COMMITTED SIGNATURE. Reconstructing
    the signature was the first thing I wrote and it is wrong: `intake.record`
    is signed over the ADAPTER'S OWN COLLECTION, whose member order and exact
    shape the persisted rows do not preserve, so a faithful row produced a
    mismatched signature as soon as an attempt held two artifacts. The result
    is what this manager itself composed, it is byte-stable in the journal, and
    comparing against it needs no guess about what somebody else sent.

    INTEGRITY RATHER THAN A COLLISION. `store.replay` raises
    `refused.operation-collision` on a signature mismatch, which is right for a
    CALLER reusing an identity and wrong here: nobody called anything twice,
    the store was edited. So the row is read directly, its own signature is
    what replays it, and divergence is reported as what it is.
    """
    record = store.operation_record(operation["operation_id"])
    if record is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation "
            f"{name_value(operation['operation_id'])} and this manager "
            f"committed no such operation; a self-consistent row is not "
            f"evidence that a decision was ever made")
    if record["kind"] != kind:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation "
            f"{name_value(operation['operation_id'])}, which this manager "
            f"committed as {name_value(record['kind'])} rather than "
            f"{name_value(kind)}")
    _, committed = store.replay(operation["operation_id"], record["signature"],
                                kind=kind)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation "
            f"{name_value(operation['operation_id'])}, which this manager "
            f"committed with no recorded answer to compare against")
    return committed


def _attempt_of(connection, attempt_id):
    """THE ONE CROSSING out of the attempts table for this module."""
    found = connection.execute(
        "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if found is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no runtime attempt {name_value(attempt_id)}")
    return boundaries.row(found, "a persisted attempt", schema.ATTEMPT_COLUMNS)


def _fixed_assignment(attempt):
    if attempt["assignment_generation"] is None:
        return None
    return documents.assignment(
        work_ref=documents.work_ref(
            authority_uuid=attempt["authority_uuid"],
            work_id=attempt["work_id"]),
        participant=attempt["assignment_participant"],
        generation=attempt["assignment_generation"])


def _require_assignment(attempt, attempt_id):
    expect = _fixed_assignment(attempt)
    if expect is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no fixed assignment; "
            f"custody of a result belongs to an exact generation and there is "
            f"none")
    return expect


def _require_participant(port, expect, attempt_id):
    if port.participant != expect["participant"]:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for {name_value(port.participant)} and attempt "
            f"{name_value(attempt_id)} is assigned to "
            f"{name_value(expect['participant'])}")


def _derived(kind, attempt, operands):
    """One derived operation identity and its signature.

    Derived rather than minted, like every other act in this manager, so a
    restart names what it already did instead of doing it twice. The id is the
    retry key and the signature is the binding over the kind and every durable
    operand -- comparing the key alone compares the weaker half.
    """
    assignment = _fixed_assignment(attempt)
    signed = {**operands, "attempt_id": attempt["runtime_attempt_id"],
              "expect": assignment}
    # §13 AT THE CONSTRUCTOR, for the reason `manager_signature` states: an
    # operation identity is PORTABLE, and a guard that runs at the eventual
    # write is a guard that runs after the caller already holds the leak.
    # These identities are derived with `digest` rather than through
    # `manager_signature`, so the walk it performs has to be performed here --
    # measured, not assumed: before this, a live bearer in an attempt row's own
    # id composed straight into a returned operation id.
    check_no_durable_secret({"kind": kind, "operands": signed},
                            what="an operation signature")
    operation_id = kind + ":" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": assignment})[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": kind,
            "operands": {**signed, "operation_id": operation_id}}))


def collect_operation(attempt):
    """The `output.collect` identity, fixed per attempt."""
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    return _derived("output.collect", taken, {})


def intake_operation(attempt):
    """The `intake.record` identity, fixed per attempt rather than per digest.

    The same rule the freeze receiver states: if the identity varied with the
    bytes, two different collections would be two different operations and BOTH
    would commit, which is the opposite of what taking custody once means. The
    identity is the ACT; the signature carries the bytes.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    return _derived("intake.record", taken, {})


def retain_operation(attempt, retention_policy_digest, artifact_ids,
                     disposition):
    """The `output.retain` identity.

    THE POLICY DIGEST IS PART OF THE IDENTITY, not just of the signature. A
    second retention decision made under a DIFFERENT policy is a different act
    and must be able to commit; a repeat of the same decision under the same
    policy is a replay. An identity that ignored the policy would make the
    first policy the only one an attempt could ever be decided under.

    AND SO ARE THE ARTIFACTS AND THE DISPOSITION -- review [P1]. `outputRetain
    Body` has five required operands and the identity carried two of them, so
    ONE policy deciding differently about two artifacts produced one operation
    id and two signatures: the second command came back as an operation
    collision, and a policy that says "keep this, discard that" is the
    ordinary case rather than an exotic one. The identity is the ACT, and
    these four operands are what make two acts different.

    THE SET IS CANONICAL before it is digested. The caller's order and any
    repeats are not part of the decision -- the same artifacts named twice or
    in another order are the same act, and an identity that disagreed would
    turn a retry into a second commit.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    boundaries.text(retention_policy_digest, "a retention policy digest")
    chosen = _chosen(artifact_ids)
    _disposition(disposition)
    assignment = _fixed_assignment(taken)
    operands = {"attempt_id": taken["runtime_attempt_id"],
                "expect": assignment,
                "artifact_ids": chosen,
                "disposition": disposition,
                "retention_policy_digest": retention_policy_digest}
    check_no_durable_secret({"kind": "output.retain", "operands": operands},
                            what="an operation signature")
    operation_id = "output.retain:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": assignment,
        "artifact_ids": chosen,
        "disposition": disposition,
        "retention_policy_digest": retention_policy_digest,
    })[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "output.retain",
            "operands": {**operands, "operation_id": operation_id}}))


def destroy_operation(attempt, receipt_digest, retention_policy_digest):
    """The `runtime.destroy` identity, over the exact body the contract fixes.

    `runtimeDestroyBody` requires the intake receipt digest and the retention
    policy digest, so both ride the identity: destroying under a different
    receipt or a different policy is a different act, and an identity that
    ignored them would replay an authorization that was never given.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    # BOTH DIGESTS RIDE A DURABLE IDENTITY, so both are owned as durable text
    # here. A digest that cannot be stored cannot be part of an operation id a
    # restart has to reproduce.
    boundaries.text(receipt_digest, "an intake receipt digest")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    assignment = _fixed_assignment(taken)
    check_no_durable_secret(
        {"kind": "runtime.destroy",
         "operands": {"attempt_id": taken["runtime_attempt_id"],
                      "expect": assignment,
                      "runtime_id": taken["runtime_id"],
                      "intake_receipt_digest": receipt_digest,
                      "retention_policy_digest": retention_policy_digest}},
        what="an operation signature")
    operation_id = "runtime.destroy:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": assignment,
        "intake_receipt_digest": receipt_digest,
        "retention_policy_digest": retention_policy_digest,
    })[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "runtime.destroy",
            "operands": {"attempt_id": taken["runtime_attempt_id"],
                         "expect": assignment,
                         "runtime_id": taken["runtime_id"],
                         "intake_receipt_digest": receipt_digest,
                         "retention_policy_digest": retention_policy_digest,
                         "operation_id": operation_id}}))


def failed_start_destroy_operation(attempt, failed_start_record_digest,
                                   retention_policy_digest):
    """W32648: the `runtime.destroy-failed-start` identity, over W34998's body.

    THE SIBLING OF `destroy_operation`, and a sibling for the same reason its
    command is one: a start that created a container and then failed has no
    intake receipt, because nothing was frozen, collected or admitted. What
    authorizes this removal is the manager's own durable `runtime.start-failed`
    record, and its digest rides the identity exactly as the receipt's does
    above -- destroying under a different failure record or a different policy
    is a different act.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    boundaries.text(failed_start_record_digest,
                    "a failed-start record digest")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    assignment = _fixed_assignment(taken)
    operands = {"attempt_id": taken["runtime_attempt_id"],
                "expect": assignment,
                "runtime_id": taken["runtime_id"],
                "failed_start_record_digest": failed_start_record_digest,
                "retention_policy_digest": retention_policy_digest}
    check_no_durable_secret({"kind": "runtime.destroy-failed-start",
                             "operands": operands},
                            what="an operation signature")
    operation_id = "runtime.destroy-failed-start:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": assignment,
        "failed_start_record_digest": failed_start_record_digest,
        "retention_policy_digest": retention_policy_digest,
    })[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "runtime.destroy-failed-start",
            "operands": {**operands, "operation_id": operation_id}}))


def refused_session_destroy_operation(attempt, refusal_record_digest,
                                     retention_policy_digest):
    """W32576: the `runtime.destroy-refused-session` identity.

    THE THIRD SIBLING OF `destroy_operation`, and a sibling for the reason the
    second one is. A handshake this manager refused has no intake receipt --
    nothing was frozen, collected or admitted -- and it is not a failed start:
    the container is running. What authorizes this removal is the manager's own
    durable `session.unsupported-version` record, and its digest rides the
    identity exactly as the receipt's and the failure record's do -- destroying
    under a different refusal or a different policy is a different act.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    boundaries.text(refusal_record_digest, "a refusal record digest")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    assignment = _fixed_assignment(taken)
    operands = {"attempt_id": taken["runtime_attempt_id"],
                "expect": assignment,
                "runtime_id": taken["runtime_id"],
                "refusal_record_digest": refusal_record_digest,
                "retention_policy_digest": retention_policy_digest}
    check_no_durable_secret({"kind": "runtime.destroy-refused-session",
                             "operands": operands},
                            what="an operation signature")
    operation_id = "runtime.destroy-refused-session:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": assignment,
        "refusal_record_digest": refusal_record_digest,
        "retention_policy_digest": retention_policy_digest,
    })[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "runtime.destroy-refused-session",
            "operands": {**operands, "operation_id": operation_id}}))


# -- intake -------------------------------------------------------------------


def request_intake(store, port, adapter, *, attempt_id):
    """Ask for the frozen material, then record what actually arrived.

    The journal entry is written BEFORE the adapter is called, for the reason
    runtime start and freeze both do: a crash between the two boundaries must
    be answerable, and an operation a restart can replay is what makes "did we
    already collect this" a question with an answer.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.capability(getattr(adapter, "collect", None),
                          "the runtime adapter's collect")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    frozen = _collectable(store, attempt, attempt_id)
    operation = collect_operation(attempt)
    signature = manager_signature(
        "output.collect", {"attempt_id": attempt_id, "expect": expect,
                           "result_id": frozen["result_id"],
                           "operation": dict(operation)})
    store.transact(
        operation["operation_id"], "output.collect", signature,
        lambda connection: _requested(store, connection, attempt_id, frozen,
                                      operation))
    # THE WHOLE IDENTITY crosses the boundary, and the RESULT MANIFEST DIGEST
    # with it: `outputActionBody` carries one, and an adapter handed only an
    # attempt id would have to guess which frozen result it is collecting.
    collected = adapter.collect({
        "attempt_id": attempt_id, "assignment": expect,
        "result_id": frozen["result_id"],
        "result_manifest_digest": frozen["manifest_digest"],
        "output_names": [entry["output_name"] for entry in frozen["artifacts"]],
        "operation": dict(operation)})
    return record_intake(store, port, attempt_id=attempt_id,
                         collected=collected)


def _collectable(store, attempt, attempt_id):
    """The frozen result, or the reason there is nothing to take custody of."""
    if attempt["output"] != "frozen":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} output is {attempt['output']}; "
            f"custody is taken of a FROZEN result, and no other state is one")
    frozen = frozen_output_of(store, attempt_id)
    if frozen is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no recorded frozen result; "
            f"the axis says frozen and this manager holds nothing to collect")
    return frozen


def _requested(store, connection, attempt_id, frozen, operation):
    # THE DECISIVE READ IS THIS ONE, from a row re-read under the write lock.
    # The check outside is an optimistic early refusal and authorizes nothing:
    # an `invalid` or `discarded` observation committing in that window must
    # win over the `frozen` row the call started from.
    _collectable(store, _attempt_of(connection, attempt_id), attempt_id)
    return documents.collect_requested(
        attempt_id=attempt_id, result_id=frozen["result_id"],
        operation=dict(operation))


def record_intake(store, port, *, attempt_id, collected):
    """Compare what arrived against what was frozen, take custody, and seal.

    NOTHING IN THE ADAPTER'S ANSWER IS ADOPTED. Every artifact it reports is
    matched against the row the freeze recorded, by identity, content digest
    and byte count; the only member this manager takes from the adapter is
    where the material now IS, because that is the one fact the freeze could
    not already know.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    taken = boundaries.document(collected, "a collection observation",
                                required=("result_id", "artifacts"))
    operation = intake_operation(attempt)
    # THE SIGNATURE IS OVER THE BYTES THAT ARRIVED, and it is computed before
    # anything about today is consulted.
    #
    # W6628's receiver was corrected for this exact ordering twice: first the
    # output axis was read ahead of the journal, so an exact retry refused once
    # the axis had moved; then the correction left a lookup of ANOTHER row
    # ahead of it, so removing that row made an exact retry refuse too. Replay
    # is a fact about an identity that already settled, and nothing about today
    # is a precondition for reproducing the answer it produced -- so the only
    # things above this line are the attempt's own fixed identity and the
    # adapter's own bytes.
    signature = manager_signature(
        "intake.record", {"attempt_id": attempt_id, "expect": expect,
                          "collected": taken})
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="intake.record")
    if found:
        return already
    # Every check below this line applies to a genuinely NEW record.
    frozen = _collectable(store, attempt, attempt_id)
    held = _compared(taken, frozen, attempt_id)
    return store.transact(
        operation["operation_id"], "intake.record", signature,
        lambda connection: _seal(store, port, connection, attempt_id, expect,
                                 frozen, held, operation))


def _compared(taken, frozen, attempt_id):
    """The collection, against the freeze. Owned, then compared."""
    boundaries.identity(taken["result_id"], "a collected result id")
    if taken["result_id"] != frozen["result_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"the collection names result {name_value(taken['result_id'])} and "
            f"this attempt froze {name_value(frozen['result_id'])}")
    # `boundaries.document` already owned the whole answer, members and all, so
    # this list is a fresh built-in copy rather than a live reference into the
    # adapter's object. What is left is the SHAPE.
    arrived = taken["artifacts"]
    if type(arrived) is not list:
        raise ContractRefusal(
            "integrity", "schema",
            f"a collection's artifacts are a list; this is "
            f"{name_value(taken['artifacts'])}")
    expected = {entry["artifact_id"]: entry for entry in frozen["artifacts"]}
    held = []
    seen = set()
    for entry in arrived:
        one = boundaries.document(
            entry, "a collected artifact",
            required=("artifact_id", "content_digest", "bytes",
                      "custody_locator"))
        artifact_id = boundaries.identity(one["artifact_id"], "an artifact id")
        if artifact_id in seen:
            raise ContractRefusal(
                "integrity", "schema",
                f"the collection reports artifact {name_value(artifact_id)} "
                f"twice; one artifact is taken into custody once")
        seen.add(artifact_id)
        declared = expected.get(artifact_id)
        if declared is None:
            # AN ARTIFACT NOBODY FROZE IS NOT CUSTODY, IT IS SUBSTITUTION.
            # Accepting it would let a collector add material the frozen
            # result never declared, under the result's own identity.
            raise ContractRefusal(
                "integrity", "schema",
                f"the collection reports artifact {name_value(artifact_id)}, "
                f"which attempt {name_value(attempt_id)} never froze")
        for what, was, now in (("content digest", declared["content_digest"],
                                one["content_digest"]),
                               ("byte count", declared["bytes"],
                                one["bytes"])):
            if was != now:
                raise ContractRefusal(
                    "integrity", "digest" if what == "content digest"
                    else "limit",
                    f"artifact {name_value(artifact_id)} was frozen with "
                    f"{what} {name_value(was)} and arrived with "
                    f"{name_value(now)}")
        held.append({"artifact_id": artifact_id,
                     "content_digest": boundaries.text(one["content_digest"],
                                                       "a content digest"),
                     "bytes": one["bytes"],
                     "custody_locator": boundaries.text(
                         one["custody_locator"], "a custody locator")})
    missing = sorted(set(expected) - seen)
    if missing:
        # POSITIVE ABSENCE IS NOT AN EMPTY HAND. A collection that simply did
        # not mention an artifact has not proved it is gone, and sealing on it
        # would record custody of material this manager does not hold.
        raise ContractRefusal(
            "ambiguous", "collection",
            f"the collection is missing artifact(s) "
            f"{', '.join(name_value(one) for one in missing)} that attempt "
            f"{name_value(attempt_id)} froze; custody is of the whole result")
    held.sort(key=lambda one: one["artifact_id"])
    return held


def _seal(store, port, connection, attempt_id, expect, frozen, held,
          operation):
    # THE DECISIVE PRECONDITION, re-read under the write lock.
    attempt = _attempt_of(connection, attempt_id)
    _collectable(store, attempt, attempt_id)
    # CUSTODY IS DECIDED HERE, at the last moment before the durable write, and
    # a dead assignment is QUARANTINED rather than refused.
    #
    # W6628 pinned this in the module that hands intake its work: its liveness
    # read "is inside the write and is still only a read", the window cannot be
    # zero, and "material from an assignment that ended anyway is quarantined
    # at intake rather than trusted here". Refusing would destroy the evidence
    # of what a worker produced because its assignment ended while it was being
    # collected; accepting would present it as the live generation's result.
    # Quarantine is the third answer, and it is the reason the disposition
    # vocabulary has that word in it.
    live = port.assignment_of(expect["work_ref"]["work_id"],
                              expect["work_ref"]["authority_uuid"])
    if live is None:
        custody, why = "quarantined", (
            f"{expect['work_ref']['work_id']} holds no live assignment; this "
            f"material was collected for a generation that has ended")
    elif live != expect:
        custody, why = "quarantined", (
            f"the live assignment is generation {live['generation']} for "
            f"{live['participant']} and this material was produced under "
            f"generation {expect['generation']} for {expect['participant']}")
    else:
        custody, why = "accepted", (
            "collected under the live assignment this attempt is fixed to")
    # RECOVERABLE CANCELLATION MATERIAL IS A DIFFERENT FACT FROM RETAINED
    # MATERIAL, and this is where the two are told apart.
    #
    # The acceptance for this Job requires them to stay distinguishable. They
    # are different reasons for the same bytes still being on disk: a
    # cancelled attempt's material is kept so the work can be RECOVERED, and a
    # retained artifact is kept because a policy said to KEEP it. Deriving this
    # from the worker disposition rather than storing a second opinion means it
    # cannot disagree with the axis it is about.
    recoverable = 1 if attempt["worker_disposition"] == _CANCELLED else 0
    receipt = documents.intake_receipt(
        attempt_id=attempt_id, assignment=expect,
        result_id=frozen["result_id"],
        manifest_digest=frozen["manifest_digest"],
        custody=custody, why=why, recoverable=bool(recoverable),
        artifacts=[documents.intake_artifact(
            artifact_id=one["artifact_id"],
            content_digest=one["content_digest"], bytes=one["bytes"],
            custody_locator=one["custody_locator"]) for one in held],
        operation=dict(operation))
    receipt_digest = digest(receipt)
    connection.execute(
        "INSERT INTO intakes (runtime_attempt_id, receipt_digest, result_id, "
        "manifest_digest, custody, why, recoverable, collect_operation_id, "
        "intake_operation_id, sealed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (attempt_id, receipt_digest, frozen["result_id"],
         frozen["manifest_digest"], custody, why, recoverable,
         collect_operation(attempt)["operation_id"],
         operation["operation_id"], store._now()))
    for one in held:
        connection.execute(
            "INSERT INTO intake_artifacts (runtime_attempt_id, artifact_id, "
            "content_digest, bytes, custody_locator) VALUES (?, ?, ?, ?, ?)",
            (attempt_id, one["artifact_id"], one["content_digest"],
             one["bytes"], one["custody_locator"]))
    # SEALED IS THE RECORD OF CUSTODY, and quarantined material is in custody
    # too. The axis says what became of the OUTPUT; `custody` says on what
    # terms this manager holds it. Leaving quarantined material unsealed would
    # invite a second collection of bytes already taken.
    observe(store, attempt_id=attempt_id, axis="output", value="sealed")
    return {**receipt, "receipt_digest": receipt_digest}


def intake_receipt_of(store, attempt_id):
    """The intake receipt this attempt recorded, or None.

    ABSENCE IS AN ANSWER HERE, not an error: "this attempt has not been taken
    into custody" is exactly what cleanup authorization asks, and it is the
    reason `blocked-on-intake` is a state rather than a retry.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    found = store._connection.execute(
        "SELECT * FROM intakes WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if found is None:
        return None
    row = boundaries.row(found, "a persisted intake", schema.INTAKE_COLUMNS)
    artifacts = [boundaries.row(entry, "a persisted intake artifact",
                                schema.INTAKE_ARTIFACT_COLUMNS)
                 for entry in store._connection.execute(
                     "SELECT * FROM intake_artifacts WHERE "
                     "runtime_attempt_id = ? ORDER BY artifact_id",
                     (attempt_id,)).fetchall()]
    attempt = _attempt_of(store._connection, attempt_id)
    # THE OPERATION IS RE-DERIVED, NOT REBUILT FROM THE ROW.
    #
    # The receipt digest is over the whole document including the operation
    # that produced it, so a read-back that reconstructed a partial operation
    # would digest to something the destroy command could never carry. It is
    # derived from the attempt exactly as it was when the receipt was written,
    # and the stored id is compared against it -- which is a real check: a
    # receipt whose act does not derive from its own attempt is not this
    # attempt's receipt.
    operation = intake_operation(attempt)
    if operation["operation_id"] != row["intake_operation_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"the persisted intake of {name_value(attempt_id)} names "
            f"{name_value(row['intake_operation_id'])} and this attempt "
            f"derives {name_value(operation['operation_id'])}")
    receipt = documents.intake_receipt(
        attempt_id=row["runtime_attempt_id"],
        assignment=_fixed_assignment(attempt),
        result_id=row["result_id"], manifest_digest=row["manifest_digest"],
        custody=row["custody"], why=row["why"],
        recoverable=bool(row["recoverable"]),
        artifacts=[documents.intake_artifact(
            artifact_id=entry["artifact_id"],
            content_digest=entry["content_digest"], bytes=entry["bytes"],
            custody_locator=entry["custody_locator"])
            for entry in artifacts],
        operation=dict(operation))
    # AND THE DIGEST IS RECOMPUTED rather than served from the column. The
    # stored one is compared against it, so a row edited underneath this
    # manager cannot authorize a destroy: what a caller receives is derived
    # from the document it is reading.
    #
    # THAT COMPARISON IS NOT EVIDENCE ON ITS OWN -- review [P1]. The row and
    # the digest beside it are both in the same table and an edit can move
    # them together, after which the receipt recomputes perfectly and
    # authorizes a destroy. The committed `intake.record` operation is the
    # independent account, and it is checked below against the signature this
    # receipt reconstructs.
    # THE READ-SIDE WALK. A write-side guard cannot see a later store edit, and
    # this hands back a document AND a digest that authorizes a destroy -- so a
    # bearer written into a custody locator behind this build's back would leave
    # here inside protocol identity. The same argument `certified_agent_session_
    # profile` was added for, at the boundary that reads custody.
    check_no_durable_secret(receipt, what="a persisted intake receipt")
    committed = _committed(
        store, operation, "intake.record",
        f"the persisted intake of {name_value(attempt_id)}")
    recomputed = digest(receipt)
    # AND AGAINST THE COMMITTED RECEIPT, which is what closes the case the
    # signature alone cannot. `why` is COMPOSED by `_seal` from the live
    # assignment it found; it reaches the journal inside the committed RESULT
    # and never inside the signature, so an edit to `why` and the digest
    # beside it reconstructs a receipt whose signature still matches. The
    # committed answer is the one account of this decision that a store edit
    # cannot reach.
    if committed is None or recomputed != committed.get("receipt_digest"):
        raise ContractRefusal(
            "integrity", "digest",
            f"the persisted intake of {name_value(attempt_id)} recomputes to "
            f"{name_value(recomputed)} and this manager committed "
            f"{name_value(None if committed is None else committed.get('receipt_digest'))}; "
            f"a row and the digest beside it moved together and the journal "
            f"did not")
    if recomputed != row["receipt_digest"]:
        raise ContractRefusal(
            "integrity", "digest",
            f"the persisted intake of {name_value(attempt_id)} records "
            f"receipt digest {name_value(row['receipt_digest'])} and its "
            f"document recomputes to {name_value(recomputed)}")
    return {**receipt, "receipt_digest": recomputed}


# -- retention ----------------------------------------------------------------


def decide_retention(store, port, adapter, *, attempt_id, artifact_ids,
                     disposition, retention_policy_digest):
    """Record what happens to intaken material, under the policy that decided.

    THE POLICY IS BOUND, NEVER READ. `retention_policy_digest` is one of ten
    `*_policy_digest` members of the assignment manifest and the frozen schema
    states the shape of none of them; a manager binds a policy by identity and
    acts on the operation that cites it. This records which artifacts, which
    disposition, and under which policy -- and nothing here opens the document.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    boundaries.capability(getattr(adapter, "retain", None),
                          "the runtime adapter's retain")
    _disposition(disposition)
    chosen = _chosen(artifact_ids)
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    operation = retain_operation(attempt, retention_policy_digest, chosen,
                                 disposition)
    signature = manager_signature(
        "output.retain", {"attempt_id": attempt_id, "expect": expect,
                          "artifact_ids": chosen,
                          "disposition": disposition,
                          "retention_policy_digest": retention_policy_digest})
    # REPLAY FIRST, and above it only the attempt's own fixed identity and the
    # caller's own operands. Nothing about today is a precondition for
    # reproducing the answer an identity already produced.
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="output.retain")
    if found:
        return already
    # Every check below this line applies to a genuinely NEW decision.
    #
    # RETENTION IS DECIDED OVER MATERIAL THIS MANAGER HOLDS. Deciding the fate
    # of artifacts that were never taken into custody would record an authority
    # over bytes nobody has -- and it is exactly the ordering
    # `blocked-on-intake` exists to keep straight.
    receipt = intake_receipt_of(store, attempt_id)
    if receipt is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has not been taken into "
            f"custody; retention decides what happens to material this "
            f"manager holds, and it holds none")
    held = {one["artifact_id"] for one in receipt["artifacts"]}
    for artifact_id in chosen:
        if artifact_id not in held:
            raise ContractRefusal(
                "policy", "retention",
                f"artifact {name_value(artifact_id)} is not in this attempt's "
                f"custody; retention names what was intaken")
    # THE COMMAND IS DELIVERED -- review [P1]. Typing `adapter.retain` and
    # never calling it left one of the two frozen output commands unissued:
    # the manager recorded a disposition and the side holding the material was
    # never told. `outputRetainBody` is what tells it, and the operation rides
    # beside the body so the delivery is effectively-once at the adapter too.
    #
    # BEFORE THE JOURNAL, for the reason `authorize_cleanup` states: the
    # cleanup and retention axes have no `requested` state to record an intent
    # in, so journalling one would invent a mechanism the axis does not have.
    # A crash between the two leaves the decision unrecorded and the next
    # identical command replays it.
    #
    # NOTHING THE ADAPTER ANSWERS IS ADOPTED. What it returns says the command
    # was received; what the material's disposition IS was decided here.
    adapter.retain({**documents.retain_command(
        assignment_ref=expect, runtime_attempt_id=attempt_id,
        artifact_ids=list(chosen), disposition=disposition,
        retention_policy_digest=retention_policy_digest),
        "operation": dict(operation)})
    return store.transact(
        operation["operation_id"], "output.retain", signature,
        lambda connection: _retain(store, connection, attempt_id,
                                   chosen, disposition,
                                   retention_policy_digest, operation))


def _retain(store, connection, attempt_id, chosen, disposition,
            retention_policy_digest, operation):
    now = store._now()
    for artifact_id in chosen:
        # ONE DECISION PER ARTIFACT, and a second one under a different policy
        # REPLACES it rather than accumulating beside it. Two live dispositions
        # for one artifact would make "may this be destroyed" a question with
        # two answers, which is the question cleanup authorization asks.
        connection.execute(
            "INSERT INTO retentions (runtime_attempt_id, artifact_id, "
            "disposition, retention_policy_digest, retain_operation_id, "
            "decided_at) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (runtime_attempt_id, artifact_id) DO UPDATE SET "
            "disposition = excluded.disposition, "
            "retention_policy_digest = excluded.retention_policy_digest, "
            "retain_operation_id = excluded.retain_operation_id, "
            "decided_at = excluded.decided_at",
            (attempt_id, artifact_id, disposition, retention_policy_digest,
             operation["operation_id"], now))
    return documents.retention_decided(
        attempt_id=attempt_id, artifact_ids=list(chosen),
        disposition=disposition,
        retention_policy_digest=retention_policy_digest,
        operation=dict(operation))


def retentions_of(store, attempt_id):
    """Every retention decision this attempt carries, or an empty tuple.

    THE ROWS ARE MATERIALIZED AND THEIR MEMBERS READ OFF THE SAME NAME the
    row-owning comprehension bound, which is the shape `frozen_output_of` uses
    and is not a style choice.

    The boundary inventory discovers which persisted columns this build reads
    by following origins from name to name. My first version pulled the rows
    through a second local and read members off it, and every retention column
    became INVISIBLE to that walk -- the read was still owned, but the
    inventory could no longer see it, so nothing could have told me a column
    had stopped being covered. The flat second scan caught it as
    `decided_at`, which is also an `offers` column name, and that collision is
    the only reason it surfaced at all.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    decisions = [boundaries.row(entry, "a persisted retention",
                                schema.RETENTION_COLUMNS)
                 for entry in store._connection.execute(
                     "SELECT * FROM retentions WHERE runtime_attempt_id = ? "
                     "ORDER BY artifact_id", (attempt_id,)).fetchall()]
    answered = tuple(documents.retention(
        artifact_id=entry["artifact_id"], disposition=entry["disposition"],
        retention_policy_digest=entry["retention_policy_digest"],
        decided_at=entry["decided_at"]) for entry in decisions)
    # THE SAME READ-SIDE WALK, and it is not redundant with the one above: a
    # retention decision is written under its own operation and can be edited
    # in the store without the intake row changing at all.
    check_no_durable_secret(list(answered), what="persisted retention decisions")
    # AND EVERY DECISION IS AUTHENTICATED AGAINST THE ACT THAT MADE IT --
    # review [P1]. Nothing compared these rows to anything: a direct edit of
    # `disposition` and `retention_policy_digest` became a valid destroy
    # authorization, because `_authorized` reads exactly this projection to
    # decide whether every artifact in custody carries a decision under THIS
    # policy.
    #
    # Retention rows joined intake's durability class the moment they started
    # authorizing cleanup, so they get intake's answer: the committed
    # `output.retain` operation is the independent evidence, and a row edited
    # underneath this manager names an act whose committed answer does not
    # describe it.
    #
    # PER SURVIVING ROW, NOT PER GROUP -- correction review [P1], and the two
    # rules it reconciles are both this module's own. `_retain` deliberately
    # stores ONE CURRENT DECISION PER ARTIFACT and its conflict update lets a
    # later policy replace one artifact without touching its peers. My first
    # version grouped the rows that are current NOW by their operation id,
    # derived a command from each group, and required that derived set to equal
    # the historical one.
    #
    # Those two rules contradict each other. One valid command decides A and B;
    # a later valid command replaces B alone; A still names the authentic A+B
    # act while the current group for that act holds only A. The reader derived
    # an A-only operation, found the journal carrying the A+B one, and reported
    # a forgery -- blocking retention reads and cleanup over a row nobody
    # touched.
    #
    # So the question asked of the journal is the one that is actually true of
    # a surviving row: does the committed act this row NAMES include THIS
    # artifact, under this disposition and this policy? A historical peer that
    # has since been re-decided is irrelevant to that, and a deleted decision
    # leaves its artifact undecided for cleanup rather than making a different,
    # still-authentic row invalid.
    for entry in decisions:
        committed = _committed(
            store, {"operation_id": entry["retain_operation_id"]},
            "output.retain",
            f"the persisted retention of {name_value(attempt_id)}")
        # THE ACT MUST BE ABOUT THIS ATTEMPT -- review round 4, and it is the
        # half the membership check could not supply.
        #
        # An artifact id, a disposition and a policy digest are LOCAL DECISION
        # DATA, not identities. Two attempts can each hold an `artifact-1` and
        # decide it `retain` under one policy, so a row whose
        # `retain_operation_id` was edited to name the OTHER attempt's
        # authentic committed act matched on all three and was accepted --
        # cleanup for one attempt drawing its authorization from a decision
        # made about another, with no journal row forged anywhere.
        #
        # The committed act names the attempt it was made about. That is the
        # binding, and comparing values that merely happen to agree is not.
        if committed.get("attempt_id") != attempt_id:
            raise ContractRefusal(
                "integrity", "schema",
                f"the persisted retention of {name_value(attempt_id)} names "
                f"committed act {name_value(entry['retain_operation_id'])}, "
                f"which was made about "
                f"{name_value(committed.get('attempt_id'))}; a decision about "
                f"another attempt is not this attempt's authorization however "
                f"exactly its artifacts and policy agree")
        if (entry["artifact_id"] not in (committed.get("artifact_ids") or ())
                or committed.get("disposition") != entry["disposition"]
                or committed.get("retention_policy_digest")
                != entry["retention_policy_digest"]):
            raise ContractRefusal(
                "integrity", "digest",
                f"the persisted retention of {name_value(attempt_id)} reads "
                f"artifact {name_value(entry['artifact_id'])} as "
                f"{name_value(entry['disposition'])} under "
                f"{name_value(entry['retention_policy_digest'])}, and the "
                f"committed act {name_value(entry['retain_operation_id'])} it "
                f"names decided "
                f"{name_value(committed.get('disposition'))} under "
                f"{name_value(committed.get('retention_policy_digest'))} for "
                f"{', '.join(name_value(one) for one in (committed.get('artifact_ids') or ())) or 'nothing'}; "
                f"the row moved and the journal did not")
    return answered


# -- cleanup ------------------------------------------------------------------


def authorize_cleanup(store, port, adapter, *, attempt_id,
                      retention_policy_digest):
    """Destroy the runtime, and end the cleanup axis at the ending it reached.

    `blocked-on-intake` IS A STATE, NOT A RETRY. The frozen axis has it, which
    means cleanup WAITS on intake rather than racing it: an attempt whose
    material has not been taken into custody is recorded as blocked and the
    adapter is never called. A caller that looped instead would be inventing a
    mechanism the axis already has.

    `retained` IS TERMINAL AND IS NOT `complete`. Material kept on purpose and
    material cleaned up are different endings, and reporting retention as
    completion would erase the reason the material still exists.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    boundaries.capability(getattr(adapter, "destroy", None),
                          "the runtime adapter's destroy")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    # THE RECEIPT IS READ BEFORE THE JOURNAL IS ASKED, and it has to be:
    # `runtimeDestroyBody` puts `intake_receipt_digest` in the body, so the
    # digest is part of this act's IDENTITY and there is no operation to look
    # up without it. It is safe above the line because an intake row is written
    # once and never updated -- unlike the state this call used to read here,
    # which moves.
    receipt = intake_receipt_of(store, attempt_id)
    if receipt is None:
        return _block_on_intake(store, attempt, attempt_id)
    operation = destroy_operation(attempt, receipt["receipt_digest"],
                                  retention_policy_digest)
    signature = manager_signature(
        "runtime.destroy",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "intake_receipt_digest": receipt["receipt_digest"],
         "retention_policy_digest": retention_policy_digest})
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="runtime.destroy")
    if found:
        return already
    # Every check below this line applies to a genuinely NEW destroy. The
    # terminal-cleanup refusal is one of them ON PURPOSE: an EXACT retry of a
    # destroy that already settled replays the answer it produced, and only a
    # DIFFERENT destroy -- another policy, another receipt -- is the one being
    # refused for arriving after an ending.
    # THE ASSIGNMENT MUST BE OVER -- review [P1], and W4 pinned it. Destroying
    # the runtime of an assignment the authority still reports LIVE tears out a
    # worker that remains authorized to execute: the manager would be ending
    # something the authority has not, which is the one direction this boundary
    # never runs.
    #
    # BELOW THE REPLAY, like every other check here. An exact retry of a
    # destroy that already committed reproduces its answer and must keep doing
    # so after the assignment has moved on; only a genuinely new destroy waits.
    #
    # ASKED OF THE AUTHORITY rather than inferred from an axis. The axes here
    # describe the RUNTIME; whether the assignment is still authorized is the
    # authority's fact and nothing this manager stores can answer it.
    live = port.assignment_of(expect["work_ref"]["work_id"],
                              expect["work_ref"]["authority_uuid"])
    if live == expect:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is still the live assignment "
            f"for {expect['participant']} generation {expect['generation']}; "
            f"cleanup destroys the runtime of an assignment that has ENDED or "
            f"been fenced, and this one is still authorized to execute")
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    _authorized(store, attempt_id, receipt, retention_policy_digest)
    # THE FROZEN ASYMMETRY, refused rather than worked around.
    #
    # `uncertain` may never become `destroyed` -- the axis states the reason
    # itself: destruction is a fact about the world, and inferring it from a
    # failure to look would report a cleaned-up runtime that is still executing
    # somebody's code. So an attempt observed uncertain cannot have its cleanup
    # settled until reconciliation returns the axis to a positive observation,
    # and this says so instead of writing the terminal value by another route.
    if attempt["execution_runtime"] == "uncertain":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution runtime is uncertain; "
            f"the frozen axis never moves from uncertain to destroyed, so "
            f"cleanup waits for a reconciliation that observes what is true")
    # THE ADAPTER IS CALLED BEFORE THE JOURNAL HERE, and that is a departure
    # from freeze and runtime start, which both journal an intent first.
    #
    # It is the frozen axis that decides it. The output axis HAS
    # `freeze-requested`, so a freeze has somewhere to record "asked, not yet
    # settled"; the cleanup axis is `pending, blocked-on-intake, complete,
    # retained, failed` and has no such state. Journalling an intent with
    # nowhere to record it would mean inventing a mechanism the axis does not
    # have, which is the same mistake as treating `blocked-on-intake` as a
    # retry loop.
    #
    # So a crash between the engine call and this journal leaves cleanup
    # `pending`, and the next authorization runs the destroy again -- which is
    # safe because a destroy is `rm --force` followed by an inspection of the
    # exact identity, and an identity that is already gone answers `absent`.
    # Recording an ending nobody observed would not be safe, and that is the
    # trade this ordering makes.
    observed = _destroyed(adapter, attempt, attempt_id, operation,
                          receipt["receipt_digest"], retention_policy_digest)
    # AN UNSETTLED CLEANUP IS NOT JOURNALLED, and W6636 found out why the hard
    # way. `_settle` returned `cleanup_unsettled` from INSIDE the transaction,
    # so the operation committed with that document as its result -- and an
    # exact retry, which is the same receipt under the same policy, replayed it
    # forever. "The offer to try again is the axis staying where it is" was
    # true of the axis and false of the operation: cleanup stayed `pending` and
    # could never leave it.
    #
    # So a destroy that did not settle returns WITHOUT committing, which puts
    # it in exactly the state the ordering note above already describes as safe
    # -- the same one a crash between the engine call and this journal leaves.
    # The next authorization runs the destroy again, and a destroy is
    # `rm --force` followed by an inspection of the exact identity, so an
    # identity already gone answers `absent`.
    #
    # A POSITIVELY SURVIVING RUNTIME IS NOT THIS CASE. That is a settled
    # failure of this cleanup, `failed` is what the frozen axis calls it, and
    # it is journalled like any other ending.
    pending = _not_an_ending(store, attempt, attempt_id, observed, operation)
    if pending is not None:
        return pending
    return store.transact(
        operation["operation_id"], "runtime.destroy", signature,
        lambda connection: _settle(store, connection, attempt_id, receipt,
                                   retention_policy_digest, observed,
                                   operation))


def authorize_failed_start_cleanup(store, port, adapter, *, attempt_id,
                                   retention_policy_digest):
    """W32648: end the attempt a start FAILED after creating a container.

    Approver ruling M33800, and the ending it fixes is precise. A start that
    reached the engine, created a container and then failed leaves an exact
    runtime, NO worker disposition this manager may invent, NO frozen result,
    NO intake receipt -- and therefore no way through `authorize_cleanup`,
    whose whole authorization is that receipt. The regression that used to
    cover this manufactured a disposition and a frozen output to get through,
    which is the fabrication this Work exists to remove.

    WHAT AUTHORIZES IT INSTEAD is the manager's own durable
    `runtime.start-failed` record. It is a fact this manager wrote about its
    own act, and its digest rides the operation identity exactly as the
    receipt's does on the other path.

    THE ORDER IS THE RULING'S. Fence at the AUTHORITY before anything
    destructive -- asked of the authority rather than inferred from an axis,
    because whether an assignment is still authorized is not something this
    manager stores. Then remove the exact attached runtime, positively observe
    its absence, and settle the delivery roots on that absence and nothing
    else.

    AND THE RESULT DIRECTORY IS LEFT WHERE IT IS. M33800 makes the existing
    unique per-generation, per-attempt directory the custody boundary: it began
    untrusted and stays untrusted after a start fault, so this ends at
    `retained` -- the frozen axis's own word for material kept on purpose --
    and deletes nothing. A later explicit retention cleanup owns that deletion.
    Nothing here writes a worker disposition, freezes an output, creates a
    second result, or admits one byte to the proposal pipeline.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    # W34998'S CAPABILITY, and not `destroy`. The two commands are siblings
    # with closed member sets precisely so a caller cannot authorize one
    # removal with the other's digest, and typing the wrong one here would
    # undo that at the only place it matters.
    boundaries.capability(getattr(adapter, "destroy_failed_start", None),
                          "the runtime adapter's failed-start destroy")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    record = _failed_start_record(store, attempt, attempt_id)
    operation = failed_start_destroy_operation(attempt, record["digest"],
                                               retention_policy_digest)
    signature = manager_signature(
        "runtime.destroy-failed-start",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "failed_start_record_digest": record["digest"],
         "retention_policy_digest": retention_policy_digest})
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="runtime.destroy-failed-start")
    if found:
        return already
    # EVERY CHECK BELOW THIS LINE APPLIES TO A GENUINELY NEW REMOVAL, which is
    # the ordering `authorize_cleanup` establishes and the reason it gives:
    # an exact retry of a removal that already settled replays its answer, and
    # only a different one -- another policy, another record -- waits.
    live = port.assignment_of(expect["work_ref"]["work_id"],
                              expect["work_ref"]["authority_uuid"])
    if live == expect:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is still the live assignment "
            f"for {expect['participant']} generation {expect['generation']}; "
            f"a failed start is fenced at the authority before anything is "
            f"destroyed, and this assignment is still authorized to execute")
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    # THE SAME FROZEN ASYMMETRY. `uncertain` never becomes `destroyed`,
    # because destruction is a fact about the world and inferring it from a
    # failure to look would report a cleaned-up runtime that is still running
    # somebody's code. A failed start reaches `uncertain` exactly when
    # reconciliation could not establish what exists -- so this is the case,
    # not an edge of it.
    if attempt["execution_runtime"] == "uncertain":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution runtime is uncertain; "
            f"the failed start attached no identity this manager can name, so "
            f"there is nothing to remove and nothing to prove absent")
    if attempt["runtime_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no attached runtime; this "
            f"ending exists for a start that CREATED a container, and a start "
            f"that created none has no exact identity to remove")
    observed = _destroyed_failed_start(adapter, attempt, attempt_id, operation,
                                       record["digest"],
                                       retention_policy_digest)
    pending = _not_an_ending(store, attempt, attempt_id, observed, operation)
    if pending is not None:
        return pending
    return store.transact(
        operation["operation_id"], "runtime.destroy-failed-start", signature,
        lambda connection: _settle_recordless_cleanup(
            store, connection, attempt_id, observed, operation,
            why="failed-start cleanup settled retained"))


def authorize_refused_session_cleanup(store, port, adapter, *, session_ref,
                                     retention_policy_digest):
    """W32576: end the attempt whose handshake this manager REFUSED.

    THE ENDING THIS WORK EXISTS FOR. `settle_unsupported_version` derives the
    refusal from the persisted session's own certified profile, records it, and
    fences the assignment at the authority. That is where it stopped: a
    `cancel-requested` axis and a stop order are not an ending. This is the
    rest of it -- exact force-removal, positive absence, credential and launch
    settlement, and the lane given back only after all three.

    IT TAKES THE SESSION REFERENCE RATHER THAN THE ATTEMPT, and that is the
    correction the shape of the record forces. The refusal is filed under the
    session act -- attempt, posture, epoch, provider session -- so an ending
    named by attempt alone would have to GUESS which session's refusal it was
    settling on an attempt that had more than one. The attempt is read from the
    proved session row, never taken as a free operand.

    WHY NOT `authorize_cleanup`. Its whole authorization is an intake receipt,
    and there is none: `request_intake` needs a frozen result, `request_freeze`
    needs a terminal worker disposition already recorded, and a handshake this
    manager could not complete produces neither. Writing a disposition to open
    that door is the fabrication W32648 exists to remove, and it would be a
    lie besides -- the worker did not cancel, complete, or reject a plan. It
    never got to say anything.

    WHY NOT `authorize_failed_start_cleanup` EITHER. A start that failed and a
    handshake that refused are different facts with different records, and
    W34998's ruling makes the member sets closed against each other precisely
    so one authorization cannot be spent on the other's ending.

    AND THE RESULT DIRECTORY IS LEFT WHERE IT IS, on the same rule M33800 set
    for the sibling. Whatever the worker wrote before the handshake refused was
    written by a worker this manager never negotiated with: it began untrusted
    and stays untrusted. So this ends at `retained` -- the frozen axis's own
    word for material kept on purpose -- and deletes nothing, freezes nothing,
    and admits not one byte to the proposal pipeline.
    """
    from .handshake import unsupported_version_operation_id
    from .sessions import _require_session, _session_ref
    reference = _session_ref(session_ref)
    boundaries.text(retention_policy_digest, "a retention policy digest")
    # W34998'S RULE, one sibling further along. Typing the wrong capability
    # here would undo the closed member sets at the only place it matters.
    boundaries.capability(getattr(adapter, "destroy_refused_session", None),
                          "the runtime adapter's refused-session destroy")
    row = _require_session(store._connection, reference)
    attempt_id = row["runtime_attempt_id"]
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    record = _refused_session_record(
        store, attempt, attempt_id,
        unsupported_version_operation_id(reference), reference, row)
    operation = refused_session_destroy_operation(attempt, record["digest"],
                                                  retention_policy_digest)
    signature = manager_signature(
        "runtime.destroy-refused-session",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "refusal_record_digest": record["digest"],
         "retention_policy_digest": retention_policy_digest})
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="runtime.destroy-refused-session")
    if found:
        return already
    # EVERY CHECK BELOW THIS LINE APPLIES TO A GENUINELY NEW REMOVAL, which is
    # the ordering both siblings establish and for the reason they give: an
    # exact retry of a removal that already settled replays its answer, and
    # only a different one waits.
    live = port.assignment_of(expect["work_ref"]["work_id"],
                              expect["work_ref"]["authority_uuid"])
    if live == expect:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is still the live assignment "
            f"for {expect['participant']} generation {expect['generation']}; "
            f"a refused handshake is fenced at the authority before anything "
            f"is destroyed, and this assignment is still authorized to "
            f"execute")
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    # THE SAME FROZEN ASYMMETRY BOTH SIBLINGS ARE UNDER. `uncertain` never
    # becomes `destroyed`, because destruction is a fact about the world and
    # inferring it from a failure to look would report a cleaned-up runtime
    # that is still running somebody's code.
    if attempt["execution_runtime"] == "uncertain":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution runtime is "
            f"uncertain; this manager cannot say what exists, so there is "
            f"nothing to remove and nothing to prove absent")
    if attempt["runtime_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no attached runtime; a "
            f"refused handshake is an ending for a session that was speaking "
            f"to a container, and there is none to remove")
    observed = _destroyed_refused_session(adapter, attempt, attempt_id,
                                          operation, record["digest"],
                                          retention_policy_digest)
    pending = _not_an_ending(store, attempt, attempt_id, observed, operation)
    if pending is not None:
        return pending
    return store.transact(
        operation["operation_id"], "runtime.destroy-refused-session",
        signature,
        lambda connection: _settle_recordless_cleanup(
            store, connection, attempt_id, observed, operation,
            why="refused-session cleanup settled retained"))


def _refused_session_record(store, attempt, attempt_id, operation_id,
                            reference, row):
    """The durable record that AUTHORIZES this removal, and its digest.

    READ FROM THE JOURNAL, never recomposed, and owned before it is believed.
    W32648 review [P0] settled the rules this follows: the row's KIND is
    verified, its answer is decoded through the journal's own reader rather
    than adopted as stored bytes, and the members that must agree with the
    world are compared against the attempt and the reference.

    THE RUNTIME IS THE MEMBER THAT MATTERS. A record written when this session
    was speaking to one container must not authorize destroying a different
    one, so `runtime_id` is compared with what the attempt is attached to NOW
    and a disagreement is `integrity/schema` rather than a reason to recompose.
    """
    held = store.operation_record(operation_id)
    if held is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no recorded "
            f"unsupported-version refusal for this session; the ending is "
            f"authorized by the record this manager wrote when it refused, "
            f"and a manager that never refused has nothing to end")
    if held["kind"] != "session.unsupported-version":
        raise ContractRefusal(
            "integrity", "schema",
            f"the journalled operation authorizing this ending is recorded as "
            f"kind {name_value(held['kind'])}; a row of another kind is not a "
            f"handshake refusal however well its result reads")
    _, committed = store.replay(operation_id, held["signature"],
                                kind="session.unsupported-version")
    record = boundaries.document(committed, "a committed refusal record",
                                 required=documents.SESSION_UNSUPPORTED_VERSION)
    for member, mine in (("attempt_id", attempt_id),
                         ("assignment", _fixed_assignment(attempt)),
                         ("runtime_id", attempt["runtime_id"]),
                         ("posture", reference["posture"]),
                         ("session_epoch", reference["session_epoch"]),
                         ("provider_session_id",
                          reference["provider_session_id"])):
        if record[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded refusal names {member} "
                f"{name_value(record[member])} and this ending is for "
                f"{name_value(mine)}; the record and the act it authorizes "
                f"must describe one runtime and one session")
    # AND WHAT IT DECIDED, not only who it is about.
    #
    # Review [P1]: the six comparisons above prove the record names this
    # attempt, this runtime and this session -- and nothing proved it still
    # SAYS the thing that authorizes destroying them. The contract carries
    # `decision`, `category` and `code` precisely so a later reader can know
    # what was decided, and this reader digested them without reading them:
    # a row whose decision had become `accepted` retained its exact member set
    # and all six identities, and authorized a removal.
    #
    # THE CLOSED VERDICT, all three members together. `refused` alone is a
    # category shared with every other refusal this manager can raise, and
    # `unsupported-version` in `decision` alone is a word the record could
    # carry while its typed pair said something else. The three agree or this
    # is not the document its kind promises.
    for member, expected in (("decision", "unsupported-version"),
                             ("category", "refused"),
                             ("code", "unsupported-version")):
        if record[member] != expected:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded refusal says {member} "
                f"{name_value(record[member])}; only a committed "
                f"{name_value('unsupported-version')} refusal authorizes this "
                f"ending, and a record that no longer says so is not one")
    # THE VERSIONS ARE THE REFUSAL'S OWN EVIDENCE, and they must still be a
    # refusal's. An unsupported-version answer is exactly a wire version that
    # is NOT the pinned one, so two integers that agree describe a successful
    # negotiation and authorize nothing.
    for member in ("pinned_wire_version", "agent_protocol_version"):
        if type(record[member]) is not int or type(record[member]) is bool:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded refusal names {member} "
                f"{name_value(record[member])}; a wire version is an integer")
    if record["pinned_wire_version"] == record["agent_protocol_version"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"the recorded refusal names the same wire version "
            f"{record['pinned_wire_version']} as pinned and as answered; a "
            f"version this manager certified is a negotiation that SUCCEEDED "
            f"and is not an ending to authorize")
    # AND THE PROFILE IS THE SESSION'S OWN, compared against the persisted row
    # rather than against a certification lookup. Review [P1] asks for this on
    # the RETAINED evidence for a reason worth keeping: reading certification
    # here would make an exact retry stop replaying the moment the profile was
    # withdrawn, which is the effectively-once defect this Work already
    # corrected once on the recording side.
    if record["profile_digest"] != row["profile_digest"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"the recorded refusal was derived against profile "
            f"{name_value(record['profile_digest'])} and this session holds "
            f"{name_value(row['profile_digest'])}; a refusal about another "
            f"profile is not evidence about this session")
    return {"record": record, "digest": digest(record)}


def _destroyed_refused_session(adapter, attempt, attempt_id, operation,
                               record_digest, retention_policy_digest):
    """The refused-session crossing, and the same observation rules.

    THE WHOLE BODY CROSSES, as it does on both siblings: what makes this
    removal authorized rather than merely requested is the digest of the
    refusal record, and the operation rides beside the body so the delivery is
    effectively-once at the adapter too.
    """
    answer = boundaries.document(
        adapter.destroy_refused_session({
            **documents.refused_session_destroy_command(
                assignment_ref=_fixed_assignment(attempt),
                runtime_attempt_id=attempt_id,
                runtime_id=attempt["runtime_id"],
                refusal_record_digest=record_digest,
                retention_policy_digest=retention_policy_digest),
            "operation": dict(operation)}),
        "a refused-session destroy observation",
        required=_DESTROY_MEMBERS[0], optional=_DESTROY_MEMBERS[1])
    boundaries.identity(answer["runtime_id"], "an observed runtime id")
    boundaries.text(answer["why"], "a destroy observation's reason")
    boundaries.text(answer["state"], "a destroy observation's state")
    if answer["state"] not in _DESTROY_STATES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(answer['state'])} is not a destroy observation; the "
            f"four this build reads are {', '.join(_DESTROY_STATES)}")
    for provider in ("credentials", "launch"):
        _provider_ending(answer[provider], provider)
    if answer["runtime_id"] != attempt["runtime_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the adapter answered about {name_value(answer['runtime_id'])} "
            f"and this attempt is attached to "
            f"{name_value(attempt['runtime_id'])}")
    return answer


def _settle_recordless_cleanup(store, connection, attempt_id, observed,
                               operation, *, why):
    """The ending for a removal NO INTAKE RECEIPT authorized.

    `_settle` chooses between `complete` and `retained` from what retention
    kept. There is nothing to count on these endings: no intake happened, no
    artifact was decided, and the untrusted result directory itself is the
    material that stays. So the ending is `retained` unconditionally -- the
    frozen axis's own word for material kept on purpose -- and reporting it as
    `complete` would erase the reason the directory still exists.

    ONE OWNER FOR BOTH RECORDLESS ENDINGS, which is what it should have been.
    A failed start and a refused handshake reach exactly the same terminal
    state check, the same axis transitions and the same lane release; only the
    reason written beside the release differs, and that is an operand.

    IT WAS BRIEFLY TWO. I wrote a copy of `_settle_failed_start_cleanup`
    rather than merge, on the ground that W32648 owned that code and was out
    for review -- and review [P2] caught that the ground had already gone:
    W32648 closed satisfying at seq 36991 and this Work was claimed at 37155.
    I checked that the BLOCK had cleared and did not check that the REVIEW
    had, which is the kind of stale premise a comment states confidently and
    nobody re-reads. Two separately editable copies of a terminal-state check
    are two orders that agree until one is edited.
    """
    attempt = _attempt_of(connection, attempt_id)
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    state = observed["state"]
    if state != "absent":
        observe(store, attempt_id=attempt_id, axis="cleanup", value="failed")
        return documents.cleanup_settled(
            attempt_id=attempt_id, cleanup="failed", state=state,
            why=observed["why"], kept=[], operation=dict(operation))
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    observe(store, attempt_id=attempt_id, axis="cleanup", value="retained")
    # W32649: the lane is given back only after positive absence and every
    # applicable provider ending -- reuse is ordered behind the proof, not
    # beside it.
    lanes._release_lane(connection, attempt_id=attempt_id,
                        reference=lanes.lane_reference(attempt), why=why)
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup="retained", state=state,
        why=observed["why"], kept=[], operation=dict(operation))


def _failed_start_record(store, attempt, attempt_id):
    """The durable record that AUTHORIZES this removal, and its digest.

    READ FROM THE JOURNAL, never recomposed. The record is what
    `request_runtime_start` wrote when the start failed, under an operation
    identity derived from the attempt and its fixed start operation -- so a
    restarted manager finds the same row, and a manager that never had the
    failure finds nothing and is told so rather than proceeding.

    THE DIGEST IS OVER THE RETAINED RESULT, which is the fact this act is
    authorized by. Recomputing it from the attempt row would be this manager
    asserting what it once decided instead of reading it.
    """
    from .attempts import start_failure_operation_id
    operation_id = start_failure_operation_id(attempt)
    held = store.operation_record(operation_id)
    if held is None or held.get("state") != "committed" \
            or held.get("result") is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} holds no committed failed-start "
            f"record; this ending is authorized by the manager's own account "
            f"of the start that failed, and without one there is nothing "
            f"saying this runtime came from a failed start rather than a "
            f"live one")
    # ITS KIND, because an identity is not a warrant. Review [P0]: this read a
    # committed row under a derived id and asked nothing else about it -- so a
    # row this manager committed as something else, under an id that happened
    # to collide, would have authorized a destroy. The same rule `_committed`
    # already applies to intake and retention decisions.
    if held.get("kind") != "runtime.start-failed":
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names operation "
            f"{name_value(operation_id)}, which this manager committed as "
            f"{name_value(held.get('kind'))} rather than a failed-start "
            f"record")
    # THE DECODED RESULT, through the journal's own reader. `operation_record`
    # hands back the stored bytes; `store.replay` is what turns a committed
    # answer back into the document this manager composed, and it is the same
    # reader `_committed` uses for intake and retention decisions.
    _, committed = store.replay(operation_id, held["signature"],
                                kind="runtime.start-failed")
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names operation "
            f"{name_value(operation_id)}, which this manager committed with "
            f"no recorded answer to authorize a removal with")
    record = boundaries.document(committed,
                                 "a committed failed-start record",
                                 required=documents.RUNTIME_START_FAILED)
    # ...AND THE FACTS IT NAMES ARE THIS ATTEMPT'S OWN.
    #
    # Review [P0], and the defect is worth stating exactly: the digest of the
    # record was cited as the authorization while the command was built from
    # the CURRENT `attempt["runtime_id"]`. Nothing compared the two, so a
    # record written when the failed start attached `runtime-1` authorized
    # destroying whatever the row named later. Two independently read facts,
    # combined into one authorization, is the shape every crossing in this
    # module has been corrected for.
    #
    # A DISAGREEMENT IS AN INTEGRITY FAILURE, not a reason to recompose. The
    # journal is the source of the failure identity and its digest; if the row
    # it is meant to authorize has moved, the honest answer is that this
    # manager cannot say which of the two describes the world.
    for member, mine in (("attempt_id", attempt_id),
                         ("expect", _fixed_assignment(attempt)),
                         ("start_operation_id",
                          _start_operation_id_of(attempt)),
                         ("runtime_id", attempt["runtime_id"])):
        if record[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the failed-start record for attempt "
                f"{name_value(attempt_id)} names {member} "
                f"{name_value(record[member])} and this attempt now carries "
                f"{name_value(mine)}; the record is what authorizes this "
                f"removal, and one that describes another act cannot "
                f"authorize this one")
    # `execution_runtime` IS DELIBERATELY NOT COMPARED, and the reason is that
    # it is the one member of the record that is allowed to move. It captures
    # the axis at the instant the failure settled; a later reconciliation may
    # legitimately observe the runtime again, so requiring the two to agree
    # would refuse a cleanup for having looked. What the axis must be NOW is
    # checked directly by the caller -- `uncertain` refuses and an unattached
    # runtime refuses -- which is a stronger statement than agreeing with a
    # stale one.
    return {"record": record, "digest": digest(record)}


def _start_operation_id_of(attempt):
    from .attempts import _start_operation_id
    return _start_operation_id(attempt)


def _destroyed_failed_start(adapter, attempt, attempt_id, operation,
                            record_digest, retention_policy_digest):
    """W34998's crossing, and the same observation rules `_destroyed` applies.

    THE WHOLE BODY CROSSES, as it does on the receipt-authorized path: what
    makes this removal authorized rather than merely requested is the digest
    of the failed-start record, and the operation rides beside the body so the
    delivery is effectively-once at the adapter too.
    """
    answer = boundaries.document(
        adapter.destroy_failed_start({
            **documents.failed_start_destroy_command(
                assignment_ref=_fixed_assignment(attempt),
                runtime_attempt_id=attempt_id,
                runtime_id=attempt["runtime_id"],
                failed_start_record_digest=record_digest,
                retention_policy_digest=retention_policy_digest),
            "operation": dict(operation)}),
        "a failed-start destroy observation",
        required=_DESTROY_MEMBERS[0], optional=_DESTROY_MEMBERS[1])
    boundaries.identity(answer["runtime_id"], "an observed runtime id")
    boundaries.text(answer["why"], "a destroy observation's reason")
    boundaries.text(answer["state"], "a destroy observation's state")
    if answer["state"] not in _DESTROY_STATES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(answer['state'])} is not a destroy observation; the "
            f"four this build reads are {', '.join(_DESTROY_STATES)}")
    for provider in ("credentials", "launch"):
        _provider_ending(answer[provider], provider)
    if answer["runtime_id"] != attempt["runtime_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the adapter answered about {name_value(answer['runtime_id'])} "
            f"and this attempt is attached to "
            f"{name_value(attempt['runtime_id'])}")
    return answer


def _not_an_ending(store, attempt, attempt_id, observed, operation):
    """The destroy answers that leave cleanup where it is, or None.

    ONE OWNER FOR "THIS DID NOT SETTLE", and it sits outside the journal for
    the reason above. Both members of it are the same statement about
    evidence: the engine could not say what the runtime is, or it said the
    runtime is gone while a root this manager delivered is not.
    """
    state = observed["state"]
    if state == "uncertain":
        # NOT AN ENDING. The engine's account did not settle the question, and
        # a cleanup axis that moved anyway would be recording an answer nobody
        # observed.
        return documents.cleanup_unsettled(
            attempt_id=attempt_id, state=state, why=observed["why"],
            operation=dict(operation))
    if state != "absent":
        return None
    waiting = _unsettled_providers(observed)
    if not waiting:
        return None
    # W6636 [P0]: POSITIVE CONTAINER ABSENCE IS NOT THE WHOLE ENDING.
    #
    # The container is the attempt's process domain and proving it gone is
    # what makes it SAFE to settle the roots it mounted -- but it is not
    # evidence that they were settled. `destroy` answers all three, and a
    # manager that read only the runtime recorded `complete` while a launch
    # root was still on disk: an attempt reported cleaned up, its lane
    # reusable, and manager storage nothing would ever come back for.
    #
    # RECORDED ON THE AXIS THAT IS TRUE AND NOT ON THE ONE THAT IS NOT. The
    # runtime really is destroyed and that observation stands; it is CLEANUP
    # that has not finished. Failing closed here costs a retry; succeeding
    # closed loses the root.
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    return documents.cleanup_unsettled(
        attempt_id=attempt_id, state=state,
        why=f"the runtime is absent and its delivery teardown is not settled "
            f"({'; '.join(waiting)}); cleanup is not complete until every "
            f"delivered root is proved gone",
        operation=dict(operation))


def _block_on_intake(store, attempt, attempt_id):
    """Recorded as blocked, with no adapter call and no refusal."""
    if attempt["cleanup"] == "pending":
        observe(store, attempt_id=attempt_id, axis="cleanup",
                value="blocked-on-intake")
    return documents.cleanup_blocked(
        attempt_id=attempt_id,
        why=f"attempt {attempt_id} has not been taken into custody; cleanup "
            f"is authorized by an intake receipt and there is none")


def _authorized(store, attempt_id, receipt, retention_policy_digest):
    """Every artifact in custody carries a decision, under THIS policy.

    Cleanup that ran with an undecided artifact would be destroying material
    nobody ruled on, and cleanup that accepted decisions made under a different
    policy would be citing an authorization that was never given for this act.
    Both are answered by comparing identities, which is all a digest allows and
    all this needs.
    """
    decided = {one["artifact_id"]: one for one in retentions_of(store,
                                                                attempt_id)}
    for held in receipt["artifacts"]:
        one = decided.get(held["artifact_id"])
        if one is None:
            raise ContractRefusal(
                "policy", "retention",
                f"artifact {name_value(held['artifact_id'])} is in custody "
                f"with no retention decision; cleanup destroys nothing "
                f"nobody ruled on")
        if one["retention_policy_digest"] != retention_policy_digest:
            raise ContractRefusal(
                "policy", "retention",
                f"artifact {name_value(held['artifact_id'])} was decided under "
                f"retention policy {name_value(one['retention_policy_digest'])}"
                f" and this destroy cites "
                f"{name_value(retention_policy_digest)}")


def _provider_ending(ending, provider):
    """One delivery provider's ending, owned where it arrives.

    W6636 owns the crossing rather than the providers, and this is the whole
    of what the crossing needs to know: which of three endings the provider
    reached. The members beyond `lifecycle_state` are the provider's own
    account -- the credential ending names the slots it released -- and they
    are named so the contract stays closed without this build pretending each
    provider answers the same shape.
    """
    required, optional = _PROVIDER_MEMBERS
    taken = boundaries.document(ending, f"a {provider} teardown ending",
                                required=required, optional=optional)
    state = boundaries.text(taken["lifecycle_state"],
                            f"a {provider} teardown ending's state")
    if state not in _PROVIDER_ENDINGS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(state)} is not a {provider} teardown ending; the "
            f"three this build reads are {', '.join(_PROVIDER_ENDINGS)}")
    return state


def _unsettled_providers(answer):
    """Every provider that did NOT reach a terminal ending, with its reason.

    A LIST RATHER THAN A BOOLEAN, because two roots can be unresolved for two
    different reasons and an operator has to act on both.

    EVERY PROVIDER IS PRESENT BY CONTRACT, so there is no absent member to
    interpret here. `not-delivered` is how an attempt with no such provider
    says so, and it is terminal; the reading that used to be inferred from an
    omission is now stated by the adapter that knows it.
    """
    waiting = []
    for provider in ("credentials", "launch"):
        ending = answer[provider]
        if ending["lifecycle_state"] not in _PROVIDER_SETTLED:
            waiting.append(
                f"{provider}: "
                f"{ending.get('why') or ending['lifecycle_state']}")
    return waiting


def _destroyed(adapter, attempt, attempt_id, operation, receipt_digest,
               retention_policy_digest):
    """What became of the runtime, as an OBSERVATION rather than a status.

    POSITIVE ABSENCE OR NOTHING. The adapter's `destroy` orders a removal and
    then inspects the exact identity, and only an engine that says this
    identity does not exist produces `absent`. A command that returned zero is
    not evidence that anything is gone.

    A RUNTIME THAT WAS NEVER STARTED IS ALREADY ABSENT, and asking an engine to
    remove an identity this manager never attached would be asking about
    something that has no name.

    BUT AN ATTACHED IDENTITY IS ALWAYS ASKED ABOUT, EVEN ONCE IT IS DESTROYED.
    Review [P0]: this short-circuited on `execution_runtime == "destroyed"` and
    answered a synthetic `absent` WITHOUT CALLING THE ADAPTER -- and that
    answer carries no provider endings, which are optional. So the exact shape
    this round introduced defeated itself: a first destroy that truthfully
    moved the runtime axis to `destroyed` while a provider reported
    `unresolved` left cleanup pending, and the retry that was supposed to
    finish the teardown skipped the adapter entirely and recorded `complete`
    with no provider retried at all.

    The runtime axis is a fact about the CONTAINER and says nothing about the
    roots it mounted. Removing an identity the engine no longer has is safe --
    `destroy` is `rm --force` followed by an inspection of the exact identity,
    and an identity already gone answers `absent` -- so the cheap short-circuit
    bought nothing and cost the second half of the ending.

    THE OUTSTANDING ENDING SURVIVES BY BEING RE-ASKED rather than remembered.
    The provider's state is the provider's fact, so a restart that re-runs the
    destroy gets the current answer from the adapter instead of replaying a
    manager's note about it.
    """
    if attempt["runtime_id"] is None:
        # NO IDENTITY MEANS NO DELIVERY EITHER. A runtime that was never
        # started mounted nothing, so both providers are `not-delivered` --
        # said explicitly, because this module holds every other answer to
        # that same rule.
        undelivered = {"credentials": {"lifecycle_state": "not-delivered"},
                       "launch": {"lifecycle_state": "not-delivered"}}
        if attempt["execution_runtime"] == "destroyed":
            return {"state": "absent",
                    "why": "this attempt already observed its runtime "
                           "destroyed and never attached an identity",
                    **undelivered}
        if attempt["execution_runtime"] != "not-started":
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} execution runtime is "
                f"{attempt['execution_runtime']} and no runtime is attached; "
                f"there is no identity to destroy and no absence to prove")
        return {"state": "absent",
                "why": "no runtime was ever started for this attempt",
                **undelivered}
    # THE WHOLE AUTHORIZING BODY CROSSES -- review [P1]. A bare runtime id
    # omits both digests `runtimeDestroyBody` requires, which are precisely
    # what makes this destroy authorized rather than merely requested, and it
    # makes the adapter guess which protocol operation it is executing. The
    # operation rides beside the body so the delivery is effectively-once at
    # the adapter too.
    answer = boundaries.document(
        adapter.destroy({**documents.destroy_command(
            assignment_ref=_fixed_assignment(attempt),
            runtime_attempt_id=attempt_id,
            runtime_id=attempt["runtime_id"],
            intake_receipt_digest=receipt_digest,
            retention_policy_digest=retention_policy_digest),
            "operation": dict(operation)}),
        "a destroy observation",
        # W6636 [P0]: THE PROVIDER ENDINGS ARE NAMED AND REQUIRED. They were
        # not named at all first -- so `boundaries.document` refused the real
        # adapter's answer outright -- and then named but optional, which let
        # an omission erase a teardown the previous answer said was owed.
        required=_DESTROY_MEMBERS[0], optional=_DESTROY_MEMBERS[1])
    # EVERY MEMBER OWNED WHERE IT ARRIVES, not just the envelope. An envelope
    # owner proves the members are present; it says nothing about what they
    # are, and all three decide something here.
    boundaries.identity(answer["runtime_id"], "an observed runtime id")
    boundaries.text(answer["why"], "a destroy observation's reason")
    boundaries.text(answer["state"], "a destroy observation's state")
    if answer["state"] not in _DESTROY_STATES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(answer['state'])} is not a destroy observation; the "
            f"four this build reads are {', '.join(_DESTROY_STATES)}")
    for provider in ("credentials", "launch"):
        _provider_ending(answer[provider], provider)
    if answer["runtime_id"] != attempt["runtime_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the adapter answered about {name_value(answer['runtime_id'])} "
            f"and this attempt is attached to "
            f"{name_value(attempt['runtime_id'])}")
    return answer


def _settle(store, connection, attempt_id, receipt, retention_policy_digest,
            observed, operation):
    """The ending, decided from the observation and from what stays."""
    attempt = _attempt_of(connection, attempt_id)
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    # THE ANSWERS THAT DO NOT SETTLE ARE `_not_an_ending`'S, and they are
    # decided before this transaction opens -- an unsettled outcome must not
    # be journalled, or the exact retry that is supposed to finish the cleanup
    # replays the fact that it did not. What reaches here is an ending.
    state = observed["state"]
    if state != "absent":
        # POSITIVELY STILL THERE. The destroy was ordered and the runtime
        # survived it, which is a settled failure of this cleanup rather than
        # an unknown -- and `failed` is what the frozen axis calls that.
        observe(store, attempt_id=attempt_id, axis="cleanup", value="failed")
        return documents.cleanup_settled(
            attempt_id=attempt_id, cleanup="failed", state=state,
            why=observed["why"], kept=[], operation=dict(operation))
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    kept = tuple(one["artifact_id"] for one in retentions_of(store, attempt_id)
                 if one["disposition"] in KEEPS_MATERIAL)
    # `retained` AND `complete` ARE DIFFERENT ENDINGS. Anything kept -- by
    # policy or by quarantine -- ends `retained`, because reporting kept
    # material as cleaned up would erase the reason it still exists. Only a
    # cleanup with nothing left behind is `complete`.
    ending = "retained" if kept or receipt["custody"] == "quarantined" \
        else "complete"
    observe(store, attempt_id=attempt_id, axis="cleanup", value=ending)
    # W32649: AND THE LANE IS GIVEN BACK, in the same write as the ending.
    #
    # THIS is the release condition the boundary names: positive runtime
    # ABSENCE -- proved above, `state == "absent"` and nothing else reaches
    # here -- plus every applicable provider ending, which `_unsettled_providers`
    # has already required, plus the custody and retention decisions this
    # ending is composed from. Not one of those alone is enough, and the
    # ending is the only place all of them are true at once.
    #
    # `retained` RELEASES AND `failed` DOES NOT, which is the ruled difference
    # between them. Retained material lives in CUSTODY -- a manager-owned
    # sibling the worker never sees -- so a successor collides with nothing;
    # a failed cleanup means the runtime survived its destroy, and a lane
    # released while a container is still there is the overlap this exists to
    # prevent. The `failed` branch above returns before this line.
    lanes._release_lane(connection, attempt_id=attempt_id,
                       reference=lanes.lane_reference(attempt),
                       why=f"cleanup settled {ending}")
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup=ending, state=state,
        why=observed["why"], kept=list(kept), operation=dict(operation))
