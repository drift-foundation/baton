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
import functools
import json
import os
import pathlib
import shutil
import sqlite3
import tempfile
import types
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal
from baton_v12.contracts import digest as _contracts_digest
from baton_v12.worker_manager import (AuthorityPort, ControlStore, boundaries,
                                      certify_profile, documents, schema)

from baton_v12.worker_manager import attempts, lanes, workspaces

from .test_handshake import acp_profile
from .test_output import (AUTHORITY, COMPLETION, JOB, POLICY, OutputCase)
from .test_offers import (FakeSession, PRINCIPAL, PROFILE, ROUTE, SCOPE,
                          UUID, WHO, WORK, decision,
                          fake_claim_signature)

NOW = "2026-08-24T00:00:00.000Z"
SURROGATE = "\ud800"
# W19784: the contract record's own published vectors, so the input pair a
# witness composes is the one the finding published rather than one written to
# pass this file's own rules.
CONTRACT_VECTORS = (pathlib.Path(__file__).resolve().parents[4] / "work"
                    / "records" / "2026" / "08"
                    / "finding-v12-isolated-agent-workers" / "findings"
                    / "finding-v12-worker-contract" / "findings"
                    / "finding-worker-control-api-manifests" / "evidence"
                    / "vectors.json")
# W6629: two digests the intake probes carry, and neither is ever dereferenced
# -- which is the point of a policy consumed by identity.
# W19784 review [P0]: `compose_input_root` now takes the manager's OWN live
# identity. A probe drives it with the surrogate path, so these two only have
# to be well formed -- `_real` refuses the path as text before either is read.
OWNED_ASSIGNMENT = {"work_ref": {"authority_uuid": "43c55d4b1234567890abcdef12345678",
                                 "work_id": "43c55d4b-W1439"},
                    "participant": "baton.claude", "generation": 1}

# W16823: a sentinel that means "take this member out", so a probe can reach
# a document owner's member-set rule rather than the envelope's value rule.
_DROP = object()

RETENTION_POLICY = "sha256:" + "7" * 64
RECEIPT = "sha256:" + "6" * 64


class _Raising:
    """A sentinel the fixture adapter raises instead of answering, so a probe
    leaves its journalled request behind and settles nothing."""


class _ProbesButCannotBeAsked:
    """An adapter that can be looked at and not spoken to.

    W6627's contract names four operations and `_ask` proves both
    interrogations before it uses either, so the half that is missing decides
    which boundary the refusal names.
    """

    def cancel(self, operands):
        return {"acknowledged": True}

    def observe_session(self, reference):
        return {"kind": "absent", "provider_session_id": "provider-1"}

    def probe(self, request):
        return {"kind": "unreachable", "why": "not asked"}


class _Interrogating:
    """An adapter carrying all four operations, with the two interrogation
    answers a case may set."""

    def __init__(self, provider, probe=None, inquire=None):
        self._provider = provider
        self._probe = probe
        self._inquiry = inquire

    def cancel(self, operands):
        return {"acknowledged": True}

    def observe_session(self, reference):
        return {"kind": "present", "state": "ready",
                "provider_session_id": self._provider}

    def probe(self, request):
        if self._probe is _Raising:
            raise TimeoutError("the adapter never came back")
        if self._probe is not None:
            return self._probe
        return {"kind": "observed", "state": "ready",
                "provider_session_id": self._provider,
                "last_activity_at": NOW, "diagnostics": {}}

    def inquire(self, request):
        return self._inquiry or {"kind": "queued"}


class _Collecting:
    """The runtime adapter's collect, answering nothing.

    Every probe using it spoils an operand read BEFORE the adapter is called,
    so the answer never matters -- but an adapter missing the operation would
    be refused at the capability check and make the probe prove the wrong
    thing.
    """

    def collect(self, operands):
        return None


class _Custodian:
    """collect, retain and destroy, each answering what a probe needs.

    W43975 made a directory-custody seam mandatory at every ending's ENTRY, so
    an adapter without one is refused before the destroy observation these
    probes are about. Carrying it here keeps each probe reaching the boundary
    it NAMES rather than the capability check in front of it -- which is the
    same rule the probe gate applies to every other driver.
    """

    custodian_image_digest = "sha256:" + "c" * 64

    def normalize_directory(self, store, *, assignment_id, which):
        from baton_v12.worker_manager import custody

        return custody._answered(
            "normalize", 0,
            {"custody": "normalize", "entries": 0, "not_ours": 0,
             "running_as": [0, 0]}, None)

    def __init__(self, collected=None, destroyed=None):
        self._collected = collected
        self._destroyed = destroyed

    def collect(self, operands):
        return self._collected

    def retain(self, operands):
        return True

    def destroy(self, command):
        return self._destroyed


class _Sealing:
    """The runtime adapter's seal, answering nothing.

    Every probe using it spoils an operand that is read BEFORE the adapter is
    called, so the answer never matters -- but an adapter missing the operation
    would be refused at the capability check and make the probe prove the wrong
    thing.
    """

    def seal(self, operands):
        return None


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

    def probe(self, request):
        # W6627: the adapter contract now names `probe` and `inquire`. A fake
        # missing either is refused at the capability check, which would make
        # every case in this file fail for a reason it is not about.
        return {"kind": "unreachable", "why": "this fixture does not probe"}

    def inquire(self, request):
        return {"kind": "unreachable", "why": "this fixture does not inquire"}


