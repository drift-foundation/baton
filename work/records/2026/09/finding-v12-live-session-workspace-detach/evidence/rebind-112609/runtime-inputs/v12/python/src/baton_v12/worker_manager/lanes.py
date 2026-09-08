"""THE RUNTIME LANE -- one execution at a time, across attempts.

W32649. `work/records/2026/08/finding-v12-local-oci-negative-race-endings/
findings/finding-v12-cross-attempt-lane-capacity/`.

THE GAP THIS CLOSES, in its finding's words: the manager had no capacity
identity spanning runtime attempts. `posture_slots` is keyed
`(runtime_attempt_id, posture)`, so a SUCCESSOR gets a different slot and no
runtime-start precondition consulted a predecessor whose container is absent
but whose credential or launch teardown, custody obligation or retryable
cleanup was still unsettled.

AND THE WINDOW IS REAL rather than theoretical. Authority claim capacity and
manager runtime cleanup answer different questions at different times: an
assignment may END -- releasing the authority's claim slot, so the Work is
claimable again -- while this manager's roots, deliveries and custody are still
being taken down. Without a lane, the next claim turns that window into two
executions over one assignment's material.

-- THE IDENTITY, and what it deliberately is not ----------------------------

    lane = (authority_uuid, work_id, principal, effective_scope)

NOT THE ATTEMPT ID, which is the whole point: an identity that changed with
every attempt could not span a predecessor and a successor, which is exactly
the relation this lane exists to enforce.

NOT THE GENERATION. A successor claims after a fence and mints a new one, so a
generation-keyed lane would be free for precisely the caller it must block.
The generation stays what §4 makes it -- the execution FENCE -- and fencing and
capacity are different questions asked at different moments.

NOT THE PARTICIPANT. W16821's finding is that one `team.member` string served
as endpoint, principal, capability grantee and claim-slot key at once, and that
two spellings of one person received two of everything. A lane keyed on the
endpoint would reproduce that defect: `org_a.worker` and `org_b.worker` mapped
by the authority to one principal would hold two lanes over one assignment's
material. The bound acceptance names that outcome as a failure, and the
PRINCIPAL is what W16823 now carries onto the attempt row for this to read.

THE SCOPE IS IN IT because it is the authority's own answer about which
authorization domain an act was decided in, and two decisions in two scopes are
two authorizations. Reading it here rather than deriving it is the same rule
W16823 applies one layer up: this manager never reconstructs the authority's
mapping, it consumes what the trusted claim result returned.

THE WORK IS IN IT because a lane protects an assignment's MATERIAL -- its
roots, deliveries and custody -- and two Works held by one principal are two
sets of material with nothing between them. A principal-only lane would make
one principal's second Work wait on its first for no reason a filesystem could
name.

-- ...AND THE INTERLOCK THE KEY ALONE DOES NOT GIVE -------------------------

The key above satisfies both halves of the acceptance -- two addresses cannot
gain two lanes, two principals are isolated -- and it leaves one hole, which is
named here rather than left for a reader to find. The claim slot the authority
releases is per PRINCIPAL, so a Work whose assignment ended may be reclaimed by
a DIFFERENT principal while this manager's cleanup is still open. That
successor's lane is a different row, and the key alone would let it start.

So `_no_predecessor_holds` is a SECOND precondition rather than a third key
part: a start also requires that no lane on the same `(authority_uuid,
work_id)` is held by anyone. Keeping it separate keeps the two facts separate
-- capacity is per principal, and the predecessor interlock is per Work -- and
each is proved on its own.

-- OCCUPANCY IS AN INSERT, AND THAT IS THE COMPARE-AND-SWAP -----------------

The table's primary key is the lane, so `INSERT` is the acquisition and SQLite
answers the race: exactly one concurrent successor commits and every other one
receives an integrity error this module turns into an ordinary refusal. There
is no read-then-write, so there is no window between the two.

RELEASE IS A DELETE BOUND TO THE HOLDER. A lane is released by the attempt
holding it and by nothing else, which is what stops a sibling attempt's
cleanup from freeing a lane another attempt is still executing in.
"""

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from . import boundaries

# THE PUBLIC SURFACE IS TWO THINGS: what a lane IS, and who holds one. The
# composition helpers below are private for the reason `posture_slots`' are --
# each must run inside a transaction its caller owns, and a `connection` is not
# an operand of any public operation this manager exposes.
__all__ = ["LANE_PARTS", "lane_reference", "runtime_lane"]

# The four parts, written out because they are the identity rather than a
# convenient tuple. Order is fixed: it is what the digest is taken over.
LANE_PARTS = ("authority_uuid", "work_id", "principal", "effective_scope")


