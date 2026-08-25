"""W4 cut A — the Worker Manager's own dependency allowlist.

PLAN item 4bi, authorized: the distribution ships two slices and only ONE may
reach a dependency. The authority's case holds it to the standard library; this
one holds the manager to exactly the ruled validator and its closure, so
"jsonschema is allowed here" never widens into "a dependency is allowed here".

A dependency set stated in a lock is a claim. These are the checks that make it
a fact, and they are deliberately two: what the SOURCE imports, and what the
LOCK pins. A module could import something the lock does not pin, and a lock
could pin something nothing imports; both are the same defect from opposite
ends.
"""

import ast
import pathlib
import re
import unittest

import baton_v12.authority as authority_package
import baton_v12.contracts as contracts
import baton_v12.worker_manager as worker_manager

HERE = pathlib.Path(__file__).resolve()
DISTRIBUTION = HERE.parents[2]
# BOTH manager packages. Cut B added `worker_manager` beside `contracts`, and an
# allowlist that named one of them would have let the other reach for anything --
# which is the rule-versus-site defect this file exists to prevent, at the level
# of the file itself.
MANAGER_PACKAGES = (pathlib.Path(contracts.__file__).resolve().parent,
                    pathlib.Path(worker_manager.__file__).resolve().parent)

# The ONE ruled third-party import. Its closure is a packaging fact rather than
# an import fact: `jsonschema` is what this package names, and `referencing`,
# `attrs`, `rpds-py` and `jsonschema-specifications` arrive because it needs
# them. So the import list is one name and the lock list is five.
ALLOWED_IMPORTS = {"jsonschema"}

# `ipaddress` is here for the canonical locator grammar's bracketed IPv6
# literal, deliberately: hand-rolling an address parser is exactly what the
# grammar ruling steers away from, and this is the standard library's own. It
# replaced `urllib`, which the grammar no longer needs -- every other clause is
# checked on the original text, so there is no parser in this boundary at all.
# Neither adds a runtime dependency: the ruled-validator rule is about
# third-party packages, and these are not.
STANDARD_LIBRARY = {"json", "pathlib", "hashlib", "re", "os", "typing",
                    "collections", "itertools", "functools", "contextlib",
                    "types", "importlib", "unicodedata", "sqlite3", "ipaddress",
                    # cut C: constant-time comparison and instant arithmetic
                    "hmac", "datetime"}

# The complete ruled runtime closure, written out. A closure that is merely
# "whatever pip resolved" is not pinned, and item 4bh named the version.
RUNTIME_CLOSURE = {
    "jsonschema": "4.26.0",
    "jsonschema-specifications": "2025.9.1",
    "referencing": "0.37.0",
    "attrs": "26.1.0",
    "rpds-py": "2026.6.3",
}


def manager_sources():
    found = []
    for package in MANAGER_PACKAGES:
        found.extend(package.rglob("*.py"))
    return sorted(found)


