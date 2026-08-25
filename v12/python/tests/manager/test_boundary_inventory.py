"""W4 — receiving trust-domain ENTRIES, keyed lexically, each with one owner and
one probe.

PLAN 4bz and 4cc. Two findings made the previous two versions of this file
worthless, and they are different findings:

  1. AN INVENTORY THAT BEGINS WITH `boundaries.<kind>` CALLS CANNOT DISCOVER A
     MISSING VALIDATOR. If an entry has no owner there is nothing to collect, so
     the walk reported a clean sweep over exactly the entries that already had
     one.
  2. AND FIXING THAT FOR TWO DOMAINS LEFT IT TRUE OF THE THIRD. The replacement
     called something an adopted entry only when it already saw a
     `boundaries.adopted` call -- the same circularity, one domain over. The
     offers table was read with `SELECT *` from three places and owned in none,
     and a persisted `settle_by` of `not-an-instant` was compared against the
     current instant with nothing refusing it.

So each domain's universe is now discovered from a structure that exists WHETHER
OR NOT ANYBODY OWNED IT:

  caller    every parameter of every public operation
  injected  every call THROUGH a capability the deployment supplied -- the
            session, the bearer mint, the clock
  adopted   every SQL read, keyed by the table it reads

An entry is `(domain, site, subject)` and the SITE IS LEXICAL: module, class and
function. `AuthorityPort.claim` and a module-level `claim` are two functions with
one name, and an inventory keyed by name alone silently merges them -- which is
how three of this package's operations went missing from a green inventory.

THE SAME KEY GOVERNS ALL THREE QUESTIONS. What exists, who owns it, and what
proves the owner is real are looked up by the same tuple, so a repeated label
cannot stand in for two entries and an entry cannot be covered by a probe aimed
somewhere else.

AND OWNERSHIP IS ONCE. PLAN 4bz: a value is owned as it crosses into the
receiving domain and is not blanket-revalidated afterwards.
"""

import ast
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore, boundaries,
                                      certify_profile, documents, schema)

from baton_v12.worker_manager import workspaces

from .test_handshake import acp_profile
from .test_offers import (FakeSession, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)

NOW = "2026-08-24T00:00:00.000Z"
SURROGATE = "\ud800"


class _ObservingAgent:
    """The agent adapter contract, with an answer a probe may spoil."""

    def __init__(self, answer=None):
        self._answer = answer

    def cancel(self, operands):
        return {"acknowledged": True}

    def observe_session(self, reference):
        if self._answer is None:
            return {"kind": "present", "state": "initializing",
                    "provider_session_id": reference["provider_session_id"]}
        return self._answer


class _HalfAnAgent:
    """An adapter carrying one of the two operations the contract names.

    W6627 defined that contract for the first time: before it, `agent.cancel`
    was a call with nothing saying an adapter had to have it.
    """

    def cancel(self, operands):
        return {"acknowledged": True}
SHAPED_BUT_UNREAL = "2026-99-99T99:99:99.999Z"

PACKAGE = pathlib.Path(worker_manager.__file__).resolve().parent
LAYER = pathlib.Path(boundaries.__file__).resolve().name

# Parameters that are not receiver INPUTS: the capabilities an operation acts
# THROUGH. Each is owned where it is constructed -- `ControlStore.open` for the
# store, `AuthorityPort` for the port -- and what a capability ANSWERS is an
# injected entry in its own right, discovered below.
# Review [P1]: this used to remove every capability operand, on the grounds that
# each is owned where it is CONSTRUCTED. Two of them were owned nowhere -- a
# non-callable bearer mint performed four authority interactions before escaping
# as a raw TypeError -- and an exclusion nobody checks is a hole with a comment
# over it. A capability operand is an entry like any other now; what differs is
# who owns it, and CONSTRUCTED_BY has to name a constructor that exists.
NOT_INPUTS = {"self", "cls"}

# The capabilities this package calls THROUGH. A call on one of these is a
# crossing into the injected domain, whatever the call is named.
CAPABILITIES = {"_session", "session", "_clock", "clock", "mint_bearer",
                "_claim_signature", "adapter", "agent"}

# Capabilities whose MEMBER NAME is not enough to identify a crossing. `cancel`
# exists on the authority session AND on the provider agent, so for these the
# holder's name is part of the member's identity -- two crossings that share a
# verb are still two crossings.
QUALIFIED = {"adapter", "agent"}

# Handles whose ANSWERS came from a capability, for origin tracking only. The
# port is this build's own object; what it returns is the authority's.
PORTS = {"port"}

# WHERE THE SUBJECT AND THE LABEL SIT, per kind. A table rather than a rule,
# because I tried two rules and both were wrong: "the label is args[1]" missed
# `deadline`, whose duration sits between, and "the label is the last
# positional" missed `alternative`, whose variant contract sits after.
POSITIONS = {"deadline": (1, 2)}


def _sources():
    for source in sorted(PACKAGE.rglob("*.py")):
        if source.name in (LAYER, "__init__.py"):
            continue
        yield source, ast.parse(source.read_text(encoding="utf-8"), str(source))


def _functions(tree, module):
    """Every function, with its LEXICAL site: module, enclosing classes, name.

    Review [P1]: the previous key was the function name alone, so two methods
    with one name collapsed into a single node -- and an inventory that cannot
    tell `AuthorityPort.claim` from a module-level `claim` cannot say which one
    has an owner.
    """
    def walk(node, prefix):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield f"{module}:{prefix}{child.name}", child
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
    yield from walk(tree, "")


def _capability_call(node):
    """The capability member this call goes through, or None."""
    if not isinstance(node, ast.Call):
        return None
    called = node.func
    if isinstance(called, ast.Name):
        return called.id if called.id in CAPABILITIES else None
    if not isinstance(called, ast.Attribute):
        return None
    base = called.value
    if isinstance(base, ast.Name) and base.id in CAPABILITIES:
        return (f"{base.id}.{called.attr}" if base.id in QUALIFIED
                else called.attr)
    if isinstance(base, ast.Attribute) and base.attr in CAPABILITIES \
            and isinstance(base.value, ast.Name) and base.value.id == "self":
        return called.attr
    if isinstance(base, ast.Name) and base.id == "self" \
            and called.attr in CAPABILITIES:
        return called.attr.lstrip("_")
    return None


def _capability_value(node):
    """A capability's bound VALUE -- `session.participant`, not a call.

    Review [P1]: the universe modelled capability CALLS and not the values a
    capability carries, so an unencodable bound participant constructed happily
    and every authorization this manager recorded named an identity that cannot
    be stored.
    """
    if not isinstance(node, ast.Attribute):
        return None
    if node.attr in CAPABILITIES:
        # `self._session` IS the capability, not a member of one.
        return None
    base = node.value
    if isinstance(base, ast.Name) and base.id in CAPABILITIES:
        return (f"{base.id}.{node.attr}" if base.id in QUALIFIED
                else node.attr)
    if isinstance(base, ast.Attribute) and base.attr in CAPABILITIES \
            and isinstance(base.value, ast.Name) and base.value.id == "self":
        return node.attr
    return None


