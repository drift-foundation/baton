"""W2845 cut 1 — what this package IS and, more usefully, what it is not.

The trust claim here is deliberately narrow, because the wide version would be
false.  Python reflection is not a sandbox: a determined trusted in-process
module can import `baton_v12.authority.store`, read a private attribute or walk
a closure, and no amount of underscores changes that.

So these cases prove the claim that is actually true and actually load-bearing:
THE SUPPORTED, EXPORTED API HANDS A CONSUMER NEITHER BOOTSTRAP NOR STORE, PATH,
SQL OR SESSION-MINT AUTHORITY.  They inspect the exported and reachable public
surface and the package's declared dependencies.  They do not claim that a
leading underscore is a capability boundary; untrusted workers are isolated by
process and container, which is a mechanism that enforces something.
"""

import ast
import os
import pathlib
import shutil
import sqlite3
import tempfile
import unittest

import baton_v12.authority as authority_package
from baton_v12.authority.schema import SCHEMA_VERSION
from baton_v12.authority import (Authority, GATE_CONTRACT_RUNTIME,
                                 GATE_QUIESCENCE, Refusal, gate_token)

HERE = pathlib.Path(__file__).resolve()
DISTRIBUTION = HERE.parents[2]
PACKAGE = DISTRIBUTION / "src" / "baton_v12"

UUID = "0123456789abcdef0123456789abcdef"


def package_sources():
    return sorted(PACKAGE.rglob("*.py"))


def authority_sources():
    """The AUTHORITY slice only.

    PLAN item 4bi, authorized: the distribution now ships two slices and only
    one of them may reach a dependency. The import allowlist below is the
    authority's own -- standard library and nothing else -- and the Worker
    Manager's exact list lives with the Worker Manager, in
    `tests/manager/test_dependencies.py`.

    The reach scan stays distribution-wide, because "nothing here opens a v11
    store or reads a dossier at runtime" is a property of BOTH slices.
    """
    return sorted((PACKAGE / "authority").rglob("*.py"))


def _runtime_strings(source):
    """Every string literal in `source` that is NOT a docstring.

    A docstring is documentation about the boundary; a literal is a value the
    running code can use.  Only the second kind can be a reach.
    """
    tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in docstrings]


class ExportedSurface(unittest.TestCase):

    def test_the_exported_names_are_the_promise(self):
        # Enumerated rather than asserted loosely, because a surface that grows
        # by accident is exactly how a bootstrap capability escapes.
        self.assertEqual(sorted(authority_package.__all__), [
            "ABSENT", "Authority", "CAPABILITIES", "GATE_CONTRACT_RUNTIME",
            "GATE_PLAN_REVISION", "GATE_QUIESCENCE", "MAX_SAFE_INTEGER",
            "Refusal", "SESSION_READS", "SESSION_TRANSITIONS", "Session",
            "V11", "V12", "assignment_ref", "claim_signature", "gate_token",
            "is_v12_contract", "parse_gate", "same_assignment", "work_ref",
        ])

    def test_no_exported_name_is_a_store_a_path_or_a_way_to_run_sql(self):
        forbidden = ("store", "sqlite", "sql", "connection", "cursor", "path",
                     "schema", "database", "db", "bootstrap")
        for name in authority_package.__all__:
            lowered = name.lower()
            for word in forbidden:
                with self.subTest(name=name, word=word):
                    self.assertNotIn(word, lowered)

    def test_the_bootstrap_face_configures_and_reads_and_never_acts(self):
        # Enumerated exactly, because a surface that grows by accident is how a
        # runtime transition ends up on the object that configures the
        # deployment.  The frozen Node host was corrected for exactly that: one
        # face carried both, and through it a consumer granted itself the close
        # capability, closed the live Work as that actor, and moved the
        # canonical target with zero proposals and zero receipts.
        with tempfile.TemporaryDirectory(prefix="v12-authority-") as root:
            path = os.path.join(root, "authority.sqlite3")
            with Authority.create(path, authority_uuid=UUID) as face:
                public = sorted(name for name in dir(face)
                                if not name.startswith("_"))
                self.assertEqual(public, sorted([
                    # identity
                    "authority_uuid",
                    # bootstrap -- `dispose`, not `close`: `close` is the
                    # Baton verb that TERMINALIZES a Work, and it now lives on
                    # the session.  One name for both invites the wrong one.
                    "create", "dispose", "open", "session",
                    # configuration
                    "add_route_handler", "canonical_target",
                    "capabilities_of", "certify_contract", "create_work",
                    "grant_capability", "holds_capability", "is_certified",
                    "permit_contract_transition",
                    "permits_contract_transition", "policy",
                    "revoke_capability", "set_policy",
                    "withdraw_certification",
                    # W16821: binding an endpoint address to a canonical
                    # principal is CONFIGURATION.  It moves that identity's
                    # claim capacity, its grants and its attribution, so the
                    # face that acts must not carry it -- which is this
                    # enumeration doing the job it was written for.
                    "bind_endpoint",
                    # projections
                    "assert_invariants", "assignment_events", "assignment_of",
                    "fenced_generations", "gate_evidence", "operation_record",
                    "operation_result", "project_work", "slot_holder",
                    "activities", "contract_events", "integration_attempts",
                    "proposal", "receipt", "receipts",
                    # W16821 projections: which principal an address resolves
                    # to, which addresses one principal holds, which Work that
                    # principal is at capacity on, and the configuration
                    # generation a decision would be taken under.
                    "endpoints_of", "policy_generation", "principal_of",
                    "slot_holder_of_principal",
                    # W29400: one Work's live label set, its mutation history,
                    # and the deployment-wide all-of/none-of inventory. Reads
                    # only -- the two label MUTATIONS are session transitions
                    # and are deliberately absent from this face.
                    "labels_of", "work_label_events", "works_with_labels",
                    # W29400: the act that made a Work is a READ on this face,
                    # and reading it acts on nothing.
                    "work_creation",
                    # Review [P0]/[P1]: the decision one authorized act was
                    # taken under, and the scope- and provenance-bearing grant
                    # projection `capabilities_of` deliberately flattens.
                    "decision_of", "grants_of",
                ]))
                self.assertEqual(face.authority_uuid, UUID)
                # And nothing about the STORE: not the path, not the
                # connection, not the schema, and no way to run a statement.
                for forbidden in ("store", "db", "connection", "path",
                                  "execute", "run", "sql", "schema"):
                    self.assertNotIn(forbidden, public, forbidden)

    def test_a_later_cut_adds_methods_rather_than_stubs(self):
        # A stub that raises `NotImplementedError` is a method the exported
        # surface CLAIMS to have.  Cut 1 implements creation, opening and
        # disposal; the runtime transitions belong to reviewed later cuts and
        # are absent rather than promised.
        # `project_work` arrived with cut 2, which is why it is not in this
        # list any more: the list is what the CURRENT cuts do not promise, and
        # it shrinks by implementation rather than by editing the claim.
        # `session` arrived with cut 5, which is why it has left this list.
        # Every RUNTIME transition is still absent from the bootstrap face --
        # that is the whole point of there being two faces, and the list is what
        # this face does not promise.
        for name in ("claim", "end", "cancel", "pass_work", "install_gate",
                     "satisfy_gate", "reject_plan", "settle_operation",
                     "advance_contract", "activity", "publish", "verify",
                     "review", "approve", "integrate", "close",
                     "mint_session"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(Authority, name))


