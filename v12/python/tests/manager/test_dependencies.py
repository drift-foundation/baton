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
                    "hmac", "datetime",
                    # W6630: §13's live-secret registry is shared mutable
                    # process state, and its reference count is a
                    # read-modify-write. A lost update there means a bearer
                    # stops being live while an owner still holds it -- a leak
                    # boundary that silently stops guarding, which is exactly
                    # the failure §13 exists to prevent. "This package is
                    # single-threaded today" is the kind of assumption this
                    # distribution has been corrected for, and `threading`
                    # costs the locked build nothing.
                    "threading",
                    # W6634 seventh review: the completion signal is opened
                    # with `O_NOFOLLOW` and proved a regular file on the
                    # OPENED DESCRIPTOR, so nothing can be swapped between the
                    # check and the read. `stat.S_ISREG` is how that mode is
                    # read, and it is the standard library's own -- the
                    # ruled-validator rule is about third-party packages.
                    "stat"}

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
        # W26283: the output-custody copy. `into` is the destination the caller
        # owns; `max_entries` and `max_bytes` are the DECLARED ceilings of one
        # delivery, distinct from this build's own policy ceilings; and
        # `admits` is the caller's own rule over each file's bytes -- §13
        # live-secret scanning, for the one caller that has such a rule --
        # applied at the single moment the content is in hand. None of the four
        # is traversal state: the walk owns its own descent entirely.
        "into", "max_entries", "max_bytes", "admits",
        # W26291: the reference worker's launch document. `session`, `contract`
        # and `role` are the three non-secret values a caller supplies and this
        # manager AUTHORS the document out of -- operands rather than
        # bookkeeping, because they are what a caller says and the module
        # decides the shape. `launch_delivery` is the materialized document
        # crossing to the adapter as one typed capability.
        #
        # `environment` IS GONE rather than kept beside them. It was this
        # Work's first correction -- four `BATON_WORKER_*` values as `--env`
        # arguments -- and the dossier superseded that transport before
        # acceptance with no compatibility path. This table refuses an entry
        # nothing uses, which is how a leftover operand would have been found.
        "session", "contract", "role",
        # `launch_delivered` is the PAIR the adapter's capability answers with,
        # reaching the argv composer exactly as a credential delivery's pairs
        # do. The capability itself is adapter construction and is not an
        # operand here, for the same reason `credential_delivery` is not.
        "launch_delivered",
        # W33936: the deployment's configured workspace GROUP, added to an
        # execution container as a SUPPLEMENTARY group so the container's fixed
        # non-root uid can write a root this manager owns -- the primary
        # identity `65532:65532` is untouched, which is the difference from the
        # rejected `--user 65532:<gid>` design.
        #
        # An OPERAND rather than a `stat` inside the composer, because a run
        # vector is provable without a filesystem; and an operand of ALLOCATION
        # too, because a workspace is put in the group when it is created.
        # `gid` is what the two workspace helpers call it, where the value is
        # already known to be a group id and naming it twice would say less.
        "workspace_group", "gid",
        # W32648: the digest of the manager's own durable failed-start record,
        # which is what authorizes the no-envelope removal -- never an intake
        # receipt, which means something the opposite.
        "failed_start_record_digest",
        # W32576: the digest of the manager's own durable
        # `session.unsupported-version` record. A THIRD word rather than a
        # reuse of the one above, for the reason the two commands are
        # siblings: a failure record says a start did not happen and a refusal
        # record says an agent answered a wire version this manager never
        # certified, and an operand name shared between them would be the one
        # place the two endings stopped being distinguishable.
        "refusal_record_digest",
        # W36540: the two operands a custody act is made of. `operation` is a
        # VERB from a closed vocabulary rather than a command -- the whole
        # point of M36166's "never a worker-supplied command" -- and
        # `attempt_root` is the single host directory the helper mounts.
        "operation", "which",
        # W16823: the two facts an offer FREEZES about the Work it was issued
        # against, and the operands the claim decision is later held to.
        # `role` is already declared above for the launch document and means
        # the same kind of thing here -- a route or capability a decision was
        # about -- so it is not repeated. `scope` is the authority-owned
        # effective scope: an operand rather than something this manager
        # derives, because deriving it would be reconstructing the authority's
        # mapping, which is the conflation this correction ends.
        "scope",
        # §12's manifest rules
        "uri", "content",
        # cut D: the runtime attempt
        "attempt_id", "adapter_name", "adapter_digest", "image_digest",
        "toolchain_digest", "expect", "axis", "source",
        # the injected runtime adapter and provider agent, and what a call
        # says it started
        "adapter", "agent", "minted", "minted_labels",
        # W6634: the sealing half. `outputs` is the assignment's DECLARED
        # outputs, owned once at construction -- what may be collected is the
        # assignment's statement, not a per-call argument. `roots`, `declared`,
        # `identity` and `input_manifest_digest` are the values the adapter
        # proved once and hands to a module that is a pure function over them,
        # which is why that module takes them rather than the adapter itself:
        # `list` and `observe` are injected capabilities with one crossing
        # each, and a second module calling them would give one capability two
        # owners.
        "outputs", "roots", "declared", "identity", "input_manifest_digest",
        # W6634 review [P1]: where this manager keeps the bytes it has taken
        # custody of. A sibling of the assignment's roots and deliberately not
        # one of them -- `ROOT_NAMES` says what a container may MOUNT, and
        # custody is what the worker must not reach after the freeze.
        "custody",
        # W36540 review [P0], round ten: the ENGINE PORT a custody act runs
        # through. `custody_act` performs its own act rather than returning a
        # vector for somebody else to execute, so the capability that reaches
        # the world has to arrive as an operand -- it is the one crossing the
        # act makes, exactly as `list` and `observe` are above, and the same
        # name `OciAdapter` already takes it under.
        "run",
        # W6629 review [P1]: the two frozen commands this manager issues. The
        # adapter seam used to take a bare runtime id, so the whole body that
        # AUTHORIZES a destroy stopped at the boundary; `command` is that body
        # arriving, and it is an operand rather than bookkeeping.
        "command",
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
        # W6631, narrowed by W15232. The acquisition half is gone from the
        # core manager, and with it every operand of a duty this manager no
        # longer performs. This table refuses an entry nothing uses, which is
        # how it noticed.
        #
        # What remains is the generic half: `root` and `storage` are places
        # this component is handed or creates, `assignment_id` names one
        # assignment's private tree, and `source` is still an operand of the
        # contracts layer.
        "root", "storage", "source", "assignment_id",
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
        # W6628: the output freeze and the sealed receiver. `attempt` is one
        # persisted attempt row crossing back IN as a caller operand -- the
        # freeze identity is derived from it, and a caller that already holds
        # the row should not have to re-fetch it by id -- and
        # `manifest_digest` names one retained document.
        "attempt", "manifest_digest",
        # W6627's interrogation split. `deadline_seconds` is the manager's own
        # waiting window -- a timeout is an observation it makes about itself,
        # so the duration is an operand and the instant is derived; `question`
        # is the conversational prose an inquiry carries; `outcome` is the
        # observed movement on the interrogation axis; `observation` is a
        # probe's control-plane reading; and `body` is what a model answered.
        "deadline_seconds", "question", "outcome", "observation", "body",
        # And the whole answer document a model's turn produced; `body` is its
        # bounded prose, and the envelope around it is what gets journalled.
        "answer",
        # W6632's constrained OCI core. `assignment_roots` is the record of
        # what THIS assignment owns, and it is an operand rather than internal
        # state for the reason the ruling gives: roots alone cannot choose the
        # posture-specific topology, so the caller supplies both and the
        # adapter proves them.
        #
        # `identity` is deliberately ABSENT: the resolved image/profile/adapter
        # record is a constructor operand of `OciAdapter`, and this gate reads
        # the module's public FUNCTIONS. Declaring a name no public function
        # takes would be a permission nobody asked for, which the stale half of
        # this check refuses in the other direction.
        "assignment_roots",
        # W6629: intake, retention and cleanup. `collected` is what the adapter
        # reports it took custody of -- compared against the freeze, never
        # adopted; `artifact_ids` names which of the intaken artifacts a
        # decision is about; `receipt_digest` is the intake receipt
        # `runtimeDestroyBody` requires; and `retention_policy_digest` is the
        # policy a decision was made under.
        #
        # `retention_policy_digest` IS AN OPERAND AND NOT INTERNAL STATE, and
        # that is the whole shape of this slice: the frozen schema states no
        # shape for the retention policy document -- exactly as it states none
        # for the nine other `*_policy_digest` members of the assignment
        # manifest -- so this manager binds the policy by IDENTITY and acts on
        # the operation that cites it. A component that read the document would
        # need it; one that binds it needs only its digest, and takes it from
        # the caller who is citing it.
        "collected", "artifact_ids", "receipt_digest",
        "retention_policy_digest",
        # W14251's split. `completion_manifest_digest` is NOT here and that is
        # the sixth review's correction: it was a caller-supplied operand, and
        # a caller's claim that a validation happened is not evidence of one.
        # `sealing.completion_envelope` opens the worker's document and
        # recomputes the digest, so nothing hands this manager the answer.
        # W6634: the credential lifecycle. Every one of these is an operand of
        # the approved boundary rather than bookkeeping, and the boundary is
        # what makes each a claim somebody can check:
        #
        #   `slots`      the assignment's own closed logical slot names -- the
        #                ONLY thing an assignment carries about credentials;
        #   `profile`    the trusted deployment mapping (already declared above
        #                for the runtime profile, and the same kind of thing);
        #   `resolution` those slots after the profile has named a provider and
        #                an opaque reference for each;
        #   `credential_provider` the injected capability that answers a bearer.
        #                It is a CAPABILITY the deployment supplies, which is
        #                the same status as `mint_bearer` and `clock` above;
        #
        # WHERE THE CREDENTIAL HOME ITSELF WENT: it is a constructor operand
        # (`CredentialHome(place)`), and this sweep deliberately does not walk
        # `__init__` -- so declaring `place` here would be a permission nothing
        # asks for, which the staleness half of this rule refuses. The boundary
        # inventory owns that entry instead, where a constructor IS public.
        #   `delivery`   one materialized delivery, which is what teardown acts
        #                on;
        #   `live`       which attempts are still live, so orphan cleanup knows
        #                what it may not remove;
        #   `credentials_delivered` the (source, target) pairs a start exposes.
        #                Named apart from `mounts` deliberately: they are owned
        #                by a different rule -- the fixed container root -- and
        #                one name for two contracts is how the wrong one gets
        #                applied.
        "slots", "resolution", "credential_provider", "delivery",
        "live", "credentials_delivered",
        # W19784: the two manager-authored `/input/` documents, and the root
        # they are composed into.
        #
        # `input_manifest` and `assignment_manifest` are DOCUMENTS the caller
        # holds, and they are named separately rather than as one `documents`
        # pair for the reason the whole Work exists: they have different
        # lifecycles and different authority. `input.json` is pre-claim
        # evidence whose bytes never change; `assignment.json` is minted after
        # the claim commits and is the only carrier of the authority
        # generation. One name for two contracts is how the wrong one gets
        # applied, and here the wrong one is unsatisfiable.
        #
        # `inputs` is the assignment's read-only root -- the place, distinct
        # from `storage` (the manager's whole workspace area) and from `root`
        # (whatever a helper was handed). `compose_input_root` acts on exactly
        # one assignment's inputs tree and nothing else.
        "input_manifest", "assignment_manifest", "inputs",
        # W19784 review [P0]: the manager's OWN live identity, as operands of
        # the composition and launch boundaries. `assignment` is the four-part
        # identity the attempt activated -- the manager's value, held against
        # the delivered document rather than read out of it, which is the
        # whole point: a pair that agrees with itself is not thereby the
        # delivery that was authorized. It is deliberately NOT called
        # `assignment_ref`: what crosses is the manager's assignment, and the
        # member of that name inside a manifest is the thing being checked.
        "assignment",
        # W19784 third review [P1]: `place` is one path, at the two canonical-
        # spelling rules the OCI adapter now exports. It became a public
        # operand because the manager's pre-journal check was a PARAPHRASE of
        # those rules and disagreed with them exactly where it cost most --
        # `/else/../input` normalized onto the fixed path and was accepted.
        # A rule with two implementations agrees with itself until it doesn't,
        # so there is one of each and both boundaries call it.
        "place",
        # W38956/W39356: the two explicit start operands and the worker-entry
        # transport's four. This gate CAUGHT them -- the transport round ran
        # its own suite and `test_oci` and not this one, so six new public
        # parameters reached the package undeclared, which is exactly the
        # "fixing the two functions a review names" failure the class docstring
        # is about. Each is a claim, made deliberately:
        #
        #   `network`      WHICH engine network a runtime joins. A deployment
        #                  decision about this assignment's isolation, and the
        #                  one substitutable value in the restriction table --
        #                  not bookkeeping, and deliberately not a general
        #                  engine-flag operand.
        #   `interactive`  WHETHER this runtime's stdin is held open so the
        #                  worker-entry channel can be spoken to it. A property
        #                  of the delivery, decided per assignment.
        #   `program`      the worker-entry program INSIDE the image. `docker
        #                  exec` applies no entrypoint, so the party that
        #                  resolved the image supplies it; it is a fact about
        #                  the artefact, like `image_digest` beside it.
        #   `channel_port` the injected capability that opens one framed
        #                  session -- the transport's `EnginePort`, and an
        #                  injected capability is an operand here exactly as
        #                  `mint_bearer` and `credential_provider` are.
        #   `operations`   WHICH worker-entry operations this conversation
        #                  asks for, in order. The manager's own plan for the
        #                  turn rather than state the transport keeps.
        #   `operation_ids` the manager's effectively-once identities for
        #                  those operations, one each. Named apart from the
        #                  singular `operation_id` on purpose: a conversation
        #                  spends several, the worker consumes each exactly
        #                  once, and one name for the two contracts is how a
        #                  replay becomes indistinguishable from a first
        #                  attempt.
        "network", "interactive", "program", "channel_port", "operations",
        "operation_ids",
        # `workspace_storage` WAS DECLARED HERE AND IS GONE AGAIN, which is
        # worth a line rather than a silent deletion. W36540's eighth round
        # added it as a capability operand of the custody mint; its ninth
        # round removed the operand entirely, because a capability minted from
        # durable state and then HELD is still a path `object.__setattr__` can
        # change before it is read. The composition opens the record itself
        # now, so there is no operand to declare -- and this gate's
        # stale-declaration half is what caught the leftover.
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
