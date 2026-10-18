"""The canonical dossier LOCATOR, and what may be said about one.

W321688, the minimal provider under W39435. This module owns the GRAMMAR and
nothing else: no store, no filesystem, no I/O. `core` binds and reads, a command
resolves evidence on disk, and the rule about what a locator may contain lives
here once so two callers cannot disagree about it.

WHY A LOCATOR IS NOT A PATH THIS AUTHORITY WALKS. W39435's approved direction is
a FLAT SET: the v11 records nest canonical directories under campaign and parent
records, so a reparent, a promotion or a dependency change wanted to MOVE a
durable record -- and a moved record is a broken reference in every review that
ever cited it. The correction is that containment, dependency, campaign and
routing live in authority state, and the record keeps one name for its whole
life. So this grammar REFUSES the things that would smuggle a relationship back
into the name:

  NO SEPARATORS. One flat segment. A locator carrying `/` would be read as a
  directory by somebody eventually, and the first time a Work was reparented the
  question "should it move?" would be reopened.

  NO RELATIVE OR ABSOLUTE ESCAPE. `.`, `..`, a leading `/` and a leading `-` are
  refused, which is also what makes a locator safe to join to a materialization
  root by a caller that is not this module.

  NO ROUTING OR RELATIONSHIP VOCABULARY. The locator is not derived from route,
  phase, parent, campaign or handler, and `bind_dossier` takes it as an operand
  rather than computing it, because an authority that derived the name from the
  route would have made the route the record's address.

WHAT IT IS INSTEAD: lowercase, digits and single hyphens, bounded, plus a
required collision-resistant suffix supplied by the caller. Two deployments that
both pick `operator-quickstart` collide; `operator-quickstart-7f3a91c2` does not,
and the authority still refuses the second binding of either rather than
resolving it.

THE EXACT SPELLING IS AN IMPLEMENTATION DETAIL under W39435's rule, which is why
the constants are named and bounded here rather than asserted in a test.
"""

import re

from .errors import Refusal, label_of
from .identity import name_of

__all__ = ["LOCATOR_LIMIT", "SUFFIX_LENGTH", "EVIDENCE_LIMIT",
           "check_locator", "check_evidence_reference", "check_evidence_digest"]

# Long enough for a readable deliverable name plus the suffix, short enough to
# be a filesystem segment on every platform a materializer might use.
LOCATOR_LIMIT = 96

# The collision-resistant tail. Hex, because it is the one alphabet every
# identity in this authority already speaks.
SUFFIX_LENGTH = 8

# A dossier binds a bounded set of evidence references. This is a RECORD, not an
# archive index: the number is here so "a few more" is a decision somebody makes
# rather than something that happens.
EVIDENCE_LIMIT = 64

_LOCATOR = re.compile(
    r"\A[a-z0-9]+(?:-[a-z0-9]+)*-[0-9a-f]{%d}\Z" % SUFFIX_LENGTH)

# An evidence reference is a repository-relative POSIX path. It is text this
# authority STORES and never opens, so the grammar is about what a later
# resolver may safely join rather than about what exists today.
_EVIDENCE = re.compile(r"\A[A-Za-z0-9._][A-Za-z0-9._/-]*\Z")
_EVIDENCE_LIMIT_CHARS = 240

# sha256, lowercase, prefixed, because every other digest this distribution
# records is spelled that way and a second spelling would be a second thing to
# compare.
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


def check_locator(value, *, what="a dossier locator"):
    """One flat canonical locator, or a refusal naming what is wrong with it.

    THE SUFFIX IS REQUIRED rather than appended here. A grammar that generated
    the tail would be deciding identity, and identity in this authority is
    supplied by its trusted bootstrap; what this does is refuse a name that
    cannot be collision-resistant.
    """
    # The LABEL is caller text at every exported helper, so it is bound by
    # the rule here, once, where it is accepted -- `identity`'s own convention.
    what = label_of(what)
    if type(value) is not str or not value:
        raise Refusal(
            f"{what} is {name_of(value)}; a dossier locator is text")
    if len(value) > LOCATOR_LIMIT:
        raise Refusal(
            f"{what} is {len(value)} characters and the limit is "
            f"{LOCATOR_LIMIT}; a canonical locator is a name, not a document")
    # NAMED BEFORE THE GRAMMAR, because "does not match" would send an operator
    # to re-read a regular expression when the actual answer is "this looks like
    # a path, and a dossier locator is deliberately not one".
    for one in ("/", "\\", ":"):
        if one in value:
            raise Refusal(
                f"{what} contains {name_of(one)}; a canonical dossier locator "
                f"is ONE FLAT SEGMENT. Containment, dependency, campaign and "
                f"routing live in authority state, so a record keeps one name "
                f"for its whole life and a relationship change moves nothing")
    if value in (".", "..") or value.startswith(".") or value.startswith("-"):
        raise Refusal(
            f"{what} is {name_of(value)}; a locator that begins with a dot or "
            f"a hyphen is a relative-path or option escape at whatever root a "
            f"materializer later joins it to")
    if _LOCATOR.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; a canonical dossier locator is "
            f"lowercase letters, digits and single hyphens ending in a "
            f"{SUFFIX_LENGTH}-character hex suffix, as in "
            f"'operator-quickstart-7f3a91c2' -- the suffix is what makes two "
            f"deployments choosing one deliverable name not collide")
    return value


def check_evidence_reference(value, *, what="an evidence reference"):
    """One repository-relative reference this authority records and never opens.

    REFUSED BEFORE IT IS STORED, not when somebody tries to resolve it. An
    absolute path or a `..` segment is a reference whose meaning depends on who
    joins it, and a durable record of one would be a standing escape.
    """
    # The LABEL is caller text at every exported helper, so it is bound by
    # the rule here, once, where it is accepted -- `identity`'s own convention.
    what = label_of(what)
    if type(value) is not str or not value:
        raise Refusal(
            f"{what} is {name_of(value)}; an evidence reference is text")
    if len(value) > _EVIDENCE_LIMIT_CHARS:
        raise Refusal(
            f"{what} is {len(value)} characters and the limit is "
            f"{_EVIDENCE_LIMIT_CHARS}")
    if value.startswith("/") or value.startswith("~"):
        raise Refusal(
            f"{what} is {name_of(value)}; an evidence reference is RELATIVE to "
            f"the materialization root a resolver supplies, so an absolute "
            f"path here would name a file on whichever host read the record")
    segments = value.split("/")
    if any(one in ("", ".", "..") for one in segments):
        raise Refusal(
            f"{what} is {name_of(value)}; an empty, dot or parent segment "
            f"escapes the root it will be joined to")
    if _EVIDENCE.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; an evidence reference is a POSIX "
            f"relative path of letters, digits, dot, underscore and hyphen")
    return value


def check_evidence_digest(value, *, what="an evidence digest"):
    """`sha256:<64 hex>`, which is what the rest of this distribution records.

    THE DIGEST IS REQUIRED, and that is the honesty of the whole feature: a
    reference with no digest can only answer "a file by this name exists", and
    the acceptance asks for a refusal when the evidence a record cites is absent
    OR has changed underneath it.
    """
    # The LABEL is caller text at every exported helper, so it is bound by
    # the rule here, once, where it is accepted -- `identity`'s own convention.
    what = label_of(what)
    if type(value) is not str or _DIGEST.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; an evidence digest is "
            f"'sha256:' and 64 lowercase hex characters")
    return value
