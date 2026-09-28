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

import json
import os
import stat

from ..contracts import (ContractRefusal, check_no_durable_secret, digest,
                         own)
from ..contracts.errors import name_value, sample_of
from . import attempts, boundaries, documents, lanes, schema
from .attempts import observe
from .authority_port import FENCE, GATE_DISCHARGE, GATE_DISCHARGED_PHASE
from .output import frozen_output_of
from .store import manager_signature

__all__ = ["collect_operation", "intake_operation", "request_intake",
           "record_intake", "intake_receipt_of", "retain_operation",
           "decide_retention", "retentions_of", "destroy_operation",
           "authorize_cleanup", "failed_start_destroy_operation",
           "authorize_failed_start_cleanup",
           "refused_session_destroy_operation",
           "authorize_refused_session_cleanup",
           "GATE_DISCHARGE_KIND", "QUIESCENCE_GATE", "RUNTIME_ABSENT",
           "discharge_quiescence_gate", "gate_discharge_of",
           "CLEANUP_ENDINGS", "CLEANUP_RECEIPT", "cleanup_of"]

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
    # THE COMMITTED RECEIPT COMES BEFORE THE PRECONDITION, and W197661 is why.
    #
    # `review_driver.end_implementation` promises that every one of its nine
    # steps replays and that a death between any two re-enters and finishes.
    # STEP FIVE DID NOT. `_collectable` admits `frozen` only and runs ahead of
    # `record_intake`'s replay -- but `sealed` is the state a SUCCESSFUL intake
    # LEAVES BEHIND, observed at the end of `_seal`. So an ending that got past
    # intake and failed at retention, publication or the freeze refused here
    # forever, and the stage stayed `answering` and asked again on every tick.
    #
    # Measured on a real deployment rather than reasoned about: two reconciles
    # 72 seconds apart each owed `conclude` for one attempt and each deferred
    # it with this function's own precondition.
    #
    # WHY RESUMING THE RECEIPT RATHER THAN ADMITTING `sealed`. Letting a sealed
    # output through `_collectable` would carry a SECOND, possibly different
    # collection into the custody comparison, which is the opposite of taking
    # custody once. `intake_operation` derives its identity from the attempt
    # row alone -- no adapter bytes -- so the committed answer can be found
    # without collecting anything again, and what is returned is the journal's
    # own byte-stable result rather than a recomputed one.
    #
    # NARROW ON PURPOSE. Only a COMMITTED record replays. An absent one, and a
    # refused one, fall through to exactly the behaviour they have today: this
    # corrects a re-entry that could not finish, and decides nothing else.
    settled = _settled_intake(store, attempt)
    if settled is not None:
        return settled
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


def _settled_intake(store, attempt):
    """This attempt's ALREADY COMMITTED intake receipt, or nothing.

    W197661. The identity is `intake_operation`'s -- derived from the attempt
    row, so it names THE ACT rather than any particular collection's bytes, and
    it can be asked for without calling an adapter.

    NO SIGNATURE COMPARISON HERE, AND THAT IS NOT A WEAKENING. `store.replay`
    compares the signature because a CALLER supplies the identity there, and a
    reused id must not replay somebody else's outcome. This identity is not
    supplied: it is derived from the persisted attempt, and the signature it
    would be compared against is over the collected bytes -- which is precisely
    what this path exists to avoid asking the adapter for a second time. The
    `kind` is still compared, because that is a fact about the row rather than
    about today's operands.

    ONLY `committed`. A refused record must keep raising through the ordinary
    path, and an absent one is an ordinary first entry; answering either from
    here would be inventing an outcome.
    """
    row = store.operation_record(intake_operation(attempt)["operation_id"])
    if row is None or row["state"] != "committed" \
            or row["kind"] != "intake.record":
        return None
    # BYTE-STABLE, from the journal. `store.replay` returns the recorded JSON
    # rather than recomputing it, for the reason this needs too: the receipt an
    # ending resumes has to be the receipt it recorded, member for member.
    if row["result"] is None:
        return None
    return json.loads(row["result"])


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


def _resource_cessation(store, settled, attempt, attempt_id):
    """The cessation a COMMITTED cleanup actually proves, or `None`.

    W275774 review 16:05:19Z: "document shape alone is not runtime/writer/effect
    proof." So this composes nothing optimistic and defaults nothing. It reads the
    cleanup record this manager committed and answers only when that record carries
    both halves of the proof a resource return needs:

      * `state == "absent"` is the POSITIVE observation that the exact runtime is
        gone -- the same fact `_absence_proof` requires before a gate discharge, and
        the reason a `failed` cleanup (runtime survived its destroy) proves nothing.
      * `directory_custody` is non-`None` EXACTLY when that absence was followed by
        normalization under this manager's own custody of each governed root, which
        `_committed_custody` has already matched against the normalization owner's
        record. That is what justifies reporting NO SURVIVING WRITER: the roots are
        held by this manager, not merely believed quiet.

    Anything short of both answers `None`, and the caller returns nothing -- which
    leaves the resource held, the honest state for an unproven cessation.
    """
    # W285465: EITHER ACCOUNT, and neither is assumed. `directory_custody` is the
    # normalized ending's; `writer_cessation` is the no-helper ending's -- a committed
    # record of an absent exact runtime, output this manager can read and an adapter-
    # established empty writer list, which `_adopted_writer_cessation` has already
    # compared against the journal before the ending could commit. Absence of BOTH is
    # still `None`, and the resource stays held.
    if settled.get("state") != "absent":
        return None
    if settled.get("directory_custody") is None:
        if settled.get("operation") is None:
            return None
        if _writer_cessation_of(store, settled) is None:
            return None
    if attempt["runtime_id"] is None:
        return None
    return {"container": attempt["runtime_id"], "stopped": True, "helpers": []}


def _established_cessation(store, attempt, operation):
    """The cessation THIS ending established, composed from its own committed record.

    W285465. The RESOURCE RETURN's evidence, derived from the committed establishment rather
    than assembled from hope: the container the attempt row names, `stopped` because the
    destroy observed that exact identity ABSENT, and an empty writer list because the
    committed record says the adapter's listing found none.

    NOT THE ADMISSION'S EVIDENCE ANY MORE. Review 2026-09-28T07-26-54Z: passing this to
    `admit_cleanup` made a caller-shaped document the authority for an ownership transfer,
    and `workspaces._ceased_generation` now reads the committed record itself. `tokens`
    performs its own validation of what this returns, against what it bound.
    """
    ceased = historical_writer_cessation(store, operation)
    if ceased is None or ceased["helpers"] != [] or ceased["state"] != "absent":
        return None
    if ceased["attempt_id"] != attempt["runtime_attempt_id"] \
            or ceased["container"] != attempt["runtime_id"]:
        return None
    return {"container": attempt["runtime_id"], "stopped": True, "helpers": []}


def _released(store, govern, attempt, attempt_id, settled):
    """Return the governed resource IF this ending proved its cessation."""
    if govern is None:
        return
    cessation = _resource_cessation(store, settled, attempt, attempt_id)
    if cessation is None:
        return
    # AFTER THE ENDING IS COMMITTED, for the reason review 15:55:27Z gave about the
    # finalization: an ending that refuses must not have released anything. The
    # return is idempotent and bound to the execution and operation that reserved
    # the generation, so a replay of this ending returns the same generation rather
    # than nothing or somebody else's.
    # `reclaiming=True` HERE TOO, and the name means "a manager settlement on
    # confirmed cessation" rather than anything about sweeps. What the token refuses
    # without it is a STALE HOLDER declaring its own resource free after expiry. This
    # is the other thing entirely: the ending holds a positive absence observation
    # and this manager's own committed custody of the roots, which is the strongest
    # evidence in the system. Refusing it would mean a revoked generation could never
    # be settled by the very act that proves it free.
    govern.release(store, attempt,
                   operation=attempts._start_operation_id(attempt),
                   cessation=cessation, reclaiming=True)


def authorize_cleanup(store, port, adapter, *, attempt_id,
                      retention_policy_digest, govern=None):
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
        # W275774: THE REPLAY RETURNS THE RESOURCE TOO, and my own case caught this
        # gap. The ending is journalled, so a repeat of it comes back HERE and never
        # reaches the release below -- which means a return that failed after the
        # ending had already committed could never be recovered by running the
        # ending again. That is precisely the case review 16:05:19Z asked for. The
        # release is idempotent and bound to the execution and operation that
        # reserved the generation, so replaying it is safe and converging.
        _released(store, govern, attempt, attempt_id, already)
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
    # EVERY CAPABILITY THIS ENDING WILL USE, PROVED HERE -- before the destroy, which is
    # the first mutation, and AFTER this entry's own operands. Both halves matter: W43975's
    # [P0] requires the seam ahead of any mutation, and the boundary catalogue's accepted
    # rule is that an entry validates its own operands first, or a probe for a bad operand
    # refuses for somebody else's reason. Measured: asking at the top took the inventory
    # from 26 pending entries to 30 failures plus an error, with operand probes catching
    # this capability refusal instead of their own.
    _ending_capable(adapter, attempt_id)
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
    # W285465, OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 with DESIGN HOST-5: THE WRITER
    # CESSATION IS ESTABLISHED AND COMMITTED HERE, IN PLACE OF NORMALIZING.
    #
    # This called `_normalized`, which runs a custody helper per root and leaves the
    # receipts the ending read back as `directory_custody`. The owner's ruling removes the
    # helper from this path, so the evidence changes and the DISCIPLINE does not: it is
    # established from observations (the exact runtime absent, the output readable by the
    # configured group, the adapter's own writer listing empty), it is COMMITTED as its own
    # journalled operation bound to this destroy's identity, and the ending reads it back
    # out of the journal instead of trusting what this frame is holding.
    #
    # BEFORE ANYTHING TERMINAL AND BEFORE THE REMOVAL, which is the ordering owner 270664
    # fixed and this preserves: a refusal here leaves cleanup `pending`, the roots present
    # and the bytes untouched, which is the honest state for an ending nobody proved. An
    # inaccessible output refuses for exactly that reason -- it is an ERROR that PRESERVES
    # the workspace, never a licence to change permissions or delete.
    #
    # AND NO HELPER RUNS HERE AT ALL, WHATEVER IS CONFIGURED. Review 2026-09-28T06-23-25Z
    # corrected my reading: OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 requires ZERO
    # automatic launches on this completion path, not merely that a missing custodian stop
    # being fatal. A configured capability is not permission to use it automatically, so the
    # branch on `_can_normalize` is GONE rather than left as a preference -- a deployment
    # that has a custodian takes exactly the same evidenced route, and the historical
    # receipts of acts already performed are preserved and still readable.
    if observed["state"] == "absent":
        _record_writer_cessation(store, adapter, attempt_id, attempt=attempt,
                                 operation=operation, observed=observed)
    # W270664 F2: THE REMOVAL HAPPENS HERE, OUTSIDE THE ENDING'S TRANSACTION.
    #
    # Owner 270664 selects the enclosing cleanup entry as well as the standalone one, and this
    # is that correction: `_settle` used to call `discard_execution_roots` from INSIDE the
    # `runtime.destroy` transaction, so a tree walk, permission changes and every `unlink` ran
    # with this manager's write lock held and blocked every unrelated write for the duration.
    #
    # THE ORDER THE REVIEWS REQUIRE IS PRESERVED: it is after the eligibility this function has
    # already proved -- the ending is real, the receipt is the attempt's, both roots are
    # normalized -- and BEFORE the ending is committed, so the lane is still held while the
    # deletion happens and nothing is released on a half-removed tree. The removal takes its own
    # ownership record, so a removal INTERRUPTED here stays unresolved and is held. THE LIMIT,
    # corrected per review 2026-09-26T08:33:54Z: a removal that COMPLETED settles its ownership,
    # so a crash after it and before this commit is held by NOTHING -- the ending retries, finds
    # the home absent and commits. That retry gap is real, it is not covered by the ownership
    # record, and no case of mine observes it yet.
    #
    # W270664 F2, review 2026-09-26T08:43:12Z: THE STORE IS MEASURED HERE TOO, once,
    # and the ending below signs its receipts under that measurement instead of
    # re-taking it under its own write lock. `None` on the surviving-runtime path is
    # correct and not a gap: that ending claims no directory act, so it reads no
    # receipt and needs no store -- it returns before `_adopted_custody`.
    prepared_store = None
    admitted_cleanup = None
    # W285465 under the owner supersession at 294568/294616: THE WORKSPACE IS PRESERVED AS IS,
    # ALWAYS.
    #
    # My previous cut preserved only material it had found unreadable, which was still the
    # earlier target: it walked the roots, and it DELETED the ones it could read. The selected
    # completion performs no output observation and no removal at all -- confirmed termination,
    # durable execution status, workspace preserved, execution gate released. So this path takes
    # NO cleanup admission and calls NO `discard_execution_roots`, and the ending settles
    # `retained`, which is what this axis calls material kept on purpose.
    #
    # THE STANDALONE CLEANUP MACHINERY IS UNTOUCHED: `admit_cleanup`,
    # `discard_execution_roots` and their ownership rules remain for the acts that actually
    # select them. What is removed is the AUTOMATIC removal from completion.
    # W285465 under the owner supersession at 294568/294616, and review 2026-09-28T10-23-30Z
    # asked for the disabled block to go rather than sit here as scaffolding: COMPLETION
    # REMOVES NOTHING AND ADMITS NOTHING. The workspace is preserved as is, the ending settles
    # `retained`, and `prepared_store`/`admitted_cleanup` stay `None` because no directory act
    # is performed to measure a store for or to own. The standalone cleanup machinery --
    # `admit_cleanup`, `discard_execution_roots` and their ownership rules -- is untouched for
    # the acts that actually select it.
    preserved = True
    settled = store.transact(
        operation["operation_id"], "runtime.destroy", signature,
        lambda connection: _settle(store, connection, attempt_id, receipt,
                                   retention_policy_digest, observed,
                                   operation, custody=adapter,
                                   prepared_store=prepared_store,
                                   admitted_cleanup=admitted_cleanup,
                                   preserved=preserved))
    # W275774: AND THE GOVERNED RESOURCE GOES BACK, if this cleanup proved it free.
    _released(store, govern, attempt, attempt_id, settled)
    return settled


# W119548: THE ACT THAT DISCHARGES THE GATE A FENCE INSTALLED.
#
# The kind is its own, deliberately distinct from `runtime.destroy`. Cleanup
# and this discharge are two acts with two identities: cleanup is local and
# settles a manager axis, this one is remote and settles a Work's scheduler phase, and
# they cannot be one database transaction because one of them is not in this
# database at all.
GATE_DISCHARGE_KIND = "authority.discharge-quiescence"

# The gate this act discharges, and the evidence kind the Authority takes for
# it. Spelled here rather than imported: `baton_v12.authority` is a sibling
# package and this manager's import boundary is exactly where its own cases say it is
# -- the same rule that keeps the claim-signature derivation injected rather
# than imported. `test_secrets`' surface catalog holds the two spellings together.
QUIESCENCE_GATE = "runtime-quiescence"
RUNTIME_ABSENT = "runtime-absent"

# The cleanup endings that FOLLOWED a positive absence observation. `failed` is
# deliberately absent: it is the settled ending of a cleanup whose runtime
# SURVIVED its own destroy, so it is evidence against absence rather than for
# it.
_ABSENT_ENDINGS = ("complete", "retained")

# EXACTLY WHAT A DISCHARGE RECEIPT CARRIES, and every public exit is held to
# it.
# Review 2026-09-08T14:27:00Z [P1]: the journalled value was returned as
# whatever decoded, so a row saying a different gate kind or a non-discharged
# phase was reported to consumer recovery as a completed discharge.
GATE_DISCHARGE_RECEIPT = ("attempt_id", "assignment", "gate", "kind", "phase",
                          "runtime_id", "cleanup", "cleanup_operation_id",
                          "operation_id")


def _discharge_operation_id(attempt):
    """This attempt's ONE discharge identity, derived and never minted.

    Over the attempt and its FIXED assignment alone, and not over the cleanup
    proof that authorizes it. That is what makes the replay below reachable
    from the attempt id by itself: a manager resuming after a crash re-derives
    this without having to re-establish the evidence first, and a discharge already
    committed replays even if the durable records it was derived from can no
    longer be read.
    """
    # §13 AT THE CONSTRUCTOR, exactly as `destroy_operation` does it and for
    # the same reason: an operation identity is PORTABLE, and a guard that runs
    # at the eventual write runs after the caller already holds the leak.
    check_no_durable_secret(
        {"kind": GATE_DISCHARGE_KIND,
         "operands": {"attempt_id": attempt["runtime_attempt_id"],
                      "expect": _fixed_assignment(attempt)}},
        what="an operation signature")
    return GATE_DISCHARGE_KIND + ":" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt)})[len("sha256:"):]


def _quiescence_gate_token(expect):
    """The exact token the authority's fence installed for this generation.

    DERIVED FROM THE ATTEMPT'S OWN FIXED ASSIGNMENT, so an attempt can only
    ever compose the token for the generation it was fenced at. The authority
    then compares it for equality against the gate actually holding the Work, and
    refuses if they differ -- which is what stops an old attempt's evidence
    from clearing a newer gate, decided by the owner of that fact rather than
    by a comparison this manager composed against state it read a moment ago.
    """
    return f"{QUIESCENCE_GATE}:{expect['generation']}"


def gate_discharge_of(store, attempt_id):
    """The committed discharge for this attempt, or absence.

    THE DISCOVERABILITY HALF, and it is a read. `authorize_cleanup` commits its
    terminal axis and its receipt together, so by the time a discharge is owed
    the cleanup axis is already terminal -- and a consumer that decided what an
    attempt still owes from that axis alone would see nothing outstanding. This
    answers the other question directly: has the discharge itself committed.

    WHAT IT DOES NOT DO is decide whether one is owed. That depends on whether
    the Work is gated at all, which is the authority's fact and not this
    store's; a deployment that has cleaned up and holds no committed discharge
    asks for one, and `discharge_quiescence_gate` is where every condition is
    proved.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _fixed_assignment(attempt)
    if expect is None:
        return None
    # ABSENCE AND A PRESENT INVALID RECORD ARE DIFFERENT ANSWERS, and the
    # difference is the whole point of this read. `_recorded_discharge` decides
    # it once for both exits: only a genuinely absent operation answers `None`,
    # and every present record is held to the same contract the replay exit
    # holds it to.
    operation_id = _discharge_operation_id(attempt)
    held = _recorded_discharge(store, attempt_id, operation_id)
    if held is None:
        return None
    record, committed = held
    return _adopted_discharge(
        committed,
        f"attempt {name_value(attempt_id)}'s committed gate discharge",
        operation_id=operation_id, signature=record["signature"],
        expect=expect, attempt_id=attempt_id)


def discharge_quiescence_gate(store, port, *, attempt_id,
                              retention_policy_digest):
    """Carry this manager's committed absence proof to the authority's gate.

    W119548. THE MISSING HALF OF THE ORDINARY ENDING. `freeze_checkpoint` and
    `request_cancellation` fence the assignment, and the authority installs
    `runtime-quiescence:<generation>` in the same transaction -- deliberately,
    because ending an assignment is not evidence that the container is gone.
    Only a positive observation of the exact runtime is, and this manager makes
    exactly that observation inside `authorize_cleanup`. Nothing carried it
    across, so the Work stayed blocked with every local ending settled and no
    accepted act able to move it.

    THE CALLER SELECTS AND SUPPLIES NOTHING ELSE. Its two operands are the
    attempt and the retention policy identity, and the second is here only
    because it is half of the key that selects the exact cleanup proof. The
    authority, the Work, the participant, the generation, the gate token, the
    runtime identity and the absence evidence are all DERIVED from durable
    records this manager owns. A caller cannot name an absence, a runtime, a
    gate or an assignment, which is the whole reason this is a manager act
    rather than a deployment composing a `satisfy_gate` call of its own.

    THE PROOF IS THE COMMITTED CLEANUP, NOT THE AXIS. `execution_runtime =
    destroyed` is a mutable column; the evidence is the `runtime.destroy`
    operation this manager COMMITTED, replayed through `_committed`, whose
    result records the observed state and the ending it settled. A store edit
    can move the axis and cannot forge the journalled answer. `failed` is not
    among the endings this accepts: it is the settled ending of a cleanup whose
    runtime survived its own destroy, which is evidence against absence.

    THE ORDER, and each step is the next one's precondition:

      1. own the two operands, read the attempt, require its fixed assignment
         and prove this session acts for that assignment's participant;
      2. REPLAY an already committed discharge and return it, before anything
         mutable is read. A remote commit whose local receipt was lost must
         reproduce its answer even after the Work has moved on, and a check of
         today's gate before recognising that replay would strand successful
         work;
      3. prove the committed cleanup and the exact runtime it observed absent;
      4. ask the authority, whose own equality check on the gate token is what
         refuses an old generation's evidence against a newer gate; and
      5. journal the answer under this act's own identity.

    FOUR AND FIVE CANNOT BE ONE TRANSACTION, and pretending otherwise is the
    trap this design is written around. The remote act commits first and the
    local receipt second; a crash between them leaves the authority's own
    replay to make the next attempt idempotent, which is exactly what step two
    then records. Putting the remote call inside a local transaction would hold
    a write lock across a network act, and putting the journal first would
    record an act that may never have happened.

    IT DECIDES NOTHING ELSE. No finalization, no acceptance, no disposal, no
    replacement work, no certified-isolation shortcut and no new authority
    policy. W61984's distinction stands untouched: stopping and finalizing are
    not absence, and this act is reached only where absence was positively
    observed.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    boundaries.capability(getattr(port, "satisfy_gate", None),
                          "the authority session's gate discharge")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)

    # STEP TWO, AND ITS POSITION IS THE CONTRACT. Read by identity through the
    # journal's OWN recorded signature rather than through a freshly derived
    # one: a discharge that committed is replayable from the attempt id alone,
    # so it survives a later edit to the records the first call derived it
    # from.
    operation_id = _discharge_operation_id(attempt)
    held = _recorded_discharge(store, attempt_id, operation_id)
    if held is not None:
        record, committed = held
        return _adopted_discharge(
            committed,
            f"attempt {name_value(attempt_id)}'s replayed gate discharge",
            operation_id=operation_id, signature=record["signature"],
            expect=expect, attempt_id=attempt_id)

    settled = _absence_proof(store, attempt, attempt_id,
                             retention_policy_digest)
    # THE RUNTIME THE EVIDENCE NAMES, and it is the attempt's own attached
    # identity rather than anything a caller or the settlement document
    # offered.
    # `_settle` cannot reach a positive absence for an attempt with no runtime,
    # so this is a real correlation and not a formality -- and the authority
    # will not take an absence claim that names nothing.
    runtime_id = boundaries.identity(
        attempt["runtime_id"],
        f"attempt {name_value(attempt_id)}'s attached runtime identity")
    gate = _quiescence_gate_token(expect)
    evidence = {"kind": RUNTIME_ABSENT, "runtime": runtime_id}
    signature = manager_signature(GATE_DISCHARGE_KIND, {
        "attempt_id": attempt_id, "expect": expect, "gate": gate,
        "runtime_id": runtime_id,
        "cleanup_operation_id": settled["operation"]["operation_id"]})
    # THE WHOLE WORK REFERENCE IS PROVED BEFORE THE REMOTE ACT, not just the
    # participant. Review 2026-09-08T14:27:00Z [P2]: `_require_participant`
    # compares one name, and `satisfy_gate` crosses with a Work id and no
    # authority, so a session bound to ANOTHER authority that happens to act
    # for the same participant discharged this attempt's gate. A four-part
    # assignment is not three quarters of one, and this crossing was reading
    # one quarter of it.
    #
    # THROUGH THE PORT'S OWN PROJECTION, which is already a required member and
    # already owns its `authority_uuid` as durable identity. No new session
    # capability is needed for this and none is taken.
    #
    # AFTER THE COMMITTED REPLAY ABOVE, deliberately. This is a mutable remote
    # read, and a discharge that already committed must reproduce its answer
    # without one -- so nothing here can strand a remote act whose local
    # receipt was lost.
    _same_authority(port, expect, attempt_id)
    answered = port.satisfy_gate(expect["work_ref"]["work_id"], operation_id,
                                 gate, evidence)
    # The Authority answers with the evidence kind. The port already checks
    # the requested gate token and discharged phase; this act additionally
    # requires the positive runtime absence it supplied.
    if answered["kind"] != RUNTIME_ABSENT:
        raise ContractRefusal(
            "integrity", "schema",
            f"the authority answered evidence kind {name_value(answered['kind'])} "
            f"for attempt {name_value(attempt_id)} and this act requires "
            f"{name_value(RUNTIME_ABSENT)}")
    # THE ANSWER IS COMPOSED HERE RATHER THAN THROUGH `documents`, and that is
    # a scope statement rather than a style one. Every other receipt in this
    # module is built by a registered `documents` contract; registering a new
    # one means editing `worker_manager/documents.py`, which this Work's
    # approved six paths do not include and which its finding says needs its
    # own scope decision before being touched. So the shape is composed and
    # owned here, and moving it into the registry is a bounded follow-up
    # rather than an edit taken on the way past.
    #
    # NOTHING IS LOST BY WAITING. `store.transact` journals this value as JSON
    # and `replay` answers `json.loads`, so what a later replay can ever return
    # is a plain document either way -- the registry would add validation,
    # not a different type.
    #
    # WHAT IS JOURNALLED IS WHAT THE AUTHORITY ANSWERED. Review [P1]: this used
    # to write its own REQUESTED gate over the reply, so an answer about
    # another gate became a durable receipt for this one. The port now proves
    # the two are equal, and this records the answer rather than the request --
    # so the receipt says what happened rather than what was asked for.
    return store.transact(
        operation_id, GATE_DISCHARGE_KIND, signature,
        lambda connection: _adopted_discharge(_composed_receipt({
            "attempt_id": attempt_id,
            "assignment": expect,
            "gate": answered["gate"],
            "kind": answered["kind"],
            "phase": answered["phase"],
            "runtime_id": runtime_id,
            "cleanup": settled["cleanup"],
            "cleanup_operation_id": settled["operation"]["operation_id"],
            "operation_id": operation_id,
        }), "a gate discharge receipt", operation_id=operation_id,
            signature=signature, expect=expect, attempt_id=attempt_id))


