"""The line's EFFECTIVE base, and the prelaunch settlement that frees it.

W131409, CONTRACT-v1 slice A. An Authority holds ONE canonical target revision
and `integration.driver` offers a proposal only against the revision it was
built from -- so once one Job integrates, every other Job whose accepted
checkpoint was built on the superseded revision has a candidate that target can
no longer take. `review_cycles.create_line` is create-or-recover by
`(authority, work)` and refuses operands that disagree with the ones it
recorded, so a line's DECLARED base is immutable and nothing may advance it.

THIS MODULE OWNS THE SECOND FACT rather than mutating the first. A committed
target-rework record says which revision a LATER round is written against; the
creation operands stay exactly where they are, an original `create_line` replay
still recovers the same line, and every historical checkpoint, verdict and
reference remains what it was. `effective_base` is the one reader that answers
which of the two a round uses.

AND IT OWNS THE ONE SETTLEMENT THAT MAKES ROOM FOR THAT ROUND. A stale
integration attempt that has been claimed and has NOT crossed the launch-intent
boundary is sealed against any future start, handed back through its own bound
Authority session, and recorded as a target-rework settlement. That is a
deliberately bounded case: a launch intent, an attached or uncertain runtime, a
live lease or an unresolved claim all HOLD here, for existing canonical
exclusion to resolve under its own authority. This module fabricates no worker
result, repurposes no operator abandonment, clears no gate and invents no
resource cleanup, and it never writes an integration receipt.
"""

import json

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from . import boundaries, schema
from .attempts import attempt_runtime_of
from .offers import claimed_offers_for
from .store import manager_signature

__all__ = ["PASS_COMMENT", "REWORK_KIND", "SEAL_KIND", "SETTLE_KIND",
           "effective_base", "prepare_rework", "rework_of", "seal_unstarted",
           "settle_unstarted", "settlement_of"]

REWORK_KIND = "target-rework.prepare"
SEAL_KIND = "target-rework.seal"
SETTLE_KIND = "target-rework.settle"

# WHAT THIS DEPLOYMENT SAYS WHEN IT HANDS A STALE INTEGRATION BACK. It is
# recorded beside the Authority transition, so it is written once here rather
# than composed at a call site -- and it says what happened, which is that the
# target moved under an attempt that had not started.
PASS_COMMENT = ("the canonical target advanced past this candidate's base and "
                "the attempt had not started; the Job's line is reworked onto "
                "the current target and reviewed again")


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _id(prefix, value):
    return prefix + "-" + digest(value).split(":", 1)[1]


def _assignment(value, what):
    """The four-part fixed assignment, proved rather than adopted."""
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


def _committed(control, operation_id, kind, what):
    """The journal row this materialized record must be bound to.

    A PUBLIC READER PROVES ITS OWN ROW. These tables are written only inside
    the journalled acts below, so a row with no committed operation of the
    right kind behind it was written by something that is not this owner --
    which is exactly the tampering a reader that trusted the table would pass
    on to a consumer as fact.
    """
    record = control.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        _refuse(f"{what} names operation {name_value(operation_id)}, which "
                f"this store's journal does not hold as a committed {kind}",
                category="integrity", code="schema")
    return record


# -- the prelaunch seal, and the handoff that consumes it --------------------


