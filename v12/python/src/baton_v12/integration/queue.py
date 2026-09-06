"""Target identity, immutable entries, rank, and the one live lease.

W71878 PLAN item 3, under the owner ruling of 2026-09-05.

WHAT THIS MODULE DECIDES AND WHAT IT DELIBERATELY DOES NOT. It decides WHICH
entry a target integrates next and WHO holds the exclusive right to do it. It
decides nothing about whether a candidate is eligible: `enqueue` takes an
already-validated eligibility account as one closed document and stores it as
evidence. Building that account -- re-resolving W71918's custody surface and
Authority's policy receipts and proving their corresponding operands describe
one candidate -- is PLAN item 4's, and it sits ABOVE this seam so that neither
half can be mistaken for the other.

NO GIT, NO FILESYSTEM, NO AUTHORITY SESSION reaches this module. The trusted
integration profile owns all three; what it must present here is a LIVE GRANT.

NO VERSION CONTROL SYSTEM REACHES THIS MODULE EITHER, and the owner
clarification of 2026-09-06 is why that sentence is separate from the one
above. Core Baton mechanically owns serialized target admission, the live
fenced grant, exclusive target write access, quiescence and durable success or
refusal; it does not parse or validate commits, refs, branches, trees, ancestry
or merge semantics, and it does not require a VCS-aware adapter to exist. The
eligibility account named `base_object`, `head_object`, `tree_object` and
`transport_ref`, and the target document named a `checkout`: five Git operands
inside coordinator vocabulary. They are replaced by a closed, versioned profile
binding -- `profile_kind`, `profile_version` and `profile_account_digest` --
which binds the profile-shaped operands without holding or interpreting them.
An opaque unvalidated document was refused by name as an escape hatch, and a
digest is not one: it is a typed identity of evidence that lives in the Work's
generic inputs, outputs and logs.

EVERY PUBLIC DOCUMENT OPERAND IS USED AS THE OWNED SNAPSHOT `boundaries`
RETURNS, and this was audited rather than assumed after the re-review of
2026-09-06 found two calls that validated one value and used another. The
public document operands are the target (`activate_target`), the eligibility
account (`enqueue`), the settlement (`settle_integrated`, `refuse_entry`), the
block account (`block_target`), the lease ending (`release_lease`) and the
recovery (`abandon_lease`); each assigns the boundary's answer and nothing
below re-reads the caller's object. The nested validations inside the helpers
-- a settlement's `verification`, an ending's `detail` -- are checks on members
of an ALREADY-owned snapshot rather than second doors, so their answers are
deliberately not rebound.
"""

import json

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from ..worker_manager.store import revive_refusal
from . import schema
from .store import integration_signature

__all__ = ["abandon_lease", "activate_target", "block_target", "enqueue",
           "entries_of", "grant_lease", "lease_of", "live_grant",
           "refuse_entry", "release_lease", "settle_integrated",
           "target_of"]

# WHAT A TARGET DOCUMENT IS, after the owner clarification of 2026-09-06: a
# NAME that integration serializes on, and nothing about where the thing it
# names lives. `checkout` was here, and a checkout is a Git idea; the
# coordinator owns serialized admission, the fenced grant, exclusive access and
# durable settlement, so the concrete location belongs to the profile that
# integrates rather than to the lock. The document version moves with the
# shape, because a document whose members changed is not the same document.
TARGET_MEMBERS = ("schema", "canonical_target_id", "description")
TARGET_SCHEMA = "baton.v12.integration-target/2"

# WHAT A BLOCKED TARGET REMEMBERS. The review of 2026-09-06 found a block that
# named one entry while a different one held the live lease, so the recovery
# that followed ended the real holder's grant. A block is now ABOUT a grant,
# and this is that grant written down.
BLOCK_MEMBERS = ("entry_id", "lease_id", "fence", "integrator_participant",
                 "attempt_id", "reason", "detail")

# A SETTLEMENT'S SHAPE FOLLOWS ITS STATE. `integrated` accounts for what
# reached the target; the two refusals account for why nothing did.
#
# THE MEMBER SET IS NOT THE SHAPE, which the re-review of 2026-09-06 [P1]
# demonstrated by storing a `held` settlement whose reason was the integer 7
# and watching it come back. Knowing which members a document carries tells you
# nothing if you do not then know what they must BE -- the same correction
# `boundaries.alternative` records against itself.
SETTLEMENT_MEMBERS = {"integrated": ("imported_paths", "verification"),
                      "refused": ("reason", "detail"),
                      "held": ("reason", "detail")}

# HOW A LEASE ENDED, as closed variants rather than one open document. The
# re-review changed an `abandoned` lease's ending to `{"outcome":
# "integrated"}` and the reader returned it: an ending that does not match the
# state it belongs to is the store contradicting itself about whether a holder
# was recovered or finished.
ENDING_VARIANTS = {"integrated": ((), ("detail",)),
                   "entry-refused": ((), ()),
                   "abandoned": (("recovery",), ())}

# Which endings each terminal lease state may carry. `released` is an ending
# its holder reached; `abandoned` is one somebody else reached for it.
ENDING_BY_STATE = {"released": ("integrated", "entry-refused"),
                   "abandoned": ("abandoned",)}

RECOVERY_MEMBERS = ("attempt_id", "evidence")


def _settlement(value, state, what):
    """One settlement, owned as the variant its entry's state requires.

    ONE OWNER FOR BOTH DOORS. The same function runs at the caller's door and
    at the persisted read, because a document validated on the way in and
    trusted on the way out is a document with one lock and two doors -- which
    is the shape `boundaries.sealed` records having been caught twice.
    """
    if state not in SETTLEMENT_MEMBERS:
        # A `queued` or `leased` entry HAS no settlement, and the schema's own
        # CHECK says so for a row. A recorded result is under no CHECK, so a
        # forged entry document carrying one reached `SETTLEMENT_MEMBERS[state]`
        # and escaped as a raw `KeyError` -- found by the seventh round's own
        # retry matrix, which corrupted a block's result into a queued entry.
        _refuse(f"{what} accounts for an entry recorded {name_value(state)}, "
                f"and a settlement belongs to "
                f"{', '.join(sorted(SETTLEMENT_MEMBERS))} work alone")
    account = boundaries.document(value, what,
                                  required=SETTLEMENT_MEMBERS[state])
    if state == "integrated":
        paths = account["imported_paths"]
        if type(paths) is not list:
            _refuse(f"{what} imports a collection of paths; this is "
                    f"{name_value(paths)}")
        for one in paths:
            boundaries.text(one, f"{what}'s imported path")
        # A DOCUMENT, AND THIS SEAM DOES NOT SAY MORE. What a verification
        # account must CONTAIN is PLAN item 5's, which owns the bounded
        # final-byte, mode and Work verification that produces it. Naming its
        # members here would be this record deciding another one's contract.
        boundaries.document(account["verification"], f"{what}'s verification")
    else:
        boundaries.text(account["reason"], f"{what}'s reason")
        boundaries.document(account["detail"], f"{what}'s detail")
    return account


def _ending(value, state, what):
    """How a lease ended, owned against the state that says it did."""
    account = boundaries.alternative(value, what, ENDING_VARIANTS,
                                     discriminator="outcome")
    if account["outcome"] not in ENDING_BY_STATE[state]:
        _refuse(f"{what} answers {name_value(account['outcome'])} on a lease "
                f"recorded {name_value(state)}, whose endings are "
                f"{' or '.join(ENDING_BY_STATE[state])}")
    if "detail" in account:
        boundaries.document(account["detail"], f"{what}'s detail")
    if account["outcome"] == "abandoned":
        account["recovery"] = _recovery(account["recovery"],
                                        f"{what}'s recovery")
    return account


def _recovery(value, what):
    account = boundaries.document(value, what, required=RECOVERY_MEMBERS)
    boundaries.identity(account["attempt_id"], f"{what}'s attempt id")
    boundaries.text(account["evidence"], f"{what}'s evidence")
    return account

# EVERY OPERAND AN ENTRY CARRIES, and each one is evidence rather than a value
# this module computes. The two digest families are both here and neither is
# derived from the other -- see `schema.entries`.
ELIGIBILITY_MEMBERS = (
    "authority_uuid", "work_id", "assignment_generation", "line_id",
    "checkpoint_id", "verdict_id", "checkpoint_digest", "proposal_id",
    "candidate_digest", "proposal_manifest_digest", "profile_kind",
    "profile_version", "profile_account_digest", "expected_target_revision",
    "path_set_digest", "scope_digest")


def _refuse(message, *, category="integrity", code="schema", durable=False):
    raise ContractRefusal(category, code, message, durable=durable)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _row(row, what, columns):
    return None if row is None else boundaries.row(row, what, columns)


# -- ONE TARGET, ADOPTED AND PROVED AS ONE RELATIONSHIP --------------------
#
# Third review of 2026-09-06 [P0]: the previous shape validated the blocked
# relationship only when `targets.blocked_account` was PRESENT, and each public
# read proved its own half. So erasing the block within the schema -- setting
# the target row back to the perfectly legal `open` shape with both block
# columns null -- left a `held` entry and an `abandoned` lease that every door
# accepted separately, and `grant_lease` then leased the next queued entry past
# unresolved held work. Validating a relationship only when one side ADMITS to
# it lets the corrupted absence choose the permissive branch.
#
# So every public read of this store goes through one pass that adopts the
# target, its entries and its leases together and proves the whole graph. It is
# not recursive: raw rows are adopted here, the invariants below read only what
# this pass already holds, and no invariant calls a public reader.
#
# THE INVARIANT THE [P0] IS ABOUT, stated once: an open target has no held
# entry and no abandonment. A held entry exists because an import could not be
# reconciled, and an abandonment exists because a block was recovered; neither
# can be true of a target that is open for business. Item 3 defines no repair,
# so nothing here reopens a target -- and whatever 3b or item 6 adds must
# reconcile the held entry and the recovery account in the SAME transaction
# that reopens, or this invariant becomes false the moment it runs.


def target_of(store, canonical_target_id):
    boundaries.identity(canonical_target_id, "a canonical target id")
    whole = _relationship(store, canonical_target_id)
    return None if whole is None else whole["target"]


def entries_of(store, canonical_target_id, *, state=None):
    boundaries.identity(canonical_target_id, "a canonical target id")
    if state is not None and state not in schema.ENTRY_STATES:
        _refuse(f"an entry state is one of {schema.ENTRY_STATES!r}")
    whole = _relationship(store, canonical_target_id)
    if whole is None:
        return []
    return [one for one in whole["entries"]
            if state is None or one["state"] == state]


def lease_of(store, lease_id):
    boundaries.identity(lease_id, "a lease id")
    with store.snapshot():
        return _lease_of(store, lease_id)


def _lease_of(store, lease_id):
    found = store._connection.execute(
        "SELECT canonical_target_id FROM leases WHERE lease_id = ?",
        (lease_id,)).fetchone()
    if found is None:
        # ABSENCE IS AN ANSWER ONLY IF NOTHING SAYS OTHERWISE. A lease this
        # store recorded granting and no longer holds is a deletion, and
        # answering `None` would report it as "never happened".
        for act in _history(store):
            if act["operation_id"] == "lease.grant:" + lease_id and \
                    act["result"] is not None:
                _refuse(f"this store recorded the grant of lease "
                        f"{name_value(lease_id)} and no such lease is "
                        f"materialized")
        return None
    whole = _relationship(store, boundaries.identity(
        found["canonical_target_id"], "a lease's target"))
    if whole is None:
        _refuse(f"lease {name_value(lease_id)} is over target "
                f"{name_value(found['canonical_target_id'])}, which this "
                f"store does not hold")
    for lease in whole["leases"]:
        if lease["lease_id"] == lease_id:
            return lease
    _refuse(f"lease {name_value(lease_id)} is not among the leases of the "
            f"target it names")