def _same_authority(port, expect, attempt_id):
    """The session's own Work projection names THIS attempt's authority."""
    work_ref = expect["work_ref"]
    projected = port.project_work(work_ref["work_id"])
    if projected is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"this session projects no Work "
            f"{name_value(work_ref['work_id'])}, "
            f"so it cannot be the authority attempt {name_value(attempt_id)} "
            f"was fixed to")
    if projected["authority_uuid"] != work_ref["authority_uuid"]:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for authority "
            f"{name_value(projected['authority_uuid'])} and attempt "
            f"{name_value(attempt_id)} is fixed to "
            f"{name_value(work_ref['authority_uuid'])}; a matching "
            f"participant "
            f"on another authority is a different assignment, not this one")


def _composed_receipt(members):
    """The receipt this act is about to journal, as an owned document.

    A separate name so the composing exit reads the same as the two reading
    ones: what is written is held to exactly the contract what is read is held
    to, rather than being trusted because this process just built it.
    """
    return own(members, what="a gate discharge receipt")


def _recorded_discharge(store, attempt_id, operation_id):
    """The journal's committed discharge for one identity, or ABSENCE.

    ONE READER FOR BOTH PUBLIC EXITS, and that is the correction rather than a
    tidy-up. Review 2026-09-08T14:53:10Z [P2]: discovery and replay had each
    written their own version of this, and they disagreed -- the replay exit
    refused a present record of the wrong kind and a present record whose
    decoded result is null, while discovery returned `None` for both. Two
    spellings of one question are two answers to it, so there is one spelling.

    ABSENCE IS THE ONLY `None`. "No discharge is recorded" is what a consumer
    acts on: it means the act is still outstanding and may be performed. "A
    discharge IS recorded and this manager cannot own it" is an integrity
    failure an operator has to look at, and reporting the second as the first
    would invite a consumer to re-run a remote act on the strength of a record
    it could not read.
    """
    record = store.operation_record(operation_id)
    if record is None:
        return None
    if record["kind"] != GATE_DISCHARGE_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names discharge operation "
            f"{name_value(operation_id)}, which this manager committed as "
            f"{name_value(record['kind'])}")
    _, committed = store.replay(operation_id, record["signature"],
                                kind=GATE_DISCHARGE_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names discharge operation "
            f"{name_value(operation_id)}, which this manager committed "
            f"with no recorded answer to replay")
    return record, committed


def _receipt_signature(taken):
    """The signature a discharge receipt's own operands compose.

    THE SAME FIVE OPERANDS `discharge_quiescence_gate` SIGNED, recomposed from
    the receipt rather than from anything read fresh. Comparing this against
    the journal's recorded signature is what binds the attempt, the fixed
    assignment, the gate, the runtime and the cleanup operation TOGETHER -- one
    comparison for a relationship that five separate field checks cannot state.
    """
    return manager_signature(GATE_DISCHARGE_KIND, {
        "attempt_id": taken["attempt_id"], "expect": taken["assignment"],
        "gate": taken["gate"], "runtime_id": taken["runtime_id"],
        "cleanup_operation_id": taken["cleanup_operation_id"]})


def _adopted_discharge(value, what, *, operation_id=None, signature=None,
                       expect=None, attempt_id=None):
    """One gate-discharge receipt, owned with its VALUES and its RELATIONSHIPS.

    BOTH PUBLIC EXITS COME THROUGH HERE -- the replay short-circuit and
    `gate_discharge_of`. Review 2026-09-08T14:27:00Z [P1]: a journalled receipt
    was handed back as whatever `json.loads` produced, so a row carrying a
    foreign kind or a non-discharged phase was reported as a completed
    discharge to exactly the consumer recovery that depends on it. Generic parsing
    establishes that bytes decode; it establishes nothing about what they say.

    AND REVIEW 2026-09-08T14:43:50Z [P2] IS THE OTHER HALF OF THAT SENTENCE.
    Checking each field individually proved every member well-formed and proved
    nothing about WHOSE receipt it is: a row naming another attempt, another
    gate, another operation or another runtime was still returned as this
    attempt's completion, and a null assignment faulted as a raw `TypeError`
    inside a keyword unpack rather than refusing. This reader is the consumer's
    proof that its selected attempt owes no discharge, so a typed receipt about
    something else is exactly the answer it must not give.

    THE JOURNAL ALREADY HELD THE BINDING. `discharge_quiescence_gate` signs the
    attempt, the fixed assignment, the gate, the runtime and the cleanup
    operation into one `manager_signature`, and the store recorded it. So the
    receipt's own operands are RECOMPOSED and compared against that recorded
    signature -- one comparison that binds all five, rather than five checks
    that bind none to each other. On top of it the receipt is bound to the
    SELECTION: the operation identity that was looked up, and the selected
    attempt's own immutable fixed assignment.

    NOTHING MUTABLE IS CONSULTED. Not today's runtime row, not the cleanup row,
    not the remote gate or phase. The receipt is durable evidence of what
    happened, and a correct one therefore still replays after the Work has been
    claimed and fenced again -- which is the distinction the preceding review
    accepted and this must not quietly undo.

    IT IS COMPOSED HERE RATHER THAN REGISTERED IN `documents.py` because that
    path is outside this Work's approved six and its finding says an additional
    one is a scope decision before editing. The review's ruling is explicit
    that being out of scope does not waive the contract -- so the contract is
    here, and moving it into the registry stays a bounded follow-up.
    """
    taken = boundaries.document(value, what, required=GATE_DISCHARGE_RECEIPT)
    boundaries.identity(taken["attempt_id"], f"{what}'s attempt")
    boundaries.identity(taken["operation_id"], f"{what}'s operation identity")
    boundaries.identity(taken["cleanup_operation_id"],
                        f"{what}'s cleanup operation identity")
    boundaries.identity(taken["runtime_id"], f"{what}'s runtime identity")
    boundaries.text(taken["gate"], f"{what}'s gate")
    if taken["kind"] != RUNTIME_ABSENT:
        _refuse_receipt(what, "kind", taken["kind"], RUNTIME_ABSENT)
    if taken["phase"] != GATE_DISCHARGED_PHASE:
        _refuse_receipt(what, "phase", taken["phase"], GATE_DISCHARGED_PHASE)
    if taken["cleanup"] not in _ABSENT_ENDINGS:
        _refuse_receipt(what, "cleanup ending", taken["cleanup"],
                        " or ".join(_ABSENT_ENDINGS))
    # THE NESTED ASSIGNMENT IS OWNED BEFORE IT IS UNPACKED.
    # `documents.assignment` takes keywords, and `**None` is a `TypeError`
    # rather than a refusal -- a raw exception at a persisted-input boundary
    # bypasses the portable refusal and retry path every other reader uses.
    assignment = boundaries.document(
        taken["assignment"], f"{what}'s assignment",
        required=("work_ref", "participant", "generation"))
    work_ref = boundaries.document(
        assignment["work_ref"], f"{what}'s Work reference",
        required=("authority_uuid", "work_id"))
    documents.assignment(work_ref=documents.work_ref(**work_ref),
                         participant=assignment["participant"],
                         generation=assignment["generation"])
    # THE GATE IS DERIVED FROM THE RECEIPT'S OWN ASSIGNMENT rather than
    # believed. A generation-1 assignment carrying gate 99 is not a document
    # about one discharge, however well formed each half is on its own.
    derived = _quiescence_gate_token(assignment)
    if taken["gate"] != derived:
        _refuse_receipt(what, "gate", taken["gate"], derived)
    # AND THE RECEIPT IS THE ONE THAT WAS SELECTED. Absence is a different
    # answer and is decided by the callers; what is refused here is a receipt
    # that is PRESENT and about something else.
    if operation_id is not None and taken["operation_id"] != operation_id:
        _refuse_receipt(what, "operation identity", taken["operation_id"],
                        operation_id)
    if attempt_id is not None and taken["attempt_id"] != attempt_id:
        _refuse_receipt(what, "attempt", taken["attempt_id"], attempt_id)
    if expect is not None and assignment != expect:
        _refuse_receipt(what, "assignment", assignment, expect)
    # THE ONE COMPARISON THAT BINDS THE FIVE SIGNED OPERANDS TOGETHER.
    if signature is not None and _receipt_signature(taken) != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} composes a signature its own operands do not match the "
            f"one this manager committed for "
            f"{name_value(taken['operation_id'])}; the attempt, the "
            f"assignment, the gate, the runtime and the cleanup operation are "
            f"ONE signed relationship, and a receipt whose members were "
            f"changed individually cannot reproduce it")
    return taken


def _refuse_receipt(what, member, found, expected):
    raise ContractRefusal(
        "integrity", "schema",
        f"{what} records {member} {name_value(found)} and a discharge this "
        f"manager committed records {name_value(expected)}; a receipt that "
        f"does not say a quiescence gate was released is not evidence that "
        f"one was")


# W120762: EXACTLY WHAT AN ORDINARY CLEANUP RECEIPT CARRIES, and the closed set
# of endings one can settle at. `kind` is optional because the recordless
# family's settlement carries one and this family's does not; nothing here
# reads it, and naming it keeps an adopted document from refusing on a member
# a sibling ending legitimately writes.
CLEANUP_RECEIPT = ("attempt_id", "cleanup", "state", "why", "kept",
                   "operation", "directory_custody")

# W285465: `writer_cessation` is the NO-HELPER ending's evidence member, and it is its own
# member rather than a value smuggled into `directory_custody` -- the owner's ruling
# forbids a fabricated custody receipt, and a reader that could not tell the two apart
# could not enforce that. OPTIONAL rather than required, and the distinction is real: every
# ending written before this member existed, and every ending whose runtime SURVIVED, has
# no cessation to record, and absent is how those documents say so. A reader that demanded
# it would refuse accepted receipts it has no quarrel with.
CLEANUP_EVIDENCE = ("writer_cessation",)
CLEANUP_ENDINGS = _ABSENT_ENDINGS + ("failed",)

# The two directory roots a positive absence normalizes, innermost first, as
# `_normalized` performs them.
_CUSTODY_ROOTS = ("result", "workspace")

# ONE VOCABULARY, ASSERTED RATHER THAN COPIED. The cleanup axis is
# `attempts.TRANSITIONS`' to define, and a set spelled here that drifted from
# it would let this reader accept an ending the axis cannot hold -- or refuse
# one it can.
assert frozenset(CLEANUP_ENDINGS) == frozenset(
    state for state, after in attempts.TRANSITIONS["cleanup"].items()
    if not after)