class Isolation(unittest.TestCase):

    def test_the_authority_imports_nothing_but_the_standard_library_and_itself(self):
        # The authority's empty dependency set is a claim; this is the check
        # that makes it a fact.
        #
        # Item 4bi: the lock's runtime set is no longer empty distribution-wide,
        # because the Worker Manager was RULED to pin a real Draft 2020-12
        # validator. That ruling is about the manager. The authority is still
        # standard-library only, and scoping this scan to the authority slice is
        # what keeps that a measured fact rather than a casualty of the manager's
        # dependency.
        allowed = {"json", "os", "re", "sqlite3", "stat", "uuid", "datetime",
                   "pathlib", "typing", "collections", "contextlib", "hashlib",
                   "secrets", "subprocess", "multiprocessing", "threading",
                   "time", "itertools", "functools"}
        for source in authority_sources():
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        with self.subTest(source=source.name, module=alias.name):
                            self.assertIn(root, allowed)
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue
                    root = (node.module or "").split(".")[0]
                    with self.subTest(source=source.name, module=node.module):
                        self.assertIn(root, allowed | {"baton_v12"})

    def test_nothing_reaches_for_v11_the_node_host_or_a_dossier(self):
        # The ways to reach these are not all imports: a subprocess call to a
        # Baton executable and a path into `work/records` are reaches too, and
        # both are STRING LITERALS rather than import statements.
        #
        # SO THE SCAN IS OVER LITERALS, NOT OVER SOURCE TEXT.  My first draft
        # scanned the file text and failed on this package's own docstrings --
        # which say, correctly, that nothing here opens `work.sqlite3` or
        # imports `src/baton_work/`.  Prose that states the boundary is exactly
        # what should be kept; a checker that cannot tell a claim from a reach
        # is a checker that punishes documentation.
        forbidden = ("baton_work", "v12/src/authority", "work.sqlite3",
                     "work/records", "baton-v11", "opt/baton")
        for source in package_sources():
            for literal in _runtime_strings(source):
                for word in forbidden:
                    with self.subTest(source=source.name, word=word):
                        self.assertNotIn(word, literal)

    def test_the_authority_schema_carries_no_manager_or_control_facts(self):
        with tempfile.TemporaryDirectory(prefix="v12-authority-") as root:
            path = os.path.join(root, "authority.sqlite3")
            Authority.create(path, authority_uuid=UUID).dispose()
            connection = sqlite3.connect(path)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            connection.close()
        self.assertEqual(tables - {"sqlite_sequence"}, {
            "meta", "certified_contract", "contract_transition", "policy",
            # W16821 schema 2: the principal separated from the endpoint
            # address, the deployment mapping between them, and the
            # configuration generation every authorization decision names.
            # Authority facts, all three: who acted, which address they acted
            # through, and under which configuration.
            "policy_generation", "principal", "endpoint",
            # ...and the decision each authorized act was taken under, in one
            # table rather than as four nullable columns on whichever row that
            # act happened to write.
            "authorization_decision",
            # W29400: the live Work-label set and its append-only mutation
            # evidence.  Authority facts: user metadata the authority owns,
            # authorizes and journals -- and deliberately NOT the Worker
            # Manager's OCI runtime labels, which are execution identity and
            # stay in its own store.
            "work_creation", "work_label", "work_label_event",
            "work", "route_handler", "capability", "fenced_generation",
            "claim_slot", "operation", "assignment_event", "contract_event",
            "gate_evidence", "activity", "proposal", "receipt",
            "integration_attempt"})
        # An authority that also stored these would be answering questions it
        # is not authoritative for.  They are the Worker Manager control
        # store's, and their absence is the boundary.
        #
        # WHOLE NAMES, NOT SUBSTRINGS.  My first draft of this scanned the
        # schema TEXT for words like "attempt" and "runtime", and it failed on
        # `integration_attempt` -- an authority fact whose name happens to
        # contain a control-store word -- and on prose in the comments that
        # merely mentions a certified runtime profile.  The instrument was
        # wrong, not the schema.  The exact table set above is the real guard;
        # this states the intent behind it in terms that can only be true or
        # false about a table.
        control_store_facts = {
            "offers", "offer", "attempts", "attempt", "runtimes", "runtime",
            "output", "quarantined_output", "intake", "cleanup", "manifests",
            "agent_sessions", "agent_events", "turns", "turn_allocations",
            "posture_slots", "artifacts", "credentials", "tokens",
        }
        self.assertEqual(tables & control_store_facts, set())


class Distribution(unittest.TestCase):

    def read(self, name):
        return (DISTRIBUTION / name).read_text(encoding="utf-8")

    def test_the_distribution_declares_the_python_it_requires(self):
        pyproject = self.read("pyproject.toml")
        self.assertIn('requires-python = ">=3.13"', pyproject)
        # Item 4bi, authorized migration: the distribution's dependency set is
        # no longer empty, because the Worker Manager was RULED to pin a real
        # Draft 2020-12 validator. What this slice still owns is the claim that
        # the AUTHORITY reaches for none of it, and that is measured by the
        # import scan above rather than by a string in this file.
        self.assertIn("test = []", pyproject)

    def test_the_runtime_lock_says_which_slice_its_pins_are_for(self):
        lock = self.read("requirements.lock")
        # Item 4bi, authorized migration: this used to assert the runtime set
        # was EMPTY. It is not any more, and pretending otherwise would be the
        # stale half of a split rather than the honest one -- so what is checked
        # now is that the lock SAYS WHOSE the pins are. A dependency nobody has
        # attributed is a dependency both slices inherit by default.
        self.assertIn("# --- runtime", lock)
        self.assertIn("Worker Manager", lock)
        self.assertIn("standard-library only", lock)

    def test_every_pinned_build_artifact_carries_a_hash(self):
        for line in self.read("requirements.lock").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("--hash"):
                continue
            with self.subTest(line=stripped):
                self.assertIn("==", stripped)
                self.assertTrue(stripped.endswith("\\"),
                                "a pin without a hash continuation is not a pin")

    def test_the_authority_slice_still_reaches_for_no_validator(self):
        # Item 4bi, authorized migration: this used to assert the DISTRIBUTION
        # named no validator, which stopped being true the moment the manager's
        # ruled dependency landed. The property it was protecting is unchanged
        # and is now measured where it lives -- in the authority's own source.
        # A file that does not mention a library and a slice that does not reach
        # for one are different facts, and only the second one matters.
        for source in authority_sources():
            text = source.read_text(encoding="utf-8")
            tree = ast.parse(text, str(source))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for name in names:
                    with self.subTest(source=source.name, module=name):
                        self.assertNotIn(name.split(".")[0],
                                         {"jsonschema", "fastjsonschema",
                                          "referencing", "jschon"})


