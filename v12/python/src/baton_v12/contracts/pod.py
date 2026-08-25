"""Exact built-in ownership for every document that crosses this boundary.

W4 cut A. This is the Python translation of the approved POD ruling: at an
in-process boundary the admitted container is an exact built-in `dict`, not a
dict subclass, arbitrary Mapping, proxy, dataclass, object, sequence or
accessor-bearing representation.

THE PROPERTY IS PORTABLE EVEN THOUGH THE MECHANISM IS NOT. The frozen host's
defect was a getter that answered one participant to the binding check and
another to the execution. Python's version of that is a `dict` subclass or a
`__getitem__` override, and the answer is the same one: types are tested with
`type(x) is T` and never `isinstance`, so a behaviour-bearing container is
REFUSED rather than admitted with its overrides intact. Validating one view and
executing another is then impossible rather than guarded against.

WHY THIS IS NOT `baton_v12.authority.identity.own`, which implements the same
idea. Two reasons, and the second is the one that decides it. First, the bounds
differ: the authority's are its own contract's, and these are the frozen
schema's. Second, `own` is not on the authority package's exported surface, and
the authority's boundary cases exist to refuse reaching past it -- so importing
it would break the very boundary the two-package split is for. A shared
primitive would be better than two copies of one idea, and PROMOTING ONE IS
RAISED RATHER THAN TAKEN: it changes the authority's exported promise, which is
closed Work.
"""

# The structural bounds live with the canonicalizer, because BOTH public doors
# have to enforce them and only one of them used to.
from .canonical import MAX_DEPTH, MAX_MEMBERS, MAX_SAFE_INTEGER
from .errors import (ContractRefusal, counted_sample_of, label_of,
                     name_value)

__all__ = ["own", "own_record", "MAX_DEPTH", "MAX_MEMBERS"]

def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def own(value, *, what="operand"):
    """Take a FRESH built-in copy of an exact built-in JSON value.

    Review [P1]: this took the traversal depth as a keyword. A leading
    underscore names a convention, not a boundary, so a caller could pass a
    negative one and own a document far past the frozen depth. A public
    operation takes only its genuine operands; the descent below keeps its own
    bookkeeping, where nobody can choose it.
    """
    return _own(value, label_of(what), 0)


def _own(value, what, _depth):
    """The descent. `what` is already bounded and the depth is ours.

    Owned in BOTH directions: the caller cannot reach in afterwards, and this
    package cannot leak a live reference back out.

    SNAPSHOT FIRST. Every member is read exactly once, into a copy, and nothing
    reads the caller's object again -- which is what makes "the value we
    validated is the value we used" a fact rather than an intention.
    """
    if _depth > MAX_DEPTH:
        _refuse(f"{what} nests deeper than the frozen limit of {MAX_DEPTH}")
    if value is None:
        return None
    kind = type(value)
    # `bool` first: `True` is an `int` in Python and is not an integer here.
    # Both survive as themselves; what must never happen is one becoming the
    # other.
    if kind is bool:
        return value
    if kind is int:
        if value < -MAX_SAFE_INTEGER or value > MAX_SAFE_INTEGER:
            _refuse(
                f"{what} carries an integer outside the range a consumer can "
                f"read back; it is {name_value(value)}")
        return value
    if kind is str:
        if not _round_trips(value):
            _refuse(
                f"{what} carries text that is not encodable; a durable value "
                f"round-trips or it is not one")
        return value
    if kind is list:
        if len(value) > MAX_MEMBERS:
            _refuse(
                f"{what} carries more than the frozen limit of {MAX_MEMBERS} "
                f"entries")
        return [_own(entry, what, _depth + 1) for entry in value]
    if kind is dict:
        if len(value) > MAX_MEMBERS:
            _refuse(
                f"{what} carries more than the frozen limit of {MAX_MEMBERS} "
                f"members")
        taken = {}
        # `dict.items` on an EXACT dict runs no caller code.
        for name, member in value.items():
            if type(name) is not str:
                _refuse(
                    f"{what} carries a {name_value(name)} name; a document's "
                    f"members are named by text, and coercing one would invent "
                    f"a member the caller did not send")
            if not _round_trips(name):
                _refuse(f"{what} carries a member name that is not encodable")
            taken[name] = _own(member, what, _depth + 1)
        return taken
    _refuse(
        f"{what} carries {name_value(value)}, which is not JSON data; this "
        f"boundary takes exact built-in documents and nothing that carries "
        f"behaviour")


def own_record(value, required, *, what="record"):
    """Own an exact record with EXACTLY the required member names.

    Extras are refused rather than dropped, and a missing member is named. An
    operand supplied and ignored is one the caller believes it chose, and a
    document silently rewritten is a document nobody can reason about -- the
    approved ruling retained exact POD precisely so an absent
    `provider_session_id` is not quietly rewritten to null.
    """
    what = label_of(what)
    taken = own(value, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one exact record; this is {name_value(value)}")
    required = tuple(required)
    # OUR OWN names, so the set is this contract's own small cost and not the
    # rejected value's. It turns the membership question below from one walk of
    # the rule per received member into one lookup.
    wanted = frozenset(required)
    # ONE PASS EACH, and neither materializes the rejected names. A generator
    # is the whole point: for a twenty-thousand-member record the sample keeps
    # three names and counts the rest, and no list of twenty thousand is ever
    # built to be sliced.
    extra, extra_count = counted_sample_of(
        name for name in taken if name not in wanted)
    missing, missing_count = counted_sample_of(
        name for name in required if name not in taken)
    if extra_count or missing_count:
        _refuse(_record_fault(what, len(required), len(taken),
                              extra, extra_count, missing, missing_count))
    return taken


def _record_fault(what, named, received, extra, extra_count,
                  missing, missing_count):
    """ONE diagnostic for one broken rule, not two alternatives for two halves.

    W1593 [P1]. This refused on the extras and returned, so a document that
    broke BOTH sides of the exact-record rule was told about one of them: a
    reference carrying `authority_uuid` and seven unexpected members heard
    about the seven and never that `work_id`, `participant` and
    `provider_session_id` were the point. Neither branch said how many members
    had actually arrived, so "three and four more" left the reader to guess
    whether that was most of the document or a corner of it.

    The approved hybrid is one message carrying the rule, what is missing from
    it, what arrived, a bounded sample of the unexpected names and how many
    were omitted -- and NO MEMBER VALUES, because the thing most likely to be
    logged and retained is a refusal.
    """
    clauses = []
    if missing_count:
        clauses.append(f"it needs {missing}")
    if extra_count:
        clauses.append(f"an exact record does not carry {extra}")
    fault = (f"{what} is an exact record of {_members(named, 'named')} and "
             f"{_members(received, 'received')} arrived: "
             f"{'; '.join(clauses)}")
    if extra_count:
        fault += ("; an extra member in an exact record is one the sender "
                  "believes was read")
    return fault


def _members(count, which):
    """`1 received member`, not `1 received members`.

    A refusal is the message most likely to be read by somebody who is already
    confused, and prose that stumbles is one more thing between them and the
    rule they broke.
    """
    return f"{count} {which} member{'' if count == 1 else 's'}"


def _round_trips(text):
    """True when the text is encodable, so a durable value can survive storage.

    Runs nothing: encoding an exact `str` is a built-in conversion.
    """
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True