def lane_reference(attempt):
    """The lane one activated attempt belongs to, or a refusal.

    READ FROM THE ATTEMPT ROW, never from a caller. Every part was written by
    `activate_assignment` out of the authority's own closed claim result
    (W16823), so there is no operand on any public surface through which a
    caller or a worker could name a lane -- which is the acceptance's
    "without exposing a mutable caller-selected principal or scope", enforced
    by there being nothing to expose.
    """
    if attempt["assignment_principal"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt['runtime_attempt_id'])} is not "
            f"activated, so it belongs to no lane; capacity is a fact about "
            f"an assignment and an attempt without one is not in a queue for "
            f"anything")
    return {"authority_uuid": attempt["authority_uuid"],
            "work_id": attempt["work_id"],
            "principal": attempt["assignment_principal"],
            "effective_scope": attempt["assignment_scope"]}


def _lane_id(reference):
    """One stable, derived name for a lane.

    DERIVED rather than minted, so a restarted manager computes the same lane
    for the same assignment without having to have remembered one -- and so
    two managers racing the same successor compute the same primary key and
    therefore actually contend, instead of each inserting its own row.
    """
    return "lane:" + digest({part: reference[part]
                             for part in LANE_PARTS})[len("sha256:"):]


def _no_predecessor_holds(connection, reference, attempt_id):
    """No OTHER attempt holds a lane over this Work.

    The interlock the key alone does not give -- see this module's header. It
    is asked of the whole `(authority_uuid, work_id)` rather than of the lane,
    because the material a predecessor is still taking down belongs to the
    WORK and does not care which principal claimed it next.

    EXCLUDING THIS ATTEMPT'S OWN ROW, so an exact retry that already holds the
    lane is not refused by its own occupancy.
    """
    # THE WHOLE ROW, AND THROUGH `_adopted`. Review [P2]: this selected three
    # columns and used them directly, so a row whose stored id no longer
    # derives from its own parts was reported here as an ORDINARY
    # predecessor -- `refused/precondition`, with a holder and a reason taken
    # from a relation this manager never owned as one. That hides corrupt
    # persisted authority behind normal contention, and it points recovery at
    # an attempt id the split row may not actually be about.
    #
    # It still prevented overlap, which is why this is [P2] and not [P1]. But
    # "the outcome happened to be safe" is not the same statement as "the
    # state was understood", and a Work left permanently blocked by a row
    # nobody can diagnose is the cost of confusing them.
    found = connection.execute(
        "SELECT * FROM runtime_lanes "
        "WHERE authority_uuid = ? AND work_id = ? AND holder <> ?",
        (reference["authority_uuid"], reference["work_id"],
         attempt_id)).fetchall()
    if not found:
        return
    holder = _adopted(found[0])
    raise ContractRefusal(
        "refused", "precondition",
        f"attempt {name_value(holder['holder'])} still holds this Work's "
        f"runtime lane ({holder['reason']}); a successor does not start while "
        f"a predecessor's runtime, deliveries or custody are unsettled, "
        f"because the authority's claim slot is released before this "
        f"manager's cleanup finishes and the gap between the two is where two "
        f"executions over one assignment's material would overlap")


def _occupy_lane(connection, now, *, attempt_id, reference, reason):
    """Take the lane, or fail closed. ONE act, inside the caller's write.

    The caller owns the transaction on purpose: occupying a lane and recording
    the manager fact that makes a start eligible are one act, and a lane taken
    by a start that then did not journal would be capacity nobody can find the
    holder of.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(reason, "a lane occupancy reason")
    _no_predecessor_holds(connection, reference, attempt_id)
    name = _lane_id(reference)
    try:
        connection.execute(
            "INSERT INTO runtime_lanes (lane_id, authority_uuid, work_id, "
            "principal, effective_scope, holder, reason, occupied_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, reference["authority_uuid"], reference["work_id"],
             reference["principal"], reference["effective_scope"],
             attempt_id, reason, now))
    except Exception as failure:
        if type(failure).__name__ not in ("IntegrityError",):
            raise
        # THE SAME RULE ON THE LOSING SIDE OF THE RACE. Review [P2]: a row
        # whose stored Work part has moved evades the predecessor query above
        # -- it is no longer selected by this Work -- and then collides on the
        # retained primary key here, where two columns were read straight out
        # of it. The loser of a genuine race and an unreadable relation are
        # different facts and were reported as the same one.
        held = connection.execute(
            "SELECT * FROM runtime_lanes WHERE lane_id = ?",
            (name,)).fetchone()
        if held is not None:
            held = _adopted(held)
        raise ContractRefusal(
            "refused", "precondition",
            f"this assignment's runtime lane is held by attempt "
            f"{name_value(held['holder'] if held else None)} "
            f"({held['reason'] if held else 'unknown'}); one execution at a "
            f"time is what the lane is, and the loser of this race is refused "
            f"rather than started beside the winner") from None
    return name


def _release_lane(connection, *, attempt_id, reference, why):
    """Give the lane back, and ONLY if this attempt holds it.

    BOUND TO THE HOLDER. Two attempts can share a lane over their lifetimes,
    so a release that matched on the lane alone would let a predecessor's late
    cleanup free the lane its successor is currently executing in -- the same
    class of defect as an unbound compare-and-swap anywhere else.

    IDEMPOTENT BY CONSTRUCTION: releasing a lane this attempt does not hold
    removes nothing and says so, which is what a crash between the delete and
    the commit has to be safe against.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(why, "a lane release reason")
    changed = connection.execute(
        "DELETE FROM runtime_lanes WHERE lane_id = ? AND holder = ?",
        (_lane_id(reference), attempt_id)).rowcount
    return changed == 1


