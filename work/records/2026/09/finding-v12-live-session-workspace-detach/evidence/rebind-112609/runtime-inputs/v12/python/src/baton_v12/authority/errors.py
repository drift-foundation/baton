"""One refusal type for the whole v12 authority.

A `Refusal` is an ORDINARY outcome: a precondition did not hold, an operand was
stale, an identity collided.  It is raised so no caller can mistake it for
success, and it is caught by the operation journal, which decides whether the
refusal wrote anything durable.

Anything that is NOT a `Refusal` escaping a transition is a fault.  The store
rolls the whole transaction back rather than journalling it, because an
operation whose failure we cannot describe is not one we may record an outcome
for.
"""

__all__ = ["Refusal", "refuse", "name_of", "type_name_of", "label_of"]

# The bound on any caller-controlled text this module puts into a message.  A
# refusal is the thing most likely to be logged, retained or carried onto a
# wire, so the diagnostic is bounded by the RULE and never by the operand.
_NAME_LIMIT = 60

# The bound on a caller-supplied diagnostic LABEL.
#
# Larger than the value bound, and measured rather than chosen: a label is the
# package's own prose naming the operand a rule is about, and the longest one
# this package writes is 118 characters -- the publication label that lists all
# five digests and then names the missing one. Setting the label bound at the
# VALUE bound truncated that label mid-word and took the member name with it, so
# a refusal that used to say which digest was missing stopped saying it.
#
# That is the settlement-signature lesson in another place: a bound below what
# the authority itself legitimately produces breaks the authority rather than the
# attacker. `test_the_label_bound_exceeds_the_longest_label_we_write` measures
# the package and fails if this number ever falls under it.
_LABEL_LIMIT = 160

# Integers wider than this are named by their bit length rather than
# rendered.  64 bits covers every value this contract can legitimately
# carry, so nothing a caller may validly send is ever reduced to a size.
_SHOWN_INTEGER_BITS = 64


class Refusal(Exception):
    """An ordinary refusal.

    `durable` is set by the transition that RAISES the refusal, and only when
    that transition has already written something it must keep -- the
    stale-target integration journals its attempt before refusing.

    Ported from the frozen Node authority with its correction intact: `durable`
    is a property of the RAISING SITE, not of the calling transition.  When it
    was a flag on the call site, one transition marked every refusal durable,
    including the ones that wrote nothing, and a pre-approval integration
    recorded a permanent REFUSED row for an operation that had not touched the
    store.  That inverts the rule: an ordinary refusal writes nothing and stays
    retryable, and REFUSED exists only when the refusal itself is a committed
    outcome.  Only the raising site knows which it was, so only the raising site
    may say so.
    """

    def __init__(self, message, *, code=None, durable=False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.durable = durable

    def __str__(self):
        return self.message


def refuse(message, *, code=None, durable=False):
    raise Refusal(message, code=code, durable=durable)


def name_of(value):
    """Name a REJECTED value from inert facts only.

    A refusal must never run the value it is refusing.  `repr()` and `str()`
    call methods the caller chose, and a caller that wants to can make either
    of them raise -- which would replace this refusal with an exception of the
    caller's choosing, at the exact moment the boundary had already decided to
    refuse.

    So: the TYPE NAME, which is the manager's own fact about the value, plus
    the value itself only for the handful of built-in constants that carry no
    caller content at all.  A `str` is shown because a string cannot run
    anything and is usually the whole diagnostic, bounded because an unbounded
    caller value in a durable message is a different problem.
    """
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    kind = type(value)
    if kind is str:
        # `ascii()` on a `str` runs nothing and cannot fail, and it renders a
        # lone surrogate readably instead of raising on the way out.
        return ascii(_shown(value))
    if kind is int:
        # Review [P1]: `str()` of an integer is NOT inert in Python 3.13 -- the
        # interpreter refuses to render one above 4,300 digits and raises
        # `ValueError`.  So the one function whose entire job is to describe a
        # rejected value safely was itself a way for a rejected value to escape
        # the authority's outcome taxonomy, which is precisely the defect this
        # helper exists to prevent, at the helper.
        #
        # `bit_length()` runs no conversion and cannot fail, so an integer too
        # large to show is described by its SIZE instead of by its digits.
        if value.bit_length() <= _SHOWN_INTEGER_BITS:
            return str(value)
        return f"an integer of {value.bit_length()} bits"
    # Review [P1]: this rendered the type name RAW, so the one helper whose job
    # is to describe a rejected value safely was itself unbounded -- a class
    # named with a million characters produced a million-character diagnostic.
    # Same shape as the integer finding: the mechanism carried the defect it
    # exists to prevent.
    return f"a {_shown(kind.__name__)}"


def _shown(text):
    """Bound one already-inert string by the RULE.

    The single place the sixty-character limit is applied, so a second caller of
    it cannot apply a different one.
    """
    if len(text) <= _NAME_LIMIT:
        return text
    return text[:_NAME_LIMIT] + "…"


def label_of(what):
    """Bound a caller-supplied DIAGNOSTIC LABEL by the rule.

    Review [P1]: the audit treated the label `what` as package-owned prose,
    because that is what it is at every INTERNAL call site. It is not what it is
    at the ten helpers `identity` EXPORTS: their public signatures take `what`
    from the caller, so a one-million-character label produced a
    one-million-character refusal through `own`, all six identity checks,
    `assignment_key` and `normalize_assignment`.

    The audit reported clean because it trusted the SPELLING of the variable
    rather than its origin, which is a sharper version of the same mistake the
    audit was written to stop: a rule that holds wherever somebody happened to
    look.

    A label is not quoted the way a rejected value is -- it is prose naming the
    operand a rule is about, and quoting it would make every message read like a
    citation. But the LENGTH rule is the same rule, so it is applied here, once,
    at the boundary that accepts the label. A label that is not text is named as
    a value instead, because a label that is not text is itself a fault worth
    seeing.
    """
    if type(what) is not str:
        return name_of(what)
    shown = what if len(what) <= _LABEL_LIMIT else what[:_LABEL_LIMIT] + "…"
    # Review [P1]: an exact `str` is INERT but not necessarily TEXT. Python
    # strings may hold lone surrogates, so a label of "\ud800" produced a
    # refusal that raised `UnicodeEncodeError` the moment anything logged it --
    # replacing an ordinary refusal with an encoding fault, which is the exact
    # failure `name_of` uses `ascii` to prevent for a rejected VALUE.
    #
    # Ordinary prose is returned as it was written; only text that cannot
    # round-trip is rendered, and `ascii` runs nothing and cannot fail. Slicing
    # cannot create this: Python strings are code points, so a bound never cuts
    # a character in half.
    try:
        shown.encode("utf-8")
    except UnicodeEncodeError:
        return ascii(shown)
    return shown


def type_name_of(value):
    """The bounded TYPE name, for a message that names a kind, not a value.

    `name_of` answers "what is this"; this answers "what KIND is this", for the
    messages whose rule is about the type -- a non-text member name, say.  It
    runs nothing: `type()` and `__name__` are the manager's own facts.
    """
    return _shown(type(value).__name__)