def _entry(store, entry_id):
    boundaries.identity(entry_id, "an entry id")
    with store.snapshot():
        return _entry_of(store, entry_id)


def _entry_of(store, entry_id):
    found = store._connection.execute(
        "SELECT canonical_target_id FROM entries WHERE entry_id = ?",
        (entry_id,)).fetchone()
    if found is None:
        _refuse(f"no integration entry {name_value(entry_id)}")
    whole = _relationship(store, boundaries.identity(
        found["canonical_target_id"], "an entry's target"))
    if whole is None:
        _refuse(f"entry {name_value(entry_id)} belongs to target "
                f"{name_value(found['canonical_target_id'])}, which this "
                f"store does not hold")
    for entry in whole["entries"]:
        if entry["entry_id"] == entry_id:
            return entry
    _refuse(f"entry {name_value(entry_id)} is not among the entries of the "
            f"target it names")


def _relationship(store, canonical_target_id):
    """Everything one target IS, adopted together, proved together, and READ
    IN ONE SNAPSHOT.

    Eighth review of 2026-09-06 [P1]: "adopted together" was true of the proof
    and false of the reads underneath it. The target row, the entries, the
    leases and the whole journal were four autocommit statements, so an
    ordinary concurrent grant -- exactly the schedule this store exists to
    serialize -- could commit between two of them and leave this pass holding a
    composite that never existed: a target at fence 0 beside a journal at fence
    1. It then reported that as corruption, which is the worst possible answer
    because nothing was corrupt and an exact retry owed its first outcome.

    The snapshot is re-entrant, so inside `transact` the write transaction the
    caller already holds IS the observation and no second one is opened.
    """
    with store.snapshot():
        return _whole(store, canonical_target_id)


def _whole(store, canonical_target_id):
    target = _target_row(store, canonical_target_id)
    entries = [_entry_row(row) for row in store._connection.execute(
        "SELECT * FROM entries WHERE canonical_target_id = ? ORDER BY rank",
        (canonical_target_id,))] if target is not None else []
    leases = [_lease_row(row) for row in store._connection.execute(
        "SELECT * FROM leases WHERE canonical_target_id = ? ORDER BY fence",
        (canonical_target_id,))] if target is not None else []
    history = _history(store)
    pending = _pending_act(store)
    if target is None:
        # A TARGET ROW CAN BE ABSENT. Its activation cannot.
        for act in history:
            if act["kind"] == "target.activate" and \
                    _about(act) == canonical_target_id:
                _refuse(f"this store recorded the activation of target "
                        f"{name_value(canonical_target_id)} and no such target "
                        f"is materialized")
        return None
    _prove(target, entries, leases)
    _agrees_with_the_journal(store, target, entries, leases, history, pending)
    return {"target": target, "entries": entries, "leases": leases}


# EVERY ACT THIS STORE CAN HAVE RECORDED, AND WHAT IT MUST CARRY. A journal
# row is persisted input like any other, so its signature is adopted against
# this before it is believed. A kind this build does not own refuses the read
# rather than being skipped: a store carrying acts this process cannot reason
# about is not one it can prove anything about.
# EVERY ACT THIS STORE CAN HAVE RECORDED. A journal row is persisted input, so
# its signature is adopted against this and its operands are owned by the SAME
# rules that owned them at admission -- `_settlement`, `_ending`, `_recovery`,
# the eligibility account, the target document. A kind this build does not own
# refuses the read rather than being skipped: a store carrying acts this
# process cannot reason about is not one it can prove anything about.
JOURNAL_OPERANDS = {
    "target.activate": ("target",),
    "entry.enqueue": ("canonical_target_id", "entry_id", "eligibility"),
    "lease.grant": ("canonical_target_id", "lease_id",
                    "integrator_participant", "attempt_id"),
    "entry.integrated": ("entry_id", "lease_id", "canonical_target_id",
                         "fence", "settlement"),
    "entry.refuse": ("canonical_target_id", "entry_id", "settlement",
                     "lease_id", "fence"),
    "target.block": ("canonical_target_id", "entry_id", "lease_id", "fence",
                     "account"),
    "lease.release": ("lease_id", "canonical_target_id", "entry_id", "fence",
                      "ending"),
    "lease.abandon": ("lease_id", "fence", "recovery"),
}

TARGET_ROW = tuple(schema.TARGET_COLUMNS)
ENTRY_ROW = tuple(schema.ENTRY_COLUMNS) + ("eligibility",)
LEASE_ROW = tuple(schema.LEASE_COLUMNS)

# What a recorded act's result must still say about the row it produced. The
# generated members -- rank, fence, the instants -- necessarily come from the
# result rather than the signed request, which is why the result is first
# proved to BE the result of that exact signed act.
ACTIVATED_TARGET = ("canonical_target_id", "document", "digest",
                    "activated_at")
ENQUEUED_ENTRY = ("entry_id", "canonical_target_id", "rank",
                  "enqueued_at") + ELIGIBILITY_MEMBERS
GRANTED_LEASE = ("lease_id", "canonical_target_id", "entry_id",
                 "integrator_participant", "attempt_id", "fence",
                 "granted_at")


def _block_operation(canonical_target_id, entry_id):
    """The identity a block of this exact pair commits under.

    THE PAIR IS DIGESTED RATHER THAN CONCATENATED. `"target.block:" + a + ":"
    + b` does not compose uniquely when either id may contain a colon: target
    `a` with entry `b:c` and target `a:b` with entry `c` spell one operation.
    """
    return ("target.block:" + canonical_target_id + ":"
            + digest({"canonical_target_id": canonical_target_id,
                      "entry_id": entry_id}))


def _activation_operation(document):
    return ("target.activate:" + document["canonical_target_id"] + ":"
            + digest({"canonical_target_id": document["canonical_target_id"],
                      "document": document}))


def _owned_target(value, what):
    """One target document, owned exactly as `activate_target` owns it."""
    taken = boundaries.document(value, what, required=TARGET_MEMBERS)
    if taken["schema"] != TARGET_SCHEMA:
        _refuse(f"{what} is {name_value(taken['schema'])}; this build owns "
                f"{name_value(TARGET_SCHEMA)}")
    boundaries.identity(taken["canonical_target_id"], f"{what}'s identity")
    boundaries.text(taken["description"], f"{what}'s description")
    return taken


# The two members that COUNT FROM ONE. `boundaries.generation` counts from
# zero, which is right for an assignment generation in the manager's own
# vocabulary and wrong for these two columns, whose CHECK constraints say `>=
# 1`. The gap was reachable: a zero passed the boundary and reached SQLite as a
# raw `IntegrityError` escaping this package as something no caller can act on
# -- found by the profile binding's own type matrix, and true of
# `assignment_generation` all along.
COUNTED_FROM_ONE = ("assignment_generation", "profile_version")


def _counted_from_one(value, what):
    boundaries.generation(value, what)
    if value < 1:
        _refuse(f"{what} counts from one; this is {name_value(value)}")
    return value


def _owned_account(value, what):
    """One eligibility account, owned exactly as `enqueue` owns it."""
    account = boundaries.document(value, what, required=ELIGIBILITY_MEMBERS)
    for name in ELIGIBILITY_MEMBERS:
        if name in COUNTED_FROM_ONE:
            _counted_from_one(account[name], f"{what}'s {name}")
        else:
            boundaries.text(account[name], f"{what}'s {name}")
    schema.check_authority(account["authority_uuid"], what=f"{what}'s Authority")
    return account


def _operands_of(kind, value):
    """One act's operands, owned by the rules that owned them at admission.

    Sixth review of 2026-09-06 [P1]: `JOURNAL_OPERANDS` closed the key SET and
    validated none of the member semantics it was being trusted for, so a
    signed account whose `candidate_digest` was the integer 7 was evidence.
    A member set is not a shape -- the third time this record has had to say
    so, and the reason these now go through the admission owners themselves
    rather than through a second spelling of them.
    """
    what = f"the operands of {kind}"
    operands = boundaries.document(value, what, required=JOURNAL_OPERANDS[kind])
    if kind == "target.activate":
        operands["target"] = _owned_target(operands["target"],
                                           "a recorded target document")
        return operands
    if kind == "entry.enqueue":
        boundaries.identity(operands["canonical_target_id"], f"{what}'s target")
        boundaries.identity(operands["entry_id"], f"{what}'s entry id")
        operands["eligibility"] = _owned_account(
            operands["eligibility"], "a recorded eligibility account")
        return operands
    if kind == "lease.grant":
        boundaries.identity(operands["canonical_target_id"], f"{what}'s target")
        boundaries.identity(operands["lease_id"], f"{what}'s lease id")
        boundaries.text(operands["integrator_participant"],
                        f"{what}'s integrator")
        boundaries.identity(operands["attempt_id"], f"{what}'s attempt id")
        return operands
    if kind == "lease.abandon":
        boundaries.identity(operands["lease_id"], f"{what}'s lease id")
        boundaries.generation(operands["fence"], f"{what}'s fence")
        operands["recovery"] = _recovery(operands["recovery"],
                                         "a recorded recovery account")
        return operands
    boundaries.identity(operands["canonical_target_id"], f"{what}'s target")
    if kind == "entry.integrated":
        boundaries.identity(operands["entry_id"], f"{what}'s entry id")
        boundaries.identity(operands["lease_id"], f"{what}'s lease id")
        boundaries.generation(operands["fence"], f"{what}'s fence")
        operands["settlement"] = _settlement(operands["settlement"],
                                             "integrated",
                                             "a recorded settlement")
    elif kind == "entry.refuse":
        boundaries.identity(operands["entry_id"], f"{what}'s entry id")
        operands["settlement"] = _settlement(operands["settlement"], "refused",
                                             "a recorded refusal")
        # A queued entry is refused with no grant at all, so these two are
        # legitimately absent -- and absent is `None`, not anything else.
        if operands["lease_id"] is not None:
            boundaries.identity(operands["lease_id"], f"{what}'s lease id")
            boundaries.generation(operands["fence"], f"{what}'s fence")
        elif operands["fence"] is not None:
            _refuse(f"{what} names a fence and no lease")
    elif kind == "target.block":
        boundaries.identity(operands["entry_id"], f"{what}'s entry id")
        boundaries.identity(operands["lease_id"], f"{what}'s lease id")
        boundaries.generation(operands["fence"], f"{what}'s fence")
        operands["account"] = _settlement(operands["account"], "held",
                                          "a recorded block account")
    else:
        boundaries.identity(operands["entry_id"], f"{what}'s entry id")
        boundaries.identity(operands["lease_id"], f"{what}'s lease id")
        boundaries.generation(operands["fence"], f"{what}'s fence")
        operands["ending"] = _ending(operands["ending"], "released",
                                     "a recorded lease ending")
    return operands


def _identity_of(kind, operands):
    """The identity this exact signed act commits under, RE-DERIVED.

    Sixth review [P0]: identities were read off the row and never recomputed,
    so a noncanonical one could stand in for another committed act, or make a
    second act for one logical subject.
    """
    if kind == "target.activate":
        return _activation_operation(operands["target"])
    if kind == "target.block":
        return _block_operation(operands["canonical_target_id"],
                                operands["entry_id"])
    if kind in ("entry.enqueue", "entry.integrated", "entry.refuse"):
        return kind + ":" + operands["entry_id"]
    return kind + ":" + operands["lease_id"]


