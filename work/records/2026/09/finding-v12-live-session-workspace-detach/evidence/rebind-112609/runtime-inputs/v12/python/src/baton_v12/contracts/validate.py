"""Draft 2020-12 validation against the frozen schemas.

W4 cut A, second half. PLAN item 4bh ruled this: a REAL validator, pinned with
its complete Python 3.13 closure in the hash-locked build, and no
handwritten substitute. The alternative shapes -- a test-only oracle, or a
partial first cut -- were considered and rejected, so the validator is a runtime
dependency of this slice and of no other.

WHY A LIBRARY HERE AND NOT FOR CANONICALIZATION, since the same distribution
does hand-implement RFC 8785. The canonicalizer's hard part is number
formatting, and this contract has no numbers to format -- what remains is member
ordering and string escaping, and the refusals close it. JSON Schema has a large
construct surface that would be RE-DERIVED rather than implemented, which is the
mistake this repository has caught me making before.

THE LIBRARY'S PROSE DOES NOT LEAVE THIS MODULE. `jsonschema` renders the
rejected instance into its messages -- that is what makes its errors useful and
exactly what this boundary may not do. A refusal here is built from the failing
KEYWORD and the failing PATH, which are facts about the schema and the document
shape, plus this package's own bounded rendering of anything caller-supplied. So
a one-million-character rejected value cannot arrive in a diagnostic by way of a
dependency's helpfulness.

AND THE DOCUMENT IS OWNED BEFORE IT IS VALIDATED. `own` refuses every
behaviour-bearing container first, so the validator only ever walks exact
built-ins: it is never the thing that decides whether a `__getitem__` override
is admissible, because one cannot reach it.
"""

import json

import jsonschema

from .canonical import digest
from .errors import ContractRefusal, label_of, name_value
from .frozen import (AGENT_SESSION_BYTES, WORKER_CONTROL_BYTES)
from .pod import own

__all__ = ["validate_worker_control", "validate_agent_session",
           "validate_against", "validate_fragment",
           "validate_agent_session_fragment", "verify_manifest_digest",
           "DEFINITIONS", "AGENT_SESSION_DEFINITIONS"]

# How many failures a refusal SHOWS. A wide record can fail hundreds of
# constraints, and the W1593 rule applies to the explanation: a fixed message
# budget, a bounded sample, a total, and no rejected values.
_SHOWN_FAILURES = 3

# The validators are built ONCE, at import, and their schemas are the frozen
# package assets. `check_schema` runs here rather than being trusted: a schema
# this package ships that is not a valid Draft 2020-12 schema is a defect in
# this package, and finding it at import is better than finding it on the first
# document.
# Review [P1]: the validators were built over the SAME dicts exported as
# `WORKER_CONTROL` and `AGENT_SESSION`, so replacing `WORKER_CONTROL["oneOf"]`
# rewrote what the runtime enforced -- a caller editing a readable projection
# changed the contract. The product may expose a readable schema; runtime
# authority is built from a PRIVATE parse of the frozen bytes, which no caller
# holds a reference to.
_WORKER_CONTROL_SCHEMA = json.loads(WORKER_CONTROL_BYTES.decode("utf-8"))
_AGENT_SESSION_SCHEMA = json.loads(AGENT_SESSION_BYTES.decode("utf-8"))

jsonschema.Draft202012Validator.check_schema(_WORKER_CONTROL_SCHEMA)
jsonschema.Draft202012Validator.check_schema(_AGENT_SESSION_SCHEMA)

_WORKER_CONTROL = jsonschema.Draft202012Validator(_WORKER_CONTROL_SCHEMA)
_AGENT_SESSION = jsonschema.Draft202012Validator(_AGENT_SESSION_SCHEMA)

# ONE VALIDATOR PER FRAGMENT, built from the SAME private parse.
#
# Cut D's remaining work validates DEFINITIONS rather than whole envelopes: a
# sealed result is a `resultManifest`, an attempt's declaration is an
# `inputManifest`, and neither arrives wrapped in a control envelope. A
# definition compiled from the frozen document's own `$defs` is the same
# contract read at a different depth -- not a second opinion about it.
#
# The subschema is `{$id, $defs, $ref}` and nothing else. Keeping the frozen
# document's other top-level keywords would apply the ENVELOPE's constraints as
# well, so every fragment would have to be an envelope to validate as itself.
DEFINITIONS = tuple(sorted(_WORKER_CONTROL_SCHEMA["$defs"]))

_FRAGMENTS = {
    name: jsonschema.Draft202012Validator({
        "$schema": _WORKER_CONTROL_SCHEMA["$schema"],
        "$id": _WORKER_CONTROL_SCHEMA["$id"],
        "$defs": _WORKER_CONTROL_SCHEMA["$defs"],
        "$ref": f"#/$defs/{name}",
    })
    for name in DEFINITIONS
}