def seal_unstarted(control, *, attempt_id):
    """Exclude any future start of one claimed, unstarted integration attempt.

    CONTRACT-v1 section 4. The bounded case this supports is an attempt that
    holds capacity and a claim while NOTHING has been launched under it, which
    is the retained two-Job witness exactly. Everything else holds.

    THE SEAL IS A ROW AND THE RACE IS THE STORE'S. `request_runtime_start`
    reads this table inside the same transaction that commits launch intent, so
    the two immediate writers serialize and exactly one wins. A null runtime
    identity or an in-memory observation is not absence proof, so neither is
    what this records: what it records is that at the instant this transaction
    committed, no start operation was journalled and the runtime axis had never
    left `not-started`.
    """
    boundaries.identity(attempt_id, "a runtime attempt identity")
    runtime = attempt_runtime_of(control, attempt_id)
    if runtime is None or runtime["assignment"] is None:
        _refuse(f"attempt {name_value(attempt_id)} holds no fixed assignment; "
                f"an attempt this manager never activated is not one it can "
                f"hand back")
    assignment = _assignment(runtime["assignment"], "the sealed assignment")
    claimed = claimed_offers_for(control, attempt_id)
    if len(claimed) != 1:
        _refuse(f"attempt {name_value(attempt_id)} carries {len(claimed)} "
                f"committed claimed offers; a target-rework handoff moves the "
                f"Work off exactly one claim, and an unresolved claim is "
                f"reconciled through its own owner before this act")
    offer_id = boundaries.identity(claimed[0]["offer_id"], "a claimed offer")
    seal_id = _id("seal", {"attempt_id": attempt_id,
                           "assignment": assignment})
    operation_id = SEAL_KIND + ":" + attempt_id
    signature = manager_signature(SEAL_KIND, {"seal_id": seal_id,
                                              "attempt_id": attempt_id,
                                              "offer_id": offer_id,
                                              "assignment": assignment})
    found, result = store_replay(control, operation_id, signature, SEAL_KIND)
    if found:
        return result

    def act(connection):
        # RE-READ INSIDE THE WRITE. Everything above is a read, and the only
        # question that matters is what is true in this transaction.
        current = attempt_runtime_of(control, attempt_id)
        if current is None or current["assignment"] != runtime["assignment"]:
            _refuse(f"attempt {name_value(attempt_id)} was activated under "
                    f"another assignment while this seal was being derived",
                    category="stale-assignment", code="generation")
        if current["execution_runtime"] != "not-started":
            # THE AXIS IS THE LAUNCH-INTENT RECORD, which is why no second
            # journal lookup is made here. `request_runtime_start` takes the
            # runtime lane and observes `start-requested` INSIDE the one
            # transaction that commits its intent, so an attempt whose axis has
            # left `not-started` is one whose intent is already committed --
            # and this transaction, being the store's other immediate writer,
            # is reading the state that intent left. Every case beyond the
            # boundary holds for existing canonical exclusion to resolve.
            _refuse(f"attempt {name_value(attempt_id)}'s runtime is "
                    f"{name_value(current['execution_runtime'])}; v1 seals an "
                    f"attempt that has not crossed the launch-intent boundary "
                    f"and holds every other case for canonical exclusion")
        if current["cleanup"] not in (None, "pending"):
            _refuse(f"attempt {name_value(attempt_id)}'s cleanup axis is "
                    f"{name_value(current['cleanup'])}; an attempt whose "
                    f"resources have already been settled is history and is "
                    f"not sealed against a start it will never make")
        now = control._now()
        connection.execute(
            "INSERT INTO attempt_launch_seals (seal_id, runtime_attempt_id, "
            "offer_id, assignment, assignment_digest, sealed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (seal_id, attempt_id, offer_id, canonical_text(assignment),
             digest(assignment), now))
        return {"seal_id": seal_id, "runtime_attempt_id": attempt_id,
                "offer_id": offer_id, "assignment": assignment,
                "sealed_at": now}

    return control.transact(operation_id, SEAL_KIND, signature, act)


def store_replay(control, operation_id, signature, kind):
    """The store's own replay, named once so every act below reads alike."""
    return control.replay(operation_id, signature, kind=kind)