def _recorded_row(value, what, members):
    return boundaries.document(value, what, required=members)


def _agree(what, was, now, members):
    for name in members:
        if was[name] != now[name]:
            _refuse(f"{what} recorded {name} {name_value(was[name])} and it is "
                    f"now {name_value(now[name])}")


def _result_of(kind, operands, value):
    """The result, adopted as this kind's variant AND bound to its request.

    THIS IS THE SIDE THAT WAS MISSING. Sixth review [P0]: an enqueue's result
    was compared to the materialized row and to nothing else, so rewriting
    BOTH of those redundant surfaces left two agreeing witnesses and a signed
    request that contradicted them -- and selection believed the two. The
    signed request is the one thing a rewrite cannot reach without changing
    what was accepted, so the result is proved to be the result OF it before
    it is used as evidence about anything.
    """
    if kind == "lease.grant" and value is None:
        # THE TYPED EMPTY GRANT. A grant over an empty queue commits, records
        # `null`, and creates no lease; that is a real outcome, not a missing
        # one, and it is the only kind whose result may be absent.
        return None
    if value is None:
        _refuse(f"a committed {kind} records no result")
    if kind == "target.activate":
        was = _recorded_row(value, f"the result of {kind}", TARGET_ROW)
        _owned_target(was["document"], "a recorded target's document")
        if was["canonical_target_id"] != \
                operands["target"]["canonical_target_id"] \
                or was["document"] != operands["target"] \
                or was["digest"] != digest(operands["target"]):
            _refuse(f"the recorded activation of "
                    f"{name_value(was['canonical_target_id'])} is not the "
                    f"result of the activation that was signed")
        if (was["state"], was["fence"], was["blocked_reason"],
                was["blocked_account"]) != ("open", 0, None, None):
            _refuse(f"the recorded activation of "
                    f"{name_value(was['canonical_target_id'])} did not adopt "
                    f"an open target at fence zero")
        boundaries.instant(was["activated_at"], "a recorded adoption instant")
        return was
    if kind == "entry.enqueue":
        was = _recorded_entry(value, kind)
        if was["entry_id"] != operands["entry_id"] \
                or was["canonical_target_id"] != operands["canonical_target_id"]:
            _refuse(f"the recorded enqueue of "
                    f"{name_value(was['entry_id'])} is not the result of the "
                    f"enqueue that was signed")
        _agree(f"the signed enqueue of {name_value(operands['entry_id'])}",
               operands["eligibility"], was, ELIGIBILITY_MEMBERS)
        if was["state"] != "queued" or was["settled_at"] is not None:
            _refuse(f"the recorded enqueue of {name_value(was['entry_id'])} "
                    f"did not place a queued entry")
        boundaries.generation(was["rank"], "a recorded rank")
        boundaries.instant(was["enqueued_at"], "a recorded enqueue instant")
        return was
    if kind == "lease.grant":
        was = boundaries.document(value, f"the result of {kind}",
                                  required=("lease", "entry"))
        lease = _recorded_row(was["lease"], "a recorded lease", LEASE_ROW)
        entry = _recorded_entry(was["entry"], kind)
        if (lease["lease_id"], lease["canonical_target_id"],
                lease["integrator_participant"], lease["attempt_id"]) != \
                (operands["lease_id"], operands["canonical_target_id"],
                 operands["integrator_participant"], operands["attempt_id"]):
            _refuse(f"the recorded grant of "
                    f"{name_value(lease['lease_id'])} is not the result of the "
                    f"grant that was signed")
        if lease["state"] != "live" or lease["entry_id"] != entry["entry_id"] \
                or entry["state"] != "leased":
            _refuse(f"the recorded grant of {name_value(lease['lease_id'])} "
                    f"did not lease the entry it names")
        boundaries.generation(lease["fence"], "a recorded fence")
        boundaries.instant(lease["granted_at"], "a recorded grant instant")
        was["lease"], was["entry"] = lease, entry
        return was
    if kind in ("entry.integrated", "entry.refuse"):
        was = _recorded_entry(value, kind)
        settled = "integrated" if kind == "entry.integrated" else "refused"
        if was["entry_id"] != operands["entry_id"] \
                or was["canonical_target_id"] != operands["canonical_target_id"] \
                or was["state"] != settled \
                or was["settlement"] != operands["settlement"]:
            _refuse(f"the recorded {kind} of {name_value(was['entry_id'])} is "
                    f"not the result of the act that was signed")
        return was
    if kind == "target.block":
        was = boundaries.document(value, f"the result of {kind}",
                                  required=("target", "entry"))
        held = _recorded_row(was["target"], "a recorded target", TARGET_ROW)
        entry = _recorded_entry(was["entry"], kind)
        if held["canonical_target_id"] != operands["canonical_target_id"] \
                or held["state"] != "blocked" \
                or held["blocked_reason"] != operands["account"]["reason"] \
                or entry["entry_id"] != operands["entry_id"] \
                or entry["state"] != "held" \
                or entry["settlement"] != operands["account"]:
            _refuse(f"the recorded block of "
                    f"{name_value(operands['canonical_target_id'])} is not the "
                    f"result of the block that was signed")
        account = boundaries.document(held["blocked_account"],
                                      "a recorded blocked account",
                                      required=BLOCK_MEMBERS)
        if (account["entry_id"], account["lease_id"], account["fence"]) != \
                (operands["entry_id"], operands["lease_id"],
                 operands["fence"]):
            _refuse(f"the recorded block of "
                    f"{name_value(operands['canonical_target_id'])} names a "
                    f"different grant from the one that was signed")
        was["target"], was["entry"] = held, entry
        return was
    was = _recorded_row(value, f"the result of {kind}", LEASE_ROW)
    ended = "released" if kind == "lease.release" else "abandoned"
    ending = (operands["ending"] if kind == "lease.release"
              else {"outcome": "abandoned", "recovery": operands["recovery"]})
    if was["lease_id"] != operands["lease_id"] or was["state"] != ended \
            or was["fence"] != operands["fence"] or was["ending"] != ending:
        _refuse(f"the recorded {kind} of {name_value(was['lease_id'])} is not "
                f"the result of the act that was signed")
    boundaries.instant(was["ended_at"], "a recorded ending instant")
    return was


def _recorded_entry(value, kind):
    was = _recorded_row(value, f"the entry recorded by {kind}", ENTRY_ROW)
    boundaries.identity(was["entry_id"], "a recorded entry id")
    boundaries.identity(was["canonical_target_id"], "a recorded target")
    _owned_account(was["eligibility"], "a recorded account")
    _agree(f"the entry recorded by {kind}", was["eligibility"], was,
           ELIGIBILITY_MEMBERS)
    if was["settlement"] is not None:
        _settlement(was["settlement"], was["state"], "a recorded settlement")
    return was


def _act(operation_id, kind, signature, result):
    """ONE journal act, adopted whole: kind, operands, identity and result."""
    if kind not in JOURNAL_OPERANDS:
        _refuse(f"operation {name_value(operation_id)} records kind "
                f"{name_value(kind)}, which this build does not own")
    signed = boundaries.document(signature, "a persisted operation signature",
                                 required=("kind", "operands"))
    if signed["kind"] != kind:
        _refuse(f"operation {name_value(operation_id)} is recorded "
                f"{name_value(kind)} and signed {name_value(signed['kind'])}")
    operands = _operands_of(kind, signed["operands"])
    canonical = _identity_of(kind, operands)
    if canonical != operation_id:
        _refuse(f"operation {name_value(operation_id)} signs operands that "
                f"commit under {name_value(canonical)}; an identity is derived "
                f"from what was asked, not recorded beside it")
    return {"operation_id": operation_id, "kind": kind, "operands": operands,
            "result": result if result is _ABSENT
            else _result_of(kind, operands, result)}


_ABSENT = object()


def _history(store):
    """Every committed act this store has recorded, IN THE ORDER IT COMMITTED.

    A GLOBAL SCAN, deliberately and with its cost stated. The review of
    2026-09-06T03:22 accepted one for this slice; what it buys is that a
    deleted row is no longer invisible, because the act that created it is
    still here. An indexed target binding would be the way to make it cheaper,
    and it would need its own schema and adoption proof.

    THE ORDER IS EVIDENCE, not a convenience for the reader. Seventh review of
    2026-09-06 [P0]: a generated rank or fence has no request-side witness, so
    the position an act holds among all of them is the only surviving statement
    about what was allocated -- see `_generated_by_the_order`. It is proved
    DENSE FROM ONE here rather than merely sorted, because a sorted sequence
    with a hole in it is an act somebody removed, and the whole point of asking
    the journal is that removal stops being invisible.
    """
    acts = []
    position = 0
    for row in store._connection.execute(
            "SELECT * FROM operations ORDER BY seq"):
        record = boundaries.row(row, "a persisted operation record",
                                schema.OPERATION_COLUMNS)
        position += 1
        if record["seq"] != position:
            _refuse(f"this store's journal holds "
                    f"{name_value(record['operation_id'])} at position "
                    f"{record['seq']} where its act number {position} belongs; "
                    f"the order acts committed in is dense from one")
        act = _recorded_act(record)
        if record["state"] == "committed":
            acts.append(act)
    _no_duplicates(acts)
    return acts


def _recorded_act(record):
    """One journal row, owned whichever outcome it recorded.

    Eighth review of 2026-09-06 [P1]: a refused row was skipped the moment its
    generic columns and its position had been checked, so `_act` never owned
    its kind, its operands or its derived identity. "A kind this build does not
    own refuses the read" was therefore true of committed rows only, and a
    schema-valid refused row of kind `unknown.kind` sat in a sound target's
    journal while every door answered normally.

    A refused act has no materialized effect to be bound to -- it changed
    nothing, which is what makes it a refusal -- but everything it SAYS is
    still this coordinator's evidence: which act was asked for, by whom, under
    which operands, at which position, and with which sealed outcome.
    `OPERATION_COLUMNS` has already owned the seal; this owns the rest.
    """
    if record["state"] != "committed":
        return _act(record["operation_id"], record["kind"],
                    json.loads(record["signature"]), _ABSENT)
    if record["result"] is None:
        # SQL NULL, which the CHECK permits for a committed row and this
        # build never writes. Sixth review [P1]: it reached `json.loads`
        # and escaped as a raw `TypeError`.
        _refuse(f"operation {name_value(record['operation_id'])} is "
                f"committed and records no result at all")
    return _act(record["operation_id"], record["kind"],
                json.loads(record["signature"]),
                json.loads(record["result"]))