def cleanup_of(store, *, attempt_id, retention_policy_digest):
    """The committed ORDINARY cleanup for this attempt and policy, or absence.

    W120762, `work/records/2026/09/finding-v12-committed-cleanup-reader/`.

    WHY A READER EXISTS AT ALL. A consumer recovering a composed ending has to
    know whether this manager finished with the runtime, and the only two ways
    to ask were both wrong. The mutable `cleanup` column says what an axis was
    set to and not what act set it, so an edit reaches it. `authorize_cleanup`
    knows the truth and is a SERVING act: when it finds no committed destroy to
    replay it goes on to read the live assignment from the Authority, which a
    recovery path may not do. So a consumer either believed a column or spent
    an Authority read to find out that there was nothing to find.

    THIS IS THE READ HALF OF THAT ACT, and it is exactly `gate_discharge_of`'s
    shape one family over: absence and a present invalid record are different
    answers, and only a genuinely missing operation answers `None`. It opens no
    session, takes no port and no adapter, calls nothing external and writes
    nothing -- there is no branch in it that could.

    ABSENCE IS THREE THINGS AND THEY ARE ALL HONEST. An attempt with no fixed
    assignment cannot have a destroy identity; an attempt with no intake
    receipt has half that identity missing, which is precisely what
    `blocked-on-intake` is a STATE for; and an identity this manager never
    committed is simply a cleanup that has not happened. None of the three is a
    fault and none of them is evidence of a cleanup, so each answers `None`
    rather than refusing -- and a caller that needs one is refusing on its own
    behalf, with its own words.

    THE POLICY IS AN OPERAND BECAUSE THE IDENTITY IS. `destroy_operation` binds
    the intake receipt digest and the retention policy digest into the act, so
    an attempt does not have "a" cleanup: it has one per policy it was
    authorized under, and a caller naming another policy is asking about an act
    this manager never committed rather than about this one.

    WHAT IS OWNED BEFORE ANYTHING IS RETURNED, and each is a relationship
    rather than a shape:

      1. the record is `runtime.destroy` and replays under its OWN journalled
         signature, so a row edited away from the answer it committed refuses
         as an integrity fault rather than as a caller's collision;
      2. the receipt's whole document contract, its attempt, and its ending
         inside the closed set the axis can hold;
      3. the committed operation compared WHOLE against one derived from the
         current rows -- `operation_id` binds the attempt, the assignment, the
         receipt and the policy, and `signature_digest` binds the runtime, so
         comparing one and dropping the other lets an edited runtime keep a
         real cleanup's evidence. `_absence_proof` learned that at review
         2026-09-08T14:27:00Z and this reader is held to it;
      4. `kept` against the retention decisions this store actually holds --
         and against `KEEPS_MATERIAL`, not against every decision. A discarded
         artifact is decided and NOT kept, so comparing against all of them
         reports an honest discard as a store that disagrees with itself; and
      5. the nested directory custody, which is where the family this reader
         serves was accepting nothing at all. A positive absence normalizes
         both roots and its receipt says so, so both are required and each is
         compared against the normalization owner's own committed record; a
         cleanup that settled `failed` performed no directory act and must
         carry none.

    IT DECIDES NOTHING WITH WHAT IT FINDS. Whether a `failed` ending, a
    surviving runtime or a discarded result is acceptable belongs to whoever
    asked; this answers what committed and refuses what it cannot own.

    THE OTHER CLEANUP FAMILIES ARE NOT COVERED. A failed start, a refused
    session and an abandonment each end through their own operation kind, and
    this reads `runtime.destroy` by name so none of them is admitted here by
    accident.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    attempt = _attempt_of(store._connection, attempt_id)
    if _fixed_assignment(attempt) is None:
        return None
    receipt = intake_receipt_of(store, attempt_id)
    if receipt is None:
        return None
    operation = destroy_operation(attempt, receipt["receipt_digest"],
                                  retention_policy_digest)
    record = store.operation_record(operation["operation_id"])
    if record is None:
        return None
    what = f"attempt {name_value(attempt_id)}'s committed cleanup"
    # THE JOURNAL'S OWN SIGNATURE, DERIVED AND COMPARED. Review
    # 2026-09-08T16-43-59Z [P1]: `_committed` replays under the signature the
    # ROW carries -- deliberately, because `intake.record` is signed over an
    # adapter's collection that the persisted rows do not preserve -- so a row
    # whose signature column was replaced with `{}` still replayed and this
    # reader still answered. The comparison that was missing is this one, and
    # it is NOT `destroy_operation`'s `signature_digest`: that digest covers
    # the operation id as well and is the adapter-facing half. These are the
    # exact operands `authorize_cleanup` signs, so a record signed over
    # anything else is not the act it claims to be.
    signature = manager_signature(
        "runtime.destroy",
        {"attempt_id": attempt_id, "expect": _fixed_assignment(attempt),
         "runtime_id": attempt["runtime_id"],
         "intake_receipt_digest": receipt["receipt_digest"],
         "retention_policy_digest": retention_policy_digest})
    if record["signature"] != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is journalled under a signature this manager does not "
            f"derive for it; the operands an ordinary cleanup signs are its "
            f"attempt, assignment, runtime, intake receipt and retention "
            f"policy, and a row signed over anything else is not that act")
    settled = _committed(store, operation, "runtime.destroy", what)
    # NO OPTIONAL MEMBER. Review [P2]: `kind` was admitted for the recordless
    # sibling's benefit, and this reader is expressly ordinary-only -- so a
    # list-valued foreign `kind` was returned unchanged. Ordinary `_settle`
    # never writes one.
    taken = boundaries.document(settled, what, required=CLEANUP_RECEIPT,
                                optional=CLEANUP_EVIDENCE)
    if taken["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} was committed for {name_value(taken['attempt_id'])}")
    boundaries.text(taken["state"], f"{what}'s observed runtime state")
    boundaries.text(taken["why"], f"{what}'s account")
    if taken["cleanup"] not in CLEANUP_ENDINGS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} settled {name_value(taken['cleanup'])}, which is not one "
            f"of {', '.join(CLEANUP_ENDINGS)}")
    committed = boundaries.document(
        taken["operation"], f"{what}'s operation",
        required=("operation_id", "signature_digest"))
    if committed != dict(operation):
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records operation "
            f"{name_value(committed['operation_id'])} signed "
            f"{name_value(committed['signature_digest'])}, and this read "
            f"derives {name_value(operation['operation_id'])} signed "
            f"{name_value(operation['signature_digest'])}; the identity and "
            f"the signature are one binding, and the signature is the half "
            f"that names the runtime")
    _settled_ending(store, attempt_id, receipt, retention_policy_digest,
                    taken, what)
    return taken


def _settled_ending(store, attempt_id, receipt, retention_policy_digest,
                    taken, what):
    """The ending, AND the facts `_settle` decides it from, checked together.

    W120762, corrected at review 2026-09-08T16-43-59Z [P1]. The first version
    asked only whether `failed` and a non-absent runtime agreed, which left
    every other crossing open: a retained ending holding material read as
    `complete`, a discard read as `retained`, and an `uncertain` or invented
    runtime state read as a settled `failed`. `_settle` does not choose an
    ending; it DERIVES one, so the reader derives the same one and compares.

    THE DERIVATION, in `_settle`'s own words. A runtime observed positively
    still there settles `failed` and nothing else -- it removed nothing, kept
    nothing and normalized nothing. A positively absent runtime settles
    `retained` when material stays, by policy or by quarantine, and `complete`
    only when nothing is left behind. And `uncertain` is not an ending at all:
    `_not_an_ending` returns before any transaction, so a journalled receipt
    carrying it describes a commit this manager cannot have made.
    """
    state = taken["state"]
    if state not in _DESTROY_STATES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} observed its runtime {name_value(state)}; a destroy "
            f"answers one of {', '.join(_DESTROY_STATES)}")
    if state == "uncertain":
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is journalled as an ending over an uncertain runtime; an "
            f"account that did not settle the question is never committed as "
            f"one, so this is a receipt for a commit that cannot have happened")
    # EVERY ARTIFACT DECIDED, UNDER THIS POLICY, and not merely "the kept ones
    # agree". Review [P1]: deleting every retention row after a real discard
    # left two empty lists agreeing with each other, so a cleanup that
    # destroyed material nobody ruled on read back as complete. This is the
    # same proof `authorize_cleanup` required before it destroyed anything,
    # asked of the same owner rather than restated.
    _authorized(store, attempt_id, receipt, retention_policy_digest)
    kept = _kept_material(store, attempt_id, taken, what)
    # W285465, and review 2026-09-28T10-39-45Z caught the compatibility half of this statically.
    #
    # THE DERIVATION FOLLOWS THE ENDING THAT WAS ACTUALLY PERFORMED, and which one that was is
    # PROVEN BY THE RECEIPT ITSELF rather than assumed from when this reader happens to run:
    #
    #   * a receipt carrying `directory_custody` was written by the PRE-RULING ending, which
    #     normalized both roots under a custody helper and then REMOVED them. Only that path
    #     ever wrote those receipts, and `_adopted_normalizations` below compares them against
    #     the normalizations this manager committed -- so the provenance is proved, not taken on
    #     trust. Those endings are derived exactly as they were: `complete` when nothing was
    #     kept, `retained` when something was.
    #   * a receipt WITHOUT it is a current execution-only ending: the workspace is preserved as
    #     is and nothing is removed, so `retained` is what those facts settle and `complete`
    #     would assert roots this manager no longer deletes.
    #
    # My previous cut derived `retained` for every absent runtime, which would have refused
    # every authentic historical `complete` receipt in an existing store. NOTHING IS ACCEPTED
    # ARBITRARILY: a receipt claiming `complete` with no custody evidence behind it is exactly
    # the fabricated removal this refuses, and no automatic deletion is restored anywhere.
    if state != "absent":
        ending = "failed"
    elif taken["directory_custody"] is not None:
        ending = "retained" if kept or receipt["custody"] == "quarantined" \
            else "complete"
    else:
        ending = "retained"
    if taken["cleanup"] != ending:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} settled {name_value(taken['cleanup'])} over a "
            f"{name_value(state)} runtime keeping "
            f"{sample_of(kept) if kept else 'nothing'} in "
            f"{name_value(receipt['custody'])} custody, and those facts "
            f"settle {name_value(ending)}; an ending is derived from them "
            f"rather than recorded beside them")
    _adopted_normalizations(store, attempt_id, taken, what)


def _kept_material(store, attempt_id, taken, what):
    """`kept` against the decisions that KEEP, and not against every decision.

    W120762. A `discard-after-intake` artifact is decided and deliberately not
    kept, so a reader comparing `kept` against the whole retention set reports
    an honest discard as two accounts that disagree. That filter is what makes
    this comparison right and is also why it cannot stand alone: the caller
    proves every artifact is DECIDED before asking what was kept.

    AND A FAILED CLEANUP KEEPS NOTHING, whatever was decided. It removed
    nothing, so it claims nothing: `_settle` returns before the retention read
    on that branch, and a receipt claiming kept material there would be an
    account of custody the cleanup never took.
    """
    kept = own(taken["kept"], what=f"{what}'s kept material")
    if type(kept) is not list:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names {name_value(taken['kept'])} as what it kept; a "
            f"cleanup keeps a list of artifact identities")
    for name in kept:
        boundaries.identity(name, f"{what}'s kept artifact id")
    expected = [] if taken["state"] != "absent" else sorted(
        one["artifact_id"] for one in retentions_of(store, attempt_id)
        if one["disposition"] in KEEPS_MATERIAL)
    if kept != expected:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} kept {sample_of(kept) if kept else 'nothing'} and this "
            f"attempt's retention decisions keep "
            f"{sample_of(expected) if expected else 'nothing'}; a cleanup and "
            f"the decisions that authorized it name one set of material")
    return kept


def _adopted_normalizations(store, attempt_id, taken, what):
    """Both directory-custody receipts, compared against their own owner.

    W120762, and the gap it closes is that NOTHING was compared. A settled
    positive absence normalizes the result root and then the workspace root
    that contains it, and its receipt records both; a consumer that accepted
    an empty document there took a cleanup's word for custody acts nobody
    showed. `custody.historical_directory_custody` is the normalization
    owner's own read and it is asked here rather than re-derived, so this
    module holds no second copy of that protocol.

    A `failed` CLEANUP CARRIES NONE, and that is not an exemption. The runtime
    survived its destroy, so no removal and no retention claim followed and
    `_settle` performs no directory act at all -- a receipt claiming one would
    be describing something that did not happen.
    """
    from . import custody as _custody

    held = taken["directory_custody"]
    ceased = _writer_cessation_of(store, taken)
    if taken["state"] != "absent":
        if held is not None or ceased is not None:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} observed its runtime {name_value(taken['state'])} "
                f"and records directory custody; a cleanup whose runtime "
                f"survived normalizes nothing and establishes no cessation")
        return
    # W285465: EXACTLY ONE OF THE TWO, and it is compared against a committed act either
    # way. `directory_custody` is the normalized ending's evidence; `writer_cessation` is
    # the no-helper ending's, and the reader below re-reads it out of the journal rather
    # than accepting the receipt's own copy. Both present would be a receipt claiming a
    # normalization that this path does not perform; neither present is a terminal ending
    # resting on nothing.
    if (held is None) == (ceased is None):
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records "
            f"{'both directory custody and a writer cessation' if held is not None else 'neither directory custody nor a writer cessation'}"
            f"; a positive absence ends on exactly one of the two accounts of its roots")
    if held is None:
        _adopted_writer_cessation(store, attempt_id, ceased, what)
        return
    adopted = boundaries.document(held, f"{what}'s directory custody",
                                  required=_CUSTODY_ROOTS)
    for which in _CUSTODY_ROOTS:
        if adopted[which] != _custody.historical_directory_custody(
                store, attempt_id, which):
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s {which} directory custody differs from the "
                f"normalization this manager committed for that root")


def _writer_cessation_of(store, taken):
    """The committed no-helper evidence for the destroy a cleanup receipt names, or `None`.

    Selected by the receipt's own operation identity -- which already binds the exact
    runtime, the intake receipt and the retention policy -- so this cannot pick up evidence
    committed for another runtime or another policy.
    """
    operation = boundaries.document(taken["operation"], "a cleanup's operation",
                                    required=("operation_id",),
                                    optional=("signature_digest", "kind",
                                              "operands"))
    return historical_writer_cessation(store, operation)


def proved_writer_cessation(store, attempt_id, operation, what):
    """The committed establishment for a destroy, VALIDATED, or a refusal.

    W285465 review 2026-09-28T06-23-25Z asks for matching readers, and a reader that only
    asks whether a record EXISTS is not one: measured, a record edited to say the runtime
    was running, or that a helper survived, or that it was established for another attempt,
    was accepted by existence alone. Every consumer of this evidence -- the ordinary ending's
    own reader and the historical review reader -- asks this.
    """
    ceased = historical_writer_cessation(store, operation)
    if ceased is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} names no committed writer cessation for its destroy; an ending "
            f"rests on an act this manager can show in its own journal")
    _adopted_writer_cessation(store, attempt_id, ceased, what)
    return ceased


def _adopted_writer_cessation(store, attempt_id, ceased, what):
    """The no-helper ending's evidence, compared against the record it names.

    Review 2026-09-28T06-00-04Z: "matching readers". The receipt's own copy proves nothing
    -- a store edit reaches it -- so this selects the committed `cleanup.writer-cessation`
    for the SAME destroy operation the receipt names and compares member for member. The
    operation identity already binds the exact runtime, the intake receipt and the
    retention policy, so evidence committed for another runtime or another policy is a
    different record and cannot be adopted here.
    """
    offered = boundaries.document(ceased, f"{what}'s writer cessation",
                                  required=WRITER_CESSATION)
    if offered["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s writer cessation was established for "
            f"{name_value(offered['attempt_id'])}")
    # W285465 under the 294568/294616 supersession: THE CESSATION HALF IS ALL THERE IS TO
    # VALIDATE HERE. No output member is recorded any more, because completion performs no
    # output observation at all; what must be true is the exact runtime absent and no
    # surviving writer, which is what execution release rests on.
    if offered["helpers"] != [] or offered["state"] != "absent":
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s writer cessation does not establish an absent runtime, "
            f"accessible output and no surviving writer")


def _absence_proof(store, attempt, attempt_id, retention_policy_digest):
    """The COMMITTED ordinary cleanup this discharge is authorized by.

    Every step selects rather than believes. The intake receipt is half the key
    to the destroy identity, the retention policy is the other half, and the
    identity that comes out is the one `authorize_cleanup` itself derived -- so
    a caller naming another policy selects an operation this manager never
    committed instead of authorizing an act under one it did.

    OTHER CLEANUP FAMILIES ARE NOT SILENTLY COVERED. A failed start, a refused
    session and an abandonment each end through their own operation kind with
    their own record, and none of them is `runtime.destroy`. This reads that
    one kind by name; the others are separately accountable and are not
    admitted here by accident.
    """
    receipt = intake_receipt_of(store, attempt_id)
    if receipt is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no intake receipt, so no "
            f"ordinary cleanup was ever authorized for it; a gate is "
            f"discharged on the cleanup this manager committed and never on "
            f"the absence of one")
    operation = destroy_operation(attempt, receipt["receipt_digest"],
                                  retention_policy_digest)
    settled = _committed(store, operation, "runtime.destroy",
                         f"attempt {name_value(attempt_id)}'s gate discharge")
    taken = boundaries.document(
        settled, f"attempt {name_value(attempt_id)}'s committed cleanup",
        required=("attempt_id", "cleanup", "state", "why", "kept", "operation",
                  "directory_custody"),
        optional=("kind",) + CLEANUP_EVIDENCE)
    if taken["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)}'s discharge selected a cleanup "
            f"committed for {name_value(taken['attempt_id'])}")
    # THE COMMITTED OPERATION IS OWNED AND COMPARED WHOLE, and "whole" is the
    # correction. Review 2026-09-08T14:27:00Z [P1]: `destroy_operation` splits
    # its binding -- `operation_id` covers the attempt, the assignment, the
    # receipt and the policy, and `signature_digest` is the half that covers
    # `runtime_id`. This compared the identity and dropped the signature, so
    # editing nothing but the attempt row's `runtime_id` after a real cleanup
    # still selected the committed act, and the evidence then certified a
    # runtime this manager had never observed absent.
    #
    # SO BOTH HALVES, against an operation derived from the CURRENT row. A
    # changed, absent or malformed runtime moves the derived signature away
    # from the committed one and refuses here -- before the authority is asked
    # and with no receipt written. `destroy_operation` and `_committed` are
    # untouched; what was missing was this comparison, not their semantics.
    committed = boundaries.document(
        taken["operation"],
        f"attempt {name_value(attempt_id)}'s committed cleanup operation",
        required=("operation_id", "signature_digest"))
    if committed != dict(operation):
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)}'s committed cleanup records "
            f"operation {name_value(committed['operation_id'])} signed "
            f"{name_value(committed['signature_digest'])}, and this discharge "
            f"derives {name_value(operation['operation_id'])} signed "
            f"{name_value(operation['signature_digest'])}; the identity and "
            f"the signature are one binding, and the signature is the half "
            f"that names the runtime this evidence would certify absent")
    if taken["state"] != "absent":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)}'s cleanup observed its runtime "
            f"{name_value(taken['state'])}; the gate takes POSITIVE absence "
            f"of the exact runtime, and an unobserved or surviving one is not "
            f"the same fact however the cleanup ended")
    if taken["cleanup"] not in _ABSENT_ENDINGS:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)}'s cleanup settled "
            f"{name_value(taken['cleanup'])}; a gate is discharged behind an "
            f"ending that followed positive absence, and "
            f"{', '.join(_ABSENT_ENDINGS)} are the two that do")
    return taken


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
    # W285465 review 2026-09-28T09-15-42Z: THE FAILED-START ENDING RUNS NO HELPER EITHER, so
    # the seam it proves before any destructive work is the writer listing its establishment
    # is made with. W43975's [P0] rule is kept -- typed here, ahead of the destroy.
    _ending_capable(adapter, attempt_id)
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
    if attempt["runtime_id"] is None and \
            attempt["execution_runtime"] != "destroyed":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no attached runtime; this "
            f"ending exists for a start that CREATED a container, and a start "
            f"that created none has no exact identity to remove")
    if attempt["runtime_id"] is None:
        # W275774 review 2026-09-26T19-13-42Z: A PROVED NON-LAUNCH IS AN ENDING
        # TOO, and until now it was the one failed start with no way out.
        #
        # A start whose RESERVATION was refused never reached the engine, so
        # `_identify` records positive absence rather than uncertainty -- see
        # `attempts._identify`'s `submitted` rule -- and this attempt holds a
        # durable start-failure record with `destroyed` and no identity. The
        # refusal above is still exactly right for the state it names, which is
        # "no identity AND no proof"; this is the other state, "no identity
        # BECAUSE nothing was created", and refusing it left ordinary token
        # contention holding its Work's runtime lane with no ending anywhere in
        # that Work's future to release it.
        #
        # THE EVIDENCE IS THE AXIS AND NOT THIS CALL'S OPINION. `destroyed` is
        # written only by a positive observation, and the same rule is already
        # how `_resource_cessation` reads an attempt that never attached one --
        # so this admits the fact that module admits rather than inventing a
        # second meaning for it. `uncertain` is still refused above; nothing
        # here weakens the frozen asymmetry.
        #
        # NO CROSSING, BECAUSE THERE IS NOTHING TO DESTROY. The engine is not
        # asked to remove a container nobody created, and both providers are
        # `not-delivered` for the reason the receipt path states: a runtime that
        # was never started mounted nothing. The roots are still normalized and
        # the receipts still adopted below, because THOSE are what authorize the
        # removal and the retention.
        observed = {"state": "absent",
                    "why": "no runtime was created for this attempt: its start "
                           "failure is recorded with no identity and this "
                           "attempt's execution runtime is destroyed",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}
    else:
        observed = _destroyed_failed_start(adapter, attempt, attempt_id,
                                           operation, record["digest"],
                                           retention_policy_digest)
    pending = _not_an_ending(store, attempt, attempt_id, observed, operation)
    if pending is not None:
        return pending
    # W285465 with OWNER-NO-AUTOMATIC-NORMALIZATION-20260928: ESTABLISHED AND COMMITTED,
    # NOT NORMALIZED -- the same correction the ordinary completion and the abandonment
    # already carry, for the same reason: this path may launch no helper, and the ending's
    # account of its roots is an observation it commits under this destroy's own identity.
    if observed["state"] == "absent":
        _record_writer_cessation(store, adapter, attempt_id, attempt=attempt,
                                 operation=operation, observed=observed)
    return store.transact(
        operation["operation_id"], "runtime.destroy-failed-start", signature,
        lambda connection: _settle_recordless_cleanup(
            store, connection, attempt_id, observed, operation,
            why="failed-start cleanup settled retained", custody=adapter))


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
    # W285465: AND THE REFUSED-SESSION ENDING RUNS NO HELPER. The attempt is named by the
    # session row above, so the seam this ending actually uses -- the writer listing -- is
    # typed as soon as there is an attempt to name, and still ahead of the destroy, which is
    # what W43975's [P0] rule requires.
    _ending_capable(adapter, attempt_id)
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
    # W285465 with OWNER-NO-AUTOMATIC-NORMALIZATION-20260928: ESTABLISHED AND COMMITTED,
    # NOT NORMALIZED -- the same correction the ordinary completion and the abandonment
    # already carry, for the same reason: this path may launch no helper, and the ending's
    # account of its roots is an observation it commits under this destroy's own identity.
    if observed["state"] == "absent":
        _record_writer_cessation(store, adapter, attempt_id, attempt=attempt,
                                 operation=operation, observed=observed)
    return store.transact(
        operation["operation_id"], "runtime.destroy-refused-session",
        signature,
        lambda connection: _settle_recordless_cleanup(
            store, connection, attempt_id, observed, operation,
            why="refused-session cleanup settled retained", custody=adapter))


def abandon_attempt(store, port, adapter, *, attempt_id, reason,
                    retention_policy_digest, seconds=None, reclaim=None,
                    govern=None):
    """W44716: end the attempt an operator DECLARES abandoned.

    THE FOURTH ENDING, and approver ruling 2026-08-30 is why it is one. A
    runtime that STARTED and whose worker then never answered has none of the
    three existing authorizations: `authorize_cleanup` is authorized by an
    intake receipt and nothing was frozen or collected;
    `authorize_failed_start_cleanup` by a start failure that did not happen;
    `authorize_refused_session_cleanup` by a handshake refusal that did not
    happen either. The start SUCCEEDED and the worker simply stopped saying
    anything, so all three decline and the manager cannot end a runtime it
    started itself.

    WHAT AUTHORIZES IT IS A DECLARATION, and CALLING THIS IS THE DECLARATION.
    There is deliberately no deadline, elapsed-time, retry-count or heartbeat
    operand and nothing here reads a clock: a timer alone does not abandon an
    attempt, because "it has been quiet a while" is not a decision and the
    thing being ended may be a worker doing slow, correct work. An operator or
    an explicit Route policy decides, and `reason` is that decision written
    down.

    THE ORDER IS THE RULING'S, and each step's proof is the next one's
    precondition:

      1. own the operands, the participant, the exact assignment and runtime,
         the adapter capability and the eligibility -- so a deployment missing
         the capability cannot leave an assignment half-recorded;
      2. commit or replay the intent BEFORE any external call, so a crash
         after the fence or after the removal resumes from a record that
         already names what was declared;
      3. fence the exact generation at the authority, through an operation
         identity distinct from both the declaration and an ordinary cancel.
         Nothing calls the adapter before that answer;
      4. read the committed intent back as the authorization;
      5. call only `destroy_abandoned`, whose force-removal is the combined
         stop and remove and whose observation owns positive absence;
      6. settle through `_settle_recordless_cleanup`: positive absence plus
         both provider endings, cleanup `retained`, and the lane released --
         and nothing else records an ending.

    AND THE RESULT DIRECTORY IS LEFT WHERE IT IS, on the rule M33800 set for
    both siblings. Whatever the worker wrote before it stopped answering was
    written by a worker this manager never heard from: it began untrusted and
    stays untrusted. This ends at `retained` and deletes nothing, freezes
    nothing, and admits not one byte to the proposal pipeline.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    reason = boundaries.text(reason, "an abandonment reason")
    if not reason.strip():
        raise ContractRefusal(
            "integrity", "schema",
            "an abandonment carries the operator's own reason; calling this "
            "operation IS the declaration, so a blank one is a declaration "
            "nobody made")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    # THE CAPABILITY BEFORE ANYTHING IS RECORDED OR FENCED. A deployment that
    # cannot perform the removal must not leave an abandoned assignment
    # half-recorded and an authority generation fenced with nothing following.
    boundaries.capability(getattr(adapter, "destroy_abandoned", None),
                          "the runtime adapter's abandoned-attempt destroy")
    # W285465 review 2026-09-28T08-48-06Z: THE ABANDONED ENDING RUNS NO HELPER EITHER, so the
    # seam it proves before any destructive work is the writer listing its establishment is
    # made with -- exactly as the ordinary completion does. W43975's [P0] rule is kept: the
    # capability is typed here, ahead of the destroy.
    _ending_capable(adapter, attempt_id)
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    if attempt["runtime_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no attached runtime; "
            f"abandonment ends an attempt whose runtime STARTED and whose "
            f"worker then never answered, and there is nothing here to end")
    # WHICH AUTHORITY ACT THIS FENCE IS. W247941, owner selection 255814: an
    # attempt whose own cancellation already fenced this generation is fenced
    # by REPLAYING that operation, because the Authority ends a generation
    # once and a second identity over it can only refuse. See the supersession
    # note on `_abandon_fence_operation_id`. An attempt with no cancellation
    # is unchanged and fences under the abandonment's own identity.
    #
    # AND A DECLARATION THAT ALREADY EXISTS CHOOSES NOTHING. Review
    # 2026-09-24T10:11:35Z [P1]: deriving this operand from the world as it
    # stands now made an interrupted declaration unresumable the moment a
    # cancellation landed after it. The committed record's own operand is
    # read back and reused, so a resumed call signs exactly what was written.
    cancelled = _committed_cancellation(store, attempt, attempt_id, expect)
    own_fence = _abandon_fence_operation_id(attempt)
    declared = _declared_fence_identity(store, attempt)
    authority_operation_id = (
        declared if declared is not None
        else own_fence if cancelled is None
        else cancelled["authority_operation_id"])
    intent = _abandon_intent(store, attempt, attempt_id, expect, reason,
                             authority_operation_id)
    operation = _abandoned_destroy_operation(attempt, intent["digest"],
                                             retention_policy_digest)
    signature = manager_signature(
        "runtime.destroy-abandoned",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "abandonment_record_digest": intent["digest"],
         "retention_policy_digest": retention_policy_digest})
    found, already = store.replay(operation["operation_id"], signature,
                                  kind="runtime.destroy-abandoned")
    if found:
        # EXACT REPLAY IS CHECKED BEFORE THE MUTABLE PRECONDITIONS, so a
        # successfully retained ending stays replayable after it is terminal.
        #
        # W275774 review 16:22:13Z [P1]: AND THE REPLAY RETURNS THE RESOURCE TOO.
        # I fixed this on the ordinary cleanup last claim and left the abandoned
        # family with the same hole, which an independent probe found immediately:
        # the ending commits, the release fails, and the retry answered the saved
        # ending without ever returning -- stranding the generation permanently,
        # because a terminal ending is the last thing that will ever run for this
        # attempt. `_released` is idempotent and resolves the generation from the
        # execution and operation that reserved it, so a stale replay finds its own
        # returned generation and cannot touch a later one.
        _released(store, govern, attempt, attempt_id, already["cleanup"])
        return already
    # THIS DERIVED CLEANUP MAY NOT REVISIT A FINISHED ENDING. Review
    # 2026-08-30T11:56:53Z [P0]: skipping the mutable eligibility for a
    # REPLAYED INTENT is right, and I wrongly extended it to every destroy
    # operation later derived from that intent. The retention policy rides the
    # destroy identity but not the declaration, so a second policy over an
    # already-settled attempt missed the replay above and went on to fence and
    # remove again, refusing only afterwards inside the settlement.
    #
    # The distinction the intent replay actually protects is narrower than it
    # looked. An INTERRUPTED same-policy call has no terminal cleanup result --
    # it is exactly the caller that must be allowed to finish what it started,
    # and its axis is still pending or blocked-on-intake. A COMPLETED
    # same-policy call is caught by the exact replay above. So a terminal axis
    # at this point can only mean a NEWLY DERIVED cleanup arriving after some
    # ending already happened, and that one refuses here -- before the
    # authority is touched and before the engine is called.
    #
    # Read fresh rather than trusting the attempt read at entry: the
    # declaration was committed in between, and what this refuses on is the
    # axis as it stands NOW.
    current = _attempt_of(store._connection, attempt_id)
    if current["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{current['cleanup']}, which is terminal; this abandonment "
            f"cleanup was derived after that ending and an ending is not "
            f"revisited")
    # THE FENCE, AND IT IS NOT CONDITIONAL ON THE ASSIGNMENT LOOKING DEAD.
    # The siblings refuse a still-live assignment because somebody else ended
    # it; abandonment is the act that ends it, so this fences rather than
    # asking whether somebody already did. `AuthorityPort.cancel` owns the
    # closed answer and proves this exact generation was fenced -- no
    # pre-read and no post-fence inference substitutes for that.
    # FENCED WITH THE ADOPTED RECORD'S OWN VALUES. A resumed call must reissue
    # the SAME authority operation with the SAME reason, and reading them off
    # the committed declaration is what makes that true across a restart.
    #
    # W247941: AND WHEN THE ADOPTED IDENTITY IS THE CANCELLATION'S, SO IS THE
    # REASON. The Authority signs a cancel over `{expect, reason}`, so
    # replaying its operation with the abandonment's own reason would be a
    # DIFFERENT act at the same identity and would collide rather than replay.
    # The reason is taken from the proved cancellation record -- never from
    # the caller and never from the axis -- and the abandonment's declaration
    # keeps its own reason in its own record, which is what
    # `abandonment_cleanup_of` and every later reader still see.
    #
    # W247941: THE DECLARATION'S BYTES AND THE FENCE EVIDENCE ARE SEPARATE
    # FACTS, and review 2026-09-24T10:11:35Z [P1] is why they have to be. The
    # record says which identity this ending DECLARED it would fence under and
    # is never rewritten; which Authority operation actually fences THIS
    # generation is decided here, from the cancellation record this manager
    # validated member by member and from the Authority's own answer to it.
    #
    # So a declaration committed before any cancellation -- including one
    # interrupted and resumed long afterwards -- keeps its bytes and still
    # ends, because the fence it needs is the cancellation's replay rather
    # than a second cancel over a generation that is already ended.
    #
    # NOTHING IS INFERRED FROM THE RECORD. `port.cancel` is still called and
    # `_abandoned_fence` still owns the answer; the record decides only which
    # operation is replayed and with which reason -- the Authority signs a
    # cancel over `{expect, reason}`, so the cancellation's own reason is the
    # only one that replays it rather than colliding with it.
    if cancelled is None:
        adopted_fence = intent["document"]["authority_operation_id"]
        fence_reason = intent["document"]["reason"]
    else:
        adopted_fence = cancelled["authority_operation_id"]
        fence_reason = cancelled["reason"]
    fenced = port.cancel(dict(expect), adopted_fence, fence_reason,
                         expect["work_ref"]["work_id"],
                         expect["work_ref"]["authority_uuid"])
    # THE WORLD IS READ AGAIN BEFORE THE DESTRUCTIVE STEP, because the
    # authority call is the one place this operation waits on somebody else.
    #
    # Review 2026-08-30T12:10:41Z [P0]: the gates below were being applied to
    # the row read at ENTRY -- before the declaration, before the destroy
    # replay and before `cancel`. RECONCILIATION IS AN INDEPENDENT MANAGER
    # OPERATION and can move the execution runtime to `uncertain` while the
    # fence is in flight; the abandonment then crossed the destructive
    # boundary on a `running` snapshot that had already been revoked, and only
    # discovered the conflict during settlement, as a refused state
    # regression. A refusal after the removal is not a refusal.
    #
    # So both gates are applied to the CURRENT row, immediately before any
    # runtime control, and this read is deliberately the last thing between
    # the fence and the engine.
    settled = _attempt_of(store._connection, attempt_id)
    # ANOTHER ENDING MAY HAVE SETTLED DURING THE AUTHORITY CALL. The
    # pre-fence check cannot see that, and an ending is not revisited however
    # narrow the window was.
    if settled["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup became "
            f"{settled['cleanup']} while the generation was being fenced; "
            f"the generation is fenced and an ending is not revisited")
    # `uncertain` MAY BE FENCED AND MAY NOT BE CLEANED UP. Stopping further
    # authorized execution is the whole point of abandonment, so the fence
    # above stands; but this manager cannot say what exists, so there is
    # nothing to prove absent and the lane is not released.
    if settled["execution_runtime"] == "uncertain":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution runtime is "
            f"uncertain; the generation is fenced, and cleanup waits for a "
            f"reconciliation that observes what is true")
    # AND IT IS STILL THE CONTAINER THE DECLARATION NAMES. The adopted record
    # authorizes destroying ONE runtime; if the row now names another, this
    # removal is not the one that was authorized, whatever moved it.
    if settled["runtime_id"] != intent["document"]["runtime_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"the recorded abandonment names runtime_id "
            f"{name_value(intent['document']['runtime_id'])} and attempt "
            f"{name_value(attempt_id)} is now attached to "
            f"{name_value(settled['runtime_id'])}; the record and the act it "
            f"authorizes must describe one runtime")
    observed = _destroyed_abandoned(adapter, settled, attempt_id, operation,
                                    intent["digest"], retention_policy_digest,
                                    seconds=seconds)
    pending = _not_an_ending(store, settled, attempt_id, observed, operation)
    if pending is not None:
        # UNSETTLED, AND SAID IN THE SAME SHAPE. Nothing is journalled, so a
        # retry runs the removal again -- which is safe, because force-removal
        # of an already absent exact identity answers absent.
        return documents.abandonment(intent=dict(intent["document"]),
                                     fenced=dict(fenced), cleanup=pending)
    # THE COMMITTED RESULT IS THE WHOLE COMPOSITE. Review
    # 2026-08-30T11:44:55Z [P0]: the first cut committed the bare
    # `cleanup.settled` document and wrapped it for the FIRST caller only, so
    # the same public operation answered `{intent, fenced, cleanup}` once and
    # a bare cleanup document on every replay. A resumed terminal attempt then
    # failed in its caller as an implementation error instead of replaying its
    # ending. What is journalled is what is answered, and replay returns it
    # without rereading a removed runtime or a mutable axis.
    # W285465 with OWNER-NO-AUTOMATIC-NORMALIZATION-20260928, review 2026-09-28T08-48-06Z:
    # ESTABLISHED AND COMMITTED, NOT NORMALIZED. This ran a custody helper per root and the
    # ending read those receipts back; the ruling removes automatic launches from this path
    # too, and the 10 `test_stage_execution` errors were exactly that -- `custody`'s episode
    # claim refused by the attempt's own live token, because a helper was being asked to act
    # over roots a governed execution still owned. The evidence is the same shape the
    # ordinary completion uses: the exact runtime absent, output this manager can read, and
    # no surviving writer, committed under this destroy's own identity and read back before
    # anything terminal.
    if observed["state"] == "absent":
        _record_writer_cessation(store, adapter, attempt_id, attempt=attempt,
                                 operation=operation, observed=observed,
                                 seconds=seconds, reclaim=reclaim)
    answer = store.transact(
        operation["operation_id"], "runtime.destroy-abandoned", signature,
        lambda connection: documents.abandonment(
            intent=dict(intent["document"]), fenced=dict(fenced),
            cleanup=_settle_recordless_cleanup(
                store, connection, attempt_id, observed, operation,
                why="abandonment cleanup settled retained",
                custody=adapter)))
    # W275774: THE ABANDONED ENDING RETURNS THE RESOURCE TOO, on the same proof.
    #
    # An abandonment is exactly the case a resource token exists for -- a runtime
    # whose worker never answered -- so leaving its workspace held forever would
    # make the governed lifecycle worse than the ungoverned one. The evidence is the
    # same: this family's cleanup record carries its own observed state and custody,
    # and `_resource_cessation` answers `None` unless both prove the resource free.
    _released(store, govern, attempt, attempt_id, answer["cleanup"])
    return answer