def _member_read(node):
    """(name, member) for `x["m"]` and `x.get("m")`, or None."""
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
            and type(node.slice.value) is str:
        return (node.value, node.slice.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "get" and node.args \
            and isinstance(node.args[0], ast.Constant) \
            and type(node.args[0].value) is str:
        return (node.func.value, node.args[0].value)
    return None


def _read_table(node):
    """The table this call reads, or None if it is not a SELECT.

    The SQL is assembled from its literal pieces, so a query built by
    concatenation -- which the offers reader is -- is still recognised. Nothing
    here executes anything; it reads the text the code will hand SQLite.
    """
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute" and node.args):
        return None
    pieces = []
    stack = [node.args[0]]
    while stack:
        item = stack.pop(0)
        if isinstance(item, ast.Constant) and type(item.value) is str:
            pieces.append(item.value)
        elif isinstance(item, ast.BinOp):
            stack[:0] = [item.left, item.right]
        elif isinstance(item, ast.JoinedStr):
            stack[:0] = list(item.values)
    text = " ".join(pieces)
    if not text.lstrip().upper().startswith("SELECT"):
        return None
    words = text.replace("(", " ").split()
    if "FROM" not in words:
        raise AssertionError(f"a SELECT with no FROM: {text!r}")
    return words[words.index("FROM") + 1]


def _source(value, origins, site=None, returns=None):
    """Where this expression's value crossed from, if it crossed at all.

    ONE function for every shape a crossing can be written in. There were two,
    and they drifted: the one that bound local names followed aliases and helper
    returns while the one that resolved a call's argument did not, so a crossing
    handed straight into a helper was tracked and the same crossing handed back
    OUT of one was not.
    """
    if isinstance(value, ast.Name):
        return origins.get(value.id)
    if site is not None:
        table = _read_table(value)
        if table is not None:
            # THE SITE IS PART OF THE ORIGIN. `meta` is read at two places and a
            # crossing belongs where it happened, so an adopted origin names the
            # read rather than only the table.
            return f"read:{site}|{table}"
    member = _capability_call(value)
    if member is not None:
        return f"session:{member}"
    bound = _capability_value(value)
    if bound is not None:
        return f"session:{bound}"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) \
            and value.func.id == "getattr" and value.args:
        # `getattr(adapter, "start", None)` IS the adapter, one member in. A
        # capability typed by the method it must supply is still that
        # capability's operand being owned, and an inventory that stopped here
        # would call the owner an orphan and the parameter unowned.
        return _source(value.args[0], origins, site, returns)
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        if isinstance(value.func.value, ast.Name):
            if value.func.value.id in PORTS:
                # The port is ours; what it hands back is the authority's, and
                # it is the same crossing however many of our own frames it
                # passes through.
                return f"session:{value.func.attr}"
            if value.func.value.id == "boundaries" and value.args:
                # THROUGH the layer. `answer = boundaries.document(...)` binds a
                # value that still came from wherever its subject came from.
                return _source(value.args[0], origins, site, returns)
        if value.func.attr in ("fetchone", "fetchall"):
            return _source(value.func.value, origins, site, returns)
    read = _member_read(value)
    if read is not None:
        inner = _source(read[0], origins, site, returns)
        return None if inner is None else f"{inner}[{read[1]}]"
    if isinstance(value, ast.Subscript):
        # A row taken out of a list of rows is still that read's row.
        return _source(value.value, origins, site, returns)
    if isinstance(value, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        # A list of rows is the read that produced them.
        return _source(value.elt, origins, site, returns)
    if isinstance(value, (ast.BoolOp, ast.IfExp)):
        # `answer.get("record") or {}` and `found[0] if found else None` are the
        # same value wearing a default. Review [P1]: tracking stopped at the
        # first of these, so a retirement's `reason` and `disposition` were
        # consumed through the alias while the inventory reported the record
        # owned and its fields invisible.
        parts = (value.values if isinstance(value, ast.BoolOp)
                 else [value.body, value.orelse])
        for operand in parts:
            found = _source(operand, origins, site, returns)
            if found is not None:
                return found
    if isinstance(value, ast.Call) and returns is not None:
        called = value.func
        name = (called.attr if isinstance(called, ast.Attribute)
                else getattr(called, "id", None))
        if name in returns:
            # A private helper that HANDS BACK a crossing hands back the
            # crossing. `row = self._operation_row(...)` is the journal row, and
            # a member read on it is a member of the adopted row.
            return returns[name]
    return None


def _returned_origins(sources):
    """Private helpers that HAND BACK a crossing, and which crossing.

    `_operation_row` returns an adopted journal row and `_offer_row` an adopted
    offer; a caller's member read on what they return is a read of that row.
    Resolved to a fixpoint, because helpers call helpers -- `_require_accepted`
    hands back what `_offer_row` handed it.
    """
    found = {}
    for _ in range(4):
        before = dict(found)
        for source, tree in sources:
            for site, node in _functions(tree, source.name):
                local = _origins(node, site, found)
                for piece in ast.walk(node):
                    if isinstance(piece, ast.Return) \
                            and piece.value is not None:
                        origin = _source(piece.value, local, site, found)
                        if origin is not None:
                            found.setdefault(node.name, origin)
        if found == before:
            break
    return found


def _origins(node, site, returns=None, seed=None, own_parameters=True):
    """Which local names hold a value that CROSSED a trust boundary.

    A read's row is bound to a name and owned a line later, and the inventory
    has to know the two are the same value. Assignments, `for` targets and
    comprehension generators all bind, so all three are followed.
    """
    # THE PARAMETERS ARE ORIGINS TOO. Review [P1]: a caller-supplied structured
    # value's members were not modelled at all, so the public revival boundary
    # could check four member NAMES and hand their contents straight on while
    # the inventory reported the entry owned. A caller's document has members
    # for the same reason an injected one does.
    # A HELPER SEEN FROM ITS CALLER carries the CALLER's origins on the
    # parameters the caller bound, and its own locals are derived from those.
    # Its remaining parameters are NOT caller entries at that site: they are
    # internal values of the operation that called it, which is the rule a
    # private helper's parameters have followed since 4bz.
    origins = ({} if not own_parameters else
               {name: f"caller:{name}" for name in _parameters(node)
                if name not in NOT_INPUTS})
    if seed is not None:
        origins.update(seed)

    def bind(target, origin):
        if origin is not None and isinstance(target, ast.Name):
            origins[target.id] = origin

    for piece in ast.walk(node):
        if isinstance(piece, ast.Assign):
            for target in piece.targets:
                bind(target, _source(piece.value, origins, site, returns))
        elif isinstance(piece, (ast.For, ast.AsyncFor)):
            bind(piece.target, _source(piece.iter, origins, site, returns))
        elif isinstance(piece, ast.comprehension):
            bind(piece.target, _source(piece.iter, origins, site, returns))
    return origins


def receiving_entries():
    """Every receiving trust-domain entry, from a structure no owner defines.

    A parameter nobody validates, a SQL read nobody adopts and a capability
    answer nobody owns all appear here. That is the whole difference from the
    two versions this replaces.
    """
    found = set()
    crossings = _crossings()
    _returns = _returned_origins(list(_sources()))
    for source, tree in _sources():
        helpers = _helpers(tree, source.name)
        returns = _returns
        for site, node in _functions(tree, source.name):
            if not node.name.startswith("_") or node.name == "__init__":
                # A private helper's parameters are internal returns of the
                # public operation that called it, already owned at entry -- so
                # revalidating them is what 4bz forbids. Its capability calls,
                # its SQL reads and its member reads are still crossings.
                #
                # A CONSTRUCTOR IS PUBLIC whatever its name. `AuthorityPort(...)`
                # is how a deployment hands this manager its capability, and an
                # inventory that skipped it because of a leading underscore
                # would be using a naming convention as a trust boundary.
                for name in _parameters(node):
                    if name not in NOT_INPUTS:
                        found.add(("caller", site, name))
            origins = _origins(node, site, returns)
            for piece in ast.walk(node):
                member = _capability_call(piece)
                if member is None:
                    member = _capability_value(piece)
                if member is not None:
                    found.add(("injected", crossings[member], member))
                table = _read_table(piece)
                if table is not None:
                    found.add(("adopted", site, table))
                read = _member_read(piece)
                if read is not None:
                    origin = _origins_of(read[0], origins)
                    if origin is not None and origin.startswith("session:"):
                        subject = _dotted(origin, read[1])
                        found.add(("injected",
                                   _crossing_of(crossings, subject), subject))
                    elif origin is not None and origin.startswith("read:"):
                        # A COLUMN THAT IS READ is a field of an adopted row,
                        # and the row's crossing is where it belongs.
                        where, table = origin[len("read:"):].split("|", 1)
                        found.add(("adopted", where,
                                   _dotted_read(table, read[1])))
                    elif origin is not None and origin.startswith("caller:") \
                            and not node.name.startswith("_"):
                        found.add(("caller", site,
                                   _dotted_read(origin[len("caller:"):],
                                                read[1])))
            # ONE LEVEL INTO THIS MODULE'S OWN HELPERS. A crossing's members are
            # often read by a private helper the crossing hands the whole
            # document to -- `_assignment` owns three members of a claim answer
            # -- and an inventory that stopped at the call would report the
            # crossing owned and its members invisible. The entry stays at the
            # CALLER's site, because that is where the value entered.
            found |= _through_helpers(crossings, site, node, origins,
                                      helpers)
    return found


def _parameters(node):
    """Every parameter, INCLUDING the variadic forms.

    Review [P1]: this enumerated positional and keyword-only arguments only, so
    nine public constructors taking `**members` were absent from an inventory
    that claimed to hold every public parameter. A universe that names its own
    shape and then omits two of Python's four is not a universe.
    """
    arguments = node.args
    names = [argument.arg for argument in
             arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
    # By their bare names: what was missing was the FORM, not a spelling. A
    # variadic parameter is a receiver input like any other, and nothing else in
    # this package shares one of their names.
    if arguments.vararg is not None:
        names.append(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.append(arguments.kwarg.arg)
    return names


def _dotted_read(table, member):
    """`operations[refusal]` + `category` -> `operations.refusal.category`."""
    return (table.replace("][", ".").replace("[", ".").rstrip("]")
            + "." + member)


def _dotted(origin, member):
    """`session:claim[result]` + `generation` -> `claim.result.generation`."""
    stem = origin[len("session:"):].replace("][", ".").replace("[", ".")
    return stem.rstrip("]") + "." + member


def _origins_of(node, origins):
    """`_source` with no site and no helper returns: for resolving arguments."""
    return _source(node, origins)


def columns_read():
    """Every persisted column name this package reads, found WITHOUT tracking.

    A SECOND MECHANISM, on purpose. The adopted member universe is computed by
    following origins, and the probes for those members are generated from the
    same universe -- so a change that stopped the tracking seeing columns would
    quietly shrink both sides and no gate would notice. This one is a flat scan
    for `x["<name>"]` where the name is a column of a table this build owns, and
    it is compared against what the tracking found.

    Coarse by design: it cannot say WHICH table, only that a column of that name
    is read. That is enough to catch a universe that has stopped seeing columns
    at all, which is the failure it exists for.
    """
    known = set(schema.OFFER_COLUMNS) | set(schema.OPERATION_COLUMNS)
    found = set()
    for _, tree in _sources():
        for piece in ast.walk(tree):
            read = _member_read(piece)
            if read is not None and read[1] in known:
                found.add(read[1])
    return found


def _crossing_of(crossings, subject):
    """Which crossing a member subject belongs to.

    A qualified capability's member is two segments (`agent.cancel`) and the
    session's is one (`claim`), so the longer key is tried first -- a member
    entry belongs to the crossing whose name it extends, not to the first
    segment that happens to match.
    """
    parts = subject.split(".")
    for take in (2, 1):
        key = ".".join(parts[:take])
        if key in crossings:
            return crossings[key]
    raise AssertionError(f"{subject} belongs to no crossing")


def _crossings():
    """capability member -> the ONE lexical site where it crosses.

    An injected value enters this package once, and the entry belongs where it
    entered. `issue_offer` reads five members of a Work projection the PORT
    obtained, and those are the port's crossing seen from further in -- not five
    more crossings. Keying them to the crossing is what makes "one entry, one
    owner, one probe" mean the same thing in all three domains.
    """
    found = {}
    for source, tree in _sources():
        for site, node in _functions(tree, source.name):
            for piece in ast.walk(node):
                member = _capability_call(piece)
                if member is None:
                    member = _capability_value(piece)
                if member is None:
                    continue
                if found.setdefault(member, site) != site:
                    raise AssertionError(
                        f"{member} crosses at {found[member]} and at {site}; a "
                        f"capability with two crossings has two owners")
    return found


def _helpers(tree, module):
    """This module's own private functions, by name, with their lexical sites."""
    found = {}
    for site, node in _functions(tree, module):
        if node.name.startswith("_"):
            found[node.name] = (site, node)
    return found


def _through_helpers(crossings, site, node, origins, helpers):
    """Member reads a private helper performs on a document handed to it."""
    found = set()
    for piece in ast.walk(node):
        if not isinstance(piece, ast.Call):
            continue
        called = piece.func
        name = (called.attr if isinstance(called, ast.Attribute)
                else getattr(called, "id", None))
        entry = helpers.get(name)
        if entry is None or entry[1] is node:
            continue
        helper = entry[1]
        parameters = _parameters(helper)
        if isinstance(called, ast.Attribute):
            parameters = parameters[1:]          # `self`
        for position, argument in enumerate(piece.args):
            origin = _origins_of(argument, origins)
            if origin is None or position >= len(parameters):
                continue
            inside = _origins(helper, site,
                              seed={parameters[position]: origin},
                              own_parameters=False)
            for step in ast.walk(helper):
                read = _member_read(step)
                if read is None:
                    continue
                found_origin = _origins_of(read[0], inside)
                if found_origin is None:
                    continue
                if found_origin.startswith("session:"):
                    subject = _dotted(found_origin, read[1])
                    found.add(("injected",
                               _crossing_of(crossings, subject), subject))
                elif found_origin.startswith("caller:") \
                        and not node.name.startswith("_"):
                    found.add(("caller", site,
                               _dotted_read(found_origin[len("caller:"):],
                                            read[1])))
    return found


def owning_validators():
    """site -> {(kind, label, subject)} for every boundary call in the package.

    The subject is resolved through the function's own bindings, so a row read
    into `record` and owned as `record` is attributed to the READ rather than to
    a local name nobody outside the function can see.

    AND ONE LEVEL INTO THIS MODULE'S HELPERS, by the same rule the universe
    uses. A crossing that hands its whole document to a private owner is still
    the crossing that owns it -- and a shared owner is how a rule written once
    ends up applied at both of its sites rather than at one.
    """
    owners = {}
    _returns = _returned_origins(list(_sources()))
    for source, tree in _sources():
        helpers = _helpers(tree, source.name)
        returns = _returns
        for site, node in _functions(tree, source.name):
            origins = _origins(node, site, returns)
            for _, helper, inside in _delegations(node, origins, helpers):
                for found in _calls_in(helper, inside, site):
                    owners.setdefault(site, set()).add(found)
            for piece in ast.walk(node):
                if not (isinstance(piece, ast.Call)
                        and isinstance(piece.func, ast.Attribute)
                        and isinstance(piece.func.value, ast.Name)
                        and piece.func.value.id == "boundaries"
                        and piece.func.attr in boundaries.KINDS):
                    continue
                subject_at, label_at = POSITIONS.get(piece.func.attr, (0, 1))
                if len(piece.args) <= label_at:
                    raise AssertionError(f"{site}:{piece.lineno} names no label")
                label = _label(piece.args[label_at])
                if label is None:
                    raise AssertionError(
                        f"{site}:{piece.lineno} owns a boundary with no literal "
                        f"label; the inventory cannot attribute it")
                owners.setdefault(site, set()).add(
                    (piece.func.attr, label,
                     _subject(piece.args[subject_at], origins)))
    return owners


def _delegations(node, origins, helpers):
    """(helper name, its parameter bindings) for each call carrying a crossing."""
    for piece in ast.walk(node):
        if not isinstance(piece, ast.Call):
            continue
        called = piece.func
        name = (called.attr if isinstance(called, ast.Attribute)
                else getattr(called, "id", None))
        found = helpers.get(name)
        if found is None or found[1] is node:
            continue
        where, helper = found
        parameters = _parameters(helper)
        if isinstance(called, ast.Attribute):
            parameters = parameters[1:]
        inside = {}
        for position, argument in enumerate(piece.args):
            origin = _origins_of(argument, origins)
            if origin is not None and position < len(parameters):
                inside[parameters[position]] = origin
        if inside:
            yield (where, helper,
                   _origins(helper, where, seed=inside, own_parameters=False))


def propagated_owners():
    """(helper site, kind, label) for every owner attributed to a caller.

    A shared owner is written once and attributed to each crossing that reaches
    it, so its own site holds calls whose subject is a bare parameter. Those are
    not orphans -- they are the same calls, seen where they were written.
    """
    found = set()
    _returns = _returned_origins(list(_sources()))
    for source, tree in _sources():
        helpers = _helpers(tree, source.name)
        returns = _returns
        for site, node in _functions(tree, source.name):
            origins = _origins(node, site, returns)
            for where, helper, inside in _delegations(node, origins, helpers):
                for kind, label, _ in _calls_in(helper, inside, site):
                    found.add((where, kind, label))
    return found


def _calls_in(node, origins, site):
    """The boundary calls a function makes, resolved through given bindings."""
    for piece in ast.walk(node):
        if not (isinstance(piece, ast.Call)
                and isinstance(piece.func, ast.Attribute)
                and isinstance(piece.func.value, ast.Name)
                and piece.func.value.id == "boundaries"
                and piece.func.attr in boundaries.KINDS):
            continue
        subject_at, label_at = POSITIONS.get(piece.func.attr, (0, 1))
        label = _label(piece.args[label_at])
        if label is None:
            raise AssertionError(f"{site}:{piece.lineno} names no label")
        subject = _subject(piece.args[subject_at], origins)
        if subject.startswith("session:") or subject.startswith("read:"):
            yield (piece.func.attr, label, subject)


def _label(node):
    """The literal text of a boundary's label, or None.

    A shared owner that serves two crossings takes the CALLER's noun and builds
    its labels from it -- `f"{what}'s generation"` -- so the label carries which
    crossing it came from while the distinguishing text stays literal in the
    source. The literal part is what an inventory can attribute and what a probe
    can assert; a label with no literal part at all still cannot be either.
    """
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value
    if isinstance(node, ast.JoinedStr):
        literal = "".join(piece.value for piece in node.values
                          if isinstance(piece, ast.Constant)
                          and type(piece.value) is str)
        return literal or None
    return None


def _subject(node, origins):
    """What a boundary call is owning, named so an entry can claim it.

    ONE derivation, shared with the universe's. `_source` already knows every
    shape a crossing can be written in, and a subject resolver that knew fewer
    would report an owner as an orphan for a spelling the discovery accepts.
    """
    found = _source(node, origins)
    if found is not None:
        return found
    bound = _capability_value(node)
    if bound is not None:
        return f"session:{bound}"
    if isinstance(node, ast.Name):
        return origins.get(node.id, node.id)
    read = _member_read(node)
    if read is not None:
        return f"{_subject(read[0], origins)}[{read[1]}]"
    if isinstance(node, ast.Subscript):
        return _subject(node.value, origins) + "[]"
    if isinstance(node, ast.Attribute):
        return _subject(node.value, origins) + "."
    if isinstance(node, ast.Call):
        member = _capability_call(node)
        if member is not None:
            return f"session:{member}"
    return "?"


def _claims(entry):
    """The subject an entry answers to, in the form owners are written in."""
    domain, _, subject = entry
    parts = subject.split(".")
    if domain == "injected":
        # THE CROSSING'S OWN NAME IS THE HEAD, however many dots it has. A
        # qualified capability's member is two segments, and splitting on the
        # first dot would make `adapter.list` read as a member `list` of a
        # crossing `adapter` that does not exist.
        known = _crossings()
        head = 2 if ".".join(parts[:2]) in known else 1
        parts = [".".join(parts[:head])] + parts[head:]
        stem = "session:" + parts[0]
    elif domain == "adopted":
        stem = f"read:{entry[1]}|" + parts[0]
    else:
        stem = "caller:" + parts[0]
    return stem + "".join(f"[{p}]" for p in parts[1:])


def _owned_here(site, stem, covering=False):
    """Labels owned at `site` for `stem`.

    EXACT FIRST, and a parent never claims its members' labels. Each member of a
    structured value is its own entry, so an ancestor that also answered for
    them would report the members owned and demand one probe prove five things.

    COVERING IS THE FALLBACK, and only where an owner genuinely owns the whole:
    `boundaries.row` owns a table's columns by contract and `boundaries.sealed`
    owns a seal's members, so a member with no owner of its own is owned by
    theirs. A member that HAS one is answered by it.
    """
    owners = owning_validators().get(site, ())
    exact = {label for _, label, subject in owners
             if subject == stem or subject.startswith(stem + ".")}
    if exact or not covering:
        return sorted(exact)
    # BOTH DIRECTIONS, and only as a fallback. A member with no owner of its own
    # is owned by the owner of the whole (`row` owns a table's columns by
    # contract; `sealed` owns a seal's members). A READ with no owner of its own
    # is owned by whatever owns what comes out of it -- the `meta` table is read
    # for two values and it is those two that are owned.
    return sorted({label for _, label, subject in owners
                   if stem.startswith(subject + "[")
                   or subject.startswith(stem + "[")})


def layer_labels(entry):
    """Every label the boundary layer owns THIS entry under, at its own site."""
    return _owned_here(entry[1], _claims(entry),
                       covering=entry[0] != "injected")


# Boundary calls whose subject is not a receiving entry, each with its reason.
# Checked for staleness, because a list of exceptions nobody compares to the
# code is a list of things somebody remembered.
NOT_AN_ENTRY = {
    ("store.py:seal_refusal", "text", "a sealed refusal"):
        "the composed seal is this build's own value on its way INTO SQLite -- "
        "a write boundary rather than a receiving one",
    ("store.py:revive_refusal", "sealed", "a sealed refusal"):
        "chained onto the adopted decode of the same entry: two properties of "
        "one crossing, like the grammar and the calendar of an instant",
    ("offers.py:accept_offer", "deadline", "the settlement deadline"):
        "the settlement window is this build's own constant; what a deadline "
        "owns from a caller is the duration, and here there is no caller",
}

# Entries owned by a rule that is NOT the boundary layer, each naming the rule.
# Every one still needs a witness: a declared owner with nothing exercising it
# is a claim, not a boundary.
STATED_OWNERS = {
    # -- the port forwards, and the authority owns its own operands ----------
    ("caller", "authority_port.py:AuthorityPort.project_work", "work_id"):
        "forwarded to the authority's projection, which owns its own operands",
    ("caller", "authority_port.py:AuthorityPort.slot_holder", "participant"):
        "the same",
    ("caller", "authority_port.py:AuthorityPort.claim", "work_id"):
        "forwarded to the authority's claim",
    ("caller", "authority_port.py:AuthorityPort.claim", "operation_id"):
        "the same",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "operation_id"): "forwarded to the authority's settlement",
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "signature"):
        "the same",
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "reason"):
        "the same",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "disposition"): "the same",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "may_retire"):
        "the same: settlement authority is asserted at the authority, which "
        "defaults it to false",
    ("caller", "authority_port.py:AuthorityPort.claim_signature", "work_id"):
        "forwarded to the authority's own derivation",
    ("caller", "authority_port.py:AuthorityPort.claim_signature",
     "participant"): "the same",
    # -- outbound: 4bz leaves the values to the next receiver ----------------
    ("caller", "documents.py:offer_bearer", "issued"):
        "an outbound constructor receives this build's own values; the "
        "contract owns the SHAPE and the far end owns the values",
    ("caller", "documents.py:offer_bearer", "bearer"): "the same",
    # -- rules that are not shapes -------------------------------------------
    ("caller", "offers.py:claim_operation_id", "offer_id"):
        "a pure derivation over already-owned values; its answer is proved "
        "where it is stored",
    ("caller", "offers.py:claim_operation_id", "intent_digest"): "the same",
    ("caller", "offers.py:issue_offer", "participant"):
        "compared against the session's binding, which is the only identity a "
        "claim can be taken as",
    ("caller", "offers.py:accept_offer", "decision"):
        "a closed set: accept or decline, refused/precondition otherwise",
    ("caller", "offers.py:accept_offer", "bearer"):
        "possession, by constant-time comparison against the stored verifier",
    ("caller", "offers.py:accept_offer", "work_ref"):
        "compared against the offer's own Work and authority",
    ("caller", "offers.py:accept_offer", "work_ref.work_id"):
        "compared against the offer's own Work: a decision naming another one "
        "is not this authorization's decision, whatever shape it has",
    ("caller", "offers.py:accept_offer", "work_ref.authority_uuid"):
        "the same comparison, for the authority the offer was issued from",
    ("caller", "offers.py:accept_offer", "runtime_attempt_id"):
        "compared against the offer's own attempt",
    ("caller", "offers.py:accept_offer", "reason"):
        "prose recorded beside a decline; it rides the settlement's manager "
        "signature, and canonicalization refuses what a durable document "
        "cannot carry",
    ("caller", "offers.py:settle_claim", "refused_evidence"):
        "forwarded to the authority's settlement as its reason, and the "
        "authority owns its own operands",
    # W6631: the port forwards, and the deployment's repository owns its own
    # operands -- the same shape `AuthorityPort` uses. What comes BACK is owned
    # at `_resolved`, because that is a value arriving FROM the injected domain
    # rather than one leaving for it.
    ("caller", "workspaces.py:GitPort.resolve", "uri"):
        "forwarded to the deployment's repository, which owns its own operands",
    ("caller", "workspaces.py:GitPort.resolve", "ref"): "the same",
    ("caller", "workspaces.py:GitPort.checkout", "uri"): "the same",
    ("caller", "workspaces.py:GitPort.checkout", "revision"):
        "the same, and already owned as a pinned base revision before this "
        "port is reached",
    ("caller", "workspaces.py:GitPort.checkout", "into"):
        "a directory THIS component created under a root it owns; the port "
        "hands out a place rather than accepting one",
    ("caller", "workspaces.py:GitPort.checkout", "git_dir"): "the same",
    ("caller", "workspaces.py:materialize_git_source", "git"):
        "typed at GitPort construction, where each operation it must carry is "
        "proved callable before a delivery can spend anything on one missing",
    # DIAGNOSED, not assumed: these two are owned by the FROZEN gitSource
    # FRAGMENT, which item 2's correction put ahead of every member read. A
    # malformed revision refuses with "'base_revision'.'hex' breaks pattern"
    # before `_pinned` is reached, so delegating them there named an owner that
    # never sees them.
    ("caller", "workspaces.py:materialize_git_source",
     "base_revision.algorithm"):
        "the frozen gitSource fragment, which types the revision as a "
        "gitObject before any member of the source is read",
    ("caller", "workspaces.py:materialize_git_source", "base_revision.hex"):
        "the same fragment, same reason",
    # W7079 [P1]: the PUBLIC sealing door owns its operand BEFORE reading a
    # member. The message sub-boundary that used to sit inside it became
    # unreachable when `ContractRefusal` began owning its own message at
    # construction; removing it left the ENCLOSING input unowned, and an object
    # with a hostile `__getattribute__` ran caller behaviour on the way to
    # `.category`. Typed by IDENTITY rather than `isinstance`, because a
    # subclass can override attribute access and that is the thing refused.
    ("caller", "store.py:seal_refusal", "refusal"):
        "identity against this build's own ContractRefusal, before any member "
        "is read",
    ("caller", "store.py:manager_signature", "operands"):
        "canonicalized, which refuses every value this contract cannot carry",
    ("caller", "store.py:ControlStore.open", "path"):
        "owned at the head of open with its OWN closed pair: a path this build "
        "must not touch is integrity/path, not a schema fault",
    ("caller", "store.py:ControlStore.open", "incarnation"):
        "owned at the head of open, before the file is touched",
    ("caller", "store.py:ControlStore.replay", "signature"):
        "compared against the journalled row: a recorded identity with other "
        "operands is an operation collision, which changes nothing (§4.2)",
    ("caller", "store.py:ControlStore.replay", "kind"):
        "the same comparison; the kind is inside the signature, so both are "
        "checked against what was recorded rather than against a rule",
    # -- capability OPERANDS: typed where they are constructed ---------------
    #
    # Review [P1]: these were removed from the universe on the grounds that each
    # is owned at its constructor, and two of them were owned nowhere. An
    # exception has to point at a constructor that EXISTS and owns it, so each
    # of these names one and CONSTRUCTED_BY is checked against the code.
    ("caller", "authority_port.py:AuthorityPort.__init__", "session"):
        "each of the four operations it must carry is typed at construction, "
        "before an offer can spend anything on one that is missing",
    ("caller", "store.py:ControlStore.__init__", "connection"):
        "the handle is assembled by ControlStore.open, which decides the "
        "database and closes it on every refused path",
    ("caller", "store.py:ControlStore.__init__", "incarnation"):
        "owned by ControlStore.open before the handle exists",
    ("caller", "store.py:ControlStore.__init__", "clock"):
        "typed by ControlStore.open as the capability it is",
    # -- outbound constructors: the contract table owns the member set --------
    ("caller", "documents.py:profile_certified", "members"):
        "documents.py:_emit, against this document's entry in CONTRACTS",
    ("caller", "documents.py:offer_issued", "members"): "the same",
    ("caller", "documents.py:offer_settled", "members"): "the same",
    ("caller", "documents.py:offer_settled_by_another", "members"):
        "the same",
    ("caller", "documents.py:offer_accepted", "members"): "the same",
    ("caller", "documents.py:claim_recorded", "members"): "the same",
    ("caller", "documents.py:settlement_observed", "members"): "the same",
    ("caller", "documents.py:recoverable_offer", "members"): "the same",
    ("caller", "documents.py:recovery_report", "members"): "the same",
    ("caller", "documents.py:agent_session_certified", "members"): "the same",
    ("caller", "documents.py:acp_negotiated", "members"): "the same",
    # -- W6592 cut A: §2.2, whose refusal is the CALLER'S rather than the
    # layer's -------------------------------------------------------------
    #
    # These are owned, and deliberately not by `boundaries`. §2.2's answer is
    # `policy.denied` -- this manager DECLINING TO ADVERTISE -- and the layer's
    # own pair is `integrity.schema`, which would say the relay sent something
    # malformed. So the exact-record verdict is taken from the POD primitive
    # and this boundary supplies the closed pair, which is what a caller-local
    # taxonomy is. The rule is exact in both directions: no member missing and
    # none extra, `terminal` identically false, `fs` empty.
    ("caller", "handshake.py:check_client_capabilities", "advertised"):
        "handshake.py:_denies, which asks the POD primitive for the "
        "exact-record verdict and raises §2.2's own policy/denied pair",
    ("caller", "handshake.py:check_client_capabilities", "advertised.fs"):
        "the same rule, applied again to the inner document: an fs member "
        "present AT ALL, even set false, is one ACP's optional type did not "
        "have to carry",
    ("caller", "handshake.py:check_client_capabilities", "advertised.terminal"):
        "compared identically against false, after the envelope is proved; a "
        "falsey value is not the constant §2.2 sends",
    ("caller", "handshake.py:negotiate_acp", "agent_protocol_version"):
        "compared against the profile's own pinned version: an answer is an "
        "announcement rather than a negotiation, and there is no downgrade",
    ("caller", "handshake.py:negotiate_acp", "agent_session_capabilities"):
        "handshake.py:_offered, which OWNS it as an exact built-in list "
        "before walking it: a generator that yields the six the first time "
        "and nothing the second would otherwise pass a handshake and then "
        "fail every one of them",

    # -- the settlement's Work, and the projection members that are COMPARED --
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "work_id"):
        "the comparison operand for a committed claim's identity; it comes "
        "from an offer row this build already adopted",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "authority_uuid"):
        "the same: the authority frozen on the offer, and the operand a "
        "committed claim's own authority is compared against",
    ("caller", "authority_port.py:AuthorityPort.claim", "authority_uuid"):
        "the authority frozen on the offer, compared against the claim "
        "answer's own; it comes from an offer row this build already adopted",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.status"):
        "compared in issue_offer against the one state an offer may be issued "
        "against; every other value refuses",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.phase"): "the same comparison",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.handler"):
        "the same: an offer is issued only against unclaimed Work, so anything "
        "other than absence refuses",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.gate"): "the same, for ungated Work",
    ("injected", "authority_port.py:AuthorityPort.settle_operation",
     "settle_operation.kind"):
        "the discriminator, owned by the closed variant set that reads it: "
        "`alternative` refuses a kind outside the four",
    # -- cut D ---------------------------------------------------------------
    ("caller", "attempts.py:observe", "axis"):
        "a closed set: the frozen runtime-attempt axes, refused otherwise",
    # -- cut D, second slice -------------------------------------------------
    ("caller", "authority_port.py:AuthorityPort.cancel", "expect"):
        "the assignment this manager already fixed and adopted; forwarded to "
        "the authority, which owns its own operands",
    ("caller", "authority_port.py:AuthorityPort.cancel", "operation_id"):
        "the derived authority identity, forwarded to the authority",
    ("caller", "authority_port.py:AuthorityPort.cancel", "reason"):
        "prose forwarded to the authority, which owns its own operands",
    ("caller", "authority_port.py:AuthorityPort.cancel", "work_id"):
        "the comparison operand for the fenced assignment's own Work",
    ("caller", "authority_port.py:AuthorityPort.cancel", "authority_uuid"):
        "the same, for the authority the assignment belongs to",
    ("injected", "authority_port.py:AuthorityPort.cancel", "cancel.fenced"):
        "a closed value: the authority either fenced the generation or this "
        "cancellation may not proceed, and anything but true refuses",
    ("injected", "attempts.py:_order_quiescence", "agent.cancel"):
        "passed through UNINTERPRETED: reaching a boundary is not evidence of "
        "its effect, and the manager has no basis for turning a settlement "
        "into a fact about the world. Positive quiescence arrives as an "
        "OBSERVATION or not at all",
    ("injected", "attempts.py:_order_quiescence", "adapter.stop"):
        "the same: ORDERED, not done",
    ("caller", "documents.py:runtime_labels", "members"):
        "documents.py:_emit, against this document's entry in CONTRACTS",
    ("caller", "documents.py:runtime_start_requested", "members"): "the same",
    ("caller", "documents.py:runtime_attached", "members"): "the same",
    ("caller", "documents.py:runtime_uncertain", "members"): "the same",
    ("caller", "documents.py:runtime_cancel", "members"): "the same",
    ("caller", "documents.py:cancel_intent", "members"): "the same",
    ("caller", "documents.py:quiescence_ordered", "members"): "the same",
    ("caller", "documents.py:quiescence_not_ordered", "members"): "the same",
    ("caller", "documents.py:attempt_cancelled", "members"): "the same",
    ("caller", "attempts.py:observe", "value"):
        "a closed set: the axis's own frozen vocabulary, refused otherwise",
    ("caller", "attempts.py:observe", "source.seq"):
        "a whole number counting from zero, compared against what the "
        "incarnation already recorded; the rule is the durable identity's, "
        "not a shape's",
    ("caller", "authority_port.py:AuthorityPort.assignment_of", "work_id"):
        "forwarded to the authority's projection, which owns its own operands",
    ("caller", "authority_port.py:AuthorityPort.assignment_of",
     "authority_uuid"):
        "the authority frozen on the activation, and the operand the live "
        "assignment's own authority is compared against",
    ("caller", "documents.py:work_ref", "members"):
        "documents.py:_emit, against this document's entry in CONTRACTS",
    ("caller", "documents.py:assignment", "members"): "the same",
    ("caller", "documents.py:attempt_recorded", "members"): "the same",
    ("caller", "documents.py:assignment_activated", "members"): "the same",
    ("caller", "documents.py:observation", "members"): "the same",
    ("adopted", "attempts.py:_next_source_seq", "observations"):
        "nothing to own: COALESCE(MAX(x), 0) + 1 over a STRICT INTEGER column "
        "is a whole number by construction, and the empty case is the COALESCE",
    ("adopted", "store.py:ControlStore._objects", "sqlite_master"):
        "nothing to own: SQLite's catalogue names objects with identifiers it "
        "accepted at CREATE time, and this read decides one membership question",
    # -- W6627: the agent session -------------------------------------------
    #
    # THE NINE FROZEN STATES ARE A CLOSED VOCABULARY, not a shape. `_state`
    # answers one membership question and raises the frozen pair itself, so
    # there is no boundary label for a probe to name -- it is witnessed by the
    # cases that drive each of its three callers instead.
    ("caller", "sessions.py:permits_session_transition", "from_state"):
        "sessions.py:_state, the closed §7.3 vocabulary: a membership question "
        "with the type established in the same expression",
    ("caller", "sessions.py:permits_session_transition", "to_state"):
        "the same",
    ("caller", "sessions.py:satisfies_runtime_quiescence_gate", "state"):
        "the same, and the reason the gate PROVES its argument rather than "
        "ignoring it: answering false to a malformed question is how a caller "
        "concludes it asked a good one",
    ("caller", "sessions.py:observe_session_state", "state"): "the same",
    # A BOOLEAN RULE, not a shape. §8.4 makes the turn outcome depend on this,
    # and `?? false` would turn a wrong argument into a missing one -- so it is
    # an exact `bool` and nothing else, refused in the frozen pair at the site.
    ("caller", "sessions.py:handle_transport_loss", "turn_in_flight"):
        "an exact boolean, refused where it is read: this decides an outcome "
        "and is never inferred from truthiness",
    # THE DISCRIMINATOR OF A CLOSED ALTERNATIVE. `boundaries.alternative` owns
    # the whole answer and reads this member to decide WHICH contract the rest
    # is owned against, so it is proved before any other member is read and has
    # no owner of its own to name.
    ("injected", "sessions.py:reconcile_agent_session",
     "agent.observe_session.kind"):
        "boundaries.alternative's discriminator, proved before any member of "
        "the variant it names is read",
    ("adopted", "sessions.py:_next_epoch", "agent_sessions"):
        "nothing to own: COALESCE(MAX(x), 0) + 1 over a STRICT INTEGER column "
        "is a whole number by construction, and the empty case is the COALESCE",
    # A POSITIVE EPOCH, refused by `posture_slots._epoch` and not by the layer.
    # `boundaries.generation` is the ASSIGNMENT generation's rule and counts
    # from zero; epoch zero is a session nobody allocated, and a query for one
    # answers absence in a way a caller reads as "no such session".
    ("caller", "posture_slots.py:release_slot", "session_epoch"):
        "posture_slots.py:_epoch, the frozen positiveInt: one membership "
        "question with its type established in the same expression",
    ("caller", "posture_slots.py:require_slot_recovery", "session_epoch"):
        "the same",
    ("caller", "sessions.py:adopt_provider_session", "session_epoch"):
        "the same",
    ("caller", "sessions.py:reconcile_agent_session", "session_epoch"):
        "the same",
}

# Entries owned by a helper that owns them FOR their caller. The layer owns by
# subject, and an operation that delegates keeps its own parameter name -- so
# this maps the entry to the function that owns it, and the label is read from
# THAT function rather than written down here.
# Where a capability operand's OWNER lives. The site must exist and must itself
# own what it holds, so an exception cannot name a constructor that is not there.
CONSTRUCTED_BY = {
    "store": "store.py:ControlStore.open",
    "port": "authority_port.py:AuthorityPort.__init__",
}