def _proved(store, row):
    """ONE recorded act, adopted whole and bound to what it materialized.

    BOTH OUTCOMES, and the eighth review [P1] is why that is stated first: a
    refused row used to be answered by the store before this ran, so an exact
    refused retry hid a journal hole that the very next ordinary read found.
    A refused act has no materialized effect to bind, but its kind, operands,
    derived identity, dense position and sealed outcome are proved before it
    is replayed, and so is the relationship it was refused against.

    THE SEMANTIC OWNER `IntegrationStore.replay` DOES NOT HAVE. Seventh review
    of 2026-09-06 [P0]: every exact retry returned `json.loads(result)` from a
    raw journal row, so the retry path -- the one that exists to make a
    transition effectively ONCE -- was the single door in this module that
    reached none of the proofs the ordinary doors reach. Two consequences the
    review demonstrated: a rewritten enqueue result replayed as the caller's
    own candidate, and a fabricated committed `entry.integrated` replayed as a
    successful post-import cutpoint while its entry was still `leased` and
    nothing had settled.

    So a replay proves the same three things a read proves, in the same order:
    the act's operands are owned by their admission owners, its identity is
    re-derived from them, its result is adopted as that kind's variant and
    bound to the signed request -- and then the whole materialized
    relationship it belongs to is proved, which is what refuses a result that
    describes an effect the store does not have.
    """
    act = _recorded_act(row)
    canonical_target_id = _about(act)
    if canonical_target_id is not None:
        if _relationship(store, canonical_target_id) is None:
            _refuse(f"operation {name_value(row['operation_id'])} is recorded "
                    f"against target {name_value(canonical_target_id)}, which "
                    f"this store does not hold")
    elif act["result"] is not _ABSENT:
        # `lease.abandon` names its target only through the lease it ended,
        # and the lease it ended is what its result IS.
        if _relationship(store, boundaries.identity(
                act["result"]["canonical_target_id"],
                "a recorded recovery's target")) is None:
            _refuse(f"operation {name_value(row['operation_id'])} is recorded "
                    f"against a target this store does not hold")
    else:
        # A REFUSED recovery has neither: its operands name only the lease, and
        # it produced no result to name the target. `lease_of` reaches the same
        # relationship through the lease when there is one, and the durable
        # history either way.
        _lease_of(store, act["operands"]["lease_id"])
    if act["result"] is _ABSENT:
        # The recorded outcome, replayed rather than re-decided -- and now
        # AFTER the proofs above, which is the whole of the eighth review's
        # second [P1]. `revive_refusal` adopts persisted TEXT.
        raise revive_refusal(row["refusal"])
    return act["result"]


def _transact(store, operation_id, kind, signature, action):
    """Every journalled act of this store, through ONE semantic owner.

    The witness is named here rather than at eight call sites so that "every
    public mutator reaches that path" is a fact about this function instead of
    a list somebody maintains.
    """
    return store.transact(operation_id, kind, signature, action,
                          witness=_proved)


def _no_duplicates(acts):
    """One logical act commits once.

    The derived identity makes a second act for one subject impossible through
    the primary key, so this is the belt to that brace: a store that somehow
    holds two is refused rather than having one of them silently win a
    dictionary.
    """
    seen = set()
    for act in acts:
        subject = (act["kind"], _about(act) or "",
                   act["operands"].get("entry_id")
                   or act["operands"].get("lease_id") or "")
        if subject in seen:
            _refuse(f"this store records two committed {act['kind']} acts for "
                    f"one subject")
        seen.add(subject)


def _about(act):
    """The target an act names directly, or None if it names one only through
    the lease it is about."""
    if act["kind"] == "target.activate":
        return act["operands"]["target"]["canonical_target_id"]
    return act["operands"].get("canonical_target_id")


def _pending_act(store):
    """The one act between its write and its record, adopted the same way.

    Sixth review [P0]: the window excused a row on the strength of the pending
    operation IDENTITY alone, which is provenance a caller chooses. The
    pending act's signed operands are adopted here by the same owner, its
    identity is re-derived from them, and what it excuses is a row that
    matches what it asked for.
    """
    pending = store._pending
    if pending is None:
        return None
    return _act(pending["operation_id"], pending["kind"],
                json.loads(pending["signature"]), _ABSENT)


def _agrees_with_the_journal(store, target, entries, leases, history,
                             pending):
    """The materialized rows and the durable history, proved BOTH ways."""
    canonical_target_id = target["canonical_target_id"]
    by_entry = {one["entry_id"]: one for one in entries}
    by_lease = {one["lease_id"]: one for one in leases}
    ours = [act for act in history if _about(act) == canonical_target_id]
    recorded = {act["operation_id"]: act for act in history}
    asked = pending["operands"] if pending is not None else {}
    pending_id = pending["operation_id"] if pending is not None else None

    activations = [act for act in ours if act["kind"] == "target.activate"]
    if len(activations) > 1:
        _refuse(f"target {name_value(canonical_target_id)} records "
                f"{len(activations)} activations, and a target is adopted once")
    if not activations:
        if pending is None or pending["kind"] != "target.activate":
            _refuse(f"target {name_value(canonical_target_id)} is materialized "
                    f"and this store recorded no activation of it")
        # THE PENDING ACT IS BOUND, NOT BELIEVED: the row must be the one it
        # asked for.
        if target["document"] != asked["target"] \
                or target["digest"] != digest(asked["target"]):
            _refuse(f"target {name_value(canonical_target_id)} is being "
                    f"activated under another configuration than the one "
                    f"materialized")
    else:
        _agree(f"the activation of target {name_value(canonical_target_id)}",
               activations[0]["result"], target, ACTIVATED_TARGET)

    enqueued = {act["operands"]["entry_id"]: act for act in ours
                if act["kind"] == "entry.enqueue"}
    for entry_id, act in enqueued.items():
        if entry_id not in by_entry:
            _refuse(f"this store recorded the enqueue of entry "
                    f"{name_value(entry_id)} on target "
                    f"{name_value(canonical_target_id)} and no such entry is "
                    f"materialized")
        _agree(f"the enqueue of entry {name_value(entry_id)}", act["result"],
               by_entry[entry_id], ENQUEUED_ENTRY)
    for entry_id, entry in by_entry.items():
        if entry_id in enqueued:
            continue
        if pending_id != "entry.enqueue:" + entry_id:
            _refuse(f"entry {name_value(entry_id)} is materialized on target "
                    f"{name_value(canonical_target_id)} and this store "
                    f"recorded no enqueue of it here")
        if entry["canonical_target_id"] != asked["canonical_target_id"]:
            _refuse(f"entry {name_value(entry_id)} is being enqueued on "
                    f"{name_value(asked['canonical_target_id'])} and is "
                    f"materialized on {name_value(canonical_target_id)}")
        _agree(f"the enqueue being made of {name_value(entry_id)}",
               asked["eligibility"], entry, ELIGIBILITY_MEMBERS)

    granted = {}
    for act in ours:
        if act["kind"] != "lease.grant" or act["result"] is None:
            continue
        granted[act["result"]["lease"]["lease_id"]] = act["result"]["lease"]
    for lease_id, was in granted.items():
        if lease_id not in by_lease:
            _refuse(f"this store recorded the grant of lease "
                    f"{name_value(lease_id)} on target "
                    f"{name_value(canonical_target_id)} and no such lease is "
                    f"materialized")
        _agree(f"the grant of lease {name_value(lease_id)}", was,
               by_lease[lease_id], GRANTED_LEASE)
    for lease_id, lease in by_lease.items():
        if lease_id in granted:
            continue
        if pending_id != "lease.grant:" + lease_id:
            _refuse(f"lease {name_value(lease_id)} is materialized on target "
                    f"{name_value(canonical_target_id)} and this store "
                    f"recorded no grant of it here")
        if (lease["canonical_target_id"], lease["integrator_participant"],
                lease["attempt_id"]) != \
                (asked["canonical_target_id"],
                 asked["integrator_participant"], asked["attempt_id"]):
            _refuse(f"lease {name_value(lease_id)} is being granted to another "
                    f"holder than the one materialized")

    # THE GENERATED DECISIONS, against the one witness that is neither the
    # result nor the row. This also decides the fence: taking it from the
    # remaining lease rows is what let a deleted lease hand its fence back, and
    # taking it from the surviving grant results is what let a rewritten pair
    # agree about a history that did not happen.
    _generated_by_the_order(canonical_target_id, ours, pending, by_entry,
                            by_lease, target)

    _terminal_acts_agree(canonical_target_id, entries, leases, recorded,
                         pending)


def _generated_by_the_order(canonical_target_id, ours, pending, by_entry,
                            by_lease, target):
    """Rank, fence and selection, DERIVED from the order the acts committed in.

    Seventh review of 2026-09-06 [P0]. A generated decision has no
    request-side witness and cannot have one: `enqueue` cannot sign the rank it
    is about to allocate and `grant_lease` cannot sign the fence it is about to
    burn. So the only two surviving statements about them were the recorded
    result and the materialized row -- and the review rewrote BOTH, putting
    entry 1 behind entry 2 at rank 3. The signed enqueue was still present and
    still true; it simply never said anything about rank, so nothing
    contradicted the pair and selection followed the reversed queue.

    THE ORDER SAYS ALL THREE. Ranks are dense from one and allocated by enqueue
    alone, so a target's Nth enqueue allocated rank N. Fences are burned by
    grants alone and increase by one in the granting transaction, so its Nth
    grant that took a lease burned fence N. And a grant takes the smallest
    QUEUED rank, so replaying the enqueues and settlements that preceded each
    grant says which entry that grant could have selected. None of the three is
    reachable by rewriting a result or a row.

    WHAT THIS IS NOT. There is no durable secret here to sign an order with, so
    a writer who also rewrites `operations.seq` presents a self-consistent
    alternative history and this seam cannot tell it from the real one. The
    claim is exact: the two-surface rewrite now contradicts a third surface
    that neither of those surfaces touches.
    """
    acts = list(ours)
    if pending is not None and _about(pending) == canonical_target_id:
        # It will take the next position in the order, so it is derived last.
        acts.append(pending)
    pending_id = pending["operation_id"] if pending is not None else None
    ranks, taken, fence = {}, set(), 0
    for act in acts:
        entry_id = act["operands"].get("entry_id")
        if act["kind"] == "entry.enqueue":
            ranks[entry_id] = len(ranks) + 1
            _allocated_rank(canonical_target_id, act, pending_id, ranks,
                            by_entry)
        elif act["kind"] == "lease.grant":
            fence = _selected_entry(canonical_target_id, act, pending_id,
                                    ranks, taken, fence, by_lease)
        elif act["kind"] in ("entry.integrated", "entry.refuse",
                             "target.block"):
            # A settlement takes an entry out of the queue. Only the refusal
            # of a never-granted entry is not already out of it, and adding
            # the other two costs nothing and states the rule once.
            taken.add(entry_id)
    if target["fence"] != fence:
        _refuse(f"target {name_value(canonical_target_id)} records fence "
                f"{target['fence']} and the greatest fence in its durable "
                f"history is {fence}")


def _allocated_rank(canonical_target_id, act, pending_id, ranks, by_entry):
    entry_id = act["operands"]["entry_id"]
    allocated = ranks[entry_id]
    if act["operation_id"] == pending_id:
        # The act between its write and its record. It has written its entry
        # or it has not yet; what it may not do is write another rank.
        entry = by_entry.get(entry_id)
        if entry is not None and entry["rank"] != allocated:
            _refuse(f"entry {name_value(entry_id)} is being enqueued as "
                    f"target {name_value(canonical_target_id)}'s enqueue "
                    f"number {allocated} and is materialized at rank "
                    f"{entry['rank']}")
        return
    if act["result"]["rank"] != allocated:
        _refuse(f"entry {name_value(entry_id)} is enqueue number "
                f"{allocated} on target {name_value(canonical_target_id)} and "
                f"its enqueue recorded rank {act['result']['rank']}; rank is "
                f"allocated in arrival order and is not a value a later edit "
                f"chooses")