def seal_of(control, attempt_id):
    """This attempt's seal, or absence. A pure read that decides nothing."""
    boundaries.identity(attempt_id, "a runtime attempt identity")
    row = control._connection.execute(
        "SELECT * FROM attempt_launch_seals WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if row is None:
        return None
    held = boundaries.row(row, "a persisted attempt launch seal",
                          schema.ATTEMPT_LAUNCH_SEAL_COLUMNS)
    _committed(control, SEAL_KIND + ":" + attempt_id, SEAL_KIND,
               "a persisted attempt launch seal")
    held["assignment"] = _assignment(json.loads(held["assignment"]),
                                     "a persisted sealed assignment")
    if held["assignment_digest"] != digest(held["assignment"]):
        _refuse("a persisted attempt launch seal does not match its digest",
                category="integrity", code="digest")
    return held


def settle_unstarted(control, session, *, seal_id, to_route):
    """Hand the sealed attempt's Work back through its own bound session.

    THE ACT IS THE AUTHORITY'S AND THE RECORD IS THIS MANAGER'S. `pass_work`
    is effectively-once at the Authority under an identity derived from the
    attempt, so a retry replays the one committed transition rather than
    performing a second; what this owns is reading that account back and
    binding it to the seal before anything downstream may treat the capacity as
    free.

    IT IS A TARGET-REWORK SETTLEMENT AND NEVER AN INTEGRATION-COMPLETED
    ACCOUNT. No integration receipt is written, no lease is touched, no gate is
    cleared and no cleanup is claimed; what moved is the Work's route, back to
    where its next implementation round is served.
    """
    boundaries.text(seal_id, "a launch seal identity")
    boundaries.text(to_route, "an outgoing route")
    row = control._connection.execute(
        "SELECT * FROM attempt_launch_seals WHERE seal_id = ?",
        (seal_id,)).fetchone()
    if row is None:
        _refuse(f"no launch seal {name_value(seal_id)}")
    held = seal_of(control, boundaries.identity(
        row["runtime_attempt_id"], "a sealed runtime attempt"))
    if held is None or held["seal_id"] != seal_id:
        _refuse(f"launch seal {name_value(seal_id)} does not name its own "
                f"attempt", category="integrity", code="schema")
    attempt_id = held["runtime_attempt_id"]
    assignment = held["assignment"]
    if getattr(session, "participant", None) != assignment["participant"]:
        _refuse(f"the settlement session acts for "
                f"{name_value(getattr(session, 'participant', None))} and the "
                f"sealed assignment names "
                f"{name_value(assignment['participant'])}",
                code="capability")
    settlement_id = _id("rework-settlement", {"seal_id": seal_id,
                                              "to_route": to_route})
    handoff_operation_id = "target-rework-pass:" + attempt_id
    operation_id = SETTLE_KIND + ":" + settlement_id
    signature = manager_signature(SETTLE_KIND, {
        "settlement_id": settlement_id, "seal_id": seal_id,
        "attempt_id": attempt_id, "assignment": assignment,
        "to_route": to_route,
        "handoff_operation_id": handoff_operation_id})
    found, result = store_replay(control, operation_id, signature, SETTLE_KIND)
    if found:
        return result
    account = session.pass_work({"expect": assignment,
                                 "operation_id": handoff_operation_id,
                                 "to_route": to_route,
                                 "comment": PASS_COMMENT})
    account = _account(account, assignment, to_route)

    def act(connection):
        now = control._now()
        connection.execute(
            "INSERT INTO rework_settlements (settlement_id, seal_id, "
            "runtime_attempt_id, assignment, to_route, handoff_operation_id, "
            "account, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (settlement_id, seal_id, attempt_id, canonical_text(assignment),
             to_route, handoff_operation_id, canonical_text(account), now))
        return {"settlement_id": settlement_id, "seal_id": seal_id,
                "runtime_attempt_id": attempt_id, "assignment": assignment,
                "to_route": to_route,
                "handoff_operation_id": handoff_operation_id,
                "account": account, "settled_at": now}

    return control.transact(operation_id, SETTLE_KIND, signature, act)


def _account(value, assignment, to_route):
    """The Authority's own returned account, held to what it must say.

    ROUTE OR GENERATION DRIFT STOPS HERE, before any consumer may read the
    settlement and release capacity: an account that ended a different
    assignment, or moved the Work somewhere else, is not this settlement's.
    """
    held = boundaries.document(value, "the target-rework handoff account",
                               required=("assignment", "route", "cause",
                                         "phase", "gate", "fenced"))
    if _assignment(held["assignment"], "the handed-off assignment") \
            != assignment:
        _refuse("the target-rework handoff ended another assignment",
                category="stale-assignment", code="generation")
    if held["route"] != to_route:
        _refuse(f"the target-rework handoff moved the Work to "
                f"{name_value(held['route'])} and this settlement names "
                f"{name_value(to_route)}",
                code="operation-collision")
    if held["cause"] != "pass":
        _refuse(f"the target-rework handoff is {name_value(held['cause'])} "
                f"and this settlement composes a pass",
                category="integrity", code="schema")
    if held["fenced"]:
        _refuse("the target-rework handoff fenced the assignment; this "
                "settlement moves a route and clears no gate",
                category="integrity", code="schema")
    return held