if __name__ == "__main__":
    unittest.main()


class EveryDiagnosticIsBoundedByTheRule(unittest.TestCase):
    """`errors.py`'s rule, enforced by a case instead of by my diligence.

    Three reviews in a row found the same defect: a refusal interpolating
    caller-controlled text directly, so a one-million-character operand produced
    a one-million-character diagnostic. The first named two Session sites; the
    second reproduced it in Core and ruled the audit package-wide; the third
    found it in the ten exported identity helpers -- AND FOUND THAT THIS CHECK
    WAS WHY. The first version classified by unparsing the expression and
    matching a string prefix, so it called `name_of(value) + value` bounded
    because the text began with `name_of`, accepted any textual `join` without
    proving its iterable, and accepted `what` because of how the variable was
    SPELLED. `what` is package prose at every internal call site and caller text
    at every exported one, so spelling was exactly the wrong thing to trust.

    So this version proves NODE SHAPES and ORIGINS:

      a bounded call        the WHOLE interpolation is one call to a named
                            bounding helper. Not a call inside a larger
                            expression -- a `BinOp` with a bounded operand is
                            not bounded.
      a proven join         `"...".join(X)` where X is a module-level constant
                            bound to a literal, proved by parsing the module
                            rather than by listing names here.
      a proven local        a bare name assigned in the same function from a
                            bounding call -- which is how `what` earns its place
                            now that `label_of` binds it at the boundary. Origin,
                            not spelling.
      a named site          a small table keyed by MODULE, FUNCTION and
                            expression. A new site with the same spelling is not
                            covered by an old entry.
    """

    # The renderings that bound by construction.
    BOUNDING_CALLS = frozenset({
        "name_of",        # the sixty-character rule, for a rejected value
        "type_name_of",   # the same rule, for a rejected value's KIND
        "label_of",       # the label rule, for a caller-supplied label
        "_sample_of",     # a bounded sample of names plus a count
        "len",            # a count is a number
    })

    # Sites whose value this package OWNS, keyed by where they are. Each names
    # the reason. An entry does not travel: the same spelling in another function
    # is a new site and fails until somebody looks at it.
    NAMED_SITES = {
        # (module, function, expression): reason, or (how many lexical sites
        # this entry covers, reason). A COUNT, because an exception that covers
        # "wherever this spelling appears" is what let one entry excuse ten
        # exported helpers. The dotted paths each entry actually covers are
        # pinned by `test_every_named_site_covers_the_paths_it_was_written_for`.
        ("core.py", "_require_capability", "capability"):
            "a capability name, from the configured constant set",
        ("core.py", "body", "kind"):
            (2, "the receipt kind the enclosing writer was called for"),
        ("core.py", "_require_free_receipt_id", "kind"):
            "the same four kinds",
        ("session.py", "_operands", "name"):
            (5, "a transition name, from the session's own table"),
        ("session.py", "_operands", "forbidden"):
            "one of the two identity operand names, written out",
        ("session.py", "_operands", "', '.join(missing)"):
            "the required keys of one table entry, so the whole set is ours",
        ("session.py", "call", "name"):
            "the same table, in the generated read wrapper",
        ("session.py", "call", "', '.join(parameters) or 'no operands'"):
            "that entry's parameter names, likewise ours",
        ("store.py", "_describe_target", "failure.errno"):
            "an OS error number, which is an integer",
        ("store.py", "create", "failure.errno"):
            "the same",
        ("identity.py", "check_opaque_id", "fault"):
            "prose from `opaque_id_fault`, whose value is already bounded -- and "
            "MEASURED: injecting the value into that helper is caught by the "
            "behavioural family suite, not by this walker, which is the argument "
            "for having both",
    }

    LITERAL_BUILDERS = frozenset({"frozenset", "tuple", "set", "dict",
                                  "list", "sorted"})

    # Statements that BIND a name. Anything here that is not a plain assignment
    # from a bounding call makes the name unproven for the whole scope, because
    # this analyzer does not model data flow and must not pretend to.
    BINDING_STATEMENTS = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For,
                          ast.AsyncFor, ast.With, ast.AsyncWith, ast.Import,
                          ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef, ast.NamedExpr, ast.ExceptHandler,
                          ast.comprehension, ast.Global, ast.Nonlocal)

    # Statements a binding may NOT be inside. A name assigned in one arm of an
    # `if` is not proved at a use after the `if`, and this analyzer does not
    # compute dominance -- so it refuses rather than guesses.
    BRANCHING = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With,
                 ast.AsyncWith, ast.IfExp, ast.match_case)

    def package(self):
        return pathlib.Path(authority_package.__file__).parent

    # -- constants, per module and with shadowing ----------------------------

    def is_literal_expression(self, node, owned=frozenset()):
        """True when this expression is built from literals and nothing else.

        `2 ** 53 - 1` is as much a constant as `1` is, so the test is not "is it
        a `Constant`" but "does it reach outside itself". A `Name`, an
        `Attribute`, a `Subscript` or a call to anything but a literal builder
        means it can depend on something a caller supplied.
        """
        for piece in ast.walk(node):
            if isinstance(piece, ast.Call):
                if getattr(piece.func, "id", "") not in self.LITERAL_BUILDERS:
                    return False
            elif isinstance(piece, (ast.Name, ast.Attribute, ast.Subscript,
                                    ast.comprehension, ast.Lambda,
                                    ast.FormattedValue)):
                if isinstance(piece, ast.Name) and (
                        piece.id in self.LITERAL_BUILDERS or piece.id in owned):
                    continue
                return False
        return True

    def module_bindings(self, tree):
        """Every module-level binding of every name, with its node.

        Shadowing is about being bound TWICE, not about what the binding looks
        like -- so this counts first and judges after. A name bound once by a
        literal assignment is a candidate; a name bound twice is nobody's
        constant, because this analyzer cannot say which binding ran last.
        """
        bindings = {}

        def note(name, node):
            bindings.setdefault(name, []).append(node)

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        note(target.id, node)
                    else:
                        for piece in ast.walk(target):
                            if isinstance(piece, ast.Name):
                                note(piece.id, None)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                for piece in ast.walk(node.target):
                    if isinstance(piece, ast.Name):
                        note(piece.id, None)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    note(alias.asname or alias.name, node)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    note((alias.asname or alias.name).split(".")[0], None)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef)):
                note(node.name, None)
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.If,
                                   ast.With, ast.AsyncWith, ast.Try)):
                for piece in ast.walk(node):
                    if isinstance(piece, ast.Name) and \
                            isinstance(piece.ctx, (ast.Store, ast.Del)):
                        note(piece.id, None)
        return bindings

    def module_constants(self, trees):
        """Constants PER MODULE, by fixpoint, honouring imports and shadowing.

        Review [P2]: this was one package-global set of bare names, so a literal
        `LIMIT` in one module proved a caller-supplied parameter named `LIMIT` in
        another. A package-global name set is a package-global spelling, which is
        the thing this analyzer exists not to trust.

        Each module owns what IT binds exactly once to a literal, plus what it
        imports from a module in THIS package that owns it. `GATE_KINDS =
        frozenset({GATE_QUIESCENCE, ...})` is owned once the imported names it
        mentions are -- origin all the way down, module by module.
        """
        bindings = {name: self.module_bindings(tree)
                    for name, tree in trees.items()}
        owned = {name: set() for name in trees}
        while True:
            grew = False
            for name, tree in trees.items():
                for candidate, nodes in bindings[name].items():
                    if candidate in owned[name] or len(nodes) != 1:
                        continue
                    node = nodes[0]
                    if node is None:
                        continue
                    if isinstance(node, ast.Assign):
                        if self.is_literal_expression(node.value, owned[name]):
                            owned[name].add(candidate)
                            grew = True
                    elif isinstance(node, ast.ImportFrom) and node.level == 1:
                        source = f"{node.module}.py" if node.module else None
                        if source not in owned:
                            continue
                        for alias in node.names:
                            if (alias.asname or alias.name) != candidate:
                                continue
                            if alias.name in owned[source]:
                                owned[name].add(candidate)
                                grew = True
            if not grew:
                return owned

    # -- locals, in their own scope and with no unsafe rebinding -------------

    def own_scope(self, function):
        """Every node lexically inside this function but not inside a nested one.

        Review [P2]: `ast.walk(function)` descends into nested functions, so an
        assignment inside a closure proved the ENCLOSING function's parameter of
        the same name. A scope is a scope.
        """
        inside = []

        def descend(node):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue
                inside.append(child)
                descend(child)

        descend(function)
        return inside

    def safe_locals(self, function):
        """Names whose EVERY binding in this scope is a top-level bounding call.

        Review [P2]: a name was called proven if ANY safe assignment existed, so
        a later raw reassignment, or a raw assignment in the other arm of an
        `if`, still read as proved. Reaching definitions would be the real
        answer; a conservative rule is the honest one for a test, so a name is
        proved only when every binding of it in this scope is a plain assignment
        from a bounding call, sitting at the top level of the function where it
        dominates everything after it.

        The answer is the FIRST such line, so a use before it is not proved
        either.
        """
        first = {}
        unsafe = set()
        nodes = self.own_scope(function)
        branching = {id(node) for node in nodes
                     if isinstance(node, self.BRANCHING)}
        inside_branch = set()

        def mark(node):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue
                inside_branch.add(id(child))
                mark(child)

        for node in nodes:
            if id(node) in branching:
                mark(node)

        for node in nodes:
            if not isinstance(node, self.BINDING_STATEMENTS):
                continue
            names = {piece.id for piece in ast.walk(node)
                     if isinstance(piece, ast.Name)
                     and isinstance(piece.ctx, (ast.Store, ast.Del))}
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                names.add(node.name)
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                names.update(node.names)
            safe = (isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in self.BOUNDING_CALLS
                    and id(node) not in inside_branch)
            if safe:
                target = node.targets[0].id
                first[target] = min(first.get(target, node.lineno), node.lineno)
            else:
                unsafe |= names
        return {name: line for name, line in first.items()
                if name not in unsafe}

    # -- the classification --------------------------------------------------

    def bounded_node(self, node, owned, proven, lineno):
        # ONE bounding call, and the whole interpolation.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in self.BOUNDING_CALLS:
            return True
        # A join whose SOURCE is proved.
        if isinstance(node, ast.Call) \
                and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "join" \
                and isinstance(node.func.value, ast.Constant) \
                and type(node.func.value.value) is str \
                and len(node.args) == 1:
            source = node.args[0]
            if isinstance(source, ast.Call) \
                    and getattr(source.func, "id", "") == "sorted" \
                    and len(source.args) == 1:
                source = source.args[0]
            if isinstance(source, ast.Name) and (
                    source.id in owned
                    or (source.id in proven and proven[source.id] < lineno)):
                return True
        # A module constant, or a local this scope proved BEFORE this line.
        if isinstance(node, ast.Name):
            if node.id in owned:
                return True
            if node.id in proven and proven[node.id] < lineno:
                return True
        return False

    def _is_bounded(self, expression):
        """The reviewer's entry point: classify ONE unparsed expression.

        Parsed as source, with no module and no function around it -- so nothing
        is owned and nothing is proven, which is the correct answer for an
        expression nobody can place.
        """
        node = ast.parse(expression, mode="eval").body
        return self.bounded_node(node, owned=frozenset(), proven={},
                                 lineno=0)

    def interpolations(self):
        """Every refusal interpolation, with a UNIQUE LEXICAL identity.

        Review [P2]: the site key was module plus SHORT function name, and this
        package deliberately has many nested `body` functions -- so one exception
        excused a same-spelled interpolation in a sibling. Each site now carries
        its dotted lexical path, and `offenders` pairs an exception with one site
        rather than with a spelling.
        """
        found = []
        trees = {source.name: ast.parse(source.read_text(encoding="utf-8"),
                                        str(source))
                 for source in sorted(self.package().glob("*.py"))}
        constants = self.module_constants(trees)
        for name, tree in trees.items():
            owned = constants[name]

            def descend(node, path, proven):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    path = path + [node.name]
                    proven = dict(proven)
                    proven.update(self.safe_locals(node))
                if isinstance(node, ast.Call) \
                        and getattr(node.func, "id", "") in ("Refusal", "refuse") \
                        and node.args:
                    for piece in ast.walk(node.args[0]):
                        if isinstance(piece, ast.FormattedValue):
                            found.append(
                                (name, path[-1] if path else "<module>",
                                 piece.lineno, ast.unparse(piece.value),
                                 self.bounded_node(piece.value, owned, proven,
                                                   piece.lineno),
                                 ".".join(path) or "<module>"))
                for child in ast.iter_child_nodes(node):
                    descend(child, path, proven)

            descend(tree, [], {})
        return found

    def offenders(self, found):
        """Sites neither proved nor named, with each exception used ONCE.

        An entry excuses the number of LEXICAL SITES it declares and no more, so
        a new same-spelled interpolation in a sibling `body` is an offender until
        somebody looks at it and says so. That is the property the previous key
        lacked: it excused a spelling, and a spelling has no count.
        """
        left = {}
        for key, reason in self.NAMED_SITES.items():
            left[key] = reason[0] if isinstance(reason, tuple) else 1
        offending = []
        for site in found:
            where, function, line, expression, ok = site[:5]
            if ok:
                continue
            key = (where, function, expression)
            if left.get(key, 0) > 0:
                left[key] -= 1
                continue
            offending.append((where, function, line, expression))
        return offending

    def test_no_refusal_renders_an_unbounded_value(self):
        self.assertEqual(self.offenders(self.interpolations()), [],
                         "unbounded refusal diagnostics")

    def test_the_check_itself_is_not_vacuous(self):
        # A walker that finds nothing passes the case above for the wrong
        # reason, which is the failure mode of every AST check.
        found = self.interpolations()
        self.assertGreater(len(found), 100, "the walker found almost nothing")
        self.assertGreater(len({site[0] for site in found}), 3,
                           "the walker is only reaching one module")
        # And the named-site table may not become the answer: most
        # interpolations must be PROVEN, not excused.
        excused = [1 for site in found
                   if not site[4]
                   and (site[0], site[1], site[3]) in self.NAMED_SITES]
        self.assertLess(len(excused), len(found) // 4,
                        "the named-site table is carrying the check")

    def test_every_named_site_is_actually_there(self):
        # An entry nothing uses is a permission nobody asked for, and it is how
        # the table grows into the answer. This fired once already, on a
        # constant I had excused for a site the walker cannot see.
        live = {(site[0], site[1], site[3])
                for site in self.interpolations() if not site[4]}
        stale = sorted(set(self.NAMED_SITES) - live)
        self.assertEqual(stale, [], "named sites no interpolation needs")

    def test_every_named_site_covers_the_paths_it_was_written_for(self):
        """The unique LEXICAL identity, pinned.

        A count stops an exception covering more sites than it declares, but a
        count alone cannot say WHICH sites -- two `body` closures in one module
        share a key, and an exception written for one would silently move to the
        other if the first were deleted. So the dotted path of every excused site
        is written out here, and moving an exception between siblings changes
        this list.
        """
        excused = sorted((site[0], site[5], site[3])
                         for site in self.interpolations() if not site[4])
        self.assertEqual(excused, [
            ("core.py", "_require_capability", "capability"),
            ("core.py", "_require_free_receipt_id", "kind"),
            ("core.py", "_write_receipt.body", "kind"),
            ("core.py", "_write_receipt.body", "kind"),
            ("identity.py", "check_opaque_id", "fault"),
            ("session.py", "_install.read.call",
             "', '.join(parameters) or 'no operands'"),
            ("session.py", "_install.read.call", "name"),
            ("session.py", "_operands", "', '.join(missing)"),
            ("session.py", "_operands", "forbidden"),
            ("session.py", "_operands", "name"),
            ("session.py", "_operands", "name"),
            ("session.py", "_operands", "name"),
            ("session.py", "_operands", "name"),
            ("session.py", "_operands", "name"),
            ("store.py", "_describe_target", "failure.errno"),
            ("store.py", "create", "failure.errno"),
        ])

    def test_the_analyzer_refuses_what_it_cannot_prove(self):
        """The conservative half, stated as cases rather than as intent.

        Every shape below is one this analyzer COULD have guessed at. Guessing is
        what produced two rounds of false proof, so each is refused and the
        refusal is the documented behaviour.
        """
        package = pathlib.Path(tempfile.mkdtemp(prefix="v12-audit-"))
        self.addCleanup(shutil.rmtree, package, True)
        for name, source in [
                # A safe assignment AFTER the use proves nothing before it.
                ("late.py", "def boundary(raw):\n"
                            "    raise Refusal(f'{shown}')\n"
                            "    shown = label_of(raw)\n"),
                # A loop target is a binding this analyzer does not model.
                ("loop.py", "def boundary(rows):\n"
                            "    shown = label_of('x')\n"
                            "    for shown in rows:\n"
                            "        pass\n"
                            "    raise Refusal(f'{shown}')\n"),
                # A `with` target, likewise.
                ("context.py", "def boundary(thing):\n"
                               "    shown = label_of('x')\n"
                               "    with thing as shown:\n"
                               "        pass\n"
                               "    raise Refusal(f'{shown}')\n"),
                # A safe assignment nested in a branch does not dominate.
                ("branch.py", "def boundary(raw, flag):\n"
                              "    if flag:\n"
                              "        shown = label_of(raw)\n"
                              "    raise Refusal(f'{shown}')\n"),
                # A module constant rebound later is nobody's constant.
                ("rebound.py", "LIMIT = 'literal'\n"
                               "LIMIT = compute()\n"
                               "def boundary():\n"
                               "    raise Refusal(f'{LIMIT}')\n"),
                # An import from OUTSIDE this package proves nothing.
                ("foreign.py", "from elsewhere import LIMIT\n"
                               "def boundary():\n"
                               "    raise Refusal(f'{LIMIT}')\n"),
                # A walrus is a binding too.
                ("walrus.py", "def boundary(raw):\n"
                              "    shown = label_of(raw)\n"
                              "    if (shown := raw):\n"
                              "        pass\n"
                              "    raise Refusal(f'{shown}')\n")]:
            (package / name).write_text(source, encoding="utf-8")
        real = self.package
        self.package = lambda: package
        try:
            offending = {(where, expression)
                         for where, _, _, expression in
                         self.offenders(self.interpolations())}
        finally:
            self.package = real
        for name, expression in [("late.py", "shown"), ("loop.py", "shown"),
                                 ("context.py", "shown"), ("branch.py", "shown"),
                                 ("rebound.py", "LIMIT"),
                                 ("foreign.py", "LIMIT"),
                                 ("walrus.py", "shown")]:
            with self.subTest(shape=name):
                self.assertIn((name, expression), offending)

    def test_a_named_site_does_not_travel(self):
        # THE PROPERTY THAT DISTINGUISHES THIS FROM THE VERSION THAT FAILED:
        # `what` was excused everywhere by SPELLING, so an entry written for the
        # internal call sites silently covered the ten exported helpers.
        #
        # Fabricated findings rather than the real ones, because the question is
        # about the LOOKUP, not about today's table: an entry must excuse the one
        # site it names and nothing else.
        for module, function, expression in sorted(self.NAMED_SITES):
            with self.subTest(site=f"{module}:{function}:{expression}"):
                itself = [(module, function, 1, expression, False)]
                self.assertEqual(self.offenders(itself), [])
                for elsewhere in [(module, "another_function", 1, expression,
                                   False),
                                  ("another_module.py", function, 1, expression,
                                   False)]:
                    self.assertEqual(len(self.offenders([elsewhere])), 1,
                                     f"{expression} travelled")

    def test_the_classifier_accepts_only_the_exact_bounded_shape(self):
        # A bounded call somewhere inside an interpolation does not make the
        # WHOLE expression bounded, and a join is safe only when its input is
        # proved package-owned. Variable spelling alone proves neither origin:
        # exported identity helpers let their caller supply `what`.
        for expression in (
                "name_of(value) + value",
                "', '.join(caller_values)",
                "what"):
            with self.subTest(expression=expression):
                self.assertFalse(self._is_bounded(expression))
        for expression in ("name_of(value)", "len(values)"):
            with self.subTest(expression=expression):
                self.assertTrue(self._is_bounded(expression))

    def test_the_shapes_the_classifier_must_still_reject(self):
        # Beyond the reviewer's three, the shapes a next round would reach for.
        for expression in ("f'{name_of(value)}{value}'",
                           "name_of(value) if flag else value",
                           "[name_of(value), value][1]",
                           "', '.join(name_of(k) for k in keys)",
                           "str(value)",
                           "value.decode()",
                           "value[:60]",
                           "repr(value)",
                           "'%s' % value"):
            with self.subTest(expression=expression):
                self.assertFalse(self._is_bounded(expression), expression)

    def test_origin_proof_respects_modules_scopes_and_control_flow(self):
        # Origin is lexical, not package-global spelling. A constant in one
        # module does not prove a same-named parameter in another, and an
        # assignment inside a nested function is not an assignment in its
        # enclosing function. One safe assignment also proves nothing if an
        # unsafe assignment can reach the interpolation afterwards.
        with tempfile.TemporaryDirectory(prefix="v12-audit-") as root:
            package = pathlib.Path(root)
            (package / "constant.py").write_text(
                "LIMIT = 'package-owned'\n", encoding="utf-8")
            (package / "shadow.py").write_text(
                "def boundary(LIMIT):\n"
                "    raise Refusal(f'{LIMIT}')\n", encoding="utf-8")
            (package / "nested.py").write_text(
                "def outer(what):\n"
                "    def nested():\n"
                "        what = label_of('safe')\n"
                "    raise Refusal(f'{what}')\n", encoding="utf-8")
            (package / "reassigned.py").write_text(
                "def boundary(raw):\n"
                "    shown = label_of(raw)\n"
                "    shown = raw\n"
                "    raise Refusal(f'{shown}')\n", encoding="utf-8")
            (package / "conditional.py").write_text(
                "def boundary(raw, flag):\n"
                "    if flag:\n"
                "        shown = label_of(raw)\n"
                "    else:\n"
                "        shown = raw\n"
                "    raise Refusal(f'{shown}')\n", encoding="utf-8")
            real_package = self.package
            self.package = lambda: package
            try:
                offenders = self.offenders(self.interpolations())
            finally:
                self.package = real_package
        sites = {(module, function, expression)
                 for module, function, _, expression in offenders}
        self.assertIn(("shadow.py", "boundary", "LIMIT"), sites)
        self.assertIn(("nested.py", "outer", "what"), sites)
        self.assertIn(("reassigned.py", "boundary", "shown"), sites)
        self.assertIn(("conditional.py", "boundary", "shown"), sites)

    def test_a_named_site_does_not_travel_between_same_named_functions(self):
        # Module + short function name is not a site key when nested helpers
        # deliberately reuse names such as `body`. Two distinct lexical sites
        # may have the same module, function name and expression.
        with tempfile.TemporaryDirectory(prefix="v12-audit-") as root:
            package = pathlib.Path(root)
            (package / "duplicate.py").write_text(
                "def first():\n"
                "    def body():\n"
                "        raise Refusal(f'{kind}')\n"
                "def second():\n"
                "    def body():\n"
                "        raise Refusal(f'{kind}')\n", encoding="utf-8")
            real_package = self.package
            real_sites = self.NAMED_SITES
            self.package = lambda: package
            self.NAMED_SITES = {
                ("duplicate.py", "body", "kind"): "the first body only"}
            try:
                offenders = self.offenders(self.interpolations())
            finally:
                self.package = real_package
                self.NAMED_SITES = real_sites
        self.assertEqual(len(offenders), 1,
                         "one named site excused its same-named sibling")