def _selected_entry(canonical_target_id, act, pending_id, ranks, taken, fence,
                    by_lease):
    """The entry this grant could have taken, and the fence it could have
    burned."""
    lease_id = act["operands"]["lease_id"]
    queued = sorted((one for one in ranks if one not in taken),
                    key=lambda one: ranks[one])
    smallest = queued[0] if queued else None
    if act["operation_id"] == pending_id:
        lease = by_lease.get(lease_id)
        if lease is None:
            # It has not written yet; an empty queue never will.
            return fence
        granted, burned = lease["entry_id"], lease["fence"]
    elif act["result"] is None:
        # THE TYPED EMPTY GRANT, and it is a claim about the queue: nothing was
        # offered because nothing was there.
        if smallest is not None:
            _refuse(f"a grant on target {name_value(canonical_target_id)} "
                    f"recorded no lease while entry {name_value(smallest)} "
                    f"stood at rank {ranks[smallest]}")
        return fence
    else:
        granted = act["result"]["entry"]["entry_id"]
        burned = act["result"]["lease"]["fence"]
    if smallest is None:
        _refuse(f"lease {name_value(lease_id)} took entry "
                f"{name_value(granted)} on target "
                f"{name_value(canonical_target_id)}, whose queue was empty "
                f"when it was granted")
    if granted != smallest:
        _refuse(f"lease {name_value(lease_id)} took entry "
                f"{name_value(granted)} while entry {name_value(smallest)} "
                f"stood at rank {ranks[smallest]}; a grant takes the smallest "
                f"queued rank, and which one that was is the order's to say")
    if burned != fence + 1:
        _refuse(f"lease {name_value(lease_id)} is target "
                f"{name_value(canonical_target_id)}'s grant number "
                f"{fence + 1} and burned fence {burned}; the fence increases "
                f"by one in the transaction that grants")
    taken.add(granted)
    return burned


def _terminal_acts_agree(canonical_target_id, entries, leases, recorded,
                         pending):
    """The acts that settled things, and the states they settled, both ways."""
    pending_id = pending["operation_id"] if pending is not None else None
    asked = pending["operands"] if pending is not None else {}

    def excused(name, settlement, member):
        """The pending act may explain this state -- if it asked for it."""
        if pending_id != name:
            return False
        if asked.get(member) != settlement:
            _refuse(f"the act now settling {name_value(name)} accounts for it "
                    f"differently from the row it has written")
        return True

    for entry in entries:
        entry_id = entry["entry_id"]
        settling = {"entry.integrated:" + entry_id:
                    ("integrated", "settlement"),
                    "entry.refuse:" + entry_id: ("refused", "settlement"),
                    _block_operation(canonical_target_id, entry_id):
                    ("held", "account")}
        for name, (state, member) in settling.items():
            act = recorded.get(name)
            if act is not None and entry["state"] != state:
                _refuse(f"this store recorded {name_value(name)} and that "
                        f"entry is {name_value(entry['state'])} rather than "
                        f"{name_value(state)}")
            if act is not None and entry["state"] == state and \
                    entry["settlement"] != act["operands"][member]:
                _refuse(f"this store recorded {name_value(name)} and the "
                        f"entry accounts for it differently")
            if entry["state"] == state and act is None and \
                    not excused(name, entry["settlement"], member):
                _refuse(f"entry {name_value(entry_id)} is {name_value(state)} "
                        f"and this store recorded no act that settled it")
    for lease in leases:
        lease_id = lease["lease_id"]
        for name, state in (("lease.release:" + lease_id, "released"),
                            ("lease.abandon:" + lease_id, "abandoned")):
            act = recorded.get(name)
            if act is not None and lease["state"] != state:
                _refuse(f"this store recorded {name_value(name)} and that "
                        f"lease is {name_value(lease['state'])} rather than "
                        f"{name_value(state)}")
            if act is not None and lease["state"] == state and \
                    lease["ending"] != act["result"]["ending"]:
                _refuse(f"this store recorded {name_value(name)} and the lease "
                        f"ends differently")
        if lease["state"] == "abandoned" and \
                "lease.abandon:" + lease_id not in recorded and \
                pending_id != "lease.abandon:" + lease_id:
            _refuse(f"lease {name_value(lease_id)} is abandoned and this store "
                    f"recorded no recovery that ended it")
        # A RELEASE HAS TWO ACTS THAT CAN PRODUCE IT. `release_lease` is one;
        # the other is the refusal that ends its entry's lease in the same
        # transaction, which records nothing of its own.
        if lease["state"] == "released" and \
                "lease.release:" + lease_id not in recorded and \
                "entry.refuse:" + lease["entry_id"] not in recorded and \
                pending_id not in ("lease.release:" + lease_id,
                                   "entry.refuse:" + lease["entry_id"]):
            _refuse(f"lease {name_value(lease_id)} is released and this store "
                    f"recorded neither a release of it nor the refusal of "
                    f"entry {name_value(lease['entry_id'])}")


def _target_row(store, canonical_target_id):
    """The target row, with its document proved to be about it.

    THE DOCUMENT IS NOT TRUSTED BECAUSE IT IS OURS. Review of 2026-09-06 [P1]:
    the stored document was decoded and handed back without proving it
    describes the row that carries it, so a target could answer with one
    identity in its key and another in its configuration. Redundant evidence
    that nothing compares is worse than none: it reads as corroboration.
    """
    found = _row(store._connection.execute(
        "SELECT * FROM targets WHERE canonical_target_id = ?",
        (canonical_target_id,)).fetchone(),
        "a persisted integration target", schema.TARGET_COLUMNS)
    if found is None:
        return None
    document = boundaries.document(json.loads(found["document"]),
                                   "a persisted target document",
                                   required=TARGET_MEMBERS)
    if document["schema"] != TARGET_SCHEMA:
        _refuse(f"the target document stored for "
                f"{name_value(canonical_target_id)} is "
                f"{name_value(document['schema'])} and this build owns "
                f"{name_value(TARGET_SCHEMA)}")
    if document["canonical_target_id"] != found["canonical_target_id"]:
        _refuse(f"the target row {name_value(found['canonical_target_id'])} "
                f"carries a document describing "
                f"{name_value(document['canonical_target_id'])}; one target is "
                f"one identity")
    if digest(document) != found["digest"]:
        _refuse(f"the target document stored for "
                f"{name_value(canonical_target_id)} does not digest to the "
                f"{name_value(found['digest'])} recorded beside it")
    found["document"] = document
    return found


def _entry_row(row):
    """One entry row, owned, with its account assembled from its columns.

    THERE IS NO SECOND COPY TO DISAGREE WITH. The first shape stored all
    seventeen operands again as one document and compared neither against the
    other; the review of 2026-09-06 changed one column and watched the reader
    hand back a row and an account that named different proposals. The account
    is now derived from the columns at the read, so it cannot contradict them.
    """
    entry = boundaries.row(row, "a persisted integration entry",
                           schema.ENTRY_COLUMNS)
    schema.check_authority(entry["authority_uuid"],
                           what="a persisted entry's Authority")
    if entry["settlement"] is not None:
        entry["settlement"] = _settlement(json.loads(entry["settlement"]),
                                          entry["state"],
                                          "a persisted entry settlement")
    entry["eligibility"] = {name: entry[name] for name in ELIGIBILITY_MEMBERS}
    return entry


def _lease_row(row):
    lease = boundaries.row(row, "a persisted integration lease",
                           schema.LEASE_COLUMNS)
    if lease["ending"] is not None:
        lease["ending"] = _ending(json.loads(lease["ending"]), lease["state"],
                                  "a persisted lease ending")
        if lease["ending"]["outcome"] == "abandoned" and \
                lease["ending"]["recovery"]["attempt_id"] != \
                lease["attempt_id"]:
            _refuse(f"lease {name_value(lease['lease_id'])} was granted to "
                    f"attempt {name_value(lease['attempt_id'])} and its "
                    f"recovery accounts for "
                    f"{name_value(lease['ending']['recovery']['attempt_id'])}")
    return lease


def _prove(target, entries, leases):
    """The state graph, as EVERY entry's whole lifecycle.

    Fourth review of 2026-09-06 [P0]: the previous pass proved selected state
    PAIRS -- live leases, held entries, abandonment against blocking -- and
    said nothing about a released lease's entry or about an entry that already
    had a lease history. So resetting an integrated, released entry to its
    schema-valid `queued` shape passed every door, and selection leased the
    same candidate again: an import whose durable account already says it
    completed, offered a second time.

    Selected pairs are how a lifecycle gets checked in the places somebody
    thought of. This states the whole of it, once, for every entry -- and the
    rule underneath it is that in the item-3 model NO entry returns to
    `queued` and no entry acquires a second lease. A later repair or retry
    design that needs either must introduce its own reviewed state and
    account; it may not arrive by weakening these.
    """
    canonical_target_id = target["canonical_target_id"]
    by_entry = {one["entry_id"]: one for one in entries}
    # A foreign key says the entry EXISTS; it says nothing about whose it is,
    # and every exclusion this store enforces is keyed on the target.
    for lease in leases:
        if lease["entry_id"] not in by_entry:
            _refuse(f"lease {name_value(lease['lease_id'])} is over target "
                    f"{name_value(canonical_target_id)} and holds entry "
                    f"{name_value(lease['entry_id'])}, which is not this "
                    f"target's")
    if len([one for one in leases if one["state"] == "live"]) > 1:
        _refuse(f"target {name_value(canonical_target_id)} holds more than one "
                f"live lease, and one target integrates one entry at a time")
    # The fence is proved in `_agrees_with_the_journal`, which is where the
    # durable history is: the greatest REMAINING lease row is not the greatest
    # grant, and the difference is exactly what deleting a lease hides.
    account = None
    if target["state"] == "blocked":
        account = _blocked_account(target, by_entry, leases)
        target["blocked_account"] = account
    holding = {}
    for lease in leases:
        holding.setdefault(lease["entry_id"], []).append(lease)
    for entry in entries:
        _prove_entry(canonical_target_id, entry,
                     holding.get(entry["entry_id"], []), account)


def _prove_entry(canonical_target_id, entry, leases, account):
    """One entry's whole lifecycle, against every lease it has ever had."""
    entry_id = entry["entry_id"]
    state = entry["state"]
    states = [one["state"] for one in leases]

    def refuse(said):
        _refuse(f"entry {name_value(entry_id)} of target "
                f"{name_value(canonical_target_id)} is {name_value(state)} "
                f"and {said}")

    if state == "queued":
        # NOTHING RETURNS TO QUEUED. An entry with a lease history has already
        # been offered, so a queued one carrying leases is a candidate about to
        # be integrated twice.
        if leases:
            refuse(f"carries lease {name_value(leases[0]['lease_id'])}; a "
                   f"queued entry has never been offered, and no entry in "
                   f"this model returns to queued")
    elif state == "leased":
        if states != ["live"]:
            refuse("no single live lease holds it")
    elif state == "integrated":
        # Live BETWEEN the two cutpoints, released with the matching ending
        # after. Both are real states of a correct integration.
        if len(leases) != 1:
            refuse(f"has {len(leases)} leases, and an integrated entry was "
                   f"integrated under exactly one")
        if states == ["released"]:
            if leases[0]["ending"]["outcome"] != "integrated":
                refuse(f"was released "
                       f"{name_value(leases[0]['ending']['outcome'])}")
        elif states != ["live"]:
            refuse(f"is under a {name_value(states[0])} lease")
    elif state == "refused":
        # Refused BEFORE selection carries no lease at all; refused under a
        # grant carries exactly the released one that ending fused.
        if leases and (len(leases) != 1 or states != ["released"]
                       or leases[0]["ending"]["outcome"] != "entry-refused"):
            refuse("does not carry exactly the one released lease its refusal "
                   "ended")
    elif state == "held":
        if account is None:
            _refuse(f"target {name_value(canonical_target_id)} is open and "
                    f"holds entry {name_value(entry_id)}; held work exists "
                    f"only under a blocked target")
        if account["entry_id"] != entry_id:
            _refuse(f"target {name_value(canonical_target_id)} is blocked over "
                    f"entry {name_value(account['entry_id'])} and also holds "
                    f"{name_value(entry_id)}")
        # Live before the recovery, abandoned after it, and it is the lease the
        # block is about -- which `_blocked_account` has already proved of the
        # account's side. This is the entry's side of the same fact.
        if len(leases) != 1 or leases[0]["lease_id"] != account["lease_id"] \
                or states[0] not in ("live", "abandoned"):
            refuse(f"does not carry exactly the "
                   f"{name_value(account['lease_id'])} the block is about, "
                   f"live or abandoned")