class TheManagerReachesForExactlyOneDependency(unittest.TestCase):

    def test_the_manager_imports_only_the_ruled_validator(self):
        allowed = STANDARD_LIBRARY | ALLOWED_IMPORTS
        for source in manager_sources():
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        with self.subTest(source=source.name, module=alias.name):
                            self.assertIn(alias.name.split(".")[0], allowed)
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue
                    root = (node.module or "").split(".")[0]
                    with self.subTest(source=source.name, module=node.module):
                        self.assertIn(root, allowed | {"baton_v12"})

    def test_only_one_module_reaches_the_validator_at_all(self):
        # A dependency that spreads is a dependency nobody can remove. The
        # validator is reached from `validate.py` and from nowhere else, so the
        # rest of the contracts package stays standard-library only and the
        # ruling's blast radius is one file.
        reaching = []
        for source in manager_sources():
            text = source.read_text(encoding="utf-8")
            tree = ast.parse(text, str(source))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                if any(name.split(".")[0] in ALLOWED_IMPORTS for name in names):
                    reaching.append(source.name)
        self.assertEqual(sorted(set(reaching)), ["validate.py"])

    def test_the_manager_stores_are_not_the_authority_s(self):
        # Cut B: two SQLite stores in one distribution. Neither may open the
        # other, and the marker is what makes that decidable -- a version number
        # is true of both.
        from baton_v12.authority.schema import STORE_KIND as AUTHORITY_KIND
        from baton_v12.worker_manager import STORE_KIND as MANAGER_KIND
        self.assertNotEqual(AUTHORITY_KIND, MANAGER_KIND)

    def test_the_manager_does_not_import_the_authority(self):
        # The two slices share a distribution and nothing else. The manager
        # consumes an INJECTED session in a later cut; it never imports the
        # authority's modules, and reaching past the authority's exported
        # surface is what its own boundary cases refuse.
        for source in manager_sources():
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    with self.subTest(source=source.name):
                        self.assertNotIn("authority", (node.module or ""))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        with self.subTest(source=source.name):
                            self.assertNotIn("authority", alias.name)

    def test_the_authority_surface_still_exposes_no_manager_capability(self):
        # 4bi asks for this explicitly: the authority's supported surface must
        # still carry no manager or validator capability, so the manager's new
        # dependency cannot have leaked across the split.
        for name in authority_package.__all__:
            with self.subTest(name=name):
                # "contract" is deliberately NOT in this list. A contract
                # IDENTIFIER -- `V12`, `is_v12_contract`, the contract-runtime
                # gate -- is an assignment fact and belongs to the authority; a
                # contract DOCUMENT belongs to the manager. Forbidding the word
                # would have measured the spelling instead of the capability,
                # which is the mistake the authority's own audit was corrected
                # for twice.
                for forbidden in ("validate", "schema", "manager", "worker",
                                  "jsonschema"):
                    self.assertNotIn(forbidden, name.lower())


class TheLockPinsExactlyTheRuledClosure(unittest.TestCase):

    def lock(self):
        return (DISTRIBUTION / "requirements.lock").read_text(encoding="utf-8")

    def pinned(self):
        found = {}
        for line in self.lock().split("\n"):
            match = re.match(r"^([A-Za-z0-9._-]+)==([0-9][^ \\]*)", line.strip())
            if match:
                found[match.group(1).lower()] = match.group(2)
        return found

    def test_every_runtime_distribution_is_pinned_at_the_ruled_version(self):
        pinned = self.pinned()
        for name, version in RUNTIME_CLOSURE.items():
            with self.subTest(distribution=name):
                self.assertEqual(pinned.get(name), version)

    def test_nothing_beyond_the_closure_and_the_build_tools_is_pinned(self):
        expected = set(RUNTIME_CLOSURE) | {"pip", "setuptools"}
        self.assertEqual(set(self.pinned()), expected)

    def test_every_pinned_artifact_carries_a_hash(self):
        # `--require-hashes` makes the locked build refuse an artifact whose
        # bytes are not the pinned ones, so a line without a hash is a line that
        # cannot install.
        lines = [line.strip() for line in self.lock().split("\n")]
        for index, line in enumerate(lines):
            if re.match(r"^[A-Za-z0-9._-]+==", line):
                with self.subTest(pin=line):
                    self.assertTrue(line.endswith("\\"))
                    self.assertTrue(lines[index + 1].startswith("--hash=sha256:"))

    def test_the_declared_dependencies_agree_with_the_lock(self):
        # `pyproject.toml` states what the distribution DEPENDS on and the lock
        # states the resolved closure. The first must appear in the second, or
        # an install resolves something the lock never hashed.
        pyproject = (DISTRIBUTION / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r"dependencies = \[(.*?)\]", pyproject, re.S)
        self.assertIsNotNone(declared)
        for match in re.finditer(r'"([A-Za-z0-9._-]+)==([^"]+)"', declared.group(1)):
            with self.subTest(dependency=match.group(1)):
                self.assertEqual(RUNTIME_CLOSURE.get(match.group(1).lower()),
                                 match.group(2))