def runtime_lane(store, attempt_id):
    """PUBLIC: this attempt's lane, who holds it, and what blocks it.

    The acceptance asks for a projection that "explains the current lane holder
    and blocking predecessor WITHOUT exposing a mutable caller-selected
    principal or scope". Both halves are structural rather than filtered:

      * every value here is read from the attempt row and the lane table, and
        both were written from the authority's own closed claim result -- there
        is no operand anywhere on this manager's surface through which a caller
        could name a principal or a scope, so there is nothing to filter;
      * the answer distinguishes the three states an operator actually needs to
        tell apart -- this attempt HOLDS the lane, somebody else holds THIS
        lane, or somebody else holds a lane over this WORK -- because "blocked"
        without saying by which of the two relations is a diagnosis nobody can
        act on.
    """
    from .attempts import _require_attempt
    attempt = _require_attempt(store, attempt_id)
    reference = lane_reference(attempt)
    identity = {"lane_id": _lane_id(reference), **reference}
    held = _holder_of(store, reference)
    blocking = [row for row in _work_lanes(store, reference)
                if row["holder"] != attempt_id]
    return {
        "attempt_id": attempt_id,
        "lane": identity,
        "holder": held["holder"] if held is not None else None,
        "held_by_this_attempt": held is not None
        and held["holder"] == attempt_id,
        "reason": held["reason"] if held is not None else None,
        # THE PREDECESSOR IS ITS OWN MEMBER because it is its own relation:
        # a lane over this Work held by another principal does not appear in
        # `holder` at all, and an operator looking only there would see a free
        # lane and an unexplained refusal.
        "blocked_by": [{"holder": row["holder"], "lane_id": row["lane_id"],
                        "principal": row["principal"], "reason": row["reason"]}
                       for row in blocking],
    }


def _adopted(row):
    """ONE persisted lane, with its RELATION owned and not only its columns.

    Review [P1], and the defect is worth stating exactly because it is the
    kind a column contract cannot see.  `lane_id` is DERIVED from the four
    identity parts stored beside it, so those five values are one relation
    rather than five independent well-typed strings.  `boundaries.row` proved
    each of them and said nothing about whether they still belong together.

    WHAT THAT COST.  An adopted row keeping its holder and its four parts but
    carrying another well-formed `lane_id` was missed by `_holder_of`, which
    looks it up by the RECOMPUTED key, and then excluded from `blocked_by` by
    `runtime_lane`, which drops rows the queried attempt holds.  The public
    projection answered `holder=None`, `held_by_this_attempt=False` and
    `blocked_by=[]` -- an operator told the lane is FREE while the capacity row
    is still there.  Reading the store as consistent when it is not is worse
    than any refusal.

    SO THE RELATION IS PROVED WHERE THE ROW IS ADOPTED, once, and both read
    paths come through here.  Neither side of the split is chosen: a stored id
    that no longer derives from its parts does not tell us which half moved,
    and picking one would be inventing the answer this refusal exists to
    withhold.
    """
    from . import schema
    taken = boundaries.row(row, "a persisted runtime lane",
                           schema.RUNTIME_LANE_COLUMNS)
    derived = _lane_id({part: taken[part] for part in LANE_PARTS})
    if taken["lane_id"] != derived:
        raise ContractRefusal(
            "integrity", "schema",
            f"a persisted runtime lane is stored as "
            f"{name_value(taken['lane_id'])} and its own authority, Work, "
            f"principal and effective scope derive "
            f"{name_value(derived)}; the name and the parts are ONE relation, "
            f"and a row where they disagree cannot say whether this lane is "
            f"held -- so it is refused rather than read as free")
    return taken


def _work_lanes(store, reference):
    return [_adopted(row) for row in store._connection.execute(
        "SELECT * FROM runtime_lanes WHERE authority_uuid = ? AND "
        "work_id = ? ORDER BY lane_id",
        (reference["authority_uuid"], reference["work_id"])).fetchall()]


def _holder_of(store, reference):
    """WHO holds this lane, as a fresh owned document, or absence.

    LOOKED UP BY THE DERIVED KEY and then held to it: a row this query
    returned already matches the recomputed name, so what `_adopted` adds here
    is that its stored PARTS still derive that name too. The two directions
    are not the same check -- one asks "is this the row for this lane", the
    other "is this row internally one lane at all".
    """
    found = store._connection.execute(
        "SELECT * FROM runtime_lanes WHERE lane_id = ?",
        (_lane_id(reference),)).fetchone()
    return None if found is None else _adopted(found)