def _blocked_account(target, by_entry, leases):
    """The blocked account, adopted as ONE RELATIONSHIP rather than a shape.

    Re-review of 2026-09-06 [P1]: the first correction proved this account's
    member TYPES and stopped. So the write transition built the relationship
    correctly and a restart believed a contradictory one -- the re-review
    changed only the stored entry id to the target's still-queued entry and
    `target_of` returned it, and changed only the account's reason and watched
    `blocked_reason` and `blocked_account.reason` come back disagreeing.

    A block's whole purpose is to name what the recovery may end. Evidence that
    names it wrongly is worse than no evidence, because `abandon_lease` checks
    against this account and would check against the wrong one.
    """
    canonical_target_id = target["canonical_target_id"]
    account = boundaries.document(json.loads(target["blocked_account"]),
                                  "a persisted blocked-target account",
                                  required=BLOCK_MEMBERS)
    boundaries.identity(account["entry_id"], "a blocked entry id")
    boundaries.identity(account["lease_id"], "a blocked target's lease id")
    boundaries.generation(account["fence"], "a blocked target's fence")
    boundaries.text(account["integrator_participant"],
                    "a blocked target's integrator")
    boundaries.identity(account["attempt_id"], "a blocked target's attempt id")
    boundaries.text(account["reason"], "a target block reason")
    boundaries.document(account["detail"], "a target block detail")
    if account["reason"] != target["blocked_reason"]:
        _refuse(f"target {name_value(canonical_target_id)} is blocked "
                f"{name_value(target['blocked_reason'])} and its account says "
                f"{name_value(account['reason'])}")
    entry = by_entry.get(account["entry_id"])
    if entry is None:
        _refuse(f"target {name_value(canonical_target_id)} is blocked over "
                f"entry {name_value(account['entry_id'])}, which is not this "
                f"target's")
    if entry["state"] != "held":
        _refuse(f"target {name_value(canonical_target_id)} is blocked over "
                f"entry {name_value(account['entry_id'])}, which is "
                f"{name_value(entry['state'])} rather than held")
    if (entry["settlement"]["reason"], entry["settlement"]["detail"]) != \
            (account["reason"], account["detail"]):
        _refuse(f"the block on target {name_value(canonical_target_id)} and "
                f"the settlement of entry {name_value(account['entry_id'])} "
                f"account for it differently")
    named = [one for one in leases if one["lease_id"] == account["lease_id"]]
    if not named:
        _refuse(f"target {name_value(canonical_target_id)} is blocked under "
                f"lease {name_value(account['lease_id'])}, which is not this "
                f"target's")
    lease = named[0]
    if (lease["entry_id"], lease["fence"], lease["integrator_participant"],
            lease["attempt_id"]) != \
            (account["entry_id"], account["fence"],
             account["integrator_participant"], account["attempt_id"]):
        _refuse(f"the block on target {name_value(canonical_target_id)} and "
                f"lease {name_value(account['lease_id'])} disagree about the "
                f"grant the block is about")
    # LIVE OR PROPERLY RECOVERED, and nothing else: a released lease under a
    # blocked target would mean the holder ended cleanly over an entry nobody
    # could reconcile.
    if lease["state"] not in ("live", "abandoned"):
        _refuse(f"target {name_value(canonical_target_id)} is blocked under a "
                f"{name_value(lease['state'])} lease")
    if lease["state"] == "abandoned" and \
            lease["ending"]["recovery"]["attempt_id"] != account["attempt_id"]:
        _refuse(f"lease {name_value(account['lease_id'])} was recovered for "
                f"attempt "
                f"{name_value(lease['ending']['recovery']['attempt_id'])} and "
                f"the block accounts for {name_value(account['attempt_id'])}")
    return account


def activate_target(store, document):
    """Adopt one canonical target from TRUSTED TARGET CONFIGURATION.

    THE KEY IS THE DOCUMENT'S AND IS NEVER DERIVED. Not from the development
    line, not from the Authority, not from the Work, the proposal, the
    checkpoint or the mutable target revision. Every one of those is scoped
    more narrowly than a target, and a key derived from any of them gives one
    target two locks -- which is the exact defect the owner ruling
    exists to prevent, arriving by a different road.

    Repeating the same document is one act. THE OPERATION IDENTITY CARRIES
    THE DOCUMENT'S DIGEST as well as the target's key, which was measured
    rather than assumed: with the key alone, a changed configuration is a
    signature mismatch on one operation id and comes back as the generic
    `operation-collision`, leaving the check below unreachable and the caller
    told nothing about targets. Two configurations are two operations, so an
    exact retry replays and a changed one is refused BY THIS FUNCTION, saying
    what it refused.
    """
    taken = _owned_target(document, "an integration target")
    canonical_target_id = taken["canonical_target_id"]
    target_digest = digest(taken)
    # THE PAIR IS DIGESTED RATHER THAN CONCATENATED. Two ids joined by ":"
    # do not compose uniquely when an id may itself contain one.
    operation_id = _activation_operation(taken)
    signature = integration_signature("target.activate", {"target": taken})

    def perform(connection):
        held = connection.execute(
            "SELECT digest FROM targets WHERE canonical_target_id = ?",
            (canonical_target_id,)).fetchone()
        if held is not None:
            # Reached by a SECOND configuration for one key; an exact retry
            # replayed before this ran. A live target is not re-described in
            # passing, and `held["digest"]` is compared rather than the
            # document because the digest is what the row is trusted for.
            if held["digest"] != target_digest:
                _denied(f"target {name_value(canonical_target_id)} is already "
                        f"activated under another configuration; a live "
                        f"target's identity is not re-described")
            return target_of(store, canonical_target_id)
        connection.execute(
            "INSERT INTO targets (canonical_target_id, document, digest, "
            "state, fence, activated_at) VALUES (?, ?, ?, 'open', 0, ?)",
            (canonical_target_id, json.dumps(taken, sort_keys=True),
             target_digest, store._now()))
        return target_of(store, canonical_target_id)

    return _transact(store, operation_id, "target.activate", signature, perform)


def enqueue(store, *, canonical_target_id, entry_id, eligibility):
    """Place one immutable entry in a target's queue and allocate its rank.

    THE ELIGIBILITY ACCOUNT ARRIVES ALREADY PROVED. This module stores it and
    never re-derives it: mixing "is this candidate eligible" with "whose turn
    is it" is how a queue ends up re-deciding policy under a lock. What is
    checked here is that the account is a closed document carrying every
    operand an entry must retain.

    RANK IS ALLOCATED IN THIS TRANSACTION, so two concurrent enqueues cannot
    receive one rank and selection never breaks a tie by row order or wall
    clock. An exact replay returns the same entry and the same rank.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    account = _owned_account(eligibility, "an eligibility account")
    operation_id = "entry.enqueue:" + entry_id
    signature = integration_signature(
        "entry.enqueue", {"canonical_target_id": canonical_target_id,
                          "entry_id": entry_id, "eligibility": account})

    def perform(connection):
        target = target_of(store, canonical_target_id)
        if target is None:
            _denied(f"target {name_value(canonical_target_id)} is not "
                    f"activated; an entry belongs to a configured target")
        # ONE CANDIDATE, ONE PLACE, AND THE INDEX IS NOT LEFT TO SAY SO.
        # `UNIQUE (canonical_target_id, authority_uuid, checkpoint_id)` would
        # answer a second entry id for one candidate with a raw
        # `sqlite3.IntegrityError` escaping this boundary as something no
        # caller can act on. The caller is told which entry the candidate
        # already holds instead, because that entry -- not the id this call
        # invented -- is the one the queue will offer.
        held = connection.execute(
            "SELECT entry_id, rank FROM entries WHERE canonical_target_id = ? "
            "AND authority_uuid = ? AND checkpoint_id = ?",
            (canonical_target_id, account["authority_uuid"],
             account["checkpoint_id"])).fetchone()
        if held is not None:
            _denied(
                f"checkpoint {name_value(account['checkpoint_id'])} of "
                f"authority {name_value(account['authority_uuid'])} already "
                f"holds rank {boundaries.generation(held['rank'], 'a rank')} "
                f"on this target as entry "
                f"{name_value(boundaries.identity(held['entry_id'], 'an entry id'))}; "
                f"a second entry id for one candidate is not a second place "
                f"in the queue")
        rank = boundaries.generation(connection.execute(
            "SELECT COALESCE(MAX(rank), 0) + 1 FROM entries "
            "WHERE canonical_target_id = ?", (canonical_target_id,)
        ).fetchone()[0], "an allocated rank")
        connection.execute(
            "INSERT INTO entries (entry_id, canonical_target_id, rank, "
            "authority_uuid, work_id, assignment_generation, line_id, "
            "checkpoint_id, verdict_id, checkpoint_digest, proposal_id, "
            "candidate_digest, proposal_manifest_digest, profile_kind, "
            "profile_version, profile_account_digest, "
            "expected_target_revision, path_set_digest, scope_digest, "
            "state, enqueued_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
            (entry_id, canonical_target_id, rank, account["authority_uuid"],
             account["work_id"], account["assignment_generation"],
             account["line_id"], account["checkpoint_id"],
             account["verdict_id"], account["checkpoint_digest"],
             account["proposal_id"], account["candidate_digest"],
             account["proposal_manifest_digest"], account["profile_kind"],
             account["profile_version"], account["profile_account_digest"],
             account["expected_target_revision"],
             account["path_set_digest"], account["scope_digest"],
             store._now()))
        return _entry(store, entry_id)

    return _transact(store, operation_id, "entry.enqueue", signature, perform)


def grant_lease(store, *, canonical_target_id, lease_id,
                integrator_participant, attempt_id):
    """Grant the one live lease for a target, over its smallest queued rank.

    THE STORE DECIDES THE RACE. `leases_one_live_per_target` is a partial
    unique index, so two grants contending for one target meet inside their
    write transactions and the loser refuses -- rather than both reading "no
    live lease" and both writing one.

    THE FENCE INCREASES IN THE SAME TRANSACTION, so a fence value names at
    most one grant that ever existed. It is evidence and not a capability:
    `live_grant` below is what a holder must pass before it mutates anything.

    A BLOCKED TARGET GRANTS NOTHING. A target whose last account this build
    could not reconcile is one nothing may be imported into until somebody
    says so, and offering the next entry would be exactly the hidden
    correction this record forbids.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.text(integrator_participant, "an integrator participant")
    boundaries.identity(attempt_id, "an integrator attempt id")
    operation_id = "lease.grant:" + lease_id
    signature = integration_signature(
        "lease.grant", {"canonical_target_id": canonical_target_id,
                        "lease_id": lease_id,
                        "integrator_participant": integrator_participant,
                        "attempt_id": attempt_id})

    def perform(connection):
        target = target_of(store, canonical_target_id)
        if target is None:
            _denied(f"target {name_value(canonical_target_id)} is not "
                    f"activated")
        if target["state"] != "open":
            _denied(f"target {name_value(canonical_target_id)} is blocked: "
                    f"{target['blocked_reason']}. A blocked target offers no "
                    f"entry until it is explicitly repaired")
        live = connection.execute(
            "SELECT lease_id FROM leases WHERE canonical_target_id = ? "
            "AND state = 'live'", (canonical_target_id,)).fetchone()
        if live is not None:
            _denied(f"target {name_value(canonical_target_id)} is already "
                    f"leased by "
                    f"{name_value(boundaries.identity(live['lease_id'], 'a lease id'))}"
                    f"; one target integrates one entry at a time")
        queued = connection.execute(
            "SELECT entry_id FROM entries WHERE canonical_target_id = ? "
            "AND state = 'queued' ORDER BY rank LIMIT 1",
            (canonical_target_id,)).fetchone()
        if queued is None:
            return None
        # Adopted, and about to be written into `leases`: the store is a
        # receiving domain on the way out as much as on the way in.
        entry_id = boundaries.identity(queued["entry_id"], "an entry id")
        fence = target["fence"] + 1
        connection.execute(
            "UPDATE targets SET fence = ? WHERE canonical_target_id = ?",
            (fence, canonical_target_id))
        connection.execute(
            "INSERT INTO leases (lease_id, canonical_target_id, entry_id, "
            "integrator_participant, attempt_id, fence, state, granted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'live', ?)",
            (lease_id, canonical_target_id, entry_id,
             integrator_participant, attempt_id, fence, store._now()))
        connection.execute(
            "UPDATE entries SET state = 'leased' WHERE entry_id = ?",
            (entry_id,))
        return {"lease": lease_of(store, lease_id),
                "entry": _entry(store, entry_id)}

    return _transact(store, operation_id, "lease.grant", signature, perform)