# W128682: THE ABANDONED FAMILY'S OWN EVIDENCE AND ITS OWN DISCHARGE.
#
# The ordinary discharge is authorized by `_absence_proof`, which requires an
# `intake_receipt_of` and reads `runtime.destroy` BY NAME. An abandonment has
# neither: nothing was frozen or collected, so there is no receipt, and its
# removal commits under `runtime.destroy-abandoned`. Widening either would let
# an abandonment ride the ordinary family's identity; fabricating a receipt
# would be inventing the evidence. So this is a separate family with separate
# identities, and the ordinary readers and act below are untouched.
ABANDONED_CLEANUP_SCHEMA = "baton.v12.abandoned-cleanup/1"

# EXACTLY WHAT A READ ABANDONED CLEANUP CARRIES. Owner128669's contract, and
# every exit is held to it.
ABANDONED_CLEANUP = ("schema", "attempt_id", "assignment", "runtime_id",
                     "retention_policy_digest", "intent", "intent_digest",
                     "fence", "cleanup")

ABANDONED_GATE_DISCHARGE_KIND = "authority.discharge-quiescence-abandoned"
ABANDONED_GATE_DISCHARGE_SCHEMA = "baton.v12.abandoned-gate-discharge/1"
ABANDONED_GATE_DISCHARGE_RECEIPT = (
    "schema", "attempt_id", "assignment", "runtime_id",
    "retention_policy_digest", "cleanup_operation", "operation_id", "gate",
    "evidence", "authority_receipt")

# The ending an abandonment settles at, and the observed runtime state that
# authorizes calling it absence. `retained` is the only ending
# `_settle_recordless_cleanup` reaches after a positive absence -- the family
# deletes nothing -- and `absent` is the engine's own positive sentence.
#
# A SURVIVING RUNTIME DOES JOURNAL, and my first comment here said it did not.
# `_settle_recordless_cleanup` commits the composite with the ending `failed`,
# which my own measured case in `test_intake` established in the same claim
# that wrote the wrong sentence. So a present record is not evidence of
# absence by itself: both facts are required and both are checked.
_ABANDONED_ENDING = "retained"
_ABANDONED_ABSENT = "absent"

# THE AUTHORITY'S OWN CANCELLATION FENCE, and it is not this module's to
# invent. `authority/core.py`'s `route_fenced` compares a committed
# cancellation against `{"cause": "cancelled", "assignment": expect, "phase":
# "block", "gate": gate, "fenced": True}` -- so those are the exact semantics
# an abandonment fence has, read from the owner that defines them.
_FENCE_CAUSE = "cancelled"
_FENCE_PHASE = "block"


def _abandonment_declaration(store, attempt, attempt_id):
    """The committed declaration this family's whole identity hangs off.

    THE JOURNAL IS THE AUTHORIZATION, exactly as `_abandon_intent` treats it
    during the act. Absence answers `None` -- an attempt nobody declared
    abandoned simply has no abandoned cleanup -- and a record this manager
    cannot own is an integrity fault rather than an absence, on
    `_recorded_discharge`'s rule: reporting the second as the first would
    invite a consumer to act as though nothing had happened.

    THE SIGNATURE IS DERIVED FROM THE RECORD'S OWN MEMBERS AND COMPARED.
    `cleanup_of` learned this at review 2026-09-08T16-43-59Z: replaying under
    the row's own signature proves the row is self-consistent and nothing else.
    `attempt.abandon` signs the attempt, the fixed assignment, the runtime, the
    reason and the authority operation together, so a row signed over anything
    else is not that act -- and the reason and the operation id are members of
    the document, which is what makes recomposing it possible here without
    asking a caller for either.
    """
    operation_id = _abandon_operation_id(attempt)
    record = store.operation_record(operation_id)
    if record is None:
        return None
    what = f"attempt {name_value(attempt_id)}'s committed abandonment"
    if record["kind"] != "attempt.abandon":
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation {name_value(operation_id)}, which this "
            f"manager committed as {name_value(record['kind'])}")
    _, committed = store.replay(operation_id, record["signature"],
                                kind="attempt.abandon")
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation {name_value(operation_id)}, which this "
            f"manager committed with no recorded answer to replay")
    held = boundaries.document(committed, what,
                               required=documents.ABANDON_INTENT)
    expect = _fixed_assignment(attempt)
    for member, mine in (("attempt_id", attempt_id),
                         ("assignment", expect),
                         ("runtime_id", attempt["runtime_id"]),
                         ("decision", "abandoned")):
        if held[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} names {member} {name_value(held[member])} and this "
                f"read is for {name_value(mine)}; the declaration and the "
                f"attempt it authorizes must describe one abandonment")
    boundaries.text(held["reason"], f"{what}'s reason")
    boundaries.identity(held["authority_operation_id"],
                        f"{what}'s authority operation identity")
    signature = manager_signature(
        "attempt.abandon",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"], "reason": held["reason"],
         "authority_operation_id": held["authority_operation_id"]})
    if record["signature"] != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is journalled under a signature this manager does not "
            f"derive for it; the operands a declaration signs are its attempt, "
            f"assignment, runtime, reason and authority operation, and a row "
            f"signed over anything else is not that act")
    return {"document": held, "digest": digest(held)}


def _abandoned_fence(taken, expect, what):
    """The authority's own fence answer, owned WHOLE and related to this
    attempt.

    Review 2026-09-09T15-22-41Z [P1], and the finding is right twice over. The
    first cut asked `if not fence["fenced"]`, so the STRING "false" -- which is
    truthy -- passed as proof that a generation had been fenced; and it checked
    neither the cause nor the phase, so a stored `cause` of "pass" or a `phase`
    of "queued" still reached the remote discharge.

    THE SEMANTICS ARE THE AUTHORITY'S AND ARE READ FROM IT. `route_fenced` in
    `authority/core.py` compares a committed cancellation against exactly
    `{"cause": "cancelled", "assignment": expect, "phase": "block", "gate":
    gate, "fenced": True}`, so all five are required here rather than the two
    that were. An abandonment fence that says anything else is not the act
    whose gate this discharges.

    AND IT STAYS HISTORICAL. Every comparison is against the RECEIPT'S OWN
    assignment and the gate that assignment composes -- nothing here reads the
    Work's current phase or gate -- so a valid read still answers after the
    Work has advanced, which is the property the review requires preserved.
    """
    fence = boundaries.document(taken, f"{what}'s committed fence",
                                required=FENCE)
    # `is not True`, NOT falsiness: "false", 1 and [0] are all truthy, and a
    # fence is a fact rather than a value that happens to be non-empty.
    if fence["fenced"] is not True:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records {name_value(fence['fenced'])} as whether the "
            f"generation was fenced; an abandonment that cannot show its own "
            f"generation was actually fenced has no gate of its own to "
            f"discharge")
    for member, expected in (("cause", _FENCE_CAUSE), ("phase", _FENCE_PHASE)):
        if fence[member] != expected:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} records fence {member} {name_value(fence[member])} "
                f"and an abandonment's cancellation fence records "
                f"{name_value(expected)}; the authority's own fenced-routing "
                f"rule names both, and an answer about another transition is "
                f"not this abandonment's")
    if fence["assignment"] != expect:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records a fence of assignment "
            f"{name_value(fence['assignment'])} and this attempt is fixed to "
            f"{name_value(expect)}; a fence that ended somebody else's "
            f"assignment is not this abandonment's")
    gate = _quiescence_gate_token(expect)
    if fence["gate"] != gate:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records gate {name_value(fence['gate'])} and this "
            f"attempt's own generation composes {name_value(gate)}")
    return fence


def _abandoned_absence(store, taken, attempt_id, operation, what):
    """The removal's settled cleanup, EVERY member of it, or a refusal.

    Review 2026-09-09T15-22-41Z [P1]. The first cut checked the ending, the
    observed state and the operation pair, and left `kept`, `directory_custody`
    and a foreign `kind` entirely unchecked -- so a composite with custody set
    to `None`, an invented artifact in `kept`, or an extra member still
    returned positive proof and drove one real `satisfy_gate`. Validating the
    REQUEST signature does not validate every member of the OUTCOME, which is
    the sentence the review put it in and the one I had missed.

    SO THE MEMBER SET IS EXACT. `_settle_recordless_cleanup` writes no `kind`
    on this family's endings at all -- `documents.cleanup_settled`'s contract
    has no optional member -- and admitting one was borrowing a sibling's
    allowance for a document that never carries it.

    `kept` IS EMPTY BY THIS FAMILY'S OWN FACTS, and that is a different rule
    from the ordinary reader's. An abandonment intakes nothing and decides no
    retention, so there is no decision set to compare against: the settlement
    writes `kept=[]` unconditionally and anything else is an account of custody
    this ending never took.

    THE NORMALIZATIONS ARE ASKED OF THEIR OWNER. `custody.
    historical_directory_custody` is the normalization owner's own read, and it
    is asked here rather than re-derived -- so this module holds no second copy
    of that protocol and nothing about the ordinary family is widened to reach
    it.
    """
    from . import custody as _custody

    cleanup = boundaries.document(taken, f"{what}'s committed cleanup",
                                  required=CLEANUP_RECEIPT,
                                  optional=CLEANUP_EVIDENCE)
    if cleanup["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records a cleanup committed for "
            f"{name_value(cleanup['attempt_id'])}")
    # A `failed` ENDING IS NOT AN INTEGRITY FAULT, and `_absence_proof` already
    # settled which category it is. The record is this family's own committed
    # act, correctly saying the runtime SURVIVED its own removal -- so it is a
    # precondition this read cannot meet rather than a row it cannot own, and
    # the caller is told which fact stopped it.
    if cleanup["cleanup"] != _ABANDONED_ENDING:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} settled {name_value(cleanup['cleanup'])}; an abandonment "
            f"that reached its ending settles "
            f"{name_value(_ABANDONED_ENDING)}, and any other ending is "
            f"evidence against absence rather than for it")
    if cleanup["state"] != _ABANDONED_ABSENT:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} observed runtime state {name_value(cleanup['state'])} and "
            f"a gate takes {name_value(_ABANDONED_ABSENT)}; a stop order, an "
            f"uncertain observation and a surviving runtime are not absence")
    boundaries.text(cleanup["why"], f"{what}'s account")
    committed = boundaries.document(
        cleanup["operation"], f"{what}'s cleanup operation",
        required=("operation_id", "signature_digest"))
    # WHOLE, AND FOR `_absence_proof`'S OWN REASON. `operation_id` binds the
    # attempt, the assignment, the declaration and the policy;
    # `signature_digest` is the half that binds the runtime. Comparing one and
    # dropping the other lets an edited runtime keep a real removal's evidence.
    if committed != dict(operation):
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records cleanup operation "
            f"{name_value(committed['operation_id'])} signed "
            f"{name_value(committed['signature_digest'])}, and this read "
            f"derives {name_value(operation['operation_id'])} signed "
            f"{name_value(operation['signature_digest'])}; the identity and "
            f"the signature are one binding")
    kept = own(cleanup["kept"], what=f"{what}'s kept material")
    if type(kept) is not list or kept != []:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} kept {name_value(cleanup['kept'])}; an abandonment "
            f"intakes nothing and decides no retention, so it keeps nothing "
            f"and its settlement records an empty list")
    # W285465 with OWNER-NO-AUTOMATIC-NORMALIZATION-20260928: EITHER ACCOUNT OF THE ROOTS,
    # and each proved against an act this manager COMMITTED. An abandonment performed before
    # the ruling carries two normalization receipts and is still proved against them --
    # historical evidence is preserved rather than reinterpreted. One performed after it
    # carries none and rests on the committed writer cessation for this destroy, validated by
    # `proved_writer_cessation` rather than accepted for existing. Neither present is an
    # ending resting on nothing, and both present would be a receipt claiming a normalization
    # this path does not perform.
    held = cleanup["directory_custody"]
    if held is None:
        proved_writer_cessation(store, attempt_id, cleanup["operation"], what)
    else:
        adopted = boundaries.document(held, f"{what}'s directory custody",
                                      required=_CUSTODY_ROOTS)
        for which in _CUSTODY_ROOTS:
            if adopted[which] != _custody.historical_directory_custody(
                    store, attempt_id, which):
                raise ContractRefusal(
                    "integrity", "schema",
                    f"{what}'s {which} directory custody differs from the "
                    f"normalization this manager committed for that root; an "
                    f"ending is not claimed on a normalization nobody can show "
                    f"was performed")
    return cleanup