def settlement_of(control, settlement_id):
    """One settlement, cross-bound to its seal and its journal rows."""
    boundaries.text(settlement_id, "a rework settlement identity")
    row = control._connection.execute(
        "SELECT * FROM rework_settlements WHERE settlement_id = ?",
        (settlement_id,)).fetchone()
    if row is None:
        return None
    held = boundaries.row(row, "a persisted rework settlement",
                          schema.REWORK_SETTLEMENT_COLUMNS)
    _committed(control, SETTLE_KIND + ":" + settlement_id, SETTLE_KIND,
               "a persisted rework settlement")
    held["assignment"] = _assignment(json.loads(held["assignment"]),
                                     "a persisted settled assignment")
    held["account"] = _account(json.loads(held["account"]),
                               held["assignment"], held["to_route"])
    seal = seal_of(control, held["runtime_attempt_id"])
    if seal is None or seal["seal_id"] != held["seal_id"] \
            or seal["assignment"] != held["assignment"]:
        _refuse(f"rework settlement {name_value(settlement_id)} does not name "
                f"its own attempt's seal",
                category="integrity", code="schema")
    return held


# -- the custody record, and the effective base it owns ----------------------


def effective_base(control, line_id):
    """The revision THIS line's next round is written against.

    THE CREATION OPERAND UNTIL A REWORK SAYS OTHERWISE, and the creation
    operand is never changed to say it. A line that has never been reworked
    answers its declared base, which is every line an earlier schema could
    hold; one whose current record is `ready` answers that record's target
    revision. Preparing and held answer the declared base, because neither
    authorizes a writer or a checkpoint.
    """
    from . import review_cycles

    line = review_cycles.line_of(control, line_id)
    if line["current_rework_id"] is None:
        return line["declared_base"]
    held = rework_of(control, line["current_rework_id"])
    if held["line_id"] != line_id:
        _refuse(f"line {name_value(line_id)} names a rework of another line",
                category="integrity", code="schema")
    if held["state"] != "ready":
        return line["declared_base"]
    return held["target_revision"]