def live_grant(store, *, lease_id, canonical_target_id, entry_id, fence):
    """Prove this holder still holds THIS target, entry, lease and fence.

    A SERIALIZED LEASE AND FENCE ARE EVIDENCE, NOT POSSESSION, and the seam
    review of 2026-09-05 is why this function exists. An earlier draft made
    the lease id and fence operands of the integration profile's calls and
    called that sufficient; operands are values and values can be replayed.
    W71918 had already corrected the same mistake for its writer grant, whose
    previously minted boundaries recheck the LIVE grant at adoption and again
    at mount composition.

    So this is read from the store immediately before canonical mutation and
    AGAIN before Authority completion. Four things must agree at once, because
    any one of them alone can be stale while the others look right: the lease
    must still be live, it must still be this target's, it must still be
    against this entry, and its fence must be exactly the one the caller
    believes it holds.
    """
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.generation(fence, "a lease fence")
    held = lease_of(store, lease_id)
    if held is None:
        _denied(f"lease {name_value(lease_id)} does not exist; a live grant "
                f"is read from the store rather than presented by its holder")
    target = target_of(store, canonical_target_id)
    if held["state"] != "live" or held["canonical_target_id"] != canonical_target_id \
            or held["entry_id"] != entry_id or held["fence"] != fence:
        _denied(f"lease {name_value(lease_id)} is {held['state']} over target "
                f"{name_value(held['canonical_target_id'])} entry "
                f"{name_value(held['entry_id'])} at fence {held['fence']}, and "
                f"this caller presents target {name_value(canonical_target_id)} "
                f"entry {name_value(entry_id)} at fence {fence}; a grant is "
                f"proved live at the moment it is used")
    if target is None or target["state"] != "open" or target["fence"] != fence:
        _denied(f"target {name_value(canonical_target_id)} is not open at "
                f"fence {fence}; the grant this caller holds has been "
                f"superseded or the target is blocked")
    return held


def _recorded(store, operation_id, kind, signature):
    """`(found, value)` for an act that must REPLAY before it proves a grant.

    THE ORDER IS THE POINT, and it was measured wrong first. The fenced verbs
    below prove a live grant before they open their transaction, which is
    correct for a first attempt and fatal for a repeat: releasing a lease ends
    it, so the retry that a caller makes after a lost answer would find its own
    completed work and refuse it as "the grant is no longer live". The same
    shape was corrected in W71917's recovery seam for the same reason.

    So the journal is asked first. An exact repeat of a recorded act returns
    that act's outcome, and only a request the journal has never seen goes on
    to prove that its grant is still held.

    ASKED FIRST IS NOT TRUSTED FIRST, and the seventh review of 2026-09-06 is
    why that sentence is here. The order above is preserved exactly -- the
    journal still answers before a now-ended grant is checked -- but what it
    answers WITH is an act proved through `_proved` rather than a decoded row.
    "Replay first" was never an argument for believing the journal; it is an
    argument about which question is asked first.
    """
    return store.replay(operation_id, signature, kind=kind, witness=_proved)


def _end_lease(store, lease_id, state, ending):
    def perform(connection):
        held = lease_of(store, lease_id)
        if held is None:
            _refuse(f"no integration lease {name_value(lease_id)}")
        if held["state"] != "live":
            _denied(f"lease {name_value(lease_id)} is already {held['state']}")
        connection.execute(
            "UPDATE leases SET state = ?, ended_at = ?, ending = ? "
            "WHERE lease_id = ?",
            (state, store._now(), json.dumps(ending, sort_keys=True),
             lease_id))
        return lease_of(store, lease_id)
    return perform


def release_lease(store, *, lease_id, canonical_target_id, entry_id, fence,
                  ending):
    """End a lease whose ENTRY has already reached a terminal account.

    THE ENTRY'S STATE IS THE PRECONDITION, and the review of 2026-09-06 [P0]
    is why it is stated here rather than assumed. This function used to check
    only that the lease was live: so a holder could release a grant while its
    entry was still `leased`, the next queued entry would be offered
    immediately, and the target would be handed to a second importer while the
    first entry still recorded unresolved canonical work. The serialization
    this whole store exists for was one call away from being undone -- and my
    own suite drove that transition and asserted only that the old grant had
    stopped being live, which BLESSED the hole instead of finding it.

    So the only lease this ends is one whose entry is `integrated`. The other
    two endings are FUSED to the transition that makes them true:
    `refuse_entry` ends the lease in the same transaction that refuses the
    entry, and an unreconcilable account KEEPS its lease through
    `block_target` and ends it only through the explicit recovery. There is no
    public transition that leaves a `queued`, `leased` or `held` entry behind
    an ended lease.

    THE CALLER STATES ALL FOUR OPERANDS. A release that read the target and
    entry off the lease would prove the lease agrees with itself; a caller
    that names the wrong entry should be refused rather than accommodated.
    """
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    account = _ending(ending, "released", "a lease ending")
    operation_id = "lease.release:" + lease_id
    signature = integration_signature(
        "lease.release", {"lease_id": lease_id,
                          "canonical_target_id": canonical_target_id,
                          "entry_id": entry_id, "fence": fence,
                          "ending": account})
    found, value = _recorded(store, operation_id, "lease.release", signature)
    if found:
        return value
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id,
               entry_id=entry_id, fence=fence)
    settled = _entry(store, entry_id)
    if settled["state"] != "integrated":
        _denied(f"entry {name_value(entry_id)} is {settled['state']} and an "
                f"ordinary release ends a lease whose entry is integrated; a "
                f"lease ended over unresolved work would offer this target's "
                f"next entry while the last one is still unaccounted for")
    if account["outcome"] != "integrated":
        _denied(f"entry {name_value(entry_id)} is integrated and this ending "
                f"accounts for {name_value(account['outcome'])}; the ending "
                f"recorded is the one that actually happened")

    def perform(connection):
        # RE-READ UNDER THE WRITE LOCK, for the reason every other verb here
        # re-reads: the state above was proved before this transaction began.
        current = _entry(store, entry_id)
        if current["state"] != "integrated":
            _denied(f"entry {name_value(entry_id)} became "
                    f"{name_value(current['state'])} before this release")
        return _end_lease(store, lease_id, "released", account)(connection)

    return _transact(store, operation_id, "lease.release", signature, perform)


def settle_integrated(store, *, lease_id, canonical_target_id, fence,
                      entry_id, settlement):
    """Record that this entry's reviewed bytes are on the target.

    CALLED ONLY AFTER REAL IMPORT AND VERIFICATION, and the live grant is
    re-proved here because this is the second of the two cutpoints the ruling
    names: one before canonical mutation, one before Authority completion.

    The target is the CALLER'S operand rather than something read off the
    lease, so a caller settling against a target it does not believe it holds
    is refused instead of being told what it holds.
    """
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    # THE OWNED SNAPSHOT IS WHAT EVERYTHING BELOW USES. Re-review of
    # 2026-09-06 [P1]: this called `boundaries.document` and threw the fresh
    # copy away, then signed and persisted the caller's own dictionary. The
    # re-review mutated it from the injected clock between the signature and
    # the SQL arguments: one call validated and journalled `['reviewed.py']`,
    # stored and returned `['other.py']`, and the exact retry of the reviewed
    # value replayed the other one. `own` snapshots every member exactly once
    # precisely so "the value we validated is the value we used" is a fact --
    # and discarding its answer gives that fact away.
    account = _settlement(settlement, "integrated",
                          "an integration settlement")
    # THE OPERATION IDENTITY IS THE ENTRY'S AND THE SIGNATURE CARRIES THE
    # LEASE. So a retry of this exact settlement replays, while the same entry
    # settled under a LATER grant is an operation collision rather than a
    # silent replay of the earlier import's account.
    operation_id = "entry.integrated:" + entry_id
    signature = integration_signature(
        "entry.integrated", {"entry_id": entry_id, "lease_id": lease_id,
                             "canonical_target_id": canonical_target_id,
                             "fence": fence, "settlement": account})
    found, value = _recorded(store, operation_id, "entry.integrated",
                             signature)
    if found:
        return value
    live_grant(store, lease_id=lease_id,
               canonical_target_id=canonical_target_id,
               entry_id=entry_id, fence=fence)

    def perform(connection):
        entry = _entry(store, entry_id)
        if entry["state"] != "leased":
            _denied(f"entry {name_value(entry_id)} is {entry['state']}; only "
                    f"a leased entry is integrated")
        connection.execute(
            "UPDATE entries SET state = 'integrated', settled_at = ?, "
            "settlement = ? WHERE entry_id = ?",
            (store._now(), json.dumps(account, sort_keys=True), entry_id))
        return _entry(store, entry_id)

    return _transact(store, operation_id, "entry.integrated", signature, perform)