def abandonment_cleanup_of(store, *, attempt_id, retention_policy_digest):
    """The committed ABANDONED cleanup for this attempt and policy, or absence.

    W128682, `work/records/2026/09/finding-v12-abandoned-cleanup-discharge/`.
    Discovered by W119114's composed proof: an operator declaration ends the
    attempt and fences its generation, and nothing could then read that ending
    as evidence, so the gate the fence installed stayed shut forever.

    IT IS `cleanup_of` ONE FAMILY OVER, and it is a separate function for the
    reason that reader states in its own last paragraph: the four cleanup
    families each end through their own operation kind, and it reads
    `runtime.destroy` by name so none of the others is admitted by accident.
    The same rule read from this side means the abandoned family needs its own
    reader rather than a widened one.

    THE SELECTION IS THE DECLARATION AND THE POLICY. There is no intake
    receipt here -- nothing was frozen or collected, which is the whole reason
    abandonment exists -- so the declaration's digest is what rides the removal
    identity, exactly as the receipt's digest rides the ordinary one. A caller
    naming another policy selects an act this manager never committed.

    ABSENCE IS HONEST AND IS THREE THINGS. An attempt with no fixed assignment
    can have no identity; an attempt nobody declared abandoned has no
    declaration; and a declaration whose removal never committed is an
    abandonment that has not finished. None of the three is a fault, none is
    evidence, and each answers `None`.

    NOTHING MUTABLE IS EVIDENCE. Not `execution_runtime = destroyed`, which is
    a column a store edit reaches; not the cleanup axis; not the Work's current
    route or gate. What is read is the journal: the committed declaration, the
    committed composite the removal wrote, and the relationships between them.
    A merely recorded intent, a failed removal and an uncertain runtime each
    fail to supply absence, and say so.

    IT WRITES NOTHING AND CALLS NOTHING. No transaction, no session, no port,
    no adapter, no engine -- there is no branch in it that could.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _fixed_assignment(attempt)
    if expect is None:
        return None
    declared = _abandonment_declaration(store, attempt, attempt_id)
    if declared is None:
        return None
    what = f"attempt {name_value(attempt_id)}'s committed abandoned cleanup"
    operation = _abandoned_destroy_operation(attempt, declared["digest"],
                                             retention_policy_digest)
    record = store.operation_record(operation["operation_id"])
    if record is None:
        return None
    if record["kind"] != "runtime.destroy-abandoned":
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation "
            f"{name_value(operation['operation_id'])}, which this manager "
            f"committed as {name_value(record['kind'])}")
    # THE ROW'S SIGNATURE, DERIVED AND COMPARED, before the answer is replayed
    # under it. These are the exact operands `abandon_attempt` signs.
    signature = manager_signature(
        "runtime.destroy-abandoned",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "abandonment_record_digest": declared["digest"],
         "retention_policy_digest": retention_policy_digest})
    if record["signature"] != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is journalled under a signature this manager does not "
            f"derive for it; the operands an abandoned removal signs are its "
            f"attempt, assignment, runtime, declaration and retention policy")
    settled = _committed(store, operation, "runtime.destroy-abandoned", what)
    composite = boundaries.document(
        settled, what, required=documents.CONTRACTS["attempt.abandonment"][0])
    # THE COMPOSITE'S OWN DECLARATION IS THE ONE THIS READ SELECTED ON. The
    # removal journalled the record it adopted, so the two must be the same
    # document -- and if they are not, the identity that selected this row was
    # derived from something the row does not describe.
    if composite["intent"] != declared["document"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records a declaration that is not the one this read "
            f"selected on; the removal's identity carries the declaration's "
            f"digest, so the two are one act or neither is")
    return own({
        "schema": ABANDONED_CLEANUP_SCHEMA,
        "attempt_id": attempt_id,
        "assignment": expect,
        "runtime_id": boundaries.identity(
            attempt["runtime_id"], f"{what}'s runtime identity"),
        "retention_policy_digest": retention_policy_digest,
        "intent": declared["document"],
        "intent_digest": declared["digest"],
        "fence": _abandoned_fence(composite["fenced"], expect, what),
        "cleanup": _abandoned_absence(store, composite["cleanup"], attempt_id,
                                      operation, what),
    }, what=what)


def _abandoned_discharge_operation_id(attempt):
    """This attempt's ONE abandoned-discharge identity, derived and not minted.

    Over the attempt and its FIXED assignment alone, exactly as
    `_discharge_operation_id` is, and for the same reason: a manager resuming
    after a crash re-derives it without first re-establishing the evidence, so
    a discharge that committed replays even if the records it was derived from
    can no longer be read.

    THE KIND PREFIX IS WHAT KEEPS THE TWO FAMILIES APART. The operands are the
    same two an ordinary discharge signs an identity over, so without a
    distinct kind the two acts would collide on one identity -- and an
    abandoned discharge replaying as an ordinary one, or the reverse, is
    exactly the confusion this Work exists to prevent.
    """
    check_no_durable_secret(
        {"kind": ABANDONED_GATE_DISCHARGE_KIND,
         "operands": {"attempt_id": attempt["runtime_attempt_id"],
                      "expect": _fixed_assignment(attempt)}},
        what="an operation signature")
    return ABANDONED_GATE_DISCHARGE_KIND + ":" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt)})[len("sha256:"):]


def _abandoned_receipt_signature(taken):
    """The signature this receipt's own operands compose.

    THE SAME OPERANDS THE ACT SIGNED, recomposed from the receipt rather than
    from anything read fresh. One comparison for a relationship six separate
    field checks cannot state: the attempt, the fixed assignment, the gate, the
    runtime and the cleanup operation's whole identity AND signature belong
    together, and the contract requires the cleanup's signature in it because
    that is the half that names the runtime.
    """
    cleanup = taken["cleanup_operation"]
    return manager_signature(ABANDONED_GATE_DISCHARGE_KIND, {
        "attempt_id": taken["attempt_id"], "expect": taken["assignment"],
        "gate": taken["gate"], "runtime_id": taken["runtime_id"],
        "retention_policy_digest": taken["retention_policy_digest"],
        "cleanup_operation_id": cleanup["operation_id"],
        "cleanup_signature_digest": cleanup["signature_digest"]})


def _adopted_abandoned_discharge(value, what, *, operation_id=None,
                                 signature=None, expect=None, attempt_id=None):
    """One abandoned gate-discharge receipt, owned with its relationships.

    BOTH PUBLIC EXITS COME THROUGH HERE -- the replay short-circuit and
    `abandoned_gate_discharge_of` -- on `_adopted_discharge`'s rule: generic
    parsing establishes that bytes decode and establishes nothing about what
    they say, and checking each field individually proves every member
    well-formed while proving nothing about WHOSE receipt it is.

    NOTHING MUTABLE IS CONSULTED. Not today's runtime row, not the cleanup
    row, not the remote gate or phase. A correct receipt therefore still
    replays after the Work has been claimed and fenced again, which is the
    distinction the ordinary family established and this must not undo.
    """
    taken = boundaries.document(value, what,
                                required=ABANDONED_GATE_DISCHARGE_RECEIPT)
    if taken["schema"] != ABANDONED_GATE_DISCHARGE_SCHEMA:
        _refuse_receipt(what, "schema", taken["schema"],
                        ABANDONED_GATE_DISCHARGE_SCHEMA)
    boundaries.identity(taken["attempt_id"], f"{what}'s attempt")
    boundaries.identity(taken["operation_id"], f"{what}'s operation identity")
    boundaries.identity(taken["runtime_id"], f"{what}'s runtime identity")
    boundaries.text(taken["retention_policy_digest"],
                    f"{what}'s retention policy digest")
    boundaries.text(taken["gate"], f"{what}'s gate")
    cleanup = boundaries.document(
        taken["cleanup_operation"], f"{what}'s cleanup operation",
        required=("operation_id", "signature_digest"))
    boundaries.identity(cleanup["operation_id"],
                        f"{what}'s cleanup operation identity")
    boundaries.text(cleanup["signature_digest"],
                    f"{what}'s cleanup operation signature")
    # THE ASSIGNMENT IS OWNED BEFORE IT IS UNPACKED, on `_adopted_discharge`'s
    # rule: `**None` is a `TypeError` rather than a refusal, and a raw
    # exception at a persisted-input boundary bypasses the portable refusal
    # path every other reader uses.
    assignment = boundaries.document(
        taken["assignment"], f"{what}'s assignment",
        required=("work_ref", "participant", "generation"))
    work_ref = boundaries.document(
        assignment["work_ref"], f"{what}'s Work reference",
        required=("authority_uuid", "work_id"))
    documents.assignment(work_ref=documents.work_ref(**work_ref),
                         participant=assignment["participant"],
                         generation=assignment["generation"])
    derived = _quiescence_gate_token(assignment)
    if taken["gate"] != derived:
        _refuse_receipt(what, "gate", taken["gate"], derived)
    # THE EVIDENCE IS THE ONE THIS FAMILY CARRIES, and it names the runtime the
    # receipt itself is about rather than any runtime.
    evidence = boundaries.document(taken["evidence"], f"{what}'s evidence",
                                   required=("kind", "runtime"))
    if evidence["kind"] != RUNTIME_ABSENT:
        _refuse_receipt(what, "evidence kind", evidence["kind"], RUNTIME_ABSENT)
    if evidence["runtime"] != taken["runtime_id"]:
        _refuse_receipt(what, "evidence runtime", evidence["runtime"],
                        taken["runtime_id"])
    # THE AUTHORITY'S OWN ANSWER, held to the accepted gate-discharge
    # semantics and never manufactured: the port compared the gate and the
    # phase when the act ran, and this holds the journalled answer to exactly
    # the same three facts.
    answer = boundaries.document(
        taken["authority_receipt"], f"{what}'s authority answer",
        required=GATE_DISCHARGE)
    if answer["gate"] != taken["gate"]:
        _refuse_receipt(what, "authority gate", answer["gate"], taken["gate"])
    if answer["kind"] != RUNTIME_ABSENT:
        _refuse_receipt(what, "authority kind", answer["kind"], RUNTIME_ABSENT)
    if answer["phase"] != GATE_DISCHARGED_PHASE:
        _refuse_receipt(what, "authority phase", answer["phase"],
                        GATE_DISCHARGED_PHASE)
    if operation_id is not None and taken["operation_id"] != operation_id:
        _refuse_receipt(what, "operation identity", taken["operation_id"],
                        operation_id)
    if attempt_id is not None and taken["attempt_id"] != attempt_id:
        _refuse_receipt(what, "attempt", taken["attempt_id"], attempt_id)
    if expect is not None and assignment != expect:
        _refuse_receipt(what, "assignment", assignment, expect)
    if signature is not None and _abandoned_receipt_signature(taken) != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} composes a signature its own operands do not match the "
            f"one this manager committed for "
            f"{name_value(taken['operation_id'])}; the attempt, the "
            f"assignment, the gate, the runtime, the policy and the cleanup "
            f"operation are ONE signed relationship, and a receipt whose "
            f"members were changed individually cannot reproduce it")
    return taken


def _recorded_abandoned_discharge(store, attempt_id, operation_id):
    """The journal's committed abandoned discharge, or ABSENCE.

    ONE READER FOR BOTH PUBLIC EXITS, on the correction `_recorded_discharge`
    records: two spellings of one question are two answers to it. Absence is
    the only `None`; a present record this manager cannot own is an integrity
    failure an operator has to look at, and reporting it as absence would
    invite a consumer to re-run a remote act.
    """
    record = store.operation_record(operation_id)
    if record is None:
        return None
    if record["kind"] != ABANDONED_GATE_DISCHARGE_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names abandoned discharge "
            f"operation {name_value(operation_id)}, which this manager "
            f"committed as {name_value(record['kind'])}")
    _, committed = store.replay(operation_id, record["signature"],
                                kind=ABANDONED_GATE_DISCHARGE_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names abandoned discharge "
            f"operation {name_value(operation_id)}, which this manager "
            f"committed with no recorded answer to replay")
    return record, committed


def abandoned_gate_discharge_of(store, attempt_id):
    """The committed abandoned discharge for this attempt, or absence.

    THE DISCOVERABILITY HALF, and it is a read. It opens no session, takes no
    port and performs no external act. What it does NOT do is decide whether a
    discharge is owed: that depends on whether the Work is gated at all, which
    is the authority's fact and not this store's.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _fixed_assignment(attempt)
    if expect is None:
        return None
    operation_id = _abandoned_discharge_operation_id(attempt)
    held = _recorded_abandoned_discharge(store, attempt_id, operation_id)
    if held is None:
        return None
    record, committed = held
    return _adopted_abandoned_discharge(
        committed,
        f"attempt {name_value(attempt_id)}'s committed abandoned gate "
        f"discharge",
        operation_id=operation_id, signature=record["signature"],
        expect=expect, attempt_id=attempt_id)


def discharge_abandoned_quiescence_gate(store, port, *, attempt_id,
                                        retention_policy_digest):
    """Carry a committed ABANDONMENT's absence proof to the gate it installed.

    W128682. `abandon_attempt` fences the generation, and the authority
    installs `runtime-quiescence:<generation>` in that same transaction -- so
    an operator declaration leaves a Work gated with no ordinary ending
    anywhere in its future to discharge it. The abandonment DID positively
    observe the exact runtime absent; nothing carried that across.

    THE CALLER SELECTS AND SUPPLIES NOTHING ELSE, exactly as the ordinary act
    does. Its two operands are the attempt and the retention policy identity,
    and the second is only half the key that selects the committed removal.
    The authority, the Work, the participant, the generation, the gate token,
    the runtime identity and the absence evidence are all DERIVED from
    `abandonment_cleanup_of`'s validated answer.

    THE ORDER IS THE ORDINARY ACT'S, and each step is the next's precondition:

      1. own the operands, read the attempt, require its fixed assignment and
         prove this session acts for that assignment's participant;
      2. REPLAY an already committed discharge and return it, before anything
         mutable is read. A remote commit whose local receipt was lost must
         reproduce its answer even after the Work has moved on, and checking
         today's gate before recognising that replay would strand successful
         work;
      3. prove the committed abandoned cleanup and the exact runtime it
         observed absent;
      4. prove the whole Work reference, then ask the authority -- whose own
         equality check on the gate token is what refuses an old generation's
         evidence against a newer gate; and
      5. journal the answer under this act's own identity.

    FOUR AND FIVE CANNOT BE ONE TRANSACTION. The remote act commits first and
    the local receipt second; a crash between them leaves the authority's own
    replay to make the next attempt idempotent, which is what step two then
    records. Putting the remote call inside a local transaction would hold a
    write lock across a network act, and journalling first would record an act
    that may never have happened.

    IT DOES NOTHING ELSE, and the list is the design. No destruction, no
    runtime refresh, no reconciliation, no writer or line transition, no
    collection, no publication, no stage replacement, no checkout restore and
    no new authority policy. A timer is not a declaration and there is no
    timer here; the declaration already happened and this reads it.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    boundaries.capability(getattr(port, "satisfy_gate", None),
                          "the authority session's gate discharge")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)

    operation_id = _abandoned_discharge_operation_id(attempt)
    held = _recorded_abandoned_discharge(store, attempt_id, operation_id)
    if held is not None:
        record, committed = held
        replayed = _adopted_abandoned_discharge(
            committed,
            f"attempt {name_value(attempt_id)}'s replayed abandoned gate "
            f"discharge",
            operation_id=operation_id, signature=record["signature"],
            expect=expect, attempt_id=attempt_id)
        # REVIEW 2026-09-09T15-22-41Z [P2]: A CHANGED OPERAND COLLIDES.
        # The discharge identity is derived over the attempt and its fixed
        # assignment alone -- deliberately, so a resuming manager re-derives it
        # without the evidence -- which means the POLICY is not in it. So a
        # second call naming another policy selected this receipt and was
        # handed back somebody else's success, with no refusal and no sign
        # anything differed. The signature check could not catch it: it
        # recomposes the receipt's own members, and they are all consistent.
        #
        # COMPARED AGAINST THE RECEIPT AND NOTHING ELSE. Not against today's
        # cleanup row and not against the Work -- a replay must answer without
        # a mutable read, which is what makes the lost-receipt retry and the
        # later-generation replay work.
        if replayed["retention_policy_digest"] != retention_policy_digest:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"attempt {name_value(attempt_id)}'s committed abandoned gate "
                f"discharge was performed under retention policy "
                f"{name_value(replayed['retention_policy_digest'])} and this "
                f"call names "
                f"{name_value(retention_policy_digest)}; one identity carries "
                f"one act, and reusing it with a different operand changes "
                f"nothing (§4.2)")
        return replayed

    proof = abandonment_cleanup_of(
        store, attempt_id=attempt_id,
        retention_policy_digest=retention_policy_digest)
    if proof is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no committed abandoned "
            f"cleanup under retention policy "
            f"{name_value(retention_policy_digest)}; this gate is discharged "
            f"on the abandonment this manager committed and never on the "
            f"absence of one")
    runtime_id = proof["runtime_id"]
    gate = _quiescence_gate_token(expect)
    evidence = {"kind": RUNTIME_ABSENT, "runtime": runtime_id}
    cleanup_operation = dict(proof["cleanup"]["operation"])
    signature = manager_signature(ABANDONED_GATE_DISCHARGE_KIND, {
        "attempt_id": attempt_id, "expect": expect, "gate": gate,
        "runtime_id": runtime_id,
        "retention_policy_digest": retention_policy_digest,
        "cleanup_operation_id": cleanup_operation["operation_id"],
        "cleanup_signature_digest": cleanup_operation["signature_digest"]})
    # THE WHOLE WORK REFERENCE BEFORE THE REMOTE ACT, and AFTER the committed
    # replay above: this is a mutable remote read, and a discharge that already
    # committed must reproduce its answer without one.
    _same_authority(port, expect, attempt_id)
    answered = port.satisfy_gate(expect["work_ref"]["work_id"], operation_id,
                                 gate, evidence)
    if answered["kind"] != RUNTIME_ABSENT:
        raise ContractRefusal(
            "integrity", "schema",
            f"the authority answered evidence kind "
            f"{name_value(answered['kind'])} for attempt "
            f"{name_value(attempt_id)} and this act requires "
            f"{name_value(RUNTIME_ABSENT)}")
    # WHAT IS JOURNALLED IS WHAT THE AUTHORITY ANSWERED, adopted whole rather
    # than re-spelled: the port proved it is about the requested gate, and
    # recomposing its fields here would be writing a second account of
    # somebody else's answer.
    return store.transact(
        operation_id, ABANDONED_GATE_DISCHARGE_KIND, signature,
        lambda connection: _adopted_abandoned_discharge({
            "schema": ABANDONED_GATE_DISCHARGE_SCHEMA,
            "attempt_id": attempt_id,
            "assignment": expect,
            "runtime_id": runtime_id,
            "retention_policy_digest": retention_policy_digest,
            "cleanup_operation": cleanup_operation,
            "operation_id": operation_id,
            "gate": gate,
            "evidence": evidence,
            "authority_receipt": dict(answered),
        }, "an abandoned gate discharge receipt", operation_id=operation_id,
            signature=signature, expect=expect, attempt_id=attempt_id))


def _abandon_operation_id(attempt):
    """The ONE declaration identity for an attempt and its fixed generation.

    DERIVED FROM THE ATTEMPT AND THE ASSIGNMENT, and deliberately not from the
    reason or the runtime. Both of those ride the SIGNATURE instead, so a
    second declaration naming a different reason or a different attached
    runtime collides against this identity rather than committing a second
    abandonment of one attempt.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    return "attempt.abandon:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": _fixed_assignment(taken)})[len("sha256:"):]


def _abandon_fence_operation_id(attempt):
    """The authority's own effectively-once identity for this fence.

    DISTINCT FROM BOTH the declaration and `attempt.cancel:*`. An abandonment
    is not a cancellation and must not be able to replay one, and the
    declaration is this manager's record rather than the authority's act --
    three identities because they are three acts.

    SUPERSEDED IN PART, 2026-09-24, W247941, owner selection 255814. The
    sentence above -- "must not be able to replay one" -- was written for an
    attempt that has NOT been cancelled, and for that attempt it stands
    unchanged: this identity is still what a fresh declaration fences under.

    WHAT IT GOT WRONG is the case where a cancellation ALREADY fenced this
    exact generation. The Authority ends a generation once
    (`assignment generation was fenced and ended`), so a second identity over
    an already-fenced generation cannot fence anything -- it can only refuse.
    Measured on the preserved two-Job run: both attempts sit `quiescent` with
    `cleanup: pending`, a committed `attempt.cancel`, no intake receipt and a
    deadline pin whose policy is null, and every one of the three endings
    declines. The runtime, its two roots and the installed gate had no
    operation that could settle them.

    So the RESTRICTION IS NARROWED, not erased: an abandonment still never
    ISSUES a cancellation, and it still never infers a fence from an intent.
    When this attempt's own committed cancellation exists, the abandonment
    fences by REPLAYING that cancellation's Authority operation with its own
    reason and its own fixed assignment, and it acts only on the Authority's
    validated answer -- which is the shape `deadlines._cancel_for_deadline`
    already uses and this build already accepts. The abandonment's declaration
    and its reason stay separate and stay this manager's own record.

    THE DERIVATION HERE IS UNCHANGED, deliberately: `_abandon_intent` signs
    the fence identity it was given and validates it on replay, so an
    abandonment intent committed before this change replays against exactly
    the string it recorded. Nothing rewrites a journal.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    return "authority.abandon-fence:" + digest({
        "attempt_id": taken["runtime_attempt_id"],
        "assignment": _fixed_assignment(taken)})[len("sha256:"):]


def _committed_cancellation(store, attempt, attempt_id, expect):
    """THIS attempt's own committed cancellation, proved, or `None`.

    W247941, owner selection 255814. The abandonment fences an already-fenced
    generation by replaying the cancellation the Authority already accepted,
    and the only thing that may authorize such a replay is a record that is
    provably THIS attempt's.

    HELD TO EXACTLY WHAT `unstarted_cancellation_of` HOLDS ITS OWN COPY TO,
    and for the reason that reader states: "a well-formed row naming a foreign
    attempt and a foreign generation" must not prove this one. The identity is
    derived here from the attempt and its fixed assignment; the record must be
    `committed`, carry the `attempt.cancel` kind, decode to the exact intent
    document those operands compose, and carry the signature those same
    operands produce. The reason is the one member that is not derivable, so
    it is taken FROM the record and then used to recompute the canonical
    document and signature -- which is what makes taking it safe.

    ABSENCE IS `None` AND A DISAGREEMENT IS A REFUSAL. An attempt that was
    never cancelled is the ordinary case and fences under its own identity; a
    cancellation record this manager cannot account for is not something to
    fall back past, because falling back would fence under a second identity
    over a generation that may already be ended.
    """
    operation_id = attempts._cancel_operation_id(attempt)
    record = store.operation_record(operation_id)
    if record is None or record["state"] != "committed" \
            or record["kind"] != "attempt.cancel":
        return None
    authority_operation_id = attempts._authority_cancel_operation_id(attempt)
    try:
        recorded = json.loads(record["result"])
    except (TypeError, ValueError):
        recorded = None
    if type(recorded) is not dict:
        raise ContractRefusal(
            "refused", "precondition",
            f"the cancellation recorded at {name_value(operation_id)} "
            f"retained no intent document; an abandonment does not replay an "
            f"Authority operation it cannot account for")
    expected_intent = documents.cancel_intent(
        attempt_id=attempt_id, assignment=expect,
        authority_operation_id=authority_operation_id,
        reason=recorded.get("reason"))
    if recorded != expected_intent:
        parts = "; ".join(
            f"{member} {name_value(recorded.get(member))} where this attempt "
            f"names {name_value(expected_intent[member])}"
            for member in sorted(expected_intent)
            if recorded.get(member) != expected_intent[member])
        raise ContractRefusal(
            "refused", "precondition",
            f"the cancellation recorded at {name_value(operation_id)} names "
            f"{parts}; a committed intent is evidence about the attempt and "
            f"generation it actually names")
    expected_signature = manager_signature(
        "attempt.cancel",
        {"attempt_id": attempt_id, "expect": expect,
         "authority_operation_id": authority_operation_id,
         "reason": recorded.get("reason")})
    if record["signature"] != expected_signature:
        raise ContractRefusal(
            "refused", "precondition",
            f"the cancellation recorded at {name_value(operation_id)} carries "
            f"a signature this attempt's own operands do not produce; its "
            f"record was written over something else")
    return recorded


def _declared_fence_identity(store, attempt):
    """The fence operand a COMMITTED declaration already signed, or `None`.

    W247941 review 2026-09-24T10:11:35Z [P1]. The first cut of Correction A
    chose the declaration's fence operand from the world as it stands NOW, so
    an abandonment interrupted after its declaration committed and cancelled
    afterwards had its next identical request compose a different operand at
    the same `attempt.abandon:` identity -- and refuse at §4.2 with the
    cleanup still absent. "Keeping the identity derivation function unchanged
    does not preserve its selected operand when the call site now chooses a
    different identity."

    So the RECORD decides, and only a declaration that does not exist yet is
    free to choose. This reads the committed declaration's own operand back
    and hands it to `_abandon_intent`, which then signs and validates exactly
    what was written. Nothing is overwritten and no signature check is
    weakened: every other member of that record is still compared against the
    live attempt there.

    WHAT THIS IS NOT is fence evidence. The operand is the identity the
    declaration recorded; whether this generation is fenced, and under which
    Authority operation, is decided at the fence itself from the separately
    validated cancellation record and the Authority's own answer.
    """
    record = store.operation_record(_abandon_operation_id(attempt))
    if record is None or record["state"] != "committed" \
            or record["kind"] != "attempt.abandon":
        return None
    try:
        recorded = json.loads(record["result"])
    except (TypeError, ValueError):
        return None
    if type(recorded) is not dict:
        return None
    held = recorded.get("authority_operation_id")
    return held if type(held) is str and held else None


def _abandon_intent(store, attempt, attempt_id, expect, reason,
                    authority_operation_id, declare=None):
    """Commit or replay the declaration, and answer it with its digest.

    COMMITTED BEFORE ANY EXTERNAL CALL, which is what makes every later step
    resumable: the fence and the removal both read this rather than a caller's
    operands, so a crash between them resumes from what was declared instead
    of from what somebody remembers declaring.
    """
    operation_id = _abandon_operation_id(attempt)
    signature = manager_signature(
        "attempt.abandon",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"], "reason": reason,
         "authority_operation_id": authority_operation_id})
    document = documents.abandon_intent(
        attempt_id=attempt_id, assignment=dict(expect),
        runtime_id=attempt["runtime_id"], decision="abandoned",
        authority_operation_id=authority_operation_id, reason=reason)
    found, already = store.replay(operation_id, signature,
                                  kind="attempt.abandon")
    # FRESH ELIGIBILITY IS CHECKED ATOMICALLY WITH THE COMMIT, and only for a
    # FRESH declaration. Review 2026-08-30T11:44:55Z [P0]: the first cut
    # checked neither the worker nor the output at all and checked cleanup
    # only AFTER committing and fencing -- so a worker that had already
    # answered `completed` was destroyed and relabelled as operator-abandoned,
    # and an already-terminal cleanup could acquire a new declaration and a
    # new authority fence before the eventual refusal.
    #
    # INSIDE THE WRITE TRANSACTION, because "check then commit" is two acts
    # and an axis can move between them. A REPLAYED declaration deliberately
    # does not re-check: those axes have moved precisely because this ending
    # already ran, and a resumed call must be able to finish what it started.
    # W63255: WHICH ELIGIBILITY BODY, because the pre-attach fence commits an
    # extra fact in this same transaction and attached abandonment must not.
    # The default is unchanged, so `abandon_attempt` commits exactly what it
    # always did; a caller that needs more supplies it here rather than
    # running a second transaction the intent could be interleaved with.
    eligible = _declared if declare is None else declare
    committed = already if found else store.transact(
        operation_id, "attempt.abandon", signature,
        lambda connection: eligible(connection, attempt_id, document))
    held = boundaries.document(committed, "a committed abandonment record",
                               required=documents.ABANDON_INTENT)
    # READ BACK AS THE AUTHORIZATION, and held to the world it names. The
    # sibling records are checked this way for the reason this one is: a
    # record written when the attempt was attached to one container must not
    # authorize destroying a different one.
    # ALL SIX MEMBERS, not the four that name the world. Review
    # 2026-08-30T11:44:55Z [P1]: the first cut adopted the record and then
    # fenced with the caller's own freshly derived operation id and reason --
    # a parallel spelling of two members the record already carries. The
    # RECORD is the authorization, so every member of it is compared, and the
    # fence below uses what was adopted rather than what was recomputed.
    for member, mine in (("attempt_id", attempt_id),
                         ("assignment", _fixed_assignment(attempt)),
                         ("runtime_id", attempt["runtime_id"]),
                         ("decision", "abandoned"),
                         ("authority_operation_id", authority_operation_id),
                         ("reason", reason)):
        if held[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded abandonment names {member} "
                f"{name_value(held[member])} and this ending is for "
                f"{name_value(mine)}; the record and the act it authorizes "
                f"must describe one attempt, one runtime and one declaration")
    return {"document": held, "digest": digest(held)}


def _no_start_declared(connection, attempt_id, document):
    """W63255: the attached checks, PLUS the two this branch owns, PLUS the
    in-flight state that closes the race -- all in one transaction.

    THE RACE IS WHY THE STATE MOVES HERE. `request_runtime_start` commits a
    signed start only while it reads `not-started`, so a pre-attach fence that
    checked the axis and then fenced in a second statement could be overtaken
    between them: the authority generation would be fenced while a runtime it
    knows nothing about was starting, on a branch that owns no agent or
    runtime-stop capability. Moving the axis off `not-started` INSIDE the
    declaration's own transaction makes the two outcomes exclusive. If a start
    won, this refuses and fences nothing, and a fresh observation selects the
    attached branch. If this won, the start can no longer pass its own
    precondition.

    `cancel-requested` is the existing word for "an ending is in flight and no
    runtime is attached", which is exactly this state; nothing new is added to
    the closed axis.
    """
    attempt = _attempt_of(connection, attempt_id)
    if attempt["runtime_id"] is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has runtime "
            f"{name_value(attempt['runtime_id'])} attached; a pre-attach "
            f"fence ends an assignment whose runtime never started, and the "
            f"attached abandonment owns this one")
    if attempt["execution_runtime"] != "not-started":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} execution is "
            f"{name_value(attempt['execution_runtime'])}; a start has already "
            f"been requested, so this fence refuses rather than fencing an "
            f"assignment a runtime may be starting under")
    # THE ATTACHED CHECKS ARE THE SAME CHECKS, reused rather than restated.
    _declared(connection, attempt_id, document)
    connection.execute(
        "UPDATE attempts SET execution_runtime = 'cancel-requested' "
        "WHERE runtime_attempt_id = ? AND execution_runtime = 'not-started'",
        (attempt_id,))
    return document


def fence_pre_attach_abandonment(store, port, *, attempt_id, reason):
    """W63255: end the ASSIGNMENT of an attempt whose runtime never started.

    THE FIFTH ENDING, and the approved 2026-09-02 direction is why it is one.
    An operator's explicit abandonment of an interrupted pre-attach attempt had
    no path to the authority at all: the recovery proved the runtime absent and
    tore down credentials, then reported `resolved` from those resource facts
    while the exact assignment stayed live, with its Handler and generation
    still held. Runtime absence and credential teardown prove resources ended;
    they do not release assignment authority or participant capacity.

    IT IS NOT `abandon_attempt` WITH A PRECONDITION REMOVED. That operation
    requires an attached runtime, an abandoned-runtime destroy capability and
    directory custody, and weakening any of them would turn a no-runtime
    declaration into authorization for the W44716 runtime ending. It is not
    `request_cancellation` either: that validates agent and runtime-stop
    capabilities before it can discover there is nothing to stop, and a
    recovery branch that owns neither would have to invent them.

    WHAT IT DOES REUSE is the part that is genuinely the same act: the durable
    declaration keyed by the exact attempt and fixed assignment, its distinct
    authority operation identity, and the `AuthorityPort.cancel` crossing that
    proves the authority fenced this exact four-member assignment. The
    declaration commits BEFORE the external call, so a crash between them
    resumes from what was declared rather than from what a caller remembers.

    THIS DECIDES NOTHING ELSE. No output is frozen, no intake accepted, no
    retention chosen, no custody settled, no review or integration performed,
    and W61984's quiescent-finalization requirement is neither invoked nor
    relaxed. It answers the assignment question and stops.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    reason = boundaries.text(reason, "an abandonment reason")
    if not reason.strip():
        raise ContractRefusal(
            "integrity", "schema",
            "an abandonment carries the operator's own reason; calling this "
            "operation IS the declaration, so a blank one is a declaration "
            "nobody made")
    attempt = _attempt_of(store._connection, attempt_id)
    expect = _require_assignment(attempt, attempt_id)
    _require_participant(port, expect, attempt_id)
    # A CHEAP EARLY REFUSAL, and NOT the decision. `_no_start_declared` asks
    # both again inside the write transaction, where the answer cannot move
    # between the question and the commit. This one exists so the ordinary
    # wrong-branch call refuses without writing anything.
    if attempt["runtime_id"] is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has runtime "
            f"{name_value(attempt['runtime_id'])} attached; a pre-attach "
            f"fence ends an assignment whose runtime never started, and the "
            f"attached abandonment owns this one")
    authority_operation_id = _abandon_fence_operation_id(attempt)
    intent = _abandon_intent(store, attempt, attempt_id, expect, reason,
                             authority_operation_id,
                             declare=_no_start_declared)
    # FENCED WITH THE ADOPTED RECORD'S OWN VALUES, for `abandon_attempt`'s
    # reason: a resumed call must reissue the SAME authority operation with the
    # SAME reason, and reading them off the committed declaration is what makes
    # that true across a restart.
    fenced = port.cancel(dict(expect),
                         intent["document"]["authority_operation_id"],
                         intent["document"]["reason"],
                         expect["work_ref"]["work_id"],
                         expect["work_ref"]["authority_uuid"])
    return {"intent": intent["document"], "fenced": fenced}