def prepare_rework(control, authority, *, line_id, checkpoint_id, target_id,
                   target_source, target_proposal_id, profile, settlement_id):
    """Prepare this line's accepted change on the target that moved past it.

    CONTRACT-v1 sections 2 and 5. Every operand below is proved against its own
    owner before anything is written, and the ORDER is the contract: the
    Authority decides what the target is, this manager decides that the
    settlement and the checkpoint are its own, and only then does an intent
    commit and the profile touch a repository.

    INTENT COMMITS BEFORE FILESYSTEM WORK, which is what makes a death in the
    middle answerable. A `preparing` record is the durable statement that this
    line is being reworked under this exact identity; recovery validates and
    reuses whatever the profile already retained instead of applying the delta
    a second time.

    THE IDENTITY IS DERIVED FROM WHAT CANNOT CHANGE -- the Authority, the Work,
    the line, the OLD immutable checkpoint digest and the intended target
    revision -- and the signature binds every other fixed operand beside it. A
    caller that reaches this identity with different operands is refused by the
    store's own collision rule rather than quietly preparing something else.

    A CONFLICT IS AN OUTCOME. It commits a `held` record naming the conflicted
    paths, and the old checkpoint, its reference, its objects, its verdict and
    the private checkout are all exactly as they were, because none of them was
    ever written.
    """
    from . import review_cycles

    profile_name = _profile(profile, ("validate", "prepare_rework",
                                      "validate_rework"))
    boundaries.identity(target_id, "a canonical target identity")
    boundaries.identity(target_proposal_id, "an Authority proposal identity")
    line = review_cycles.line_of(control, line_id)
    if line["profile_name"] != profile_name:
        _refuse("the line and rework profile do not match",
                category="policy", code="profile-uncertified")
    checkpoint = review_cycles.checkpoint_of(control, checkpoint_id)
    if checkpoint["line_id"] != line_id or checkpoint["state"] != "frozen":
        _refuse(f"checkpoint {name_value(checkpoint_id)} is not a frozen "
                f"checkpoint of line {name_value(line_id)}",
                category="integrity", code="schema")
    evidence = checkpoint["evidence"]
    # THE TARGET IS THE AUTHORITY'S ANSWER AND THE PROPOSAL IS PROVED AGAINST
    # IT. A digest this manager was told about is not a target; a proposal the
    # Authority holds, whose candidate IS the current canonical target and
    # whose integration receipt says `integrated`, is.
    target_revision = boundaries.text(_authority(authority.canonical_target,
                                                 "the canonical target read"),
                                      "the Authority's canonical target")
    proposal = _authority(lambda: authority.proposal(target_proposal_id),
                          "the target proposal read")
    if proposal is None or proposal.get("candidate_digest") != target_revision:
        _refuse(f"proposal {name_value(target_proposal_id)} is not the "
                f"candidate this Authority's canonical target names",
                code="operation-collision")
    receipt = _authority(
        lambda: authority.receipt(target_proposal_id, "integration"),
        "the target integration receipt read")
    if receipt is None or receipt.get("disposition") != "integrated":
        _refuse(f"proposal {name_value(target_proposal_id)} carries no "
                f"integrated receipt; a rework is prepared onto a revision an "
                f"integration actually produced")
    source = _nominated(target_source)
    line_object = {"path": line["line_path"], "device": line["line_device"],
                   "inode": line["line_inode"]}
    operation_id = REWORK_KIND + ":" + _id("rework", {
        "authority_uuid": line["authority_uuid"], "work_id": line["work_id"],
        "line_id": line_id, "old_checkpoint_digest": checkpoint[
            "checkpoint_digest"], "target_revision": target_revision})
    operands = {"operation_id": operation_id,
                "line_id": line_id, "checkpoint_id": checkpoint_id,
                "old_checkpoint_digest": checkpoint["checkpoint_digest"],
                "old_base": evidence["base"], "target_id": target_id,
                "target_revision": target_revision,
                "target_receipt_id": receipt["receipt_id"],
                "target_proposal_id": target_proposal_id,
                "target_source": source, "profile_name": profile_name,
                "line_object": line_object, "settlement_id": settlement_id}
    signature = manager_signature(REWORK_KIND, operands)
    # THE REPLAY COMES BEFORE THE FACTS THIS ACT ALREADY CHANGED. A committed
    # preparation retired the old eligibility and moved the line, so asking
    # again whether the line holds an accepted checkpoint would refuse a
    # RETRY of the very act that retired it. Everything above is derivable
    # from operands and from records this act does not touch; everything below
    # is what a first run consumes.
    found, _result = store_replay(control, operation_id, signature,
                                  REWORK_KIND)
    if found:
        return rework_of(control, operation_id)
    accepted = review_cycles.integration_checkpoint(control, line_id)
    if accepted is None or accepted["checkpoint_id"] != checkpoint_id:
        _refuse(f"line {name_value(line_id)} holds no accepted integration "
                f"checkpoint {name_value(checkpoint_id)}; a rework "
                f"re-expresses the change a review already accepted and never "
                f"one nobody has")
    settlement = settlement_of(control, settlement_id)
    if settlement is None:
        _refuse(f"no rework settlement {name_value(settlement_id)}; the stale "
                f"integration attempt is settled through its own owner before "
                f"its Job's line is reworked")
    if settlement["assignment"]["work_ref"] != {
            "authority_uuid": line["authority_uuid"],
            "work_id": line["work_id"]}:
        _refuse(f"rework settlement {name_value(settlement_id)} settled "
                f"another Work's attempt", code="operation-collision")
    if target_revision == evidence["base"]:
        _refuse(f"line {name_value(line_id)} is already based on "
                f"{name_value(target_revision)}; a rework answers a target "
                f"that moved and there is nothing here to re-express")
    held_line = review_cycles._consumable_line(control, line_id)
    if {"path": held_line["line_path"], "device": held_line["line_device"],
            "inode": held_line["line_inode"]} != line_object:
        _refuse("the line object moved while its rework was being derived",
                category="integrity", code="path")
    eligibility = {"checkpoint_id": accepted["checkpoint_id"],
                   "verdict_id": accepted["verdict_id"]}

    def intend(connection):
        current = review_cycles.line_of(control, line_id)
        if current["state"] != "accepted" \
                or current["current_checkpoint_id"] != checkpoint_id:
            _refuse("the line moved on while its rework was being derived",
                    category="stale-assignment", code="generation")
        if current["current_rework_id"] is not None:
            _refuse(f"line {name_value(line_id)} already holds rework "
                    f"{name_value(current['current_rework_id'])}; one line "
                    f"prepares one round at a time",
                    code="operation-collision")
        now = control._now()
        connection.execute(
            "INSERT INTO target_reworks (operation_id, authority_uuid, "
            "work_id, line_id, old_checkpoint_id, old_checkpoint_digest, "
            "old_base, target_id, target_revision, target_receipt_id, "
            "target_proposal_id, target_source, profile_name, line_object, "
            "state, reason, prepared, superseded_eligibility, "
            "integration_settlement, recorded_at) VALUES (?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, 'preparing', NULL, NULL, ?, ?, ?)",
            (operation_id, line["authority_uuid"], line["work_id"], line_id,
             checkpoint_id, checkpoint["checkpoint_digest"], evidence["base"],
             target_id, target_revision, receipt["receipt_id"],
             target_proposal_id, canonical_text(source), profile_name,
             canonical_text(line_object), canonical_text(eligibility),
             canonical_text(settlement), now))
        connection.execute(
            "UPDATE review_lines SET state = 'reworking', "
            "current_rework_id = ? WHERE line_id = ?",
            (operation_id, line_id))
        return {"operation_id": operation_id, "state": "preparing"}

    control.transact(operation_id, REWORK_KIND, signature, intend)
    # -- and only now does anything outside this store happen ---------------
    answer = profile.prepare_rework(
        held_line["line_path"], evidence, line_id=line_id,
        revision=checkpoint["revision"], target_source=source["path"],
        target_revision=target_revision)
    return _settled(control, operation_id, line_id, source, answer,
                    target_revision)