def refuse_entry(store, *, canonical_target_id, entry_id, settlement,
                 lease_id=None, fence=None):
    """Terminally refuse ONE entry, leaving the target open.

    THIS IS THE ORDINARY REFUSAL, and the targeted review of 2026-09-05 fixed
    which failures reach it: a current-policy, scope or target failure found
    BEFORE any mutation. The candidate is not integrable and the queue moves
    on; the target is untouched and its next entry may be offered.

    A LEASED ENTRY IS REFUSED BY ITS HOLDER AND BY NOBODY ELSE. This verb ENDS
    a live lease and hands the target to whoever asks next, so it is the one
    place a caller can hand the target away from a holder that is still
    mutating it -- and a lease id with a fence is a replayable value, so the
    grant is proved LIVE here exactly as it is before canonical mutation. A
    queued entry has no holder to be, and needs no grant.

    THE ASYMMETRY WITH `block_target` IS DELIBERATE AND IS NOT AN OVERSIGHT.
    Blocking only ever REMOVES permission, so it stays available to a caller
    holding nothing -- which is what keeps a crashed holder's target
    recoverable at all. This verb GRANTS permission for the next entry, so it
    demands the grant.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    # The owned snapshot, for the reason `settle_integrated` records: the
    # value validated is the value signed, stored and returned.
    account = _settlement(settlement, "refused", "an entry refusal")
    standing = _entry(store, entry_id)
    if standing["canonical_target_id"] != canonical_target_id:
        _denied(f"entry {name_value(entry_id)} belongs to "
                f"{name_value(standing['canonical_target_id'])} and this "
                f"caller presents {name_value(canonical_target_id)}")
    operation_id = "entry.refuse:" + entry_id
    signature = integration_signature(
        "entry.refuse", {"canonical_target_id": canonical_target_id,
                         "entry_id": entry_id, "settlement": account,
                         "lease_id": lease_id, "fence": fence})
    found, value = _recorded(store, operation_id, "entry.refuse", signature)
    if found:
        return value
    if standing["state"] == "leased":
        if lease_id is None:
            _denied(f"entry {name_value(entry_id)} is leased; the refusal that "
                    f"ends its lease and offers the target to the next caller "
                    f"is proved by a live grant rather than asserted")
        live_grant(store, lease_id=lease_id,
                   canonical_target_id=canonical_target_id,
                   entry_id=entry_id, fence=fence)

    def perform(connection):
        entry = _entry(store, entry_id)
        if entry["state"] in ("integrated", "refused", "held"):
            _denied(f"entry {name_value(entry_id)} is already "
                    f"{entry['state']}")
        # RE-READ UNDER THE WRITE LOCK. The grant above was proved before this
        # transaction began, so a queued entry that has since been leased --
        # or leased by somebody else -- is caught here rather than having its
        # holder's lease ended by a caller who never held one.
        standing = connection.execute(
            "SELECT lease_id FROM leases WHERE entry_id = ? AND state = 'live'",
            (entry_id,)).fetchone()
        if standing is not None and boundaries.identity(
                standing["lease_id"], "a lease id") != lease_id:
            _denied(f"entry {name_value(entry_id)} is held live by "
                    f"{name_value(standing['lease_id'])} and this caller "
                    f"presents {name_value(lease_id)}")
        connection.execute(
            "UPDATE entries SET state = 'refused', settled_at = ?, "
            "settlement = ? WHERE entry_id = ?",
            (store._now(), json.dumps(account, sort_keys=True), entry_id))
        live = connection.execute(
            "SELECT lease_id FROM leases WHERE entry_id = ? AND state = 'live'",
            (entry_id,)).fetchone()
        if live is not None:
            connection.execute(
                "UPDATE leases SET state = 'released', ended_at = ?, "
                "ending = ? WHERE lease_id = ?",
                (store._now(),
                 json.dumps(_ending({"outcome": "entry-refused"}, "released",
                                    "a fused lease ending"), sort_keys=True),
                 live["lease_id"]))
        return _entry(store, entry_id)

    return _transact(store, operation_id, "entry.refuse", signature, perform)


def block_target(store, *, canonical_target_id, entry_id, lease_id, fence,
                 reason, detail):
    """Hold the LEASED entry and KEEP its lease, for an unreconcilable account.

    THE OTHER REFUSAL, and it is not a louder version of the first. An
    integrity, digest or ambiguous-custody failure is a statement about the
    TARGET rather than about this candidate: the working tree may hold base
    bytes, candidate bytes or a mixture, and offering the next entry into that
    would be the hidden correction this record forbids.

    So the entry is `held` rather than `refused`, the live lease is left LIVE,
    and the target is `blocked` carrying the account of the grant that was live
    when it blocked.

    IT IS THE LIVE LEASE'S ENTRY OR IT IS NOTHING. Review of 2026-09-06 [P0]:
    this accepted any queued or leased entry of the target and recorded no
    association with the live grant at all, so a block naming entry B while
    entry A held the lease left A `leased`, B `held`, and a recovery that then
    ended A's grant against B's block. Every operand of the live grant is now
    named by the caller and cross-checked, and the whole account is persisted
    for the recovery to check against rather than re-derive.

    A BLOCK IS NOT A GRANT, THOUGH, and demanding one would be the same defect
    from the other side: a crashed holder cannot present its own grant, so a
    target whose holder is gone could never be blocked and never be recovered.
    The caller must NAME the live grant exactly; it need not hold it. That is
    what keeps blocking available to a third party while making it impossible
    to block about the wrong entry.

    A TARGET WITH NO LIVE LEASE IS NOT BLOCKED HERE. Nothing has touched it, so
    there is no unreconcilable account -- an unusable candidate is
    `refuse_entry`'s. Item 3 defines no other blocking transition, and this
    refuses rather than inventing one.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.generation(fence, "a lease fence")
    # OWNED AS ONE ACCOUNT AND USED AS THE OWNED ONE, by the same rule the two
    # verbs above record: the shape a `held` settlement must have is
    # `_settlement`'s to state, and the snapshot it returns is what is signed
    # and persisted.
    stated = _settlement({"reason": reason, "detail": detail}, "held",
                         "a target block account")
    operation_id = _block_operation(canonical_target_id, entry_id)
    signature = integration_signature(
        "target.block", {"canonical_target_id": canonical_target_id,
                         "entry_id": entry_id, "lease_id": lease_id,
                         "fence": fence, "account": stated})

    def perform(connection):
        target = target_of(store, canonical_target_id)
        if target is None:
            _denied(f"target {name_value(canonical_target_id)} is not "
                    f"activated")
        if target["state"] != "open":
            _denied(f"target {name_value(canonical_target_id)} is already "
                    f"blocked over entry "
                    f"{name_value(target['blocked_account']['entry_id'])}; a "
                    f"second block would replace the account the recovery "
                    f"checks against")
        entry = _entry(store, entry_id)
        if entry["canonical_target_id"] != canonical_target_id:
            _denied(f"entry {name_value(entry_id)} is not this target's")
        # THE ENTRY'S OWN STATE FIRST, so an already-settled entry is told
        # that rather than being told about a lease it could never have.
        if entry["state"] != "queued" and entry["state"] != "leased":
            _denied(f"entry {name_value(entry_id)} is already "
                    f"{entry['state']}")
        held = lease_of(store, lease_id)
        if held is None or held["state"] != "live" \
                or held["canonical_target_id"] != canonical_target_id \
                or held["entry_id"] != entry_id or held["fence"] != fence:
            _denied(f"target {name_value(canonical_target_id)} has no live "
                    f"lease {name_value(lease_id)} over entry "
                    f"{name_value(entry_id)} at fence {fence}; a block is "
                    f"about the grant that was live, and naming another of "
                    f"this target's entries would block one and abandon "
                    f"another")
        account = dict(stated, entry_id=entry_id, lease_id=lease_id,
                       fence=fence,
                       integrator_participant=held["integrator_participant"],
                       attempt_id=held["attempt_id"])
        connection.execute(
            "UPDATE entries SET state = 'held', settled_at = ?, "
            "settlement = ? WHERE entry_id = ?",
            (store._now(), json.dumps(stated, sort_keys=True), entry_id))
        connection.execute(
            "UPDATE targets SET state = 'blocked', blocked_reason = ?, "
            "blocked_account = ? WHERE canonical_target_id = ?",
            (reason, json.dumps(account, sort_keys=True),
             canonical_target_id))
        return {"target": target_of(store, canonical_target_id),
                "entry": _entry(store, entry_id)}

    return _transact(store, operation_id, "target.block", signature, perform)


def abandon_lease(store, *, lease_id, fence, recovery):
    """End a live lease this caller does not hold, on a BLOCKED target.

    THE ONE WAY A LEASE ENDS WITHOUT ITS HOLDER, and it is deliberately narrow.
    `leases` carries no timeout column: a holder's silence is not evidence that
    it has stopped, and a lease that expired on its own would hand a working
    tree to a second importer while the first is still writing into it.

    SO THE TARGET MUST ALREADY BE BLOCKED. That ordering is the whole safety
    argument. Blocking says "nothing may be imported here until somebody says
    so", and it is reachable without a grant precisely so a crashed holder's
    target is recoverable; only once the target is closed to new work is it
    safe to end the grant that used to protect it. Abandoning does NOT reopen
    the target -- repair stays explicit, and this build decides none of it.

    WHAT THE RECOVERY DOCUMENT IS AND IS NOT. This module cannot prove that a
    prior holder can no longer mutate: the evidence for that lives in the
    Worker Manager's attempt record and the integration profile, both outside
    this seam. So the account is validated as a closed document, its
    `attempt_id` must be the one the lease was granted to -- a caller
    recovering the wrong attempt is refused -- and it is RETAINED as the
    lease's ending rather than interpreted here.
    """
    boundaries.identity(lease_id, "a lease id")
    boundaries.generation(fence, "a lease fence")
    account = _recovery(recovery, "a lease recovery account")
    operation_id = "lease.abandon:" + lease_id
    signature = integration_signature(
        "lease.abandon", {"lease_id": lease_id, "fence": fence,
                          "recovery": account})
    found, value = _recorded(store, operation_id, "lease.abandon", signature)
    if found:
        return value
    held = lease_of(store, lease_id)
    if held is None:
        _refuse(f"no integration lease {name_value(lease_id)}")
    if held["state"] != "live":
        _denied(f"lease {name_value(lease_id)} is already {held['state']}")
    if held["fence"] != fence:
        _denied(f"lease {name_value(lease_id)} is at fence {held['fence']} and "
                f"this recovery names {fence}; a recovery ends the grant it "
                f"observed rather than whichever one is current")
    if account["attempt_id"] != held["attempt_id"]:
        _denied(f"lease {name_value(lease_id)} was granted to attempt "
                f"{name_value(held['attempt_id'])} and this recovery accounts "
                f"for {name_value(account['attempt_id'])}")
    target = target_of(store, held["canonical_target_id"])
    if target is None or target["state"] != "blocked":
        _denied(f"target {name_value(held['canonical_target_id'])} is not "
                f"blocked, so its live lease is not somebody else's to end; "
                f"block the target first and the target stays blocked after")
    # THE BLOCK'S OWN ACCOUNT, CHECKED RATHER THAN RE-DERIVED. A recovery that
    # only proved "some target is blocked and this lease is live at this
    # fence" is what let a block about one entry end a grant over another.
    blocked = target["blocked_account"]
    if (blocked["lease_id"], blocked["fence"], blocked["entry_id"]) != \
            (lease_id, fence, held["entry_id"]):
        _denied(f"target {name_value(held['canonical_target_id'])} is blocked "
                f"over entry {name_value(blocked['entry_id'])} under lease "
                f"{name_value(blocked['lease_id'])} at fence "
                f"{blocked['fence']}, and this recovery ends "
                f"{name_value(lease_id)} over "
                f"{name_value(held['entry_id'])} at fence {fence}; a recovery "
                f"ends the grant the block was about")
    ending = _ending({"outcome": "abandoned", "recovery": account},
                     "abandoned", "a lease ending")
    return _transact(store, operation_id, "lease.abandon", signature,
                          _end_lease(store, lease_id, "abandoned", ending))