class _HalfAnAgent:
    """An adapter carrying one of the operations the contract names.

    W6627 defined that contract for the first time: before it, `agent.cancel`
    was a call with nothing saying an adapter had to have it. The contract is
    four operations now, and this fake still carries exactly one.
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
                "_claim_signature", "adapter", "agent",
                # W6634: the credential provider. Trusted to be the
                # deployment's and NOT trusted to be correct, exactly like
                # `mint_bearer` -- so what it ANSWERS is an injected crossing
                # and gets an owner and a probe like any other.
                "credential_provider",
                # W43977: THE ENGINE'S OWN ANSWER. `EnginePort.__call__` is
                # where the deployment's injected runner answers, and until
                # this was named the universe could not discover that document
                # or the `status`, `stdout` and `stderr` it consumes at all --
                # so custody's listing, inspection, stop and removal paths all
                # crossed an injected boundary the inventory could not see.
                # Modelled once at the real crossing rather than once per
                # vector, which is where the rule already lives.
                "_run"}

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


# THE DISCOVERY PROJECTIONS BELOW ARE PURE AND MEMOISED, W54182. They read the
# manager package and nothing else -- no fixture, no store, no temporary
# directory -- so their answer is a property of the source tree and is the same
# every time it is asked for within one process. It used to be recomputed
# instead: `_sources` was a generator, so each of `receiving_entries`,
# `owning_validators`, `propagated_owners`, `columns_read` and `_crossings`
# re-walked the package and re-parsed all 21 modules between one and four times,
# and the probe driver asked for them once per probe. That is how a 21-module
# package reached 103,950 parses and 620 measured seconds in one test.
#
# THE DERIVED PROJECTIONS ARE IMMUTABLE VALUES -- a `frozenset`, or a
# `MappingProxyType` over `frozenset`s -- because a shared mutable projection is
# a way for one assertion to change what a later one is told. Their members are
# strings and tuples of strings, so handing the cached object out is safe.
#
# THE SOURCE SNAPSHOT IS NOT, AND SAYING OTHERWISE WAS WRONG. Review
# 2026-08-31T16:16:32Z [P2]: `_sources()` returns an immutable TUPLE whose
# members are `ast.Module` objects, and an AST node is mutable. Clearing one
# module's `tree.body` and recomputing a projection really does lose crossings
# the previous caller saw. What keeps the snapshot safe is therefore an
# INVARIANT this file owns rather than a property of the value: every walker
# here traverses with `ast.walk` and none of them assigns to a node.
#
# So the invariant is MEASURED instead of promised.
# `test_the_shared_trees_are_never_mutated_by_a_projection` fingerprints every
# tree, runs all five projections, and requires the fingerprints unchanged --
# and proves the fingerprint can tell, by mutating one tree and requiring it to
# notice. A comment asserting "nothing mutates these" is the kind of claim that
# is true until somebody writes the line that makes it false.


@functools.cache
def _sources():
    """The manager package, parsed ONCE per process, in one shared snapshot.

    THE TUPLE IS IMMUTABLE AND THE TREES IN IT ARE NOT. `ast` nodes are ordinary
    mutable objects, so this is a shared cache held safe by a rule rather than
    by a type: every walker in this file only READS -- `ast.walk`, attribute
    reads, `isinstance` -- and none of them assigns to a node or replaces a
    `body`. `test_the_shared_trees_are_never_mutated_by_a_projection` is what
    holds that rule to being true, and it fails if a projection starts editing
    what it was given.
    """
    return tuple(
        (source, ast.parse(source.read_text(encoding="utf-8"), str(source)))
        for source in sorted(PACKAGE.rglob("*.py"))
        if source.name not in (LAYER, "__init__.py"))


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


@functools.cache
def _helper_returns():
    """`_returned_origins` over the one source snapshot, computed once.

    Three projections need it and each used to run the four-pass fixpoint over
    a freshly parsed package of its own.
    """
    return types.MappingProxyType(dict(_returned_origins(_sources())))


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

    # TO A FIXED POINT, because `ast.walk` is BREADTH-FIRST and a binding can
    # depend on one the walk has not reached yet.
    #
    # W43977 [P0]: `EnginePort.__call__` assigns `answer` inside both arms of
    # an `if`, then joins with `taken = boundaries.document(answer, ...)` at
    # the top level. Breadth-first visits the JOIN first -- `answer` has no
    # origin yet -- so `taken` was bound to nothing and the engine's answer,
    # with the `status`, `stdout` and `stderr` this manager consumes, was
    # invisible to the universe. One more pass would have caught that one, and
    # a chain one link longer would have needed another; a fixed point needs
    # no guess about depth.
    #
    # It terminates because origins only ever GAIN names and each name's
    # origin is derived from names already bound, so the map is monotone over
    # a finite set of local names.
    while True:
        before = dict(origins)
        for piece in ast.walk(node):
            if isinstance(piece, ast.Assign):
                for target in piece.targets:
                    bind(target, _source(piece.value, origins, site, returns))
            elif isinstance(piece, (ast.For, ast.AsyncFor)):
                bind(piece.target, _source(piece.iter, origins, site, returns))
            elif isinstance(piece, ast.comprehension):
                bind(piece.target, _source(piece.iter, origins, site, returns))
        if origins == before:
            return origins


@functools.cache
def receiving_entries():
    """Every receiving trust-domain entry, from a structure no owner defines.

    A parameter nobody validates, a SQL read nobody adopts and a capability
    answer nobody owns all appear here. That is the whole difference from the
    two versions this replaces.
    """
    found = set()
    crossings = _crossings()
    _returns = _helper_returns()
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
    return frozenset(found)


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


@functools.cache
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
    return frozenset(found)


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


@functools.cache
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
    return types.MappingProxyType(found)


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


@functools.cache
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
    _returns = _helper_returns()
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
    return types.MappingProxyType(
        {site: frozenset(found) for site, found in owners.items()})


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


@functools.cache
def propagated_owners():
    """(helper site, kind, label) for every owner attributed to a caller.

    A shared owner is written once and attributed to each crossing that reaches
    it, so its own site holds calls whose subject is a bare parameter. Those are
    not orphans -- they are the same calls, seen where they were written.
    """
    found = set()
    _returns = _helper_returns()
    for source, tree in _sources():
        helpers = _helpers(tree, source.name)
        returns = _returns
        for site, node in _functions(tree, source.name):
            origins = _origins(node, site, returns)
            for where, helper, inside in _delegations(node, origins, helpers):
                for kind, label, _ in _calls_in(helper, inside, site):
                    found.add((where, kind, label))
    return frozenset(found)


# EVERY MEMOISED PROJECTION, NAMED ONCE. W54182's boundedness regression clears
# and counts exactly these, so a cached projection missing from this tuple is
# one the check cannot see -- and a cache nobody checks is how the repeated
# package walk came back the first time.
MEMOISED = (_sources, _helper_returns, _crossings, receiving_entries,
            columns_read, owning_validators, propagated_owners)


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
    # -- W43977: the engine's answer, member by member -----------------------
    #
    # The ENVELOPE is layer-owned at the port -- `boundaries.document` names
    # the three members required -- and each MEMBER's rule lives in a private
    # owner beside it. Stated rather than layer-owned because neither rule is
    # a boundary KIND and neither could honestly become one: an exit status is
    # a whole number that may be ZERO, and an engine stream is text that may
    # be EMPTY, which is exactly what a quiet engine writes. `boundaries.text`
    # and `boundaries.injected` refuse both of those, so naming either here
    # would make the rule wrong to satisfy the table -- and a round of this
    # Work proved it, with thirty failures and ninety-nine errors in
    # `test_oci`.
    ("injected", "oci.py:EnginePort.__call__", "run.status"):
        "owned by `oci.py:_status`: a whole number and never a bool, and zero "
        "is the ordinary answer rather than an absence",
    ("injected", "oci.py:EnginePort.__call__", "run.stdout"):
        "owned by `oci.py:_stream`: storable text that MAY be empty, because "
        "nothing on this stream is what a quiet engine writes",
    ("injected", "oci.py:EnginePort.__call__", "run.stderr"): "the same",
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
        "W33937: the rule depends on the decision the operand arrives with. An "
        "ACCEPTANCE proves possession, by constant-time comparison against the "
        "stored verifier; a DECLINE carries no bearer at all, so any carried "
        "value -- including the empty string and `None` -- is integrity/schema "
        "and the absence is a module-private sentinel the operand defaults to",
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
    # DIAGNOSED, not assumed: these two are owned by the FROZEN gitSource
    # FRAGMENT, which item 2's correction put ahead of every member read. A
    # malformed revision refuses with "'base_revision'.'hex' breaks pattern"
    # before `_pinned` is reached, so delegating them there named an owner that
    # never sees them.
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
    # -- W6627: publishing one model answer, which is the manager's act ------
    ("caller", "authority_port.py:AuthorityPort.publish_answer", "work_ref"):
        "the Work this manager already fixed and adopted; forwarded to the "
        "authority, which owns its own operands",
    ("caller", "authority_port.py:AuthorityPort.publish_answer",
     "operation_id"):
        "the interrogation identity the manager minted and journalled, "
        "forwarded to the authority",
    ("caller", "authority_port.py:AuthorityPort.publish_answer", "body"):
        "the answer, owned where it entered as bounded storable text and "
        "forwarded intact; re-owning prose here would be the blanket "
        "revalidation 4bz refuses",
    ("injected", "attempts.py:_order_quiescence", "agent.cancel"):
        "passed through UNINTERPRETED: reaching a boundary is not evidence of "
        "its effect, and the manager has no basis for turning a settlement "
        "into a fact about the world. Positive quiescence arrives as an "
        "OBSERVATION or not at all",
    ("injected", "attempts.py:_order_quiescence", "adapter.stop"):
        "the same: ORDERED, not done",
    # -- W6629: intake, retention and cleanup --------------------------------
    #
    # The same rule the other closed constructors follow: `**members` is not a
    # caller's document to own, it is the member SET this build states, and
    # `_emit` refuses one that does not match the contract.
    # -- W6634: the sealing half, called by the adapter that owns its operands
    #
    # `sealing.py` is a PURE FUNCTION OVER DATA and its caller is the adapter
    # in the same package. Every operand here is a value that adapter proved
    # ONCE and holds: `roots` was resolved by `_roots` at construction,
    # `declared` by `sealing.declared_outputs` at construction, `identity` by
    # `_identity`, and the request's members by the document owner inside
    # `sealed_result` itself. Re-proving them at this internal call is the
    # blanket revalidation 4bz forbids -- the crossing already happened, once,
    # where the value entered the adapter.
    # -- W6634: the assignment-scoped credential lifecycle -------------------
    #
    # THE THREE SHAPES BELOW ARE NOT BOUNDARY KINDS, which is exactly why they
    # are stated rather than probed. A LIST is not a crossing -- what crosses
    # is its members, and each has its own owner one line down. A CLOSED
    # VOCABULARY is a comparison against this module's own constant. And a
    # DELIVERY is an object this manager built: what proves it is that it IS
    # one, because everything inside it was owned when it was constructed.
    ("caller", "credentials.py:resolved_delivery", "slots"):
        "credentials.py:_authorized_slots for the shape and the bound, then "
        "credentials.slot_name for every member -- a slot name becomes both a "
        "filename and a container path segment, so its grammar is a "
        "containment rule rather than a style",
    ("caller", "credentials.py:Delivery.__init__", "state"):
        "credentials.LIFECYCLE_STATES, the module's own closed vocabulary; a "
        "delivery is live, adopted or torn-down and nothing else",
    ("caller", "credentials.py:Delivery.__init__", "bearers"):
        "the KEYS by credentials.slot_name and the whole by shape. The VALUES "
        "are deliberately not named in any refusal: they are the one thing "
        "§13 exists to keep off a durable surface, and a diagnostic is one",
    ("caller", "credentials.py:CredentialHome.tear_down", "delivery"):
        "proved to BE a credentials.Delivery, whose constructor owned every "
        "member; teardown acts on an object this manager materialized rather "
        "than on a document a caller composed",
    # -- W26291: the worker's launch document --------------------------------
    ("caller", "launch.py:LaunchDelivery.__init__", "attempt_id"):
        "constructed only by launch.materialize, which owned every one of "
        "these before a byte was written -- this object is what the manager "
        "MADE, not a document a caller composed, and the doors that receive it "
        "prove its kind rather than re-walking its members",
    ("caller", "launch.py:LaunchDelivery.__init__", "root"): "the same",
    ("caller", "launch.py:LaunchDelivery.__init__", "place"): "the same",
    ("caller", "launch.py:LaunchDelivery.__init__", "document"): "the same",
    ("caller", "launch.py:discard", "root"):
        "a root this module created and froze. Removal is by name inside a "
        "directory this module made and never a walk of something else could "
        "have replaced, and absence is the state asked for rather than a "
        "refusal -- so there is nothing here a caller decides",
    ("caller", "oci.py:OciAdapter.__init__", "launch_delivery"):
        "proved to BE a launch.LaunchDelivery, whose materializer owned every "
        "member; the adapter composes one read-only mount out of an object "
        "this manager made rather than out of a document a caller composed",
    ("caller", "oci.py:OciAdapter.__init__", "credential_delivery"):
        "the same -- and this adapter deliberately does not resolve "
        "credentials at all: the assignment names slots, the trusted profile "
        "maps them, and the MANAGER materializes. An adapter that called the "
        "provider itself would put a credential decision inside the component "
        "whose whole contract is that it decides nothing",
    ("caller", "sealing.py:sealed_result", "roots"):
        "resolved by oci.py:_roots at adapter construction",
    ("caller", "sealing.py:sealed_result", "roots.workspace"): "the same",
    ("caller", "sealing.py:sealed_result", "declared"):
        "proved by sealing.declared_outputs at adapter construction",
    ("caller", "sealing.py:sealed_result", "identity"):
        "resolved by oci.py:_identity at adapter construction",
    ("caller", "sealing.py:sealed_result", "identity.policy_digest"):
        "the same",
    ("caller", "sealing.py:sealed_result", "input_manifest_digest"):
        "the assignment's own input manifest digest, held by the adapter and "
        "carried into the result unread",
    ("caller", "sealing.py:collected_result", "custody"):
        "derived by the adapter from its own assignment roots; collection "
        "reads what this manager took custody OF rather than the workspace, "
        "which is the worker's and may have moved",
    ("caller", "sealing.py:sealed_result", "custody"): "the same",
    ("caller", "oci.py:OciAdapter.collect", "operands.attempt_id"):
        "owned by the collect-request document owner in "
        "sealing.collected_result",
    ("caller", "sealing.py:collected_result", "declared"): "the same",
    ("caller", "oci.py:OciAdapter.seal", "request.attempt_id"):
        "owned by the freeze-request document owner in sealing.sealed_result",
    ("caller", "oci.py:OciAdapter.seal", "request"):
        "owned by the freeze-request document owner in sealing.sealed_result, "
        "which is the one place this request's members are proved",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment"): "the same",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.generation"):
        "the same",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.participant"):
        "the same",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.work_ref"):
        "the same",
    ("caller", "oci.py:OciAdapter.seal",
     "request.assignment.work_ref.authority_uuid"): "the same",
    ("caller", "oci.py:OciAdapter.seal",
     "request.assignment.work_ref.work_id"): "the same",
    ("caller", "oci.py:OciAdapter.collect", "operands"):
        "owned by the collect-request document owner in "
        "sealing.collected_result",
    ("caller", "oci.py:OciAdapter.__init__", "outputs"):
        "sealing.declared_outputs, at construction -- which is the point: "
        "what may be collected is the assignment's statement rather than a "
        "per-call argument",
    ("caller", "oci.py:OciAdapter.__init__", "input_manifest_digest"):
        "carried into the sealed result unread; the manifest it names is the "
        "manager's to validate and this adapter never opens it",
    # W6634 fifth review: `start` compares the mounted delivery's attempt with
    # the runtime's own label. The label document is owned one line earlier by
    # `documents.runtime_labels` through `oci._labels`, so this member arrives
    # proved; what the comparison adds is a RELATIONSHIP between two already
    # owned values, which is a semantic rule rather than a second crossing.
    ("caller", "oci.py:OciAdapter.start", "labels.runtime_attempt_id"):
        "oci._labels -> documents.runtime_labels, at the top of the same "
        "operation; the comparison against the delivery's attempt is a rule "
        "over two owned values",
    ("caller", "documents.py:collect_requested", "members"):
        "documents._emit against this document's own contract: exactly these "
        "members, and nothing about their values",
    ("caller", "documents.py:intake_artifact", "members"): "the same",
    ("caller", "documents.py:intake_receipt", "members"): "the same",
    ("caller", "documents.py:retention", "members"): "the same",
    ("caller", "documents.py:retention_decided", "members"): "the same",
    ("caller", "documents.py:cleanup_blocked", "members"): "the same",
    ("caller", "documents.py:cleanup_unsettled", "members"): "the same",
    ("caller", "documents.py:cleanup_settled", "members"): "the same",
    # W6629 review [P1]: the two frozen COMMANDS this manager issues, closed
    # by the same `_emit` rule as every other outbound constructor.
    ("caller", "documents.py:retain_command", "members"): "the same",
    ("caller", "documents.py:destroy_command", "members"): "the same",
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
    # W61984: the already-quiescent finalization's two documents.
    ("caller", "documents.py:finalize_intent", "members"): "the same",
    ("caller", "documents.py:attempt_finalized", "members"): "the same",
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
    # -- W6627: the operator interrogation split -----------------------------
    ("caller", "documents.py:interrogation_requested", "members"):
        "documents.py:_emit, against this document's entry in CONTRACTS",
    ("caller", "documents.py:interrogation", "members"): "the same",
    # The optional member, OMITTED rather than nulled when a probe never
    # observed anything -- `_emit` refuses a member CONTRACTS does not name and
    # refuses a required one that is missing, so absence is a shape decision it
    # owns rather than a value this constructor invents.
    ("caller", "documents.py:interrogation", "members.observation"):
        "documents.py:_emit, against this document's entry in CONTRACTS: an "
        "optional member is absent or present, never present-and-empty",
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
    # -- W6628: the output freeze and the sealed receiver --------------------
    #
    # A MANIFEST IS OWNED BY THE CONTRACTS LAYER'S OWN COMPOSITE, which is a
    # different owner from `boundaries` and a stronger one: schema first, then
    # the digest recomputed over the document's own canonical bytes, then §12's
    # semantics. Owning the envelope here as well would be the blanket
    # revalidation 4bz forbids, and it would answer a weaker question than the
    # one already being answered.
    ("caller", "manifests.py:retain_manifest", "document"):
        "contracts.check_manifest_structure, against the named definition: "
        "schema, then the self-identifying digest, then §12's semantics",
    ("caller", "output.py:record_frozen_result", "sealed"):
        "the same, against resultManifest -- and then bound to THIS attempt, "
        "which is the half a validator cannot know",
    # -- W19784: the two manager-authored `/input/` documents ----------------
    #
    # THE SAME OWNER, and here it answers a question no single-document
    # validator can: `contracts.check_input_pair` proves each document against
    # its own definition AND then holds the two against each other -- one
    # Work, the assignment minted against that exact input digest, one policy
    # and one runtime profile. Owning either envelope again here would be the
    # blanket revalidation 4bz forbids, and it would answer the weaker of the
    # two questions.
    ("caller", "workspaces.py:compose_input_root", "input_manifest"):
        "contracts.check_input_pair, against inputManifest and then against "
        "the assignment manifest beside it",
    ("caller", "workspaces.py:compose_input_root", "assignment_manifest"):
        "contracts.check_input_pair, against assignmentManifest and then "
        "against the input manifest beside it",
    ("injected", "output.py:request_freeze", "adapter.seal"):
        "what the adapter answers is a sealed result and is owned as one where "
        "it arrives, by `record_frozen_result`; an adapter's account of its "
        "own success decides nothing here",
    # -- W6629: intake, retention and cleanup --------------------------------
    ("injected", "intake.py:request_intake", "adapter.collect"):
        "what the adapter answers is a collection observation and is owned as "
        "one where it arrives, by `record_intake` -- which then compares every "
        "artifact against what the freeze recorded, so nothing in the "
        "adapter's account of its own success is adopted",
    # A LIST, and `boundaries` has no list kind because a list is not a
    # boundary: what crosses is the MEMBERS. The contracts layer's `own` takes
    # the fresh built-in copy, the shape is proved here, and every member is
    # owned as an identity -- which is what the entries below `chosen` prove
    # one at a time.
    ("caller", "intake.py:decide_retention", "artifact_ids"):
        "contracts.own for the fresh copy and the shape, then "
        "boundaries.identity on every member",
    # W6629 review [P1]: the artifact set and the disposition became part of
    # the RETAIN IDENTITY, so this exported derivation receives them too and
    # owns them by the same rules as the door above -- `intake.py:_chosen` for
    # the set, written once because the identity and the command body must
    # name the same canonical answer, and `intake.py:_disposition` for the
    # closed three.
    ("caller", "intake.py:retain_operation", "artifact_ids"):
        "intake.py:_chosen -- contracts.own for the fresh copy and the shape, "
        "then boundaries.identity on every member",
    ("caller", "intake.py:retain_operation", "disposition"):
        "intake.py:_disposition, the frozen three established as text in the "
        "same expression",
    # AND THE COMMAND THIS MANAGER NOW ISSUES. The adapter's answer to
    # `output.retain` is DISCARDED: what the material's disposition is was
    # decided here and committed to the journal, so there is nothing in the
    # reply to own.
    ("injected", "intake.py:decide_retention", "adapter.retain"):
        "nothing is read from it -- the answer is discarded, and the decision "
        "this command carries is the manager's own committed one",
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
    # -- W6627: the operator interrogation split -----------------------------
    ("caller", "interrogation.py:probe", "session_epoch"):
        "posture_slots.py:_epoch, the frozen positiveInt: one membership "
        "question with its type established in the same expression",
    ("caller", "interrogation.py:inquire", "session_epoch"): "the same",
    ("caller", "interrogation.py:interrogations_of", "session_epoch"):
        "the same",
    # THE DISCRIMINATORS of two closed alternatives, proved by
    # `boundaries.alternative` before any member of the variant they name is
    # read.
    ("injected", "interrogation.py:probe", "agent.probe.kind"):
        "boundaries.alternative's discriminator, proved before any member of "
        "the variant it names is read",
    ("injected", "interrogation.py:inquire", "agent.inquire.kind"):
        "the same, for the acknowledgement set",
    # -- W6632: the constrained OCI adapter core -----------------------------
    #
    # THE ENVELOPE IS ITERATED, NOT READ. `mounts` is a sequence this adapter
    # walks; every mount inside it is owned as a document, and the sequence
    # itself is never indexed, measured or branched on. A boundary on the
    # container would be a boundary on nothing.
    ("caller", "oci.py:run_vector", "mounts"):
        "iterated, never read: `_mounts` owns each mount as a document and "
        "this adapter never indexes, measures or branches on the sequence",
    ("caller", "oci.py:OciAdapter.__init__", "mounts"): "the same",
    # A YES OR A NO, decided by `type(...) is bool` rather than by a boundary
    # helper. The domain has no two-valued rule and inventing one for a single
    # field would put a helper on the package's surface that answers a question
    # `type` already answers exactly.
    ("caller", "oci.py:run_vector", "mounts.writable"):
        "`type(value) is bool`: an exact two-valued rule, and a truthy "
        "substitute is refused rather than read as yes",
    # A POSITIVE WHOLE NUMBER OF SECONDS, for the same reason: `type(...) is
    # int` with `bool` excluded and a range, written where it is used.
    ("caller", "oci.py:stop_vector", "seconds"):
        "an exact positive whole number, with `bool` excluded because it is "
        "an int and a stop timeout of `True` is not one second",
    # NEVER TRUSTED, ONLY COMPARED. The engine's `Running` member is matched
    # against the two exact singletons and anything else -- absent, a string,
    # a number, `None` -- falls through to `uncertain`. A manager that treated
    # confusion as death would release an assignment whose worker is running,
    # so this field cannot refuse and must not be owned as though it could.
    ("caller", "oci.py:OciAdapter.observe", "document.Running"):
        "compared with `is True` / `is False` and anything else answers "
        "`uncertain`; this read cannot refuse, because confusion is not death",
    # -- W39666: the worker-entry transport's composite operands -------------
    #
    # EACH OF THESE IS A SEQUENCE WHOSE MEMBERS ARE LAYER-OWNED AND WHOSE
    # SHAPE IS NOT. The per-member `boundaries.*` call sits inside a `for`, so
    # the inventory attributes it to the loop variable rather than to the
    # operand -- correctly, because the container rule is genuinely a second
    # rule. Stating the owner is the honest description: the site owns the
    # sequence shape, its cardinality and its members, and the label on any one
    # member would not be the whole of it.
    ("caller", "oci.py:exec_vector", "program"):
        "a composite owner at the site: `list`/`tuple` and nothing "
        "that merely iterates, non-empty, at most MAX_PROGRAM_WORDS, "
        "and every word held "
        "to `boundaries.text` under `an exec program word`",
    ("caller", "worker_entry.py:converse", "operations"):
        "a composite owner at the site: `list`/`tuple` and nothing "
        "that merely iterates, non-empty, and every member in the "
        "closed OPERATIONS "
        "vocabulary",
    ("caller", "worker_entry.py:converse", "operation_ids"):
        "a composite owner at the site: `list`/`tuple` and nothing "
        "that merely iterates, one per operation, each held to "
        "`boundaries.identity` under "
        "`a worker-entry operation identity` and to MAX_IDENTITY, and all "
        "distinct because the worker consumes each once per session",
    ("caller", "worker_entry.py:converse", "program"):
        "forwarded to `oci.py:exec_vector`, whose own composite owner is "
        "stated above; a delegation cannot name it because the rule there is "
        "not a layer label either",
    # A POSITIVE WHOLE NUMBER, owned at the port that hands it to the world,
    # exactly as `oci.py:stop_vector`'s is. `ChannelPort.__call__` is where the
    # bound becomes a real timeout, and a rule that lived here instead would be
    # a second copy of it.
    ("caller", "worker_entry.py:converse", "seconds"):
        "owned by `worker_entry.py:ChannelPort.__call__`: an exact positive "
        "whole number with `bool` excluded, checked where the bound is handed "
        "to the channel rather than where it was passed through",
    # ALREADY PROVED, ONE FRAME EARLIER. `_Reader` is private and only ever
    # receives the channel `ChannelPort.__call__` just held to CHANNEL_MEMBERS,
    # so a boundary call here would re-ask a question this package answered --
    # and would answer it at a site no caller can reach.
    ("caller", "worker_entry.py:_Reader.__init__", "channel"):
        "an internal value already held to CHANNEL_MEMBERS by "
        "`worker_entry.py:ChannelPort.__call__`; nothing outside this module "
        "constructs a `_Reader`",
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
    ("adopted", "output.py:frozen_output_of", "output_artifacts.bytes"):
        "the same: an artifact byte count SQLite will not let a writer spoil",
    ("adopted", "output.py:frozen_output_of", "outputs.runtime_attempt_id"):
        "the one read of this table SELECTS BY this column, so a spoiled value "
        "makes the row unfindable and a probe would prove absence rather than "
        "the rule; the contract still owns it for any later reader",
    ("adopted", "attempts.py:_attempts", "attempts.assignment_generation"):
        "the same: a generation column SQLite will not let a writer spoil",
    # W35557: THE ATTEMPT TABLE'S LOOKUP KEY, at each of the three sites that
    # adopt a row from it. Every one of them selects
    # `WHERE runtime_attempt_id = ?`, so a spoiled value is not a malformed row
    # this build adopts -- it is a row the query does not return, and the
    # caller receives "no runtime attempt", which is a different boundary
    # answering a different question. No reader of this table finds a row by
    # anything else, so there is nothing to drive the probe with. The same
    # exemption `outputs` and `intakes` already carry, for the same reason and
    # in the same words.
    # ONE ENTRY, NOT THREE. I declared the same exemption at all three sites
    # that adopt this row, and `test_every_unprobed_entry_is_a_real_owned_entry`
    # refused two of them: the inventory attributes this column's crossing to
    # `attempts.py:_attempts` alone, so exemptions at the other two named
    # nothing. That guard exists precisely so "no probe" cannot become a way to
    # retire an entry by declaring it, and it caught me trying.
    ("adopted", "attempts.py:_attempts", "attempts.runtime_attempt_id"):
        "the one read of this table SELECTS BY this column, so a spoiled value "
        "makes the row unfindable and a probe would prove absence rather than "
        "the rule; the contract still owns it for any later reader",
    ("adopted", "interrogation.py:_row", "interrogations.session_epoch"):
        "the same: a session epoch column SQLite will not let a writer spoil",
    # -- W6629: intake, retention and cleanup --------------------------------
    ("adopted", "intake.py:intake_receipt_of", "intake_artifacts.bytes"):
        "the same: an artifact byte count SQLite will not let a writer spoil",
    ("adopted", "intake.py:intake_receipt_of", "intakes.runtime_attempt_id"):
        "the one read of this table SELECTS BY this column, so a spoiled value "
        "makes the row unfindable and a probe would prove absence rather than "
        "the rule; the contract still owns it for any later reader",
    # -- W26294 re-review [P0]: a refusal DELIBERATELY ABSORBED ---------------
    #
    # These two owners still run and still decide what the adapter answered.
    # What changed is where their refusal goes: an observation this build
    # cannot read is now a durable `uncertain` rather than an exception, and a
    # probe asserting that the refusal ESCAPES would be asserting the exact
    # defect the correction removed -- a failed observation leaving the axis at
    # whatever it said before, including `running`.
    #
    # The rule is covered where the behaviour actually is: `test_attempts`'s
    # `test_an_answer_that_is_not_a_document_is_uncertain_and_says_so` requires
    # the durable state to be `uncertain` and the EXACT reason to name what was
    # wrong, which is what tells the document rule from the member rule.
    ("injected", "attempts.py:_observed", "adapter.observe.state"):
        "the refusal is absorbed into a durable `uncertain` observation by "
        "design; test_attempts asserts the state and the exact reason instead",
    ("injected", "attempts.py:_observed", "adapter.observe.why"):
        "the same",
}

DELEGATED = {
    # -- W6632: the constrained OCI adapter core -----------------------------
    #
    # Every public vector and the adapter itself share the same private owners,
    # which is what keeps one rule one rule: `_engine` decides which engines
    # this adapter speaks, `_labels` holds the frozen label document, `_roots`
    # holds the assignment's own roots and the posture that reads them, and
    # `_mounts` owns each mount. Owning them at six call sites instead would be
    # how a rule ends up applied at five of them.
    ("caller", "oci.py:run_vector", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:stop_vector", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:list_vector", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:inspect_vector", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:destroy_vector", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:OciAdapter.__init__", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "oci.py:run_vector", "labels"):
        ("oci.py:_labels", "caller:labels"),
    ("caller", "oci.py:list_vector", "labels"):
        ("oci.py:_labels", "caller:labels"),
    ("caller", "oci.py:run_vector", "assignment_roots"):
        ("oci.py:_roots", "caller:assignment_roots"),
    ("caller", "oci.py:OciAdapter.__init__", "assignment_roots"):
        ("oci.py:_roots", "caller:assignment_roots"),
    ("caller", "oci.py:run_vector", "posture"):
        ("oci.py:_roots", "caller:posture"),
    ("caller", "oci.py:OciAdapter.__init__", "posture"):
        ("oci.py:_roots", "caller:posture"),
    ("caller", "oci.py:run_vector", "mounts.source"):
        ("oci.py:canonical_source", "caller:place"),
    # W19784 third review [P1]: a target's spelling rule left `_mounts` and
    # became `canonical_target`, beside the source rule it had always been the
    # twin of. It moved because the manager's pre-journal check was a
    # PARAPHRASE of it and disagreed exactly where it cost most; one rule with
    # one owner is what stops that recurring. The label the entry answers to
    # moves with the owner -- `a container path`, which is what the site now
    # writes, and which says the thing the rule is actually about: a target is
    # never resolved against THIS host.
    ("caller", "oci.py:run_vector", "mounts.target"):
        ("oci.py:canonical_target", "caller:place"),
    # W6634: the credential mounts, whose owner is SEPARATE from `_mounts` on
    # purpose. `_mounts` admits a source because this manager created the
    # assignment root it lives under, and a credential is not assignment
    # material -- so every target is proved an entry of the fixed
    # `/run/baton/credentials` root instead.
    # W26291: the launch document's three values share ONE PRIVATE OWNER
    # under one literal label. `launch._value` states the rule -- bounded
    # non-empty text, a per-member ceiling, and no NUL -- and both the
    # authoring function and the materializer are attributed to it, which is
    # what keeps one rule one rule rather than three copies of it.
    ("caller", "launch.py:launch_document", "session"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:launch_document", "contract"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:launch_document", "role"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:materialize", "session"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:materialize", "contract"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:materialize", "role"):
        ("launch.py:_value", "caller:given"),
    ("caller", "oci.py:run_vector", "credentials_delivered"):
        ("oci.py:_credential_mounts", "caller:pairs"),
    # W26291: the same shape for the launch document. The typed capability
    # crosses to the ADAPTER; what reaches this argv composer is the pair that
    # capability answered with, owned by one private site exactly as a
    # credential delivery's pairs are.
    ("caller", "oci.py:run_vector", "launch_delivered"):
        ("oci.py:_launch_mount", "caller:pair"),
    ("caller", "oci.py:OciAdapter.__init__", "run"):
        ("oci.py:EnginePort.__init__", "caller:run"),
    # -- W43977: the custody acts, owned where each rule actually lives -------
    #
    # `custody_act` is a COMPOSER: it hands every operand to the private
    # composer that owns it and then to the engine port, and owning them again
    # at this entry would be a second spelling of five rules. The delegates
    # below are the sites that refuse, and each is named rather than implied.
    #
    # `_custody_vector` performs the durable lookup and the argv composition in
    # ONE act -- eleven review rounds went into removing the interval between
    # them -- so it is also where the engine, the image identity, the verb, the
    # attempt and the root kind are held.
    ("caller", "custody.py:custody_act", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "custody.py:custody_act", "run"):
        ("oci.py:EnginePort.__init__", "caller:run"),
    ("caller", "custody.py:custody_act", "operation"):
        ("custody.py:check_custody_operation", "caller:operation"),
    ("caller", "custody.py:custody_act", "which"):
        ("custody.py:check_custody_root", "caller:which"),
    ("caller", "custody.py:custody_act", "assignment_id"):
        ("custody.py:_derived_root", "caller:assignment_id"),
    ("caller", "custody.py:custody_act", "image_digest"):
        ("custody.py:_custody_vector", "caller:image_digest"),
    # The two public composition entries hold the attempt and the capability
    # themselves; the root kind is the one rule they share with the act, and
    # W43977 gave it a single named owner rather than the three inline copies
    # it had -- which is the same shape the verb has had since W36540.
    ("caller", "custody.py:normalize_directory", "which"):
        ("custody.py:check_custody_root", "caller:which"),
    ("caller", "custody.py:adopted_directory_custody", "which"):
        ("custody.py:check_custody_root", "caller:which"),
    # -- W47225: the launch delivery a restarted process adopts ---------------
    #
    # Adoption AUTHORS what this component would have written, through the same
    # `launch_document` that wrote it, and requires the canonical bytes to
    # match. So the three values it is given are owned exactly where the
    # writing side owns them -- which is the whole reason adoption reuses the
    # authoring owner instead of re-implementing its rules.
    ("caller", "launch.py:adopt", "session"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:adopt", "contract"):
        ("launch.py:_value", "caller:given"),
    ("caller", "launch.py:adopt", "role"):
        ("launch.py:_value", "caller:given"),
    # The ONE resolved identity a delivery is made under, owned once at
    # construction so the started image and the reconciliation labels are one
    # account rather than two.
    ("caller", "oci.py:OciAdapter.__init__", "identity"):
        ("oci.py:_identity", "caller:identity"),
    # -- W6627: the operator interrogation split -----------------------------
    #
    # `probe` and `inquire` are the two halves of one act and share `_ask`,
    # which binds the session, journals the request and only then reaches the
    # adapter. Owning their operands there rather than twice is what keeps the
    # two operations one rule.
    ("caller", "interrogation.py:probe", "attempt_id"):
        ("interrogation.py:_ask", "caller:attempt_id"),
    ("caller", "interrogation.py:inquire", "attempt_id"):
        ("interrogation.py:_ask", "caller:attempt_id"),
    ("caller", "interrogation.py:probe", "operation_id"):
        ("interrogation.py:_ask", "caller:operation_id"),
    ("caller", "interrogation.py:inquire", "operation_id"):
        ("interrogation.py:_ask", "caller:operation_id"),
    ("caller", "interrogation.py:probe", "deadline_seconds"):
        ("interrogation.py:_ask", "caller:deadline_seconds"),
    ("caller", "interrogation.py:inquire", "deadline_seconds"):
        ("interrogation.py:_ask", "caller:deadline_seconds"),
    ("caller", "interrogation.py:probe", "agent"):
        ("interrogation.py:_ask", "caller:agent"),
    ("caller", "interrogation.py:inquire", "agent"):
        ("interrogation.py:_ask", "caller:agent"),
    ("caller", "interrogation.py:inquire", "question"):
        ("interrogation.py:_ask", "caller:question"),
    ("caller", "interrogation.py:probe", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "interrogation.py:inquire", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    ("caller", "interrogation.py:interrogations_of", "posture"):
        ("posture_slots.py:_posture", "caller:posture"),
    # W6627 re-review [P1]: the probe observation's members are owned before
    # any of them is returned or persisted. `_diagnostics` is where the
    # provider's free-form report becomes an exact bounded document.
    ("injected", "interrogation.py:probe", "agent.probe.diagnostics"):
        ("interrogation.py:_diagnostics", "caller:given"),
    # -- W6628: the output freeze and the sealed receiver --------------------
    #
    # TWO SHARED OWNERS, each written once. The kind a retained document must
    # be is the same question at both ends of the retention, and a declared
    # disposition is the same question wherever it is declared.
    ("caller", "manifests.py:retain_manifest", "definition"):
        ("manifests.py:_definition", "caller:definition"),
    ("caller", "manifests.py:load_manifest", "definition"):
        ("manifests.py:_definition", "caller:definition"),
    ("caller", "output.py:request_freeze", "disposition"):
        ("output.py:_disposition", "caller:disposition"),
    # W6629: the same shape one axis over. A retention disposition is the same
    # question wherever it is asked, and a local copy of a question is how two
    # sites come to disagree about one string.
    ("caller", "intake.py:decide_retention", "disposition"):
        ("intake.py:_disposition", "caller:disposition"),
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
    # W43975 and W39358 added two more entries onto the same store, and they
    # are handed to the same one owner: the read-only adoption a resuming
    # deployment uses, and the selective removal an ordinary ending performs.
    # Registered here rather than left for whoever next runs the inventory,
    # because they are debts those Works created.
    ("caller", "workspaces.py:adopted_assignment_workspace", "storage"):
        ("workspaces.py:_real", "caller:path"),
    ("caller", "workspaces.py:discard_execution_roots", "storage"):
        ("workspaces.py:_real", "caller:path"),
    # W19784: the assignment's own read-only root, delegated to the same one
    # owner as every other path this component is handed.
    ("caller", "workspaces.py:compose_input_root", "inputs"):
        ("workspaces.py:_real", "caller:path"),
    # W15232 removed the acquisition half's delegations with the operations
    # that had them.
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
    # -- W39666: the worker-entry transport's forwards -----------------------
    #
    # W39356 recorded `oci.py:_network` as owing an entry, and it does own one
    # -- just not its own. `_network` is private, so it is not a receiving site
    # at all; what crosses is `run_vector`'s `network` operand, which is handed
    # straight to it. Declaring the forward is what makes the historical debt
    # true rather than approximately true, and it is why `_network` is NOT in
    # `NOT_AN_ENTRY`: hiding the helper would leave the public operand unowned.
    ("caller", "oci.py:run_vector", "network"):
        ("oci.py:_network", "caller:network"),
    # `converse` composes its argv through `exec_vector` rather than owning an
    # engine name or a runtime identity of its own -- the same reason every
    # other vector delegates to `_engine`. The runtime id stops at
    # `exec_vector`, which owns it under the layer; the engine name travels one
    # further, to the owner all six other vectors already share.
    ("caller", "worker_entry.py:converse", "engine"):
        ("oci.py:_engine", "caller:engine"),
    ("caller", "worker_entry.py:converse", "runtime_id"):
        ("oci.py:exec_vector", "caller:runtime_id"),
    # THE PORT IS CONSTRUCTED FROM IT WHEN IT IS NOT ALREADY ONE, so a raw
    # open operation reaches `ChannelPort.__init__`'s capability rule -- the
    # same rule, at the site that has always owned it.
    ("caller", "worker_entry.py:converse", "channel_port"):
        ("worker_entry.py:ChannelPort.__init__", "caller:open_channel"),
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
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
            policy_digest="sha256:" + "d" * 64)
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
                adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
                policy_digest="sha256:" + "d" * 64)
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis="consent_runtime", value="running")
        return run

    def spoiling_observation(self, column):
        def run():
            worker_manager.record_attempt(
                self.store, attempt_id="attempt-1", adapter_name="acp",
                adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
                policy_digest="sha256:" + "d" * 64)
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

    # -- W6627's interrogation half ------------------------------------------

    def interrogating(self, posture="execution"):
        """An open session with a provider identity adopted -- the precondition
        both interrogations need to REACH the boundary they name."""
        self.sessioned(posture)
        worker_manager.adopt_provider_session(
            self.store, attempt_id="attempt-1", posture=posture,
            session_epoch=1, provider_session_id="provider-1")
        return "provider-1"

    def asking(self, kind, *, agent=None, **spoiled):
        def run():
            self.interrogating()
            operands = dict(attempt_id="attempt-1", posture="execution",
                            session_epoch=1, operation_id=f"{kind}-1",
                            deadline_seconds=30)
            if kind == "inquire":
                operands["question"] = "how is it going?"
            operands.update(spoiled)
            getattr(worker_manager, kind)(
                self.store, self.port,
                _Interrogating("provider-1") if agent is None else agent,
                **operands)
        return run

    def spoiling_interrogation(self, column, driver="one"):
        def run():
            self.interrogating()
            worker_manager.probe(
                self.store, self.port, _Interrogating("provider-1"),
                attempt_id="attempt-1", posture="execution", session_epoch=1,
                operation_id="probe-1", deadline_seconds=30)
            self.corrupt(f"UPDATE interrogations SET {column} = ?",
                         self.SPOILED[
                             schema.INTERROGATION_COLUMNS[column].kind])
            if driver == "one":
                worker_manager.interrogation_of(self.store, "probe-1")
            else:
                worker_manager.interrogations_of(self.store, "attempt-1",
                                                 "execution", 1)
        return run

    def settling(self, observation):
        """The exported settlement, driven with a spoiled reading.

        The interrogation is left REQUESTED — its adapter never answered — so
        what the probe reaches is this door's own owner rather than a move the
        axis would have refused anyway."""
        def run():
            self.interrogating()
            try:
                worker_manager.probe(
                    self.store, self.port,
                    _Interrogating("provider-1", probe=_Raising),
                    attempt_id="attempt-1", posture="execution",
                    session_epoch=1, operation_id="settle-1",
                    deadline_seconds=30)
            except TimeoutError:
                pass
            worker_manager.settle_interrogation(
                self.store, operation_id="settle-1", outcome="observed",
                observation=observation)
        return run

    def publishing(self, reference):
        def run():
            self.interrogating()
            worker_manager.inquire(
                self.store, self.port, _Interrogating("provider-1"),
                attempt_id="attempt-1", posture="execution", session_epoch=1,
                operation_id="inquire-1", deadline_seconds=30,
                question="how is it going?")
            worker_manager.record_inquiry_answer(
                self.store, operation_id="inquire-1",
                answer={"body": "halfway through the second gate"})
            self.session._published = reference
            worker_manager.publish_inquiry_answer(self.store, self.port,
                                                  operation_id="inquire-1")
        return run

    def interrogation_probes(self):
        """One probe per (entry, label) W6627's interrogation split added.

        Every one drives the REAL exported operation with exactly one operand
        spoiled, and `refusing` requires the refusal to name the label -- so a
        probe stopped by an earlier precondition fails rather than passing for
        the wrong reason.
        """
        I = "interrogation.py"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        found = {
            # -- the shared operands, owned once in `_ask` -------------------
            (at(f"{I}:publish_inquiry_answer", "operation_id"),
             "an interrogation operation id"): (
                "an interrogation operation id",
                lambda: worker_manager.publish_inquiry_answer(
                    self.store, self.port, operation_id=SURROGATE)),
            (at(f"{I}:interrogation_of", "operation_id"),
             "an interrogation operation id"): (
                "an interrogation operation id",
                lambda: worker_manager.interrogation_of(self.store,
                                                        SURROGATE)),
            (at(f"{I}:settle_interrogation", "operation_id"),
             "an interrogation operation id"): (
                "an interrogation operation id",
                lambda: worker_manager.settle_interrogation(
                    self.store, operation_id=SURROGATE, outcome="observed")),
            (at(f"{I}:settle_interrogation", "outcome"),
             "an interrogation outcome"): (
                "an interrogation outcome",
                lambda: worker_manager.settle_interrogation(
                    self.store, operation_id="probe-1", outcome=SURROGATE)),
            (at(f"{I}:record_inquiry_answer", "operation_id"),
             "an interrogation operation id"): (
                "an interrogation operation id",
                lambda: worker_manager.record_inquiry_answer(
                    self.store, operation_id=SURROGATE,
                    answer={"body": "done"})),
            (at(f"{I}:record_inquiry_answer", "answer"),
             "an inquiry answer"): (
                "an inquiry answer",
                lambda: worker_manager.record_inquiry_answer(
                    self.store, operation_id="inquire-1", answer="done")),
            (at(f"{I}:record_inquiry_answer", "answer.body"),
             "an inquiry answer body"): (
                "an inquiry answer body",
                # NOT the surrogate: the document's own encodability walk
                # refuses that first, and a probe stopped by an earlier
                # boundary proves the earlier boundary. A number is a
                # perfectly storable JSON value and still not prose.
                lambda: worker_manager.record_inquiry_answer(
                    self.store, operation_id="inquire-1",
                    answer={"body": 7})),
            (at(f"{I}:interrogations_of", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.interrogations_of(
                    self.store, SURROGATE, "execution", 1)),
            (at(f"{I}:interrogations_of", "posture"), "a posture"): (
                "a posture",
                lambda: worker_manager.interrogations_of(
                    self.store, "attempt-1", SURROGATE, 1)),
            # -- what Baton answered when the manager published --------------
            (at("authority_port.py:AuthorityPort.publish_answer",
                "publish_answer", "injected"),
             "a published answer reference"): (
                "a published answer reference", self.publishing(7)),
        }
        # THE TWO OPERATIONS, spoiled the same way, because the delegation says
        # they are owned in one place: a probe that only ever drove `probe`
        # would leave `inquire` claiming an owner nothing exercised.
        for kind in ("probe", "inquire"):
            for subject, label, spoiled in (
                    ("attempt_id", "a runtime attempt id",
                     {"attempt_id": SURROGATE}),
                    ("posture", "a posture", {"posture": SURROGATE}),
                    ("operation_id", "an interrogation operation id",
                     {"operation_id": SURROGATE}),
                    ("deadline_seconds", "an interrogation deadline",
                     {"deadline_seconds": "thirty"})):
                found[(at(f"{I}:{kind}", subject), label)] = (
                    label, self.asking(kind, **spoiled))
            # `_ask` proves BOTH operations before either is used, so an
            # adapter missing only `inquire` is what reaches the second label.
            found[(at(f"{I}:{kind}", "agent"), "the agent adapter's ")] = (
                f"the agent adapter's {kind}",
                self.asking(kind, agent=_HalfAnAgent() if kind == "probe"
                            else _ProbesButCannotBeAsked()))
            found[(at(f"{I}:{kind}", f"agent.{kind}", "injected"),
                   f"an agent {'probe answer' if kind == 'probe' else 'inquiry acknowledgement'}")] = (
                f"an agent {'probe answer' if kind == 'probe' else 'inquiry acknowledgement'}",
                self.asking(kind, agent=_Interrogating(
                    "provider-1", **{kind: "not an answer"})))
            found[(at(f"{I}:{kind}", f"agent.{kind}.provider_session_id",
                      "injected"), "an observed provider session id")] = (
                "an observed provider session id",
                self.asking(kind, agent=_Interrogating(
                    "provider-1",
                    **{kind: {"kind": "runtime-absent",
                              "provider_session_id": ""}})))
        # -- W6627 re-review [P1]: the observed variant's own members --------
        #
        # `alternative` closes the member NAMES and deliberately does not own
        # their values, and this reading is now DURABLE — so each member is
        # owned before it is returned or written, and each has its own probe.
        for subject, label, spoiled in (
                ("state", "an observed session state", {"state": ""}),
                ("last_activity_at", "an observed last activity instant",
                 {"last_activity_at": "not-an-instant"}),
                ("diagnostics", "probe diagnostics",
                 {"diagnostics": "not a document"})):
            found[(at(f"{I}:probe", f"agent.probe.{subject}", "injected"),
                   label)] = (
                label,
                self.asking("probe", agent=_Interrogating(
                    "provider-1",
                    probe={"kind": "observed", "state": "ready",
                           "provider_session_id": "provider-1",
                           "last_activity_at": NOW, "diagnostics": {},
                           **spoiled})))
        found[(at(f"{I}:inquire", "question"), "an inquiry question")] = (
            "an inquiry question", self.asking("inquire", question=SURROGATE))
        # -- the adopted row, member by member ------------------------------
        for column in ("answer", "authority_uuid", "kind", "outcome",
                       "published_at", "work_id"):
            found[(at(f"{I}:_row", f"interrogations.{column}", "adopted"),
                   "a persisted interrogation")] = (
                "a persisted interrogation",
                self.spoiling_interrogation(column))
        found[(at(f"{I}:_row", "interrogations", "adopted"),
               "a persisted interrogation")] = (
            "a persisted interrogation", self.spoiling_interrogation("kind"))
        # W6627's third correction: the observation is a persisted column now,
        # and the posture/epoch are read to bind a settlement to its session.
        for column in ("observation", "posture"):
            found[(at(f"{I}:_row", f"interrogations.{column}", "adopted"),
                   "a persisted interrogation")] = (
                "a persisted interrogation",
                self.spoiling_interrogation(column))
        # -- the PUBLIC settlement door, which owns its caller's reading -----
        #
        # Third review [P1]: this door took an observation straight to the
        # column while the adapter path owned one. Each member is spoiled on
        # its own, because an envelope owner answering for five members would
        # demand one probe prove five things.
        sound = {"kind": "observed", "state": "ready",
                 "provider_session_id": "provider-1",
                 "last_activity_at": NOW, "diagnostics": {}}
        found[(at(f"{I}:settle_interrogation", "observation"),
               "an interrogation observation")] = (
            "an interrogation observation",
            self.settling("not a document"))
        for member in ("state", "provider_session_id", "last_activity_at",
                       "diagnostics"):
            found[(at(f"{I}:settle_interrogation", f"observation.{member}"),
                   "an interrogation observation")] = (
                "an interrogation observation",
                self.settling({name: value for name, value in sound.items()
                               if name != member}))
        found[(at(f"{I}:interrogations_of", "interrogations", "adopted"),
               "a persisted interrogation")] = (
            "a persisted interrogation",
            self.spoiling_interrogation("kind", driver="many"))
        return found

    # -- W6632: the constrained OCI adapter core -----------------------------

    # W15232 review [P1]: TWO generic roots. The third was acquisition-specific
    # capacity this manager provisioned for every assignment.
    OCI_ROOTS = {"inputs": "/srv/a-1/inputs",
                 "workspace": "/srv/a-1/workspace"}
    # W16823 adds the principal and the effective scope, beside the fence.
    OCI_LABELS = {"runtime_attempt_id": "attempt-1", "authority_uuid": UUID,
                  "work_id": WORK, "participant": WHO, "generation": 1,
                  "principal": PRINCIPAL, "effective_scope": SCOPE,
                  "profile_digest": "sha256:" + "b" * 64,
                  "policy_digest": "sha256:" + "d" * 64,
                  "adapter_digest": "sha256:" + "c" * 64}
    OCI_IMAGE = "sha256:" + "e" * 64
    # AGREEING with OCI_LABELS, because that is the contract: a fixture whose
    # identity and labels disagreed would make every seam probe refuse for the
    # mismatch instead of for its own operand.
    OCI_IDENTITY = {"image_digest": OCI_IMAGE,
                    "profile_digest": "sha256:" + "b" * 64,
                    "policy_digest": "sha256:" + "d" * 64,
                    "adapter_digest": "sha256:" + "c" * 64}

    def running_vector(self, **spoiled):
        from baton_v12.worker_manager import oci
        operands = dict(image_digest=self.OCI_IMAGE,
                        labels=dict(self.OCI_LABELS),
                        assignment_roots=dict(self.OCI_ROOTS),
                        posture="execution",
                        # W33936: an execution vector without the configured
                        # workspace group refuses before every rule these
                        # probes name, so a probe that omitted it would land
                        # on that refusal rather than on its own boundary.
                        workspace_group=self.configured_group(),
                        name="baton-op-1")
        engine = spoiled.pop("engine", "docker")
        operands.update(spoiled)
        return lambda: oci.run_vector(engine, **operands)

    def mounting(self, **spoiled):
        one = {"source": "/srv/a-1/workspace/tree", "target": "/workspace",
               "writable": True}
        one.update(spoiled)
        return self.running_vector(mounts=[one])

    def adapter(self, **spoiled):
        """One adapter over a silent engine, with one operand spoiled."""
        from baton_v12.worker_manager import oci
        operands = dict(identity=dict(self.OCI_IDENTITY),
                        assignment_roots=dict(self.OCI_ROOTS),
                        posture="execution")
        engine = spoiled.pop("engine", "docker")
        run = spoiled.pop("run", lambda argv: {"status": 0, "stdout": "[]",
                                               "stderr": ""})
        operands.update(spoiled)
        return lambda: oci.OciAdapter(engine, run, **operands)

    def seam(self, member, request):
        """One adapter seam operation, driven with a spoiled request."""
        from baton_v12.worker_manager import oci

        def run():
            built = oci.OciAdapter(
                "docker",
                lambda argv: {"status": 0, "stdout": "[]", "stderr": ""},
                identity=dict(self.OCI_IDENTITY),
                assignment_roots=dict(self.OCI_ROOTS), posture="execution")
            getattr(built, member)(request)
        return run

    def oci_probes(self):
        """One probe per (entry, label) the OCI core owns.

        Every one drives the REAL public vector or seam with exactly one
        operand spoiled, and `refusing` requires the refusal to name the
        label -- so a probe stopped by an earlier precondition fails rather
        than passing for the wrong reason.
        """
        from baton_v12.worker_manager import oci
        A = "oci.py"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        found = {}
        # THE SHARED ENGINE NAME, at every vector and at the adapter. Six
        # entries delegate to one owner, so each gets its own drive: a
        # delegation nobody exercised at a site is a rule that site does not
        # actually have.
        engines = {
            f"{A}:run_vector": self.running_vector(engine=SURROGATE),
            f"{A}:stop_vector":
                lambda: oci.stop_vector(SURROGATE, runtime_id="r-1"),
            f"{A}:list_vector":
                lambda: oci.list_vector(SURROGATE,
                                        labels=dict(self.OCI_LABELS)),
            f"{A}:inspect_vector":
                lambda: oci.inspect_vector(SURROGATE, runtime_id="r-1"),
            f"{A}:destroy_vector":
                lambda: oci.destroy_vector(SURROGATE, runtime_id="r-1"),
            f"{A}:OciAdapter.__init__": self.adapter(engine=SURROGATE),
        }
        for site, drive in engines.items():
            found[(at(site, "engine"), "an engine name")] = (
                "an engine name", drive)
        # The runtime identity, at each vector that names one.
        for site, drive in (
                (f"{A}:stop_vector",
                 lambda: oci.stop_vector("docker", runtime_id=SURROGATE)),
                (f"{A}:inspect_vector",
                 lambda: oci.inspect_vector("docker", runtime_id=SURROGATE)),
                (f"{A}:destroy_vector",
                 lambda: oci.destroy_vector("docker", runtime_id=SURROGATE))):
            found[(at(site, "runtime_id"), "a runtime id")] = (
                "a runtime id", drive)
        found[(at(f"{A}:OciAdapter.observe", "runtime_id"),
               "a runtime id")] = (
            "a runtime id", self.seam("observe", SURROGATE))
        # W6629 review [P1]: this seam receives `runtimeDestroyBody` now, so
        # the identity is spoiled INSIDE the command rather than instead of it.
        #
        # W34998: AND THERE ARE TWO SEAMS NOW, because a failed start has a
        # runtime to remove and no intake receipt to authorize it with. The
        # two commands are siblings with closed member sets, so each gets its
        # own envelope probe and its own spoiled identity -- probing one and
        # trusting the other is exactly the shape "no fallback" forbids.
        assignment = {"work_ref": {"authority_uuid": "u" * 32,
                                   "work_id": "u" * 32 + "-W1"},
                      "participant": "baton.claude", "generation": 1}
        for method, label, digest_member, digest_value in (
                ("destroy", "a destroy command",
                 "intake_receipt_digest", RECEIPT),
                ("destroy_failed_start", "a failed-start destroy command",
                 "failed_start_record_digest", RECEIPT),
                # W32576: the third sibling, probed as one rather than trusted
                # because it resembles the other two.
                ("destroy_refused_session", "a refused-session destroy command",
                 "refusal_record_digest", RECEIPT)):
            body = {"assignment_ref": assignment,
                    "runtime_attempt_id": "attempt-1",
                    "runtime_id": SURROGATE,
                    digest_member: digest_value,
                    "retention_policy_digest": RETENTION_POLICY}
            found[(at(f"{A}:OciAdapter.{method}", "command.runtime_id"),
                   label)] = (label, self.seam(method, dict(body)))
            found[(at(f"{A}:OciAdapter.{method}", "command"), label)] = (
                label, self.seam(method, "not a document"))
        # The frozen label document, at both vectors that carry one.
        found[(at(f"{A}:run_vector", "labels"), "a runtime's labels")] = (
            "a runtime's labels", self.running_vector(labels="not a document"))
        found[(at(f"{A}:list_vector", "labels"), "a runtime's labels")] = (
            "a runtime's labels",
            lambda: oci.list_vector("docker", labels="not a document"))
        # The assignment's roots and the posture that reads them.
        for site, drive in (
                (f"{A}:run_vector",
                 self.running_vector(assignment_roots="not a document")),
                (f"{A}:OciAdapter.__init__",
                 self.adapter(assignment_roots="not a document"))):
            found[(at(site, "assignment_roots"),
                   "the assignment's roots")] = (
                "the assignment's roots", drive)
        for site, drive in (
                (f"{A}:run_vector", self.running_vector(posture=SURROGATE)),
                (f"{A}:OciAdapter.__init__",
                 self.adapter(posture=SURROGATE))):
            found[(at(site, "posture"), "a worker posture")] = (
                "a worker posture", drive)
        # The image, the name, and the injected engine capability.
        found[(at(f"{A}:run_vector", "image_digest"), "an image digest")] = (
            "an image digest", self.running_vector(image_digest=SURROGATE))
        found[(at(f"{A}:OciAdapter.__init__", "identity"),
               "a resolved runtime identity")] = (
            "a resolved runtime identity",
            self.adapter(identity="not a document"))
        # THE ENVELOPE AND THE MEMBERS ARE TWO RULES AND TWO DOORS. The
        # document owner above proves the shape; each digest inside it is
        # owned as durable text by its own boundary, and an identity is what a
        # restart compares a running worker against -- so a member that is not
        # durable text has to be refused there rather than reaching the digest
        # pattern that assumes it is.
        #
        # THE EMPTY STRING RATHER THAN THE SURROGATE, for the reason stated
        # below about members inside an owned envelope: `own` walks the
        # document for encodability first, so a surrogate proves the
        # envelope's rule and never reaches this one.
        found[(at(f"{A}:OciAdapter.__init__", "identity"),
               "a resolved identity digest")] = (
            "a resolved identity digest",
            self.adapter(identity=dict(self.OCI_IDENTITY,
                                       image_digest="")))
        found[(at(f"{A}:run_vector", "name"), "a runtime name")] = (
            "a runtime name", self.running_vector(name=SURROGATE))
        found[(at(f"{A}:OciAdapter.__init__", "run"),
               "the engine's run operation")] = (
            "the engine's run operation", self.adapter(run=object()))
        # THE PORT'S OWN DOOR as well as the adapter's. The adapter wraps a
        # bare callable in an `EnginePort`, and a caller holding the port
        # constructs one directly -- two doors to one rule, so two drives.
        found[(at(f"{A}:EnginePort.__init__", "run"),
               "the engine's run operation")] = (
            "the engine's run operation", lambda: oci.EnginePort(object()))
        # W43977: AND WHAT THAT CAPABILITY ANSWERS, which is a different
        # crossing from whether it is callable. The port is the one place a
        # deployment's runner speaks to this manager -- every vector this
        # module composes, and every custody listing, inspection, stop and
        # removal, arrives back through here -- so the answer is owned once,
        # at the real crossing, rather than once per vector.
        def answering(**members):
            # A NON-ZERO STATUS and non-empty streams, so a probe that means
            # to spoil ONE member is not stopped by the injected-answer rule
            # refusing another's falsey default first.
            body = {"status": 1, "stdout": "out", "stderr": "err"}
            body.update(members)
            return lambda: oci.EnginePort(lambda argv: body)(
                ["docker", "version"])

        found[(("injected", f"{A}:EnginePort.__call__", "run"),
               "the engine's answer")] = (
            "the engine's answer",
            lambda: oci.EnginePort(lambda argv: "not a document")(
                ["docker", "version"]))
        # The three members this manager consumes are DISCOVERED now and have
        # no layer owner the scanner can see; W43977's handoff explains why
        # and what closing it needs. Probing them would assert an ownership
        # that does not exist.
        del answering
        # A mount, member by member.
        # THE EMPTY STRING RATHER THAN THE SURROGATE for members inside an
        # owned envelope: the envelope's own encodability walk refuses a
        # surrogate FIRST, so such a probe would prove the envelope's rule and
        # call it the member's. An empty string is perfectly encodable and is
        # still not a path.
        found[(at(f"{A}:run_vector", "mounts.source"), "a host path")] = (
            "a host path", self.mounting(source=""))
        found[(at(f"{A}:run_vector", "mounts.target"), "a container path")] = (
            "a container path", self.mounting(target=""))
        # The seam's own requests, envelope and member by member.
        found[(at(f"{A}:OciAdapter.start", "request"), "a start request")] = (
            "a start request", self.seam("start", "not a document"))
        found[(at(f"{A}:OciAdapter.start", "request.labels"),
               "a start request")] = (
            "a start request",
            self.seam("start", {"operation_id": "runtime.start:1"}))
        found[(at(f"{A}:OciAdapter.start", "request.operation_id"),
               "an operation identity")] = (
            "an operation identity",
            self.seam("start", {"labels": dict(self.OCI_LABELS),
                                "operation_id": ""}))
        found[(at(f"{A}:OciAdapter.list", "request"), "a list request")] = (
            "a list request", self.seam("list", "not a document"))
        found[(at(f"{A}:OciAdapter.list", "request.labels"),
               "a list request")] = (
            "a list request", self.seam("list", {}))
        found[(at(f"{A}:OciAdapter.stop", "request"), "a stop request")] = (
            "a stop request", self.seam("stop", "not a document"))
        found[(at(f"{A}:OciAdapter.stop", "request.runtime_id"),
               "a runtime id")] = (
            "a runtime id",
            self.seam("stop", {"runtime_id": "",
                               "operation_id": "runtime.stop:1"}))
        found[(at(f"{A}:OciAdapter.stop", "request.operation_id"),
               "an operation identity")] = (
            "an operation identity",
            self.seam("stop", {"runtime_id": "r-1",
                               "operation_id": ""}))
        return found

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

    # -- W6628: the output freeze and the sealed receiver --------------------

    def output_world(self):
        """The published declaration retained, and one activated, quiescent
        attempt with a terminal disposition -- the precondition every probe
        below needs to REACH the boundary it names rather than an earlier one.

        The session is re-pointed at the DECLARATION's own Work, because §12
        rule 1 makes a Work id carry its authority's prefix and the offer
        fixtures this file shares were written for a path that never validates
        a manifest.
        """
        self.session._work = {"status": "open", "phase": "queued",
                              "handler": None, "gate": None,
                              "authority_uuid": AUTHORITY,
                              # W16823: what the offer freezes about the Work.
                              "scope": SCOPE, "route": ROUTE}
        live = {"work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
                "participant": WHO, "generation": 1}
        # W16823: the closed claim result.
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": 1,
                                     "decision": decision()}
        self.session.live_assignment = dict(live)
        declaration = OutputCase.published()
        self.declaration = declaration
        self.input_digest = worker_manager.retain_manifest(
            self.store, declaration, "inputManifest")["digest"]
        worker_manager.issue_offer(
            self.store, self.port, offer_id="offer-o", work_id=JOB,
            runtime_attempt_id="attempt-1", input_digest=self.input_digest,
            policy_digest=POLICY, profile_digest=PROFILE,
            profile_name="reference", mint_bearer=lambda: "bearer-1")
        worker_manager.accept_offer(
            self.store, self.port, offer_id="offer-o", decision="accept",
            bearer="bearer-1", now=NOW, runtime_attempt_id="attempt-1",
            work_ref={"authority_uuid": AUTHORITY, "work_id": JOB})
        worker_manager.record_attempt(
            self.store, attempt_id="attempt-1", adapter_name="acp",
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
            input_digest=self.input_digest, policy_digest=POLICY)
        worker_manager.submit_claim(self.store, self.port, offer_id="offer-o")
        worker_manager.activate_assignment(
            self.store, self.port, attempt_id="attempt-1",
            expect=dict(self.session.claim_answer["assignment"]))
        for axis, value in (("execution_runtime", "running"),
                            ("execution_runtime", "quiescent"),
                            ("worker_disposition", "completed")):
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis=axis, value=value)
        return "attempt-1"

    def attempt_row(self):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                ("attempt-1",)).fetchone()
            return {key: found[key] for key in found.keys()}
        finally:
            beside.close()

    def sealed_result(self, **members):
        body = {
            "version": {"major": 1, "minor": 0},
            "manifest_id": "result-manifest-1", "created_at": NOW,
            "extensions": {}, "schema": "baton.worker-manifest/result",
            "result_id": "result-1",
            "assignment_ref": {
                "work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
                "participant": WHO, "generation": 1},
            "input_manifest_digest": self.input_digest,
            "policy_digest": POLICY, "disposition": "completed",
            "outputs": OutputCase.present(), "evidence": [],
            "freeze_operation": dict(
                worker_manager.freeze_operation(self.attempt_row())),
            "manager_observed_at": NOW,
            # W14251 fourth review: a COMPLETED receipt binds the worker
            # completion envelope the manager validated before freezing. These
            # probes are about the receiving rules rather than about which
            # envelope was validated, so the value is a fixture.
            "completion_manifest_digest": COMPLETION,
        }
        body.update(members)
        rest = {name: value for name, value in body.items()
                if name != "manifest_digest"}
        return {**rest, "manifest_digest": _contracts_digest(rest)}

    def froze(self):
        attempt_id = self.output_world()

        class Sealer:
            def __init__(self, answer):
                self._answer = answer

            def seal(self, operands):
                return self._answer

        worker_manager.request_freeze(
            self.store, self.port, Sealer(self.sealed_result()),
            attempt_id=attempt_id, disposition="completed")
        return attempt_id

    def spoiling_output_attempt(self, column):
        def run():
            self.output_world()
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.record_frozen_result(
                self.store, attempt_id="attempt-1",
                sealed=self.sealed_result())
        return run

    def spoiling_retained(self, column):
        def run():
            self.output_world()
            self.corrupt(f"UPDATE manifests SET {column} = ?",
                         self.SPOILED[schema.MANIFEST_COLUMNS[column].kind])
            worker_manager.load_manifest(self.store, self.input_digest,
                                         "inputManifest")
        return run

    def spoiling_frozen(self, column):
        def run():
            self.froze()
            self.corrupt(f"UPDATE outputs SET {column} = ?",
                         self.SPOILED[schema.OUTPUT_COLUMNS[column].kind])
            worker_manager.frozen_output_of(self.store, "attempt-1")
        return run

    def spoiling_artifact(self, column):
        def run():
            self.froze()
            self.corrupt(f"UPDATE output_artifacts SET {column} = ?",
                         self.SPOILED[
                             schema.OUTPUT_ARTIFACT_COLUMNS[column].kind])
            worker_manager.frozen_output_of(self.store, "attempt-1")
        return run

    def freezing(self, **spoiled):
        def run():
            attempt_id = self.output_world()
            operands = dict(attempt_id=attempt_id, disposition="completed")
            operands.update(spoiled)
            worker_manager.request_freeze(
                self.store, self.port, spoiled.pop("adapter", _Sealing()),
                **{k: v for k, v in operands.items() if k != "adapter"})
        return run

    # -- W6629: intake, retention and cleanup --------------------------------

    def collection(self, attempt_id="attempt-1"):
        """What a collection ANSWERING this attempt's freeze looks like."""
        frozen = worker_manager.frozen_output_of(self.store, attempt_id)
        return {"result_id": frozen["result_id"],
                "artifacts": [{"artifact_id": one["artifact_id"],
                               "content_digest": one["content_digest"],
                               "bytes": one["bytes"],
                               "custody_locator":
                                   "file:///var/lib/baton/custody/"
                                   + one["artifact_id"]}
                              for one in frozen["artifacts"]]}

    def intaken(self):
        """Frozen, taken into custody, and a runtime attached.

        The runtime id is written behind this build's back for the same reason
        every other probe here corrupts a row: `output_world` never starts one,
        and a cleanup probe that stopped at "nothing is attached" would prove an
        earlier precondition rather than the boundary it names.
        """
        attempt_id = self.froze()
        self.corrupt("UPDATE attempts SET runtime_id = ?", "runtime-1")
        worker_manager.request_intake(
            self.store, self.port, _Custodian(self.collection()),
            attempt_id=attempt_id)
        return attempt_id

    def decided(self, disposition="discard-after-intake"):
        attempt_id = self.intaken()
        worker_manager.decide_retention(
            self.store, self.port, _Custodian(), attempt_id=attempt_id,
            artifact_ids=["artifact-1"], disposition=disposition,
            retention_policy_digest=RETENTION_POLICY)
        return attempt_id

    def spoiling_intake_attempt(self, column):
        def run():
            self.froze()
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.request_intake(self.store, self.port, _Collecting(),
                                          attempt_id="attempt-1")
        return run

    def spoiling_intake(self, column):
        def run():
            self.intaken()
            self.corrupt(f"UPDATE intakes SET {column} = ?",
                         self.SPOILED[schema.INTAKE_COLUMNS[column].kind])
            worker_manager.intake_receipt_of(self.store, "attempt-1")
        return run

    def spoiling_custody(self, column):
        def run():
            self.intaken()
            self.corrupt(f"UPDATE intake_artifacts SET {column} = ?",
                         self.SPOILED[
                             schema.INTAKE_ARTIFACT_COLUMNS[column].kind])
            worker_manager.intake_receipt_of(self.store, "attempt-1")
        return run

    def spoiling_retention(self, column="disposition"):
        def run():
            self.decided()
            self.corrupt(f"UPDATE retentions SET {column} = ?",
                         self.SPOILED[schema.RETENTION_COLUMNS[column].kind])
            worker_manager.retentions_of(self.store, "attempt-1")
        return run

    def collecting(self, **spoiled):
        def run():
            attempt_id = self.froze()
            worker_manager.record_intake(
                self.store, self.port, attempt_id=attempt_id,
                collected=dict(self.collection(), **spoiled))
        return run

    def collecting_with(self, collected):
        """A collection that is not a document at all, over a real attempt.

        The attempt has to EXIST or the probe stops at "no runtime attempt" and
        proves an earlier precondition instead of the envelope rule it names.
        """
        def run():
            attempt_id = self.froze()
            worker_manager.record_intake(self.store, self.port,
                                         attempt_id=attempt_id,
                                         collected=collected)
        return run

    def spoiled_artifact(self, member):
        def run():
            attempt_id = self.froze()
            collected = self.collection()
            collected["artifacts"][0][member] = SURROGATE
            worker_manager.record_intake(self.store, self.port,
                                         attempt_id=attempt_id,
                                         collected=collected)
        return run

    def failed_start_world(self):
        """An attempt whose start CREATED a runtime and then failed.

        W32648. Built through the production writers rather than by hand: the
        runtime is attached by an observation and the failure is recorded by
        `attempts._record_start_failure`, which is what
        `request_runtime_start` calls when a start fails. A probe aimed at this
        ending has to reach it, and the ending's first act is to look for that
        record.
        """
        from baton_v12.worker_manager import attempts as attempts_module
        attempt_id = self.output_world()
        # THE ATTACHED IDENTITY AND THE AXIS TOGETHER, written behind the
        # build's back for the reason `corrupt` gives: `output_world` leaves
        # this attempt `quiescent`, and the frozen axis has no transition from
        # there back to a live runtime. What this probe needs is the STATE a
        # failed start leaves -- an attached identity on a runtime that is not
        # yet destroyed -- rather than the sequence that produces it, which
        # `test_attempts` drives through `request_runtime_start` for real.
        self.corrupt("UPDATE attempts SET runtime_id = ?, "
                     "execution_runtime = 'running' "
                     "WHERE runtime_attempt_id = ?", "runtime-1", attempt_id)
        attempts_module._record_start_failure(
            self.store, attempt_id,
            {"kind": "fault", "fault": "RuntimeError",
             "message": "the socket went"})
        # THE ASSIGNMENT IS OVER, which this ending requires before it runs --
        # so a probe aimed at anything past the fence has to get past it.
        self.session.live_assignment = None
        return attempt_id

    def refused_session_world(self):
        """An attempt whose HANDSHAKE this manager refused, runtime attached.

        W32576. Built through the production writers: the session is opened
        against a certified ACP profile pinned to wire version 1 and the
        answered version is 9, so the refusal that reaches the record is one
        `negotiate_acp` DERIVED rather than one this fixture handed in. A
        probe aimed at this ending has to reach it, and the ending's first act
        after the operand checks is to look for that record.
        """
        attempt_id = self.output_world()
        # THE ATTACHED IDENTITY AND THE AXIS TOGETHER, behind the build's back
        # for the reason `failed_start_world` gives: `output_world` leaves this
        # attempt `quiescent` and the frozen axis has no transition back to a
        # live runtime. What this ending needs is a RUNNING container with an
        # identity, which is the state a handshake refusal happens in.
        self.corrupt("UPDATE attempts SET runtime_id = ?, "
                     "execution_runtime = 'running' "
                     "WHERE runtime_attempt_id = ?", "runtime-1", attempt_id)
        profile = acp_profile()
        worker_manager.certify_agent_session_profile(self.store, profile)
        worker_manager.open_agent_session(
            self.store, self.port, attempt_id=attempt_id, posture="execution",
            profile_digest=profile["document_digest"],
            intent="open-execution-1")
        reference = {"runtime_attempt_id": attempt_id, "posture": "execution",
                     "session_epoch": 1, "provider_session_id": None}
        # THE FENCE ANSWERS ABOUT THE WORK `output_world` RE-POINTED THE
        # SESSION AT. The default fixture answer names the shared offer
        # fixtures' authority, and the ending runs `request_cancellation`,
        # which refuses an assignment another authority made -- so without
        # this every probe below would be proving that refusal instead of the
        # one it names.
        self.session.fence_answer = {
            "cause": "cancelled",
            "assignment": {"work_ref": {"authority_uuid": AUTHORITY,
                                        "work_id": JOB},
                           "participant": WHO, "generation": 1},
            "phase": "block", "gate": "runtime-quiescence:1", "fenced": True}
        worker_manager.settle_unsupported_version(
            self.store, self.port, FakeAgent(), FakeAdapter(self),
            session_ref=dict(reference), agent_protocol_version=9)
        # THE ASSIGNMENT IS OVER, which this ending requires before it runs.
        self.session.live_assignment = None
        return reference

    def destroying_refused_session(self, **answer):
        """One refused-session destroy answer with exactly one member spoiled.

        The same closed-envelope rule the other two state: a probe aimed at a
        RUNTIME member carries both provider endings, or the envelope refuses
        it and the member's own rule is never reached.
        """
        if answer:
            answer = {"credentials": {"lifecycle_state": "not-delivered"},
                      "launch": {"lifecycle_state": "not-delivered"},
                      **answer}

        class _RefusedSessionCustodian:
            # W43975 made the directory-custody seam mandatory at every
            # ending's ENTRY, so a driver without one is refused before the
            # observation this probe NAMES.
            custodian_image_digest = "sha256:" + "c" * 64

            def normalize_directory(self, store, *, assignment_id, which):
                from baton_v12.worker_manager import custody

                return custody._answered(
                    "normalize", 0,
                    {"custody": "normalize", "entries": 0, "not_ours": 0,
                     "running_as": [0, 0]}, None)

            def destroy_refused_session(self, command):
                return answer or None

        def run():
            reference = self.refused_session_world()
            worker_manager.authorize_refused_session_cleanup(
                self.store, self.port, _RefusedSessionCustodian(),
                session_ref=reference,
                retention_policy_digest=RETENTION_POLICY)
        return run

    def destroying_failed_start(self, **answer):
        """One failed-start destroy answer with exactly one member spoiled.

        The same closed-envelope rule `destroying` states: a probe aimed at a
        RUNTIME member carries both provider endings, or the envelope refuses
        it and the member's own rule is never reached.
        """
        if answer:
            answer = {"credentials": {"lifecycle_state": "not-delivered"},
                      "launch": {"lifecycle_state": "not-delivered"},
                      **answer}

        class _FailedStartCustodian:
            # W43975 made the directory-custody seam mandatory at every
            # ending's ENTRY, so a driver without one is refused before the
            # observation this probe NAMES.
            custodian_image_digest = "sha256:" + "c" * 64

            def normalize_directory(self, store, *, assignment_id, which):
                from baton_v12.worker_manager import custody

                return custody._answered(
                    "normalize", 0,
                    {"custody": "normalize", "entries": 0, "not_ours": 0,
                     "running_as": [0, 0]}, None)

            def destroy_failed_start(self, command):
                return answer or None

        def run():
            attempt_id = self.failed_start_world()
            worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, _FailedStartCustodian(),
                attempt_id=attempt_id,
                retention_policy_digest=RETENTION_POLICY)
        return run

    def destroying(self, **answer):
        """One destroy answer with exactly one member spoiled.

        W6636: the destroy answer's member contract is CLOSED -- every
        provider ending answers on every destroy -- so a probe aimed at a
        RUNTIME member has to carry both provider endings or it is refused by
        the envelope and the member's own rule is never reached. That is the
        vacuous-probe shape this file exists to catch, and it is the same
        reason the spoiling values here are ones the envelope accepts. A probe
        that IS about a provider ending overrides its own.
        """
        if answer:
            answer = {"credentials": {"lifecycle_state": "not-delivered"},
                      "launch": {"lifecycle_state": "not-delivered"},
                      **answer}

        def run():
            attempt_id = self.decided()
            # W6629 review [P1]: cleanup refuses while the fixed assignment is
            # still the live one, so a probe aimed at the ADAPTER boundary has
            # to get past that gate to reach it.
            self.session.live_assignment = None
            worker_manager.authorize_cleanup(
                self.store, self.port, _Custodian(destroyed=answer),
                attempt_id=attempt_id,
                retention_policy_digest=RETENTION_POLICY)
        return run

    def sealing_probes(self):
        """One probe per (entry, label) W6634 added.

        The two requests are DOCUMENTS, so the envelope owner answers for the
        whole and for each member it names -- which is why every subject here
        carries the same label. Each drives the real exported operation with
        one operand spoiled, and the spoiling value is one the enclosing owner
        ACCEPTS: `boundaries.document` takes a deep built-in copy and refuses
        unencodable text anywhere inside it, so a surrogate would be caught by
        the envelope and the member's own rule would never be reached. That is
        the vacuous-probe shape this file exists to catch.
        """
        from baton_v12.worker_manager import sealing
        S = "sealing.py"

        def at(site, subject):
            return ("caller", site, subject)

        roots = {"inputs": "/srv/a-1/inputs", "workspace": "/srv/a-1/workspace"}
        declared = {"proposal": {
            "name": "proposal", "type": "directory-result", "path": "out",
            "required": True,
            "constraints": {"max_bytes": 1024, "max_entries": 8,
                            "allowed_media_types": ["text/plain"],
                            "link_policy": "forbid",
                            "validator_digest": None}}}
        assignment = {"work_ref": {"authority_uuid": AUTHORITY,
                                   "work_id": JOB},
                      "participant": WHO, "generation": 1}
        operation = {"operation_id": "output.freeze:1",
                     "signature_digest": RETENTION_POLICY}

        def freeze(drop=None, **spoiled):
            body = {"attempt_id": "attempt-1", "assignment": assignment,
                    "context": {"principal": PRINCIPAL,
                                "effective_scope": SCOPE},
                    "disposition": "completed", "now": NOW,
                    "operation": operation}
            body.update(spoiled)
            # REMOVED rather than nulled, for the member probes. The envelope
            # owner's rule is PRESENCE, so a member set to `None` is present
            # and the probe never reaches what it names -- measured: those
            # subcases were reported as not reaching their boundary.
            if drop is not None:
                body.pop(drop)
            return lambda: sealing.sealed_result(
                body, roots=roots, declared=declared,
                identity={"policy_digest": RETENTION_POLICY},
                custody="/srv/a-1/custody",
                input_manifest_digest=RETENTION_POLICY)

        def collect(drop=None, **spoiled):
            body = {"attempt_id": "attempt-1", "assignment": assignment,
                    "result_id": "result-1",
                    "result_manifest_digest": RETENTION_POLICY,
                    "output_names": ["proposal"], "operation": operation}
            body.update(spoiled)
            if drop is not None:
                body.pop(drop)
            return lambda: sealing.collected_result(
                body, custody="/srv/a-1/custody", declared=declared)

        found = {}
        # THE ENVELOPE ITSELF, then each member the owner names.
        found[(at(f"{S}:sealed_result", "request"), "a freeze request")] = (
            "a freeze request", lambda: sealing.sealed_result(
                "not a document", roots=roots, declared=declared,
                identity={"policy_digest": RETENTION_POLICY},
                custody="/srv/a-1/custody",
                input_manifest_digest=RETENTION_POLICY))
        for member in ("attempt_id", "assignment", "disposition", "operation"):
            found[(at(f"{S}:sealed_result", f"request.{member}"),
                   "a freeze request")] = (
                "a freeze request", freeze(drop=member))
        # `now` has its own rule and therefore its own label.
        found[(at(f"{S}:sealed_result", "request.now"),
               "a freeze instant")] = (
            "a freeze instant", freeze(now="not an instant"))
        found[(at(f"{S}:collected_result", "operands"),
               "a collect request")] = (
            "a collect request", lambda: sealing.collected_result(
                "not a document", custody="/srv/a-1/custody",
                declared=declared))
        for member in ("attempt_id", "result_id"):
            found[(at(f"{S}:collected_result", f"operands.{member}"),
                   "a collect request")] = (
                "a collect request", collect(drop=member))
        # `output_names` IS OWNED BY THE PER-NAME RULE NOW, not by the
        # envelope. W6634 sixth review [P1]: the collection iterated
        # `sorted(...)`, a call the derivation cannot follow, so the identity
        # rule below owned a value nothing could attribute to this operand.
        # Iterating the member in place made it attributable and moved the
        # label with it.
        found[(at(f"{S}:collected_result", "operands.output_names"),
               "a collected output name")] = (
            "a collected output name", collect(output_names=[7]))
        # THE DECLARATION'S OWN MEMBERS. W6634 sixth review [P1]: these six
        # boundaries were owners the derivation could not attribute, because
        # `declared_outputs` iterated the copy `_list` returns rather than the
        # caller's own sequence. They are attributable now, so each gets the
        # probe it always needed.
        def declaring(drop=None, **spoiled):
            one = {"name": "proposal", "type": "directory-result",
                   "path": "out", "required": True,
                   "constraints": {"max_bytes": 1024, "max_entries": 8,
                                   "allowed_media_types": ["text/plain"],
                                   "link_policy": "forbid",
                                   "validator_digest": None}}
            one.update(spoiled)
            if drop is not None:
                one.pop(drop)
            return lambda: sealing.declared_outputs([one])

        for subject, label, drive in (
                ("outputs", "a declared output", declaring(drop="required")),
                ("outputs.required", "a declared output",
                 declaring(drop="required")),
                ("outputs.name", "a declared output name",
                 declaring(name=7)),
                ("outputs.type", "a declared output type",
                 declaring(type=7)),
                ("outputs.path", "a declared output path",
                 declaring(path=7)),
                ("outputs.constraints", "a declared output's constraints",
                 declaring(constraints="not a document"))):
            found[(at(f"{S}:declared_outputs", subject), label)] = (
                label, drive)

        return found

    def launch_probes(self):
        """One probe per (entry, label) W26291's launch document added.

        NOTHING HERE TOUCHES A FILESYSTEM, and that is part of what is
        asserted: `materialize` owns its two operands before it decides where
        anything goes, so a delivery whose operands this module cannot read is
        refused before a root exists to clean up.

        The three VALUES the document carries are not probed here because they
        are not entries of this site: they are owned inside `_value` under one
        literal label, which is the rule a shared owner has to follow, and
        `test_launch` drives each of them by name.
        """
        from baton_v12.worker_manager import launch, oci
        L = "launch.py"

        def at(site, subject):
            return ("caller", site, subject)

        def making(**overrides):
            body = {"storage": "/srv/launch", "attempt_id": "attempt-1",
                    "session": "session-1", "contract": "do the thing",
                    "role": "implementer"}
            body.update(overrides)
            place = body.pop("storage")
            return lambda: launch.materialize(place, **body)

        def authored(**overrides):
            body = {"session": "session-1", "contract": "do the thing",
                    "role": "implementer"}
            body.update(overrides)
            return lambda: launch.launch_document(**body)

        def adopting(**overrides):
            body = {"storage": "/srv/launch", "attempt_id": "attempt-1",
                    "session": "session-1", "contract": "do the thing",
                    "role": "implementer"}
            body.update(overrides)
            place = body.pop("storage")
            return lambda: launch.adopt(place, **body)

        found = {
            (at(f"{L}:adopt", "attempt_id"), "a launch attempt id"): (
                "a launch attempt id", adopting(attempt_id=7)),
            (at(f"{L}:adopt", "storage"),
             "the manager's launch storage"): (
                "the manager's launch storage", adopting(storage=7)),
            (at(f"{L}:materialize", "attempt_id"), "a launch attempt id"): (
                "a launch attempt id", making(attempt_id=7)),
            (at(f"{L}:materialize", "storage"),
             "the manager's launch storage"): (
                "the manager's launch storage", making(storage=7)),
        }
        # THE THREE VALUES, at both sites that receive them and through the one
        # private owner both are attributed to. `materialize` forwards rather
        # than owning a second time, so the SAME refusal has to arrive through
        # it -- which is what makes the delegation a fact rather than a note.
        for name in ("session", "contract", "role"):
            found[(at(f"{L}:launch_document", name),
                   "a launch document value")] = (
                "a launch document value", authored(**{name: 7}))
            found[(at(f"{L}:materialize", name),
                   "a launch document value")] = (
                "a launch document value", making(**{name: 7}))
            # W47225: adoption AUTHORS the expected document through the same
            # owner before it reads anything, so the same refusal arrives
            # through it -- which is what makes that delegation a fact.
            found[(at(f"{L}:adopt", name),
                   "a launch document value")] = (
                "a launch document value", adopting(**{name: 7}))
        # And the pair the adapter's capability answers with, owned where the
        # argv is composed exactly as a credential delivery's pairs are.
        found[(("caller", "oci.py:run_vector", "launch_delivered"),
               "a launch document target")] = (
            "a launch document target",
            lambda: oci.run_vector(
                "docker", image_digest=self.OCI_IMAGE,
                labels=dict(self.OCI_LABELS),
                assignment_roots=dict(self.OCI_ROOTS), posture="execution",
                workspace_group=self.configured_group(),
                launch_delivered=("/srv/launch/launch.json", 7),
                name="baton-op-1"))
        return found

    def credential_probes(self):
        """One probe per (entry, label) W6634's credential lifecycle added.

        THE HOME IS A FIXED PATH AND NOTHING HERE TOUCHES A FILESYSTEM. Every
        rule below refuses before any of these operations reaches disk, which
        is itself part of what is being asserted: a delivery whose operands
        this module cannot read is refused before a bearer is anywhere.

        Two entries carry TWO labels each -- the recorded slot's `slot` and
        `target` are owned by the lifecycle-record envelope AND by the
        per-slot document -- so each gets two probes that reach different
        owners. The envelope's is driven with an unencodable value, because
        `boundaries.document` takes a deep built-in copy and refuses one
        anywhere inside; the slot document's is driven by removing the member.
        """
        from baton_v12.worker_manager import credentials
        C = "credentials.py"
        HOME = "/srv/a-1"
        SURROGATE = "\ud800"

        def at(site, subject):
            return ("caller", site, subject)

        home = credentials.CredentialHome(HOME)
        root = home.volatile_root("attempt-1")
        mapping = {"api": {"provider": "vault", "reference": "kv/one"}}

        def slot(**spoiled):
            body = {"slot": "api", "provider": "vault",
                    "target": "/run/baton/credentials/api"}
            body.update(spoiled)
            return body

        def record(drop=None, slots=None, **spoiled):
            body = {"attempt_id": "attempt-1", "runtime_id": "runtime-1",
                    "credential_root": root,
                    "container_root": credentials.CREDENTIAL_ROOT,
                    "slots": [slot()] if slots is None else slots,
                    "lifecycle_state": "live"}
            body.update(spoiled)
            if drop is not None:
                body.pop(drop)
            return body

        def adopting(**overrides):
            body = {"record": record(), "attempt_id": "attempt-1",
                    "runtime_id": "runtime-1"}
            body.update(overrides)
            return lambda: home.adopt(
                body["record"], attempt_id=body["attempt_id"],
                runtime_id=body["runtime_id"],
                workspace_group=self.configured_group())

        def delivery(**spoiled):
            body = {"attempt_id": "attempt-1", "root": root,
                    "slots": [slot()], "state": "live",
                    "bearers": {"api": "a" * 40}}
            body.update(spoiled)
            return credentials.Delivery(**body)

        found = {}

        # -- the home, and every identity named under it ---------------------
        found[(at(f"{C}:CredentialHome.__init__", "place"),
               "a manager credential home")] = (
            "a manager credential home",
            lambda: credentials.CredentialHome(7))
        for site, call in (
                ("volatile_root", lambda: home.volatile_root(7)),
                ("state_path", lambda: home.state_path(7)),
                ("read_state", lambda: home.read_state(7)),
                ("discard_orphan", lambda: home.discard_orphan(7)),
                # W55758: the two no-read orphan sites, owned like the rest.
                ("orphan_evidence", lambda: home.orphan_evidence(7)),
                ("tear_down_orphan", lambda: home.tear_down_orphan(7)),
                ("written_state", lambda: home.written_state(7, record())),
                ("materialize", lambda: home.materialize(
                    [{"slot": "api", "provider": "vault",
                      "reference": "kv/one"}], attempt_id=7,
                    workspace_group=self.configured_group(),
                    credential_provider=lambda one, two: "x" * 40)),
                ("adopt", adopting(attempt_id=7))):
            found[(at(f"{C}:CredentialHome.{site}", "attempt_id"),
                   "a credential attempt id")] = (
                "a credential attempt id", call)

        found[(at(f"{C}:CredentialHome.materialize", "credential_provider"),
               "a credential provider")] = (
            "a credential provider",
            lambda: home.materialize(
                [], attempt_id="attempt-1",
                workspace_group=self.configured_group(),
                credential_provider="not a capability"))
        found[(at(f"{C}:CredentialHome.discard_orphans", "live"),
               "a live attempt id")] = (
            "a live attempt id", lambda: home.discard_orphans(live=[7]))
        # W55758: the typed orphan ending owns its attempt at construction,
        # exactly as every other credential door owns the same identity.
        found[(at(f"{C}:OrphanTeardown.__init__", "attempt_id"),
               "a credential attempt id")] = (
            "a credential attempt id",
            lambda: credentials.OrphanTeardown(7, homes=[home]))
        found[(at(f"{C}:CredentialHome.written_state", "body"),
               "a credential lifecycle record")] = (
            "a credential lifecycle record",
            lambda: home.written_state("attempt-1", "not a document"))

        # -- the lifecycle record, and the slots inside it -------------------
        found[(at(f"{C}:CredentialHome.adopt", "record"),
               "a credential lifecycle record")] = (
            "a credential lifecycle record",
            adopting(record="not a document"))
        found[(at(f"{C}:CredentialHome.adopt", "record.lifecycle_state"),
               "a credential lifecycle record")] = (
            "a credential lifecycle record",
            adopting(record=record(drop="lifecycle_state")))
        found[(at(f"{C}:CredentialHome.adopt", "record.slots"),
               "a recorded credential slot")] = (
            "a recorded credential slot",
            adopting(record=record(slots=["not a document"])))
        found[(at(f"{C}:CredentialHome.adopt", "record.slots.provider"),
               "a credential provider identity")] = (
            "a credential provider identity",
            adopting(record=record(slots=[slot(provider=7)])))
        for member in ("slot", "target"):
            # The ENVELOPE's own rule: an unencodable value anywhere inside
            # the record refuses as the record rather than as the member.
            found[(at(f"{C}:CredentialHome.adopt", f"record.slots.{member}"),
                   "a credential lifecycle record")] = (
                "a credential lifecycle record",
                adopting(record=record(slots=[slot(**{member: SURROGATE})])))
            # And the per-slot document's, reached by REMOVING the member --
            # the owner's rule there is presence, so a spoiled value would be
            # present and this probe would never arrive.
            missing = slot()
            missing.pop(member)
            found[(at(f"{C}:CredentialHome.adopt", f"record.slots.{member}"),
                   "a recorded credential slot")] = (
                "a recorded credential slot",
                adopting(record=record(slots=[missing])))
        found[(at(f"{C}:CredentialHome.adopt", "runtime_id"),
               "a credential runtime id")] = (
            "a credential runtime id", adopting(runtime_id=7))

        # -- the delivery ----------------------------------------------------
        found[(at(f"{C}:Delivery.__init__", "attempt_id"),
               "a credential attempt id")] = (
            "a credential attempt id", lambda: delivery(attempt_id=7))
        found[(at(f"{C}:Delivery.__init__", "root"),
               "a credential root")] = (
            "a credential root", lambda: delivery(root=7))
        found[(at(f"{C}:Delivery.record", "runtime_id"),
               "a credential runtime id")] = (
            "a credential runtime id",
            lambda: delivery().record(runtime_id=7))

        # -- the trusted profile ---------------------------------------------
        found[(at(f"{C}:resolved_delivery", "profile"),
               "a credential slot's provider mapping")] = (
            "a credential slot's provider mapping",
            lambda: credentials.resolved_delivery(
                ["api"], profile={"api": "not a document"}))
        found[(at(f"{C}:resolved_delivery", "profile.provider"),
               "a credential provider identity")] = (
            "a credential provider identity",
            lambda: credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": 7,
                                          "reference": "kv/one"}}))
        found[(at(f"{C}:resolved_delivery", "profile.reference"),
               "a credential provider reference")] = (
            "a credential provider reference",
            lambda: credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": "vault",
                                          "reference": 7}}))
        # -- the resolution, and the provider's own answer -------------------
        def materializing(resolution, mint=None):
            return lambda: home.materialize(
                resolution, attempt_id="attempt-1",
                workspace_group=self.configured_group(),
                credential_provider=mint or (lambda one, two: "x" * 40))

        def resolved(**spoiled):
            body = {"slot": "api", "provider": "vault",
                    "reference": "kv/one"}
            body.update(spoiled)
            return body

        found[(at(f"{C}:CredentialHome.materialize", "resolution"),
               "a resolved credential slot")] = (
            "a resolved credential slot",
            materializing(["not a document"]))
        found[(at(f"{C}:CredentialHome.materialize", "resolution.slot"),
               "a resolved credential slot")] = (
            "a resolved credential slot",
            materializing([{"provider": "vault", "reference": "kv/one"}]))
        found[(at(f"{C}:CredentialHome.materialize", "resolution.provider"),
               "a credential provider identity")] = (
            "a credential provider identity",
            materializing([resolved(provider=7)]))
        found[(at(f"{C}:CredentialHome.materialize", "resolution.reference"),
               "a credential provider reference")] = (
            "a credential provider reference",
            materializing([resolved(reference=7)]))
        # THE PROVIDER'S ANSWER, which is an INJECTED crossing rather than a
        # caller's operand: trusted to be the deployment's and not trusted to
        # be correct, exactly like the bearer mint.
        # ON A REAL HOME, because this is the ONE probe here that reaches
        # disk: everything above refuses before a directory exists, which is
        # itself part of what those probes assert. This one has to get as far
        # as calling the provider.
        writable = credentials.CredentialHome(self.root)
        found[(("injected", f"{C}:CredentialHome.materialize",
                "credential_provider"), "a materialized credential")] = (
            "a materialized credential",
            lambda: writable.materialize(
                [resolved()], attempt_id="attempt-1",
                workspace_group=self.configured_group(),
                credential_provider=lambda one, two: 7))
        found[(at(f"{C}:Delivery.__init__", "slots"),
               "a delivered credential slot")] = (
            "a delivered credential slot",
            lambda: delivery(slots=[{"slot": "api"}]))
        # -- the credential mounts, at the vector that composes them ---------
        found[(("caller", "oci.py:run_vector", "credentials_delivered"),
               "a credential mount target")] = (
            "a credential mount target",
            self.running_vector(credentials_delivered=(
                ("/srv/a-1/credentials/attempt-1/api", 7),)))
        # -- the restart recovery path, on the adapter ----------------------
        #
        # THE ENVELOPE OWNS THE NESTED MEMBERS, so each of these is driven with
        # an unencodable value rather than a missing one: `boundaries.document`
        # takes a deep built-in copy and refuses a surrogate anywhere inside,
        # which is the rule that actually covers them.
        recovering = self.adapter()

        def recovery(**spoiled):
            body = {"attempt_id": "attempt-1",
                    "assignment": {"work_ref": {"authority_uuid": AUTHORITY,
                                                "work_id": JOB},
                                   "participant": WHO, "generation": 1},
                    "context": {"principal": PRINCIPAL,
                                "effective_scope": SCOPE}}
            for path, value in spoiled.items():
                at_document = body
                pieces = path.split(".")
                for piece in pieces[:-1]:
                    at_document = at_document[piece]
                # `_DROP` REMOVES the member rather than spoiling it, which is
                # what reaches a document owner's member-set rule; an
                # unencodable value reaches the envelope first.
                if value is _DROP:
                    at_document.pop(pieces[-1])
                else:
                    at_document[pieces[-1]] = value
            return lambda: recovering().recover_credentials(body)

        found[(("caller", "oci.py:OciAdapter.recover_credentials", "request"),
               "a credential recovery request")] = (
            "a credential recovery request",
            lambda: recovering().recover_credentials("not a document"))
        # THE ENVELOPE still covers the leaf members, and it is reached with an
        # unencodable value because that is what `own` refuses anywhere inside
        # the document it copies.
        for member in ("assignment.work_ref.authority_uuid",
                       "assignment.work_ref.work_id",
                       "assignment.participant", "assignment.generation"):
            found[(("caller", "oci.py:OciAdapter.recover_credentials",
                    f"request.{member}"),
                   "a credential recovery request")] = (
                "a credential recovery request",
                recovery(**{member: SURROGATE}))

        # AND THE TWO DOCUMENT OWNERS INSIDE IT, which the envelope cannot
        # stand in for: a value the envelope happily copies can still be the
        # wrong SHAPE for the assignment or the work reference. Each is driven
        # by a shape fault rather than by an unencodable value, because an
        # unencodable one never gets past the envelope.
        def without(path):
            body = {"work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
                    "participant": WHO, "generation": 1}
            pieces = path.split(".")
            at_document = body
            for piece in pieces[:-1]:
                at_document = at_document[piece]
            at_document.pop(pieces[-1])
            return recovery(assignment=body)

        R = ("caller", "oci.py:OciAdapter.recover_credentials")
        for entry, label, drive in (
                ("request.assignment", "a recovery assignment",
                 recovery(assignment="not a document")),
                ("request.assignment.participant", "a recovery assignment",
                 without("participant")),
                ("request.assignment.generation", "a recovery assignment",
                 without("generation")),
                ("request.assignment.work_ref.authority_uuid",
                 "a recovery assignment", without("work_ref")),
                ("request.assignment.work_ref.work_id",
                 "a recovery assignment", without("work_ref")),
                ("request.assignment.work_ref", "a recovery work ref",
                 recovery(**{"assignment.work_ref": "not a document"})),
                ("request.assignment.work_ref.authority_uuid",
                 "a recovery work ref", without("work_ref.authority_uuid")),
                ("request.assignment.work_ref.work_id",
                 "a recovery work ref", without("work_ref.work_id")),
                # W16823: the trusted context, owned at this door beside the
                # assignment because the label set this recovery SELECTS on
                # now names the principal. Each member is reached under both
                # the envelope's label and the context document's own, exactly
                # as the assignment's members are.
                ("request.context", "a recovery authorization context",
                 recovery(context="not a document")),
                ("request.context.principal",
                 "a recovery authorization context",
                 recovery(**{"context.principal": _DROP})),
                ("request.context.effective_scope",
                 "a recovery authorization context",
                 recovery(**{"context.effective_scope": _DROP})),
                ("request.context.principal", "a credential recovery request",
                 recovery(**{"context.principal": SURROGATE})),
                ("request.context.effective_scope",
                 "a credential recovery request",
                 recovery(**{"context.effective_scope": SURROGATE}))):
            found[((R[0], R[1], entry), label)] = (label, drive)
        found[(("caller", "oci.py:OciAdapter.recover_credentials",
                "request.attempt_id"), "a credential attempt id")] = (
            "a credential attempt id", recovery(attempt_id=7))

        found[(at(f"{C}:slot_name", "value"), "a credential slot name")] = (
            "a credential slot name", lambda: credentials.slot_name(7))
        return found

    def intake_probes(self):
        """One probe per (entry, label) W6629 added."""
        I = "intake.py"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        row = {"runtime_attempt_id": "attempt-1", "adapter_name": "acp",
               "adapter_digest": "sha256:" + "a" * 64,
               "profile_digest": PROFILE, "input_digest": None,
               "policy_digest": "sha256:" + "d" * 64, "image_digest": None,
               "toolchain_digest": None, "created_at": NOW,
               "work_id": JOB, "authority_uuid": AUTHORITY,
               "assignment_participant": WHO, "assignment_generation": 1,
               # W16823: activation fixes the context with the fence, so a row
               # carrying one and not the other is not a persisted attempt.
               "assignment_claim_event_seq": 1,
               "assignment_principal": PRINCIPAL,
               "assignment_scope": SCOPE, "assignment_role": ROUTE,
               "assignment_grant": "direct",
               "assignment_policy_generation": 1,
               "runtime_id": "runtime-1", "observation_seq": 0,
               "observed_at": None,
               # W61599: the liveness projection travels with the row like
               # every other column; a document missing it is not a persisted
               # attempt.
               "activity_bytes": None, "activity_at": None}
        for axis in schema.ATTEMPT_AXES:
            row[axis] = next(iter(schema.ATTEMPT_COLUMNS[axis].allowed))

        derive = {
            "collect_operation": lambda one: worker_manager.collect_operation(
                one),
            "intake_operation": lambda one: worker_manager.intake_operation(
                one),
            # W6629 review [P1]: the artifact set and disposition joined this
            # identity, because one policy deciding differently about two
            # artifacts produced one operation id and two signatures.
            "retain_operation": lambda one: worker_manager.retain_operation(
                one, RETENTION_POLICY, ["artifact-1"], "retain"),
            "destroy_operation": lambda one: worker_manager.destroy_operation(
                one, RECEIPT, RETENTION_POLICY),
        }
        found = {}
        # THE DERIVED IDENTITIES. Each takes a persisted row back IN as a
        # caller operand, and each member it reads is its own entry -- an
        # envelope owner answering for six members would demand one probe
        # prove six things.
        for name, call in derive.items():
            found[(at(f"{I}:{name}", "attempt"), "a persisted attempt")] = (
                "a persisted attempt", lambda call=call: call("not a row"))
        for name in ("collect_operation", "intake_operation"):
            found[(at(f"{I}:{name}", "attempt.runtime_attempt_id"),
                   "a persisted attempt")] = (
                "a persisted attempt",
                lambda name=name: derive[name](
                    dict(row, runtime_attempt_id=SURROGATE)))
        for name in ("retain_operation", "destroy_operation"):
            members = ("runtime_attempt_id", "work_id", "authority_uuid",
                       "assignment_participant", "assignment_generation")
            if name == "destroy_operation":
                members = members + ("runtime_id",)
            for member in members:
                found[(at(f"{I}:{name}", f"attempt.{member}"),
                       "a persisted attempt")] = (
                    "a persisted attempt",
                    lambda name=name, member=member: derive[name](
                        dict(row, **{member: SURROGATE})))
        found[(at(f"{I}:retain_operation", "retention_policy_digest"),
               "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.retain_operation(
                dict(row), SURROGATE, ["artifact-1"], "retain"))
        found[(at(f"{I}:destroy_operation", "retention_policy_digest"),
               "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.destroy_operation(dict(row), RECEIPT,
                                                     SURROGATE))
        found[(at(f"{I}:destroy_operation", "receipt_digest"),
               "an intake receipt digest")] = (
            "an intake receipt digest",
            lambda: worker_manager.destroy_operation(dict(row), SURROGATE,
                                                     RETENTION_POLICY))
        # THE OPERATIONS, each with the operand it names spoiled.
        found[(at(f"{I}:request_intake", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.request_intake(
                self.store, self.port, _Collecting(), attempt_id=SURROGATE))
        found[(at(f"{I}:request_intake", "adapter"),
               "the runtime adapter's collect")] = (
            "the runtime adapter's collect",
            lambda: worker_manager.request_intake(
                self.store, self.port, object(), attempt_id="attempt-1"))
        found[(at(f"{I}:record_intake", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.record_intake(
                self.store, self.port, attempt_id=SURROGATE, collected={}))
        found[(at(f"{I}:record_intake", "collected"),
               "a collection observation")] = (
            "a collection observation", self.collecting_with(SURROGATE))
        found[(at(f"{I}:record_intake", "collected.result_id"),
               "a collection observation")] = (
            "a collection observation", self.collecting(result_id=SURROGATE))
        found[(at(f"{I}:record_intake", "collected.artifacts"),
               "a collection observation")] = (
            "a collection observation", self.collecting(artifacts=SURROGATE))
        for member in ("artifact_id", "content_digest", "custody_locator",
                       "bytes"):
            found[(at(f"{I}:record_intake", f"collected.artifacts.{member}"),
                   "a collection observation")] = (
                "a collection observation", self.spoiled_artifact(member))
        found[(at(f"{I}:intake_receipt_of", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.intake_receipt_of(self.store, SURROGATE))
        found[(at(f"{I}:retentions_of", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.retentions_of(self.store, SURROGATE))
        found[(at(f"{I}:decide_retention", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.decide_retention(
                self.store, self.port, _Custodian(), attempt_id=SURROGATE,
                artifact_ids=["artifact-1"], disposition="retain",
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:decide_retention", "adapter"),
               "the runtime adapter's retain")] = (
            "the runtime adapter's retain",
            lambda: worker_manager.decide_retention(
                self.store, self.port, object(), attempt_id="attempt-1",
                artifact_ids=["artifact-1"], disposition="retain",
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:decide_retention", "retention_policy_digest"),
               "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.decide_retention(
                self.store, self.port, _Custodian(), attempt_id="attempt-1",
                artifact_ids=["artifact-1"], disposition="retain",
                retention_policy_digest=SURROGATE))
        found[(at(f"{I}:decide_retention", "disposition"),
               "a retention disposition")] = (
            "a retention disposition",
            lambda: worker_manager.decide_retention(
                self.store, self.port, _Custodian(), attempt_id="attempt-1",
                artifact_ids=["artifact-1"], disposition=SURROGATE,
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:authorize_cleanup", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.authorize_cleanup(
                self.store, self.port, _Custodian(), attempt_id=SURROGATE,
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:authorize_cleanup", "adapter"),
               "the runtime adapter's destroy")] = (
            "the runtime adapter's destroy",
            lambda: worker_manager.authorize_cleanup(
                self.store, self.port, object(), attempt_id="attempt-1",
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:authorize_cleanup", "retention_policy_digest"),
               "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.authorize_cleanup(
                self.store, self.port, _Custodian(), attempt_id="attempt-1",
                retention_policy_digest=SURROGATE))
        # W32648: THE FAILED-START ENDING, its three operands and its own
        # derived identity. The sibling of `authorize_cleanup` and
        # `destroy_operation` above, and probed as one rather than trusted
        # because it resembles them.
        class _FailedStartCustodian:
            def destroy_failed_start(self, command):
                return None

        found[(at(f"{I}:authorize_failed_start_cleanup", "attempt_id"),
               "a runtime attempt id")] = (
            "a runtime attempt id",
            lambda: worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, _FailedStartCustodian(),
                attempt_id=SURROGATE,
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:authorize_failed_start_cleanup", "adapter"),
               "the runtime adapter's failed-start destroy")] = (
            "the runtime adapter's failed-start destroy",
            lambda: worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, object(), attempt_id="attempt-1",
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:authorize_failed_start_cleanup",
                  "retention_policy_digest"), "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.authorize_failed_start_cleanup(
                self.store, self.port, _FailedStartCustodian(),
                attempt_id="attempt-1", retention_policy_digest=SURROGATE))
        found[(at(f"{I}:failed_start_destroy_operation", "attempt"),
               "a persisted attempt")] = (
            "a persisted attempt",
            lambda: worker_manager.failed_start_destroy_operation(
                "not a row", RECEIPT, RETENTION_POLICY))
        for member in ("runtime_attempt_id", "work_id", "authority_uuid",
                       "assignment_participant", "assignment_generation",
                       "runtime_id"):
            found[(at(f"{I}:failed_start_destroy_operation",
                      f"attempt.{member}"), "a persisted attempt")] = (
                "a persisted attempt",
                lambda member=member:
                worker_manager.failed_start_destroy_operation(
                    dict(row, **{member: SURROGATE}), RECEIPT,
                    RETENTION_POLICY))
        found[(at(f"{I}:failed_start_destroy_operation",
                  "failed_start_record_digest"),
               "a failed-start record digest")] = (
            "a failed-start record digest",
            lambda: worker_manager.failed_start_destroy_operation(
                dict(row), SURROGATE, RETENTION_POLICY))
        found[(at(f"{I}:failed_start_destroy_operation",
                  "retention_policy_digest"), "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.failed_start_destroy_operation(
                dict(row), RECEIPT, SURROGATE))
        # W32576: THE REFUSED-SESSION ENDING, the third sibling. Its two
        # caller operands are checked BEFORE any session is looked up -- the
        # reference is owned, then the policy digest, then the capability --
        # so these probes need a well-shaped reference and no world at all.
        class _RefusedSessionCustodian:
            def destroy_refused_session(self, command):
                return None

        reference = {"runtime_attempt_id": "attempt-1",
                     "posture": "execution", "session_epoch": 1,
                     "provider_session_id": None}
        found[(at(f"{I}:authorize_refused_session_cleanup",
                  "retention_policy_digest"), "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.authorize_refused_session_cleanup(
                self.store, self.port, _RefusedSessionCustodian(),
                session_ref=dict(reference),
                retention_policy_digest=SURROGATE))
        found[(at(f"{I}:authorize_refused_session_cleanup", "adapter"),
               "the runtime adapter's refused-session destroy")] = (
            "the runtime adapter's refused-session destroy",
            lambda: worker_manager.authorize_refused_session_cleanup(
                self.store, self.port, object(), session_ref=dict(reference),
                retention_policy_digest=RETENTION_POLICY))
        found[(at(f"{I}:refused_session_destroy_operation", "attempt"),
               "a persisted attempt")] = (
            "a persisted attempt",
            lambda: worker_manager.refused_session_destroy_operation(
                "not a row", RECEIPT, RETENTION_POLICY))
        for member in ("runtime_attempt_id", "work_id", "authority_uuid",
                       "assignment_participant", "assignment_generation",
                       "runtime_id"):
            found[(at(f"{I}:refused_session_destroy_operation",
                      f"attempt.{member}"), "a persisted attempt")] = (
                "a persisted attempt",
                lambda member=member:
                worker_manager.refused_session_destroy_operation(
                    dict(row, **{member: SURROGATE}), RECEIPT,
                    RETENTION_POLICY))
        found[(at(f"{I}:refused_session_destroy_operation",
                  "refusal_record_digest"), "a refusal record digest")] = (
            "a refusal record digest",
            lambda: worker_manager.refused_session_destroy_operation(
                dict(row), SURROGATE, RETENTION_POLICY))
        found[(at(f"{I}:refused_session_destroy_operation",
                  "retention_policy_digest"), "a retention policy digest")] = (
            "a retention policy digest",
            lambda: worker_manager.refused_session_destroy_operation(
                dict(row), RECEIPT, SURROGATE))
        # ...AND WHAT ITS ADAPTER ANSWERED, envelope and members, exactly as
        # the receipt-authorized crossing's are.
        found[(at(f"{I}:_destroyed_failed_start",
                  "adapter.destroy_failed_start", "injected"),
               "a failed-start destroy observation")] = (
            "a failed-start destroy observation",
            self.destroying_failed_start())
        for member, label, spoiled in (
                ("runtime_id", "an observed runtime id",
                 dict(runtime_id=5, state="absent", why="gone")),
                ("state", "a destroy observation's state",
                 dict(runtime_id="runtime-1", state=5, why="gone")),
                ("why", "a destroy observation's reason",
                 dict(runtime_id="runtime-1", state="absent", why=5))):
            found[(at(f"{I}:_destroyed_failed_start",
                      f"adapter.destroy_failed_start.{member}", "injected"),
                   label)] = (label,
                              self.destroying_failed_start(**spoiled))
        # W32576: ...and the third sibling's answer, the same way.
        found[(at(f"{I}:_destroyed_refused_session",
                  "adapter.destroy_refused_session", "injected"),
               "a refused-session destroy observation")] = (
            "a refused-session destroy observation",
            self.destroying_refused_session())
        for member, label, spoiled in (
                ("runtime_id", "an observed runtime id",
                 dict(runtime_id=5, state="absent", why="gone")),
                ("state", "a destroy observation's state",
                 dict(runtime_id="runtime-1", state=5, why="gone")),
                ("why", "a destroy observation's reason",
                 dict(runtime_id="runtime-1", state="absent", why=5))):
            found[(at(f"{I}:_destroyed_refused_session",
                      f"adapter.destroy_refused_session.{member}", "injected"),
                   label)] = (label,
                              self.destroying_refused_session(**spoiled))
        # WHAT THE ADAPTER ANSWERED, envelope and members.
        #
        # A MEMBER IS SPOILED WITH SOMETHING THE ENVELOPE OWNER ACCEPTS. The
        # document owner takes a deep built-in copy and refuses unencodable
        # text anywhere inside it, so a surrogate here would be refused by the
        # envelope and the member's own rule would never be reached -- which is
        # the vacuous-probe shape this file exists to catch.
        found[(at(f"{I}:_destroyed", "adapter.destroy", "injected"),
               "a destroy observation")] = (
            "a destroy observation", self.destroying())
        found[(at(f"{I}:_destroyed", "adapter.destroy.runtime_id", "injected"),
               "an observed runtime id")] = (
            "an observed runtime id",
            self.destroying(runtime_id=5, state="absent", why="gone"))
        found[(at(f"{I}:_destroyed", "adapter.destroy.state", "injected"),
               "a destroy observation's state")] = (
            "a destroy observation's state",
            self.destroying(runtime_id="runtime-1", state=5, why="gone"))
        found[(at(f"{I}:_destroyed", "adapter.destroy.why", "injected"),
               "a destroy observation's reason")] = (
            "a destroy observation's reason",
            self.destroying(runtime_id="runtime-1", state="absent", why=5))
        # THE PERSISTED ROWS CROSSING BACK IN -- W35557 moved the attempt
        # columns to `attempt_probes`, which derives them from
        # `ATTEMPT_COLUMNS` for every site that adopts one. This hand-written
        # list named seven of them and had drifted; a derivation cannot.
        for column in ("custody", "intake_operation_id", "manifest_digest",
                       "receipt_digest", "recoverable", "result_id", "why"):
            found[(at(f"{I}:intake_receipt_of", f"intakes.{column}",
                      "adopted"), "a persisted intake")] = (
                "a persisted intake", self.spoiling_intake(column))
        found[(at(f"{I}:intake_receipt_of", "intakes", "adopted"),
               "a persisted intake")] = (
            "a persisted intake", self.spoiling_intake("custody"))
        for column in ("artifact_id", "content_digest", "custody_locator"):
            found[(at(f"{I}:intake_receipt_of",
                      f"intake_artifacts.{column}", "adopted"),
                   "a persisted intake artifact")] = (
                "a persisted intake artifact", self.spoiling_custody(column))
        found[(at(f"{I}:intake_receipt_of", "intake_artifacts", "adopted"),
               "a persisted intake artifact")] = (
            "a persisted intake artifact",
            self.spoiling_custody("custody_locator"))
        for column in ("artifact_id", "decided_at", "disposition",
                       "retention_policy_digest"):
            found[(at(f"{I}:retentions_of", f"retentions.{column}",
                      "adopted"), "a persisted retention")] = (
                "a persisted retention", self.spoiling_retention(column))
        found[(at(f"{I}:retentions_of", "retentions", "adopted"),
               "a persisted retention")] = (
            "a persisted retention", self.spoiling_retention())
        return found

    def output_probes(self):
        """One probe per (entry, label) W6628 added."""
        M, O = "manifests.py", "output.py"

        def at(site, subject, domain="caller"):
            return (domain, site, subject)

        row = {"runtime_attempt_id": "attempt-1", "adapter_name": "acp",
               "adapter_digest": "sha256:" + "a" * 64,
               "profile_digest": PROFILE, "input_digest": None,
               "policy_digest": "sha256:" + "d" * 64, "image_digest": None,
               "toolchain_digest": None, "created_at": NOW,
               "work_id": JOB, "authority_uuid": AUTHORITY,
               "assignment_participant": WHO, "assignment_generation": 1,
               # W16823: activation fixes the context with the fence, so a row
               # carrying one and not the other is not a persisted attempt.
               "assignment_claim_event_seq": 1,
               "assignment_principal": PRINCIPAL,
               "assignment_scope": SCOPE, "assignment_role": ROUTE,
               "assignment_grant": "direct",
               "assignment_policy_generation": 1,
               "runtime_id": None, "observation_seq": 0, "observed_at": None,
               "activity_bytes": None, "activity_at": None}
        for axis in schema.ATTEMPT_AXES:
            row[axis] = next(iter(schema.ATTEMPT_COLUMNS[axis].allowed))

        def deriving(**spoiled):
            return lambda: worker_manager.freeze_operation(
                dict(row, **spoiled))

        found = {
            (at(f"{M}:retain_manifest", "definition"),
             "a retained manifest definition"): (
                "a retained manifest definition",
                lambda: worker_manager.retain_manifest(
                    self.store, OutputCase.published(), SURROGATE)),
            (at(f"{M}:load_manifest", "definition"),
             "a retained manifest definition"): (
                "a retained manifest definition",
                lambda: worker_manager.load_manifest(
                    self.store, "sha256:" + "a" * 64, SURROGATE)),
            (at(f"{M}:load_manifest", "manifest_digest"),
             "a retained manifest digest"): (
                "a retained manifest digest",
                lambda: worker_manager.load_manifest(
                    self.store, SURROGATE, "inputManifest")),
            (at(f"{O}:request_freeze", "attempt_id"), "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.request_freeze(
                    self.store, self.port, _Sealing(), attempt_id=SURROGATE,
                    disposition="completed")),
            (at(f"{O}:request_freeze", "disposition"),
             "a declared worker disposition"): (
                "a declared worker disposition",
                lambda: worker_manager.request_freeze(
                    self.store, self.port, _Sealing(),
                    attempt_id="attempt-1", disposition=SURROGATE)),
            (at(f"{O}:request_freeze", "adapter"),
             "the runtime adapter's seal"): (
                "the runtime adapter's seal",
                lambda: worker_manager.request_freeze(
                    self.store, self.port, object(), attempt_id="attempt-1",
                    disposition="completed")),
            (at(f"{O}:record_frozen_result", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.record_frozen_result(
                    self.store, attempt_id=SURROGATE, sealed={})),
            (at(f"{O}:frozen_output_of", "attempt_id"),
             "a runtime attempt id"): (
                "a runtime attempt id",
                lambda: worker_manager.frozen_output_of(self.store,
                                                        SURROGATE)),
            (at(f"{O}:freeze_operation", "attempt"), "a persisted attempt"): (
                "a persisted attempt",
                lambda: worker_manager.freeze_operation("not a row")),
            (at(f"{M}:_manifest_row", "manifests", "adopted"),
             "a retained manifest"): (
                "a retained manifest", self.spoiling_retained("body")),
            (at(f"{M}:_manifest_row", "manifests.body", "adopted"),
             "a retained manifest"): (
                "a retained manifest", self.spoiling_retained("body")),
        }
        # THE MEMBERS OF THE ADOPTED ROW CROSSING BACK IN. Each is its own
        # entry, and each is spoiled on its own -- an envelope owner answering
        # for five members would demand one probe prove five things.
        for member in ("runtime_attempt_id", "work_id", "authority_uuid",
                       "assignment_participant", "assignment_generation",
                       "worker_disposition"):
            found[(at(f"{O}:freeze_operation", f"attempt.{member}"),
                   "a persisted attempt")] = (
                "a persisted attempt", deriving(**{member: SURROGATE}))
        # W35557: the attempt columns are derived in `attempt_probes` now, for
        # this site and the two others that adopt the same row.
        for column in ("result_id", "disposition", "manifest_digest",
                       "freeze_operation_id", "frozen_at"):
            found[(at(f"{O}:frozen_output_of", f"outputs.{column}", "adopted"),
                   "a persisted frozen output")] = (
                "a persisted frozen output", self.spoiling_frozen(column))
        found[(at(f"{O}:frozen_output_of", "outputs", "adopted"),
               "a persisted frozen output")] = (
            "a persisted frozen output", self.spoiling_frozen("result_id"))
        for column in ("output_name", "artifact_id", "media_type",
                       "content_digest", "locator"):
            found[(at(f"{O}:frozen_output_of",
                      f"output_artifacts.{column}", "adopted"),
                   "a persisted output artifact")] = (
                "a persisted output artifact", self.spoiling_artifact(column))
        found[(at(f"{O}:frozen_output_of", "output_artifacts", "adopted"),
               "a persisted output artifact")] = (
            "a persisted output artifact", self.spoiling_artifact("locator"))
        return found

    def configured_group(self):
        """The deployment's configured workspace group, for a probe.

        W33936 review [P1]: the group is a capability read from this manager's
        own record rather than an integer, so a probe that needs one
        configures it and reads it back -- which is also what stops a probe
        from proving a boundary with a value no deployment ever chose.
        """
        from . import input_roots
        if getattr(self, "_group", None) is None:
            self._group = input_roots.configured_group(self.store)
        return self._group

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
        # THE POLICY DIGEST IS RECORDED. W6632 review [P1] made it a
        # reconciliation label, so a runtime start needs an attempt that can
        # name the policy its delivery is made under; without it these probes
        # refuse before reaching the operand they are aimed at.
        operands = dict(adapter_name="acp", adapter_digest="sha256:" + "a" * 64,
                        profile_digest=PROFILE, policy_digest="sha256:" + "d" * 64)
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

    def observing(self, answer):
        """An adapter whose OBSERVATION is whatever this probe needs. W26294.

        The listing is the ordinary one, so what the probe drives is the
        answer `reconcile_runtime` now asks for about the exact runtime rather
        than infers from membership.
        """
        def run():
            self.bound_attempt()
            adapter = FakeAdapter(self)
            # THE LISTING HAS TO MATCH, or reconciliation never reaches the
            # observation at all. `FakeAdapter.list` answers `[]` until
            # something has been started through it, so a probe that only set
            # the observation took the "nothing is listed" path and never
            # touched the boundary it names -- measured: the probe was
            # declared and did not arrive.
            adapter.list = lambda operands: [
                {"runtime_id": adapter.runtime_id,
                 "labels": adapter.labels_for()}]
            adapter.observation = answer
            worker_manager.reconcile_runtime(self.store, adapter,
                                             attempt_id="attempt-1")
        return run

    def observing_without_observe(self):
        """An adapter that LISTS and cannot observe. W26294.

        `object()` would be refused by `reconcile_runtime`'s own `list`
        capability check first and would probe that instead, so the probe
        needs one that gets past the listing and then has nothing to answer
        with.
        """
        def run():
            self.bound_attempt()
            worker_manager.reconcile_runtime(self.store,
                                             _WithoutObserve(self),
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

        # W16823: THE ANSWER NESTS ONE LEVEL DEEPER, so the spoilers say which
        # level they reach.
        #
        #   whole=       replaces the whole closed result
        #   assignment=  replaces the assignment inside it
        #   decision=    replaces the decision inside it
        #   anything else spoils a MEMBER, of the decision when the decision
        #   names it and of the assignment otherwise
        #
        # One composer rather than three, because the claim path and the
        # late-commit path receive the same document and every probe below has
        # to reach the same owner by either door.
        def spoiling(held, **answer):
            if "whole" in answer:
                return answer["whole"]
            result = dict(held)
            for member, value in answer.items():
                if member in ("assignment", "decision"):
                    result[member] = value
                elif member in held["decision"]:
                    result["decision"] = dict(result["decision"],
                                              **{member: value})
                else:
                    result["assignment"] = dict(result["assignment"],
                                                **{member: value})
            return result

        def claiming(offer_id, **answer):
            def run():
                self.accepted(offer_id)
                self.session.claim_answer = spoiling(
                    self.session.claim_answer, **answer)
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
                    "result": spoiling(self.session.claim_answer, **result)}
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
            (at("workspaces.py:assignment_workspace", "assignment_id"),
             "an assignment identity"):
                ("an assignment identity",
                 lambda: workspaces.assignment_workspace(
                     self.configured_group(), self.root, SURROGATE)),
            (at("workspaces.py:discard_workspace", "assignment_id"),
             "an assignment identity"):
                ("an assignment identity",
                 lambda: workspaces.discard_workspace(
                     self.root, SURROGATE)),
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
                lambda: workspaces.assignment_workspace(
                    self.configured_group(), SURROGATE, "a-1")),
            (at("workspaces.py:discard_workspace", "storage"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.discard_workspace(SURROGATE, "a-1")),
            # W43975 and W39358 put two more entries onto the same store, and
            # both reach `_real` before anything else: the read-only adoption
            # a resuming deployment uses, and the selective removal an
            # ordinary ending performs.
            (at("workspaces.py:adopted_assignment_workspace", "storage"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.adopted_assignment_workspace(
                    SURROGATE, "a-1")),
            (at("workspaces.py:discard_execution_roots", "storage"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.discard_execution_roots(SURROGATE, "a-1")),
            (at("workspaces.py:adopted_assignment_workspace", "assignment_id"),
             "an assignment identity"): ("an assignment identity",
                lambda: workspaces.adopted_assignment_workspace(
                    "/srv/workspaces", 7)),
            (at("workspaces.py:discard_execution_roots", "assignment_id"),
             "an assignment identity"): ("an assignment identity",
                lambda: workspaces.discard_execution_roots(
                    "/srv/workspaces", 7)),
            # W19784: the input root, at the same single owner. `_real`
            # refuses the surrogate as TEXT, before the pair is validated and
            # before anything reaches the filesystem -- so this probe proves
            # the path boundary and not the document one.
            (at("workspaces.py:compose_input_root", "inputs"),
             "a filesystem root"): ("a filesystem root",
                lambda: workspaces.compose_input_root(
                    SURROGATE, {}, {}, assignment=OWNED_ASSIGNMENT,
                    runtime_attempt_id="attempt-1")),
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
            # W16823: the two members this manager now READS out of the
            # projection, because an offer freezes them and the claim decision
            # is held to them.
            (at(f"{A}.project_work", "project_work.scope", "injected"),
             "the projection's effective scope"):
                ("the projection's effective scope",
                 lambda: (setattr(self.session, "_work",
                                  dict(self.session._work, scope=7)),
                          self.issued("offer-ps"))),
            (at(f"{A}.project_work", "project_work.route", "injected"),
             "the projection's route"):
                ("the projection's route",
                 lambda: (setattr(self.session, "_work",
                                  dict(self.session._work, route=7)),
                          self.issued("offer-pr"))),
            (at(f"{A}.slot_holder", "slot_holder", "injected"),
             "the session's slot holder"): ("the session's slot holder",
                lambda: (setattr(self.session, "_held", 7),
                         self.issued("offer-sh"))),
            # W16823: THE RESULT'S OWN ENVELOPE, and then each nested owner
            # under the member it now lives in. The fence's rules did not
            # change; the document it arrives inside did, so the subjects say
            # `claim.assignment.*` where they used to say `claim.*`.
            (at(f"{A}.claim", "claim", "injected"),
             "the claim answer's result"):
                ("the claim answer's result", claiming("offer-cr", whole=7)),
            (at(f"{A}.claim", "claim.assignment", "injected"), "'s identity"):
                ("the claim answer's identity",
                 claiming("offer-ca", assignment=7)),
            (at(f"{A}.claim", "claim.assignment.work_ref", "injected"),
             "'s Work reference"): ("the claim answer's Work reference",
                claiming("offer-cw", work_ref=7)),
            (at(f"{A}.claim", "claim.assignment.work_ref.authority_uuid",
                "injected"),
             "'s authority"): ("the claim answer's authority",
                claiming("offer-cu",
                         work_ref={"authority_uuid": 7, "work_id": WORK})),
            (at(f"{A}.claim", "claim.assignment.work_ref.work_id", "injected"),
             "'s Work id"): ("the claim answer's Work id",
                claiming("offer-ci",
                         work_ref={"authority_uuid": UUID, "work_id": 7})),
            (at(f"{A}.claim", "claim.assignment.participant", "injected"),
             "'s participant"): ("the claim answer's participant",
                claiming("offer-cp", participant=7)),
            (at(f"{A}.claim", "claim.assignment.generation", "injected"),
             "'s generation"): ("the claim answer's generation",
                claiming("offer-cg", generation="not-a-generation")),
            # ...and the decision, which is new rather than moved.
            (at(f"{A}.claim", "claim.decision", "injected"), "'s decision"):
                ("the claim answer's decision",
                 claiming("offer-cd", decision=7)),
            (at(f"{A}.claim", "claim.decision.endpoint", "injected"),
             "'s decision endpoint"): ("the claim answer's decision endpoint",
                claiming("offer-ce", endpoint=7)),
            (at(f"{A}.claim", "claim.decision.principal", "injected"),
             "'s principal"): ("the claim answer's principal",
                claiming("offer-cn", principal=7)),
            (at(f"{A}.claim", "claim.decision.effective_scope", "injected"),
             "'s effective scope"): ("the claim answer's effective scope",
                claiming("offer-cv", effective_scope=7)),
            (at(f"{A}.claim", "claim.decision.role", "injected"),
             "'s decided role"): ("the claim answer's decided role",
                claiming("offer-co", role=7)),
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
            # W16823: the same twelve, by the other door. A commit this
            # manager never saw reaches exactly the columns a submitted claim
            # does, so it is owned exactly as one -- and probing only the
            # claim path would be a rule enforced at one of its two entrances.
            (at(f"{A}.settle_operation", "settle_operation.result",
                "injected"), "the committed claim's result"):
                ("the committed claim's result",
                 committing("offer-mr", whole=7)),
            (at(f"{A}.settle_operation", "settle_operation.result.assignment",
                "injected"), "'s identity"):
                ("the committed claim's identity",
                 committing("offer-mi", assignment=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.assignment.work_ref", "injected"),
             "'s Work reference"):
                ("the committed claim's Work reference",
                 committing("offer-mw", work_ref=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.assignment.work_ref.authority_uuid",
                "injected"),
             "'s authority"): ("the committed claim's authority",
                committing("offer-mu",
                           work_ref={"authority_uuid": 7, "work_id": WORK})),
            (at(f"{A}.settle_operation",
                "settle_operation.result.assignment.work_ref.work_id",
                "injected"),
             "'s Work id"): ("the committed claim's Work id",
                committing("offer-mk",
                           work_ref={"authority_uuid": UUID, "work_id": 7})),
            (at(f"{A}.settle_operation",
                "settle_operation.result.assignment.participant", "injected"),
             "'s participant"): ("the committed claim's participant",
                committing("offer-mp", participant=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.assignment.generation", "injected"),
             "'s generation"):
                ("the committed claim's generation",
                 committing("offer-mg", generation="not-a-generation")),
            (at(f"{A}.settle_operation", "settle_operation.result.decision",
                "injected"), "'s decision"):
                ("the committed claim's decision",
                 committing("offer-md", decision=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.decision.endpoint", "injected"),
             "'s decision endpoint"):
                ("the committed claim's decision endpoint",
                 committing("offer-me", endpoint=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.decision.principal", "injected"),
             "'s principal"): ("the committed claim's principal",
                committing("offer-mn", principal=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.decision.effective_scope",
                "injected"),
             "'s effective scope"): ("the committed claim's effective scope",
                committing("offer-mv", effective_scope=7)),
            (at(f"{A}.settle_operation",
                "settle_operation.result.decision.role", "injected"),
             "'s decided role"): ("the committed claim's decided role",
                committing("offer-mo", role=7)),
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
            # W26294: reconciliation calls a SECOND capability now. `list`
            # answers which containers carry these labels; `observe` answers
            # what one of them is, and an adapter with one and not the other
            # is a narrow adapter this seam cannot use.
            (at("attempts.py:reconcile_runtime", "adapter"),
             "the runtime adapter's observe"):
                ("the runtime adapter's observe",
                 self.observing_without_observe()),
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
            # W61984: the already-quiescent finalization's two caller operands.
            # Unlike a cancellation's, its reason is REQUIRED -- calling the
            # operation is the operator's decision -- so its label carries no
            # "when it is given" and it is owned by `boundaries.text` directly.
            (at("attempts.py:finalize_quiescent_assignment", "attempt_id"),
             "a runtime attempt id"): ("a runtime attempt id",
                lambda: worker_manager.finalize_quiescent_assignment(
                    store, port, attempt_id=SURROGATE,
                    reason="the operator ended it")),
            (at("attempts.py:finalize_quiescent_assignment", "reason"),
             "a finalization reason"): ("a finalization reason",
                lambda: (self.attached(),
                         worker_manager.finalize_quiescent_assignment(
                             store, port, attempt_id="attempt-1",
                             reason=SURROGATE))),
            # W61984 review [P1]: AND THE JOURNAL'S OWN ANSWER, which is the
            # crossing the first round left unmodelled. `transact` hands back
            # this build's document on the call that commits and whatever bytes
            # SQLite kept on every replay, so the decision the fence is issued
            # from re-enters this manager through `adopt_finalization_record`
            # and is owned there. Driven directly, because the operand IS the
            # store's answer and this probe is about the rule rather than about
            # which of the two doors produced it;
            # `tests/tools/test_quiescent_assignment_finalization.py` drives
            # the substituted and corrupted replays through the real journal
            # and pins that neither reaches `port.cancel`.
            (at("attempts.py:adopt_finalization_record", "record"),
             "a committed finalization record"):
                ("a committed finalization record",
                 lambda: attempts.adopt_finalization_record(7)),
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
            # -- W26294: the exact runtime's own state -----------------------
            #
            # Its two members are in `NO_PROBE`, not here. The re-review
            # required every failed or unrecognised exact observation to become
            # a durable `uncertain` rather than a propagated refusal, so these
            # owners still DECIDE and their refusals no longer escape -- see
            # the reason recorded there.
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


class FakeAdapter:
    """The narrow runtime adapter this slice calls through.

    It lists exactly what it started, which is the ordinary case; the cases that
    need a mismatch, a duplicate or an absence build their own.
    """

    def __init__(self, case, runtime_id="runtime-1"):
        self.case = case
        self.runtime_id = runtime_id
        self.started = []
        # W26294: reconciliation now ASKS this adapter what the exact runtime
        # IS instead of reading `running` off a listing that includes exited
        # containers. Every case here that starts a runtime reconciles, so the
        # narrow adapter needs the capability; `running` is the answer that
        # preserves what these cases are about, which is the cancellation
        # crossing rather than the runtime's state.
        self.observation = {"state": "running", "why": "it is up",
                            "mounts": None}

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
                "policy_digest": row["policy_digest"],
                "adapter_digest": row["adapter_digest"]}

    def start(self, operands):
        self.started.append(operands)
        return {"runtime_id": self.runtime_id, "labels": operands["labels"]}

    def list(self, operands):
        if not self.started:
            return []
        return [{"runtime_id": self.runtime_id,
                 "labels": self.started[0]["labels"]}]

    def observe(self, runtime_id):
        return self.observation

    def stop(self, operands):
        return {"stopped": True}


class _WithoutObserve(FakeAdapter):
    """W26294: an adapter that lists and cannot observe.

    The capability probe needs an adapter that gets PAST the listing and then
    has nothing to answer with -- `object()` would be refused by
    `reconcile_runtime`'s own `list` capability check first, and would probe
    that instead.
    """

    observe = None


class FakeAgent:
    def __init__(self):
        self.cancelled = []

    def cancel(self, operands):
        self.cancelled.append(operands)
        return {"acknowledged": True}


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

    def test_the_universe_sees_the_engine_answer_and_every_consumed_member(self):
        """The branch join must not hide members of an injected answer.

        W43977 review 2026-08-30T18:25:36Z. `ast.walk` reaches the top-level
        `taken = document(answer, ...)` before either nested assignment to
        `answer`, so a one-pass origin projection saw the envelope and lost
        all three members subsequently consumed from it. The inventory must
        discover these from source structure; a declaration table would make
        the check circular again.
        """
        entries = receiving_entries()
        for subject in ("run", "run.status", "run.stdout", "run.stderr"):
            with self.subTest(subject=subject):
                self.assertIn(
                    ("injected", "oci.py:EnginePort.__call__", subject),
                    entries)

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
        # W10265: the container is SORTED so that this assertion's failure text
        # is the same bytes on every run. `entries` is a set, and `assertIn`
        # renders the whole container when membership fails, so an unsorted one
        # reported the same stale entry in a different order every time and
        # made "did this change?" unanswerable by diff. Membership in a sorted
        # list is the same question as membership in the set it came from.
        entries = receiving_entries()
        for table, what in ((STATED_OWNERS, "stated"), (DELEGATED, "delegated")):
            for entry in sorted(table):
                with self.subTest(table=what, entry=entry):
                    self.assertIn(entry, sorted(entries))

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

    # W35557: EVERY SITE THAT ADOPTS AN ATTEMPT ROW, and the driver that
    # reaches it. Three modules read this one table through
    # `boundaries.row(..., ATTEMPT_COLUMNS)`, and each was covered differently
    # -- two by hand-written column lists that drifted out of date, and the
    # third not at all.
    ATTEMPT_ROW_SITES = ("attempts.py:_attempts", "intake.py:_attempt_of",
                         "output.py:_attempt_of")

    # THE COLUMNS A CORRUPTION PROBE CANNOT DRIVE ARE `NO_PROBE`'S, and this
    # derivation reads that table rather than keeping a second list. An
    # exemption declared in two places is one that can be lifted in one of
    # them -- and `test_every_unprobed_entry_is_a_real_owned_entry` already
    # holds every `NO_PROBE` entry to being live and owned, which is exactly
    # the "explicit, justified, and checked" this correction is asked for.

    def attempt_probes(self):
        """One probe per adopted ATTEMPT column, per site that adopts one.

        DERIVED FROM THE TABLE CONTRACT, for the reason `column_probes` gives
        for offers and operations: a column added to a contract and never
        spoiled is exactly the gap this file keeps being corrected for. Two of
        these three sites had hand-written lists, and both had drifted -- one
        was missing four columns and the other was declaring seven the
        inventory no longer attributes to it.
        """
        entries = receiving_entries()
        found = {}
        for site in self.ATTEMPT_ROW_SITES:
            driver = self.spoiling_attempt_at(site)
            for name in sorted(schema.ATTEMPT_COLUMNS):
                entry = ("adopted", site, f"attempts.{name}")
                if entry not in entries or entry in NO_PROBE \
                        or self.owned_by_sqlite(schema.ATTEMPT_COLUMNS[name]):
                    continue
                found[(entry, "a persisted attempt")] = (
                    "a persisted attempt", driver(name))
            envelope = ("adopted", site, "attempts")
            if envelope in entries:
                found[(envelope, "a persisted attempt")] = (
                    "a persisted attempt", driver("execution_runtime"))
        return found

    def spoiling_attempt_at(self, site):
        """The driver that reaches ONE site's adoption of the attempt row.

        Each module reads the table through its own private crossing, so a
        probe has to enter through that module's own public operation --
        driving somebody else's would prove somebody else's owner.
        """
        if site == "intake.py:_attempt_of":
            return self.spoiling_intake_attempt
        if site == "output.py:_attempt_of":
            return self.spoiling_output_attempt
        return self.spoiling_attempts_attempt

    def spoiling_attempts_attempt(self, column):
        """`attempts.py`'s own crossing, driven through `observe`.

        The cheapest public operation in that module that reads the row and
        does nothing else first: `_require_attempt` adopts it before any axis
        rule runs, so a spoiled column is refused at the row rather than at a
        transition.
        """
        def run():
            self.output_world()
            self.corrupt(f"UPDATE attempts SET {column} = ?",
                         self.SPOILED[schema.ATTEMPT_COLUMNS[column].kind])
            worker_manager.observe(self.store, attempt_id="attempt-1",
                                   axis="consent_runtime", value="running")
        return run

    def lane_probes(self):
        """W32649: one probe per `runtime_lanes` column this build reads.

        DERIVED FROM THE TABLE CONTRACT rather than listed, for the reason the
        offers and operations columns are: a column added to a contract and
        never spoiled is exactly the gap this file keeps being corrected for.

        BOTH READING SITES GET THEIR OWN ENTRY and share one probe, because
        they share one LABEL -- `runtime_lane` asks the holder first and the
        Work's lanes second, so a spoiled column is refused at whichever runs
        first and the refusal names the same document either way. The entry is
        what the inventory tracks; the label is what a probe proves it reached.
        """
        entries = receiving_entries()
        found = {}
        # W32649 review [P2]: FOUR READS, not two. The projection pair reads
        # this relation to ANSWER about it; the start pair reads it to DECIDE
        # whether a runtime may exist. An inventory that enumerated only the
        # first two is exactly how the second two came to use partial rows.
        for site, probe in (("lanes.py:_no_predecessor_holds",
                             self.spoiling_predecessor_lane),
                            ("lanes.py:_occupy_lane",
                             self.spoiling_colliding_lane)):
            for name in sorted(schema.RUNTIME_LANE_COLUMNS):
                entry = ("adopted", site, f"runtime_lanes.{name}")
                if entry not in entries or self.owned_by_sqlite(
                        schema.RUNTIME_LANE_COLUMNS[name]):
                    continue
                found[(entry, "a persisted runtime lane")] = (
                    "a persisted runtime lane", probe(name))
            entry = ("adopted", site, "runtime_lanes")
            if entry in entries:
                found[(entry, "a persisted runtime lane")] = (
                    "a persisted runtime lane", probe("holder"))
        for site in ("lanes.py:_holder_of", "lanes.py:_work_lanes"):
            for name in sorted(schema.RUNTIME_LANE_COLUMNS):
                entry = ("adopted", site, f"runtime_lanes.{name}")
                if entry not in entries or self.owned_by_sqlite(
                        schema.RUNTIME_LANE_COLUMNS[name]):
                    continue
                found[(entry, "a persisted runtime lane")] = (
                    "a persisted runtime lane", self.spoiling_lane(name))
            entry = ("adopted", site, "runtime_lanes")
            if entry in entries:
                found[(entry, "a persisted runtime lane")] = (
                    "a persisted runtime lane", self.spoiling_lane("holder"))
        return found

    def spoiling_predecessor_lane(self, column):
        """A PREDECESSOR's lane row, spoiled, read by a successor's start.

        The row is held by another attempt over the same Work, so the
        predecessor query selects it -- and a start that reaches it must own
        the whole relation before reporting a holder from it.
        """
        def run():
            attempt_id = self.bound_attempt()
            row = self.attempt_row_of(attempt_id)
            self.corrupt(
                "INSERT INTO runtime_lanes (lane_id, authority_uuid, work_id, "
                "principal, effective_scope, holder, reason, occupied_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                "lane:predecessor", row["authority_uuid"], row["work_id"],
                row["assignment_principal"], row["assignment_scope"],
                "attempt-predecessor", "held for a probe", NOW)
            self.corrupt(f"UPDATE runtime_lanes SET {column} = ?",
                         self.SPOILED[
                             schema.RUNTIME_LANE_COLUMNS[column].kind])
            worker_manager.request_runtime_start(
                self.store, FakeAdapter(self), attempt_id=attempt_id)
        return run

    def spoiling_colliding_lane(self, column):
        """A row this attempt's own start COLLIDES with, spoiled.

        Held by this attempt, so the predecessor query excludes it -- which is
        precisely the path the review found: a row that evades the first
        query and is met at the primary key instead. `lane_id` is the derived
        one, so the insert really conflicts.
        """
        def run():
            attempt_id = self.bound_attempt()
            row = self.attempt_row_of(attempt_id)
            reference = worker_manager.lane_reference(row)
            self.corrupt(
                "INSERT INTO runtime_lanes (lane_id, authority_uuid, work_id, "
                "principal, effective_scope, holder, reason, occupied_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                lanes._lane_id(reference), row["authority_uuid"],
                row["work_id"], row["assignment_principal"],
                row["assignment_scope"], attempt_id, "held for a probe", NOW)
            self.corrupt(f"UPDATE runtime_lanes SET {column} = ?",
                         self.SPOILED[
                             schema.RUNTIME_LANE_COLUMNS[column].kind])
            worker_manager.request_runtime_start(
                self.store, FakeAdapter(self), attempt_id=attempt_id)
        return run

    def spoiling_lane(self, column):
        def run():
            attempt_id = self.output_world()
            row = self.attempt_row_of(attempt_id)
            self.corrupt(
                "INSERT INTO runtime_lanes (lane_id, authority_uuid, work_id, "
                "principal, effective_scope, holder, reason, occupied_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                "lane:probe", row["authority_uuid"], row["work_id"],
                row["assignment_principal"], row["assignment_scope"],
                attempt_id, "held for a probe", NOW)
            self.corrupt(f"UPDATE runtime_lanes SET {column} = ?",
                         self.SPOILED[
                             schema.RUNTIME_LANE_COLUMNS[column].kind])
            worker_manager.runtime_lane(self.store, attempt_id)
        return run

    def attempt_row_of(self, attempt_id):
        found = self.store._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone()
        return {key: found[key] for key in found.keys()}

    def custody_probes(self):
        """One driver per (entry, label) W43977 declared for `custody.py`.

        EACH DRIVES THE DELEGATE'S OWN REFUSAL, which is the whole point of a
        delegation: `custody_act` forwards these to the private composer and
        the engine port, so the SAME refusal has to arrive through the public
        entry or the declaration is a note rather than a fact.

        THE ORDER IS WHY EACH PROBE VARIES ONE OPERAND. `_custody_vector`
        holds the engine, then the image digest, then the verb, and only then
        performs the durable lookup that owns the attempt and the root kind --
        so a probe that spoiled two would prove the earlier one twice and the
        later one never.
        """
        from baton_v12.worker_manager import custody

        def at(site, subject):
            return ("caller", f"custody.py:{site}", subject)

        def acting(**overrides):
            body = {"engine": "docker", "run": lambda argv: {},
                    "image_digest": self.OCI_IMAGE, "store": self.store,
                    "assignment_id": "attempt-1", "operation": "normalize",
                    "which": "workspace"}
            body.update(overrides)
            engine = body.pop("engine")
            run = body.pop("run")
            return lambda: custody.custody_act(engine, run, **body)

        class Seam:
            custodian_image_digest = "sha256:" + "c" * 64

            def normalize_directory(self, store, *, assignment_id, which):
                raise AssertionError("the root kind is held before the act")

        class Untyped:
            """Carries the act and no identity to sign it with."""
            custodian_image_digest = 7

            def normalize_directory(self, store, *, assignment_id, which):
                raise AssertionError("the image identity is held first")

        found = {
            # The two owners this module holds directly, each at its own site.
            (at("check_custody_operation", "operation"),
             "a custody operation"): (
                "a custody operation",
                lambda: custody.check_custody_operation(7)),
            (at("check_custody_root", "which"), "a custody root name"): (
                "a custody root name", lambda: custody.check_custody_root(7)),
            # The attempt, at both public composition entries.
            (at("normalize_directory", "assignment_id"),
             "an assignment identity"): (
                "an assignment identity",
                lambda: custody.normalize_directory(
                    self.store, Seam(), assignment_id=7, which="workspace")),
            (at("adopted_directory_custody", "assignment_id"),
             "an assignment identity"): (
                "an assignment identity",
                lambda: custody.adopted_directory_custody(
                    self.store, Seam(), 7, "workspace")),
            # The typed seam itself: it must BE the act, and it must carry the
            # identity the receipt is signed with. Two rules, two probes.
            (at("normalize_directory", "custody"),
             "the runtime adapter's directory-custody act"): (
                "the runtime adapter's directory-custody act",
                lambda: custody.normalize_directory(
                    self.store, object(), assignment_id="attempt-1",
                    which="workspace")),
            (at("normalize_directory", "custody"),
             "the custodian image identity this act is signed with"): (
                "the custodian image identity this act is signed with",
                lambda: custody.normalize_directory(
                    self.store, Untyped(), assignment_id="attempt-1",
                    which="workspace")),
            (at("adopted_directory_custody", "custody"),
             "the custodian image identity this act is signed with"): (
                "the custodian image identity this act is signed with",
                lambda: custody.adopted_directory_custody(
                    self.store, Untyped(), "attempt-1", "workspace")),
            (at("custody_act", "engine"), "an engine name"): (
                "an engine name", acting(engine=7)),
            (at("custody_act", "run"), "the engine's run operation"): (
                "the engine's run operation", acting(run=7)),
            (at("custody_act", "image_digest"), "an image digest"): (
                "an image digest", acting(image_digest=7)),
            (at("custody_act", "operation"), "a custody operation"): (
                "a custody operation", acting(operation=7)),
            (at("custody_act", "which"), "a custody root name"): (
                "a custody root name", acting(which=7)),
            (at("custody_act", "assignment_id"), "an assignment identity"): (
                "an assignment identity", acting(assignment_id=7)),
            # The two public composition entries share the one root-kind owner
            # with the act, and each holds it before it touches the capability
            # it was given -- which is what the `Seam` above asserts by
            # refusing to be reached.
            (at("normalize_directory", "which"), "a custody root name"): (
                "a custody root name",
                lambda: custody.normalize_directory(
                    self.store, Seam(), assignment_id="attempt-1", which=7)),
            (at("adopted_directory_custody", "which"),
             "a custody root name"): (
                "a custody root name",
                lambda: custody.adopted_directory_custody(
                    self.store, Seam(), "attempt-1", 7)),
        }
        return found

    def worker_entry_probes(self):
        """W39666: the worker-entry transport's layer and delegated owners.

        Six pairs, and every one of them is driven through a PUBLIC operation
        of this slice rather than through the delegate. A delegation nobody
        exercised at the site that has it is a rule that site does not
        actually have -- the same reason the shared engine name is driven at
        each of its six vectors above.
        """
        from baton_v12.worker_manager import worker_entry

        W = "worker_entry.py"
        program = ["python3", "/opt/baton/baton_worker.py"]

        def opened(argv, *, seconds):
            raise AssertionError("the channel was opened anyway")

        def conversing(**spoiled):
            operands = dict(engine="docker", runtime_id="8fce41c0d2b4",
                            program=list(program), session="session-w39666",
                            operations=["describe"], operation_ids=["op-1"],
                            seconds=30)
            port = spoiled.pop("channel_port", opened)
            operands.update(spoiled)
            return lambda: worker_entry.converse(port, **operands)

        found = {}
        # THE CAPABILITY, at the port that types it and at the operation that
        # constructs one from a raw open operation.
        for entry, drive in (
                (("caller", f"{W}:ChannelPort.__init__", "open_channel"),
                 lambda: worker_entry.ChannelPort(SURROGATE)),
                (("caller", f"{W}:converse", "channel_port"),
                 conversing(channel_port=SURROGATE))):
            found[(entry, "the channel's open operation")] = (
                "the channel's open operation", drive)
        found[(("caller", f"{W}:converse", "session"),
               "the launched worker session")] = (
            "the launched worker session", conversing(session=SURROGATE))
        # THE TWO THAT TRAVEL INTO THE EXEC VECTOR, each driven from
        # `converse` so the forward itself is what is exercised.
        found[(("caller", f"{W}:converse", "engine"), "an engine name")] = (
            "an engine name", conversing(engine=SURROGATE))
        found[(("caller", f"{W}:converse", "runtime_id"), "a runtime id")] = (
            "a runtime id", conversing(runtime_id=SURROGATE))
        # W39356's retained network obligation, owned by the private helper
        # and driven at the public operand that forwards to it.
        found[(("caller", "oci.py:run_vector", "network"),
               "an engine network")] = (
            "an engine network", self.running_vector(network=SURROGATE))
        return found

    def all_probes(self):
        return {**self.probes(), **self.column_probes(),
                **self.custody_probes(),
                **self.attempt_probes(), **self.lane_probes(),
                **self.session_probes(), **self.output_probes(),
                **self.interrogation_probes(), **self.oci_probes(),
                **self.intake_probes(), **self.sealing_probes(),
                **self.credential_probes(), **self.launch_probes(),
                **self.worker_entry_probes()}

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
        # THE KEY UNIVERSE ONCE, THE FIXTURE-BOUND CATALOG PER PROBE. W54182:
        # which (entry, label) pairs exist is a property of the source inventory
        # and the static probe tables, so the keys are taken once. The catalog's
        # VALUES are not a property of the source: its closures capture THIS
        # fixture's store, credential homes and ports, so a catalog carried
        # across fixtures would either hand a later probe an already-closed
        # store or let two probes share one. It is rebuilt inside each fresh
        # fixture instead, which the memoised discovery above makes cheap.
        keys = sorted(self.all_probes())
        # AND THE FRAMEWORK'S OWN FIXTURE IS RELEASED BEFORE THE LOOP. `unittest`
        # already called `setUp` once to get here; leaving its store open would
        # be the same leak this correction is about, one fixture smaller.
        self.doCleanups()
        for entry, fragment in keys:
            with self.subTest(entry=entry, label=fragment):
                # ONE FIXTURE PER PROBE, RECLAIMED IMMEDIATELY -- including when
                # the probe fails and when `setUp` itself does, which is why the
                # setup is inside the `try`. This loop used to call `setUp` 549
                # times against one cleanup stack: 1,098 temporary directories
                # and SQLite connections waited for the end of the test while
                # `self._root`, `self.store`, `self.session` and `self.port`
                # were overwritten under them, and the measured file-descriptor
                # count grew with the probe count instead of staying flat.
                try:
                    self.setUp()
                    full, probe = self.all_probes()[(entry, fragment)]
                    # The fragment is what the SOURCE says; the full label is
                    # what the refusal must carry. Requiring the one to contain
                    # the other is what stops a probe naming a boundary it never
                    # reaches.
                    self.assertIn(fragment, full)
                    self.refusing(full, probe)
                finally:
                    self.doCleanups()

    def test_the_missing_probe_check_can_actually_fail(self):
        """Every entry has a probe today, so relaxing the check changes no
        verdict -- measured.

        The way to test a guard with nothing to catch is to hand it something:
        drop one probe and require the difference to name exactly that entry.
        """
        declared = set(self.all_probes())
        wanted = self.expected()
        # W10265: `sorted(...)` against `[]` rather than the set against
        # `set()`, matching the already-stable form two tests above. The
        # emptiness verdict is identical; what changes is that a NONEMPTY
        # difference lists its entries in one fixed order instead of hash
        # order, which is the only reason this line was reordering run to run.
        #
        # AND THE WHOLE LIST, which the first correction cost and review R1
        # caught. `assertEqual` over two lists dispatches to unittest's list
        # comparison, and its default `maxDiff` replaced eight of the nine
        # missing entries with a truncation notice -- so the diagnostic became
        # deterministic and stopped saying what was missing, which is the
        # failure-context half of this record's own acceptance. Approved as a
        # test-local assignment (T10265, message 11462): it changes what THIS
        # diagnostic prints and nothing else, where a global setting would be
        # the output normalization the same ruling excludes.
        self.maxDiff = None
        self.assertEqual(sorted(wanted - declared), [])
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
    # -- W6632: the constrained OCI adapter core -----------------------------
    ("caller", "oci.py:run_vector", "mounts"):
        "test_a_mount_sequence_is_iterated_and_never_read",
    ("caller", "oci.py:OciAdapter.__init__", "mounts"):
        "test_a_mount_sequence_is_iterated_and_never_read",
    ("caller", "oci.py:run_vector", "mounts.writable"):
        "test_a_writable_flag_is_a_yes_or_a_no",
    ("caller", "oci.py:stop_vector", "seconds"):
        "test_a_stop_timeout_is_a_positive_whole_number",
    ("caller", "oci.py:OciAdapter.observe", "document.Running"):
        "test_an_unrecognised_running_member_is_uncertain_and_never_absent",
    # -- W6627: the operator interrogation split -----------------------------
    ("caller", "interrogation.py:probe", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "interrogation.py:inquire", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("caller", "interrogation.py:interrogations_of", "session_epoch"):
        "test_a_session_epoch_counts_from_one",
    ("injected", "interrogation.py:probe", "agent.probe.kind"):
        "test_an_interrogation_discriminator_decides_before_anything_is_read",
    ("injected", "interrogation.py:inquire", "agent.inquire.kind"):
        "test_an_interrogation_discriminator_decides_before_anything_is_read",
    # -- W6628: the output freeze and the sealed receiver --------------------
    ("caller", "manifests.py:retain_manifest", "document"):
        "test_a_manifest_is_owned_by_the_contracts_own_composite",
    ("caller", "output.py:record_frozen_result", "sealed"):
        "test_a_manifest_is_owned_by_the_contracts_own_composite",
    ("injected", "output.py:request_freeze", "adapter.seal"):
        "test_what_the_adapter_seals_is_owned_where_it_arrives",
    # -- W19784: the two manager-authored `/input/` documents ----------------
    ("caller", "workspaces.py:compose_input_root", "input_manifest"):
        "test_the_input_pair_is_owned_by_the_contracts_own_composite",
    ("caller", "workspaces.py:compose_input_root", "assignment_manifest"):
        "test_the_input_pair_is_owned_by_the_contracts_own_composite",
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
    ("injected", "oci.py:EnginePort.__call__", "run.status"):
        "test_an_engine_status_is_a_whole_number_and_zero_is_ordinary",
    ("injected", "oci.py:EnginePort.__call__", "run.stdout"):
        "test_an_engine_stream_is_text_that_may_be_empty",
    ("injected", "oci.py:EnginePort.__call__", "run.stderr"):
        "test_a_quiet_engine_stderr_is_not_a_fault",
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
        "test_the_bearer_is_acceptances_capability_and_no_declines",
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
    ("caller", "documents.py:finalize_intent", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:attempt_finalized", "members"):
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
    ("caller", "documents.py:interrogation_requested", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:interrogation", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:interrogation", "members.observation"):
        "test_an_absent_observation_is_omitted_and_not_nulled",
    ("caller", "authority_port.py:AuthorityPort.publish_answer", "work_ref"):
        "test_an_answer_is_published_by_the_manager_and_never_the_worker",
    ("caller", "authority_port.py:AuthorityPort.publish_answer",
     "operation_id"):
        "test_an_answer_is_published_by_the_manager_and_never_the_worker",
    ("caller", "authority_port.py:AuthorityPort.publish_answer", "body"):
        "test_an_answer_is_published_by_the_manager_and_never_the_worker",
    ("adopted", "attempts.py:_next_source_seq", "observations"):
        "test_a_minted_sequence_is_whole_because_the_column_is",
    ("adopted", "store.py:ControlStore._objects", "sqlite_master"):
        "test_the_catalogue_decides_one_membership_question",
    # -- W6629: intake, retention and cleanup --------------------------------
    #
    # Eight of these ten are the closed outbound constructors, and their
    # witness is DERIVED from `documents.CONTRACTS` rather than listed -- so a
    # constructor added tomorrow is exercised tomorrow, which is the property
    # that made these eight arrive with the gate already able to see them.
    # -- W6634: the assignment-scoped credential lifecycle -------------------
    ("caller", "credentials.py:resolved_delivery", "slots"):
        "test_a_credential_sequence_is_a_list_of_owned_members",
    ("caller", "credentials.py:Delivery.__init__", "state"):
        "test_a_delivery_is_one_of_the_closed_lifecycle_states",
    ("caller", "credentials.py:Delivery.__init__", "bearers"):
        "test_a_deliverys_bearers_are_keyed_by_a_proved_slot",
    ("caller", "credentials.py:CredentialHome.tear_down", "delivery"):
        "test_a_teardown_acts_on_a_delivery_this_manager_materialized",
    ("caller", "oci.py:OciAdapter.__init__", "credential_delivery"):
        "test_a_teardown_acts_on_a_delivery_this_manager_materialized",
    # -- W26291: the worker's launch document --------------------------------
    ("caller", "launch.py:LaunchDelivery.__init__", "attempt_id"):
        "test_a_launch_mount_acts_on_a_delivery_this_manager_materialized",
    ("caller", "launch.py:LaunchDelivery.__init__", "root"):
        "test_a_launch_mount_acts_on_a_delivery_this_manager_materialized",
    ("caller", "launch.py:LaunchDelivery.__init__", "place"):
        "test_a_launch_mount_acts_on_a_delivery_this_manager_materialized",
    ("caller", "launch.py:LaunchDelivery.__init__", "document"):
        "test_a_launch_mount_acts_on_a_delivery_this_manager_materialized",
    ("caller", "launch.py:discard", "root"):
        "test_discarding_a_root_this_module_did_not_make_is_absence",
    ("caller", "oci.py:OciAdapter.__init__", "launch_delivery"):
        "test_a_launch_mount_acts_on_a_delivery_this_manager_materialized",
    ("caller", "sealing.py:sealed_result", "roots"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "roots.workspace"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "declared"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "identity"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "identity.policy_digest"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "input_manifest_digest"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:collected_result", "custody"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:sealed_result", "custody"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.collect", "operands.attempt_id"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "sealing.py:collected_result", "declared"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.attempt_id"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.generation"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.participant"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.work_ref"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.work_ref.authority_uuid"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.seal", "request.assignment.work_ref.work_id"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.collect", "operands"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.__init__", "outputs"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.__init__", "input_manifest_digest"):
        "test_a_declaration_is_owned_once_at_construction",
    ("caller", "oci.py:OciAdapter.start", "labels.runtime_attempt_id"):
        "test_one_delivery_belongs_to_one_attempt",
    ("caller", "documents.py:collect_requested", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:intake_artifact", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:intake_receipt", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:retention", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:retention_decided", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:cleanup_blocked", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:cleanup_unsettled", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:cleanup_settled", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:retain_command", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    ("caller", "documents.py:destroy_command", "members"):
        "test_every_outbound_constructor_holds_its_contract",
    # And the two that state a rule of their own.
    ("injected", "intake.py:request_intake", "adapter.collect"):
        "test_what_the_adapter_collects_is_owned_where_it_arrives",
    ("caller", "intake.py:decide_retention", "artifact_ids"):
        "test_a_retention_names_artifacts_and_owns_every_one_of_them",
    ("caller", "intake.py:retain_operation", "artifact_ids"):
        "test_a_retention_names_artifacts_and_owns_every_one_of_them",
    ("caller", "intake.py:retain_operation", "disposition"):
        "test_a_retention_names_artifacts_and_owns_every_one_of_them",
    ("injected", "intake.py:decide_retention", "adapter.retain"):
        "test_what_the_retain_adapter_answers_decides_nothing",
    # -- W39666: the worker-entry transport ----------------------------------
    ("caller", "oci.py:exec_vector", "program"):
        "test_an_exec_program_is_a_sequence_of_words_and_not_a_string",
    ("caller", "worker_entry.py:converse", "program"):
        "test_a_conversations_program_is_held_to_the_exec_program_rule",
    ("caller", "worker_entry.py:converse", "operations"):
        "test_a_conversation_asks_for_a_sequence_of_known_operations",
    ("caller", "worker_entry.py:converse", "operation_ids"):
        "test_operation_identities_are_a_sequence_one_per_operation",
    ("caller", "worker_entry.py:converse", "seconds"):
        "test_a_worker_entry_bound_is_a_positive_whole_number",
    ("caller", "worker_entry.py:_Reader.__init__", "channel"):
        "test_a_reader_only_ever_receives_a_channel_the_port_proved",
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


class StatedRules(BoundaryCase):
    """The witnesses themselves. Each exercises one stated rule."""

    # -- W6627's stated owners, exercised through the public operation -------

    # -- W43977's engine-answer members, one witness each --------------------

    @staticmethod
    def _answering(**members):
        from baton_v12.worker_manager import oci

        body = {"status": 1, "stdout": "out", "stderr": "err"}
        body.update(members)
        return oci.EnginePort(lambda argv: body)(["docker", "version"])

    def test_an_engine_status_is_a_whole_number_and_zero_is_ordinary(self):
        """`_status` owns it, and ZERO is what success looks like.

        A rule that refused zero would refuse every engine act that worked,
        which is why no existing boundary kind fits this member.
        """
        self.assertEqual(self._answering(status=0)["status"], 0)
        # EACH IS JSON DATA and wrong only for THIS member: the envelope's own
        # walk refuses a float or bytes first, so such a probe would prove the
        # envelope's rule and call it the member's.
        for wrong in ("0", True, None, []):
            with self.subTest(status=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self._answering(status=wrong)
                self.assertIn("exit status", str(caught.exception))

    def test_an_engine_stream_is_text_that_may_be_empty(self):
        """`_stream` owns it, and the EMPTY string is admitted on purpose."""
        self.assertEqual(self._answering(stdout="")["stdout"], "")
        for wrong in (7, None, {}):
            with self.subTest(stdout=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self._answering(stdout=wrong)
                self.assertIn("stdout", str(caught.exception))

    def test_a_quiet_engine_stderr_is_not_a_fault(self):
        """The same owner at the other stream, witnessed independently: two
        entries that share a rule are still two crossings."""
        self.assertEqual(self._answering(stderr="")["stderr"], "")
        with self.assertRaises(ContractRefusal) as caught:
            self._answering(stderr=[])
        self.assertIn("stderr", str(caught.exception))

    def test_an_interrogation_discriminator_decides_before_anything_is_read(
            self):
        """An unrecognised answer is refused rather than read as the least
        alarming member of the set -- and each operation has its OWN set,
        because a probe is never queued and an inquire is never observed."""
        provider = self.interrogating()
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.probe(
                self.store, self.port,
                _Interrogating(provider, probe={"kind": "queued"}),
                attempt_id="attempt-1", posture="execution", session_epoch=1,
                operation_id="probe-x", deadline_seconds=30)
        self.assertIn("an agent probe answer answers", caught.exception.message)
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.inquire(
                self.store, self.port,
                _Interrogating(provider, inquire={"kind": "observed"}),
                attempt_id="attempt-1", posture="execution", session_epoch=1,
                operation_id="inquire-x", deadline_seconds=30,
                question="how is it going?")
        self.assertIn("an agent inquiry acknowledgement answers",
                      caught.exception.message)

    # -- W6632's stated owners, exercised through the public operation ------

    OCI_ROOTS = {"inputs": "/srv/a-1/inputs",
                 "workspace": "/srv/a-1/workspace"}
    # EXACTLY the frozen `runtime.labels` member set, taken from the contract
    # rather than retyped: a fixture with an invented member would make every
    # case here refuse for the label document's reason instead of its own.
    OCI_LABELS = {"runtime_attempt_id": "attempt-1", "authority_uuid": UUID,
                  "work_id": WORK, "participant": WHO, "generation": 1,
                  # W16823 adds these two, beside the fence.
                  "principal": PRINCIPAL, "effective_scope": SCOPE,
                  "profile_digest": "sha256:" + "b" * 64,
                  "policy_digest": "sha256:" + "d" * 64,
                  "adapter_digest": "sha256:" + "c" * 64}

    def vector(self, **overrides):
        from baton_v12.worker_manager import oci
        operands = dict(image_digest="sha256:" + "e" * 64,
                        labels=dict(self.OCI_LABELS),
                        assignment_roots=dict(self.OCI_ROOTS),
                        posture="execution",
                        # W33936: an execution vector is given the
                        # deployment's configured workspace group, and one
                        # without it refuses before every rule below -- so a
                        # probe that omitted it would land on that refusal
                        # rather than on the boundary it names.
                        workspace_group=self.configured_group(),
                        name="baton-op-1")
        operands.update(overrides)
        return oci.run_vector("docker", **operands)

    # -- W6634: the assignment-scoped credential lifecycle -------------------

    def credentials(self):
        from baton_v12.worker_manager import credentials
        return credentials

    def a_delivery(self, **spoiled):
        credentials = self.credentials()
        body = {"attempt_id": "attempt-1",
                "root": "/srv/a-1/credentials/attempt-1",
                "slots": [{"slot": "api", "provider": "vault",
                           "target": "/run/baton/credentials/api"}],
                "state": "live", "bearers": {"api": "a" * 40}}
        body.update(spoiled)
        return credentials.Delivery(**body)

    def test_a_credential_sequence_is_a_list_of_owned_members(self):
        """A LIST IS NOT A CROSSING; its members are.

        Each of the three sequences this lifecycle takes proves the shape and
        then hands every member to the rule that owns it -- and the member
        rules are the ones the probe table exercises. What this asserts is the
        half a probe cannot: that something other than a list refuses, and
        that a well-shaped list of ill-formed members refuses too.
        """
        credentials = self.credentials()
        home = credentials.CredentialHome("/srv/a-1")
        for spoiled in ("not a list", 7, None, {"api": "yes"}):
            with self.subTest(spoiled=spoiled, door="resolved_delivery"):
                with self.assertRaises(ContractRefusal):
                    credentials.resolved_delivery(spoiled, profile={})
            with self.subTest(spoiled=spoiled, door="materialize"):
                with self.assertRaises(ContractRefusal):
                    home.materialize(
                        spoiled, attempt_id="attempt-1",
                        workspace_group=self.configured_group(),
                        credential_provider=lambda a, b: "x" * 40)
            with self.subTest(spoiled=spoiled, door="Delivery"):
                with self.assertRaises(ContractRefusal):
                    self.a_delivery(slots=spoiled)
        # AND A LIST WHOSE MEMBERS ARE WRONG, which is the half that says the
        # sequence rule did not stop at the shape.
        with self.assertRaises(ContractRefusal):
            credentials.resolved_delivery(["../escape"], profile={})
        with self.assertRaises(ContractRefusal):
            self.a_delivery(slots=[{"slot": "api"}])

    def test_a_delivery_is_one_of_the_closed_lifecycle_states(self):
        """A comparison against this module's own constant, not a boundary."""
        credentials = self.credentials()
        for state in credentials.LIFECYCLE_STATES:
            with self.subTest(state=state):
                self.assertEqual(self.a_delivery(state=state).state, state)
        for spoiled in ("invented", "", None, 7, "LIVE"):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    self.a_delivery(state=spoiled)

    def test_a_deliverys_bearers_are_keyed_by_a_proved_slot(self):
        """The keys are owned; the VALUES are never named in a refusal.

        Every other rule in this package puts the value it rejected into its
        diagnostic. Here that would be the one thing §13 exists to keep off a
        durable surface -- and a refusal is a durable surface, which is what
        `errors.py` established for §13 in the first place.
        """
        from baton_v12.contracts import held_secret
        bearer = "b" * 40
        with held_secret(bearer):
            with self.assertRaises(ContractRefusal) as caught:
                self.a_delivery(bearers={"../escape": bearer})
            self.assertNotIn(bearer, caught.exception.message)
            for spoiled in (["api"], "api", None):
                with self.subTest(spoiled=spoiled):
                    with self.assertRaises(ContractRefusal):
                        self.a_delivery(bearers=spoiled)

    def test_a_launch_value_is_bounded_text_with_no_nul(self):
        """W26291. One owner for all three values, and one literal label.

        The ceilings differ -- `session` is what every frame binds to and is
        held to the WORKER's own identity bound, while a contract line and a
        role are operator prose -- but the rule is one rule and it lives at
        one site.
        """
        from baton_v12.worker_manager import launch

        def authored(**spoiled):
            body = {"session": "session-1", "contract": "do the thing",
                    "role": "implementer"}
            body.update(spoiled)
            return lambda: launch.launch_document(**body)

        for name in ("session", "contract", "role"):
            for spoiled, why in ((None, "null"), ("", "empty"), (7, "not text"),
                                 ("nul\x00inside", "a NUL")):
                with self.subTest(name=name, why=why):
                    with self.assertRaises(ContractRefusal):
                        authored(**{name: spoiled})()
        # THE TWO CEILINGS, and that they are different is the point.
        with self.assertRaises(ContractRefusal):
            authored(session="s" * (launch.MAX_SESSION + 1))()
        with self.assertRaises(ContractRefusal):
            authored(role="r" * (launch.MAX_LAUNCH_VALUE + 1))()
        # AND THE SAME REFUSALS ARRIVE THROUGH `materialize`, which forwards
        # rather than owning a second time.
        with self.assertRaises(ContractRefusal):
            launch.materialize("/srv/launch", attempt_id="attempt-1",
                               session="", contract="c", role="r")

    def test_a_launch_mount_acts_on_a_delivery_this_manager_materialized(self):
        """What proves a launch delivery is that it IS one.

        Everything inside it was owned when `materialize` authored it, so the
        rule at these doors is identity of kind rather than a re-walk of
        members a constructor already proved -- and a mapping or a PATH would
        be exactly the caller-selected locator the fixed target removes.
        """
        from baton_v12.worker_manager import launch, oci

        composed = {"attempt_id": "attempt-1", "root": "/srv/launch",
                    "place": "/srv/launch/launch.json", "document": {}}
        # `None` IS AN ANSWER HERE: an assignment that authorizes no document
        # has none to expose, and absence is absence rather than a default.
        self.adapter(launch_delivery=None)()
        for spoiled in (composed, "/srv/launch/launch.json", 7):
            with self.subTest(spoiled=type(spoiled).__name__):
                with self.assertRaises(ContractRefusal):
                    self.adapter(launch_delivery=spoiled)()
        self.assertIsNot(type(composed), launch.LaunchDelivery)
        self.assertIsNotNone(oci.run_vector)

    def test_discarding_a_root_this_module_did_not_make_is_absence(self):
        """W26291. `discard` answers whether the root is gone.

        It removes by name inside a directory this module created and never
        walks anything else could have replaced, so a path that was never a
        launch root is ABSENCE rather than a refusal -- there is nothing here
        a caller decides and nothing to own.
        """
        from baton_v12.worker_manager import launch

        self.assertTrue(launch.discard("/srv/no-such-launch-root"))

    def test_a_teardown_acts_on_a_delivery_this_manager_materialized(self):
        """What proves a delivery is that it IS one.

        Everything inside it was owned when it was constructed, so the rule at
        these two doors is identity of kind rather than a re-walk of members a
        constructor already proved.
        """
        credentials = self.credentials()
        home = credentials.CredentialHome("/srv/a-1")
        composed = {"attempt_id": "attempt-1", "root": "/srv/a-1",
                    "slots": [], "state": "live", "bearers": {}}
        for spoiled in (composed, "a delivery", None, 7):
            with self.subTest(spoiled=type(spoiled).__name__):
                with self.assertRaises(ContractRefusal):
                    home.tear_down(spoiled)
        # `None` IS AN ANSWER AT THE ADAPTER and not at teardown, because an
        # assignment that authorizes no slot has no delivery to expose -- and
        # one that reached teardown with nothing to tear down would be an
        # ending nobody asked for.
        for spoiled in (composed, "a delivery", 7):
            with self.subTest(spoiled=type(spoiled).__name__):
                with self.assertRaises(ContractRefusal):
                    self.adapter(credential_delivery=spoiled)()

    def test_one_delivery_belongs_to_one_attempt(self):
        """A mounted credential root is keyed by attempt, and so is the runtime
        that mounts it. Labelling the container with a different attempt would
        make reconciliation and restart look for that delivery under an
        identity it was never recorded against.

        The label document is owned before this comparison happens; what this
        witnesses is the RELATIONSHIP, which no document owner can see.
        """
        import tempfile
        from baton_v12.worker_manager import credentials
        home = credentials.CredentialHome(self.root)
        delivered = home.materialize(
            credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": "vault",
                                          "reference": "kv/one"}}),
            attempt_id="attempt-1",
            workspace_group=self.configured_group(),
            credential_provider=lambda one, two: "z" * 40)
        # W26291 re-review [P1]: a start REQUIRES a materialized launch
        # document, so this witness carries one — otherwise it would refuse
        # for the missing document and prove nothing about the attempt
        # relationship it exists for.
        from baton_v12.worker_manager import launch
        launch_home = tempfile.mkdtemp(prefix="w26291-witness-launch-")
        delivery = launch.materialize(
            launch_home, attempt_id="attempt-1", session="session-1",
            contract="do the thing", role="implementer")
        try:
            built = self.adapter(credential_delivery=delivered,
                                 launch_delivery=delivery)()
            labels = dict(self.OCI_LABELS, runtime_attempt_id="attempt-2")
            with self.assertRaises(ContractRefusal) as caught:
                built.start({"labels": labels, "operation_id": "op-1"})
            self.assertIn("attempt-2", caught.exception.message)
            self.assertIn("attempt-1", caught.exception.message)
        finally:
            home.tear_down(delivered)
            launch.discard(delivery.root)
            if os.path.lexists(launch_home):
                os.rmdir(launch_home)

    def test_a_credential_mount_is_an_entry_of_the_fixed_root(self):
        """A SEPARATE OWNER FROM `_mounts`, and the separation is the point.

        `_mounts` admits a source because this manager created the assignment
        root it lives under; a credential is not assignment material and must
        not become a third mountable root. So the rule here is the fixed
        container root instead, applied to every pair.
        """
        source = "/srv/a-1/credentials/attempt-1/api"
        for spoiled in ("not a sequence of pairs",
                        [(source,)],
                        [(source, "/etc/api")],
                        [(source, "/run/baton/credentials/sub/api")],
                        [(source, "/run/baton/credentials/other")],
                        [(source, "/run/baton/credentials/api"),
                         (source, "/run/baton/credentials/api")]):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    self.running_vector(credentials_delivered=spoiled)()

    def test_a_mount_sequence_is_iterated_and_never_read(self):
        """The container is walked; every mount inside it is owned. Any
        iterable of owned mounts produces the same argv, because nothing
        indexes, measures or branches on the sequence itself."""
        one = {"source": "/srv/a-1/workspace", "target": "/workspace",
               "writable": True}
        as_list = self.vector(mounts=[dict(one)])
        as_tuple = self.vector(mounts=(dict(one),))
        as_generator = self.vector(mounts=iter([dict(one)]))
        self.assertEqual(as_list, as_tuple)
        self.assertEqual(as_list, as_generator)
        # And an element that is NOT a mount is refused as one, which is what
        # says the ownership is on the member rather than on the container.
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(mounts=["not a mount"])
        self.assertIn("a runtime mount", caught.exception.message)

    def test_a_writable_flag_is_a_yes_or_a_no(self):
        """`type(value) is bool`, so a truthy substitute is refused rather
        than read as yes -- which would silently grant write access."""
        for spoiled in (1, "true", "yes", None, [], 0):
            with self.subTest(writable=spoiled):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(mounts=[{"source": "/srv/a-1/workspace",
                                         "target": "/workspace",
                                         "writable": spoiled}])
                self.assertIn("that is a yes or a no",
                              caught.exception.message)

    def test_a_stop_timeout_is_a_positive_whole_number(self):
        from baton_v12.worker_manager import oci
        self.assertIn("30", oci.stop_vector("docker", runtime_id="r-1"))
        for spoiled in (0, -1, 1.5, True, False, "30", None):
            with self.subTest(seconds=spoiled):
                with self.assertRaises(ContractRefusal) as caught:
                    oci.stop_vector("docker", runtime_id="r-1",
                                    seconds=spoiled)
                self.assertIn("positive whole number",
                              caught.exception.message)

    def test_an_unrecognised_running_member_is_uncertain_and_never_absent(
            self):
        """This read CANNOT refuse, and that is the rule rather than an
        omission: a manager that treated confusion as death would release an
        assignment whose worker is still running."""
        from baton_v12.worker_manager import oci
        import json as _json

        def engine_saying(state):
            record = {"Id": "r-1", "State": state}
            return lambda argv: {"status": 0,
                                 "stdout": _json.dumps([record]),
                                 "stderr": ""}

        for running in (True, False, None, "yes", 1, [], {}):
            with self.subTest(running=running):
                adapter = oci.OciAdapter(
                    "docker", engine_saying({"Running": running}),
                    identity={"image_digest": "sha256:" + "e" * 64,
                              "profile_digest": "sha256:" + "b" * 64,
                              "policy_digest": "sha256:" + "d" * 64,
                              "adapter_digest": "sha256:" + "c" * 64},
                    assignment_roots=dict(self.OCI_ROOTS),
                    posture="execution")
                seen = adapter.observe("r-1")
                if running is True:
                    self.assertEqual(seen["state"], "running")
                elif running is False:
                    # The engine SAID it is not running, which this adapter
                    # reports as quiescence rather than as absence: the
                    # container is still there.
                    self.assertEqual(seen["state"], "quiescent")
                else:
                    self.assertEqual(seen["state"], "uncertain")
                    self.assertNotEqual(seen["state"], "absent")

    def test_an_absent_observation_is_omitted_and_not_nulled(self):
        """An inquiry never observes anything, and the view says so by not
        carrying the member -- `_emit` owns the shape, so absence is a decision
        the contract makes rather than a null this constructor invents."""
        provider = self.interrogating()
        answer = worker_manager.inquire(
            self.store, self.port, _Interrogating(provider),
            attempt_id="attempt-1", posture="execution", session_epoch=1,
            operation_id="inquire-w", deadline_seconds=30,
            question="how is it going?")
        self.assertEqual(answer["kind"], "inquire")
        self.assertNotIn("observation", answer)
        probed = worker_manager.probe(
            self.store, self.port, _Interrogating(provider),
            attempt_id="attempt-1", posture="execution", session_epoch=1,
            operation_id="probe-w", deadline_seconds=30)
        self.assertIn("observation", probed)

    def test_an_answer_is_published_by_the_manager_and_never_the_worker(self):
        """The whole isolation topology exists so that a worker holds no Baton
        capability. This is the boundary where that is true rather than
        asserted: the answer reaches Baton through the manager's own session,
        carrying the interrogation identity the manager minted."""
        provider = self.interrogating()
        worker_manager.inquire(
            self.store, self.port, _Interrogating(provider),
            attempt_id="attempt-1", posture="execution", session_epoch=1,
            operation_id="inquire-p", deadline_seconds=30,
            question="how is it going?")
        worker_manager.record_inquiry_answer(
            self.store, operation_id="inquire-p",
            answer={"body": "halfway through the second gate"})
        self.session.calls.clear()
        published = worker_manager.publish_inquiry_answer(
            self.store, self.port, operation_id="inquire-p")
        self.assertEqual(
            [call for call in self.session.calls
             if call[0] == "publish_answer"],
            [("publish_answer",
              {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
               "operation_id": "inquire-p",
               "body": "halfway through the second gate"})])
        self.assertIsNotNone(published["published_at"])

    # -- W6628's stated owners, exercised through the public operation -------

    def test_a_manifest_is_owned_by_the_contracts_own_composite(self):
        """A DIFFERENT OWNER FROM `boundaries`, and a stronger one: schema
        first, then the digest recomputed over the document's own canonical
        bytes, then §12's semantics.

        Owning the envelope with the boundary layer as well would be the
        blanket revalidation 4bz forbids and would answer a weaker question
        than the one already being answered -- so what has to be true is that
        the composite's own refusal is what a caller gets, for both directions
        of the retention.
        """
        published = OutputCase.published()
        for what, document, run in [
                ("not a document", "not a manifest",
                 lambda value: worker_manager.retain_manifest(
                     self.store, value, "inputManifest")),
                ("a manifest with no declared outputs",
                 dict(published, outputs=[]),
                 lambda value: worker_manager.retain_manifest(
                     self.store, value, "inputManifest")),
                ("a document that does not identify itself",
                 dict(published, manifest_id="edited-after-sealing"),
                 lambda value: worker_manager.retain_manifest(
                     self.store, value, "inputManifest")),
                ("a sealed result that is not one", {"schema": "wrong"},
                 lambda value: worker_manager.record_frozen_result(
                     self.store, attempt_id="attempt-1", sealed=value))]:
            with self.subTest(what=what):
                self.setUp()
                if "sealed" in what:
                    self.output_world()
                with self.assertRaises(ContractRefusal) as caught:
                    run(document)
                self.assertIn("a sealed result" if "sealed" in what
                              else "a retained manifest",
                              caught.exception.message)

    def test_the_input_pair_is_owned_by_the_contracts_own_composite(self):
        """W19784. The same owner as a retained manifest, answering a question
        no single-document validator can: `check_input_pair` proves each
        document against its own definition AND THEN holds the two against
        each other.

        So the cases below split deliberately. The first two are documents
        that are not what they are delivered as, which the composite refuses
        on its own; the last is TWO STRUCTURALLY PERFECT DOCUMENTS that are
        not one delivery -- and that one is the whole reason this owner is the
        composite rather than the boundary layer, because `boundaries` has
        nothing that could see it.
        """
        home = tempfile.mkdtemp(prefix="v12-input-pair-")
        self.addCleanup(shutil.rmtree, home, True)
        given, assignment = self.canonical_input_pair()
        # The manager's own identity operands are supplied and CORRECT in every
        # case below, so what refuses is the composite's document rule rather
        # than the authorization beside it. `test_workspaces` owns the
        # authorization's own cases.
        for what, pair in [
                ("neither document is a document", ("not a manifest", {})),
                ("the assignment side is the input side again",
                 (given, given)),
                ("two documents that are not one delivery",
                 (given, self.canonical_input_pair(
                     policy_digest="sha256:" + "f" * 64)[1]))]:
            with self.subTest(what=what):
                root = os.path.join(home, what.replace(" ", "-"))
                os.makedirs(root)
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.compose_input_root(
                        root, *pair,
                        assignment=dict(
                            assignment["assignment_ref"]),
                        runtime_attempt_id=assignment["runtime_attempt_id"])
                self.assertIn("execution input", caught.exception.message)
                self.assertEqual(os.listdir(root), [],
                                 "a refused pair reached the filesystem")

    def canonical_input_pair(self, **spoiled):
        """The record's own input manifest and an assignment minted for it."""
        corpus = json.loads(CONTRACT_VECTORS.read_text(encoding="utf-8"))
        by_schema = {one["document"].get("schema"): one["document"]
                     for one in corpus["valid"]}
        given = by_schema["baton.worker-manifest/input"]
        assignment = dict(by_schema["baton.worker-manifest/assignment"])
        assignment.update(spoiled)
        assignment.pop("manifest_digest", None)
        assignment["manifest_digest"] = _contracts_digest(assignment)
        return given, assignment

    def test_what_the_adapter_seals_is_owned_where_it_arrives(self):
        """An adapter's account of its own success decides NOTHING here.

        What it returns is a sealed result and is owned as one by
        `record_frozen_result`, which is where it arrives -- so an adapter that
        answers with something that is not a result manifest is refused there,
        and the axis is left where the durable state honestly is rather than
        advanced because a call returned.
        """
        attempt_id = self.output_world()

        class Confident:
            """Reports success and answers with nothing that is a result."""

            def seal(self, operands):
                return {"ok": True, "frozen": True}

        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.request_freeze(
                self.store, self.port, Confident(), attempt_id=attempt_id,
                disposition="completed")
        self.assertIn("a sealed result", caught.exception.message)
        self.assertIsNone(worker_manager.frozen_output_of(self.store,
                                                          attempt_id))

    # -- W6629's stated owners, exercised through the public operation -------

    def test_what_the_adapter_collects_is_owned_where_it_arrives(self):
        """The same rule as the seal above, one boundary later.

        `request_intake` journals its `output.collect` request BEFORE the
        adapter is called, and what comes back is a COLLECTION OBSERVATION
        owned by `record_intake`, which is where it arrives. So an adapter that
        reports success and answers with something that is not a collection is
        refused there -- and custody is not taken, because taking custody is
        what the answer was supposed to establish.
        """
        attempt_id = self.froze()

        class Confident:
            """Reports success and answers with nothing that is a collection."""

            def collect(self, operands):
                return {"ok": True, "collected": True}

        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.request_intake(self.store, self.port, Confident(),
                                          attempt_id=attempt_id)
        self.assertIn("a collection observation", caught.exception.message)
        self.assertIsNone(worker_manager.intake_receipt_of(self.store,
                                                           attempt_id))
        self.assertEqual(self.attempt_row()["output"], "frozen",
                         "the axis moved on an answer nobody could read")

    def test_what_the_retain_adapter_answers_decides_nothing(self):
        """The command is DELIVERED and its reply is discarded.

        W6629 review [P1] required the manager to stop typing `adapter.retain`
        without calling it. It did not make the adapter an authority: what the
        material's disposition IS was decided here, committed to the journal,
        and read back from this manager's own rows. So an adapter that answers
        with nonsense changes nothing, which is what makes there be nothing in
        the reply to own.
        """
        attempt_id = self.intaken()

        class Contradicting:
            def retain(self, command):
                self.command = command
                return {"accepted": False, "disposition": "quarantine"}

        adapter = Contradicting()
        decided = worker_manager.decide_retention(
            self.store, self.port, adapter, attempt_id=attempt_id,
            artifact_ids=["artifact-1"], disposition="retain",
            retention_policy_digest=RETENTION_POLICY)
        assert decided["disposition"] == "retain"
        # The command still crossed, whole.
        assert adapter.command["retention_policy_digest"] == RETENTION_POLICY
        assert adapter.command["artifact_ids"] == ["artifact-1"]
        self.assertEqual(
            [one["disposition"]
             for one in worker_manager.retentions_of(self.store, attempt_id)],
            ["retain"], "the adapter's opinion reached the record")

    def test_a_declaration_is_owned_once_at_construction(self):
        """W6634. `sealing.py` is a pure function over data whose caller is the
        adapter in the same package, so its operands are proved ONCE -- where
        they enter that adapter -- and used afterwards.

        This drives the one place that proving happens for the declarations. A
        declaration the adapter cannot read refuses at CONSTRUCTION, before any
        freeze, because by freeze time a worker has already done the work
        against limits nobody could state.
        """
        from baton_v12.worker_manager import sealing
        whole = {"name": "proposal", "type": "directory-result", "path": "out",
                 "required": True,
                 "constraints": {"max_bytes": 1024, "max_entries": 8,
                                 "allowed_media_types": ["text/plain"],
                                 "link_policy": "forbid",
                                 "validator_digest": None}}
        self.assertEqual(sorted(sealing.declared_outputs([whole])),
                         ["proposal"])
        for spoiled in ("not a list", [], [{"name": "x"}],
                        [dict(whole, required="yes")],
                        [dict(whole, constraints=dict(whole["constraints"],
                                                      max_entries="lots"))],
                        [whole, whole]):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    sealing.declared_outputs(spoiled)

    def test_a_retention_names_artifacts_and_owns_every_one_of_them(self):
        """A LIST IS NOT A BOUNDARY -- what crosses is the members.

        `boundaries` has no list kind for that reason, so this operand is owned
        in three parts and each part is a different mistake: `contracts.own`
        takes the fresh built-in copy and refuses what is not JSON data, the
        shape is refused here because a decision naming no artifact decides
        nothing, and every member is owned as an identity.

        All three are driven, because an operand owned in parts is owned only
        as well as its weakest part.
        """
        attempt_id = self.intaken()
        for artifact_ids, expect in (
                (("artifact-1",), "not JSON data"),
                ([], "names at least one artifact"),
                ([7], "an artifact id is durable text")):
            with self.subTest(artifact_ids=artifact_ids):
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.decide_retention(
                        self.store, self.port, _Custodian(),
                        attempt_id=attempt_id, artifact_ids=artifact_ids,
                        disposition="retain",
                        retention_policy_digest=RETENTION_POLICY)
                self.assertIn(expect, caught.exception.message)
        self.assertEqual(worker_manager.retentions_of(self.store, attempt_id),
                         (), "a refused decision left one behind")

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

    def test_the_bearer_is_acceptances_capability_and_no_declines(self):
        """W33937: ONE OPERAND, TWO RULES, chosen by the decision it rides.

        An acceptance is about to TAKE authority and proves possession of the
        exact bearer. A decline is authorized by its binding and carries none,
        so a carried value is refused as the schema fault it is -- and the
        absence it requires is a sentinel rather than a value, which is why
        `None` and the empty string are refusals here and not spellings of it.
        """
        for what, operands, pair in [
                ("an acceptance with another secret",
                 {"decision": "accept", "bearer": "bearer-2"},
                 ("refused", "capability")),
                ("an acceptance with no secret at all",
                 {"decision": "accept", "bearer": None},
                 ("refused", "capability")),
                ("an acceptance carrying nothing at all",
                 {"decision": "accept"}, ("refused", "capability")),
                ("a decline carrying this offer's own bearer",
                 {"decision": "decline", "bearer": "bearer-1"},
                 ("integrity", "schema")),
                ("a decline carrying the empty string",
                 {"decision": "decline", "bearer": ""},
                 ("integrity", "schema")),
                ("a decline carrying a null claim token",
                 {"decision": "decline", "bearer": None},
                 ("integrity", "schema"))]:
            with self.subTest(what=what):
                self.setUp()
                self.issued("offer-b")
                call = dict(offer_id="offer-b", now=NOW,
                            runtime_attempt_id="attempt-1",
                            work_ref={"authority_uuid": UUID, "work_id": WORK})
                call.update(operands)
                with self.assertRaises(ContractRefusal) as caught:
                    worker_manager.accept_offer(self.store, self.port, **call)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code), pair)
                self.assertEqual(
                    self.store._connection.execute(
                        "SELECT state FROM offers WHERE offer_id = ?",
                        ("offer-b",)).fetchone()["state"],
                    "issued")
        # AND THE ABSENCE IS WHAT A DECLINE IS SPELLED WITH: the same call
        # without the operand settles the offer, so the rule above refuses a
        # carried value rather than the decision.
        self.setUp()
        self.issued("offer-b")
        self.assertEqual(
            worker_manager.accept_offer(
                self.store, self.port, offer_id="offer-b", decision="decline",
                now=NOW, runtime_attempt_id="attempt-1",
                work_ref={"authority_uuid": UUID, "work_id": WORK})["state"],
            "declined")

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
                now=NOW, runtime_attempt_id="attempt-1",
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
        # W16823: a late-recorded commit is the same closed result, and the
        # member this case spoils is the fence inside it.
        self.session.settle_answer = {
            "kind": "committed",
            "result": dict(self.session.claim_answer,
                           assignment={"work_ref": {"authority_uuid": UUID,
                                                    "work_id": "0000000a-W9"},
                                       "participant": WHO, "generation": 1})}
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
        self.session.claim_answer = dict(
            self.session.claim_answer,
            assignment={"work_ref": {"authority_uuid": elsewhere,
                                     "work_id": WORK},
                        "participant": WHO, "generation": 1})
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
            "result": dict(self.session.claim_answer,
                           assignment={"work_ref": {"authority_uuid": elsewhere,
                                                    "work_id": WORK},
                                       "participant": WHO, "generation": 1})}
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
            adapter_digest="sha256:" + "a" * 64, profile_digest=PROFILE,
            policy_digest="sha256:" + "d" * 64)
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

    # -- W39666: the worker-entry transport's composite operands -------------

    WORKER_ENTRY_RUNTIME = "8fce41c0d2b4"
    WORKER_ENTRY_SESSION = "session-w39666"
    WORKER_ENTRY_PROGRAM = ["python3", "/opt/baton/baton_worker.py"]

    def conversing(self, **spoiled):
        """One conversation whose channel RECORDS whether it was ever opened.

        Every rule below is owned before anything is sent, so the recorder is
        half the witness: a refusal that happened after the channel opened
        would be a different rule than the one being claimed.
        """
        from baton_v12.worker_manager import worker_entry

        self.opened = []

        def open_channel(argv, *, seconds):
            self.opened.append(argv)
            raise AssertionError("the channel was opened anyway")

        operands = dict(engine="docker",
                        runtime_id=self.WORKER_ENTRY_RUNTIME,
                        program=list(self.WORKER_ENTRY_PROGRAM),
                        session=self.WORKER_ENTRY_SESSION,
                        operations=["describe"], operation_ids=["op-1"],
                        seconds=30)
        operands.update(spoiled)
        return lambda: worker_entry.converse(open_channel, **operands)

    def test_an_exec_program_is_a_sequence_of_words_and_not_a_string(self):
        """`exec_vector` owns the whole operand, not one word of it.

        The string case is the one this rule exists for: `list("python3")` is
        seven one-character words, so iterating would compose
        `docker exec ... p y t h o n 3` -- a closed vector rather than a
        refusal.
        """
        from baton_v12.worker_manager import oci

        def ran(program):
            return lambda: oci.exec_vector(
                "docker", runtime_id=self.WORKER_ENTRY_RUNTIME,
                program=program)

        for wrong in ("python3", None, 7, {"python3": 1}):
            with self.subTest(program=wrong):
                self.refusing("list or tuple of words", ran(wrong))
        self.refusing("names the program", ran([]))
        self.refusing("at most", ran(["x"] * (oci.MAX_PROGRAM_WORDS + 1)))
        # AND THE MEMBERS, which is the half a shape check does not cover.
        self.refusing("an exec program word", ran(["python3", SURROGATE]))
        self.assertEqual(
            oci.exec_vector("docker", runtime_id=self.WORKER_ENTRY_RUNTIME,
                            program=("python3", "-c", "pass")),
            ["docker", "exec", "--interactive", self.WORKER_ENTRY_RUNTIME,
             "python3", "-c", "pass"])

    def test_a_conversations_program_is_held_to_the_exec_program_rule(self):
        """The forward reaches that owner, from the public operation.

        Stated rather than delegated because the rule at `exec_vector` is not
        a layer label either -- so this witness drives `converse` itself and
        requires the refusal that owner writes.
        """
        self.refusing("list or tuple of words",
                      self.conversing(program="python3"))
        self.refusing("an exec program word",
                      self.conversing(program=["python3", SURROGATE]))
        self.assertEqual(self.opened, [])

    def test_a_conversation_asks_for_a_sequence_of_known_operations(self):
        """Shape, emptiness and the closed vocabulary -- all three, one owner.

        W39666 measured the first of them escaping: `list(operations)` let
        `None` and `7` leave as a raw `TypeError`, which is not a refusal this
        manager can be said to have made.
        """
        for wrong in (None, 7, True, "describe", {"describe": 1}):
            with self.subTest(operations=wrong):
                self.refusing("operations is a list or tuple",
                              self.conversing(operations=wrong))
        self.refusing("at least one operation",
                      self.conversing(operations=[], operation_ids=[]))
        self.refusing("is not an operation this channel speaks",
                      self.conversing(operations=["negotiate"]))
        self.assertEqual(self.opened, [])

    def test_operation_identities_are_a_sequence_one_per_operation(self):
        """Shape, cardinality, each identity, its ceiling, and distinctness."""
        from baton_v12.worker_manager.worker_entry import MAX_IDENTITY

        for wrong in (None, 7, True, "op-1", {"op-1": 1}):
            with self.subTest(operation_ids=wrong):
                self.refusing("operation_ids is a list or tuple",
                              self.conversing(operation_ids=wrong))
        self.refusing("one operation identity per operation",
                      self.conversing(operations=["describe", "work"],
                                      operation_ids=["op-1"]))
        self.refusing("a worker-entry operation identity",
                      self.conversing(operation_ids=[SURROGATE]))
        self.refusing("at most",
                      self.conversing(
                          operation_ids=["o" * (MAX_IDENTITY + 1)]))
        self.refusing("consumed once per worker session",
                      self.conversing(operations=["describe", "work"],
                                      operation_ids=["op-1", "op-1"]))
        self.assertEqual(self.opened, [])

    def test_a_worker_entry_bound_is_a_positive_whole_number(self):
        """Owned at the port, where the bound is handed to the world.

        `bool` is excluded for the reason `stop_vector`'s is: `True` is an
        `int` and a one-second worker session is not what a caller passing it
        meant.
        """
        for wrong in (0, -1, True, 1.5, "30", None):
            with self.subTest(seconds=wrong):
                self.refusing("whole number of seconds",
                              self.conversing(seconds=wrong))
        self.assertEqual(self.opened, [])

    def test_a_reader_only_ever_receives_a_channel_the_port_proved(self):
        """The stated rule is that nothing unproved reaches `_Reader`.

        So the witness drives a channel the port must reject and requires that
        the reader never saw it: `receive` is what a `_Reader` calls first, and
        a channel that records being read would mean the refusal came later
        than claimed.
        """
        from baton_v12.worker_manager import worker_entry

        read = []

        class Partial:
            def send(self, payload):
                return len(payload)

            def receive(self, count):
                read.append(count)
                return b""

        self.assertNotIn("_Reader", worker_entry.__all__)
        self.refusing(
            "is not the framed session",
            lambda: worker_entry.converse(
                lambda argv, *, seconds: Partial(),
                engine="docker", runtime_id=self.WORKER_ENTRY_RUNTIME,
                program=list(self.WORKER_ENTRY_PROGRAM),
                session=self.WORKER_ENTRY_SESSION, operations=["describe"],
                operation_ids=["op-1"], seconds=30))
        self.assertEqual(read, [], "the reader was handed an unproved channel")


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
        # THE CANONICAL DICTIONARY, WHEREVER THE AUTHORITY KEEPS IT.
        #
        # W29400 review [P1]: this parsed `project_work` for a literal return,
        # and that Work's snapshot correction made `project_work` a wrapper
        # that opens one read transaction and delegates to `_projected`, where
        # the dictionary now lives. The extractor did not move with it, so this
        # gate failed before it could compare anything -- a compatibility check
        # that cannot FIND the thing it compares is not passing or failing, it
        # is silent.
        #
        # Both names are searched rather than one, because which of them holds
        # the literal is the authority's business and not this gate's; what
        # this gate is about is the MEMBERS.
        for name in ("_projected", "project_work"):
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    for piece in ast.walk(node):
                        if isinstance(piece, ast.Return) \
                                and isinstance(piece.value, ast.Dict):
                            return sorted(key.value
                                          for key in piece.value.keys)
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
                                   "authority_uuid": UUID,
                                   # W16823: two more members this manager now
                                   # READS, so a null is not a whole
                                   # projection any more than a missing one is.
                                   "scope": SCOPE, "route": ROUTE})
        self.assertEqual(self.issued("offer-full"), "offer-full")


class AnIdentityIsMoreThanAShape(BoundaryCase):
    """The properties exact POD does not establish.

    Review [P1]: exact POD and an exact member set are the SAFE REPRESENTATION
    of a document, not its field contract. Every case here is a well-formed
    document whose members mean something the manager cannot record.
    """

    def claiming(self, offer_id, **answer):
        self.accepted(offer_id)
        self.session.claim_answer = dict(
            self.session.claim_answer,
            assignment=dict(self.session.claim_answer["assignment"],
                            **answer))
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
        #
        # W16823 moved which layer that is, and nothing else about this case.
        # The claim answer is now the CLOSED RESULT, so the outermost exact-POD
        # owner is the result rather than the identity nested inside it -- and
        # the range is still owned exactly once, by whichever document is
        # outermost. That is the property; the label names where it lives.
        self.refusing("the claim answer's result",
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


# The label a substituted probe proves it arrived at, for the driver regressions
# below. It is this file's own string rather than a real boundary's, because
# what those tests exercise is the LOOP, not the package.
PROBE_LABEL = "a witnessed boundary"


class TheWorkerEntryTransportIsFullyInventoried(BoundaryCase):
    """W39666's own completeness check, over W39666's own slice.

    THE AGGREGATE CANNOT ANSWER THIS QUESTION YET.
    `EveryReceivingEntryHasOneOwner` and `EveryProbeProvesItArrived` are
    red on debt that belongs to W48697's
    parked OCI rescan and to W54802's missing probes, so a slice finished today
    would be invisible inside their failures -- and "it is still red, but less
    so" is not something a reviewer can check.

    So the slice states itself. Every `worker_entry.py` receiving entry, plus
    the exactly two OCI entries W39356 retained as this Work's debt, and
    nothing else. This does NOT weaken or replace the aggregate assertions: it
    is a narrower claim that can be true before they are.
    """

    # THE TWO OCI ENTRIES THIS WORK OWNS, WRITTEN OUT. W39356 recorded its
    # transport additions as `oci.py:_network` and `oci.py:exec_vector`; the
    # first is private and is not a receiving site, so its real crossing is the
    # public operand that forwards to it. Naming both here is what keeps the
    # scope split with W48697 visible: `exec_vector.engine`,
    # `run_vector.interactive` and the adapter's forwarded operands are that
    # Work's and are deliberately absent.
    OCI_ENTRIES = (("caller", "oci.py:run_vector", "network"),
                   ("caller", "oci.py:exec_vector", "program"))

    def slice_entries(self):
        entries = receiving_entries()
        found = {entry for entry in entries
                 if entry[1].startswith("worker_entry.py:")}
        for entry in self.OCI_ENTRIES:
            self.assertIn(entry, entries,
                          "a recorded W39666 entry left the inventory")
            found.add(entry)
        return sorted(found)

    def test_the_slice_is_the_sites_this_work_was_given(self):
        """A completeness claim over a set that quietly shrank is worthless."""
        sites = sorted({entry[1] for entry in self.slice_entries()})
        self.assertEqual(sites, ["oci.py:exec_vector", "oci.py:run_vector",
                                 "worker_entry.py:ChannelPort.__init__",
                                 "worker_entry.py:_Reader.__init__",
                                 "worker_entry.py:converse"])
        self.assertGreaterEqual(len(self.slice_entries()), 12)

    def test_every_entry_in_the_slice_has_an_owning_validator(self):
        owners = EveryReceivingEntryHasOneOwner(
            "test_every_receiving_entry_has_an_owning_validator")
        unowned = [entry for entry in self.slice_entries()
                   if owners.owner_of(entry)[0] is None]
        self.assertEqual(unowned, [], "W39666 entries with no owner")

    def test_every_stated_owner_in_the_slice_has_a_witness(self):
        owners = EveryReceivingEntryHasOneOwner(
            "test_every_receiving_entry_has_an_owning_validator")
        for entry in self.slice_entries():
            if owners.owner_of(entry)[0] != "stated":
                continue
            with self.subTest(entry=entry):
                name = WITNESSES.get(entry)
                self.assertIsNotNone(name, "a stated owner with no witness")
                self.assertTrue(callable(getattr(StatedRules, name, None)),
                                f"{name} is not a method")

    def test_every_probed_owner_in_the_slice_has_exactly_one_probe(self):
        """Layer and delegated owners only: a stated rule is witnessed above.

        The probe catalog is fixture-bound, so this borrows the driver's own
        fixture and releases it rather than carrying one across.

        BOTH DIRECTIONS, RESTRICTED TO THIS SLICE. Review
        2026-08-31T17:55:24Z [P2]: this asserted only `wanted - declared`, so
        an extra or stale probe for one of this Work's entries — including one
        registered under the WRONG LABEL — passed. The global catalog check is
        exact in both directions and would catch it, but it is deliberately red
        on W48697's and W54802's parked debt, so it cannot be this Work's
        independent acceptance signal. The declared set is therefore narrowed to
        this slice's entries and compared for equality: a probe this slice does
        not own is as much a defect as one it owns and lacks.
        """
        driver = EveryProbeProvesItArrived(
            "test_every_declared_probe_reaches_its_named_boundary")
        driver.setUp()
        try:
            catalog = set(driver.all_probes())
        finally:
            driver.doCleanups()
        entries = set(self.slice_entries())
        declared = {pair for pair in catalog if pair[0] in entries}
        wanted = set()
        for entry in sorted(entries):
            if entry in NO_PROBE:
                continue
            for label in layer_labels(entry):
                wanted.add((entry, label))
            if entry in DELEGATED:
                for label in delegated_labels(entry):
                    wanted.add((entry, label))
        self.assertGreaterEqual(len(wanted), 6)
        self.assertEqual(sorted(wanted - declared), [],
                         "owned in this slice, never probed")
        self.assertEqual(sorted(declared - wanted), [],
                         "probed in this slice, never owned under that label")

    def test_no_entry_in_the_slice_is_exempted_from_probing(self):
        """`NO_PROBE` is how an entry could be retired by declaring it, and
        nothing in this slice needs it: every crossing here is reachable from a
        public operation with one operand spoiled."""
        for entry in self.slice_entries():
            with self.subTest(entry=entry):
                self.assertNotIn(entry, NO_PROBE)


class TheDiscoveryProjectionsAreBoundedAndImmutable(unittest.TestCase):
    """W54182: the inventory's discovery is pure, so it is computed once.

    Before this, `_sources` was a generator and the projections below rebuilt it
    on every call: one `all_probes()` walked the package nine times and parsed
    189 files, and the probe driver asked for a catalog once per probe. The
    repetition was invisible because every rebuild agreed with the last one --
    which is why the check is on the WORK, not on the answer.
    """

    def counting(self):
        """`ast.parse`, replaced by one that records the file it was given."""
        parsed = []
        parse = ast.parse

        def counted(text, *rest, **named):
            parsed.append(rest[0] if rest else None)
            return parse(text, *rest, **named)

        self.addCleanup(setattr, ast, "parse", parse)
        ast.parse = counted
        return parsed

    def test_the_package_is_parsed_once_however_many_projections_ask(self):
        modules = [source for source in sorted(PACKAGE.rglob("*.py"))
                   if source.name not in (LAYER, "__init__.py")]
        self.assertGreater(len(modules), 15)
        for projection in MEMOISED:
            projection.cache_clear()
        # THE SAME SOURCE OF TRUTH THE INVARIANT CASE USES, and for the same
        # reason. Review 2026-08-31T17:47:05Z [P2]: this drove a hand-written
        # list of five, so the next projection added to `MEMOISED` would not
        # run under the parse counter unless somebody also remembered a SECOND
        # list -- which is exactly the maintenance failure the shared-tree
        # correction had just removed from its neighbour.
        derived = tuple(projection for projection in MEMOISED
                        if projection is not _sources)
        self.assertGreater(len(derived), 5)
        parsed = self.counting()
        for _ in range(2):
            for projection in derived:
                projection()
        self.assertEqual(sorted(parsed), sorted(str(found) for found in modules),
                         "the package is walked and parsed more than once")

    def test_a_projection_answers_with_the_same_object_every_time(self):
        for projection in MEMOISED:
            with self.subTest(projection=projection.__name__):
                self.assertIs(projection(), projection())

    def test_no_caller_can_poison_a_cached_derived_projection(self):
        """A shared projection is only safe if nobody can edit it.

        Every consumer takes a set difference, a membership test or a sorted
        list; none of them may reach the one cached answer the next assertion
        will be given.

        THE DERIVED PROJECTIONS ONLY, and the name says so now. Review
        2026-08-31T16:16:32Z [P2]: this case used to open with
        `assertIsInstance(_sources(), tuple)` under a name that promised no
        caller could poison ANY cached projection, and a tuple of mutable
        `ast.Module` objects is exactly the projection a caller can poison. The
        source snapshot's narrower invariant is measured by
        `test_the_shared_trees_are_never_mutated_by_a_projection`; what belongs
        here are the projections whose members really are immutable values.
        """
        for projection in (receiving_entries, columns_read, propagated_owners):
            with self.subTest(projection=projection.__name__):
                self.assertIsInstance(projection(), frozenset)
        for projection in (_crossings, owning_validators, _helper_returns):
            with self.subTest(projection=projection.__name__):
                self.assertIsInstance(projection(), types.MappingProxyType)
                with self.assertRaises(TypeError):
                    projection()["nowhere.py:invented"] = "invented"
        for site, found in owning_validators().items():
            with self.subTest(site=site):
                self.assertIsInstance(found, frozenset)
        entries = receiving_entries()
        self.assertGreater(len(entries), 50)
        taken = set(entries)
        taken.clear()
        self.assertEqual(len(receiving_entries()), len(entries))

    def fingerprints(self):
        """A structural reading of every cached tree, as text.

        `ast.dump` renders the node graph rather than the object identity, so a
        body that lost a statement, a call whose function was rebound and an
        attribute assigned in place all change this and nothing else does.
        """
        return {str(source): ast.dump(tree) for source, tree in _sources()}

    def test_the_shared_trees_are_never_mutated_by_a_projection(self):
        """The narrower invariant the source snapshot actually has.

        The tuple is immutable; the `ast.Module` objects inside it are not, so
        the snapshot is shared safely only because every projection here READS.
        That is a rule about this file's code, and the way to keep a rule true
        is to measure it rather than to comment it.

        EVERY DERIVED MEMBER, DERIVED FROM `MEMOISED` RATHER THAN LISTED.
        Review 2026-08-31T17:23:04Z [P2]: this cleared and reran five
        projections by name and omitted `_helper_returns`, which walks the
        shared trees too. Measured, its miss count did not move across the two
        fingerprints -- so a mutation written into that walker would have
        happened while the earlier boundedness cases warmed it, before the
        `before` reading, and this case could not have seen it. A hand-written
        list is the same failure the `MEMOISED` tuple exists to prevent, so the
        set is taken from there and a projection added later is covered without
        anybody remembering to add it here.

        `_sources` IS DELIBERATELY NOT CLEARED. Reparsing would hand the second
        fingerprint a different node graph, and the question is whether a
        projection edited THIS one.
        """
        before = self.fingerprints()
        self.assertGreater(len(before), 15)
        derived = tuple(projection for projection in MEMOISED
                        if projection is not _sources)
        self.assertGreater(len(derived), 5)
        for projection in derived:
            projection.cache_clear()
        for projection in derived:
            projection()
        self.assertEqual(self.fingerprints(), before,
                         "a projection edited the tree it was given")

    def test_the_mutation_check_can_actually_notice(self):
        """The guard above is only evidence if it can fail.

        Review 2026-08-31T16:16:32Z [P2] reproduced the real hazard by clearing
        one module's `tree.body` and recomputing a projection, which loses
        crossings the previous caller saw. So this stages that mutation,
        requires the fingerprint to notice it, and puts the statement back --
        no projection runs while the tree is short, and the fingerprint is
        required to return to what it was.
        """
        chosen = next(tree for source, tree in _sources()
                      if source.name == "oci.py")
        before = self.fingerprints()
        removed = chosen.body.pop()
        try:
            self.assertNotEqual(self.fingerprints(), before,
                                "the fingerprint cannot see a lost statement")
        finally:
            chosen.body.append(removed)
        self.assertEqual(self.fingerprints(), before,
                         "the staged mutation was not put back")

    def test_a_probe_catalog_costs_no_further_discovery(self):
        """The driver builds one catalog per probe, and that has to be cheap.

        The catalog is fixture-bound and cannot be shared; what made rebuilding
        it cost 1.1 seconds was the discovery underneath, and that is shared.
        """
        case = EveryProbeProvesItArrived(
            "test_every_declared_probe_reaches_its_named_boundary")
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.all_probes()
        parsed = self.counting()
        first = set(case.all_probes())
        second = set(case.all_probes())
        self.assertEqual(parsed, [])
        self.assertEqual(first, second)
        self.assertGreater(len(first), 400)


class TheProbeDriverIsBounded(unittest.TestCase):
    """W54182: the probe driver's fixture lifetime, as a check.

    The driver used to call `setUp` once per probe against ONE cleanup stack, so
    549 probes registered 1,098 pending cleanups, overwrote `self.store` under
    each of them and grew the process file-descriptor table for the whole run.
    Every test here runs the SHIPPED driver method; the only substitution is the
    catalog it iterates, so the loop, the per-probe setup and the teardown under
    test are the real ones.

    Checking the eventual framework teardown would not do: that teardown is what
    the leaking shape relied on, and it passed throughout.
    """

    def driving(self, *probes, opening=None):
        """Run the real driver over a catalog of `probes`.

        Each probe is called with the live case and every fixture `setUp` has
        produced so far, in creation order and INCLUDING the one `unittest`
        itself opened before the test method began. `opening` is called with
        each fixture's index as it is created, so a setup failure can be staged.
        """
        case = EveryProbeProvesItArrived(
            "test_every_declared_probe_reaches_its_named_boundary")
        fixtures = []
        builds = []
        opened = case.setUp

        def recording():
            opened()
            fixtures.append((case.root, case.store))
            if opening is not None:
                opening(len(fixtures) - 1)

        def catalog():
            builds.append(case.store)
            return {(("caller", f"probe.py:probe_{index:03d}", "operand"),
                     PROBE_LABEL): (PROBE_LABEL,
                                    lambda run=run: run(case, fixtures))
                    for index, run in enumerate(probes)}

        case.setUp = recording
        case.all_probes = catalog
        result = unittest.TestResult()
        case.run(result)
        return case, result, fixtures, builds

    def refuse(self):
        """What an arriving probe does: refuse at the label it was named for."""
        raise ContractRefusal("integrity", "schema", PROBE_LABEL)

    def closed(self, store):
        """Whether this store's connection is gone, asked through its own API."""
        try:
            store.operation_record("op-absent")
        except sqlite3.ProgrammingError:
            return True
        return False

    def test_each_probe_runs_in_its_own_reclaimed_fixture(self):
        seen = []

        def probe(case, fixtures):
            seen.append([(os.path.isdir(root), self.closed(store))
                         for root, store in fixtures])
            self.refuse()

        case, result, fixtures, _ = self.driving(probe, probe, probe)
        self.assertEqual((result.failures, result.errors), ([], []))
        # The framework's own fixture, then exactly one more per probe.
        self.assertEqual(len(fixtures), 4)
        self.assertEqual(len({root for root, _ in fixtures}), 4)
        self.assertEqual(len({id(store) for _, store in fixtures}), 4)
        for index, earlier in enumerate(seen):
            with self.subTest(probe=index):
                self.assertEqual(len(earlier), index + 2)
                # This probe's own fixture is live and open ...
                self.assertEqual(earlier[-1], (True, False))
                # ... and every fixture before it, the framework's included, is
                # already removed and closed rather than waiting for the end.
                self.assertEqual(earlier[:-1], [(False, True)] * (index + 1))
        self.assertEqual(case._cleanups, [])

    def test_a_failing_probe_releases_its_fixture_before_the_next(self):
        """The `finally` is the point: a probe that fails is a probe that ran.

        The failure this stages is the vacuity one -- an operation that returns
        instead of refusing -- because that is the failure the real inventory
        reports, and it must not also leak a store.
        """
        seen = []

        def accepting(case, fixtures):
            seen.append(len(fixtures))

        def following(case, fixtures):
            seen.append([(os.path.isdir(root), self.closed(store))
                         for root, store in fixtures[:-1]])
            self.refuse()

        case, result, fixtures, _ = self.driving(accepting, following)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.failures), 1)
        self.assertIn("accepted", str(result.failures[0][1]))
        self.assertEqual(seen[1], [(False, True), (False, True)])
        self.assertEqual(len(fixtures), 3)
        self.assertEqual(case._cleanups, [])

    def test_a_fixture_that_fails_to_open_is_still_reclaimed(self):
        """Setup is inside the `try`, so a half-built fixture is not stranded."""
        def breaking(index):
            if index == 2:
                raise RuntimeError("the fixture did not open")

        case, result, fixtures, _ = self.driving(
            lambda case, fixtures: self.refuse(),
            lambda case, fixtures: self.refuse(),
            opening=breaking)
        self.assertEqual(result.failures, [])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("the fixture did not open", str(result.errors[0][1]))
        self.assertEqual(len(fixtures), 3)
        for root, store in fixtures:
            with self.subTest(root=root):
                self.assertFalse(os.path.isdir(root))
                self.assertTrue(self.closed(store))
        self.assertEqual(case._cleanups, [])

    def test_nothing_accumulates_with_the_probe_count(self):
        """The measured defect, stated as an invariant.

        Twenty setups took the process from four file descriptors to sixty-four
        and left forty pending cleanups. What has to be true is that neither the
        cleanup stack nor the number of live fixtures depends on how many probes
        have already run.
        """
        depths = []
        live = []

        def probe(case, fixtures):
            depths.append(len(case._cleanups))
            live.append(sum(1 for root, _ in fixtures if os.path.isdir(root)))
            self.refuse()

        for count in (2, 12):
            depths.clear()
            live.clear()
            case, result, fixtures, _ = self.driving(*[probe] * count)
            with self.subTest(probes=count):
                self.assertEqual((result.failures, result.errors), ([], []))
                self.assertEqual(len(fixtures), count + 1)
                # One temporary directory and one SQLite connection at a time,
                # whatever the probe count.
                self.assertEqual(live, [1] * count)
                self.assertEqual(depths, [2] * count)
                self.assertEqual(case._cleanups, [])

    def test_every_probes_catalog_is_built_against_its_own_fixture(self):
        """The catalog cannot be hoisted: its closures capture this fixture.

        One current catalog captured eighty stores, twenty-four credential homes
        and forty ports directly, so a catalog carried across fixtures would
        hand a later probe an already-closed store. The keys are taken once; the
        values are rebuilt where they are used.
        """
        case, result, fixtures, builds = self.driving(
            lambda case, fixtures: self.refuse(),
            lambda case, fixtures: self.refuse())
        self.assertEqual((result.failures, result.errors), ([], []))
        # Once for the key universe, then once inside each probe's fixture.
        self.assertEqual(len(builds), 3)
        self.assertEqual([id(store) for store in builds],
                         [id(store) for _, store in fixtures])


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
