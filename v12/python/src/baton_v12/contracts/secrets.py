"""§13: the one deliberate secret stays off every durable surface.

W6630. `work/records/2026/08/finding-v12-manager-section-13-security/`. Ported
from the frozen Node `contracts.mjs` by obligation, and its five design
decisions are carried forward rather than re-derived.

THE ANCHOR IS A CODE, NOT A SHAPE. §13 has no `$defs` in the frozen schema: it
is prose in the spec and BEHAVIOUR in the implementation, anchored by
`integrity.secret-leak`, which this package's closed pairing already carries.
What was missing was the rule that raises it.

IT IS A WALK, NOT A TOP-LEVEL CHECK, because the boundary is about what a
durable document CONTAINS, at any depth. A bearer nested inside a copied
decision body is exactly as durable as one at the root.

BOTH HALVES ARE NEEDED AND NEITHER IMPLIES THE OTHER. A member NAMED for a
secret is refused whatever it holds, because the name says the value is one;
and a known secret VALUE is refused wherever it appears, because a leak does
not depend on what the leaking member was called. A name-only check reads as a
leak boundary while being a naming convention.

THE VALUE TEST IS CONTAINMENT, NOT EQUALITY. An interpolated refusal message
carries the bearer just as durably as a bare member does — which is where §13
meets bounded diagnostics: a refusal that quotes an operand is a durable
surface like a label, a log line, a store row or an artifact.

SHAPE CANNOT SUBSTITUTE FOR THE REGISTRY. The contract admits any bearer from
32 to 4096 characters, so a rule that refused token-shaped strings would refuse
ordinary durable operands and still miss a short one. The only safe test is
against the actual live values.

WHY THE REGISTRY IS HERE AND NOT IN THE MANAGER. The manifest composite beside
this module has to consult it, and this package may not import from the one
above it. It is deliberately small: a reference count keyed by value, holding
nothing that is not currently live, and every entry is forgotten by the act
that acquired it however that act ends.
"""

import threading

from .errors import ContractRefusal, label_of, name_value

__all__ = ["SECRET_MEMBERS", "check_no_durable_secret", "forget_secret",
           "held_secret", "live_secret", "remember_secret"]

# The member names §13 names, matched CASE-INSENSITIVELY. A member called
# `Authorization` is the same member.
SECRET_MEMBERS = ("claim_token", "password", "authorization", "access_token",
                  "refresh_token", "private_key")

_FORBIDDEN = frozenset(SECRET_MEMBERS)

# A REFERENCE COUNT, NOT A PRESENCE SET, and the distinction is load-bearing.
# An outer owner holding a bearer and an inner scope using the same value are
# two registrations of ONE value; presence cannot express shared ownership, so
# the inner scope's release would delete the outer owner's still-live entry.
#
# GUARDED, because a manager may serve several threads and a count that two of
# them increment is a count that loses one. The lock is held only around the
# arithmetic — never around a walk, which would make every durable write
# contend on one mutex.
_live = {}
_lock = threading.Lock()


def remember_secret(value):
    """Register an ephemeral secret for as long as it is live.

    REGISTRATIONS NEST. Each one must be matched by exactly one release, and
    the value stays live until the last of them.
    """
    if type(value) is not str or not value:
        raise ContractRefusal(
            "integrity", "schema",
            "a remembered secret is a non-empty string value")
    with _lock:
        _live[value] = _live.get(value, 0) + 1
    return value


def forget_secret(value):
    """Release ONE registration, and answer whether the value is still live.

    THE ANSWER IS ABOUT THE VALUE, NOT ABOUT WHAT THIS CALL DID. An unbalanced
    release of a value that is already gone has nothing to decrement, and
    reporting "still live" there would contradict the guard, which correctly
    permits it. Both branches consult the same fact.

    A verifier is single-use across acceptance, decline and expiry alike, so a
    spent bearer stops being live — and keeping dead strings would grow a
    registry that every durable write scans.
    """
    if type(value) is not str:
        raise ContractRefusal(
            "integrity", "schema",
            "a released secret is the string value that was remembered")
    with _lock:
        held = _live.get(value)
        if held is None:
            return False
        if held > 1:
            _live[value] = held - 1
            return True
        del _live[value]
        return False


def live_secret(value):
    """Whether this exact value is currently registered.

    Exported so a caller can ASK rather than infer from a release's answer.
    It is a fact about the registry and never about a document -- the walk is
    what decides a document.

    IT PROVES ITS OPERAND rather than answering False to anything that is not
    text. A value that cannot be a registered secret is a malformed question,
    and answering "no" to a malformed question is how a caller concludes it
    asked a good one.
    """
    if type(value) is not str:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(value)} cannot be a registered secret; a secret is "
            f"a string value and asking about anything else is a malformed "
            f"question")
    with _lock:
        return value in _live


class held_secret:
    """Hold a secret for the duration of one act, HOWEVER THAT ACT ENDS.

    A context manager rather than a callback, which is what Python gives for
    exactly this: the release is in `__exit__` and runs on a return, on a
    raise, and on a `break` out of the block. The frozen host needed a
    callback and then needed three review rounds of thenable handling to make
    the release wait for an asynchronous act; there is no such split here,
    because a `with` block ends when the block ends.

    NESTING IS THE POINT. Two owners of one value are two registrations, and
    the value stays live until the outer one leaves.
    """

    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def __enter__(self):
        return remember_secret(self._value)

    def __exit__(self, kind, value, traceback):
        forget_secret(self._value)
        return False


def _snapshot():
    """The live values, taken ONCE per walk.

    The walk recurses and the registry is shared state; re-reading it at every
    node would let a value registered mid-walk be refused in one subtree and
    admitted in another, which is a decision that depends on traversal order.
    """
    with _lock:
        return tuple(_live)


def check_no_durable_secret(document, what="a durable surface"):
    """Refuse a document that carries a secret, at any depth.

    Called BEFORE a document's other rules wherever both apply: a document
    carrying a secret is refused as SUCH rather than as whatever structural
    fault is also in it, because the two answers send a caller to different
    places.

    Returns the document, so a composite can chain it.
    """
    _walk(document, label_of(what), _snapshot())
    return document


def _walk(node, what, live):
    if type(node) is str:
        for secret in live:
            # CONTAINMENT. A message that interpolated the bearer carries it
            # just as durably as a member that held it alone.
            if secret in node:
                raise ContractRefusal(
                    "integrity", "secret-leak",
                    f"{what} carries a live bearer value; §13 keeps the one "
                    f"deliberate secret off every durable surface, whatever "
                    f"member it arrives in")
        return
    if type(node) in (list, tuple):
        for entry in node:
            _walk(entry, what, live)
        return
    if type(node) is not dict:
        # Numbers, booleans and None carry no text. NOT a general `object`
        # fallthrough: a value with behaviour is refused by the owner that
        # accepted the document, and reading its members here would run
        # somebody's code inside a rule whose whole job is to decide without
        # doing that.
        return
    for member, value in node.items():
        if type(member) is str and member.lower() in _FORBIDDEN:
            raise ContractRefusal(
                "integrity", "secret-leak",
                f"{what} carries {name_value(member)}; §13 keeps the one "
                f"deliberate secret off every durable surface, and a member "
                f"named for one says the value is one")
        # THE KEY IS WALKED TOO. A document whose KEY is the bearer is as
        # durable as one whose value is -- canonical JSON stores both.
        _walk(member, what, live)
        _walk(value, what, live)