def _settled(control, operation_id, line_id, source, answer, target_revision):
    """Record what the profile answered, once, under this same intent."""
    from . import review_cycles

    if type(answer) is not dict or answer.get("state") not in ("ready", "held"):
        _refuse("a rework profile answers a ready or held outcome",
                category="integrity", code="schema")
    # THE OBJECT THE PROFILE ACTUALLY RESOLVED, not the one it was handed.
    verified = boundaries.document(answer.get("target"),
                                   "the verified target object",
                                   required=("commit", "tree"))
    if boundaries.text(verified["commit"], "the verified target commit") \
            != target_revision:
        _refuse("the profile verified another target commit",
                code="operation-collision")
    boundaries.text(verified["tree"], "the verified target tree")
    source = dict(source, commit=verified["commit"], tree=verified["tree"])
    ready = answer["state"] == "ready"
    prepared = None
    reason = None
    if ready:
        prepared = review_cycles._evidence(answer["prepared"])
    else:
        reason = boundaries.text(answer.get("reason"), "a rework hold reason")
        conflicts = answer.get("conflicts")
        if type(conflicts) is not list:
            _refuse("a held rework answers the paths it conflicted on",
                    category="integrity", code="schema")
        reason = reason + " (" + ", ".join(
            boundaries.text(one, "a conflicted path")
            for one in conflicts) + ")" if conflicts else reason
    outcome_id = operation_id + "#outcome"
    signature = manager_signature(REWORK_KIND + ".outcome", {
        "operation_id": operation_id, "state": answer["state"],
        "prepared": prepared, "reason": reason, "target_source": source})
    found, _result = store_replay(control, outcome_id, signature,
                                  REWORK_KIND + ".outcome")
    if found:
        return rework_of(control, operation_id)

    def act(connection):
        current = control._connection.execute(
            "SELECT state FROM target_reworks WHERE operation_id = ?",
            (operation_id,)).fetchone()
        if current is None or current["state"] != "preparing":
            _refuse("this rework's intent is no longer preparing",
                    code="operation-collision")
        connection.execute(
            "UPDATE target_reworks SET state = ?, reason = ?, prepared = ?, "
            "target_source = ? WHERE operation_id = ? AND state = 'preparing'",
            (answer["state"], reason,
             None if prepared is None else canonical_text(prepared),
             canonical_text(source), operation_id))
        if ready:
            # THE OLD ELIGIBILITY IS RETIRED, and its identity is already
            # retained in this record. The accepted verdict stays exactly where
            # it is -- it remains the historical fact that somebody reviewed
            # and accepted those bytes -- but the CURRENT claim that this
            # line's checkpoint may be integrated is what the moved target
            # invalidated, and leaving it standing would let the stale
            # candidate be offered again.
            connection.execute(
                "DELETE FROM integration_eligibility WHERE line_id = ?",
                (line_id,))
            connection.execute(
                "UPDATE review_lines SET state = 'rework-ready' "
                "WHERE line_id = ?", (line_id,))
        else:
            connection.execute(
                "UPDATE review_lines SET state = 'rework-held' "
                "WHERE line_id = ?", (line_id,))
        return {"operation_id": operation_id, "state": answer["state"]}

    control.transact(outcome_id, REWORK_KIND + ".outcome", signature, act)
    return rework_of(control, operation_id)