def _declared(connection, attempt_id, document):
    """Prove the attempt is eligible to be abandoned, then answer the record.

    THE THREE THE CONTRACT NAMES, read inside the write transaction that
    commits the declaration. An attempt whose worker ANSWERED has an ending of
    its own and abandoning it would relabel what the worker said; an attempt
    whose output has moved off `open` is one this manager has already begun
    accounting for; and a terminal cleanup is not revisited.
    """
    attempt = _attempt_of(connection, attempt_id)
    if attempt["worker_disposition"] != "none":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has worker disposition "
            f"{name_value(attempt['worker_disposition'])}; abandonment ends "
            f"an attempt whose worker never answered, and this one did")
    if attempt["output"] != "open":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} output is "
            f"{name_value(attempt['output'])}; abandonment ends an attempt "
            f"this manager never began accounting for, and this one it did")
    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited, and a declaration is not recorded over one")
    return document


def _destroyed_abandoned(adapter, attempt, attempt_id, operation,
                         record_digest, retention_policy_digest, *,
                         seconds=None):
    """The abandonment crossing, under the same observation rules.

    THE WHOLE BODY CROSSES, as it does on both siblings: what makes this
    removal authorized rather than merely requested is the digest of the
    declaration, and the operation rides beside the body so the delivery is
    effectively-once at the adapter too.
    """
    command = {
        **documents.abandoned_destroy_command(
            assignment_ref=_fixed_assignment(attempt),
            runtime_attempt_id=attempt_id,
            runtime_id=attempt["runtime_id"],
            abandonment_record_digest=record_digest,
            retention_policy_digest=retention_policy_digest),
        "operation": dict(operation)}
    # THE COMMAND IS UNCHANGED AND THE ALLOWANCE RIDES BESIDE IT, never in it:
    # the command is what the durable identity is derived from, and execution
    # control must not enter a signed document. An adapter composed before
    # this allowance existed does not take the keyword, so an UNBOUNDED call
    # is byte for byte the call it always was.
    answer = boundaries.document(
        adapter.destroy_abandoned(command) if seconds is None
        else adapter.destroy_abandoned(command, seconds=seconds),
        "an abandoned-attempt destroy observation",
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


def _abandoned_destroy_operation(attempt, abandonment_record_digest,
                                 retention_policy_digest):
    """The `runtime.destroy-abandoned` identity.

    THE FOURTH SIBLING OF `destroy_operation`. The declaration's digest rides
    the identity exactly as the receipt's, the failure record's and the
    refusal's do: removing under a different declaration or a different policy
    is a different act, and a different retention policy after a terminal
    ending is refused without another engine call.
    """
    taken = boundaries.document(attempt, "a persisted attempt",
                                required=tuple(schema.ATTEMPT_COLUMNS))
    boundaries.text(abandonment_record_digest, "an abandonment record digest")
    boundaries.text(retention_policy_digest, "a retention policy digest")
    assignment = _fixed_assignment(taken)
    operands = {"attempt_id": taken["runtime_attempt_id"],
                "expect": assignment,
                "runtime_id": taken["runtime_id"],
                "abandonment_record_digest": abandonment_record_digest,
                "retention_policy_digest": retention_policy_digest}
    check_no_durable_secret({"kind": "runtime.destroy-abandoned",
                             "operands": operands},
                            what="an operation signature")
    # THE ID IS COMPOSED ONCE AND THEN BOUND INTO THE SIGNATURE, exactly as
    # `destroy_operation` and both recordless siblings do. Review
    # 2026-08-30T11:44:55Z [P1]: the first cut hashed the five body operands
    # alone, so the envelope did not carry the binding its own `operation`
    # contract promises -- and it did not mirror the siblings it says it
    # mirrors, which is worse than either alone.
    operation_id = "runtime.destroy-abandoned:" + digest(
        operands)[len("sha256:"):]
    return documents.operation(
        operation_id=operation_id,
        signature_digest=digest({
            "kind": "runtime.destroy-abandoned",
            "operands": {**operands, "operation_id": operation_id}}))


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


def _ending_capable(adapter, attempt_id):
    """EVERY CAPABILITY THIS ENDING WILL USE, typed BEFORE any destructive work.

    W285465 with OWNER-NO-AUTOMATIC-NORMALIZATION-20260928, and it KEEPS W43975's [P0]
    rule rather than relaxing it. That review's point is that a capability discovered after
    the world was mutated was never typed at all, so the seam is proved up front -- and
    which seam an ending needs depends on which ending it is:

      * a deployment that CAN normalize is held to exactly the accepted requirement, both
        halves of the custody seam, unchanged;
      * a deployment with NO custodian must still be able to establish that no writer
        survives, so its listing capability IS the seam and is typed here, in the same
        place and ahead of the same destructive work.

    A deployment with NEITHER is refused before the destroy is called, which is the
    condition the accepted guard protects: an ending that could not have been completed
    must not begin by removing a runtime.
    """
    # W285465 under OWNER-SIMPLE-COMPLETION-20260928: THE LISTING IS NO LONGER MANDATORY.
    #
    # The previous target required every selected ending to inventory hypothetical writers
    # after the exact confined container had already been observed absent, and this typed that
    # requirement at the entry. The owner's selected model is that confined Docker cessation
    # PROVES the confined writers stopped, so a deployment that offers no listing is not
    # thereby uncertain and must not be refused an ending.
    #
    # WHAT IS STILL TYPED: an adapter that OFFERS a listing must offer a callable one, because
    # `_record_writer_cessation` will ask it and a positively surviving writer still refuses.
    # A present-but-unusable capability would be discovered after the destroy, which is
    # exactly what W43975's [P0] rule forbids.
    offered = getattr(adapter, "surviving_helpers", None)
    if offered is not None:
        boundaries.capability(
            offered,
            f"the runtime adapter's writer-listing act, which attempt "
            f"{name_value(attempt_id)}'s ending asks when the deployment offers one")
    return adapter


def _custody_capable(adapter):
    """NO CALLERS as of W285465: kept as the historical seam's typed reader.

    Every ending this module owns now proves `_ending_capable` instead, because
    OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 removed the automatic launches this typed for.
    The rule it states is still the accepted one wherever a custody act IS performed, so it
    stays beside `_normalized` rather than being deleted with the callers.

    THE RULE IT STATES, unchanged: the mandatory custody seam, PROVED BEFORE ANY DESTRUCTIVE
    WORK.

    W43975 review 2026-08-30T15:21:44Z [P0]. `normalize_directory` and
    `custodian_image_digest` were first read inside `_normalized` -- after the
    runtime had been removed and both providers settled -- so a deployment
    missing the seam mutated the world and only then got a capability
    refusal. A capability discovered once durable state depends on it was not
    typed at all, which is the rule `AuthorityPort` states about its session
    and the reason it checks at construction.
    """
    boundaries.capability(getattr(adapter, "normalize_directory", None),
                          "the runtime adapter's directory-custody act")
    boundaries.text(getattr(adapter, "custodian_image_digest", None),
                    "the custodian image identity custody acts are signed "
                    "with")
    return adapter


def inaccessible_output(store, attempt_id, roots=None):
    """The FIRST entry the shared group cannot read, or `None` -- and it launches nothing.

    W285465, owner ruling OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 with DESIGN HOST-5.
    Slawomir selects SHARED-GROUP ACCESSIBLE job output: accessible output progresses
    with no normalization receipt at all, and inaccessible output is an ERROR that
    preserves the workspace. So the question this answers is the one the selected
    completion and recovery endings actually need, and it is a READ:

      * the configured workspace group is read from this manager's own record, never
        chosen by a caller -- the same capability `workspaces` mints for every other
        group-bearing act;
      * each entry under the governed roots is `lstat`ed with no follow, and what decides
        is whether THAT GROUP can reach it: `S_IRGRP` on files, and `S_IRGRP | S_IXGRP`
        on directories, since a directory without execute cannot be entered whatever its
        read bit says;
      * a symlink is reported rather than followed, because what a link points at is not
        what this manager provisioned.

    IT CHANGES NOTHING AND STARTS NOTHING. No chmod, no chown, no delete, no helper and
    no container -- the owner ruling forbids every one of those as a substitute, and a
    caller that gets an answer here reports the exact operation and preserves the bytes.
    """
    from . import workspaces as _workspaces

    boundaries.identity(attempt_id, "an assignment identity")
    group = _workspaces.configured_workspace_group(store).gid

    def unreachable(name, place, why, held=None):
        return {"root": name, "path": place, "group": group,
                "mode": None if held is None else stat.S_IMODE(held.st_mode),
                "gid": None if held is None else held.st_gid, "why": why}

    def reachable(name, place, held):
        """The group's own access to ONE entry, by mode and owning group."""
        if stat.S_ISLNK(held.st_mode):
            return unreachable(
                name, place,
                "a symlink is reported rather than followed; what it points at is not "
                "what this manager provisioned", held)
        needed = (stat.S_IRGRP | stat.S_IXGRP if stat.S_ISDIR(held.st_mode)
                  else stat.S_IRGRP)
        if held.st_gid != group or stat.S_IMODE(held.st_mode) & needed != needed:
            return unreachable(
                name, place,
                "the configured workspace group cannot read this entry, and this "
                "manager does not change permissions to make it readable", held)
        return None

    # W285465 review 2026-09-28T02-55-12Z: THE ROOTS ARE DERIVED, NOT ACCEPTED.
    #
    # My first cut took a caller mapping, so `roots={}` answered "accessible" -- it had
    # nothing to walk -- and a missing key was silently skipped while `S_ISDIR` was
    # treated as if it proved identity. None of that is an authenticated root. So both
    # governed roots are RE-OPENED from durable state through `custody._derived_root`,
    # which is the derivation eight review rounds of that module settled on, and a root
    # this manager cannot derive is REPORTED rather than skipped: an absence nobody has
    # evidenced is not success.
    from . import custody as _custody

    for name in ("result", "workspace"):
        try:
            place, _gid, _recorded = _custody._derived_root(store, attempt_id, name)
        except ContractRefusal as refused:
            return {"root": name, "path": None, "group": group, "mode": None,
                    "gid": None,
                    "why": f"this manager could not derive the {name} root from durable "
                           f"state ({refused.category}/{refused.code}), so its "
                           f"accessibility is not established: {refused}"}
        # A CALLER MAY STATE WHAT IT EXPECTS, AND IT IS COMPARED RATHER THAN TRUSTED.
        # `roots` is an EXPECTATION, never the identity: a supplied mapping must AGREE
        # with what was derived, and a substituted or omitted root is an ANSWER rather
        # than a skip -- which is what the unauthenticated version got wrong.
        if roots is not None:
            expected = roots.get(name) if hasattr(roots, "get") else None
            if expected is None or os.path.realpath(expected) != os.path.realpath(place):
                return {"root": name, "path": expected, "group": group, "mode": None,
                        "gid": None,
                        "why": f"the caller named {name_value(expected)} as this "
                               f"attempt's {name} root and durable state derives "
                               f"{name_value(place)}; a substituted or omitted root is "
                               f"refused rather than skipped"}
        # W285465 review 2026-09-28T02-50-56Z [P1]: THE ROOT ITSELF IS AN ENTRY. My first
        # cut walked only CHILDREN, so a root at 0700 -- unreachable, and empty because
        # nothing could be listed -- answered "accessible". A root nobody can enter is
        # the first thing that is inaccessible, not a special case.
        try:
            held = os.lstat(place)
        except OSError as failure:
            return unreachable(
                name, place,
                f"this manager could not observe the root at all "
                f"({type(failure).__name__}), so accessibility is not established")
        if not stat.S_ISDIR(held.st_mode) or stat.S_ISLNK(held.st_mode):
            return unreachable(
                name, place,
                "a governed root is the directory this manager provisioned; this is "
                "not one", held)
        refused = reachable(name, place, held)
        if refused is not None:
            return refused
        # AND A TRAVERSAL FAILURE IS AN ANSWER, NOT SILENCE. `os.walk` swallows errors by
        # default, so an unreadable subdirectory looked like an empty one -- the
        # reviewer's probe injected exactly that. `onerror` reports it instead.
        stumbled = []
        for walked, directories, files in os.walk(
                place, onerror=lambda failure: stumbled.append(failure)):
            if stumbled:
                break
            directories.sort()
            for entry in sorted(directories) + sorted(files):
                found = os.path.join(walked, entry)
                try:
                    held = os.lstat(found)
                except OSError as failure:
                    return unreachable(
                        name, found,
                        f"this manager could not observe this entry "
                        f"({type(failure).__name__}), so accessibility is not "
                        f"established")
                refused = reachable(name, found, held)
                if refused is not None:
                    return refused
        if stumbled:
            failure = stumbled[0]
            return unreachable(
                name, getattr(failure, "filename", place) or place,
                f"this manager could not traverse the output "
                f"({type(failure).__name__}), so accessibility is not established")
    return None


def _normalized(store, adapter, attempt_id, *, seconds=None, reclaim=None):
    """NO CALLERS as of W285465, and DELIBERATELY RETAINED.

    OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 removed the automatic launches from all five
    endings, so nothing in this module calls this. The reviewer notes the removal would be
    routine cleanup rather than an owner decision -- but it is not free: the immutable
    `review_configured_no_helper_20260928.py` and the owned configured-custodian case both
    PATCH THIS NAME to assert no helper is launched, so deleting it would break an artifact
    whose whole purpose is to hold this path to the ruling. It stays until those are
    superseded, and it is dead code on purpose rather than by oversight.

    WHAT IT DID, kept for the readers of its historical receipts: both roots, RESULT FIRST,
    before anything terminal is committed.

    W43975 review [P0] point 4 and 5. The order is the containment: `result`
    is nested BELOW `workspace`, so they are separately attributable custody
    subjects rather than two independent deletion trees, and normalizing the
    inner one first means the outer act never runs over a subject nobody has
    accounted for yet.

    OUTSIDE THE TRANSACTION, because each act runs a container. A helper
    invocation inside a write transaction would hold the control store open
    across an engine call, and the receipt each act commits is its own
    journalled operation anyway -- which is the whole reason a crash between
    the two loses nothing.
    """
    from . import custody as _custody

    for which in ("result", "workspace"):
        # ONE DECREASING ALLOWANCE ACROSS BOTH ROOTS. `seconds` is read at
        # each boundary rather than divided in advance, so the second root
        # gets what the first left rather than a fresh half.
        _custody.normalize_directory(store, adapter, assignment_id=attempt_id,
                                     which=which, seconds=seconds,
                                     reclaim=reclaim)


WRITER_CESSATION_KIND = "cleanup.writer-cessation"

# What the no-helper ending's own committed record carries. Every member is a FACT
# this manager observed, and there is no member for anything it merely believes.
WRITER_CESSATION = ("attempt_id", "container", "state", "exit_status", "why",
                    "workspace", "helpers", "established", "listing",
                    # W285465 review 2026-09-28T07-47-09Z: THE SCHEDULE, not only the
                    # subject. A container identity is reused across generations of the same
                    # attempt, so equality of containers alone cannot say WHICH run ceased.
                    # These two name it: the workspace generation this establishment was
                    # made over, and the start operation that generation journalled.
                    "generation", "launch")


def _writer_cessation_id(operation):
    """Bound to the DESTROY operation identity, which already covers the exact
    runtime, the intake receipt and the retention policy. So this evidence cannot be
    replayed onto another runtime, another receipt or another policy -- the attribution
    the review requires is inherited rather than re-invented.
    """
    return operation["operation_id"] + ":writer-cessation"


def _record_writer_cessation(store, adapter, attempt_id, *, attempt, operation,
                             observed, seconds=None, reclaim=None):
    """ESTABLISH and COMMIT what this completion observed about the EXECUTION. Nothing else.

    W285465 under the owner supersession recorded at 294568/294616 and read through DESIGN
    primary step 4, HOST-1/5, ART-7 and section 19. The selected sequence is now exactly four
    facts, and the third of them is what this function had wrong twice:

      1. the exact Docker runtime terminated;
      2. its observed EXECUTION status, durably recorded, with an UNKNOWN exit reported
         honestly -- an unknown exit is not an unknown termination and must not invent success
         or prevent release;
      3. the workspace PRESERVED AS IS -- no walk, no permission check, no manifest, no digest.
         Output validation belongs to the later, independently selected consumer. Container
         success is not output acceptance, and a scan here was an unselected prerequisite whose
         own errors could interrupt a completion that had already succeeded;
      4. the exact execution gate released.

    SO THERE IS NO OUTPUT OBSERVATION IN THIS RECORD AT ALL. The previous target's
    `inaccessible_output` and `_output_root_identities` calls are GONE from this path; both
    readers remain for the consumption that selects them. What is still refused is the
    cessation half: the exact runtime must be positively ABSENT, and a POSITIVELY SURVIVING
    writer -- an actually observed violation, asked only where a deployment offers a listing --
    still refuses. A missing or unreadable listing answer is recorded, not held, because
    confined container cessation is what proves the confined writers stopped.

    NOTHING HERE IS FABRICATED: no custody receipt, no helper, no claim about output.
    """
    from .store import manager_signature

    if observed.get("state") != "absent":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)}'s writer cessation cannot be "
            f"established while its runtime is {name_value(observed.get('state'))}; "
            f"only a positive absence of the exact runtime admits this evidence")
    surviving, unavailable = _surviving_writers(adapter, store, attempt_id,
                                               seconds=seconds, reclaim=reclaim)
    if unavailable is None and surviving:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"a writer of attempt {name_value(attempt_id)} still survives "
            f"({name_value(surviving[0].get('helper_identity'))}): "
            f"{surviving[0].get('why')}; the roots are left as they are")
    generation, launch = _ceased_schedule(store, attempt, attempt_id)
    document = {"attempt_id": attempt_id,
                "container": attempt["runtime_id"],
                "generation": generation,
                "launch": launch,
                "state": observed["state"],
                # THE OBSERVED EXECUTION STATUS, honestly. `exit_status` is whatever the
                # destroy observation carried; `None` means this manager does not know what the
                # execution exited with, which is a fact about the EXIT and not about the
                # termination -- so it neither invents success nor prevents release.
                "exit_status": observed.get("exit_status"),
                "why": observed.get("why"),
                # AND WHERE THE PRESERVED WORKSPACE IS, as a locator rather than an
                # observation: composed from this manager's configuration and the attempt
                # identity, with nothing read, walked or measured under it.
                "workspace": _expected_root(store, attempt_id, "workspace"),
                "helpers": [],
                "established": "container-cessation" if unavailable is not None
                else "container-cessation+listing",
                "listing": unavailable}
    return store.transact(_writer_cessation_id(operation), WRITER_CESSATION_KIND,
                          manager_signature(WRITER_CESSATION_KIND, document),
                          lambda _connection: dict(document))


