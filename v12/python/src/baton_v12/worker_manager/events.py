"""What this manager PUBLISHES about the offers it owns, regenerably.

W73629. THE PROBLEM THIS EXISTS FOR. `recover_on_restart` correctly abandons an
`issued` offer a previous incarnation minted, because nothing durable proves
its bearer was ever delivered. Nothing told the consumer. A Job manager holding
that stage's `admit` receipt went on projecting `offered` and owing `claim`
against a terminal offer forever, so one restart wedged the stage permanently.

WHAT IS PUBLISHED IS A LEVEL, NOT AN EDGE. An `offer.state` event says what an
offer's canonical state IS at the instant the row was read -- not that it just
changed. That is the whole design: the event is a pure function of a row this
manager already owns, so it can be regenerated at startup, at consumer
attachment, or periodically, and a lost delivery costs nothing but latency. A
transition NOTICE would be the opposite: miss it once and the consumer is
wedged with no way to ask again short of reading this manager's tables, which
is the boundary this file exists to avoid crossing.

THE REVISION IS DERIVED, WHICH IS WHY IT NEEDS NO COLUMN. An offer's lifecycle
is already monotone -- `issued` precedes `accepted`, and every terminal state
follows both -- so the RANK of the state is a monotonic revision that recomputes
from the row every time. A stored counter would be a second account of the same
fact, and the first restart where the two disagreed would need somebody to
decide which one the consumer should believe.

NOTHING HERE PUBLISHES FROM INSIDE A WRITE. Every function below only READS
canonical rows and appends to a transient transport. The caller invokes them
after its operation has returned and its transactions have committed, which is
what keeps a consumer's handler from running inside this manager's transaction.
`offers.py` is deliberately untouched by this Work: it still owns settlement,
and it does not acquire a second job of announcing it. Reading through its
`_offers` is that decision's other half -- it is that module's ONE declared
crossing out of the offers table, and every row it answers is already owned, so
publishing goes through the same boundary every other offer question does
rather than opening a second reader beside it.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries, schema
from .offers import _offers

__all__ = ["OFFER_STATE", "OFFER_STATE_KIND", "OFFER_STATE_MEMBERS",
           "STATE_REVISIONS", "TERMINAL_OFFER_STATES", "offer_state",
           "offer_state_revision", "publish_offer_states"]

OFFER_STATE_KIND = "offer.state"

OFFER_STATE_MEMBERS = ("kind", "offer_id", "attempt_id", "state", "revision")

# The monotone rank of each canonical offer state. Three levels, because three
# is what the lifecycle actually has: not yet decided, authorized, and over.
#
# EVERY TERMINAL STATE SHARES ONE RANK ON PURPOSE. The rank exists to answer
# "is this assertion older than the one I applied", and an offer reaches at
# most one ending, so ranking the endings against each other would be ordering
# events that cannot both exist. WHICH ending it was travels in the same
# document, where a consumer that cares reads it as a state rather than as a
# number.
STATE_REVISIONS = {"issued": 1, "accepted": 2, "declined": 3, "expired": 3,
                   "abandoned-after-restart": 3, "claimed": 3,
                   "claim-refused": 3, "settlement-expired": 3}

TERMINAL_OFFER_STATES = tuple(
    sorted(state for state, rank in STATE_REVISIONS.items() if rank == 3))

# The contract is checked here rather than trusted, because a state this build
# has no rank for would otherwise be published with no revision at all.
assert tuple(sorted(STATE_REVISIONS)) == tuple(sorted(schema.OFFER_STATES))

OFFER_STATE = (OFFER_STATE_MEMBERS, ())


def offer_state_revision(state):
    """The monotonic rank of one canonical offer state."""
    boundaries.text(state, "a canonical offer state")
    if state not in STATE_REVISIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build ranks {', '.join(sorted(STATE_REVISIONS))}; the "
            f"offers table answered {name_value(state)}, and publishing a "
            f"state with no revision would give a consumer no way to tell it "
            f"from a stale one")
    return STATE_REVISIONS[state]


def offer_state(offer):
    """One canonical offer row, as the assertion a consumer reads.

    The attempt id travels beside the offer id because the consumer's own
    identities are BOTH of them: a stage names an offer it asked for and an
    attempt that offer froze, and an assertion carrying only one would make
    the consumer derive the other -- which is the derivation that let a foreign
    attempt be read as this stage's in the first place.

    THE ROW IS ALREADY OWNED AND IS NOT OWNED AGAIN. `_offers` proves every
    column against `OFFER_COLUMNS` on the way out of the table, so re-proving
    `offer_id`, `runtime_attempt_id` and `state` here would be the blanket
    revalidation of a trusted internal value that PLAN 4bz rules against --
    and it would put three boundary entries in this package's inventory that
    assert what another entry has already asserted. `offer_state_revision`
    stays, because it is a public function a consumer calls with a state it
    received rather than one this manager read.
    """
    state = offer["state"]
    return {"kind": OFFER_STATE_KIND, "offer_id": offer["offer_id"],
            "attempt_id": offer["runtime_attempt_id"], "state": state,
            "revision": offer_state_revision(state)}


def publish_offer_states(store, queue, offer_ids):
    """Assert the CURRENT state of each named offer this manager holds.

    THE CONSUMER NAMES WHAT IS RELEVANT and this manager answers about its own
    rows. That is what "the Worker Manager enumerates the relevant canonical
    offer rows" means in one process: the consumer does not read this store,
    and this store does not have to guess which of possibly several consumers'
    offers to broadcast.

    AN OFFER THIS MANAGER DOES NOT HOLD IS SILENCE, not a refusal. A consumer
    may name an offer whose act never reached issuance -- that is the ordinary
    state of a stage this manager has not been asked about yet, and answering
    it with an error would make regeneration fail exactly when a consumer most
    needs to resynchronize.

    Answers the ids it published, so a caller can record what a regeneration
    actually asserted rather than what it asked for.
    """
    boundaries.capability(getattr(queue, "publish", None),
                          "the transport's publish")
    wanted = [boundaries.identity(one, "an offer id") for one in offer_ids]
    if not wanted:
        return []
    published = []
    # One crossing out of the offers table, and one read for the whole set --
    # a row per call would be a different instant per offer, and a consumer
    # comparing two of them would be comparing this manager with itself at two
    # times.
    held = {offer["offer_id"]: offer for offer in _offers(
        store, "WHERE offer_id IN (" + ", ".join("?" * len(wanted)) + ")",
        tuple(wanted))}
    for offer_id in wanted:
        offer = held.get(offer_id)
        if offer is None:
            continue
        queue.publish(offer_state(offer))
        published.append(offer_id)
    return published