class EveryCallerTextFamilyIsBounded(unittest.TestCase):
    """The audit, driven through the PUBLIC FACES rather than asserted.

    The AST check above proves every `Refusal` call site renders through a
    bounded mechanism. That is a claim about the source. This is the claim about
    the behaviour, and the two are different facts: a bounded rendering inside a
    message built by an unbounded helper is still an unbounded message, and the
    walker cannot see the helper.

    So each family below drives ONE MILLION caller-controlled characters through
    a supported entry point and measures what comes back. Families, not
    representatives: the review's two reproductions were a Work id and an actor,
    and treating those as the surface is what produced two rounds of the same
    finding.
    """

    HUGE = "q" * 1_000_000

    # TWO AUDITED SITES CANNOT BE WITNESSED HERE, and saying which is part of
    # the audit rather than a gap in it:
    #
    #   the assignment's authority UUID   the grammar is exactly 32 hexadecimal
    #                                     characters, so a wide value is refused
    #                                     by the grammar and this refusal is
    #                                     unreachable
    #   a colliding receipt identity      `check_opaque_id` caps it at 160, so
    #                                     the worst message this site can build
    #                                     is already short
    #
    # Both render through `name_of` anyway, as defence in depth if a grammar is
    # ever relaxed, and the AST check above is what witnesses them. "Bounded
    # because the grammar is fixed" is a different fact from "bounded because we
    # render it safely", and a reader should not have to work out which is which.

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "authority.sqlite3")
        self.authority = Authority.create(
            self.path, authority_uuid="0" * 31 + "a",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.authority.dispose)
        self.authority.certify_contract("v12")
        self._ops = 0

    def op(self):
        self._ops += 1
        return f"op-{self._ops}"

    def claimed(self, work_id="0000000a-W1", participant="baton.claude"):
        self.authority.create_work(
            work_id, "baton.impl", contract="v12",
            operation_id=("create-" + work_id)[:160])
        self.authority.add_route_handler("baton.impl", participant)
        session = self.authority.session(participant)
        # W16823: the claim answers a closed result; this fixture's callers
        # want the four-part fence out of it.
        return session, session.claim(
            {"work_id": work_id,
             "operation_id": self.op()})["assignment"]

    def assertBounded(self, family, phrase, call):
        """Bounded AND the refusal this family is about.

        `phrase` is not decoration. Without it a family passes when a DIFFERENT
        refusal fires first -- and one of these families did exactly that, being
        intercepted by the session binding check and never reaching the rule it
        was written for. A case that accepts any refusal measures whichever one
        happens to arrive.
        """
        with self.subTest(family=family):
            with self.assertRaises(Refusal) as caught:
                call()
            message = str(caught.exception)
            self.assertIn(phrase, message, f"{family}: wrong refusal")
            self.assertLess(len(message), 500, f"{family}: {len(message)}")
            self.assertNotIn(self.HUGE, message, family)
            # The verdict must survive the bound: a message trimmed to nothing
            # is bounded and useless.
            self.assertGreater(len(message), 20, family)

    def test_every_caller_text_family_is_bounded(self):
        wide_work = "0000000a-W" + "1" * 1_000_000
        wide_participant = "baton." + self.HUGE
        wide_route = self.HUGE

        # THE WORK IDENTITY family, including the stored value echoed back by a
        # LATER refusal -- which is the case the review singled out, because the
        # text is ours by the time it is rendered and still the caller's by
        # origin.
        self.authority.create_work(wide_work, "baton.impl",
                                   operation_id="create-wide-1")
        self.assertBounded("a Work identity already created",
                           "already exists",
                           # A FRESH IDENTITY PER ATTEMPT: `assertBounded`
                           # drives the call more than once, and W29400 made
                           # creation effectively-once -- so a fixed id would
                           # replay the first answer instead of reaching the
                           # refusal this case is about.
                           lambda: self.authority.create_work(
                               wide_work, "r.x", operation_id=self.op()))
        self.assertBounded("no such Work",
                           "no such Work",
                           lambda: self.authority.project_work(
                               "0000000b-W" + "2" * 1_000_000))

        # THE ROUTE and PARTICIPANT families.
        self.authority.create_work("0000000a-W9", wide_route, contract="v12", operation_id="create-" + "0000000a-W9")
        self.assertBounded(
            "a route that does not resolve",
                           "does not resolve to",
            lambda: self.authority.session("baton.other").claim(
                {"work_id": "0000000a-W9", "operation_id": self.op()}))
        self.authority.add_route_handler(wide_route, wide_participant)
        self.assertBounded(
            "an actor without the capability",
                           "does not hold the close capability",
            lambda: self.authority.session(wide_participant).close(
                {"work_id": "0000000a-W9", "operation_id": self.op(),
                 "outcome": "satisfying", "rationale": "r"}))

        # THE SLOT family: one participant, a second Work.
        session, _ = self.claimed(participant=wide_participant)
        self.authority.create_work("0000000a-W2", "baton.impl", contract="v12", operation_id="create-" + "0000000a-W2")
        self.assertBounded(
            "a participant already holding a slot",
                           "already holds",
            lambda: session.claim({"work_id": "0000000a-W2",
                                   "operation_id": self.op()}))

        # THE ASSIGNMENT-IDENTITY family, both directions.
        _, mine = self.claimed("0000000a-W3", "baton.gemini")
        foreign = dict(mine, participant="baton." + self.HUGE)
        self.assertBounded(
            "an assignment naming another participant",
                           "this session acts for",
            lambda: self.authority.session("baton.gemini").end(
                {"expect": foreign, "operation_id": self.op()}))
        # The AUTHORITY family is the one site that CANNOT carry unbounded text:
        # the grammar is exactly 32 hexadecimal characters, so a wide value is
        # refused by the grammar before this refusal is reachable at all. Written
        # out rather than dropped, because "bounded because the grammar is fixed"
        # is a different fact from "bounded because we render it safely", and a
        # reader should not have to work out which sites are which. `name_of`
        # here is defence in depth, witnessed by the AST check above.
        elsewhere = {"work_ref": {"authority_uuid": "b" * 31 + "a",
                                  "work_id": "0000000a-W3"},
                     "participant": "baton.gemini", "generation": 1}
        self.assertBounded(
            "an assignment naming another authority",
                           "assignment names authority",
            lambda: self.authority.session("baton.gemini").end(
                {"expect": elsewhere, "operation_id": self.op()}))

        # THE GATE family: an arrival whose supplied identity names another Work.
        other = dict(mine)
        other["work_ref"] = dict(mine["work_ref"], work_id=wide_work)
        self.assertBounded(
            "a gate arrival for another Work",
                           "this gate arrival is for",
            lambda: self.authority.session("baton.gemini").install_gate(
                {"work_id": "0000000a-W3", "operation_id": self.op(),
                 "gate": gate_token(GATE_QUIESCENCE, "x"), "expect": other}))

        # THE GATE-TOKEN family. A gate token's DETAIL is caller text with no
        # length, so a Work blocked by a wide gate rendered that gate into every
        # claim refusal. Reachable, and it was missing: the AST check caught the
        # site and no case drove it.
        blocked = "0000000a-W4"
        self.authority.create_work(
            blocked, "baton.impl", contract="v12", phase="block",
            gate=gate_token(GATE_QUIESCENCE, self.HUGE),
            operation_id=("create-" + blocked)[:160])
        self.assertBounded(
            "a Work blocked by a wide gate",
            "blocked by",
            lambda: self.authority.session("baton.gemini").claim(
                {"work_id": blocked, "operation_id": self.op()}))

        # THE CLOSE-IDENTITY family: the other half of "an identity is compared
        # against the Work it belongs to or not at all".
        self.authority.grant_capability("baton.gemini", "close")
        self.assertBounded(
            "a close whose identity names another Work",
            "this close is for",
            lambda: self.authority.session("baton.gemini").close(
                {"work_id": "0000000a-W3", "operation_id": self.op(),
                 "outcome": "satisfying", "rationale": "r", "expect": other}))

        # THE CONTRACT family. A contract name is caller text with no length,
        # and the certified-profile refusal renders it. Reachable through the
        # gate it belongs to, and the last of the four sites the AST check found
        # with no behavioural witness.
        contract = self.HUGE
        self.authority.certify_contract(contract, profile="reference")
        self.authority.create_work("0000000a-W5", "baton.impl", operation_id="create-" + "0000000a-W5",
                                   contract=contract)
        # A FRESH participant: one participant holds one claim across the whole
        # deployment, so reusing an earlier family's session would refuse for the
        # slot rule and never reach the contract rule.
        self.authority.add_route_handler("baton.impl", "baton.contract")
        wide_session = self.authority.session("baton.contract")
        held = wide_session.claim({"work_id": "0000000a-W5",
                                   "operation_id": self.op()})["assignment"]
        runtime = gate_token(GATE_CONTRACT_RUNTIME, "local")
        wide_session.install_gate({"work_id": "0000000a-W5",
                                   "operation_id": self.op(),
                                   "gate": runtime, "expect": held})
        self.assertBounded(
            "a certified profile the evidence does not name",
            "the certified profile for",
            lambda: wide_session.satisfy_gate(
                {"work_id": "0000000a-W5", "operation_id": self.op(),
                 "gate": runtime,
                 "evidence": {"kind": "certified-profile",
                              "profile": "something-else"}}))

        # THE OPAQUE-IDENTITY family, which is `opaque_id_fault`'s prose -- the
        # allow-listed entry the AST check cannot verify.
        self.assertBounded(
            "an operation identity that is not one",
                           "an operation id",
            lambda: self.authority.session("baton.gemini").settle_operation(
                {"operation_id": self.HUGE, "signature": "s"}))

        # THE TYPE-NAME family, both halves. `name_of` describes a value it
        # cannot show by its TYPE, and `type_name_of` describes a member name the
        # same way -- so a class named with two hundred thousand characters is
        # caller-controlled text arriving through the one helper whose whole job
        # is to render safely. Found because a mutation of `name_of`'s type
        # branch had NO WITNESS: every case I had drove the KEY path.
        wide_type = type(self.HUGE[:200000], (), {})
        self.assertBounded(
            "a value nothing can render, named by its type",
            "which is not JSON data",
            lambda: self.authority.set_policy("k", wide_type()))
        self.assertBounded(
            "a member named by something that is not text",
                           "members are named by text",
            lambda: self.authority.set_policy("k", {wide_type(): 1}))

    def test_the_digest_and_receipt_collision_families_are_bounded(self):
        session, mine = self.claimed()
        # The FIRST publication carries the wide digest, so the refusal below
        # echoes text that is OURS by the time it renders and the CALLER's by
        # origin. That distinction is the whole point of this family: a digest
        # read back out of our own column is not our text.
        digests = {"result_id": "result-1", "result_digest": self.HUGE,
                   "candidate_digest": "c" * 64, "input_digest": "i" * 64,
                   "policy_digest": "p" * 64}
        session.publish({"expect": mine, "operation_id": self.op(),
                         "proposal_id": "proposal-1", **digests})
        self.authority.create_work("0000000a-W2", "baton.impl", contract="v12", operation_id="create-" + "0000000a-W2")
        second = self.authority.session("baton.claude")

        # THE FROZEN-RESULT family: the same identity naming other bytes. The
        # digest is caller text and is ECHOED FROM THE STORE by this refusal.
        self.assertBounded(
            "a frozen result naming two sets of bytes",
                           "names one set of bytes",
            lambda: session.publish(
                {"expect": mine, "operation_id": self.op(),
                 "proposal_id": "proposal-2",
                 **dict(digests, result_digest="d" * 64)}))
        # And the same identity under a different assignment. The session
        # binding check fires first for another PARTICIPANT, so the reachable
        # case is the same participant on a LATER GENERATION of the same Work --
        # which is also the honest one: two live assignments claiming to have
        # produced the same frozen bytes.
        session.end({"expect": mine, "operation_id": self.op()})
        again = session.claim({"work_id": "0000000a-W1",
                               "operation_id": self.op()})["assignment"]
        self.assertNotEqual(again["generation"], mine["generation"])
        self.assertBounded(
            "a frozen result under another assignment",
                           "a different assignment",
            lambda: session.publish(
                {"expect": again, "operation_id": self.op(),
                 "proposal_id": "proposal-4", **digests}))

        # THE RECEIPT-COLLISION family: one identity, two receipts.
        for capability in ("verify", "review"):
            self.authority.grant_capability("baton.claude", capability)
        session.verify({"proposal_id": "proposal-1",
                        "verification_id": "receipt-1",
                        "observation": "passed", "operation_id": self.op()})
        self.assertBounded(
            "a receipt identity already taken",
                           "receipt needs its own",
            lambda: session.review({"proposal_id": "proposal-1",
                                    "review_id": "receipt-1",
                                    "disposition": "accepted",
                                    "operation_id": self.op()}))
        del second

    def test_the_store_path_family_is_bounded(self):
        # A path is caller text with NO GRAMMAR AT ALL, and every store refusal
        # named it. Linux caps a component at 255 bytes and a whole path at
        # 4096, so the long paths here are built by padding with `/.` segments:
        # every component is legal, the whole string is thousands of characters,
        # and the files are real. The kernel's limit is not a diagnostic bound --
        # a 4,000-character refusal is still four thousand characters.
        def padded(name, segments=1800):
            return self._root.name + "/." * segments + "/" + name

        absent = padded("absent.sqlite3")
        self.assertGreater(len(absent), 3000)
        self.assertBounded("open of an absent path",
                           "there is no authority store",
                           lambda: Authority.open(absent))
        self.assertBounded("create over an existing store",
                           "already exists at",
                           lambda: Authority.create(
                               padded("authority.sqlite3"),
                               authority_uuid="0" * 31 + "b"))
        empty = os.path.join(self._root.name, "empty.sqlite3")
        open(empty, "wb").close()
        self.assertBounded("open of an empty file",
                           "is empty and is not an authority store",
                           lambda: Authority.open(padded("empty.sqlite3")))
        foreign = os.path.join(self._root.name, "foreign.sqlite3")
        # A bare `connect` writes NOTHING, so the file would be zero bytes and
        # the empty-file rule would answer instead of the not-our-store rule.
        other = sqlite3.connect(foreign)
        other.execute("CREATE TABLE somebody_elses (id INTEGER)")
        other.commit()
        other.close()
        self.assertBounded("open of a file that is not our store",
                           "adopts nothing",
                           lambda: Authority.open(padded("foreign.sqlite3")))
        self.assertBounded(
            "open with a mismatched expected authority",
                           "never reassigned",
            lambda: Authority.open(padded("authority.sqlite3"),
                                   expected_authority_uuid="0" * 31 + "c"))
        # A directory is not a regular file, and its path is rendered too.
        self.assertBounded("open of a directory",
                           "not a regular file",
                           lambda: Authority.open(padded("")[:-1]))
        # And the path rendered inside a LABEL rather than a message. The
        # recorded-uuid check is handed `what="the authority UUID recorded at
        # <path>"`, so the path reaches a refusal built one function away. This
        # was the last mutation with no witness: the site was audited, and every
        # case opened a store whose recorded uuid was VALID, so the label was
        # never rendered.
        malformed = os.path.join(self._root.name, "malformed.sqlite3")
        connection = sqlite3.connect(malformed, isolation_level=None)
        connection.execute(
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        # THE FIXTURE'S VERSION IS THE BUILD'S, symbolically.  It was the
        # literal "1"; W16821 made the build schema 2, and a store recording an
        # older version is refused for its VERSION before the recorded-uuid
        # check is reached -- so this case would have stopped exercising the
        # site it is named for while still passing something.  The assertion
        # below is unchanged.
        for key, value in (("store_kind", "baton.v12.python.authority"),
                           ("schema_version", str(SCHEMA_VERSION)),
                           ("authority_uuid", "not-a-uuid")):
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (key, value))
        connection.close()
        self.assertBounded("a malformed recorded uuid at a long path",
                           "recorded at",
                           lambda: Authority.open(padded("malformed.sqlite3")))