# THE SAME TREATMENT FOR THE OTHER FROZEN SCHEMA, and it is a second table
# rather than one merged one. W6592: the manager's composition validates an
# agent-session `sessionProfile`, which is a definition of a DIFFERENT frozen
# document. Merging the two `$defs` namespaces would let a name resolve against
# whichever schema happened to carry it -- and `version`, `digest` and
# `timestamp` are defined in both -- so a caller asking for one contract's
# definition could silently receive the other's.
AGENT_SESSION_DEFINITIONS = tuple(sorted(_AGENT_SESSION_SCHEMA["$defs"]))

_AGENT_SESSION_FRAGMENTS = {
    name: jsonschema.Draft202012Validator({
        "$schema": _AGENT_SESSION_SCHEMA["$schema"],
        "$id": _AGENT_SESSION_SCHEMA["$id"],
        "$defs": _AGENT_SESSION_SCHEMA["$defs"],
        "$ref": f"#/$defs/{name}",
    })
    for name in AGENT_SESSION_DEFINITIONS
}

# The validator objects this package will RUN. Identity, not shape: a duck-typed
# object with an `iter_errors` method is a caller program, and running one is
# the seam this check closes.
_OWNED_VALIDATORS = (_WORKER_CONTROL, _AGENT_SESSION) + tuple(
    _FRAGMENTS[name] for name in DEFINITIONS) + tuple(
    _AGENT_SESSION_FRAGMENTS[name] for name in AGENT_SESSION_DEFINITIONS)


def _path_of(error):
    """The failing member path, as this package's own text.

    Built from the path elements, which are member names and array indices --
    facts about the document's SHAPE. The rejected value is not in it, and
    neither is the library's rendering of it.
    """
    if not error.absolute_path:
        return "the document"
    parts = []
    for element in error.absolute_path:
        if type(element) is int:
            parts.append(f"[{element}]")
        else:
            # A member NAME is caller-supplied text, so it is rendered by the
            # same bounded rule as any other caller value.
            parts.append(name_value(element))
    return ".".join(parts)


# How deep to follow a combinator's sub-errors. `oneOf` and `anyOf` carry their
# real failures in `context`, and this schema's top level is one `oneOf` over
# every message shape -- so a fault that stopped at the outer error would say
# "the document breaks oneOf" and tell a caller nothing at all. Found by my own
# case rather than by a review, which is the first time that has happened in
# this campaign and worth saying so.
_FAULT_DEPTH = 4


def _fault_of(error, depth=0):
    """One failure, named by the KEYWORD it broke and WHERE it broke.

    `error.validator` is the schema keyword -- `type`, `required`, `pattern`,
    `maxLength` -- which is the schema's own vocabulary and never the caller's.
    `error.message` is deliberately NOT used: it renders the rejected instance.

    A combinator is followed into its sub-errors, because "breaks oneOf" is a
    true statement that helps nobody. The descent is bounded, and it picks the
    sub-error that got FURTHEST into the document -- the branch the caller most
    likely meant, which is the same heuristic the library's own `best_match`
    uses and the only part of it worth borrowing.
    """
    keyword = error.validator
    if type(keyword) is not str:
        keyword = "a schema rule"
    context = getattr(error, "context", None)
    if context and depth < _FAULT_DEPTH:
        deepest = None
        for sub in context:
            if deepest is None or len(sub.absolute_path) > len(deepest.absolute_path):
                deepest = sub
        if deepest is not None:
            return f"{_fault_of(deepest, depth + 1)} (under {keyword})"
    return f"{_path_of(error)} breaks {keyword}"


def _count_of(error, depth=0):
    """How many failures this error really carries.

    One `oneOf` error over seventeen message shapes is seventeen failures, and
    counting it as one made "and N more" say nothing for the document that needs
    it most.
    """
    context = getattr(error, "context", None)
    if context and depth < _FAULT_DEPTH:
        return sum(_count_of(sub, depth + 1) for sub in context)
    return 1


def validate_against(validator, document, *, what="document"):
    """Validate against one of THIS PACKAGE'S validators.

    Review [P1]: this accepted an arbitrary object and invoked its `iter_errors`,
    which put a caller-program execution seam in the trusted contracts surface --
    the one thing this whole cut exists to keep out. The document was owned
    first, so the caller could not smuggle a container; nothing stopped it
    smuggling a VALIDATOR.

    The check is IDENTITY rather than shape. A duck-typed object with the right
    method is exactly what a caller supplies, so asking "does it have
    `iter_errors`" would be asking the attacker to confirm their own
    credentials.
    """
    for owned in _OWNED_VALIDATORS:
        if validator is owned:
            return _validate_with(validator, document, what=what)
    raise ContractRefusal(
        "integrity", "schema",
        f"{label_of(what)} can only be validated against a frozen schema this "
        f"package owns; a supplied validator is a program and this boundary "
        f"runs none")