# Entries whose owner NO WRITER CAN DRIVE, each with its reason. A column
# declared INTEGER in a STRICT table cannot hold anything that is not a whole
# number, so the `count` rule over it is a boundary a probe would have to fake.
# Written down rather than skipped silently: an entry with no probe should be a
# decision somebody made, and it is checked to be a real, owned entry.
NO_PROBE = {
    ("adopted", "offers.py:_offers", "offers.claim_generation"):
        "a STRICT INTEGER column; SQLite refuses the value a probe would need",
    ("adopted", "posture_slots.py:_slot_row", "posture_slots.session_epoch"):
        "the same: a session epoch column SQLite will not let a writer spoil",
    ("adopted", "sessions.py:_session_row", "agent_sessions.session_epoch"):
        "the same",
    ("adopted", "attempts.py:_attempts", "attempts.assignment_generation"):
        "the same: a generation column SQLite will not let a writer spoil",
}

DELEGATED = {
    # -- W6627: the agent session -------------------------------------------
    #
    # THREE SHARED OWNERS, each written once. `_posture`, `_epoch` and
    # `_evidence` are the same question wherever it is asked, and a local copy
    # of a question is how two sites come to disagree about one string -- which
    # is the defect the frozen host recorded when a posture was "a nonempty
    # string" at one boundary and one of two at another.
    ("caller", "posture_slots.py:posture_slot", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "posture_slots.py:release_slot", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "posture_slots.py:require_slot_recovery", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "sessions.py:open_agent_session", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "sessions.py:adopt_provider_session", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "sessions.py:reconcile_agent_session", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "posture_slots.py:release_slot", "evidence"):
        ("posture_slots.py:_evidence", "caller:evidence"),
    # The two public slot movements are thin wrappers around the `_in`
    # composition helpers -- one transaction each -- and the helper is where
    # every operand is owned, because an act that also runs inside somebody
    # else's transaction must own its operands in the one place both paths
    # reach.
    ("caller", "posture_slots.py:release_slot", "attempt_id"):
        ("posture_slots.py:_release_slot_in", "caller:attempt_id"),
    ("caller", "posture_slots.py:release_slot", "reason"):
        ("posture_slots.py:_release_slot_in", "caller:reason"),
    ("caller", "posture_slots.py:release_slot", "observed_identity"):
        ("posture_slots.py:_release_slot_in", "caller:observed_identity"),
    ("caller", "posture_slots.py:require_slot_recovery", "attempt_id"):
        ("posture_slots.py:_require_slot_recovery_in", "caller:attempt_id"),
    ("caller", "posture_slots.py:require_slot_recovery", "reason"):
        ("posture_slots.py:_require_slot_recovery_in", "caller:reason"),
    # THE §3.1 REFERENCE, owned whole and member by member in one place. All
    # four components label evidence, and a boundary that binds three quarters
    # of one moves the row held for provider session A on a report about B.
    ("caller", "sessions.py:observe_session_state", "session_ref"):
        ("sessions.py:_session_ref", "caller:session_ref"),
    ("caller", "sessions.py:close_agent_session", "session_ref"):
        ("sessions.py:_session_ref", "caller:session_ref"),
    ("caller", "sessions.py:handle_transport_loss", "session_ref"):
        ("sessions.py:_session_ref", "caller:session_ref"),
    ("caller", "sessions.py:close_agent_session", "session_ref.posture"):
        ("sessions.py:_session_ref", "caller:session_ref[posture]"),
    ("caller", "sessions.py:close_agent_session",
     "session_ref.runtime_attempt_id"):
        ("sessions.py:_session_ref",
         "caller:session_ref[runtime_attempt_id]"),
    ("caller", "sessions.py:close_agent_session", "session_ref.session_epoch"):
        ("sessions.py:_session_ref", "caller:session_ref[session_epoch]"),
    ("caller", "sessions.py:close_agent_session",
     "session_ref.provider_session_id"):
        ("sessions.py:_session_ref",
         "caller:session_ref[provider_session_id]"),
    ("caller", "sessions.py:handle_transport_loss", "session_ref.posture"):
        ("sessions.py:_session_ref", "caller:session_ref[posture]"),
    ("caller", "sessions.py:handle_transport_loss",
     "session_ref.runtime_attempt_id"):
        ("sessions.py:_session_ref",
         "caller:session_ref[runtime_attempt_id]"),
    ("caller", "sessions.py:handle_transport_loss",
     "session_ref.session_epoch"):
        ("sessions.py:_session_ref", "caller:session_ref[session_epoch]"),
    ("caller", "sessions.py:handle_transport_loss",
     "session_ref.provider_session_id"):
        ("sessions.py:_session_ref",
         "caller:session_ref[provider_session_id]"),
    # W6631: every path this component is handed, owned in ONE place by
    # `_real` -- which refuses text a durable value cannot carry, refuses a
    # relative path, and canonicalizes, so a symlink component is resolved
    # before anything is compared.
    ("caller", "workspaces.py:directory_manifest", "root"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:assignment_workspace", "storage"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:discard_workspace", "storage"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:materialize_directory_source", "origin"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:materialize_directory_source", "inputs"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:materialize_git_source", "inputs"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:materialize_git_source", "git_metadata"):
        ("workspaces.py:_real", "caller:path"),
    # The git half at its single-owner helpers. These four subjects are NEWER
    # than the block that was lost: they appeared when the review's [P1] split
    # three owner calls out of `materialize_git_source`.
    ("caller", "workspaces.py:materialize_git_source", "found.algorithm"):
        ("workspaces.py:_resolved", "caller:found"),
    ("caller", "workspaces.py:materialize_git_source", "found.hex"):
        ("workspaces.py:_resolved", "caller:found"),
    ("caller", "offers.py:accept_offer", "offer_id"):
        ("offers.py:_offer_row", "caller:offer_id"),
    ("caller", "offers.py:submit_claim", "offer_id"):
        ("offers.py:_offer_row", "caller:offer_id"),
    ("caller", "offers.py:settle_claim", "offer_id"):
        ("offers.py:_offer_row", "caller:offer_id"),
    ("caller", "store.py:ControlStore.transact", "kind"):
        ("store.py:ControlStore._agreeing", "caller:kind"),
    ("caller", "store.py:ControlStore.transact", "signature"):
        ("store.py:ControlStore._agreeing", "caller:signature"),
    ("caller", "attempts.py:activate_assignment", "attempt_id"):
        ("attempts.py:_attempt_row", "caller:attempt_id"),
    ("caller", "attempts.py:observe", "attempt_id"):
        ("attempts.py:_attempt_row", "caller:attempt_id"),
    ("caller", "attempts.py:observe", "source"):
        ("attempts.py:_source_identity", "caller:source"),
    ("caller", "attempts.py:observe", "source.incarnation"):
        ("attempts.py:_source_identity", "caller:source[incarnation]"),
    ("caller", "attempts.py:record_attempt", "input_digest"):
        ("attempts.py:_optional", "caller:value"),
    ("caller", "attempts.py:record_attempt", "policy_digest"):
        ("attempts.py:_optional", "caller:value"),
    ("caller", "attempts.py:record_attempt", "image_digest"):
        ("attempts.py:_optional", "caller:value"),
    ("caller", "attempts.py:record_attempt", "toolchain_digest"):
        ("attempts.py:_optional", "caller:value"),
    ("caller", "attempts.py:request_cancellation", "reason"):
        ("attempts.py:_optional", "caller:value"),
    ("caller", "attempts.py:request_runtime_start", "attempt_id"):
        ("attempts.py:_attempt_row", "caller:attempt_id"),
    ("caller", "attempts.py:reconcile_runtime", "attempt_id"):
        ("attempts.py:_attempt_row", "caller:attempt_id"),
    ("caller", "attempts.py:request_cancellation", "attempt_id"):
        ("attempts.py:_attempt_row", "caller:attempt_id"),
    ("caller", "handshake.py:negotiate_acp", "profile_digest"):
        ("handshake.py:certified_agent_session_profile",
         "caller:profile_digest"),

}


def delegated_labels(entry):
    """The labels the delegate owns, read from the DELEGATE's own code."""
    site, stem = DELEGATED[entry]
    return _owned_here(site, stem)


class BoundaryCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-worker-manager-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "control.sqlite3")
        self.instants = [NOW]
        self.store = ControlStore.open(
            self.path, incarnation="manager-1", clock=lambda: self.instants[-1])
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)

    # -- preconditions, so a probe reaches what it aims at -------------------

    def issued(self, offer_id="offer-1"):
        worker_manager.issue_offer(
            self.store, self.port, offer_id=offer_id, work_id=WORK,
            runtime_attempt_id="attempt-1",
            input_digest="sha256:" + "1" * 64,
            policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE,
            profile_name="reference", mint_bearer=lambda: "bearer-1")
        return offer_id

    def accepted(self, offer_id="offer-1"):
        self.issued(offer_id)
        worker_manager.accept_offer(
            self.store, self.port, offer_id=offer_id, decision="accept",
            bearer="bearer-1", now=NOW, runtime_attempt_id="attempt-1",
            work_ref={"authority_uuid": UUID, "work_id": WORK})
        return offer_id

    def claimed(self, offer_id="offer-a", attempt_id="attempt-1"):
        """An attempt with THIS attempt's own committed claim behind it.

        Activation's whole point is that a live assignment elsewhere is not
        evidence, so the precondition a probe needs is the claim itself.
        """
        self.issued(offer_id)
        worker_manager.accept_offer(
            self.store, self.port, offer_id=offer_id, decision="accept",
            bearer="bearer-1", now=NOW, runtime_attempt_id="attempt-1",
            work_ref={"authority_uuid": UUID, "work_id": WORK})
        worker_manager.record_attempt(
            self.store, attempt_id=attempt_id, adapter_name="acp",
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE)
        worker_manager.submit_claim(self.store, self.port, offer_id=offer_id)
        return attempt_id

    def living(self, answer):
        def run():
            self.claimed()
            self.session.live_assignment = answer
            worker_manager.activate_assignment(
                self.store, self.port, attempt_id="attempt-1",
                expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                        "participant": WHO, "generation": 1})
        return run

    def spoiling_attempt(self, column):
        def run():
            worker_manager.record_attempt(
                self.store, attempt_id="attempt-1", adapter_name="acp",
                adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE)
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis="consent_runtime", value="running")
        return run

    def spoiling_observation(self, column):
        def run():
            worker_manager.record_attempt(
                self.store, attempt_id="attempt-1", adapter_name="acp",
                adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE)
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis="consent_runtime", value="running",
                                   source={"incarnation": "worker", "seq": 1})
            self.corrupt(f"UPDATE observations SET {column} = ?",
                         self.SPOILED[
                             schema.OBSERVATION_COLUMNS[column].kind])
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis="consent_runtime", value="running",
                                   source={"incarnation": "worker", "seq": 1})
        return run

    # -- W6627: the agent session --------------------------------------------

    def sessioned(self, posture="execution", *, opened=True):
        """An activated attempt, a certified agent-session profile, and one
        open session -- the precondition every probe below needs to REACH the
        boundary it names rather than an earlier one."""
        self.claimed()
        worker_manager.activate_assignment(
            self.store, self.port, attempt_id="attempt-1",
            expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                    "participant": WHO, "generation": 1})
        profile = acp_profile()
        worker_manager.certify_agent_session_profile(self.store, profile)
        self.agent_profile = profile["document_digest"]
        if opened:
            worker_manager.open_agent_session(
                self.store, self.port, attempt_id="attempt-1", posture=posture,
                profile_digest=self.agent_profile, intent="open-1")
        return self.reference(posture)

    @staticmethod
    def reference(posture="execution", epoch=1, provider=None, **spoiled):
        whole = {"runtime_attempt_id": "attempt-1", "posture": posture,
                 "session_epoch": epoch, "provider_session_id": provider}
        whole.update(spoiled)
        return whole

    def opening(self, **spoiled):
        def run():
            self.sessioned(opened=False)
            operands = dict(attempt_id="attempt-1", posture="execution",
                            profile_digest=self.agent_profile,
                            intent="open-1")
            operands.update(spoiled)
            worker_manager.open_agent_session(self.store, self.port,
                                              **operands)
        return run

    def adopting(self, **spoiled):
        def run():
            self.sessioned()
            operands = dict(attempt_id="attempt-1", posture="execution",
                            session_epoch=1,
                            provider_session_id="provider-1")
            operands.update(spoiled)
            worker_manager.adopt_provider_session(self.store, **operands)
        return run

    def releasing(self, **spoiled):
        def run():
            self.sessioned()
            operands = dict(attempt_id="attempt-1", posture="execution",
                            session_epoch=1, evidence="runtime-absent",
                            observed_identity="runtime-1",
                            reason="observed absent")
            operands.update(spoiled)
            worker_manager.release_slot(self.store, **operands)
        return run

    def recovering(self, **spoiled):
        def run():
            self.sessioned()
            operands = dict(attempt_id="attempt-1", posture="execution",
                            session_epoch=1, reason="ambiguous ending")
            operands.update(spoiled)
            worker_manager.require_slot_recovery(self.store, **operands)
        return run

    def reconciling(self, **spoiled):
        def run():
            self.sessioned()
            operands = dict(attempt_id="attempt-1", posture="execution",
                            session_epoch=1)
            operands.update(spoiled)
            worker_manager.reconcile_agent_session(
                self.store, spoiled.pop("agent", _ObservingAgent()),
                **{k: v for k, v in operands.items() if k != "agent"})
        return run

    def answering(self, **answer):
        """The adapter's own ANSWER spoiled, which is the injected domain: its
        callability was proved when the capability was accepted, and what it
        returns is a separate crossing."""
        def run():
            self.sessioned()
            worker_manager.adopt_provider_session(
                self.store, attempt_id="attempt-1", posture="execution",
                session_epoch=1, provider_session_id="provider-1")
            worker_manager.reconcile_agent_session(
                self.store, _ObservingAgent(answer), attempt_id="attempt-1",
                posture="execution", session_epoch=1)
        return run

    def spoiling_session(self, column, driver="observe"):
        def run():
            reference = self.sessioned()
            self.corrupt(f"UPDATE agent_sessions SET {column} = ?",
                         self.SPOILED[
                             schema.AGENT_SESSION_COLUMNS[column].kind])
            if driver == "observe":
                worker_manager.observe_session_state(self.store, reference,
                                                     "initializing")
            elif driver == "list":
                worker_manager.agent_sessions_of(self.store, "attempt-1")
            else:
                worker_manager.release_slot(
                    self.store, attempt_id="attempt-1", posture="execution",
                    session_epoch=1, evidence="provider-session-closed",
                    reason="observed closed")
        return run

    def spoiling_slot(self, column):
        def run():
            self.sessioned()
            self.corrupt(f"UPDATE posture_slots SET {column} = ?",
                         self.SPOILED[
                             schema.POSTURE_SLOT_COLUMNS[column].kind])
            worker_manager.posture_slot(self.store, "attempt-1", "execution")
        return run

    def spoiling_attached_runtime(self):
        def run():
            self.sessioned()
            # EMPTY, not a surrogate. SQLite hands a stored surrogate back as a
            # driver fault before any owner sees it, so a probe using one would
            # prove the driver rather than the boundary -- which is what the
            # SPOILED table exists for.
            self.corrupt("UPDATE attempts SET runtime_id = ?",
                         self.SPOILED["text"])
            worker_manager.release_slot(
                self.store, attempt_id="attempt-1", posture="execution",
                session_epoch=1, evidence="runtime-absent",
                observed_identity="runtime-1", reason="observed absent")
        return run

    def spoiling_session_attempt(self, column):
        def run():
            self.sessioned(opened=False)
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.open_agent_session(
                self.store, self.port, attempt_id="attempt-1",
                posture="execution", profile_digest=self.agent_profile,
                intent="open-1")
        return run

    def session_probes(self):
        """One probe per (entry, label) W6627 added.

        Every one drives the REAL exported operation with exactly one operand
        spoiled, and `refusing` requires the refusal to name the label -- so a
        probe that is stopped by an earlier precondition fails rather than
        passing for the wrong reason.
        """
        S, P = "sessions.py", "posture_slots.py"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        return {
            # -- the caller's operands ------------------------------------
            (at(f"{P}:posture_slot", "attempt_id"), "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.posture_slot(self.store, SURROGATE,
                                                    "execution")),
            (at(f"{P}:posture_slot", "posture"), "a posture"): (
                "a posture",
                lambda: worker_manager.posture_slot(self.store, "attempt-1",
                                                    SURROGATE)),
            (at(f"{P}:release_slot", "attempt_id"), "a runtime attempt id"): (
                "a runtime attempt id", self.releasing(attempt_id=SURROGATE)),
            (at(f"{P}:release_slot", "posture"), "a posture"): (
                "a posture", self.releasing(posture=SURROGATE)),
            (at(f"{P}:release_slot", "reason"), "a slot movement reason"): (
                "a slot movement reason", self.releasing(reason=SURROGATE)),
            (at(f"{P}:release_slot", "evidence"), "slot recovery evidence"): (
                "slot recovery evidence", self.releasing(evidence=SURROGATE)),
            (at(f"{P}:release_slot", "observed_identity"),
             "the identity observed absent"): (
                "the identity observed absent",
                self.releasing(observed_identity=SURROGATE)),
            (at(f"{P}:require_slot_recovery", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id", self.recovering(attempt_id=SURROGATE)),
            (at(f"{P}:require_slot_recovery", "posture"), "a posture"): (
                "a posture", self.recovering(posture=SURROGATE)),
            (at(f"{P}:require_slot_recovery", "reason"),
             "a slot movement reason"): (
                "a slot movement reason", self.recovering(reason=SURROGATE)),
            (at(f"{S}:open_agent_session", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id", self.opening(attempt_id=SURROGATE)),
            (at(f"{S}:open_agent_session", "posture"), "a posture"): (
                "a posture", self.opening(posture=SURROGATE)),
            (at(f"{S}:open_agent_session", "profile_digest"),
             "a certified profile digest"): (
                "a certified profile digest",
                self.opening(profile_digest=SURROGATE)),
            (at(f"{S}:open_agent_session", "intent"),
             "a session opening intent"): (
                "a session opening intent", self.opening(intent=SURROGATE)),
            (at(f"{S}:adopt_provider_session", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id", self.adopting(attempt_id=SURROGATE)),
            (at(f"{S}:adopt_provider_session", "posture"), "a posture"): (
                "a posture", self.adopting(posture=SURROGATE)),
            (at(f"{S}:adopt_provider_session", "provider_session_id"),
             "a provider session id"): (
                "a provider session id",
                self.adopting(provider_session_id=SURROGATE)),
            (at(f"{S}:agent_sessions_of", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.agent_sessions_of(self.store,
                                                         SURROGATE)),
            (at(f"{S}:reconcile_agent_session", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id",
                self.reconciling(attempt_id=SURROGATE)),
            (at(f"{S}:reconcile_agent_session", "posture"), "a posture"): (
                "a posture", self.reconciling(posture=SURROGATE)),
            (at(f"{S}:reconcile_agent_session", "agent"),
             "the agent adapter's "): (
                "the agent adapter's observe_session",
                self.reconciling(agent=_HalfAnAgent())),
            (at(f"{S}:reprompt_after_transport_loss", "prompt"),
             "a prompt offered after transport loss"): (
                "a prompt offered after transport loss",
                lambda: worker_manager.reprompt_after_transport_loss(
                    SURROGATE)),
            (at(f"{S}:transport_reachability_reidentifies", "evidence"),
             "reachability evidence offered as re-identification"): (
                "reachability evidence offered as re-identification",
                lambda: worker_manager.transport_reachability_reidentifies(
                    SURROGATE)),
            (at(f"{S}:close_agent_session", "reason"),
             "a session close reason"): (
                "a session close reason",
                lambda: worker_manager.close_agent_session(
                    self.store, self.sessioned(), SURROGATE)),
            # -- the §3.1 reference, whole and member by member -------------
            (at(f"{S}:observe_session_state", "session_ref"),
             "an agent session reference"): (
                "an agent session reference",
                lambda: worker_manager.observe_session_state(
                    self.store, "not a reference", "initializing")),
            (at(f"{S}:close_agent_session", "session_ref"),
             "an agent session reference"): (
                "an agent session reference",
                lambda: worker_manager.close_agent_session(
                    self.store, "not a reference")),
            (at(f"{S}:handle_transport_loss", "session_ref"),
             "an agent session reference"): (
                "an agent session reference",
                lambda: worker_manager.handle_transport_loss(
                    self.store, "not a reference")),
            (at(f"{S}:close_agent_session", "session_ref.runtime_attempt_id"),
             "an agent session reference's runtime attempt id"): (
                "an agent session reference's runtime attempt id",
                lambda: worker_manager.close_agent_session(
                    self.store,
                    self.reference(runtime_attempt_id=""))),
            (at(f"{S}:close_agent_session",
                "session_ref.provider_session_id"),
             "an agent session reference's provider session id"): (
                "an agent session reference's provider session id",
                lambda: worker_manager.close_agent_session(
                    self.store, self.reference(provider=""))),
            (at(f"{S}:handle_transport_loss",
                "session_ref.runtime_attempt_id"),
             "an agent session reference's runtime attempt id"): (
                "an agent session reference's runtime attempt id",
                lambda: worker_manager.handle_transport_loss(
                    self.store,
                    self.reference(runtime_attempt_id=""))),
            (at(f"{S}:handle_transport_loss",
                "session_ref.provider_session_id"),
             "an agent session reference's provider session id"): (
                "an agent session reference's provider session id",
                lambda: worker_manager.handle_transport_loss(
                    self.store, self.reference(provider=""))),
            # -- what the adapter ANSWERED with ------------------------------
            (at(f"{S}:reconcile_agent_session", "agent.observe_session",
                "injected"), "an agent session observation"): (
                "an agent session observation",
                self.answering(kind="present")),
            (at(f"{S}:reconcile_agent_session",
                "agent.observe_session.state", "injected"),
             "an observed session state"): (
                "an observed session state",
                self.answering(kind="present", state="",
                               provider_session_id="provider-1")),
            (at(f"{S}:reconcile_agent_session",
                "agent.observe_session.provider_session_id", "injected"),
             "an observed provider session id"): (
                "an observed provider session id",
                self.answering(kind="absent", provider_session_id="")),
            # -- adopted rows: the store is a receiving trust domain ---------
            (at(f"{S}:_session_row", "agent_sessions", "adopted"),
             "a persisted agent session"): (
                "a persisted agent session", self.spoiling_session("state")),
            (at(f"{S}:_session_row", "agent_sessions.state", "adopted"),
             "a persisted agent session"): (
                "a persisted agent session", self.spoiling_session("state")),
            (at(f"{S}:_session_row", "agent_sessions.provider_session_id",
                "adopted"), "a persisted agent session"): (
                "a persisted agent session",
                self.spoiling_session("provider_session_id")),
            (at(f"{S}:agent_sessions_of", "agent_sessions", "adopted"),
             "a persisted agent session"): (
                "a persisted agent session",
                self.spoiling_session("state", driver="list")),
            (at(f"{P}:_prove", "agent_sessions", "adopted"),
             "a persisted agent session"): (
                "a persisted agent session",
                self.spoiling_session("state", driver="release")),
            (at(f"{P}:_prove", "agent_sessions.state", "adopted"),
             "a persisted agent session"): (
                "a persisted agent session",
                self.spoiling_session("state", driver="release")),
            (at(f"{P}:_prove", "agent_sessions.provider_session_id",
                "adopted"), "a persisted agent session"): (
                "a persisted agent session",
                self.spoiling_session("provider_session_id",
                                      driver="release")),
            (at(f"{P}:_prove", "attempts", "adopted"),
             "a persisted attached runtime id"): (
                "a persisted attached runtime id",
                self.spoiling_attached_runtime()),
            (at(f"{P}:_prove", "attempts.runtime_id", "adopted"),
             "a persisted attached runtime id"): (
                "a persisted attached runtime id",
                self.spoiling_attached_runtime()),
            (at(f"{P}:_slot_row", "posture_slots", "adopted"),
             "a persisted posture slot"): (
                "a persisted posture slot", self.spoiling_slot("occupancy")),
            (at(f"{P}:_slot_row", "posture_slots.occupancy", "adopted"),
             "a persisted posture slot"): (
                "a persisted posture slot", self.spoiling_slot("occupancy")),
            (at(f"{P}:_slot_row", "posture_slots.reason", "adopted"),
             "a persisted posture slot"): (
                "a persisted posture slot", self.spoiling_slot("reason")),
            (at(f"{P}:_slot_row", "posture_slots.changed_at", "adopted"),
             "a persisted posture slot"): (
                "a persisted posture slot", self.spoiling_slot("changed_at")),
            (at(f"{S}:_attempt", "attempts", "adopted"),
             "a persisted attempt"): (
                "a persisted attempt",
                self.spoiling_session_attempt("work_id")),
            (at(f"{S}:_attempt", "attempts.work_id", "adopted"),
             "a persisted attempt"): (
                "a persisted attempt",
                self.spoiling_session_attempt("work_id")),
            (at(f"{S}:_attempt", "attempts.authority_uuid", "adopted"),
             "a persisted attempt"): (
                "a persisted attempt",
                self.spoiling_session_attempt("authority_uuid")),
        }

    def corrupt(self, statement, *operands):
        """Change persisted bytes behind this build's back.

        Which is the point: adopted data is data THIS process did not write, and
        a probe that wrote it through the manager's own owned path would be
        testing the writer instead of the reader.
        """
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            # A CHECK constraint binds THIS build's writers. Adopted data is by
            # definition data this process did not write, and a repair tool, a
            # restore or another build is exactly the case a column contract
            # exists for -- so the probe writes what SQLite would refuse from us.
            beside.execute("PRAGMA ignore_check_constraints = ON")
            beside.execute(statement, operands)
        finally:
            beside.close()

    def refusing(self, label, run):
        """Run `run` and require the refusal that NAMES `label`.

        The label is how a probe proves it arrived. Anything else -- including a
        perfectly good refusal from an earlier precondition -- is a vacuous
        probe.
        """
        try:
            run()
        except ContractRefusal as refusal:
            # THE LABEL FIRST. A refusal from an earlier precondition carries a
            # different closed pair, and asserting the pair first would fail
            # with "refused != integrity" -- true, and not the thing that went
            # wrong.
            self.assertIn(label, refusal.message,
                          f"refused, but not at {label!r}: {refusal.message}")
            self.assertEqual(refusal.category, "integrity")
            self.assertEqual(refusal.code, "schema")
            return
        except BaseException as failure:
            self.fail(f"{label}: escaped as {type(failure).__name__}: {failure}")
        self.fail(f"{label}: accepted")

    # -- the table: one probe per (entry, label) -----------------------------

    def offering(self, offer_id="offer-x", **spoiled):
        operands = dict(work_id=WORK, runtime_attempt_id="attempt-1",
                        input_digest="d", policy_digest="d",
                        profile_digest=PROFILE, profile_name="reference",
                        mint_bearer=lambda: "bearer-1")
        operands.update(spoiled)
        return lambda: worker_manager.issue_offer(
            self.store, self.port, offer_id=offer_id, **operands)

    SPOILED = {"text": "", "identity": "", "json": "", "refusal": "",
               "instant": "not-an-instant", "flag": 2}

    def owned_by_sqlite(self, contract):
        """A column whose whole contract is its STRICT declared type.

        A `count` column is INTEGER STRICT, so nothing that is not a whole
        number can reach the read, and a probe for it would be a probe for a
        boundary no writer can drive. Named here rather than skipped silently:
        a column with no probe should be a decision somebody made.
        """
        return contract.kind == "count"

    def column_probes(self):
        """One probe per adopted COLUMN that this build reads.

        Derived from the table contracts rather than listed, because a column
        added to a contract and never spoiled is exactly the gap this file keeps
        being corrected for. Each spoils ITS OWN column and drives a read.
        """
        entries = receiving_entries()
        found = {}
        for name in sorted(schema.OFFER_COLUMNS):
            entry = ("adopted", "offers.py:_offers", f"offers.{name}")
            if entry in entries and not self.owned_by_sqlite(
                    schema.OFFER_COLUMNS[name]):
                found[(entry, "a persisted offer")] = (
                    "a persisted offer", self.spoiling_offer(name))
        for name in sorted(schema.OPERATION_COLUMNS):
            entry = ("adopted", "store.py:ControlStore._operation_row",
                     f"operations.{name}")
            if entry in entries and not self.owned_by_sqlite(
                    schema.OPERATION_COLUMNS[name]):
                found[(entry, "a persisted operation")] = (
                    "a persisted operation", self.spoiling_operation(name))
        return found

    def spoiling_offer(self, column):
        def run():
            self.accepted("offer-c")
            self.corrupt(f"UPDATE offers SET {column} = ?",
                         self.SPOILED[schema.OFFER_COLUMNS[column].kind])
            if column in ("offer_id", "state"):
                # The lookup finds a row BY its identity and recovery finds one
                # by its state, so each of those two needs the other's driver.
                worker_manager.recover_on_restart(self.store, now=NOW) \
                    if column == "offer_id" else \
                    worker_manager.submit_claim(self.store, self.port,
                                                offer_id="offer-c")
            else:
                worker_manager.submit_claim(self.store, self.port,
                                            offer_id="offer-c")
        return run

    def spoiling_operation(self, column):
        def run():
            operation = "profile.certify:runtime:reference"
            if column == "refusal":
                # A committed row carries no refusal, so this one needs a
                # DURABLE refusal to have been sealed first.
                operation = "op-sealed"
                try:
                    self.store.transact(
                        operation, "k",
                        worker_manager.manager_signature("k", {}),
                        lambda connection: (_ for _ in ()).throw(
                            ContractRefusal("policy", "retention", "held",
                                            durable=True)))
                except ContractRefusal:
                    pass
                self.corrupt(
                    "UPDATE operations SET refusal = ? WHERE operation_id = ?",
                    '{"category": 7, "code": "retention", "message": "m",'
                    ' "durable": true}', operation)
            else:
                self.corrupt(
                    f"UPDATE operations SET {column} = ? "
                    f"WHERE operation_id = ?",
                    self.SPOILED[schema.OPERATION_COLUMNS[column].kind],
                    operation)
            self.store.operation_record(operation)
        return run

    def recorded(self, attempt_id="attempt-1", **spoiled):
        operands = dict(adapter_name="acp", adapter_digest="sha256:" + "a" * 64,
                        profile_digest=PROFILE)
        operands.update(spoiled)
        return lambda: worker_manager.record_attempt(
            self.store, attempt_id=attempt_id, **operands)

    def activated(self, attempt_id="attempt-1", **spoiled):
        """An attempt with a claim behind it, activated with a spoiled expect.

        The preconditions are real: without the claimed offer the activation
        refuses before it reaches the operand this probe is aimed at.
        """
        expect = {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": WHO, "generation": 1}
        for member, value in spoiled.items():
            if member == "whole":
                expect = value
            elif member.startswith("work_ref."):
                expect["work_ref"][member.split(".", 1)[1]] = value
            else:
                expect[member] = value

        def run():
            self.claimed("offer-a", attempt_id)
            worker_manager.activate_assignment(self.store, self.port,
                                               attempt_id=attempt_id,
                                               expect=expect)
        return run

    def bound_attempt(self, attempt_id="attempt-1"):
        """An attempt bound to its assignment: the precondition the runtime
        slice starts from."""
        self.claimed("offer-a", attempt_id)
        worker_manager.activate_assignment(
            self.store, self.port, attempt_id=attempt_id,
            expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                    "participant": WHO, "generation": 1})
        return attempt_id

    def attached(self, attempt_id="attempt-1", runtime_id="runtime-1"):
        self.bound_attempt(attempt_id)
        worker_manager.request_runtime_start(
            self.store, FakeAdapter(self, runtime_id), attempt_id=attempt_id)
        return attempt_id

    def starting(self, answer):
        """An adapter whose START answer is whatever this probe needs."""
        def run():
            self.bound_attempt()
            adapter = FakeAdapter(self)
            adapter.start = lambda operands: answer
            worker_manager.request_runtime_start(self.store, adapter,
                                                 attempt_id="attempt-1")
        return run

    def listing(self, answer):
        """An adapter whose LISTING is whatever this probe needs."""
        def run():
            self.bound_attempt()
            adapter = FakeAdapter(self)
            adapter.list = lambda operands: answer
            worker_manager.reconcile_runtime(self.store, adapter,
                                             attempt_id="attempt-1")
        return run

    def fencing(self, **spoiled):
        def run():
            self.attached()
            answer = dict(self.session.fence_answer)
            for member, value in spoiled.items():
                if member == "whole":
                    answer = value
                elif member.startswith("assignment."):
                    answer["assignment"] = dict(
                        answer["assignment"],
                        **{member.split(".", 1)[1]: value})
                elif member.startswith("work_ref."):
                    answer["assignment"] = dict(answer["assignment"])
                    answer["assignment"]["work_ref"] = dict(
                        answer["assignment"]["work_ref"],
                        **{member.split(".", 1)[1]: value})
                else:
                    answer[member] = value
            self.session.fence_answer = answer
            worker_manager.request_cancellation(
                self.store, self.port, FakeAgent(), FakeAdapter(self),
                attempt_id="attempt-1")
        return run

    def materializing(self, **overrides):
        """One directory delivery, with one operand spoiled."""
        def run():
            storage = os.path.join(self.root, "probe-storage")
            os.makedirs(storage, exist_ok=True)
            roots = workspaces.assignment_workspace(storage, "a-probe")
            origin = os.path.join(self.root, "probe-origin")
            os.makedirs(origin, exist_ok=True)
            # A DESTINATION THIS DELIVERY HAS NOT USED. Diagnosed: the helper
            # reused one name, so the second probe refused with "already
            # delivered" before its spoiled operand was read -- a probe that
            # fails for an earlier reason proves the earlier reason.
            call = {"origin": origin, "inputs": roots["inputs"]}
            call.update(overrides)
            workspaces.materialize_directory_source(
                {"name": "src", "type": "directory",
                 "uri": "file:///origin", "destination": "src",
                 "required": True,
                 "content_manifest": workspaces.directory_manifest(origin)},
                **call)
        return run

    def revising(self, *, answers=None, base_revision=None, **overrides):
        """One revision delivery, with one operand spoiled."""
        def run():
            storage = os.path.join(self.root, "probe-storage")
            os.makedirs(storage, exist_ok=True)
            roots = workspaces.assignment_workspace(storage, "a-probe")
            source = {"name": "repo", "type": "git",
                      "uri": "https://example.test/repo",
                      "destination": "repo", "required": True,
                      "repository_id": "repo-1", "object_format": "sha1",
                      "base_revision": (dict(GIT_REVISION)
                                        if base_revision is None
                                        else base_revision),
                      "source_ref": overrides.pop("source_ref", None),
                      "integration_ref": None,
                      "acquisition_policy_digest": "sha256:" + "c" * 64}
            call = {"inputs": roots["inputs"], "git_metadata": roots["git"]}
            call.update(overrides)
            workspaces.materialize_git_source(
                source, git=workspaces.GitPort(RecordingRepository(answers)),
                **call)
        return run

    def probes(self):
        """(entry, label fragment) -> (the full label, the one call that drives
        it).

        Keyed by the SAME tuple the universe and the owners are keyed by.
        Review [P1]: the previous table was keyed by `(kind, label)`, so one
        probe covered every entry sharing a label.

        THE FRAGMENT IS WHAT THE CODE SAYS; THE FULL LABEL IS WHAT THE PROBE
        ASSERTS. A shared owner builds its labels from the caller's noun, so
        `_assignment` contributes the literal `'s generation` to two crossings
        -- and asserting that fragment alone would let a probe aimed at the
        claim answer be satisfied by the committed claim's refusal, which is the
        one-label-two-entries problem again.
        """
        store, port = self.store, self.port
        offers = "offers.py"
        S = "store.py:ControlStore"
        A = "authority_port.py:AuthorityPort"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        def claiming(offer_id, **answer):
            def run():
                self.accepted(offer_id)
                self.session.claim_answer = (
                    answer["whole"] if "whole" in answer
                    else dict(self.session.claim_answer, **answer))
                worker_manager.submit_claim(store, port, offer_id=offer_id)
            return run

        def retiring(offer_id, **record):
            def run():
                self.accepted(offer_id)
                self.session.settle_answer = {
                    "kind": "retired",
                    "record": dict({"reason": "r", "disposition": "d"},
                                   **record)}
                worker_manager.settle_claim(store, port, offer_id=offer_id,
                                            now=NOW)
            return run

        def committing(offer_id, **result):
            def run():
                self.accepted(offer_id)
                self.session.settle_answer = {
                    "kind": "committed",
                    "result": (result["whole"] if "whole" in result
                               else dict(self.session.claim_answer, **result))}
                worker_manager.settle_claim(store, port, offer_id=offer_id,
                                            now=NOW)
            return run

        H = "handshake.py"

        def spoiling_profile(*path):
            """A valid ACP profile with ONE member made unstorable.

            The document owner refuses the whole document for any member it
            cannot take, so the probe for each member spoils exactly that
            member and nothing else -- which is what keeps one probe from
            standing in for its neighbour.
            """
            def run():
                profile = acp_profile()
                target = profile
                for step in path[:-1]:
                    target = target[step]
                target[path[-1]] = SURROGATE
                worker_manager.certify_agent_session_profile(store, profile)
            return run

        def spoiling_retained(body):
            def run():
                profile = acp_profile()
                worker_manager.certify_agent_session_profile(store, profile)
                self.corrupt("UPDATE profiles SET body = ?", body(profile))
                worker_manager.certified_agent_session_profile(
                    store, profile["document_digest"])
            return run

        def without(profile, member):
            return json.dumps({name: value for name, value in profile.items()
                               if name != member})

        return {
            # -- W6631: the six focused gaps left after its declarations -----
            (at("workspaces.py:GitPort.__init__", "repository"),
             "the git repository's resolve operation"):
                ("the git repository's resolve operation",
                 lambda: workspaces.GitPort(type(
                     "MissingResolve", (),
                     {"checkout": lambda *args, **kwargs: None})())),
            (at("workspaces.py:GitPort.__init__", "repository"),
             "the git repository's checkout operation"):
                ("the git repository's checkout operation",
                 lambda: workspaces.GitPort(type(
                     "MissingCheckout", (),
                     {"resolve": lambda *args, **kwargs: None})())),
            (at("workspaces.py:assignment_workspace", "assignment_id"),
             "an assignment identity"):
                ("an assignment identity",
                 lambda: workspaces.assignment_workspace(
                     self.root, SURROGATE)),
            (at("workspaces.py:discard_workspace", "assignment_id"),
             "an assignment identity"):
                ("an assignment identity",
                 lambda: workspaces.discard_workspace(
                     self.root, SURROGATE)),
            (at("workspaces.py:materialize_directory_source", "source"),
             "a directory source"):
                ("a directory source",
                 lambda: workspaces.materialize_directory_source(
                     7, origin=self.root, inputs=self.root)),
            (at("workspaces.py:materialize_git_source", "source"),
             "a git source"):
                ("a git source",
                 lambda: workspaces.materialize_git_source(
                     7, git=None, inputs=self.root, git_metadata=self.root)),
            # -- W6592 cut A: the composition's own operands ------------------
            (at(f"{H}:certify_agent_session_profile", "profile"),
             "an agent-session profile"): ("an agent-session profile",
                lambda: worker_manager.certify_agent_session_profile(
                    store, SURROGATE)),
            (at(f"{H}:certify_agent_session_profile", "profile.profile_id"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("profile_id")),
            (at(f"{H}:certify_agent_session_profile",
                "profile.document_digest"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("document_digest")),
            (at(f"{H}:certify_agent_session_profile", "profile.postures"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("postures")),
            (at(f"{H}:certify_agent_session_profile",
                "profile.postures.consent"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("postures", "consent")),
            (at(f"{H}:certify_agent_session_profile",
                "profile.postures.consent.policy"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("postures", "consent", "policy")),
            (at(f"{H}:certify_agent_session_profile",
                "profile.postures.execution"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("postures", "execution")),
            (at(f"{H}:certify_agent_session_profile",
                "profile.postures.execution.policy"),
             "an agent-session profile"): ("an agent-session profile",
                spoiling_profile("postures", "execution", "policy")),
            (at(f"{H}:certified_agent_session_profile", "profile_digest"),
             "a certified profile digest"): ("a certified profile digest",
                lambda: worker_manager.certified_agent_session_profile(
                    store, SURROGATE)),
            (at(f"{H}:negotiate_acp", "profile_digest"),
             "a certified profile digest"): ("a certified profile digest",
                lambda: worker_manager.negotiate_acp(
                    store, SURROGATE, agent_protocol_version=1)),
            # -- and the row it reads back ------------------------------------
            (at(f"{H}:certified_agent_session_profile", "profiles", "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(lambda profile: "{not json")),
            (at(f"{H}:certified_agent_session_profile", "profiles.body",
                "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(lambda profile: "[]")),
            (at(f"{H}:certified_agent_session_profile",
                "profiles.body.document_digest", "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(
                     lambda profile: without(profile, "document_digest"))),
            (at(f"{H}:certified_agent_session_profile",
                "profiles.body.wire_protocol", "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(
                     lambda profile: without(profile, "wire_protocol"))),
            (at(f"{H}:certified_agent_session_profile",
                "profiles.body.pinned_wire_version", "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(
                     lambda profile: without(profile, "pinned_wire_version"))),
            (at(f"{H}:certified_agent_session_profile",
                "profiles.body.client_capabilities", "adopted"),
             "a retained agent-session profile"):
                ("a retained agent-session profile",
                 spoiling_retained(
                     lambda profile: without(profile,
                                             "client_capabilities"))),
            # -- W6631: every path at its ONE owner, and the git half at
            # its single-owner helpers ---------------------------------------
            #
            # Each drives the real exported operation. `_real` refuses the
            # surrogate as text before it ever reaches the filesystem, which is
            # the point: the label is what the refusal must carry.
            (at("workspaces.py:directory_manifest", "root"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.directory_manifest(SURROGATE)),
            (at("workspaces.py:assignment_workspace", "storage"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.assignment_workspace(SURROGATE, "a-1")),
            (at("workspaces.py:discard_workspace", "storage"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.discard_workspace(SURROGATE, "a-1")),
            (at("workspaces.py:materialize_directory_source", "origin"),
             "a filesystem root"): ("a filesystem root",
                self.materializing(origin=SURROGATE)),
            (at("workspaces.py:materialize_directory_source", "inputs"),
             "a filesystem root"): ("a filesystem root",
                self.materializing(inputs=SURROGATE)),
            (at("workspaces.py:materialize_git_source", "inputs"),
             "a filesystem root"): ("a filesystem root",
                self.revising(inputs=SURROGATE)),
            (at("workspaces.py:materialize_git_source", "git_metadata"),
             "a filesystem root"): ("a filesystem root",
                self.revising(git_metadata=SURROGATE)),
            (at("workspaces.py:materialize_git_source", "found.algorithm"),
             "a resolved git object"): ("a resolved git object",
                self.revising(source_ref="refs/heads/main",
                              answers={"refs/heads/main": {"hex": "b" * 40}})),
            (at("workspaces.py:materialize_git_source", "found.hex"),
             "a resolved git object"): ("a resolved git object",
                self.revising(source_ref="refs/heads/main",
                              answers={"refs/heads/main":
                                       {"algorithm": "sha1"}})),
            # -- caller operands the layer owns at their own site -------------
            (at(f"{offers}:certify_profile", "kind"),
             "a certified profile kind"): ("a certified profile kind",
                lambda: certify_profile(store, SURROGATE, "reference", PROFILE)),
            (at(f"{offers}:certify_profile", "name"),
             "a certified profile name"): ("a certified profile name",
                lambda: certify_profile(store, "runtime", SURROGATE, PROFILE)),
            (at(f"{offers}:certify_profile", "profile_digest"),
             "a certified profile digest"): ("a certified profile digest",
                lambda: certify_profile(store, "runtime", "reference",
                                        SURROGATE)),
            (at(f"{offers}:expire_overdue", "now"), "the current instant"):
                ("the current instant",
                 lambda: worker_manager.expire_overdue(store,
                                                       SHAPED_BUT_UNREAL)),
            (at(f"{offers}:expire_overdue", "work_id"), "a Work id"):
                ("a Work id",
                 lambda: worker_manager.expire_overdue(store, NOW,
                                                       work_id=SURROGATE)),
            (at(f"{offers}:issue_offer", "offer_id"), "an offer id"):
                ("an offer id", self.offering(offer_id=SURROGATE)),
            (at(f"{offers}:issue_offer", "work_id"), "a Work id"):
                ("a Work id", self.offering(work_id=SURROGATE)),
            (at(f"{offers}:issue_offer", "runtime_attempt_id"),
             "a runtime attempt id"):
                ("a runtime attempt id",
                 self.offering(runtime_attempt_id=SURROGATE)),
            (at(f"{offers}:issue_offer", "input_digest"), "an input digest"):
                ("an input digest", self.offering(input_digest=SURROGATE)),
            (at(f"{offers}:issue_offer", "policy_digest"), "a policy digest"):
                ("a policy digest", self.offering(policy_digest=SURROGATE)),
            (at(f"{offers}:issue_offer", "profile_digest"), "a profile digest"):
                ("a profile digest", self.offering(profile_digest=SURROGATE)),
            (at(f"{offers}:issue_offer", "profile_name"), "a profile name"):
                ("a profile name", self.offering(profile_name=SURROGATE)),
            (at(f"{offers}:issue_offer", "ttl_seconds"), "the offer's expiry"):
                ("the offer's expiry", self.offering(ttl_seconds=10 ** 100)),
            (at(f"{offers}:issue_offer", "mint_bearer"), "the bearer mint"):
                ("the bearer mint", self.offering(mint_bearer=7)),
            (at(f"{offers}:accept_offer", "now"), "the current instant"):
                ("the current instant",
                 lambda: (self.issued("offer-an"),
                          worker_manager.accept_offer(
                              store, port, offer_id="offer-an",
                              decision="accept", bearer="bearer-1",
                              now=SHAPED_BUT_UNREAL,
                              runtime_attempt_id="attempt-1",
                              work_ref={"authority_uuid": UUID,
                                        "work_id": WORK}))),
            (at(f"{offers}:settle_claim", "now"), "the current instant"):
                ("the current instant",
                 lambda: (self.accepted("offer-sn"),
                          worker_manager.settle_claim(
                              store, port, offer_id="offer-sn",
                              now=SHAPED_BUT_UNREAL))),
            (at(f"{offers}:recover_on_restart", "now"), "the current instant"):
                ("the current instant",
                 lambda: worker_manager.recover_on_restart(
                     store, now=SHAPED_BUT_UNREAL)),
            (at("store.py:manager_signature", "kind"), "an operation kind"):
                ("an operation kind",
                 lambda: worker_manager.manager_signature(SURROGATE, {})),

            (at("store.py:revive_refusal", "sealed"), "a sealed refusal"):
                ("a sealed refusal",
                 lambda: worker_manager.revive_refusal("{not json")),
            # THE SEAL'S OWN MEMBERS, at the public door. Review [P1]: this
            # boundary checked four member NAMES and handed their contents on,
            # so a list category escaped as TypeError, a cross-category pair as
            # AssertionError, an integer message was accepted into a refusal,
            # and a `false` durable marker was silently rewritten to true.
            (at("store.py:revive_refusal", "sealed.category"),
             "a sealed refusal"): ("a sealed refusal",
                lambda: worker_manager.revive_refusal(json.dumps(
                    {"category": [], "code": "retention", "message": "held",
                     "durable": True}))),
            (at("store.py:revive_refusal", "sealed.code"),
             "a sealed refusal"): ("a sealed refusal",
                lambda: worker_manager.revive_refusal(json.dumps(
                    {"category": "policy", "code": "precondition",
                     "message": "held", "durable": True}))),
            (at("store.py:revive_refusal", "sealed.message"),
             "a sealed refusal"): ("a sealed refusal",
                lambda: worker_manager.revive_refusal(json.dumps(
                    {"category": "policy", "code": "retention", "message": 7,
                     "durable": True}))),
            (at(f"{S}.transact", "operation_id"), "an operation identity"):
                ("an operation identity",
                 lambda: store.transact(
                     SURROGATE, "k", worker_manager.manager_signature("k", {}),
                     lambda connection: None)),
            (at(f"{S}.transact", "action"), "the journalled action"):
                ("the journalled action",
                 lambda: store.transact(
                     "op-a", "k", worker_manager.manager_signature("k", {}),
                     7)),
            (at(f"{S}.replay", "operation_id"), "an operation identity"):
                ("an operation identity",
                 lambda: store.replay(
                     SURROGATE, worker_manager.manager_signature("k", {}))),
            (at(f"{S}.operation_record", "operation_id"),
             "an operation identity"): ("an operation identity",
                lambda: store.operation_record(SURROGATE)),
            (at(f"{S}.open", "clock"), "the manager's instant source"):
                ("the manager's instant source",
                 lambda: ControlStore.open(
                     os.path.join(self.root, "unclocked.sqlite3"),
                     incarnation="m", clock=7)),
            (at(f"{A}.__init__", "claim_signature"),
             "the authority's claim-signature derivation"):
                ("the authority's claim-signature derivation",
                 lambda: AuthorityPort(FakeSession(), "not callable")),
            # -- delegated: the probe drives the PUBLIC entry and must land on
            #    the delegate's label, which is what proves the delegation ----
            (at(f"{offers}:accept_offer", "offer_id"), "an offer id"):
                ("an offer id",
                 lambda: worker_manager.accept_offer(
                     store, port, offer_id=SURROGATE, decision="accept",
                     bearer="b", now=NOW, runtime_attempt_id="a",
                     work_ref={"authority_uuid": UUID, "work_id": WORK})),
            (at(f"{offers}:submit_claim", "offer_id"), "an offer id"):
                ("an offer id",
                 lambda: worker_manager.submit_claim(store, port,
                                                     offer_id=SURROGATE)),
            (at(f"{offers}:settle_claim", "offer_id"), "an offer id"):
                ("an offer id",
                 lambda: worker_manager.settle_claim(store, port,
                                                     offer_id=SURROGATE,
                                                     now=NOW)),
            (at(f"{S}.transact", "kind"), "an operation kind"):
                ("an operation kind",
                 lambda: store.transact(
                     "op-1", SURROGATE,
                     worker_manager.manager_signature("k", {}),
                     lambda connection: None)),
            (at(f"{S}.transact", "signature"), "an operation signature"):
                ("an operation signature",
                 lambda: store.transact("op-1", "k", SURROGATE,
                                        lambda connection: None)),
            # -- injected: the capability's bound value ----------------------
            (at(f"{A}.__init__", "participant", "injected"),
             "the identity this session binds an authorization to"):
                ("the identity this session binds an authorization to",
                 lambda: AuthorityPort(FakeSession(participant=SURROGATE),
                                       fake_claim_signature)),
            # -- injected: what a supplied capability ANSWERS -----------------
            (at(f"{A}.project_work", "project_work", "injected"),
             "the session's Work projection"):
                ("the session's Work projection",
                 lambda: (setattr(self.session, "_work", 7),
                          self.issued("offer-pw"))),
            (at(f"{A}.project_work", "project_work.authority_uuid",
                "injected"), "the projection's authority"):
                ("the projection's authority",
                 lambda: (setattr(self.session, "_work",
                                  dict(self.session._work, authority_uuid=7)),
                          self.issued("offer-pa"))),
            (at(f"{A}.slot_holder", "slot_holder", "injected"),
             "the session's slot holder"): ("the session's slot holder",
                lambda: (setattr(self.session, "_held", 7),
                         self.issued("offer-sh"))),
            (at(f"{A}.claim", "claim", "injected"), "'s identity"):
                ("the claim answer's identity", claiming("offer-ca", whole=7)),
            (at(f"{A}.claim", "claim.work_ref", "injected"),
             "'s Work reference"): ("the claim answer's Work reference",
                claiming("offer-cw", work_ref=7)),
            (at(f"{A}.claim", "claim.work_ref.authority_uuid", "injected"),
             "'s authority"): ("the claim answer's authority",
                claiming("offer-cu",
                         work_ref={"authority_uuid": 7, "work_id": WORK})),
            (at(f"{A}.claim", "claim.work_ref.work_id", "injected"),
             "'s Work id"): ("the claim answer's Work id",
                claiming("offer-ci",
                         work_ref={"authority_uuid": UUID, "work_id": 7})),
            (at(f"{A}.claim", "claim.participant", "injected"),
             "'s participant"): ("the claim answer's participant",
                claiming("offer-cp", participant=7)),
            (at(f"{A}.claim", "claim.generation", "injected"),
             "'s generation"): ("the claim answer's generation",
                claiming("offer-cg", generation="not-a-generation")),
            (at(f"{A}.settle_operation", "settle_operation", "injected"),
             "the session's settlement answer"):
                ("the session's settlement answer",
                 lambda: (self.accepted("offer-sa"),
                          setattr(self.session, "settle_answer",
                                  {"kind": "who-knows"}),
                          worker_manager.settle_claim(store, port,
                                                      offer_id="offer-sa",
                                                      now=NOW))),
            (at(f"{A}.settle_operation", "settle_operation.record.reason",
                "injected"), "the retirement's reason"):
                ("the retirement's reason", retiring("offer-rn", reason=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.record.disposition", "injected"),
             "the retirement's disposition"):
                ("the retirement's disposition",
                 retiring("offer-rp", disposition=7)),
            (at(f"{A}.settle_operation", "settle_operation.record",
                "injected"), "the retirement's bound record"):
                ("the retirement's bound record",
                 lambda: (self.accepted("offer-rr"),
                          setattr(self.session, "settle_answer",
                                  {"kind": "retired", "record": 7}),
                          worker_manager.settle_claim(store, port,
                                                      offer_id="offer-rr",
                                                      now=NOW))),
            (at(f"{A}.settle_operation", "settle_operation.detail",
                "injected"), "the refused settlement's detail"):
                ("the refused settlement's detail",
                 lambda: (self.accepted("offer-rd"),
                          setattr(self.session, "settle_answer",
                                  {"kind": "refused", "detail": 7}),
                          worker_manager.settle_claim(store, port,
                                                      offer_id="offer-rd",
                                                      now=NOW))),
            (at(f"{A}.settle_operation", "settle_operation.result",
                "injected"), "'s identity"):
                ("the committed claim's identity",
                 committing("offer-mi", whole=7)),
            (at(f"{A}.settle_operation", "settle_operation.result.work_ref",
                "injected"), "'s Work reference"):
                ("the committed claim's Work reference",
                 committing("offer-mw", work_ref=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.work_ref.authority_uuid", "injected"),
             "'s authority"): ("the committed claim's authority",
                committing("offer-mu",
                           work_ref={"authority_uuid": 7, "work_id": WORK})),
            (at(f"{A}.settle_operation",
                "settle_operation.result.work_ref.work_id", "injected"),
             "'s Work id"): ("the committed claim's Work id",
                committing("offer-mk",
                           work_ref={"authority_uuid": UUID, "work_id": 7})),
            (at(f"{A}.settle_operation",
                "settle_operation.result.participant", "injected"),
             "'s participant"): ("the committed claim's participant",
                committing("offer-mp", participant=7)),
            (at(f"{A}.settle_operation", "settle_operation.result.generation",
                "injected"), "'s generation"):
                ("the committed claim's generation",
                 committing("offer-mg", generation="not-a-generation")),
            (at(f"{A}.claim_signature", "claim_signature", "injected"),
             "the authority's claim signature"):
                ("the authority's claim signature",
                 lambda: (setattr(self, "port", AuthorityPort(
                     self.session, lambda work_id, participant: None)),
                     self.issued("offer-cs"),
                     worker_manager.accept_offer(
                         store, self.port, offer_id="offer-cs",
                         decision="accept", bearer="bearer-1", now=NOW,
                         runtime_attempt_id="attempt-1",
                         work_ref={"authority_uuid": UUID,
                                   "work_id": WORK}))),
            (at(f"{offers}:issue_offer", "mint_bearer", "injected"),
             "a minted bearer"): ("a minted bearer",
                self.offering(offer_id="offer-mb",
                              mint_bearer=lambda: SURROGATE)),
            (at(f"{S}._now", "clock", "injected"),
             "the configured clock's answer"):
                ("the configured clock's answer",
                 lambda: ControlStore.open(
                     os.path.join(self.root, "clock.sqlite3"), incarnation="m",
                     clock=lambda: SHAPED_BUT_UNREAL)),
            # -- adopted: persisted bytes, corrupted behind this build's back -
            (at(f"{offers}:_offers", "offers", "adopted"), "a persisted offer"):
                ("a persisted offer",
                 lambda: (self.accepted("offer-po"),
                          self.corrupt("UPDATE offers SET settle_by = ?",
                                       "not-an-instant"),
                          worker_manager.settle_claim(store, port,
                                                      offer_id="offer-po",
                                                      now=NOW))),
            (at(f"{offers}:_certified", "meta", "adopted"),
             "a persisted profile certification"):
                ("a persisted profile certification",
                 lambda: (self.corrupt(
                     "UPDATE meta SET value = '' WHERE key = ?",
                     "profile:runtime:reference"),
                     self.issued("offer-pc"))),
            (at(f"{S}._operation_row", "operations", "adopted"),
             "a persisted operation"): ("a persisted operation",
                lambda: (self.corrupt("UPDATE operations SET settled_at = ''"),
                         store.operation_record(
                             "profile.certify:runtime:reference"))),
            # -- cut D: the attempt, its activation and its observations ----
            (at("attempts.py:record_attempt", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                self.recorded(attempt_id=SURROGATE)),
            (at("attempts.py:record_attempt", "adapter_name"),
             "an adapter name"): ("an adapter name",
                self.recorded(adapter_name=SURROGATE)),
            (at("attempts.py:record_attempt", "adapter_digest"),
             "an adapter digest"): ("an adapter digest",
                self.recorded(adapter_digest=SURROGATE)),
            (at("attempts.py:record_attempt", "profile_digest"),
             "an attempt's profile digest"): ("an attempt's profile digest",
                self.recorded(profile_digest=SURROGATE)),
            (at("attempts.py:record_attempt", "input_digest"),
             ", when it is given,"):
                ("an attempt's input digest, when it is given,",
                 self.recorded(input_digest=SURROGATE)),
            (at("attempts.py:record_attempt", "policy_digest"),
             ", when it is given,"):
                ("an attempt's policy digest, when it is given,",
                 self.recorded(policy_digest=SURROGATE)),
            (at("attempts.py:record_attempt", "image_digest"),
             ", when it is given,"):
                ("an image digest, when it is given,",
                 self.recorded(image_digest=SURROGATE)),
            (at("attempts.py:record_attempt", "toolchain_digest"),
             ", when it is given,"):
                ("a toolchain digest, when it is given,",
                 self.recorded(toolchain_digest=SURROGATE)),
            (at("offers.py:claimed_offers_for", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.claimed_offers_for(store, SURROGATE)),
            (at("attempts.py:activate_assignment", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.activate_assignment(
                    store, port, attempt_id=SURROGATE,
                    expect={"work_ref": {"authority_uuid": UUID,
                                         "work_id": WORK},
                            "participant": WHO, "generation": 1})),
            (at("attempts.py:activate_assignment", "expect"),
             "the expected assignment"): ("the expected assignment",
                self.activated(whole=7)),
            (at("attempts.py:activate_assignment", "expect.work_ref"),
             "the expected assignment's Work reference"):
                ("the expected assignment's Work reference",
                 self.activated(work_ref=7)),
            (at("attempts.py:activate_assignment",
                "expect.work_ref.authority_uuid"),
             "the expected assignment's authority"):
                ("the expected assignment's authority",
                 self.activated(**{"work_ref.authority_uuid": 7})),
            (at("attempts.py:activate_assignment", "expect.work_ref.work_id"),
             "the expected assignment's Work"):
                ("the expected assignment's Work",
                 self.activated(**{"work_ref.work_id": 7})),
            (at("attempts.py:activate_assignment", "expect.participant"),
             "the expected assignment's participant"):
                ("the expected assignment's participant",
                 self.activated(participant=7)),
            (at("attempts.py:activate_assignment", "expect.generation"),
             "the expected assignment's generation"):
                ("the expected assignment's generation",
                 self.activated(generation="not-a-generation")),
            (at("attempts.py:observe", "attempt_id"), "a runtime attempt id"):
                ("a runtime attempt id",
                 lambda: worker_manager.observe(
                     store, attempt_id=SURROGATE, axis="consent_runtime",
                     value="running")),
            (at("attempts.py:observe", "source.incarnation"),
             "an observation source's incarnation"):
                ("an observation source's incarnation",
                 lambda: (self.recorded()(),
                          worker_manager.observe(
                              store, attempt_id="attempt-1",
                              axis="consent_runtime", value="running",
                              source={"incarnation": 7, "seq": 1}))),
            (at("attempts.py:observe", "source"), "an observation source"):
                ("an observation source",
                 lambda: (self.recorded()(),
                          worker_manager.observe(
                              store, attempt_id="attempt-1",
                              axis="consent_runtime", value="running",
                              source=7))),
            (at(f"{A}.assignment_of", "assignment_of", "injected"),
             "'s identity"): ("the live assignment's identity",
                self.living(7)),
            (at(f"{A}.assignment_of", "assignment_of.work_ref", "injected"),
             "'s Work reference"): ("the live assignment's Work reference",
                self.living({"work_ref": 7, "participant": WHO,
                             "generation": 1})),
            (at(f"{A}.assignment_of", "assignment_of.work_ref.authority_uuid",
                "injected"), "'s authority"):
                ("the live assignment's authority",
                 self.living({"work_ref": {"authority_uuid": 7,
                                           "work_id": WORK},
                              "participant": WHO, "generation": 1})),
            (at(f"{A}.assignment_of", "assignment_of.work_ref.work_id",
                "injected"), "'s Work id"):
                ("the live assignment's Work id",
                 self.living({"work_ref": {"authority_uuid": UUID,
                                           "work_id": 7},
                              "participant": WHO, "generation": 1})),
            (at(f"{A}.assignment_of", "assignment_of.participant", "injected"),
             "'s participant"): ("the live assignment's participant",
                self.living({"work_ref": {"authority_uuid": UUID,
                                          "work_id": WORK},
                             "participant": 7, "generation": 1})),
            (at(f"{A}.assignment_of", "assignment_of.generation", "injected"),
             "'s generation"): ("the live assignment's generation",
                self.living({"work_ref": {"authority_uuid": UUID,
                                          "work_id": WORK},
                             "participant": WHO,
                             "generation": "not-a-generation"})),
            (at("attempts.py:_attempts", "attempts", "adopted"),
             "a persisted attempt"): ("a persisted attempt",
                self.spoiling_attempt("created_at")),
            (at("attempts.py:_attempts", "attempts.runtime_id", "adopted"),
             "a persisted attempt"): ("a persisted attempt",
                self.spoiling_attempt("runtime_id")),
            (at("attempts.py:_decide", "observations", "adopted"),
             "a recorded observation digest"):
                ("a recorded observation digest",
                 self.spoiling_observation("observation_digest")),
            (at("attempts.py:_decide", "observations.observation_digest",
                "adopted"), "a recorded observation digest"):
                ("a recorded observation digest",
                 self.spoiling_observation("observation_digest")),
            # -- cut D, second slice: the runtime and its cancellation ------
            (at("attempts.py:request_runtime_start", "adapter"),
             "the runtime adapter's start"):
                ("the runtime adapter's start",
                 lambda: worker_manager.request_runtime_start(
                     store, object(), attempt_id="attempt-1")),
            (at("attempts.py:request_runtime_start", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.request_runtime_start(
                    store, FakeAdapter(self), attempt_id=SURROGATE)),
            (at("attempts.py:reconcile_runtime", "adapter"),
             "the runtime adapter's list"):
                ("the runtime adapter's list",
                 lambda: worker_manager.reconcile_runtime(
                     store, object(), attempt_id="attempt-1")),
            (at("attempts.py:reconcile_runtime", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.reconcile_runtime(
                    store, FakeAdapter(self), attempt_id=SURROGATE)),
            (at("attempts.py:reconcile_runtime", "minted"),
             "a minted runtime id"): ("a minted runtime id",
                lambda: (self.bound_attempt(),
                         worker_manager.reconcile_runtime(
                             store, FakeAdapter(self), attempt_id="attempt-1",
                             minted=7))),
            (at("attempts.py:reconcile_runtime", "minted_labels"),
             "a minted runtime's labels"): ("a minted runtime's labels",
                lambda: (self.bound_attempt(),
                         worker_manager.reconcile_runtime(
                             store, FakeAdapter(self), attempt_id="attempt-1",
                             minted="runtime-1", minted_labels=7))),
            (at("attempts.py:request_cancellation", "agent"),
             "the agent's cancel"): ("the agent's cancel",
                lambda: worker_manager.request_cancellation(
                    store, port, object(), FakeAdapter(self),
                    attempt_id="attempt-1")),
            (at("attempts.py:request_cancellation", "adapter"),
             "the runtime adapter's stop"): ("the runtime adapter's stop",
                lambda: worker_manager.request_cancellation(
                    store, port, FakeAgent(), object(),
                    attempt_id="attempt-1")),
            (at("attempts.py:request_cancellation", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.request_cancellation(
                    store, port, FakeAgent(), FakeAdapter(self),
                    attempt_id=SURROGATE)),
            (at("attempts.py:request_cancellation", "reason"),
             ", when it is given,"):
                ("a cancellation reason, when it is given,",
                 lambda: (self.attached(),
                          worker_manager.request_cancellation(
                              store, port, FakeAgent(), FakeAdapter(self),
                              attempt_id="attempt-1", reason=SURROGATE))),
            (at("attempts.py:request_runtime_start", "adapter.start",
                "injected"), "the adapter's start answer"):
                ("the adapter's start answer", self.starting(7)),
            (at("attempts.py:request_runtime_start", "adapter.start.runtime_id",
                "injected"), "a started runtime id"):
                ("a started runtime id",
                 self.starting({"runtime_id": 7, "labels": None})),
            (at("attempts.py:request_runtime_start", "adapter.start.labels",
                "injected"), "a started runtime's labels"):
                ("a started runtime's labels",
                 self.starting({"runtime_id": "runtime-1", "labels": 7})),
            (at("attempts.py:reconcile_runtime", "adapter.list", "injected"),
             "a listed runtime"): ("a listed runtime", self.listing([7])),
            (at("attempts.py:reconcile_runtime", "adapter.list.runtime_id",
                "injected"), "a listed runtime's id"):
                ("a listed runtime's id",
                 self.listing([{"runtime_id": 7, "labels": {}}])),
            (at("attempts.py:reconcile_runtime", "adapter.list.labels",
                "injected"), "a listed runtime's labels"):
                ("a listed runtime's labels",
                 self.listing([{"runtime_id": "runtime-1", "labels": 7}])),
            (at(f"{A}.cancel", "cancel", "injected"),
             "the session's fence answer"): ("the session's fence answer",
                self.fencing(whole=7)),
            (at(f"{A}.cancel", "cancel.cause", "injected"),
             "the fence's cause"): ("the fence's cause",
                self.fencing(cause=7)),
            (at(f"{A}.cancel", "cancel.assignment", "injected"),
             "'s identity"): ("the fenced assignment's identity",
                self.fencing(assignment=7)),
            (at(f"{A}.cancel", "cancel.assignment.work_ref", "injected"),
             "'s Work reference"): ("the fenced assignment's Work reference",
                self.fencing(**{"assignment.work_ref": 7})),
            (at(f"{A}.cancel", "cancel.assignment.work_ref.authority_uuid",
                "injected"), "'s authority"):
                ("the fenced assignment's authority",
                 self.fencing(**{"work_ref.authority_uuid": 7})),
            (at(f"{A}.cancel", "cancel.assignment.work_ref.work_id",
                "injected"), "'s Work id"):
                ("the fenced assignment's Work id",
                 self.fencing(**{"work_ref.work_id": 7})),
            (at(f"{A}.cancel", "cancel.assignment.participant", "injected"),
             "'s participant"): ("the fenced assignment's participant",
                self.fencing(**{"assignment.participant": 7})),
            (at(f"{A}.cancel", "cancel.assignment.generation", "injected"),
             "'s generation"): ("the fenced assignment's generation",
                self.fencing(**{"assignment.generation": "not-a-generation"})),
            (at("attempts.py:_attempts", "attempts.execution_runtime",
                "adopted"), "a persisted attempt"):
                ("a persisted attempt",
                 self.spoiling_attempt("execution_runtime")),
            (at(f"{S}._adopt", "meta.key", "adopted"),
             "a persisted meta key"): ("a persisted meta key",
                lambda: (self.corrupt(
                    "UPDATE meta SET key = '' WHERE key = 'schema_version'"),
                    ControlStore.open(self.path, incarnation="m",
                                      clock=lambda: NOW))),
            (at(f"{S}._adopt", "meta.value", "adopted"),
             "a persisted meta value"): ("a persisted meta value",
                lambda: (self.corrupt(
                    "UPDATE meta SET value = '' WHERE key = 'schema_version'"),
                    ControlStore.open(self.path, incarnation="m",
                                      clock=lambda: NOW))),
            (at(f"{offers}:_certified", "meta.value", "adopted"),
             "a persisted profile certification"):
                ("a persisted profile certification",
                 lambda: (self.corrupt(
                     "UPDATE meta SET value = '' WHERE key = ?",
                     "profile:runtime:reference"),
                     self.issued("offer-pv"))),
            (at(f"{S}._adopt", "meta", "adopted"), "a persisted meta key"):
                ("a persisted meta key",
                 lambda: (self.corrupt(
                     "UPDATE meta SET key = '' WHERE key = 'store_kind'"),
                     ControlStore.open(self.path, incarnation="m",
                                       clock=lambda: NOW))),
            (at(f"{S}._adopt", "meta", "adopted"), "a persisted meta value"):
                ("a persisted meta value",
                 lambda: (self.corrupt(
                     "UPDATE meta SET value = '' WHERE key = 'store_kind'"),
                     ControlStore.open(self.path, incarnation="m",
                                       clock=lambda: NOW))),
        }


GIT_REVISION = {"algorithm": "sha1", "hex": "a" * 40}


class RecordingRepository:
    """A repository that answers the two questions and records both."""

    def __init__(self, refs=None):
        self.refs = refs or {}
        self.calls = []

    def resolve(self, *, uri, ref):
        self.calls.append(("resolve", uri, ref))
        return self.refs.get(ref)

    def checkout(self, *, uri, revision, into, git_dir):
        self.calls.append(("checkout", uri, revision, into, git_dir))
        with open(os.path.join(into, "README"), "wb") as handle:
            handle.write(b"hello")


class FakeAdapter:
    """The narrow runtime adapter this slice calls through.

    It lists exactly what it started, which is the ordinary case; the cases that
    need a mismatch, a duplicate or an absence build their own.
    """

    def __init__(self, case, runtime_id="runtime-1"):
        self.case = case
        self.runtime_id = runtime_id
        self.started = []

    def labels_for(self, attempt_id="attempt-1"):
        beside = sqlite3.connect(self.case.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            row = beside.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (attempt_id,)).fetchone()
        finally:
            beside.close()
        return {"runtime_attempt_id": row["runtime_attempt_id"],
                "authority_uuid": row["authority_uuid"],
                "work_id": row["work_id"],
                "participant": row["assignment_participant"],
                "generation": row["assignment_generation"],
                "profile_digest": row["profile_digest"],
                "adapter_digest": row["adapter_digest"]}

    def start(self, operands):
        self.started.append(operands)
        return {"runtime_id": self.runtime_id, "labels": operands["labels"]}

    def list(self, operands):
        if not self.started:
            return []
        return [{"runtime_id": self.runtime_id,
                 "labels": self.started[0]["labels"]}]

    def stop(self, operands):
        return {"stopped": True}


class FakeAgent:
    def __init__(self):
        self.cancelled = []

    def cancel(self, operands):
        self.cancelled.append(operands)
        return {"acknowledged": True}


class SourceMaterializerCase(BoundaryCase):
    """W6631's revision half, driven through the public operation."""

    def deliver_revision(self, repository, **overrides):
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        roots = workspaces.assignment_workspace(self.storage,
                                                    "assignment-repo")
        source = {"name": "repo", "type": "git",
                  "uri": "https://example.test/repo",
                  "destination": "repo", "required": True,
                  "repository_id": "repo-1", "object_format": "sha1",
                  "base_revision": dict(GIT_REVISION),
                  "source_ref": None, "integration_ref": None,
                  "acquisition_policy_digest": "sha256:" + "c" * 64}
        source.update(overrides)
        return workspaces.materialize_git_source(
            source, git=workspaces.GitPort(repository),
            inputs=roots["inputs"], git_metadata=roots["git"])


class EveryReceivingEntryHasOneOwner(BoundaryCase):
    """PLAN 4bz and 4cc, as a check rather than an intention."""

    def owner_of(self, entry):
        if layer_labels(entry):
            return ("layer", layer_labels(entry))
        if entry in STATED_OWNERS:
            return ("stated", STATED_OWNERS[entry])
        if entry in DELEGATED and delegated_labels(entry):
            return ("delegated", delegated_labels(entry))
        if entry[0] == "caller" and entry[2] in CONSTRUCTED_BY:
            return ("constructed", CONSTRUCTED_BY[entry[2]])
        return (None, None)

    def test_every_receiving_entry_has_an_owning_validator(self):
        unowned = sorted(entry for entry in receiving_entries()
                         if self.owner_of(entry)[0] is None)
        self.assertEqual(unowned, [], "receiving entries with no owner")

    def test_the_universe_is_not_derived_from_the_validators(self):
        """The property that distinguishes this from what it replaces.

        Each domain is discovered from a structure that survives deleting every
        validator: parameters, capability calls, SQL reads.
        """
        entries = receiving_entries()
        self.assertGreater(len(entries), 50)
        self.assertEqual(sorted({domain for domain, _, _ in entries}),
                         sorted(boundaries.DOMAINS))
        counted = {domain: sum(1 for found, _, _ in entries if found == domain)
                   for domain in boundaries.DOMAINS}
        for domain, least in (("caller", 40), ("injected", 7), ("adopted", 5)):
            with self.subTest(domain=domain):
                self.assertGreaterEqual(counted[domain], least)

    def test_every_site_is_lexical(self):
        """Module, class and function -- because a name alone collapses methods.

        `AuthorityPort.claim` and a module-level `claim` are two functions with
        one name, and the version this replaces merged them.
        """
        sites = {site for _, site, _ in receiving_entries()}
        self.assertIn("authority_port.py:AuthorityPort.claim", sites)
        self.assertIn("store.py:ControlStore.replay", sites)
        self.assertIn("offers.py:settle_claim", sites)
        for site in sorted(sites):
            with self.subTest(site=site):
                self.assertRegex(site, r"\A[a-z_]+\.py:[A-Za-z_][\w.]*\Z")

    def test_variadic_public_parameters_are_receiving_entries_too(self):
        entries = receiving_entries()
        for constructor in ("profile_certified", "offer_issued",
                            "offer_settled", "offer_settled_by_another",
                            "offer_accepted", "claim_recorded",
                            "settlement_observed", "recoverable_offer",
                            "recovery_report"):
            with self.subTest(constructor=constructor):
                self.assertIn(("caller", f"documents.py:{constructor}",
                               "members"), entries)

    def test_the_universe_sees_every_persisted_column_that_is_read(self):
        """The anti-circularity check for the adopted member universe.

        Its entries are found by following origins and its probes are generated
        from those entries, so both shrink together if the tracking stops
        working. This compares the tracked result against a flat scan that uses
        none of that machinery.
        """
        tracked = {subject.split(".")[-1]
                   for domain, _, subject in receiving_entries()
                   if domain == "adopted" and "." in subject}
        scanned = columns_read()
        self.assertGreater(len(scanned), 12)
        self.assertEqual(sorted(scanned - tracked), [],
                         "columns this build reads that the universe cannot see")

    def test_no_declared_owner_is_stale(self):
        entries = receiving_entries()
        for table, what in ((STATED_OWNERS, "stated"), (DELEGATED, "delegated")):
            for entry in sorted(table):
                with self.subTest(table=what, entry=entry):
                    self.assertIn(entry, entries)

    def test_every_named_constructor_exists_and_owns_what_it_holds(self):
        """An exception has to point at a constructor that is THERE.

        Review [P1]: capability operands were removed from the universe because
        "each is owned at its constructor", and two of them were owned nowhere.
        The claim is only worth making if the site it names exists and has
        owners of its own.
        """
        sites = {site for _, site, _ in receiving_entries()}
        owners = owning_validators()
        for operand, site in sorted(CONSTRUCTED_BY.items()):
            with self.subTest(operand=operand):
                self.assertIn(site, sites)
                self.assertTrue(owners.get(site),
                                f"{site} owns nothing, so it cannot be where "
                                f"{operand} is owned")

    def test_no_declared_exception_is_stale(self):
        owners = owning_validators()
        for site, kind, label in sorted(NOT_AN_ENTRY):
            with self.subTest(site=site, label=label):
                self.assertIn((kind, label),
                              {(k, l) for k, l, _ in owners.get(site, ())})

    def test_every_boundary_call_belongs_to_an_entry_or_is_declared(self):
        """The other direction: an owner with nothing to own is also a defect.

        A layer call the inventory cannot attribute is either a boundary on a
        value nobody receives -- the double validation 4bz forbids -- or an
        entry the universe is failing to see. Both are worth a name.
        """
        owners = owning_validators()
        # BY (kind, label), not by site. A shared owner is written once and
        # attributed to every crossing that reaches it, so one call appears at
        # the helper's site and at each caller's -- and asking whether THIS copy
        # is claimed reports the copies as orphans. What has to be true is that
        # the boundary is claimed SOMEWHERE: a rule nothing owns has a label no
        # entry answers to, wherever it is written.
        claimed = set()
        for entry in receiving_entries():
            places = [(entry[1], _claims(entry))]
            if entry in DELEGATED:
                places.append(DELEGATED[entry])
            for site, stem in places:
                for label in _owned_here(site, stem,
                                         covering=entry[0] != "injected"):
                    claimed |= {(kind, label)
                                for kind, found, _ in owners.get(site, ())
                                if found == label}
        orphans = sorted({(site, kind, label)
                          for site, found in owners.items()
                          for kind, label, _ in found
                          if (kind, label) not in claimed
                          and (site, kind, label) not in NOT_AN_ENTRY})
        self.assertEqual(orphans, [], "boundary calls attributed to no entry")

    def test_the_double_ownership_check_can_actually_fail(self):
        # Nothing is owned twice today, so relaxing the count changes no
        # verdict -- measured. The check guards a future mistake, and the way to
        # test a guard with nothing to catch is to hand it something.
        fabricated = ("caller", "offers.py:issue_offer", "offer_id")
        self.assertTrue(layer_labels(fabricated))
        claims = sum([bool(layer_labels(fabricated)),
                      fabricated in {**STATED_OWNERS, fabricated: "fabricated"},
                      fabricated in DELEGATED])
        self.assertGreater(claims, 1, "the counting cannot see a second claim")

    def test_no_entry_is_owned_twice(self):
        """4bz forbids blanket revalidation, and this is where it shows."""
        for entry in sorted(receiving_entries()):
            with self.subTest(entry=entry):
                claims = sum([bool(layer_labels(entry)),
                              entry in STATED_OWNERS,
                              entry in DELEGATED,
                              entry[0] == "caller"
                              and entry[2] in CONSTRUCTED_BY])
                self.assertLessEqual(claims, 1, "owned more than once")


class EveryProbeProvesItArrived(BoundaryCase):
    """One probe per (entry, label), and every probe reaches what it names.

    Review [P1]: the probe gate iterated a global `(kind, label)` table while
    the inventory was keyed by entry, so nothing asserted that each entry had a
    probe -- an unowned adopted crossing coexisted with a green gate.
    """

    def all_probes(self):
        return {**self.probes(), **self.column_probes(),
                **self.session_probes()}

    def expected(self):
        """(entry, label) for every entry the LAYER or a DELEGATE owns.

        A stated owner is witnessed instead: its rule is not a boundary label,
        so a probe asserting one would be asserting the wrong thing.
        """
        wanted = set()
        for entry in receiving_entries():
            if entry in NO_PROBE:
                continue
            for label in layer_labels(entry):
                wanted.add((entry, label))
            if entry in DELEGATED:
                for label in delegated_labels(entry):
                    wanted.add((entry, label))
        return wanted

    def test_every_unprobed_entry_is_a_real_owned_entry(self):
        """An exemption has to name something that exists and IS owned.

        Otherwise "no probe" becomes a way to retire an entry by declaring it,
        which is the shape every exclusion in this file has been corrected for.
        """
        entries = receiving_entries()
        for entry in sorted(NO_PROBE):
            with self.subTest(entry=entry):
                self.assertIn(entry, entries)
                self.assertTrue(layer_labels(entry),
                                "unprobed and unowned is not an exemption")

    def test_every_owned_entry_has_exactly_one_probe(self):
        declared = set(self.all_probes())
        wanted = self.expected()
        self.assertEqual(sorted(wanted - declared), [], "owned, never probed")
        self.assertEqual(sorted(declared - wanted), [], "probed, never owned")

    def test_every_declared_probe_reaches_its_named_boundary(self):
        for entry, fragment in sorted(self.all_probes()):
            with self.subTest(entry=entry, label=fragment):
                self.setUp()
                full, probe = self.all_probes()[(entry, fragment)]
                # The fragment is what the SOURCE says; the full label is what
                # the refusal must carry. Requiring the one to contain the other
                # is what stops a probe naming a boundary it never reaches.
                self.assertIn(fragment, full)
                self.refusing(full, probe)

    def test_the_missing_probe_check_can_actually_fail(self):
        """Every entry has a probe today, so relaxing the check changes no
        verdict -- measured.

        The way to test a guard with nothing to catch is to hand it something:
        drop one probe and require the difference to name exactly that entry.
        """
        declared = set(self.all_probes())
        wanted = self.expected()
        self.assertEqual(wanted - declared, set())
        dropped = sorted(declared)[0]
        self.assertEqual(wanted - (declared - {dropped}), {dropped})

    def test_a_probe_that_is_refused_earlier_fails(self):
        """The vacuity guard, proved rather than promised.

        A review once found a row whose offer did not exist, so an earlier
        precondition refused and the spoiled operand was never read.
        """
        with self.assertRaises(AssertionError) as caught:
            self.refusing(
                "the current instant",
                lambda: worker_manager.submit_claim(
                    self.store, self.port, offer_id="never-issued"))
        self.assertIn("not at", str(caught.exception))


# Which test method witnesses each stated owner. A stated rule is not a boundary
# label, so it is exercised rather than probed -- and the mapping is checked both
# ways, so a rule with no witness and a witness naming no rule both fail.
WITNESSES = {
    # -- W6627: the agent session -------------------------------------------
    ("caller", "sessions.py:permits_session_transition", "from_state"):
        "test_the_nine_frozen_states_are_a_closed_vocabulary",
    ("caller", "sessions.py:permits_session_transition", "to_state"):
        "test_the_nine_frozen_states_are_a_closed_vocabulary",
    ("caller", "sessions.py:satisfies_runtime_quiescence_gate", "state"):
        "test_the_nine_frozen_states_are_a_closed_vocabulary",
    ("caller", "sessions.py:observe_session_state", "state"):
        "test_the_nine_frozen_states_are_a_closed_vocabulary",
    ("caller", "posture_slots.py:release_slot", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "posture_slots.py:require_slot_recovery", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "sessions.py:adopt_provider_session", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "sessions.py:reconcile_agent_session", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "sessions.py:handle_transport_loss", "turn_in_flight"):
        "test_whether_a_turn_was_in_flight_is_an_exact_boolean",
    ("injected", "sessions.py:reconcile_agent_session",
     "agent.observe_session.kind"):
        "test_the_observation_discriminator_decides_before_anything_is_read",
    ("adopted", "sessions.py:_next_epoch", "agent_sessions"):
        "test_the_next_epoch_is_a_whole_number_by_construction",
    ("caller", "workspaces.py:GitPort.resolve", "uri"):
        "test_a_git_operand_reaches_the_repository_unchanged",
    ("caller", "workspaces.py:GitPort.resolve", "ref"):
        "test_a_git_operand_reaches_the_repository_unchanged",
    ("caller", "workspaces.py:GitPort.checkout", "uri"):
        "test_a_git_operand_reaches_the_repository_unchanged",
    ("caller", "workspaces.py:GitPort.checkout", "revision"):
        "test_a_git_operand_reaches_the_repository_unchanged",
    ("caller", "workspaces.py:GitPort.checkout", "into"):
        "test_a_checkout_is_given_places_this_component_created",
    ("caller", "workspaces.py:GitPort.checkout", "git_dir"):
        "test_a_checkout_is_given_places_this_component_created",
    ("caller", "workspaces.py:materialize_git_source", "git"):
        "test_a_repository_missing_an_operation_is_refused_at_construction",
    ("caller", "workspaces.py:materialize_git_source",
     "base_revision.algorithm"):
        "test_the_frozen_fragment_owns_the_revision_before_pinned_sees_it",
    ("caller", "workspaces.py:materialize_git_source", "base_revision.hex"):
        "test_the_frozen_fragment_owns_the_revision_before_pinned_sees_it",
    ("caller", "store.py:seal_refusal", "refusal"):
        "test_public_sealing_owns_the_refusal_before_reading_it",
    # -- W6592 cut A --------------------------------------------------------
    ("caller", "documents.py:agent_session_certified", "members"):
        "test_an_outbound_constructor_owns_its_member_set",
    ("caller", "documents.py:acp_negotiated", "members"):
        "test_an_outbound_constructor_owns_its_member_set",
    ("caller", "handshake.py:check_client_capabilities", "advertised"):
        "test_the_advertised_capability_is_owned_by_2_2s_own_rule",
    ("caller", "handshake.py:check_client_capabilities", "advertised.fs"):
        "test_the_advertised_capability_is_owned_by_2_2s_own_rule",
    ("caller", "handshake.py:check_client_capabilities", "advertised.terminal"):
        "test_the_advertised_capability_is_owned_by_2_2s_own_rule",
    ("caller", "handshake.py:negotiate_acp", "agent_protocol_version"):
        "test_the_answered_wire_version_is_compared_against_the_pin",
    ("caller", "handshake.py:negotiate_acp", "agent_session_capabilities"):
        "test_the_agents_capability_answer_is_owned_before_it_is_walked",
    ("caller", "authority_port.py:AuthorityPort.project_work", "work_id"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.slot_holder", "participant"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.claim", "work_id"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.claim", "operation_id"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "operation_id"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "signature"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "reason"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "disposition"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "may_retire"): "test_settlement_authority_is_asserted_not_inherited",
    ("caller", "authority_port.py:AuthorityPort.claim_signature", "work_id"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "authority_port.py:AuthorityPort.claim_signature",
     "participant"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "documents.py:offer_bearer", "issued"):
        "test_an_outbound_constructor_refuses_a_shape_its_contract_omits",
    ("caller", "documents.py:offer_bearer", "bearer"):
        "test_an_outbound_document_is_built_in_its_contract_order",
    ("caller", "offers.py:claim_operation_id", "offer_id"):
        "test_the_claim_operation_id_is_a_derivation_of_its_operands",
    ("caller", "offers.py:claim_operation_id", "intent_digest"):
        "test_the_claim_operation_id_is_a_derivation_of_its_operands",
    ("caller", "offers.py:issue_offer", "participant"):
        "test_an_offer_naming_another_participant_is_refused",
    ("caller", "offers.py:accept_offer", "decision"):
        "test_a_decision_is_accept_or_decline",
    ("caller", "offers.py:accept_offer", "bearer"):
        "test_a_decision_carries_the_bearer_the_offer_was_issued_with",
    ("caller", "offers.py:accept_offer", "work_ref"):
        "test_a_decision_names_this_offers_own_attempt_and_work",
    ("caller", "offers.py:accept_offer", "work_ref.work_id"):
        "test_a_decision_names_this_offers_own_attempt_and_work",
    ("caller", "offers.py:accept_offer", "work_ref.authority_uuid"):
        "test_a_decision_names_this_offers_own_attempt_and_work",
    ("caller", "offers.py:accept_offer", "runtime_attempt_id"):
        "test_a_decision_names_this_offers_own_attempt_and_work",
    ("caller", "offers.py:accept_offer", "reason"):
        "test_prose_rides_the_signature_that_records_it",
    ("caller", "offers.py:settle_claim", "refused_evidence"):
        "test_a_forwarded_operand_reaches_the_authority_unchanged",
    ("caller", "store.py:manager_signature", "operands"):
        "test_signature_operands_are_canonicalized",
    ("caller", "store.py:ControlStore.open", "path"):
        "test_open_refuses_its_own_operands_with_its_own_closed_pair",
    ("caller", "store.py:ControlStore.open", "incarnation"):
        "test_open_refuses_its_own_operands_with_its_own_closed_pair",
    ("caller", "store.py:ControlStore.replay", "signature"):
        "test_a_replay_of_other_operands_is_an_operation_collision",
    ("caller", "store.py:ControlStore.replay", "kind"):
        "test_a_replay_of_other_operands_is_an_operation_collision",
    ("caller", "authority_port.py:AuthorityPort.__init__", "session"):
        "test_every_operation_the_port_names_is_typed_at_construction",
    ("caller", "authority_port.py:AuthorityPort.settle_operation", "work_id"):
        "test_a_committed_claim_for_another_work_is_refused",
    ("caller", "authority_port.py:AuthorityPort.settle_operation",
     "authority_uuid"):
        "test_an_assignment_from_another_authority_is_refused",
    ("caller", "authority_port.py:AuthorityPort.claim", "authority_uuid"):
        "test_an_assignment_from_another_authority_is_refused",
    ("caller", "documents.py:profile_certified", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:offer_issued", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:offer_settled", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:offer_settled_by_another", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:offer_accepted", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:claim_recorded", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:settlement_observed", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:recoverable_offer", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:recovery_report", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "store.py:ControlStore.__init__", "connection"):
        "test_a_refused_open_leaves_no_handle_and_no_store",
    ("caller", "store.py:ControlStore.__init__", "incarnation"):
        "test_open_refuses_its_own_operands_with_its_own_closed_pair",
    ("caller", "store.py:ControlStore.__init__", "clock"):
        "test_open_refuses_its_own_operands_with_its_own_closed_pair",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.status"):
        "test_an_offer_is_issued_only_against_open_queued_unclaimed_work",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.phase"):
        "test_an_offer_is_issued_only_against_open_queued_unclaimed_work",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.handler"):
        "test_an_offer_is_issued_only_against_open_queued_unclaimed_work",
    ("injected", "authority_port.py:AuthorityPort.project_work",
     "project_work.gate"):
        "test_an_offer_is_issued_only_against_open_queued_unclaimed_work",
    ("injected", "authority_port.py:AuthorityPort.settle_operation",
     "settle_operation.kind"):
        "test_every_settlement_variant_carries_its_own_members",
    ("caller", "attempts.py:observe", "axis"):
        "test_an_observation_names_a_frozen_axis_and_one_of_its_values",
    ("caller", "authority_port.py:AuthorityPort.cancel", "expect"):
        "test_cancellation_fences_before_it_orders_anything",
    ("caller", "authority_port.py:AuthorityPort.cancel", "operation_id"):
        "test_cancellation_fences_before_it_orders_anything",
    ("caller", "authority_port.py:AuthorityPort.cancel", "reason"):
        "test_cancellation_fences_before_it_orders_anything",
    ("caller", "authority_port.py:AuthorityPort.cancel", "work_id"):
        "test_a_fence_that_ended_another_assignment_is_refused",
    ("caller", "authority_port.py:AuthorityPort.cancel", "authority_uuid"):
        "test_a_fence_that_ended_another_assignment_is_refused",
    ("injected", "authority_port.py:AuthorityPort.cancel", "cancel.fenced"):
        "test_an_unfenced_answer_stops_the_cancellation",
    ("injected", "attempts.py:_order_quiescence", "agent.cancel"):
        "test_a_settlement_rides_back_exactly_as_the_boundary_gave_it",
    ("injected", "attempts.py:_order_quiescence", "adapter.stop"):
        "test_a_settlement_rides_back_exactly_as_the_boundary_gave_it",
    ("caller", "documents.py:runtime_labels", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:runtime_start_requested", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:runtime_attached", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:runtime_uncertain", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:runtime_cancel", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:cancel_intent", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:quiescence_ordered", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:quiescence_not_ordered", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:attempt_cancelled", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "attempts.py:observe", "value"):
        "test_an_observation_names_a_frozen_axis_and_one_of_its_values",
    ("caller", "attempts.py:observe", "source.seq"):
        "test_a_source_sequence_counts_from_zero",
    ("caller", "authority_port.py:AuthorityPort.assignment_of", "work_id"):
        "test_activation_asks_the_authority_for_the_live_assignment",
    ("caller", "authority_port.py:AuthorityPort.assignment_of",
     "authority_uuid"):
        "test_activation_asks_the_authority_for_the_live_assignment",
    ("caller", "documents.py:work_ref", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:assignment", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:attempt_recorded", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:assignment_activated", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:observation", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("adopted", "attempts.py:_next_source_seq", "observations"):
        "test_a_minted_sequence_is_whole_because_the_column_is",
    ("adopted", "store.py:ControlStore._objects", "sqlite_master"):
        "test_the_catalogue_decides_one_membership_question",
}


class EveryStatedOwnerHasAWitness(BoundaryCase):
    """A stated owner is a claim until something exercises it."""

    def test_every_stated_owner_names_a_witness_that_exists(self):
        self.assertEqual(sorted(WITNESSES), sorted(STATED_OWNERS))
        for entry, name in sorted(WITNESSES.items()):
            with self.subTest(entry=entry):
                found = getattr(StatedRules, name, None)
                self.assertTrue(callable(found), f"{name} is not a method")
                self.assertTrue(name.startswith("test_"),
                                f"{name} would never run")


class StatedRules(SourceMaterializerCase):
    """The witnesses themselves. Each exercises one stated rule."""

    # -- W6627's stated owners, exercised through the public operation -------

    def sessioned_here(self):
        """The same precondition the probes use, on this case's own store."""
        return BoundaryCase.sessioned(self)

    def test_the_nine_frozen_states_are_a_closed_vocabulary(self):
        """`sessions._state` answers ONE membership question and raises the
        frozen pair itself, so there is no boundary label to probe.

        Every caller of it is driven here, including the two functions whose
        whole answer is a constant: a gate that ignored its argument would
        answer `false` to a malformed question, which is how a caller concludes
        it asked a good one.
        """
        for what, run in [
                ("from_state",
                 lambda: worker_manager.permits_session_transition(
                     "gone", "ready")),
                ("to_state",
                 lambda: worker_manager.permits_session_transition(
                     "ready", "gone")),
                ("the quiescence gate",
                 lambda: worker_manager.satisfies_runtime_quiescence_gate(
                     "agent-gone")),
                ("an observed state",
                 lambda: worker_manager.observe_session_state(
                     self.store, self.sessioned_here(), "agent-gone"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    run()
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))
                self.assertIn("nine agent session states",
                              caught.exception.message)

    def test_a_session_epoch_counts_from_one(self):
        """`posture_slots._epoch` owns the frozen `positiveInt`, and it is not
        `boundaries.generation`: that rule is the ASSIGNMENT generation's and
        counts from zero. Epoch zero is a session nobody allocated."""
        self.sessioned_here()
        for what, run in [
                ("release_slot", lambda epoch: worker_manager.release_slot(
                    self.store, attempt_id="attempt-1", posture="execution",
                    session_epoch=epoch, evidence="runtime-absent",
                    observed_identity="runtime-1", reason="gone")),
                ("require_slot_recovery",
                 lambda epoch: worker_manager.require_slot_recovery(
                     self.store, attempt_id="attempt-1", posture="execution",
                     session_epoch=epoch, reason="ambiguous")),
                ("adopt_provider_session",
                 lambda epoch: worker_manager.adopt_provider_session(
                     self.store, attempt_id="attempt-1", posture="execution",
                     session_epoch=epoch, provider_session_id="p-1")),
                ("reconcile_agent_session",
                 lambda epoch: worker_manager.reconcile_agent_session(
                     self.store, _ObservingAgent(), attempt_id="attempt-1",
                     posture="execution", session_epoch=epoch))]:
            for spoiled in (0, -1, True, "1"):
                with self.subTest(what=what, epoch=spoiled):
                    with self.assertRaises(ContractRefusal) as caught:
                        run(spoiled)
                    self.assertIn("positive session epoch",
                                  caught.exception.message)

    def test_whether_a_turn_was_in_flight_is_an_exact_boolean(self):
        """§8.4 makes the reported turn outcome depend on this, and `?? false`
        would turn a WRONG argument into a MISSING one -- committing the epoch
        on an operand nobody proved."""
        reference = self.sessioned_here()
        for spoiled in (1, "yes", None, [], 0):
            with self.subTest(turn_in_flight=spoiled):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.handle_transport_loss(
                        self.store, reference, turn_in_flight=spoiled)
                self.assertIn("whether a turn was in flight",
                              caught.exception.message)

    def test_the_observation_discriminator_decides_before_anything_is_read(
            self):
        """`boundaries.alternative` reads `kind` to decide WHICH contract the
        rest of the answer is owned against, so an unrecognised answer is
        refused rather than read as the least alarming member of the set."""
        self.sessioned_here()
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.reconcile_agent_session(
                self.store, _ObservingAgent({"kind": "unreachable"}),
                attempt_id="attempt-1", posture="execution", session_epoch=1)
        self.assertIn("an agent session observation answers",
                      caught.exception.message)

    def test_the_next_epoch_is_a_whole_number_by_construction(self):
        """`COALESCE(MAX(x), 0) + 1` over a STRICT INTEGER column: there is
        nothing to own, and the empty case is the COALESCE. Witnessed by the
        two answers it can give -- a never-used posture and a used one."""
        self.sessioned_here()
        self.assertEqual(
            [row["session_epoch"]
             for row in worker_manager.agent_sessions_of(self.store,
                                                         "attempt-1")],
            [1])
        worker_manager.observe_session_state(
            self.store, self.reference(), "initializing")
        worker_manager.close_agent_session(self.store, self.reference())
        worker_manager.open_agent_session(
            self.store, self.port, attempt_id="attempt-1",
            posture="execution", profile_digest=self.agent_profile,
            intent="open-2")
        self.assertEqual(
            sorted(row["session_epoch"]
                   for row in worker_manager.agent_sessions_of(self.store,
                                                               "attempt-1")),
            [1, 2])

    # -- W6631's stated owners, exercised through the public operation -------

    def deliver_revision(self, repository, **overrides):
        storage = os.path.join(self.root, "storage")
        os.makedirs(storage, exist_ok=True)
        roots = workspaces.assignment_workspace(storage,
                                                    "assignment-repo")
        source = {"name": "repo", "type": "git",
                  "uri": "https://example.test/repo",
                  "destination": "repo", "required": True,
                  "repository_id": "repo-1", "object_format": "sha1",
                  "base_revision": dict(GIT_REVISION),
                  "source_ref": None, "integration_ref": None,
                  "acquisition_policy_digest": "sha256:" + "c" * 64}
        source.update(overrides)
        self.storage = storage
        return workspaces.materialize_git_source(
            source, git=workspaces.GitPort(repository),
            inputs=roots["inputs"], git_metadata=roots["git"])

    def test_a_git_operand_reaches_the_repository_unchanged(self):
        """The port forwards; the repository owns.

        What these entries state is that this component does not own what it
        forwards -- so what has to be true is that the operand ARRIVES exactly
        as it was given. A port that quietly rewrote one would leave the
        repository answering about something nobody asked for.
        """
        repository = RecordingRepository(refs={"refs/heads/main":
                                               dict(GIT_REVISION)})
        answer = self.deliver_revision(repository, source_ref="refs/heads/main")
        self.assertIn(("resolve", "https://example.test/repo",
                       "refs/heads/main"), repository.calls)
        checkout = [call for call in repository.calls if call[0] == "checkout"]
        self.assertEqual(len(checkout), 1)
        self.assertEqual(checkout[0][1], "https://example.test/repo")
        self.assertEqual(checkout[0][2], dict(GIT_REVISION))
        self.assertEqual(answer["base_revision"], dict(GIT_REVISION))

    def test_a_checkout_is_given_places_this_component_created(self):
        """The port hands out a place rather than accepting one.

        A caller that could name the checkout directory or the metadata
        directory would decide where somebody else's process writes, which is
        the private-metadata rule and the containment rule at once.
        """
        repository = RecordingRepository()
        answer = self.deliver_revision(repository)
        checkout = [call for call in repository.calls
                    if call[0] == "checkout"][0]
        into, git_dir = checkout[3], checkout[4]
        roots = workspaces.assignment_workspace(self.storage,
                                                    "assignment-repo")
        self.assertTrue(into.startswith(roots["inputs"] + os.sep))
        self.assertTrue(git_dir.startswith(roots["git"] + os.sep))
        self.assertEqual(answer["git_dir"], git_dir)

    def test_the_frozen_fragment_owns_the_revision_before_pinned_sees_it(self):
        """DIAGNOSED, not assumed. Item 2 put the frozen closed fragment ahead
        of every member read, so a malformed `base_revision` is refused as
        SHAPE -- "'base_revision'.'hex' breaks pattern" -- and never reaches
        `_pinned`. The declaration follows the code rather than the reverse.
        """
        for what, revision in [("no algorithm", {"hex": "a" * 40}),
                               ("no hex", {"algorithm": "sha1"}),
                               ("a hex that is not one",
                                {"algorithm": "sha1", "hex": "nope"})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.deliver_revision(RecordingRepository(),
                                          base_revision=revision)
                self.assertIn("frozen schema", caught.exception.message)

    def test_a_repository_missing_an_operation_is_refused_at_construction(self):
        """Typing a capability is cheap and happens before anything is spent."""
        class Partial:
            def resolve(self, **operands):
                return None

        for what, repository in [("nothing at all", object()),
                                 ("one operation missing", Partial())]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    workspaces.GitPort(repository)

    def test_public_sealing_owns_the_refusal_before_reading_it(self):
        """The public sealing door types its operand BEFORE reading a member.

        W7079 [P1]: removing the message sub-boundary left the ENCLOSING input
        unowned, so an object with a hostile `__getattribute__` ran caller
        behaviour on the way to `.category` and escaped as a raw
        AssertionError. Identity rather than `isinstance`, because a subclass
        can override attribute access and that is the thing being refused.
        """
        ran = []

        class Hostile:
            def __getattribute__(self, name):
                ran.append(name)
                raise AssertionError("caller code ran")

        for what, value in [("a hostile object", Hostile()),
                            ("not a refusal", "policy.retention"),
                            ("nothing", None)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.seal_refusal(value)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))
        self.assertEqual(ran, [], "a member was read before the type was")

    def test_an_outbound_constructor_owns_its_member_set(self):
        """4bz's outbound half: the contract owns the SHAPE.

        What these entries state is that `_emit` refuses a member set the
        document's own CONTRACTS entry does not name -- so a missing or an
        unexpected member is a defect in THIS build rather than something the
        far end has to discover.
        """
        for what, members in [
                ("a missing member", {"profile_id": "p"}),
                ("an unexpected member", {"profile_id": "p", "digest": "d",
                                          "extra": 1})]:
            with self.subTest(what=what):
                with self.assertRaises(Exception):
                    documents.agent_session_certified(**members)
        with self.assertRaises(Exception):
            documents.acp_negotiated(wire_version=1)
        self.assertEqual(
            list(documents.acp_negotiated(wire_version=1,
                                          client_capabilities={},
                                          session_capabilities=[])),
            ["wire_version", "client_capabilities", "session_capabilities"])

    def test_the_advertised_capability_is_owned_by_2_2s_own_rule(self):
        """Owned, and deliberately NOT by the layer.

        §2.2's answer is `policy.denied` -- this manager declining to
        advertise -- where the layer's own pair would say the relay sent
        something malformed. So the exact-record verdict comes from the POD
        primitive and this boundary supplies the closed pair, which is what a
        caller-local taxonomy is.
        """
        for what, advertised in [
                ("not a record", "fs"),
                ("a missing member", {"fs": {}}),
                ("an unexpected member", {"fs": {}, "terminal": False,
                                          "session": {}}),
                ("terminal not false", {"fs": {}, "terminal": 0}),
                ("an fs member present at all",
                 {"fs": {"readTextFile": False}, "terminal": False})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.check_client_capabilities(advertised)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
        self.assertEqual(
            worker_manager.check_client_capabilities({"fs": {},
                                                      "terminal": False}),
            {"fs": {}, "terminal": False})

    def test_the_answered_wire_version_is_compared_against_the_pin(self):
        """An answer is an announcement, not a negotiation."""
        profile = acp_profile()
        worker_manager.certify_agent_session_profile(self.store, profile)
        every = list(worker_manager.SESSION_CAPABILITIES)
        for answered in (2, 0, None, "1"):
            with self.subTest(answered=repr(answered)):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.negotiate_acp(
                        self.store, profile["document_digest"],
                        agent_protocol_version=answered,
                        agent_session_capabilities=every)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("refused", "unsupported-version"))
        self.assertEqual(
            worker_manager.negotiate_acp(
                self.store, profile["document_digest"],
                agent_protocol_version=profile["pinned_wire_version"],
                agent_session_capabilities=every)["wire_version"],
            profile["pinned_wire_version"])

    def test_the_agents_capability_answer_is_owned_before_it_is_walked(self):
        """An operand this manager iterates is one it can be handed a
        behaviour-bearing version of.

        A generator that yields the six mandatory capabilities the first time
        and nothing the second would otherwise pass the handshake and then
        fail every one of them, and a list whose members are not text would
        reach the comparison as values nobody owned.
        """
        profile = acp_profile()
        worker_manager.certify_agent_session_profile(self.store, profile)
        every = list(worker_manager.SESSION_CAPABILITIES)

        def once():
            yield from every

        for what, offered in [("a generator", once()),
                              ("a set", set(every)),
                              ("text", "".join(every)),
                              ("a member that is not text", every + [object()])]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    worker_manager.negotiate_acp(
                        self.store, profile["document_digest"],
                        agent_protocol_version=1,
                        agent_session_capabilities=offered)

    def test_a_forwarded_operand_reaches_the_authority_unchanged(self):
        """The port forwards; the authority owns.

        What these entries state is that the manager does not own what it
        forwards -- so what has to be true is that the operand ARRIVES, exactly
        as it was given. A port that quietly rewrote one would leave the
        authority owning a value nobody sent.
        """
        self.accepted("offer-f")
        worker_manager.submit_claim(self.store, self.port, offer_id="offer-f")
        self.assertIn(("project_work", WORK), self.session.calls)
        self.assertIn(("slot_holder", WHO), self.session.calls)
        claimed = [operands for name, operands in self.session.calls
                   if name == "claim"]
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0]["work_id"], WORK)
        self.assertEqual(
            claimed[0]["operation_id"],
            self.store.operation_record("offer.accept:offer-f") is not None
            and claimed[0]["operation_id"])
        self.assertTrue(claimed[0]["operation_id"].startswith("claim:"))
        self.accepted("offer-g")
        worker_manager.settle_claim(self.store, self.port, offer_id="offer-g",
                                    now=NOW, refused_evidence="it refused")
        settled = [operands for name, operands in self.session.calls
                   if name == "settle_operation"][-1]
        self.assertEqual(settled["reason"], "it refused")
        self.assertEqual(settled["disposition"], "claim-refused")
        self.assertTrue(settled["signature"])
        self.assertTrue(settled["operation_id"].startswith("claim:"))

    def test_settlement_authority_is_asserted_not_inherited(self):
        """`may_retire` is computed here and forwarded, never defaulted.

        Before the deadline and with no positive evidence a manager may only
        OBSERVE, and this operand is how the authority is told which it is.
        """
        self.accepted("offer-m")
        worker_manager.settle_claim(self.store, self.port, offer_id="offer-m",
                                    now=NOW)
        observed = [operands for name, operands in self.session.calls
                    if name == "settle_operation"][-1]
        self.assertIs(observed["may_retire"], False)
        # A FRESH STORE. `offer-m` is still accepted and still holds this Work's
        # one live slot, which is the invariant a second offer would violate.
        self.setUp()
        self.accepted("offer-m2")
        worker_manager.settle_claim(self.store, self.port, offer_id="offer-m2",
                                    now=NOW, refused_evidence="it refused")
        asserted = [operands for name, operands in self.session.calls
                    if name == "settle_operation"][-1]
        self.assertIs(asserted["may_retire"], True)

    def test_an_outbound_constructor_refuses_a_shape_its_contract_omits(self):
        """4bz's outbound half: the constructor owns the SHAPE.

        Its operands are this build's own values and the far end owns those, so
        what a constructor refuses is a member set -- the one thing it is
        responsible for.
        """
        issued = documents.offer_issued(
            offer_id="o", work_id=WORK, participant=WHO,
            runtime_attempt_id="a", verifier="v", issued_at=NOW,
            expires_at=NOW)
        carried = documents.offer_bearer(issued, "bearer-1")
        self.assertEqual(
            list(carried),
            list(documents.CONTRACTS["offer.issued-with-bearer"][0]))
        with self.assertRaises(ContractRefusal) as caught:
            documents.offer_bearer(dict(issued, surprise=1), "bearer-1")
        self.assertIn("surprise", caught.exception.message)
        with self.assertRaises(ContractRefusal) as caught:
            documents.offer_bearer({"offer_id": "o"}, "bearer-1")
        self.assertIn("work_id", caught.exception.message)

    def test_an_outbound_document_is_built_in_its_contract_order(self):
        """Two paths building one document must build the same bytes.

        These answers are JOURNALLED, and an exact retry reproduces the stored
        ones -- so a document whose member order depends on which branch
        assembled it is two durable answers wearing one identity.
        """
        first = documents.claim_recorded(offer_id="o", state="claimed",
                                         assignment=None, late=True)
        second = documents.claim_recorded(late=True, assignment=None,
                                          state="claimed", offer_id="o")
        self.assertEqual(list(first), list(second))
        self.assertEqual(list(first), ["offer_id", "state", "assignment",
                                       "late"])
        # And an omitted optional member stays omitted rather than arriving as
        # None: "no reason" and "the reason was null" are different answers.
        self.assertEqual(list(documents.claim_recorded(offer_id="o",
                                                       state="claimed")),
                         ["offer_id", "state"])

    def test_the_claim_operation_id_is_a_derivation_of_its_operands(self):
        """Same operands, same id; different operands, different id.

        Nothing is owned here because nothing is stored here -- the answer is
        proved where acceptance freezes it.
        """
        first = worker_manager.claim_operation_id("offer-1", "sha256:aa")
        self.assertEqual(
            first, worker_manager.claim_operation_id("offer-1", "sha256:aa"))
        self.assertNotEqual(
            first, worker_manager.claim_operation_id("offer-2", "sha256:aa"))
        self.assertNotEqual(
            first, worker_manager.claim_operation_id("offer-1", "sha256:bb"))

    def test_an_offer_naming_another_participant_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.issue_offer(
                self.store, self.port, offer_id="offer-p", work_id=WORK,
                runtime_attempt_id="a", input_digest="d", policy_digest="d",
                profile_digest=PROFILE, profile_name="reference",
                mint_bearer=lambda: "b", participant="baton.someone-else")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("the binding", caught.exception.message)

    def test_a_decision_is_accept_or_decline(self):
        self.issued("offer-d")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.accept_offer(
                self.store, self.port, offer_id="offer-d", decision="maybe",
                bearer="bearer-1", now=NOW, runtime_attempt_id="attempt-1",
                work_ref={"authority_uuid": UUID, "work_id": WORK})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("accept or decline", caught.exception.message)

    def test_a_decision_carries_the_bearer_the_offer_was_issued_with(self):
        for what, bearer in [("another secret", "bearer-2"),
                             ("no secret at all", None)]:
            with self.subTest(what=what):
                self.setUp()
                self.issued("offer-b")
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.accept_offer(
                        self.store, self.port, offer_id="offer-b",
                        decision="accept", bearer=bearer, now=NOW,
                        runtime_attempt_id="attempt-1",
                        work_ref={"authority_uuid": UUID, "work_id": WORK})
                self.assertEqual(caught.exception.code, "capability")

    def test_a_decision_names_this_offers_own_attempt_and_work(self):
        for what, operands in [
                ("another attempt", dict(runtime_attempt_id="attempt-9")),
                ("another Work", dict(work_ref={"authority_uuid": UUID,
                                                "work_id": "0000000a-W9"})),
                ("another authority", dict(work_ref={"authority_uuid": "z" * 32,
                                                     "work_id": WORK})),
                ("no Work reference at all", dict(work_ref=7))]:
            with self.subTest(what=what):
                self.setUp()
                self.issued("offer-w")
                call = dict(offer_id="offer-w", decision="accept",
                            bearer="bearer-1", now=NOW,
                            runtime_attempt_id="attempt-1",
                            work_ref={"authority_uuid": UUID, "work_id": WORK})
                call.update(operands)
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.accept_offer(self.store, self.port, **call)
                self.assertEqual(caught.exception.code, "precondition")

    def test_prose_rides_the_signature_that_records_it(self):
        """Prose is not owned at entry; the act that records it owns it.

        A decline's reason becomes part of the settlement's manager signature,
        and canonicalization refuses every value a durable document cannot
        carry -- so unstorable prose is refused BEFORE the decision commits
        rather than accepted and lost at the driver.
        """
        self.issued("offer-r")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.accept_offer(
                self.store, self.port, offer_id="offer-r", decision="decline",
                bearer="bearer-1", now=NOW, runtime_attempt_id="attempt-1",
                work_ref={"authority_uuid": UUID, "work_id": WORK},
                reason="declined " + SURROGATE)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("surrogate", caught.exception.message)
        # AND NOTHING COMMITTED: the decline left no journal row, so the
        # refusal happened before the decision rather than after it.
        self.assertIsNone(
            self.store.operation_record("offer.declined:offer-r"))

    def test_a_replay_of_other_operands_is_an_operation_collision(self):
        """Replay compares; it does not re-derive.

        §4.2: reusing a recorded identity with different operands changes
        nothing and says so. Both operands are checked against WHAT WAS
        RECORDED, which is why neither is owned by a shape rule here.
        """
        signature = worker_manager.manager_signature("k", {"a": 1})
        self.store.transact("op-1", "k", signature, lambda connection: None)
        self.assertEqual(self.store.replay("op-1", signature, kind="k"),
                         (True, None))
        for what, call in [
                ("other operands",
                 dict(signature=worker_manager.manager_signature("k", {"a": 2}),
                      kind="k")),
                ("another kind", dict(signature=signature, kind="other"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.store.replay("op-1", call["signature"],
                                      kind=call["kind"])
                self.assertEqual(caught.exception.code, "operation-collision")

    def test_signature_operands_are_canonicalized(self):
        """Canonicalization is the owner: it refuses what it cannot carry."""
        self.assertEqual(worker_manager.manager_signature("k", {"a": 1}),
                         worker_manager.manager_signature("k", {"a": 1}))
        for what, operands in [("a set", {"a": {1, 2}}),
                               ("an object", {"a": object()}),
                               ("a nan", {"a": float("nan")})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    worker_manager.manager_signature("k", operands)

    def test_open_refuses_its_own_operands_with_its_own_closed_pair(self):
        """A path this build must not touch is integrity/PATH, not a schema
        fault.

        Which is exactly why these two are not the layer's: the closed pair a
        caller receives is part of the answer, and `text` would give the wrong
        one.
        """
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open("", incarnation="m", clock=lambda: NOW)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "path"))
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(os.path.join(self.root, "x.sqlite3"),
                              incarnation="", clock=lambda: NOW)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("incarnation", caught.exception.message)

    def test_every_operation_the_port_names_is_typed_at_construction(self):
        """A capability discovered to be missing once durable state depends on
        it was not typed at all.

        So each of the four is checked BEFORE the port exists, and a session
        carrying three of them and `None` for the fourth is refused rather than
        found out during acceptance.
        """
        for member in ("project_work", "slot_holder", "claim",
                       "settle_operation"):
            with self.subTest(member=member):
                session = FakeSession()
                setattr(session, member, None)
                with self.assertRaises(ContractRefusal) as caught:
                    AuthorityPort(session, fake_claim_signature)
                self.assertIn(member, caught.exception.message)

    def test_a_committed_claim_for_another_work_is_refused(self):
        """The Work operand is the COMPARISON, and it comes from an owned row.

        A commit this manager never saw is recorded late from the authority's
        answer, so an answer naming another Work would durably attribute
        somebody else's claim to this offer.
        """
        self.accepted("offer-ow")
        self.session.settle_answer = {
            "kind": "committed",
            "result": {"work_ref": {"authority_uuid": UUID,
                                    "work_id": "0000000a-W9"},
                       "participant": WHO, "generation": 1}}
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.settle_claim(self.store, self.port,
                                        offer_id="offer-ow", now=NOW)
        self.assertIn("0000000a-W9", caught.exception.message)
        self.assertIn(WORK, caught.exception.message)

    def test_an_assignment_from_another_authority_is_refused(self):
        """The relationship the type check left unowned.

        A four-part identity is not owned if one of its relationships is only
        shaped: a well-formed assignment from authority ffff... was accepted for
        an offer issued from 0000...a, advanced it to `claimed` and recorded the
        foreign generation. Both claim paths compare it now, from the offer's
        own adopted authority.
        """
        elsewhere = "f" * 32
        self.accepted("offer-fa")
        self.session.claim_answer = {
            "work_ref": {"authority_uuid": elsewhere, "work_id": WORK},
            "participant": WHO, "generation": 1}
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.submit_claim(self.store, self.port,
                                        offer_id="offer-fa")
        self.assertIn(elsewhere, caught.exception.message)
        self.assertIn(UUID, caught.exception.message)
        self.assertEqual(
            self.store.operation_record("offer.settle:offer-fa"), None)
        self.setUp()
        self.accepted("offer-fb")
        self.session.settle_answer = {
            "kind": "committed",
            "result": {"work_ref": {"authority_uuid": elsewhere,
                                    "work_id": WORK},
                       "participant": WHO, "generation": 1}}
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.settle_claim(self.store, self.port,
                                        offer_id="offer-fb", now=NOW)
        self.assertIn(elsewhere, caught.exception.message)

    def test_every_outbound_constructor_holds_its_contract(self):
        """All nine, derived from the table rather than listed here.

        Each is driven with its own required members, then with one missing and
        with one the contract does not name -- so a constructor added without a
        contract, or a contract nothing enforces, fails this rather than waiting
        for a reader.
        """
        for name in sorted(documents.CONTRACTS):
            builder = getattr(documents, name.replace(".", "_")
                              .replace("-", "_"), None)
            if builder is None:
                continue
            required, _ = documents.CONTRACTS[name]
            with self.subTest(document=name):
                whole = {member: member for member in required}
                self.assertEqual(list(builder(**whole)), list(required))
                with self.assertRaises(ContractRefusal):
                    builder(**dict(whole, surprise=1))
                if required:
                    short = dict(whole)
                    short.pop(required[0])
                    with self.assertRaises(ContractRefusal):
                        builder(**short)

    def test_a_refused_open_leaves_no_handle_and_no_store(self):
        """The handle is assembled by `open`, which closes it on every refused
        path.

        Which is the rule `connection` states: nobody hands this class a
        connection it did not decide on, and a refused open holds no lock on a
        database it has just said it must not touch.
        """
        foreign = os.path.join(self.root, "notours.sqlite3")
        beside = sqlite3.connect(foreign, isolation_level=None)
        try:
            beside.execute("CREATE TABLE somebody_elses (id INTEGER)")
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal):
            ControlStore.open(foreign, incarnation="m", clock=lambda: NOW)
        # The proof the handle went with it: the file is writable by another
        # connection immediately, with no lock left behind.
        beside = sqlite3.connect(foreign, isolation_level=None, timeout=0.1)
        try:
            beside.execute("INSERT INTO somebody_elses (id) VALUES (1)")
        finally:
            beside.close()

    def test_an_offer_is_issued_only_against_open_queued_unclaimed_work(self):
        """The four projection members the manager COMPARES rather than shapes.

        Their contract is not a type: it is the one state an offer may be issued
        against, and every other value -- including a well-formed one -- refuses.
        """
        for member, value in [("status", "closed"), ("phase", "active"),
                              ("handler", "baton.someone"),
                              ("gate", {"token": "g", "kind": "offer",
                                        "detail": None})]:
            with self.subTest(member=member):
                self.setUp()
                self.session._work = dict(self.session._work, **{member: value})
                with self.assertRaises(ContractRefusal) as caught:
                    self.issued("offer-q")
                self.assertEqual(caught.exception.code, "precondition")
                self.assertIn("open, queued, unclaimed, ungated",
                              caught.exception.message)

    def test_every_settlement_variant_carries_its_own_members(self):
        """The discriminator is owned by the closed set that reads it."""
        for kind in ("live", "committed", "retired", "refused"):
            with self.subTest(kind=kind):
                self.setUp()
                self.accepted("offer-k")
                self.session.settle_answer = {"kind": kind}
                self.refusing("the session's settlement answer",
                              lambda: worker_manager.settle_claim(
                                  self.store, self.port, offer_id="offer-k",
                                  now=NOW))
        self.setUp()
        self.accepted("offer-u")
        self.session.settle_answer = {"kind": "who-knows"}
        self.refusing("the session's settlement answer",
                      lambda: worker_manager.settle_claim(
                          self.store, self.port, offer_id="offer-u", now=NOW))

    def test_a_minted_sequence_is_whole_because_the_column_is(self):
        """The store's own typing is the owner, and it is worth checking.

        `source_seq` is a STRICT INTEGER column, so the arithmetic that mints
        the next one cannot answer with anything else -- which is why there is
        no boundary here. What can be shown is that the guarantee is real: the
        column refuses a value that is not whole, from a writer that is not
        this build.
        """
        worker_manager.record_attempt(
            self.store, attempt_id="attempt-1", adapter_name="acp",
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE)
        worker_manager.observe(self.store, attempt_id="attempt-1",
                               axis="consent_runtime", value="running",
                               source={"incarnation": "worker", "seq": 1})
        with self.assertRaises(sqlite3.IntegrityError):
            self.corrupt("UPDATE observations SET source_seq = 9.5")
        minted = worker_manager.observe(
            self.store, attempt_id="attempt-1", axis="execution_runtime",
            value="running")
        self.assertEqual(type(minted["manager_seq"]), int)

    def test_an_observation_names_a_frozen_axis_and_one_of_its_values(self):
        """Two closed sets, and the second depends on the first.

        A vocabulary lists what an axis may SAY. Treating an unknown axis or an
        unknown value as something to record would let a caller invent a state
        machine the manager then reasons about.
        """
        self.recorded()()
        for what, call in [("an invented axis", dict(axis="mood",
                                                     value="running")),
                           ("another axis's value",
                            dict(axis="consent_runtime",
                                 value="start-requested")),
                           ("an invented value", dict(axis="output",
                                                      value="lovely"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.observe(self.store,
                                           attempt_id="attempt-1", **call)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))

    def test_a_source_sequence_counts_from_zero(self):
        """The sequence is half of a DURABLE IDENTITY, not a shape.

        `(attempt, incarnation, source_seq)` is what makes "the same
        observation again" answerable, so a sequence that is not a whole number
        is an identity nothing can be compared against.
        """
        self.recorded()()
        for what, seq in [("negative", -1), ("text", "1"),
                          ("a boolean", True)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.observe(
                        self.store, attempt_id="attempt-1",
                        axis="consent_runtime", value="running",
                        source={"incarnation": "worker", "seq": seq})
                self.assertIn("counts from zero", caught.exception.message)

    def test_activation_asks_the_authority_for_the_live_assignment(self):
        """Three things must agree, and the third is the authority's own answer.

        The session's binding and this attempt's committed claim agreeing is
        not enough -- any two of the three agreeing is exactly how a replayed
        activation gets in -- so the Work and the authority are forwarded and
        the answer is compared.
        """
        self.claimed()
        worker_manager.activate_assignment(
            self.store, self.port, attempt_id="attempt-1",
            expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                    "participant": WHO, "generation": 1})
        self.assertIn(("assignment_of", WORK), self.session.calls)
        self.setUp()
        self.claimed()
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.activate_assignment(
                self.store, self.port, attempt_id="attempt-1",
                expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                        "participant": WHO, "generation": 1})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("stale-assignment", "ended"))

    def test_a_settlement_rides_back_exactly_as_the_boundary_gave_it(self):
        """ORDERED, not done.

        The frozen host discarded the adapter's answer and reported
        `stopped: true` whenever the call RETURNED -- so an adapter answering
        `{stopped: false}` left the manager announcing a stopped runtime while
        its own axis said only `cancel-requested`. Reaching a boundary is not
        evidence of its effect, so both settlements ride back un-summarized and
        NOT normalized: "the boundary returned nothing" and "the boundary
        returned null" stay different answers.
        """
        for what, settlement in [("a refusal to stop", {"stopped": False}),
                                 ("nothing at all", None),
                                 ("prose", "ask again later")]:
            with self.subTest(what=what):
                self.setUp()
                self.attached()
                agent, adapter = FakeAgent(), FakeAdapter(self)
                agent.cancel = lambda operands: settlement
                adapter.stop = lambda operands: settlement
                answer = worker_manager.request_cancellation(
                    self.store, self.port, agent, adapter,
                    attempt_id="attempt-1")
                quiescence = answer["quiescence"]
                self.assertIs(quiescence["ordered"], True)
                self.assertEqual(quiescence["agent_settlement"], settlement)
                self.assertEqual(quiescence["runtime_settlement"], settlement)

    def test_cancellation_fences_before_it_orders_anything(self):
        """FENCE, THEN STOP -- and the operands the fence needs are forwarded.

        Until the generation is fenced the assignment is still live, so a
        runtime stopped first would be a worker torn out from under an
        assignment the authority still believes is executing.
        """
        agent, adapter = FakeAgent(), FakeAdapter(self)
        self.attached()
        answer = worker_manager.request_cancellation(
            self.store, self.port, agent, adapter, attempt_id="attempt-1",
            reason="operator asked")
        fenced = [operands for name, operands in self.session.calls
                  if name == "cancel"]
        self.assertEqual(len(fenced), 1)
        self.assertEqual(fenced[0]["reason"], "operator asked")
        self.assertTrue(fenced[0]["operation_id"].startswith("authority."))
        self.assertEqual(fenced[0]["expect"],
                         answer["intent"]["assignment"])
        self.assertIs(answer["quiescence"]["ordered"], True)
        self.assertEqual(len(agent.cancelled), 1)

    def test_a_fence_that_ended_another_assignment_is_refused(self):
        """The Work and the authority are the COMPARISON operands.

        A fence that ended somebody else's assignment is not this cancellation,
        however well-formed the answer is.
        """
        self.attached()
        self.session.fence_answer = dict(
            self.session.fence_answer,
            assignment={"work_ref": {"authority_uuid": "f" * 32,
                                     "work_id": WORK},
                        "participant": WHO, "generation": 1})
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.request_cancellation(
                self.store, self.port, FakeAgent(), FakeAdapter(self),
                attempt_id="attempt-1")
        self.assertIn("f" * 32, caught.exception.message)

    def test_an_unfenced_answer_stops_the_cancellation(self):
        """`fenced` is a closed value, and false is not a smaller yes."""
        self.attached()
        self.session.fence_answer = dict(self.session.fence_answer,
                                         fenced=False)
        agent = FakeAgent()
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.request_cancellation(
                self.store, self.port, agent, FakeAdapter(self),
                attempt_id="attempt-1")
        self.assertIn("leaves the assignment live", caught.exception.message)
        self.assertEqual(agent.cancelled, [])

    def test_the_catalogue_decides_one_membership_question(self):
        """Nothing to own, and the membership answer is what matters.

        A database holding objects and no `meta` is refused UNTOUCHED, which is
        the entire use this read is put to.
        """
        foreign = os.path.join(self.root, "foreign.sqlite3")
        beside = sqlite3.connect(foreign, isolation_level=None)
        try:
            beside.execute("CREATE TABLE somebody_elses (id INTEGER)")
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(foreign, incarnation="m", clock=lambda: NOW)
        self.assertIn("Nothing was changed", caught.exception.message)
        beside = sqlite3.connect(foreign, isolation_level=None)
        try:
            names = [row[0] for row in beside.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")]
        finally:
            beside.close()
        self.assertEqual(names, ["somebody_elses"])


class AnAdoptedRowIsAWholeRow(BoundaryCase):
    """The column SET is adopted as well as the column values.

    A mutation dropping the set check measured zero: every probe corrupted a
    VALUE, so nothing exercised the half that decides whether the row is one
    this build owns at all. A store written by a later build is not a store this
    one can reason about, and adopting its familiar-looking columns would be
    reading a stranger's row as our own.
    """

    def test_a_row_carrying_a_column_this_build_does_not_name_is_refused(self):
        self.accepted("offer-extra")
        self.corrupt("ALTER TABLE offers ADD COLUMN surprise TEXT")
        self.refusing("a persisted offer",
                      lambda: worker_manager.settle_claim(
                          self.store, self.port, offer_id="offer-extra",
                          now=NOW))

    def test_a_journal_row_carrying_an_unnamed_column_is_refused(self):
        self.corrupt("ALTER TABLE operations ADD COLUMN surprise TEXT")
        self.refusing("a persisted operation",
                      lambda: self.store.operation_record(
                          "profile.certify:runtime:reference"))

    def test_the_refusal_says_which_column_arrived(self):
        # Two readings of an unexpected column and both are alarming; a reader
        # of the refusal should at least learn which one it was.
        self.accepted("offer-name")
        self.corrupt("ALTER TABLE offers ADD COLUMN surprise TEXT")
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.settle_claim(self.store, self.port,
                                        offer_id="offer-name", now=NOW)
        self.assertIn("surprise", caught.exception.message)


class TheProjectionContractMatchesTheAuthorityItReads(BoundaryCase):
    """The contract is a claim about somebody else's answer, so it is checked
    against them.

    A mutation emptying the unread half measured zero, because the fake session
    answers the five members the manager reads and no more. That is the fake
    agreeing with the contract rather than the AUTHORITY agreeing with it -- and
    a closed contract that has never seen a real projection would refuse the
    first one it met.

    So the members are read out of the authority's own source. It is a sibling
    package in this distribution, and this is a test rather than an import: the
    manager still does not depend on the authority's module graph.
    """

    def authority_projection(self):
        core = (PACKAGE.parent / "authority" / "core.py")
        tree = ast.parse(core.read_text(encoding="utf-8"), str(core))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "project_work":
                for piece in ast.walk(node):
                    if isinstance(piece, ast.Return) \
                            and isinstance(piece.value, ast.Dict):
                        return sorted(key.value for key in piece.value.keys)
        raise AssertionError("the authority's projection was not found")

    def test_the_contract_names_exactly_what_the_authority_answers(self):
        from baton_v12.worker_manager.authority_port import (PROJECTION_READ,
                                                             PROJECTION_UNREAD)
        self.assertEqual(sorted(PROJECTION_READ + PROJECTION_UNREAD),
                         self.authority_projection())

    def test_a_whole_authority_projection_is_accepted(self):
        self.session._work = {member: None
                              for member in self.authority_projection()}
        self.session._work.update({"status": "open", "phase": "queued",
                                   "authority_uuid": UUID})
        self.assertEqual(self.issued("offer-full"), "offer-full")


class AnIdentityIsMoreThanAShape(BoundaryCase):
    """The properties exact POD does not establish.

    Review [P1]: exact POD and an exact member set are the SAFE REPRESENTATION
    of a document, not its field contract. Every case here is a well-formed
    document whose members mean something the manager cannot record.
    """

    def claiming(self, offer_id, **answer):
        self.accepted(offer_id)
        self.session.claim_answer = dict(self.session.claim_answer, **answer)
        return lambda: worker_manager.submit_claim(self.store, self.port,
                                                   offer_id=offer_id)

    def test_a_generation_outside_the_frozen_range_is_refused(self):
        """A whole number is not enough: §10.1 makes the space FINITE.

        A mutation keeping "is an integer" and dropping the range measured zero
        -- every case I had written was a generation that was not a number at
        all. Driving it turned up something better than a missing case: the
        frozen range is ALREADY owned, by the exact-POD rule that owns the
        document this member arrives in, and my range check was a second owner
        for one property. It is gone; this is the half that is this rule's.
        """
        for what, value in [("negative", -1),
                            ("a boolean, which equals 1", True)]:
            with self.subTest(what=what):
                self.setUp()
                self.refusing("the claim answer's generation",
                              self.claiming("offer-g", generation=value))

    def test_the_frozen_range_is_owned_where_the_document_is(self):
        # And the property is still enforced -- by ONE owner, one layer up.
        self.refusing("the claim answer's identity",
                      self.claiming("offer-big",
                                    generation=boundaries.MAX_SAFE_INTEGER + 1))

    def test_the_first_generation_the_range_allows_is_accepted(self):
        # The other half: a bound that refuses everything is not a bound.
        run = self.claiming("offer-ok",
                            generation=boundaries.MAX_SAFE_INTEGER)
        self.assertEqual(run()["state"], "claimed")

    def test_a_live_settlement_carrying_a_record_is_refused(self):
        """`live` is the answer that says nothing is decided.

        A mutation allowing a record beside it measured zero: every settlement
        case I had written supplied the authority's own `record: None`. A
        record beside `live` would be a decision nobody made, arriving on the
        one path whose whole point is that the manager writes nothing.
        """
        self.accepted("offer-lr")
        self.session.settle_answer = {"kind": "live",
                                      "record": {"reason": "r",
                                                 "disposition": "d"}}
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.settle_claim(self.store, self.port,
                                        offer_id="offer-lr", now=NOW)
        self.assertIn("a live settlement carries no record",
                      caught.exception.message)

    def test_a_sealed_refusal_is_more_than_four_member_names(self):
        """What makes a seal a seal is the CLOSED PAIRING.

        Mutations dropping the pairing, the message rule and the durable marker
        all measured zero: every case I had written spoiled the CATEGORY, which
        the first check catches. §9 says a category and a code mean something
        together -- `refused.precondition` and `policy.retention` carry different
        portable meanings and different retry policies -- so a pair this build
        cannot place is not one of its refusals, however well-formed its parts.
        """
        for what, sealed in [
                ("a code from another category",
                 '{"category": "policy", "code": "precondition",'
                 ' "message": "m", "durable": true}'),
                ("a message that is not text",
                 '{"category": "policy", "code": "retention",'
                 ' "message": 7, "durable": true}'),
                ("a seal that is not marked durable",
                 '{"category": "policy", "code": "retention",'
                 ' "message": "m", "durable": false}')]:
            with self.subTest(what=what):
                self.setUp()
                try:
                    self.store.transact(
                        "op-seal", "k",
                        worker_manager.manager_signature("k", {}),
                        lambda connection: (_ for _ in ()).throw(
                            ContractRefusal("policy", "retention", "held",
                                            durable=True)))
                except ContractRefusal:
                    pass
                self.corrupt("UPDATE operations SET refusal = ? "
                             "WHERE operation_id = 'op-seal'", sealed)
                self.refusing("a persisted operation",
                              lambda: self.store.operation_record("op-seal"))

    def test_the_declared_owner_checks_can_actually_fail(self):
        """Two guards with nothing to catch, handed something.

        Both measured as equivalences: every constructor exception names a site
        that exists, and every probe's fragment is part of its full label. The
        way to test a guard whose condition holds everywhere is to fabricate one
        where it does not.
        """
        sites = {site for _, site, _ in receiving_entries()}
        self.assertNotIn("nowhere.py:Invented.constructor", sites)
        fabricated = dict(CONSTRUCTED_BY,
                          invented="nowhere.py:Invented.constructor")
        self.assertEqual(
            [site for site in fabricated.values() if site not in sites],
            ["nowhere.py:Invented.constructor"])
        self.assertNotIn("'s generation", "the offer's expiry")
        # And the third: an exemption from probing must name an entry that is
        # owned, so "no probe" cannot become a way to retire an entry.
        invented = ("adopted", "nowhere.py:_read", "nothing")
        self.assertFalse(layer_labels(invented))
        self.assertEqual(
            [entry for entry in {**NO_PROBE, invented: "fabricated"}
             if not layer_labels(entry)], [invented])


class TheInstantRuleIsThreeProperties(BoundaryCase):
    """Shape, calendar and PADDING are three different refusals.

    A mutation dropping the grammar measured zero, because `strptime` rejects
    most malformed text on its own -- and it accepts `2026-8-24T0:0:0.1Z`, which
    is a real moment written without padding. That value parses, is a perfectly
    good instant, and SORTS WRONG: "2026-8-24..." orders after "2026-12-01...".
    """

    def test_a_real_instant_written_without_padding_is_refused(self):
        for what, value in [("a one-digit month", "2026-8-24T00:00:00.000Z"),
                            ("a one-digit hour", "2026-08-24T0:00:00.000Z"),
                            ("a short fraction", "2026-08-24T00:00:00.1Z"),
                            ("no fraction at all", "2026-08-24T00:00:00Z")]:
            with self.subTest(what=what):
                self.refusing("the current instant",
                              lambda: worker_manager.expire_overdue(
                                  self.store, value))

    def test_the_three_refusals_say_which_property_failed(self):
        for value, phrase in [(SURROGATE, "not encodable"),
                              ("2026-08-24T00:00:00Z", "grammar"),
                              (SHAPED_BUT_UNREAL, "names no moment")]:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ContractRefusal) as caught:
                    boundaries.instant(value, "an instant")
                self.assertIn(phrase, caught.exception.message)


class ClosedShapesAreClosedBothWays(BoundaryCase):
    """A contract that names a subset of what it accepts is a floor.

    Review [P1]: `document` rejected missing members and accepted every extra
    one, and `alternative` closed the vocabulary and left every variant's shape
    open -- so `{"kind": "committed"}` was a complete settlement and the offer
    advanced to `claimed` carrying a null assignment.
    """

    def test_a_document_refuses_a_member_its_contract_does_not_name(self):
        self.session._work = dict(self.session._work, unexpected="hello")
        self.refusing("the session's Work projection",
                      lambda: self.issued("offer-x"))

    def test_a_projection_missing_what_the_manager_reads_is_refused(self):
        for member in ("status", "phase", "handler", "gate", "authority_uuid"):
            with self.subTest(member=member):
                self.setUp()
                self.session._work = {key: value for key, value
                                      in self.session._work.items()
                                      if key != member}
                self.refusing("the session's Work projection",
                              lambda: self.issued("offer-y"))

    def test_every_settlement_variant_must_carry_its_own_members(self):
        for kind in ("live", "committed", "retired", "refused"):
            with self.subTest(kind=kind):
                self.setUp()
                self.accepted("offer-v")
                self.session.settle_answer = {"kind": kind}
                self.refusing("the session's settlement answer",
                              lambda: worker_manager.settle_claim(
                                  self.store, self.port, offer_id="offer-v",
                                  now=NOW))

    def test_a_committed_settlement_without_its_result_never_advances(self):
        """The defect the closed variant exists to stop, end to end."""
        self.accepted("offer-c")
        self.session.settle_answer = {"kind": "committed"}
        with self.assertRaises(ContractRefusal):
            worker_manager.settle_claim(self.store, self.port,
                                        offer_id="offer-c", now=NOW)
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            state = beside.execute(
                "SELECT state FROM offers WHERE offer_id = 'offer-c'"
            ).fetchone()[0]
        finally:
            beside.close()
        self.assertEqual(state, "accepted")


if __name__ == "__main__":
    unittest.main()