def _profile(profile, methods):
    name = getattr(profile, "name", None)
    boundaries.text(name, "a checkpoint profile name")
    for method in methods:
        boundaries.capability(getattr(profile, method, None),
                              f"a checkpoint profile's {method} capability")
    return name


def _authority(read, what):
    """One Authority read, answered in this boundary's own vocabulary."""
    from ..authority import Refusal

    try:
        return read()
    except Refusal as refusal:
        _refuse(f"{what}: {refusal}", code="capability")


def _nominated(value):
    """The read-only target content this rework is prepared from.

    AN OBJECT AND NOT A PATHNAME. What is recorded is the path together with
    the device and inode it resolved to, so a later reader can say whether the
    repository this preparation actually read is the one a caller names now.
    """
    import os

    place = boundaries.text(getattr(value, "place", value),
                            "a nominated target repository")
    if not os.path.isabs(place) or os.path.islink(place) \
            or not os.path.isdir(place):
        _refuse(f"the nominated target content at {name_value(place)} is a "
                f"real directory of its own", category="integrity",
                code="path")
    status = os.stat(place)
    return {"path": place, "device": status.st_dev, "inode": status.st_ino,
            "commit": None, "tree": None}


def rework_of(control, operation_id):
    """One committed custody record, as a typed document.

    A PURE READ WITH NO LAZY PREPARATION. What it adds to the row is the
    binding a consumer cannot make for itself: that this store's journal holds
    a committed preparation under this identity, and that the record's own
    documents decode to what their columns say.
    """
    boundaries.text(operation_id, "a target-rework operation identity")
    row = control._connection.execute(
        "SELECT * FROM target_reworks WHERE operation_id = ?",
        (operation_id,)).fetchone()
    if row is None:
        _refuse(f"no target rework {name_value(operation_id)}")
    held = boundaries.row(row, "a persisted target rework",
                          schema.TARGET_REWORK_COLUMNS)
    _committed(control, operation_id, REWORK_KIND, "a persisted target rework")
    for member in ("target_source", "line_object", "superseded_eligibility"):
        held[member] = json.loads(held[member])
    if held["prepared"] is not None:
        held["prepared"] = json.loads(held["prepared"])
    if held["integration_settlement"] is not None:
        held["integration_settlement"] = json.loads(
            held["integration_settlement"])
    return held