def _validate_with(validator, document, *, what="document"):
    """Own the document, then validate it, then refuse in OUR words.

    The order is the point. Ownership first means the validator walks exact
    built-ins only; validation second means the schema decides the contract; and
    the refusal last means the diagnostic is built from the schema's vocabulary
    and this package's bounded rendering, never from the library's prose.

    Returns the OWNED document, so a caller that validates cannot then go on to
    use the original -- which is the same "validate one view, execute another"
    defect this cut exists to make impossible.
    """
    what = label_of(what)
    owned = own(document, what=what)
    # `iter_errors` rather than `validate`: the first failure is rarely the
    # useful one, and a bounded SAMPLE plus a total says more than a single
    # arbitrary error while staying inside the message budget.
    failures = []
    total = 0
    for error in validator.iter_errors(owned):
        total += _count_of(error)
        if len(failures) < _SHOWN_FAILURES:
            failures.append(_fault_of(error))
        # No early exit: the count is part of the answer, and iteration over an
        # owned exact document is bounded work by construction -- `own` has
        # already refused anything deeper than the frozen depth or wider than
        # the frozen width.
    if total:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} does not satisfy the frozen schema: "
            f"{_sample_of_faults(failures, total)}")
    return owned


def _sample_of_faults(failures, total):
    """The analogue of `sample_of` for schema failures.

    Separate from it deliberately: `sample_of` QUOTES what it names, because it
    names caller-supplied member names. A fault is already this package's own
    prose -- a schema keyword and a path -- so quoting it would read like a
    citation of ourselves.
    """
    shown = "; ".join(failures)
    if total <= len(failures):
        return shown
    return f"{shown} and {total - len(failures)} more"


# The two named entry points bound their own label.
#
# They delegate to a body that bounds it too, so they were SAFE IN EFFECT -- and
# the new exported-label check flagged them anyway, correctly. A label becomes
# caller input at the EXPORTED BOUNDARY, and a property that holds only because
# of what a callee happens to do is a property that holds where somebody looked.
# `label_of` is idempotent, so bounding it here costs a call and makes the
# guarantee local to the function that makes it.
def validate_fragment(document, definition, *, what="document"):
    """Validate against ONE named definition of the frozen worker-control
    schema.

    `definition` is a CLOSED SET -- the frozen document's own `$defs` keys --
    and the type is established before the membership question, because
    `x in mapping` on an unhashable value raises rather than answering and a
    check that assumes the type it is checking is not owning the field.

    A NAME, never a subschema. The frozen host also accepts an inline fragment
    here; this does not, because a caller-supplied subschema is a program this
    boundary would then run -- the same seam `validate_against`'s identity check
    exists to close, arriving as data instead of as an object.
    """
    what = label_of(what)
    if type(definition) is not str or definition not in _FRAGMENTS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names definition {name_value(definition)}, which is not "
            f"one of the frozen worker-control schema's own definitions")
    return validate_against(_FRAGMENTS[definition], document, what=what)


def validate_agent_session_fragment(document, definition, *,
                                    what="document"):
    """Validate against ONE named definition of the frozen AGENT-SESSION schema.

    The sibling of `validate_fragment`, and deliberately a separate operation
    rather than a `schema=` parameter on that one. A caller that names a
    definition is naming a contract, and the contract it means is not something
    this boundary should infer from a keyword: `version`, `digest` and
    `timestamp` are defined in BOTH frozen documents, so one function over a
    merged namespace would answer about whichever schema happened to carry the
    name first.
    """
    what = label_of(what)
    if type(definition) is not str \
            or definition not in _AGENT_SESSION_FRAGMENTS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names definition {name_value(definition)}, which is not "
            f"one of the frozen agent-session schema's own definitions")
    return validate_against(_AGENT_SESSION_FRAGMENTS[definition], document,
                            what=what)


def verify_manifest_digest(manifest, *, what="manifest"):
    """A manifest must be the document its own digest names.

    §12: the declared `manifest_digest` is computed over the manifest WITHOUT
    that member -- so the number is a fact about the bytes rather than a field
    the document filled in about itself. A document whose declared digest does
    not recompute is one whose identity nobody can rely on, and every table that
    stores a manifest stores it under this key.

    Returns the RECOMPUTED digest, not the declared one. A caller that stores
    what it was handed is storing a claim; a caller that stores what this
    returns is storing a computation.
    """
    what = label_of(what)
    owned = own(manifest, what=what)
    if type(owned) is not dict or "manifest_digest" not in owned:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} carries no manifest digest, so nothing identifies it")
    recomputed = digest({member: value for member, value in owned.items()
                         if member != "manifest_digest"})
    if owned["manifest_digest"] != recomputed:
        raise ContractRefusal(
            "integrity", "digest",
            f"{what} declares a manifest digest its own bytes do not produce; "
            f"a manifest that does not identify itself is not one")
    return recomputed


def validate_worker_control(document, *, what="worker-control document"):
    return validate_against(_WORKER_CONTROL, document, what=label_of(what))


def validate_agent_session(document, *, what="agent-session document"):
    return validate_against(_AGENT_SESSION, document, what=label_of(what))