def _surviving_writers(adapter, store, attempt_id, *, seconds=None, reclaim=None):
    """THE ONE CROSSING of `adapter.surviving_helpers`, answering `(surviving, missing)`.

    W285465: both no-helper endings -- the revoked generation's settlement and the ordinary
    completion -- need the same fact, and the boundary catalogue's rule is that a
    capability has one owner. Measured: calling it from both places directly took the
    inventory from 26 pending entries to 49 failures with "a capability with two crossings
    has two owners", which is the rule working. So the call lives here and the endings ask
    this.

    `missing` is a sentence rather than a bool because what the caller must not do is treat
    an unavailable capability as an absence; every caller refuses or holds on it.
    """
    asking = getattr(adapter, "surviving_helpers", None)
    if asking is None:
        return (), ("this deployment's adapter cannot establish whether any custody "
                    "writer survives")
    answered = asking(store, assignment_id=attempt_id, seconds=seconds,
                      reclaim=reclaim)
    # AND THE ANSWER IS VALIDATED HERE, at the crossing, not believed. Review
    # 2026-09-28T06-23-25Z: a callable that answered `None` was read as "no writers" and
    # committed a positive cleanup -- an UNKNOWN turned into a confirmed absence, which is
    # the one thing every ruling on this path forbids. So the shape decides: a list or
    # tuple of mappings is an OBSERVATION, and an empty one of those is the only thing that
    # means "none survive". Anything else -- `None`, `False`, a bare string, a mapping, a
    # sequence of non-mappings -- is an answer this manager cannot read, and an unreadable
    # answer holds exactly like a missing capability.
    if type(answered) not in (list, tuple):
        return (), (f"this deployment's adapter answered "
                    f"{name_value(answered)} when asked which custody writers survive, "
                    f"which is not an observation this manager can read")
    for one in answered:
        if not isinstance(one, dict):
            return (), (f"this deployment's adapter listed "
                        f"{name_value(one)} among the custody writers that survive, "
                        f"which is not an observation this manager can read")
    return tuple(answered), None


def _ceased_schedule(store, attempt, attempt_id):
    """WHICH workspace generation and start this establishment is about.

    W285465 review 2026-09-28T07-47-09Z: "container equality alone does not demonstrate
    schedules". A runtime identity can be the same across two generations of one attempt, so
    an establishment that named only the container could be adopted by a LATER generation's
    ownership transfer. These are read from the journal -- the generation outstanding over
    this attempt's pinned workspace object, and the start operation that generation
    journalled -- so the record says which run it saw end.

    REFUSES rather than recording an unbound establishment: if no generation is outstanding
    or it journalled no launch, there is no schedule to name and a record without one would
    be adoptable by anything.
    """
    from . import tokens as _tokens

    # `(None, None)` MEANS "THIS ENDING HAS NO GOVERNED RUN TO NAME", and review
    # 2026-09-28T07-55-48Z is right that the distinction has to be stated exactly, because my
    # first wording ran the two together.
    #
    # It is answered for an attempt whose workspace object was never PINNED -- so no
    # generation could ever have been taken over it -- or over which no generation stands at
    # all. Those are ungoverned endings, and they have no ownership for this ending to take
    # over: `_task_token_refusal` finds nothing outstanding and the admission needs no
    # transfer.
    #
    # IT IS NOT "the governed state is unknown". A governed attempt whose generation is
    # outstanding gets that generation named, and where this cannot name a single one --
    # more than one outstanding, or one that journalled no start -- the null it returns
    # AUTHORIZES NOTHING: `workspaces._ceased_generation` refuses to move ownership on a
    # record with a null schedule, so such an attempt keeps its roots held rather than being
    # treated as ungoverned.
    try:
        domain = _tokens.domain_of("workspace",
                                  _tokens.workspace_identity(attempt))
    except ContractRefusal:
        return None, None
    standing = list(_tokens.outstanding(store, domain))
    if len(standing) != 1:
        return None, None
    current = _tokens.token_of(store, domain, standing[0]["generation"])
    if current is None or current.get("launch") is None:
        return None, None
    return standing[0]["generation"], current["launch"]


def _output_root_places(store, attempt_id):
    """Each governed root's derived path, or its own UNKNOWN, as `(place, unknown)`.

    Review 2026-09-28T06-52-46Z: my previous cut swallowed the derivation refusal and turned
    it into `None`, which the establishment then recorded as "the root is gone". A manager
    that cannot say WHERE a root is has not observed that it is absent -- it has failed to
    look -- so the reason travels instead of being discarded.
    """
    from . import custody as _custody

    found = {}
    for which in _CUSTODY_ROOTS:
        try:
            found[which] = (_custody._derived_root(store, attempt_id, which)[0],
                            None)
        except ContractRefusal as refused:
            # A REFUSED DERIVATION IS NOT ONE FACT. `custody._derived_root` validates as
            # well as derives -- it refuses for an unconfigured store, a root that is not a
            # directory this manager created, AND for a root that is simply GONE, which is
            # the ordinary state after this ending's own removal. Telling those apart by
            # reading its sentence would be brittle, so this asks the one durable question
            # that decides it: is the attempt's home there at all? An absent home is an
            # EVIDENCED absence of everything under it; a home that exists beside a root
            # this manager cannot account for is UNKNOWN and holds.
            expected = _expected_root(store, attempt_id, which)
            if expected is None:
                found[which] = (None, f"this manager cannot derive the {which} root's "
                                      f"location at all ({refused})")
                continue
            try:
                os.lstat(expected)
            except FileNotFoundError:
                # AN EVIDENCED ABSENCE, ONCE THE ANCESTORS SAY SO: the object this attempt's
                # root would BE is not there, in a tree this manager can still recognise as
                # its own. That is the ordinary state after this ending's own removal and an
                # observation rather than a failure to look -- but ONLY when nothing on the
                # way down has been substituted. See `_unauthentic_ancestor`.
                unsound = _unauthentic_ancestor(store, expected)
                found[which] = (None, None) if unsound is None else (
                    None, f"the {which} root is missing and its path cannot be "
                          f"trusted: {unsound}")
                continue
            except OSError as failed:
                found[which] = (None, f"the {which} root could not be accounted for "
                                      f"({refused}) and {name_value(expected)} could not "
                                      f"be observed either "
                                      f"({type(failed).__name__}: {failed})")
                continue
            # IT IS THERE AND STILL COULD NOT BE ACCOUNTED FOR -- a foreign owner, a
            # symlink, something that is not a directory. That is exactly what must hold.
            found[which] = (None, f"the {which} root at {name_value(expected)} is present "
                                  f"and this manager cannot account for it ({refused})")
    return found


def _expected_root(store, attempt_id, which):
    """Where this attempt's `which` root WOULD be, from configuration alone, or `None`.

    The same two operands `custody._derived_root` composes from -- the manager's own
    configured workspace store and the attempt identity -- and the same layout, with none of
    its validation. It selects no path of a caller's choosing and answers exactly one
    question: is the object that root would be actually there? That is what separates an
    EVIDENCED removal from a root this manager merely failed to account for, and reading
    `_derived_root`'s sentence to tell them apart would have been brittle.
    """
    from . import workspaces as _workspaces

    try:
        storage = _workspaces.configured_workspace_storage(store)
    except ContractRefusal:
        return None
    workspace = os.path.join(storage.place, attempt_id, "workspace")
    return workspace if which == "workspace" \
        else os.path.join(workspace, f"result-{attempt_id}")


def _unauthentic_ancestor(store, place):
    """Why `place`'s ANCESTORS cannot authenticate an absence below them, or `None`.

    W285465 review 2026-09-28T08-03-34Z, and the hole it closes is exact. `os.lstat` does not
    follow the LAST component and follows every one before it, so with the attempt home
    renamed aside and a symlink to an empty foreign directory left at its path, an `lstat` of
    `<home>/workspace` resolved THROUGH that link, answered `ENOENT` inside somebody else's
    directory, and this module recorded "both roots absent". A missing child seen through a
    substituted parent is not an absence -- it is a different tree.

    So the ancestors are authenticated before any `ENOENT` below them is believed. Every
    component from the configured workspace store down to `place`'s parent must be either:

      * a real directory that is NOT a symlink -- proved with `lstat`, which asks about the
        entry itself; or
      * ABSENT, in which case nothing can exist below it and the child's absence follows.
        `discard_execution_roots` leaves exactly that state, which is why the accepted
        post-removal retry still works.

    Anything else -- a symlink, a file, an entry this manager cannot observe -- is an answer
    about a tree that is not the one it prepared, and it is REPORTED so the caller refuses.
    Nothing here follows a link, changes a permission or deletes anything.
    """
    from . import workspaces as _workspaces

    try:
        storage = _workspaces.configured_workspace_storage(store)
    except ContractRefusal as refused:
        return f"this manager has no configured workspace store ({refused})"
    root = storage.place
    if not place.startswith(root + os.sep):
        return (f"the expected root {name_value(place)} is not inside this manager's "
                f"configured workspace store")
    walked = root
    for name in os.path.relpath(os.path.dirname(place), root).split(os.sep):
        if name in ("", os.curdir):
            continue
        walked = os.path.join(walked, name)
        try:
            held = os.lstat(walked)
        except FileNotFoundError:
            # AN ABSENT ANCESTOR AUTHENTICATES THE ABSENCE BELOW IT: nothing exists under a
            # directory that is not there, and this is the ordinary post-removal state.
            return None
        except OSError as failed:
            return (f"{name_value(walked)} could not be observed "
                    f"({type(failed).__name__}: {failed})")
        if stat.S_ISLNK(held.st_mode):
            return (f"{name_value(walked)} is a symbolic link, so an answer about what is "
                    f"below it is an answer about another tree")
        if not stat.S_ISDIR(held.st_mode):
            return f"{name_value(walked)} is not a directory this manager prepared"
    return None


def _output_root_identities(store, attempt_id):
    """Each governed root's `device:inode`, `None` for EVIDENCED absence, or a refusal.

    W285465 review 2026-09-28T06-52-46Z, and the distinction it turns on: `None` here is a
    POSITIVE OBSERVATION that the object is not there -- which is what lets the retry after
    a crash between the removal and the terminal commit finish -- and it may only ever come
    from an answer that says so. `ENOENT` says so. A derivation this manager cannot perform
    does not, and neither does `EACCES`, `ELOOP`, `ENOTDIR` or any other error: those are
    failures to look, and recording one as an absence would be the same class of defect as
    reading an unreadable listing answer as "no writers".

    So anything that is not an object and not an evidenced absence REFUSES, and the caller
    holds. The refusal names which root and why.
    """
    found = {}
    for which, (place, unknown) in _output_root_places(store, attempt_id).items():
        if unknown is not None:
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"attempt {name_value(attempt_id)}'s output cannot be accounted for: "
                f"{unknown}; an absence nobody has evidenced is not one this ending may "
                f"record")
        if place is None:
            # THE DERIVATION REFUSED AND THE OBJECT IT WOULD BE IS NOT THERE: an evidenced
            # absence, already established by `_output_root_places`, with nothing left to
            # `lstat`.
            found[which] = None
            continue
        try:
            held = os.lstat(place)
        except FileNotFoundError:
            # THE ONE ANSWER THAT IS AN OBSERVATION -- once the path it was asked along is
            # this manager's own. A child missing under a SUBSTITUTED parent is an answer
            # about somebody else's tree, and review 2026-09-28T08-03-34Z measured exactly
            # that: `lstat` follows every component but the last.
            unsound = _unauthentic_ancestor(store, place)
            if unsound is not None:
                raise ContractRefusal(
                    "runtime-observation", "quiescence-unknown",
                    f"attempt {name_value(attempt_id)}'s {which} root is missing at "
                    f"{name_value(place)} and its path cannot be trusted: {unsound}; a "
                    f"child missing under a substituted parent is not an absence this "
                    f"ending may record") from None
            found[which] = None
            continue
        except OSError as failed:
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"attempt {name_value(attempt_id)}'s {which} root at "
                f"{name_value(place)} could not be observed ({type(failed).__name__}: "
                f"{failed}); this manager does not read a failure to look as an absence, "
                f"and the roots are left exactly as they are") from None
        found[which] = f"{held.st_dev}:{held.st_ino}"
    return found


def historical_writer_cessation(store, operation):
    """The COMMITTED no-helper evidence for this destroy, or `None`.

    A READER, and the reason it exists is the same one `_adopted_custody` gives: the
    ending must name an act this manager can show it journalled, never a document the
    caller happens to be holding.
    """
    record = store.operation_record(_writer_cessation_id(operation))
    if record is None or record["kind"] != WRITER_CESSATION_KIND \
            or record["state"] != "committed":
        return None
    try:
        recorded = json.loads(record["result"])
    except (TypeError, ValueError):
        raise ContractRefusal(
            "integrity", "schema",
            "the committed writer cessation for this destroy is unreadable") from None
    return boundaries.document(recorded, "a committed writer cessation",
                               required=WRITER_CESSATION)


def _adopted_custody(store, adapter, attempt_id, prepared_store=None):
    """The two receipts, READ BACK, as the terminal claim's own evidence.

    Never the answers the caller happens to be holding: a caller-held document
    is one the caller composed, and what makes the terminal claim worth
    anything is that it names acts this manager can show it journalled.

    W270664 F2: `prepared_store` is passed straight through to each receipt
    read, and it is what keeps this loop from asking the filesystem three
    times per root while its caller holds a write lock.
    """
    from . import custody as _custody

    adopted = {}
    for which in ("result", "workspace"):
        receipt = _custody.adopted_directory_custody(store, adapter,
                                                     attempt_id, which,
                                                     prepared_store)
        if receipt is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} has no committed "
                f"directory-custody receipt for its {which} root; an ending is "
                f"not claimed on a normalization this manager cannot show it "
                f"performed")
        adopted[which] = receipt
    return adopted


def _authorize_deadline_cleanup(store, adapter, *, command, fence):
    """Receiptless deadline cleanup, reusing exact removal and retained custody.

    Only the deadline owner composes this command from its reached observation
    and matching Authority cancellation. No abandonment or worker disposition
    is written. Output eligibility is checked after each external boundary and
    again in the settlement transaction; concurrent output keeps its own owner.
    """
    from . import deadlines

    taken = boundaries.document(command, "a deadline cleanup authorization",
                                required=deadlines.DESTROY)
    attempt_id = taken["runtime_attempt_id"]
    operation = deadlines._operation(taken)
    signature = manager_signature("runtime.destroy-deadline", taken)
    found, already = store.replay(operation["operation_id"], signature, kind="runtime.destroy-deadline")
    if found:
        return already

    def eligible():
        current = _attempt_of(store._connection, attempt_id)
        if _fixed_assignment(current) != taken["assignment_ref"] or current["runtime_id"] != taken["runtime_id"]:
            raise ContractRefusal("refused", "precondition", "deadline cleanup identity changed")
        if current["cleanup"] not in ("pending", "blocked-on-intake"):
            raise ContractRefusal("refused", "already-terminal", "deadline cleanup is already terminal")
        if current["worker_disposition"] != "none" or current["output"] != "open":
            raise ContractRefusal("refused", "precondition", "deadline cleanup waits for the existing output owner")
        if current["execution_runtime"] == "uncertain":
            raise ContractRefusal("runtime-observation", "quiescence-unknown", "deadline cleanup waits for exact runtime reconciliation")
        return current

    # The intent is fixed independently from the removal result. A failed or
    # uncertain removal never becomes a permanent replay of an unsettled result.
    authorization_id = "runtime.deadline-cleanup-authorized:" + digest(taken)[len("sha256:"):]

    def authorize(connection):
        eligible()
        return dict(taken)

    authorized = store.transact(authorization_id, "runtime.deadline-cleanup-authorized",
        manager_signature("runtime.deadline-cleanup-authorized", taken), authorize)
    if authorized != taken:
        raise ContractRefusal("integrity", "schema", "deadline cleanup authorization differs from its command")
    current = eligible()
    observed = deadlines._destroy_observation(
        adapter.destroy_deadline({**documents.deadline_destroy_command(**taken), "operation": operation}),
        taken["runtime_id"])
    eligible()
    pending = _not_an_ending(store, current, attempt_id, observed, operation)
    if pending is not None:
        return documents.deadline_cleanup(command=taken, fence=fence, observed=observed, cleanup=pending)
    # W285465: AND THE DEADLINE ENDING, on the same rule. `current` is this attempt's row as
    # the eligibility read left it, which is what names the container the establishment is
    # about.
    if observed["state"] == "absent":
        _record_writer_cessation(store, adapter, attempt_id, attempt=current,
                                 operation=operation, observed=observed)

    def settle(connection):
        eligible()
        return documents.deadline_cleanup(command=taken, fence=fence, observed=observed,
            cleanup=_settle_recordless_cleanup(store, connection, attempt_id, observed, operation,
                why="deadline cleanup settled retained", custody=adapter))

    return store.transact(operation["operation_id"], "runtime.destroy-deadline", signature, settle)


def _preserved_ending(store, connection, attempt_id, observed, operation,
                      ending, kept, receipt):
    """The ordinary ending that REMOVED NOTHING, settled and recorded.

    W285465 under OWNER-SIMPLE-COMPLETION-20260928. An establishment that recorded
    `inaccessible` preserves the material, so this path takes no cleanup admission and calls
    no removal -- and therefore has no admission to settle and no store measurement to sign a
    receipt under. What it still does is what the ruling asks for: record the ACTUAL outcome,
    which is `retained` over material this manager could not read, with `directory_custody`
    null because no custody act was performed.

    The axis moves and the lane is NOT released here: reuse of a workspace whose bytes are
    preserved is exactly what the ruling separates from execution release, and the resource
    return is `_released`'s decision on the cessation facts.
    """
    observe(store, attempt_id=attempt_id, axis="cleanup", value=ending)
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup=ending, state=observed["state"],
        why=observed["why"], kept=list(kept), operation=dict(operation),
        directory_custody=None)


def _settle_recordless_cleanup(store, connection, attempt_id, observed,
                               operation, *, why, custody=None):
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
        # A POSITIVELY SURVIVING RUNTIME NEEDS NO DIRECTORY ACT. No removal and
        # no retention claim follows from it, so there is nothing for a custody
        # receipt to authorize.
        observe(store, attempt_id=attempt_id, axis="cleanup", value="failed")
        return documents.cleanup_settled(
            attempt_id=attempt_id, cleanup="failed", state=state,
            why=observed["why"], kept=[], operation=dict(operation),
            directory_custody=None)
    # W285465: THE RECORDLESS ENDING READS AN ACT THIS MANAGER COMMITTED, and which act
    # depends on which sibling this is.
    #
    # The ABANDONMENT path now establishes a writer cessation and launches no helper, so its
    # evidence is that record, read back here exactly as the ordinary completion reads its
    # own -- a document this frame is holding is one this frame composed. The failed-start and
    # refused-session siblings still normalize, and this function is shared with them, so
    # their receipts are still what they rest on: converting them is the next piece of work
    # and breaking them to get there would be worse than either.
    #
    # NEITHER present is an ending resting on nothing, and that refuses.
    ceased = historical_writer_cessation(store, operation)
    adopted = None
    if ceased is None:
        adopted = _adopted_custody(store, custody, attempt_id)
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    observe(store, attempt_id=attempt_id, axis="cleanup", value="retained")
    # W266336 stage 2 [P1], review 2026-09-25T18-36-24Z: A PENDING SUBMITTER
    # KEEPS THE RESERVATION, whatever anybody else can see.
    #
    # Absence plus every provider ending is what this release has always
    # required, and all of it can be established by a manager that is NOT the one
    # holding the start call. A second handle cancelled, reconciled and ended an
    # attempt while the original `adapter.start` had not returned, and the lane
    # went with it -- so reuse was ordered behind an observation rather than
    # behind the submitter. `start_submission_returned` is the submitter's own
    # record, which nobody else can write.
    #
    # THE REFUSAL IS NON-DURABLE ON PURPOSE: the whole settlement rolls back, so
    # the reservation, the axis and the cleanup state stay exactly as they were
    # and the ending is retryable once the submitter comes back.
    if not attempts.start_submission_returned(store, attempt):
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)}'s start submission has not "
            f"returned to the manager that made it; a reservation is not given "
            f"back on somebody else's observation of the runtime, because the "
            f"submitter may still act")
    # W32649: the lane is given back only after positive absence and every
    # applicable provider ending -- reuse is ordered behind the proof, not
    # beside it.
    lanes._release_lane(connection, attempt_id=attempt_id,
                        reference=lanes.lane_reference(attempt), why=why)
    # THE HOME IS RETAINED AND NOT REMOVED. Both recordless endings keep the
    # untrusted result directory -- that is what `retained` MEANS here -- so
    # they commit the two receipts and call no removal at all.
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup="retained", state=state,
        why=observed["why"], kept=[], operation=dict(operation),
        directory_custody=adopted)


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
            observed, operation, custody=None, prepared_store=None,
            admitted_cleanup=None, preserved=False):
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
            why=observed["why"], kept=[], operation=dict(operation),
            directory_custody=None)
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    kept = tuple(one["artifact_id"] for one in retentions_of(store, attempt_id)
                 if one["disposition"] in KEEPS_MATERIAL)
    # `retained` AND `complete` ARE DIFFERENT ENDINGS. Anything kept -- by
    # policy or by quarantine -- ends `retained`, because reporting kept
    # material as cleaned up would erase the reason it still exists. Only a
    # cleanup with nothing left behind is `complete`.
    # W285465 under OWNER-SIMPLE-COMPLETION-20260928: AND MATERIAL PRESERVED BECAUSE IT COULD
    # NOT BE READ. `preserved` is set when the committed establishment recorded `inaccessible`,
    # and this ending removed nothing -- so reporting `complete` would say the roots are gone
    # when they are exactly where they were.
    ending = "retained" if kept or receipt["custody"] == "quarantined" \
        or preserved else "complete"
    # W270664 F2: THE STORE WAS MEASURED BEFORE THIS TRANSACTION OPENED, and the
    # absence of it is a WIRING failure rather than a deployment one.
    #
    # Review 2026-09-26T08:43:12Z traced all six of this ending's locked
    # filesystem calls to the receipt reads below: each derived its signature
    # operand by validating the configured store on disk, three `lstat` calls
    # per root. `authorize_cleanup` now validates it once, outside, and hands
    # the frozen answer in; `recorded_storage_place` rebinds it here against
    # the journal and refuses it if the configuration moved in between.
    #
    # THIS REFUSAL IS WHY THERE IS NO SILENT WAY BACK. A default of `None`
    # would let a future caller fall back to the locked reader and nothing
    # would fail -- which is exactly how I shipped the earlier hoist that
    # measured unchanged. An unprepared ending fails here instead.
    # W285465 under OWNER-SIMPLE-COMPLETION-20260928: A PRESERVING ENDING MEASURED NO STORE,
    # because it performed no directory act to sign a receipt for. The wiring rule this guard
    # states is about the ending that REMOVES; requiring a measurement from one that preserves
    # would be requiring evidence of an act the ruling forbids it to perform.
    if prepared_store is None and not preserved:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)}'s ending was reached without the "
            f"workspace store its receipts are signed under having been measured "
            f"outside this transaction; the ending does not validate directories "
            f"while it holds this manager's write lock")
    # W285465: THE NO-HELPER ENDING READS ITS OWN COMMITTED EVIDENCE, and it reads it out
    # of the journal exactly as `_adopted_custody` reads normalization receipts -- for the
    # same reason, which is that a document this frame is holding is one this frame
    # composed. `authorize_cleanup` established and committed it before the removal and
    # before this transaction; an ending that finds nothing committed REFUSES rather than
    # claiming an absence no act recorded.
    ceased = historical_writer_cessation(store, operation)
    if ceased is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no committed writer cessation for "
            f"this destroy, so whether any writer of its roots survives is UNKNOWN; "
            f"the ending waits for the establishment rather than claiming it")
    adopted = None
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
    # W266336 stage 2 [P1], review 2026-09-25T18-36-24Z: A PENDING SUBMITTER
    # KEEPS THE RESERVATION, whatever anybody else can see.
    #
    # Absence plus every provider ending is what this release has always
    # required, and all of it can be established by a manager that is NOT the one
    # holding the start call. A second handle cancelled, reconciled and ended an
    # attempt while the original `adapter.start` had not returned, and the lane
    # went with it -- so reuse was ordered behind an observation rather than
    # behind the submitter. `start_submission_returned` is the submitter's own
    # record, which nobody else can write.
    #
    # THE REFUSAL IS NON-DURABLE ON PURPOSE: the whole settlement rolls back, so
    # the reservation, the axis and the cleanup state stay exactly as they were
    # and the ending is retryable once the submitter comes back.
    if not attempts.start_submission_returned(store, attempt):
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)}'s start submission has not "
            f"returned to the manager that made it; a reservation is not given "
            f"back on somebody else's observation of the runtime, because the "
            f"submitter may still act")
    lanes._release_lane(connection, attempt_id=attempt_id,
                       reference=lanes.lane_reference(attempt),
                       why=f"cleanup settled {ending}")
    # W270664 F2, review 2026-09-26T09:15:26Z: AND THE CLEANUP'S EXCLUSION ENDS IN THIS
    # SAME WRITE, which is the whole point of settling it here rather than anywhere else.
    #
    # The admission was taken in `authorize_cleanup` before the removal; from there to
    # this line the attempt's roots are nobody else's to allocate, adopt or remove, and
    # the window the reviewer's probe exploited does not exist. A rollback of this ending
    # rolls the settlement back with it and the roots stay held; a crash before it leaves
    # the admission standing, which is the held state this Work requires of every
    # interruption. IT IS PURE DATABASE WORK under a lock this transaction already holds,
    # so it does not reintroduce the defect F2 is about.
    #
    # THE SAME WIRING RULE AS THE PREPARED STORE: no silent fallback. An absent admission
    # on this path means the ending was reached without the exclusion ever being taken.
    # W285465 under OWNER-SIMPLE-COMPLETION-20260928: AND THERE IS NO REMOVAL TO OWN when the
    # ending PRESERVES. The rule this states is about the window between a removal and this
    # commit; a preserving ending performs no removal, took no admission deliberately, and
    # settles an exclusion nobody needed. Demanding one would be demanding that it acquire
    # ownership in order to delete nothing.
    if admitted_cleanup is None and not preserved:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)}'s ending was reached without a cleanup "
            f"admission, so nothing owned its roots between the removal and this "
            f"commit; an ending does not settle an exclusion it never took")
    from .workspaces import settle_cleanup

    if admitted_cleanup is None:
        return _preserved_ending(store, connection, attempt_id, observed,
                                 operation, ending, kept, receipt)
    settle_cleanup(store, connection, attempt_id, admitted_cleanup,
                   f"cleaning up attempt {name_value(attempt_id)}")
    # THE ONE ORDINARY REMOVAL, ORDERED BEHIND BOTH RECEIPTS.
    #
    # W43975 review [P0] point 5, as CORRECTED by review 2026-08-30T15:21:44Z.
    # "Contained" was always the operative word and the container was wrong:
    # this removed the whole attempt HOME, which also holds `custody` -- where
    # intaken material lives -- so a `retained` ending deleted the very
    # locators it said were kept, and in the real-engine gate reached a
    # sibling attempt's credential root. `result` is nested below `workspace`,
    # so removing the two execution roots is still ONE contained removal
    # rather than two independent deletion trees -- and it happens only after both roots are normalized and
    # both receipts adopted, because a removal is the act those receipts
    # authorize. A crash after either helper act replays or re-performs that
    # act; a crash after this removal replays both receipts, observes the home
    # already absent, and commits the ending. `discard_workspace` is
    # recoverable rather than exact for exactly that reason.
    # W270664 F2: THE REMOVAL IS NO LONGER PERFORMED HERE. It ran inside this transaction --
    # the whole of F2's enclosing entry -- and now happens in `authorize_cleanup`, after the
    # eligibility this ending rests on and before this commit, with no database lock held.
    # W257624 R3's operand requirement is unchanged; it moved with the call.
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup=ending, state=state,
        why=observed["why"], kept=list(kept), operation=dict(operation),
        # W285465: THE DOCUMENT IS EXACTLY WHAT THE FROZEN `cleanup.settled` CONTRACT
        # NAMES, and that is a correction: my first cut carried the no-helper evidence as a
        # new member here and the contract refused it -- "a cleanup.settled document
        # carrying writer_cessation, which its contract does not name". Adding a member to
        # a frozen contract is a DESIGN change and not mine to make, so the evidence lives
        # where it was already committed: its own journalled operation, bound to this
        # destroy's identity, which `historical_writer_cessation` reads back by identity.
        # Nothing about the ending is weaker for it -- `_settle` above refuses without that
        # record, and `_released` consults the same one.
        directory_custody=adopted)


