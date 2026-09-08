"""The Work-label grammar, and nothing else.

W29400, under the approved W28880 contract.  A Work label is ONE OPAQUE KEY --
not a parsed `name=value` pair, not a path, not a namespace.  Dots, underscores
and hyphens are ordinary characters in it and carry no hierarchy, which is why
this module has no splitter and no separator vocabulary at all: a helper that
could take a label apart is the first step towards somebody reading meaning out
of a spelling, and the contract forbids inferring any authority or scheduler
behaviour from one.

WHY THE GRAMMAR IS THIS NARROW.  Case-insensitive uniqueness has to agree
across SQLite, Python, JSON, a CLI and a TUI.  Restricting the alphabet to
ASCII makes lowering deterministic everywhere -- Unicode case folding is
locale- and version-dependent, and two clients disagreeing about whether two
labels are the same key would make the live set ambiguous rather than merely
inconvenient.  The bounds also keep a complete projected set of 32 labels under
about 2 KiB, so a projection never becomes a paging problem.

WHAT IS DELIBERATELY ABSENT: no reserved spelling and no reserved prefix.  If
this authority later needs system-owned metadata it gets a typed field of its
own; a magic prefix would make a user's ordinary label silently authoritative,
which is exactly the inference the contract forbids.
"""

import re

from .errors import Refusal, label_of, name_of

__all__ = ["MAX_LABEL_LENGTH", "MAX_LABELS", "canonical_label",
           "canonical_label_set"]

MAX_LABEL_LENGTH = 64

# THE CARDINALITY IS A PROPERTY OF THE WORK, not of one call.  It is checked
# inside the write transaction that adds a label, because a limit enforced by a
# read before the write is a limit two concurrent additions can both pass.
MAX_LABELS = 32

_LABEL = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,63}\Z")


def canonical_label(value, *, what="a Work label"):
    """One supplied label, normalized and owned, or a refusal.

    NORMALIZED BEFORE IT IS VALIDATED, so `Release-Foo` and `release-foo` are
    one key and the refusal a caller sees is about the key rather than about
    its case.  `str.lower()` is not used: it case-folds beyond ASCII, and a
    label containing a character whose lowering is not ASCII would be accepted
    as a different string than the one the caller wrote.  The alphabet is
    checked on the LOWERED value, so `İ` is refused rather than silently
    becoming `i̇`.
    """
    what = label_of(what)
    if type(value) is not str:
        raise Refusal(
            f"{what} is {name_of(value)}; a Work label is text")
    lowered = "".join(
        chr(ord(one) + 32) if "A" <= one <= "Z" else one for one in value)
    if _LABEL.match(lowered) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; a Work label is 1 to "
            f"{MAX_LABEL_LENGTH} characters, starts with an ASCII letter or "
            f"digit, and continues with ASCII letters, digits, dots, "
            f"underscores or hyphens")
    return lowered


def canonical_label_set(values, *, what="a Work label set"):
    """A supplied collection of labels, as a sorted canonical tuple.

    DUPLICATES AFTER NORMALIZATION REFUSE rather than collapsing.  Two operands
    that normalize to one key are a caller who believes they asked for two
    things, and silently deduplicating would answer a question they did not
    ask -- the same reason a repeated filter operand refuses.

    The cardinality bound is NOT checked here: this is the shape of what was
    supplied, and how many labels the Work would then hold is a fact about the
    Work that only its write transaction can decide.
    """
    what = label_of(what)
    if type(values) not in (list, tuple):
        raise Refusal(
            f"{what} is {name_of(values)}; a Work label set is a list of "
            f"labels")
    seen = {}
    for one in values:
        canonical = canonical_label(one, what=f"{what}'s member")
        if canonical in seen:
            raise Refusal(
                f"{what} names {name_of(one)} and {name_of(seen[canonical])}, "
                f"which are one label after normalization; a set that meant "
                f"two things is not deduplicated into one")
        seen[canonical] = one
    return tuple(sorted(seen))