class TheHashesAreTheArtifactsOwn(unittest.TestCase):
    """SUPERSEDED in mechanism, RETAINED in property.

    This class used to assert a wheel existed locally for every pinned name,
    because the build resolved from a repository-local wheelhouse. PLAN item 4bp
    removed that: dependency distributions do not belong in Git, and a checkout
    downloads the locked artifacts into a disposable environment instead.

    The property it was protecting is NOT superseded. "A lock whose hashes came
    from a document rather than from the bytes pins a claim" is true wherever the
    bytes come from -- so the check moved from the wheelhouse to the environment
    the lock actually produces, rather than being deleted along with the
    directory it used to read.
    """

    def lock(self):
        return (DISTRIBUTION / "requirements.lock").read_text(encoding="utf-8")

    def test_the_repository_carries_no_dependency_distributions(self):
        # The ruling, as a case. A wheel or sdist reappearing anywhere under the
        # distribution is the thing item 4bp forbids, and "we removed it once"
        # is not a property.
        found = [path.name for pattern in ("*.whl", "*.tar.gz", "*.zip")
                 for path in DISTRIBUTION.rglob(pattern)]
        self.assertEqual(found, [])
        self.assertFalse((DISTRIBUTION / "wheelhouse").exists())

    def test_the_build_still_enforces_the_hashes_it_pins(self):
        """`--require-hashes` is what makes this a LOCKED build.

        Without it the index chooses and the lock only advises.

        THE ASSERTION READS THE RECIPE, not the file. My first version searched
        the whole justfile, and the comment two lines above the install command
        contains the flag -- so removing it from the COMMAND changed nothing and
        the case passed on its own prose. Measuring the documentation instead of
        the mechanism is the defect this package has been corrected for twice.
        """
        justfile = (DISTRIBUTION / "justfile").read_text(encoding="utf-8")
        commands = [line for line in justfile.split("\n")
                    if "pip" in line and "install" in line
                    and not line.strip().startswith("#")]
        locked = [line for line in justfile.split("\n")
                  if "requirements.lock" in line
                  and not line.strip().startswith("#")]
        self.assertTrue(commands)
        self.assertTrue(any("--require-hashes" in line
                            for line in commands + locked), commands + locked)
        # And the removed mechanism is gone from the recipes AND the prose.
        self.assertNotIn("--find-links", justfile)
        self.assertNotIn("WHEELHOUSE", justfile)

    # Mechanisms this distribution no longer has. A live statement describing
    # one is acceptance drift, which item 4bp had to name twice -- first two
    # module docstrings, then the gate's own prose.
    #
    # `--no-index` is deliberately NOT here: the second install uses it
    # correctly, to install THIS project from the local directory rather than
    # resolve it from an index. A removed-mechanism list that swept it up would
    # be banning a word instead of a mechanism.
    REMOVED_MECHANISMS = ("wheelhouse", "--find-links", "offline")

    # A line that marks what follows as history rather than as description.
    HISTORICAL = ("superseded", "replaces", "used to", "no longer",
                  "may supply")

    def test_no_live_statement_describes_a_removed_mechanism(self):
        """Prose is part of the deliverable, and stale prose is a wrong answer.

        A reader who trusts a comment describing a mechanism the tree does not
        have has been told something false by the tree itself -- and the last two
        reviews each found one, first in two module docstrings and then in the
        gate's own text.

        A removed mechanism may be MENTIONED only after a line that marks the
        passage as history. Line-scoped rather than paragraph-scoped on purpose:
        my first version allowed a whole paragraph if it said "superseded"
        anywhere, and the live sentence and the historical note lived in ONE
        comment block -- so the escape hatch swallowed exactly the drift it was
        written to catch.
        """
        for name in ("justfile", "requirements.lock"):
            text = (DISTRIBUTION / name).read_text(encoding="utf-8")
            historical = False
            for number, line in enumerate(text.split("\n"), 1):
                if not line.strip():
                    historical = False
                if any(marker in line for marker in self.HISTORICAL):
                    historical = True
                    continue
                for mechanism in self.REMOVED_MECHANISMS:
                    if mechanism not in line or historical:
                        continue
                    with self.subTest(file=name, line=number):
                        self.fail(f"{name}:{number} describes {mechanism!r} "
                                  f"as live: {line.strip()[:160]}")

    def test_every_hash_is_a_sha256_of_something(self):
        # Shape, not provenance: a truncated or mistyped digest cannot verify
        # anything, and `--require-hashes` would only find that out at install.
        digests = re.findall(r"--hash=sha256:([0-9a-fA-F]*)", self.lock())
        self.assertEqual(len(digests), 7)
        for digest in digests:
            with self.subTest(digest=digest[:16]):
                self.assertEqual(len(digest), 64)
                self.assertEqual(digest, digest.lower())

    def test_the_locked_stage_is_what_proves_the_pin(self):
        """A green SOURCE run does not prove the dependency pin, and says so.

        Found while implementing item 4bp: the source stage resolves whatever
        `jsonschema` the ambient interpreter has -- 4.19.2 on this machine, while
        the lock pins 4.26.0 -- so it had been proving the code works with a
        version this distribution does not pin, quietly, for two rounds.

        The arrangement is fine; the SILENCE was not. So the gate must actually
        include the stage that builds the locked environment, and that is
        asserted here rather than assumed from a recipe name.
        """
        justfile = (DISTRIBUTION / "justfile").read_text(encoding="utf-8")
        self.assertRegex(justfile, r"(?m)^gate: .*\bbuild\b")
        # And the locked stage runs THIS suite inside the environment it built,
        # rather than merely importing the package there.
        self.assertRegex(justfile, r'PYTHONPATH= "\$ENV/bin/python" -m unittest')

    def test_the_pinned_versions_hold_when_we_are_inside_that_environment(self):
        """The retained property, measured where the artifacts now live.

        Reported rather than silently skipped when this is not that environment:
        a skip nobody can see is how the mismatch above stayed invisible.
        """
        import importlib.metadata as metadata
        installed = {}
        for name in RUNTIME_CLOSURE:
            try:
                installed[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                installed[name] = None
        if installed != RUNTIME_CLOSURE:
            self.skipTest(
                f"not the locked environment: resolved {installed}, the lock "
                f"pins {RUNTIME_CLOSURE}. `just build` runs this suite inside "
                f"the environment where this assertion holds.")
        self.assertEqual(installed, RUNTIME_CLOSURE)


class NoPublicOperationTakesInternalState(unittest.TestCase):
    """The rule the traversal-depth finding was one instance of.

    A leading underscore names a CONVENTION, not a boundary. `_depth` was a
    parameter of two exported functions, so a caller could hand the descent a
    negative starting point and walk straight past a bound the same correction
    had just made shared. The bound was shared; its enforcement STATE was not.

    Fixing the two functions a review names is what this repository has caught
    me doing five times, so the rule is checked instead: no public operation in
    this package takes a parameter that is bookkeeping rather than an operand.
    A new one fails the gate rather than waiting for a sixth review.
    """

    # Parameters a public operation may legitimately take. Written out, because
    # deriving "is this an operand" from a name is the guessing this case exists
    # to stop -- and an entry here is a claim somebody has to make deliberately.
    OPERANDS = {
        # contracts
        "value", "payload", "document", "name", "names", "what", "required",
        "validator",
        # the control store
        "path", "incarnation", "clock", "operation_id", "kind", "signature",
        "action", "operands", "refusal", "sealed",
        # cut C: the injected capability, the offer and the claim
        "store", "port", "offer_id", "work_id", "work_ref", "participant",
        "runtime_attempt_id", "input_digest", "policy_digest", "profile_digest",
        "profile_name", "intent_digest", "mint_bearer", "bearer", "decision",
        "authority_uuid",
        # the contracts layer's shared pairing question
        "category", "code", "definition", "manifest",
        # §12's manifest rules
        "uri", "content",
        # cut D: the runtime attempt
        "attempt_id", "adapter_name", "adapter_digest", "image_digest",
        "toolchain_digest", "expect", "axis", "source",
        # the injected runtime adapter and provider agent, and what a call
        # says it started
        "adapter", "agent", "minted", "minted_labels",
        "reason", "now", "ttl_seconds", "refused_evidence", "disposition",
        "may_retire",
        # the boundary layer
        "from_instant", "seconds", "discriminator", "optional", "variants",
        "record", "columns", "issued",
        # W6592 cut A: the composition. `advertised` is what a relay says it
        # can do and `profile` is the document being certified; the two
        # negotiation operands are what the agent ANSWERED WITH, which is the
        # only thing a handshake has to go on.
        "advertised", "profile", "agent_protocol_version",
        "agent_session_capabilities",
        # W6631: the source materializer. `root`, `storage`, `origin`,
        # `inputs` and `git_metadata` are PLACES this component is handed or
        # creates; `source` is the descriptor being delivered; `ref`,
        # `revision` and `into` are what the repository port forwards.
        "root", "storage", "origin", "inputs", "git_metadata", "source",
        "ref", "revision", "into", "git_dir", "assignment_id", "git",
        # W6632: the OCI adapter core. `engine` is which of the two runtimes is
        # being spoken to, `labels` is the frozen reconciliation set, `mounts`
        # is what the worker may see, `runtime_id` is one exact identity,
        # `image_digest` is the image named by digest, `name` is the container
        # name this manager chooses, `seconds` is a stop timeout and `request`
        # is the seam `attempts.py` already calls with.
        "engine", "labels", "mounts", "runtime_id", "image_digest", "name",
        "seconds", "request",
        # W6627: the agent session. `posture` is which of the two containers,
        # `session_epoch` is which allocation of it, `session_ref` is the §3.1
        # reference that labels evidence and `provider_session_id` is its
        # fourth component; `state` is one of the nine, `from_state`/`to_state`
        # are the two ends of a transition question, `intent` is the caller's
        # own opening identity (the operand that makes a retry distinguishable
        # from a deliberate second session), `evidence` and `observed_identity`
        # are what positively established an absence, `turn_in_flight` decides
        # an outcome and is never inferred, and `prompt` is what a refused
        # re-prompt was carrying.
        #
        # `connection` and `at` are deliberately ABSENT. The composition
        # helpers that take a caller's own transaction and its sampled instant
        # are private -- an act that takes a posture and fails to become a
        # session, or records an observation whose slot movement did not land,
        # is exactly the stranding this axis exists to remove -- so neither is
        # a public operand, and declaring one would be a permission nobody
        # asked for.
        "posture", "session_epoch", "session_ref", "provider_session_id",
        "state", "from_state", "to_state", "intent", "evidence",
        "observed_identity", "turn_in_flight", "prompt",
    }

    # Names that are BOOKKEEPING whatever they are attached to. This is the
    # discriminating half of the rule, and it replaces a ratio.
    #
    # My first version required the operand list to stay SMALLER than the
    # surface it permits, as a proxy for "the list must not become the answer".
    # Cut C made that proxy wrong rather than strict: a package can legitimately
    # have more distinct operand names than functions, and the ratio then fails
    # for growth instead of for laxity. Measuring the wrong thing strictly is
    # not rigour, so the proxy is gone and the property it stood for is stated
    # directly.
    NEVER_OPERANDS = ("depth", "seen", "visited", "budget", "stack", "cursor",
                      "offset", "index", "accumulator", "memo")

    def public_functions(self):
        """Every public function AND public method.

        Cut B put the store's surface on a class, so a sweep that walked only
        module-level functions would have stopped seeing most of the package the
        moment it grew a class -- a check that silently narrows as the code
        widens is worse than no check.
        """
        found = []
        for source in manager_sources():
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    found.append((source.name, node))
                elif isinstance(node, ast.ClassDef):
                    for member in node.body:
                        if isinstance(member, ast.FunctionDef) \
                                and not member.name.startswith("_"):
                            found.append((f"{source.name}:{node.name}", member))
        return found

    def test_every_public_parameter_is_a_declared_operand(self):
        # ONE mechanism, not two. My first version had a separate
        # "no underscore-named parameter" case in front of this one, and
        # measured it: removing that case changed no verdict, because an
        # underscore-named parameter is not a declared operand either. A guard
        # nothing can observe is worth less than the line it costs, so it is
        # gone rather than reported.
        #
        # This is also the stronger statement. A future `depth`, `seen` or
        # `budget` WITHOUT an underscore would have passed the weaker case and
        # been exactly the same defect.
        for where, node in self.public_functions():
            arguments = node.args
            names = ([a.arg for a in arguments.posonlyargs]
                     + [a.arg for a in arguments.args]
                     + [a.arg for a in arguments.kwonlyargs])
            for parameter in names:
                if parameter in ("self", "cls"):
                    continue
                with self.subTest(function=f"{where}:{node.name}",
                                  parameter=parameter):
                    self.assertIn(parameter, self.OPERANDS)

    def test_no_declared_operand_is_bookkeeping_by_nature(self):
        # The half that actually discriminates. `_depth` was caught by its
        # underscore; a future `depth` would not have been, and neither would
        # `seen` or `budget`.
        for name in sorted(self.OPERANDS):
            with self.subTest(operand=name):
                for forbidden in self.NEVER_OPERANDS:
                    self.assertNotIn(forbidden, name)

    def test_no_declared_operand_is_stale(self):
        # An entry nothing uses is a permission nobody asked for, and it is how
        # a declared list quietly becomes the answer. Same discipline as the
        # named-site table in the diagnostics audit.
        used = set()
        for _, node in self.public_functions():
            arguments = node.args
            used |= {a.arg for a in (arguments.posonlyargs + arguments.args
                                     + arguments.kwonlyargs)}
        self.assertEqual(sorted(self.OPERANDS - used), [])

    def test_the_sweep_is_not_vacuous(self):
        # A walker that finds nothing passes the cases above for the wrong
        # reason, which is the failure mode of every check like this.
        found = self.public_functions()
        self.assertGreater(len(found), 20)
        self.assertGreater(len({where for where, _ in found}), 3)


class AnExportedLabelIsCallerInput(unittest.TestCase):
    """The rule the `durable_text` export broke, checked instead of remembered.

    A diagnostic label is this package's own prose at an internal call site and
    CALLER INPUT the moment the function is exported. The distinction is invisible
    in the function body, which is exactly why it keeps being missed: the
    authority slice was corrected for ten exported helpers whose labels were
    interpolated raw, and I then widened a manager helper into the same hazard by
    adding one name to two `__all__` lists.

    So the rule is mechanical now. Every exported function that takes a label
    must route it through the bounded, no-code label rule before anything renders
    it -- or not be exported.
    """

    LABEL_PARAMETERS = ("what", "where", "label")
    BOUNDING = ("label_of",)

    def exported_functions(self):
        """Every function actually reachable through a package's `__all__`."""
        found = []
        for package in (contracts, worker_manager):
            root = pathlib.Path(package.__file__).resolve().parent
            sources = {}
            for source in sorted(root.rglob("*.py")):
                tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        sources.setdefault(node.name, (source.name, node))
            for name in package.__all__:
                if name in sources and callable(getattr(package, name, None)):
                    found.append((package.__name__, *sources[name]))
        return found

    def test_every_exported_function_bounds_the_label_it_is_given(self):
        for package, where, node in self.exported_functions():
            arguments = node.args
            names = ([a.arg for a in arguments.posonlyargs]
                     + [a.arg for a in arguments.args]
                     + [a.arg for a in arguments.kwonlyargs])
            labels = [name for name in names if name in self.LABEL_PARAMETERS]
            if not labels:
                continue
            with self.subTest(function=f"{package}.{node.name}", where=where):
                bounded = any(
                    isinstance(piece, ast.Call)
                    and getattr(piece.func, "id", "") in self.BOUNDING
                    for piece in ast.walk(node))
                self.assertTrue(
                    bounded,
                    f"{where}:{node.name} is exported and takes {labels}; a "
                    f"label is caller input at an exported boundary and must be "
                    f"bounded before anything renders it")

    def test_the_sweep_finds_the_exported_functions_it_claims_to(self):
        # A walker that resolves nothing passes the case above for the wrong
        # reason -- and the surface it must see spans both packages.
        found = self.exported_functions()
        self.assertGreater(len(found), 8)
        self.assertEqual(len({package for package, _, _ in found}), 2)
        # And at least one of them really does take a label, or the rule above
        # is being proved against an empty set.
        with_labels = [node for _, _, node in found
                       if any(a.arg in self.LABEL_PARAMETERS
                              for a in node.args.args + node.args.kwonlyargs)]
        self.assertGreater(len(with_labels), 1)