# -- W275774: RECLAIMING AN OVERDUE RESOURCE, in four acts --------------------


def reclaim_operation_id(attempt, generation):
    """This reclaim's OWN operation identity, derived and receipt-free.

    W275774 review 16:55:05Z [P1]: the first cut reused `destroy_operation`, which
    legitimately requires an intake receipt -- and a RUNNING attempt has none. So the
    reclaim committed its revocation and then refused on that schema BEFORE calling
    the engine at all: revoked, and nothing stopped. Weakening the ordinary cleanup's
    receipt contract would have been the wrong repair, because that contract is what
    makes a cleanup authorized. A reclaim is simply not a cleanup: it performs no
    intake and claims no retention, so it carries its own identity instead of
    borrowing one whose preconditions it cannot meet.
    """
    # THE TWO MEMBERS THIS IDENTITY IS MADE OF, and the row carries many more, so
    # the shape is checked by reading them rather than by an exact-membership
    # document check -- a persisted attempt row is not a caller document.
    boundaries.identity(attempt["runtime_attempt_id"], "an attempt identity")
    boundaries.identity(attempt["runtime_id"], "a runtime identity")
    taken = attempt
    return "resource.reclaim:" + digest({
        "kind": "resource.reclaim",
        "attempt_id": taken["runtime_attempt_id"],
        "runtime_id": taken["runtime_id"],
        "generation": generation})


def reclaim_expired_resource(store, adapter, *, attempt_id, govern):
    """Revoke, STOP, positively confirm, then settle -- in that order.

    Review 16:37:09Z selected this as the basic host expiry, and 16:55:05Z corrected
    its shape. Expiry is not self-executing: an overdue generation stops being
    ENTITLED to act, and the container it governs may still be running with the
    workspace still mounted writable. So reclaiming is four acts and the order is the
    content:

      1. REVOKE, durably and first, so the old holder is refused at its next
         journal-guarded step rather than racing this reclaim. Only an expired
         generation can be revoked.
      2. STOP the exact container, through the adapter's `stop` -- NOT the ordinary
         cleanup's `destroy`, which is receipt-bound and which a running attempt
         could not satisfy. **EXTERNAL I/O BETWEEN TRANSACTIONS**: the revocation
         above committed and closed, and the settlement below opens its own.
      3. POSITIVELY CONFIRM, by asking the adapter what that exact identity now is.
         Anything other than a positive absence or quiescence proves nothing.
      4. SETTLE, which is the ordinary return on the custody this manager already
         committed for the governed roots.

    An unknown or delayed outcome answers `held`: the generation stays revoked and
    the resource stays held, which is why step 1 is not conditional on step 3.
    """
    # W275774 review 2026-09-26T20-07-17Z: THE EXPIRY STOP IS ITS OWN CAPABILITY.
    # This crossed `stop`, which `attempts._order_quiescence` already owns, so one
    # capability had two crossing owners -- and the two acts are not the same act:
    # a cancellation's stop follows an authority fence, and this one follows an
    # overdue token generation with no fence and no receipt anywhere. Routing a
    # sweep through the cancellation's owner would drag that fence into it, which
    # is the shape this narrower verb exists to avoid.
    boundaries.capability(getattr(adapter, "stop_expired", None),
                          "the runtime adapter's expiry stop")
    attempt = _attempt_of(store._connection, attempt_id)
    operation_id = attempts._start_operation_id(attempt)
    overdue = govern.overdue(store, attempt, operation=operation_id)
    if overdue is None:
        return {"reclaimed": "not-overdue", "attempt_id": attempt_id}
    if attempt["runtime_id"] is None:
        # W275774 review 17:09:10Z [P1]: NO ATTACHED IDENTITY IS NOT "NEVER LAUNCHED".
        #
        # I wrote that inference and it is wrong in the one direction that matters: a
        # launch may have crossed to the engine and its reply may have been lost, so
        # `runtime_id is None` can mean a container this manager cannot name is
        # running right now with the workspace mounted writable. That is the
        # unknown/delayed launch case, and inferring absence from it would free a
        # resource that is still being written.
        #
        # So the TOKEN'S OWN LAUNCH EVIDENCE decides which of the two this is, and the
        # answer carries it either way. The entitlement is withdrawn in both -- an
        # overdue holder stops being entitled regardless -- and the resource stays
        # held, because neither case has a cessation to confirm.
        govern.revoke(store, attempt, operation=operation_id)
        launched = overdue.get("launch") is not None
        return {"reclaimed": "held", "attempt_id": attempt_id,
                "state": attempt["execution_runtime"], "launched": launched,
                "why": ("this generation JOURNALLED A LAUNCH and no container was "
                        "ever bound, so whether an execution is running is UNKNOWN; "
                        "the revocation stands and the resource stays held"
                        if launched else
                        "this generation journalled no launch and no runtime is "
                        "attached, so there is nothing to stop; the revocation "
                        "stands and the roots are the ending's to settle")}
    # 1. THE ENTITLEMENT GOES FIRST.
    govern.revoke(store, attempt, operation=operation_id)
    # 2. THE SHUTDOWN, outside every lock, under this reclaim's own identity.
    #
    # W275774 review 17:54:31Z [P1]: STOP AND THEN REMOVE, correlated to the same
    # reclaim. A stop-only reclaim left the container PRESENT, so the observation could
    # never reach `absent` and the revoked-resource ending -- which requires absence --
    # could never run. The two halves did not compose, and a lifecycle whose halves
    # cannot meet frees nothing.
    #
    # The removal is a separate verb because stopping and removing are separate facts:
    # a container that stopped but could not be removed is still holding its mounts,
    # and reporting them together would lose exactly that distinction.
    reclaim_id = reclaim_operation_id(attempt, overdue["generation"])
    try:
        adapter.stop_expired({"runtime_id": attempt["runtime_id"],
                              "operation_id": reclaim_id})
        remove = getattr(adapter, "remove", None)
        if remove is not None:
            remove({"runtime_id": attempt["runtime_id"],
                    "operation_id": reclaim_id})
    except ContractRefusal as refusal:
        # A REFUSED STOP IS NOT A CESSATION. The revocation stands, the resource
        # stays held, and the reason is carried rather than swallowed.
        return {"reclaimed": "held", "attempt_id": attempt_id, "state": "uncertain",
                "why": f"the stop was refused: {refusal.message}"}
    # 3. AND WHAT THAT EXACT IDENTITY NOW IS, asked of the adapter.
    state, _value, why = attempts._observed(adapter, attempt["runtime_id"])
    # THE OBSERVATION'S OWN VOCABULARY: `attempts.OBSERVED_RUNTIME` names the four
    # states an adapter may answer, and `absent` is the positive "this exact identity
    # does not exist". My first cut compared against the mapped VALUE `destroyed`
    # instead of the answered state, so a positively absent runtime read as
    # inconclusive and nothing was ever confirmed.
    if state not in ("absent", "quiescent"):
        return {"reclaimed": "held", "attempt_id": attempt_id, "state": state,
                "why": f"cessation is not positively proved: {why}"}
    cessation = _resource_cessation(
        store,
        {"state": "absent",
         # A RECLAIM NORMALIZES NOTHING, so it carries no directory custody of its
         # own and must not pretend to. What it can honestly report is the custody
         # this manager already committed for those roots.
         "directory_custody": _custody_already_committed(store, attempt_id),
         # A RECLAIM ESTABLISHES NO WRITER CESSATION OF ITS OWN either, and says so
         # rather than leaving the member to a reader's default.
         "writer_cessation": None},
        attempt, attempt_id)
    if cessation is None:
        # AND THE DIAGNOSTIC NAMES THE OBSERVED STATE rather than asserting absence.
        # Review 17:09:10Z: this said "the container is gone", which is true of
        # `absent` and NOT of `quiescent` -- a quiescent container still exists and
        # still holds its mounts. Reporting them the same way would put a false fact
        # in the record a later reader relies on.
        return {"reclaimed": "held", "attempt_id": attempt_id, "state": state,
                "why": f"the runtime observed {name_value(state)} and no "
                       f"writer-absence proof exists yet, so the revoked generation "
                       f"keeps the resource"}
    # 4. THE RETURN, as a manager settlement on confirmed cessation.
    govern.release(store, attempt, operation=operation_id, cessation=cessation,
                   reclaiming=True)
    return {"reclaimed": "returned", "attempt_id": attempt_id, "state": state,
            "container": cessation["container"]}


def _custody_already_committed(store, attempt_id):
    """The directory custody this manager committed for the governed roots, or None.

    Asked of the normalization owner rather than re-derived here, and absent unless
    EVERY governed root has it -- a partial answer is not a proof that no writer
    survives anywhere.
    """
    from . import custody as _custody

    held = {}
    for which in _CUSTODY_ROOTS:
        try:
            held[which] = _custody.historical_directory_custody(
                store, attempt_id, which)
        except ContractRefusal:
            # NOT AN ERROR HERE, and this is the distinction that matters: the
            # normalization owner refuses because there is no committed
            # normalization for that root, and the absence of a proof is exactly
            # what this function exists to report. A reclaim over an attempt whose
            # roots were never normalized has no basis for saying no writer
            # survives, so it says nothing and the resource stays held.
            return None
    return held


def settle_revoked_resource(store, adapter, *, attempt_id, govern,
                            seconds=None, reclaim=None):
    """The REVOKED generation's own ending: normalize the roots, then return.

    W275774 review 17:44:30Z named this as the executable milestone, and the gap it
    closes is one my own cases exposed: a reclaim revokes and stops but normalizes
    nothing, and the ordinary cleanup is authorized by an intake RECEIPT that a
    reclaimed running attempt never had. So a revoked resource could sit held with no
    operation able to free it -- the reclaim lacking the custody proof, the cleanup
    lacking its authorization.

    THE ORDER IS THE CONTENT, again:

      1. THE GENERATION MUST ALREADY BE REVOKED. This ending does not withdraw an
         entitlement; that is the reclaim's act and its own precondition (only an
         overdue generation may be revoked). An unrevoked generation is somebody's
         live permission and this refuses to settle it.
      2. THE CONTAINER MUST BE POSITIVELY GONE, asked of the adapter here rather than
         remembered from the reclaim, because time passed in between and a remembered
         absence is not an observation. Anything short of absence holds.
      3. THE OUTPUT IS ASKED, AND NOTHING IS RUN. W285465 under
         OWNER-NO-AUTOMATIC-NORMALIZATION-20260928: Slawomir selects shared-group
         ACCESSIBLE job output, so this step used to NORMALIZE and no longer does.
         Accessible output progresses with no receipt at all; inaccessible output is an
         ERROR that names the exact path and preserves the workspace, its bytes and its
         holds. No container, no permission change and no deletion.
      4. RETURN, on a cessation whose writer half is ESTABLISHED rather than inherited
         from a receipt: the adapter's read says which custody helpers still answer, a
         survivor holds with its identity named, and an adapter that cannot answer holds
         too -- absence is never inferred from a missing capability.

    AND NO OLD WRITABLE RESTART. The container is gone before step 3 and the
    generation is revoked throughout, so `_owning` refuses every act a stale holder
    could attempt -- a launch, a binding, an activation admission. A replacement
    becomes possible only after step 4 commits, which is after the proof.
    """
    from . import tokens

    boundaries.capability(getattr(adapter, "observe", None),
                          "the runtime adapter's observe")
    attempt = _attempt_of(store._connection, attempt_id)
    operation_id = attempts._start_operation_id(attempt)
    domain = tokens.domain_of(govern.resource_kind, govern.identity(attempt))
    generation = tokens.generation_of(
        store, domain, execution=attempt_id, operation=operation_id)
    if generation is None:
        return {"settled": "nothing-reserved", "attempt_id": attempt_id}
    current = tokens.token_of(store, domain, generation)
    if current["returned"]:
        return {"settled": "already-returned", "attempt_id": attempt_id}
    if not current["revoked"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"generation {generation} of {name_value(domain)} has not been revoked; "
            f"this ending settles a withdrawn entitlement and does not withdraw one, "
            f"because an unrevoked generation is a live permission")
    if attempt["runtime_id"] is None:
        return {"settled": "held", "attempt_id": attempt_id,
                "why": "no runtime was ever attached, so this ending has no "
                       "container to confirm gone and no writer absence to claim"}
    # W275774 review 17:54:31Z [P1]: THE EXCLUSION IS ESTABLISHED BEFORE THE EFFECTS.
    #
    # My order was wrong in the one way that matters. I normalized and THEN called the
    # return, which refuses while an activation is in flight -- so an admitted
    # unresolved activation meant this ending DELETED AND MOVED FILES and only
    # afterwards discovered it was not allowed to settle. Normalizing under a possible
    # writer is precisely what this ending must never do, and I had written that
    # sentence while doing it.
    #
    # An admitted activation with no settled outcome means a container MAY BE ABOUT TO
    # RUN over these roots. A momentary absence observation cannot settle that: the
    # submission may simply not have taken effect yet. So it is asked here, before any
    # effect, and the return re-asks it under the write lock afterwards -- the
    # exclusion is established first and kept through the settlement.
    if current["activating"]:
        return {"settled": "held", "attempt_id": attempt_id,
                "why": "an ADMITTED ACTIVATION of this generation has no settled "
                       "outcome, so a container may be about to run over these roots; "
                       "a momentary absence does not settle a delayed submission"}
    # AND THE EVIDENCE MUST BE ABOUT THIS EXACT EXECUTION. The container this ending
    # is about to account for is the one the token bound, under the launch it
    # journalled -- not whatever identity the attempt row happens to carry now.
    if current["container"] != attempt["runtime_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"generation {generation} of {name_value(domain)} governs container "
            f"{name_value(current['container'])} and this attempt now carries "
            f"{name_value(attempt['runtime_id'])}; this ending settles the bound "
            f"execution and not a different one")
    if current["launch"] is None:
        return {"settled": "held", "attempt_id": attempt_id,
                "why": "this generation bound a container under no journalled launch, "
                       "which is a state to reconcile rather than to settle"}
    state, _value, why = attempts._observed(adapter, attempt["runtime_id"])
    if state != "absent":
        # ASKED AGAIN RATHER THAN REMEMBERED. The reclaim's absence was true at the
        # reclaim's instant; a container can be restarted by a hand outside this
        # manager, and normalizing under a running writer is the one thing this
        # ending must never do.
        return {"settled": "held", "attempt_id": attempt_id, "state": state,
                "why": f"the runtime is not positively absent now: {why}"}
    # W285465, OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 with DESIGN HOST-5: THIS ENDING
    # RUNS NO HELPER. Slawomir selects shared-group ACCESSIBLE job output, so there is no
    # normalization here to produce a receipt and none is required: accessible output
    # PROGRESSES, and inaccessible output is an ERROR that preserves the workspace.
    #
    # The old shape normalized and then read `directory_custody` out of that act. Both are
    # gone from this path -- no container is created or started, no permission is changed
    # and nothing is deleted, each of which the ruling forbids as a substitute.
    # W285465 under the owner supersession at 294568/294616: NO OUTPUT SCAN ON THIS PATH.
    # This first held on an unreadable output and then reported it; both were the earlier
    # target. Completion and this settlement observe the EXECUTION, preserve the workspace as
    # is, and release the exact gate -- output validation belongs to the consumer that selects
    # it. Even a non-refusing walk was an unselected prerequisite whose own errors could
    # interrupt a settlement that had already proved what it needed.
    inaccessible = None
    # AND THE WRITER HALF IS ESTABLISHED RATHER THAN INFERRED. With no receipt to rest on,
    # `helpers` has to be a fact: the adapter's own read answers which custody helpers
    # still respond, and an adapter that CANNOT answer leaves this HELD. Review
    # 2026-09-28T03-08-08Z: absence must not be inferred from a missing capability, and no
    # custodian image is silently required to obtain one.
    # AND THE WRITER OBSERVATION, asked where it can be answered. Under
    # OWNER-SIMPLE-COMPLETION-20260928 a deployment that offers no listing is NOT uncertain
    # about the container this settlement has already observed absent, so `unavailable` no
    # longer holds; a POSITIVELY SURVIVING writer -- an observed violation -- still does.
    surviving, unavailable = _surviving_writers(adapter, store, attempt_id,
                                               seconds=seconds, reclaim=reclaim)
    if unavailable is not None:
        surviving = ()
    if surviving:
        return {"settled": "held", "attempt_id": attempt_id, "state": state,
                "why": f"a writer of attempt {name_value(attempt_id)} still survives "
                       f"({name_value(surviving[0].get('helper_identity'))}): "
                       f"{surviving[0].get('why')}",
                "surviving": list(surviving)}
    # THE SHAPE IS THE ONE THIS BUILD'S CONTRACT NAMES -- container, stopped, helpers --
    # and `tokens.release` composes the domain, generation and launch itself. Measured:
    # offering those three here is refused as unrecognised members, which is the closed
    # document rule doing its job.
    # THE CESSATION IS COMPOSED FROM FACTS THIS ENDING HAS ALREADY ESTABLISHED: the exact
    # bound container, observed ABSENT above and not remembered from the reclaim, and an
    # empty writer list the adapter's read just proved rather than a receipt's by-product.
    # The `cessation is None` branch that used to follow belonged to the normalization
    # builder and is REMOVED rather than left unreachable -- every held outcome on this
    # path now returns above, where the fact that is missing is named.
    cessation = {"container": current["container"], "stopped": True, "helpers": []}
    govern.release(store, attempt, operation=operation_id, cessation=cessation,
                   reclaiming=True)
    answer = {"settled": "returned", "attempt_id": attempt_id, "state": state,
              "container": cessation["container"]}
    if inaccessible is not None:
        # THE DURABLE ERROR TRAVELS WITH THE RETURN, so a reader learns both facts: the
        # execution ownership is released because its cessation held, AND this attempt's
        # output could not be read, which is a failure about the material and not about the
        # container. The bytes are preserved.
        answer["inaccessible"] = inaccessible
        answer["why"] = (
            f"attempt {name_value(attempt_id)}'s output is not readable by the configured "
            f"workspace group at {name_value(inaccessible.get('path'))}: "
            f"{inaccessible['why']}. The workspace, its bytes and its modes are preserved, "
            f"this manager changes no permissions, and nothing here is collection success or "
            f"permission to delete, reset or reuse it")
    return answer
