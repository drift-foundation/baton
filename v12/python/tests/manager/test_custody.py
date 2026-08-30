"""W36540 — the custody vector and its closed vocabulary, daemon-free.

`test_custody_engine.py` asks what a real daemon DID. This asks what the
manager COMPOSED: the closed verb set, the single mount, the identity that
makes the act unconditional, and the operands that do not exist.

THE RULING'S THREE CONSTRAINTS ARE THE THREE THINGS THIS FILE IS ABOUT.
M36166 requires the helper to mount only the exact attempt directory, to run
under the owning worker identity, and to execute only typed manager-owned
operations. Each is asserted against the argv rather than against a docstring.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody, workspaces

from . import input_roots

IMAGE = "sha256:" + "a" * 64


class CustodyCase(unittest.TestCase):

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-")
        self.addCleanup(root.cleanup)
        self.root = root.name
        self.store = self.opened()
        # THE DEPLOYMENT'S OWN RECORD, through the same fixture W33936's
        # matrix uses: a capability read back, never an integer composed here.
        self.group = input_roots.configured_group(self.store)
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        # THE DEPLOYMENT'S OWN RECORD, for the store exactly as for the group.
        # W36540 review [P0]: the mint no longer accepts a path, so a fixture
        # cannot hand it one either -- it has to CONFIGURE the store, which is
        # the deployment's act, and then read the manager's record back.
        workspaces.configure_workspace_storage(self.store, self.storage)
        workspaces.assignment_workspace(self.group, self.storage, "attempt-1")

    def opened(self):
        from baton_v12.worker_manager import ControlStore
        store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="custody-1",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(store.close)
        return store

    def mounted(self, argv):
        """The one bind source this act composed."""
        return argv[argv.index("--mount") + 1]

    def acted(self, **overrides):
        """One custody act, run against a recording engine port.

        W36540 review [P0] round ten: there is no composed argv to ask for any
        more, because `custody_act` performs the act rather than describing
        it. What this fixture holds is what the ENGINE PORT received — which
        is the one place the vector legitimately exists, and the place every
        other vector this manager composes also reaches. Observing it there
        proves what ran; it is not a handoff, because by the time the port
        holds it there is nothing left to retarget.
        """
        operands = {"image_digest": IMAGE, "name": "baton-custody-1",
                    "store": self.store, "assignment_id": "attempt-1",
                    "operation": "normalize"}
        operands.update(overrides)
        self.seen = []

        def run(argv):
            self.seen.append(list(argv))
            return {"status": 0,
                    "stdout": json.dumps({"custody": operands["operation"],
                                          "entries": 3,
                                          "running_as": [65532, 65532]}),
                    "stderr": ""}

        return custody.custody_act("docker", run, **operands)

    def vector(self, **overrides):
        """What the engine port was handed for one act."""
        self.acted(**overrides)
        return self.seen[0]


class TheVocabularyIsClosed(CustodyCase):

    def test_the_six_the_ruling_names_are_the_six_this_build_owns(self):
        self.assertEqual(custody.CUSTODY_OPERATIONS,
                         ("inspect", "read", "hash", "archive", "normalize",
                          "discard"))

    def test_a_verb_outside_the_vocabulary_selects_nothing(self):
        for wrong in ("exec", "sh", "rm -rf /", "NORMALIZE", "", "chmod"):
            with self.subTest(operation=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(operation=wrong)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))

    def test_a_verb_that_is_not_durable_text_is_refused(self):
        for wrong in (None, 5, ["normalize"], {"op": "normalize"}):
            with self.subTest(operation=wrong):
                with self.assertRaises(ContractRefusal):
                    self.vector(operation=wrong)

    def test_the_program_enforces_the_same_set_it_was_composed_from(self):
        """BOTH ENDS OF THE CROSSING, which is why the program carries its own
        copy: a verb that reached it another way selects nothing there either.
        """
        self.assertIn('VERBS = ("inspect", "read", "hash", "archive", '
                      '"normalize", "discard")', custody.CUSTODY_PROGRAM)
        self.assertIn("if verb not in VERBS", custody.CUSTODY_PROGRAM)

    def test_every_advertised_operation_is_an_operation_not_a_placeholder(self):
        """A closed vocabulary is a capability claim, not a future-work list."""
        for operation in custody.CUSTODY_OPERATIONS:
            with self.subTest(operation=operation):
                root = tempfile.TemporaryDirectory(prefix="v12-custody-op-")
                self.addCleanup(root.cleanup)
                with open(os.path.join(root.name, "worker-output"), "w") as held:
                    held.write("one result")
                program = custody.CUSTODY_PROGRAM.replace(
                    'ROOT = "/custody"', f"ROOT = {root.name!r}", 1)
                done = subprocess.run(
                    [sys.executable, "-c", program, operation],
                    capture_output=True, timeout=30)
                self.assertEqual(
                    done.returncode, 0,
                    done.stdout.decode("utf-8", "replace") +
                    done.stderr.decode("utf-8", "replace"))


class ThereIsNoCommandOperand(CustodyCase):

    def test_no_caller_operand_reaches_the_argv_as_a_command(self):
        """The ruling's "never a worker-supplied command", asserted.

        The program is a CONSTANT of the module. The only caller-chosen token
        after `-c` is the verb, and the verb is checked against a closed set
        before it gets there.
        """
        argv = self.vector()
        self.assertEqual(argv[argv.index("-c") + 1], custody.CUSTODY_PROGRAM)
        self.assertEqual(argv[argv.index("-c") + 2], "normalize")
        self.assertEqual(len(argv), argv.index("-c") + 3,
                         "nothing follows the verb")

    def test_the_entrypoint_is_the_managers_own(self):
        argv = self.vector()
        self.assertEqual(argv[argv.index("--entrypoint") + 1], "python3")


class OneMountAndNothingElse(CustodyCase):

    def test_exactly_one_mount_is_composed(self):
        argv = self.vector()
        self.assertEqual(argv.count("--mount"), 1)
        self.assertEqual(argv.count("--volume"), 0)
        self.assertEqual(argv.count("-v"), 0)

    def test_the_mount_is_the_attempt_root_at_a_fixed_target(self):
        argv = self.vector()
        mount = argv[argv.index("--mount") + 1]
        self.assertIn(f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))}", mount)
        self.assertIn(f"target={custody.CUSTODY_ROOT}", mount)
        self.assertIn("readonly=false", mount)

    def test_an_arbitrary_absolute_path_is_not_a_custody_capability(self):
        """A repository, a credential root or an unrelated sibling cannot be
        selected, because there is no path operand at all -- the only thing
        that names a directory here is the deployment's own record."""
        for wrong in ("/etc", "/home/sl/src", self.root, "relative", None, 5,
                      {"place": "/etc"}):
            with self.subTest(store=wrong):
                with self.assertRaises((ContractRefusal, TypeError,
                                        AttributeError)):
                    self.vector(store=wrong)

    def test_the_vector_takes_no_path_bearing_object_to_retarget(self):
        """Review [P0] round nine: the handoff is GONE, not hardened again.

        The vector took a minted `CustodyRoot` and read `.place` off it, so
        `object.__setattr__` on a genuine root put an unrelated directory
        verbatim into `--mount source=...`. Nine rounds of setters, private
        slots and type checks were all on the wrong side of that interval.

        There is no interval now: `custody_act` reads the durable record,
        composes the argv and RUNS it in one act, and its operands are the
        engine port, a store and a NAME. So this asserts the absence rather
        than another refusal — there is nothing left to hand it that could
        carry a path.
        """
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertEqual(list(signature.parameters),
                         ["engine", "run", "image_digest", "name", "store",
                          "assignment_id", "operation", "which"])
        self.assertFalse(hasattr(custody, "CustodyRoot"))
        self.assertFalse(hasattr(custody, "attempt_custody_root"))
        self.assertFalse(hasattr(custody, "custody_vector"))
        # AND THE MOUNT IS THIS ATTEMPT'S OWN, derived rather than supplied.
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            self.mounted(self.vector()))

    def test_the_authenticated_mount_is_not_returned_as_a_mutable_handoff(self):
        """Lookup, composition and execution ARE the same owned act.

        Reviewer regression (2026-08-29T22:28:08Z [P0]). Its original form
        took the returned argv, rewrote the `--mount` member and required the
        unrelated path not to be there — a requirement no returned list can
        meet, which is the review's own point: "a tuple or another frozen argv
        wrapper would not close the boundary". So the case asserts what the
        review actually asked for instead. There is no returned vector: the
        act runs the engine itself and answers a typed result, so a caller has
        neither a host path nor an executable command to retarget.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-vector-retarget-")
        self.addCleanup(unrelated.cleanup)
        answered = self.acted()
        # NOTHING EXECUTABLE AND NOTHING PATH-BEARING CAME BACK.
        self.assertIsInstance(answered, custody.CustodyAnswer)
        self.assertFalse(hasattr(custody, "custody_vector"))
        rendered = repr(answered) + json.dumps(dict(answered.answer))
        for absent in (self.storage, self.root, "--mount", "docker",
                       custody.CUSTODY_ROOT, "type=bind"):
            self.assertNotIn(absent, rendered, absent)
        # AND THE ACT ALREADY HAPPENED. What the port was handed is the one
        # vector that ran; rewriting it afterwards reaches no execution,
        # because there is no second one for a caller to perform.
        argv = self.seen[0]
        argv[argv.index("--mount") + 1] = (
            f"type=bind,source={unrelated.name},"
            f"target={custody.CUSTODY_ROOT},readonly=false")
        self.assertEqual(len(self.seen), 1)
        self.assertNotIn(unrelated.name, json.dumps(dict(answered.answer)))

    def test_the_answer_a_caller_keeps_carries_no_host_path(self):
        """The custodian answers paths relative to its own mount, which is the
        only namespace it knows — so what a holder keeps afterwards names
        nothing on this host."""
        answered = self.acted(operation="inspect")
        self.assertTrue(answered.ok)
        self.assertNotIn(self.storage, json.dumps(dict(answered.answer)))
        for gone in ("place", "source", "root", "argv", "vector"):
            self.assertFalse(hasattr(answered, gone), gone)

    def test_a_custody_answer_cannot_be_minted_by_a_caller(self):
        """An answer is what one act REPORTED, so a caller that could mint one
        could report an act that never happened — the same rule every
        capability in this package is under."""
        with self.assertRaises(TypeError):
            custody.CustodyAnswer("normalize", 0, {}, "")

    def test_a_custody_answer_is_not_revised_by_its_holder(self):
        """An answer somebody can edit is an account that disagrees with what
        happened."""
        answered = self.acted()
        for name, value in (("status", 1), ("operation", "discard"),
                            ("answer", {}), ("_status", 1)):
            with self.subTest(member=name):
                with self.assertRaises(AttributeError):
                    setattr(answered, name, value)
        with self.assertRaises(TypeError):
            answered.answer["custody"] = "discard"

    def test_an_act_that_answered_nothing_is_not_reported_as_custody(self):
        """A zero exit with no readable document is an act this manager cannot
        account for, and custody that cannot be accounted for is not it."""
        for stdout in ("", "not a document", "[1, 2, 3]", "null"):
            with self.subTest(stdout=stdout):
                answered = custody.custody_act(
                    "docker",
                    lambda argv, out=stdout: {"status": 0, "stdout": out,
                                              "stderr": ""},
                    image_digest=IMAGE, name="baton-custody-1",
                    store=self.store, assignment_id="attempt-1",
                    operation="normalize")
                self.assertIsNone(answered.answer)
                self.assertFalse(answered.ok)

    def test_a_failed_act_carries_a_bounded_diagnostic(self):
        answered = custody.custody_act(
            "docker",
            lambda argv: {"status": 3, "stdout": "",
                          "stderr": "x" * (custody.MAX_DIAGNOSTIC * 4)},
            image_digest=IMAGE, name="baton-custody-1", store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertEqual(answered.status, 3)
        self.assertFalse(answered.ok)
        self.assertEqual(len(answered.diagnostic), custody.MAX_DIAGNOSTIC)

    def test_a_caller_mapping_cannot_launder_an_unrelated_host_root(self):
        """There is no mapping operand left to launder anything through.

        The mint took one for six review rounds and read the mount source out
        of it. It now DERIVES the source, so a mapping is simply not one of
        the things it accepts -- and the group slot, which is where a caller
        would try to put one, requires the deployment's own capability.
        """
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        forged = {"inputs": roots["inputs"], "workspace": self.root}
        for wrong in (forged, roots, self.root):
            with self.subTest(operand=type(wrong).__name__):
                with self.assertRaises((ContractRefusal, TypeError,
                                        AttributeError)):
                    self.vector(store=wrong)

    def test_a_caller_cannot_forge_the_expected_directory_shape(self):
        """Reproducing the layout somewhere else buys nothing any more.

        The previous cuts INFERRED authority from two sibling directories
        named `inputs` and `workspace`, which any caller can make. The mint no
        longer looks at a layout a caller assembled: it composes
        `<storage>/<assignment>/workspace` itself, so the forged home is not a
        thing it can be pointed at -- naming it as the storage root reaches a
        home that does not exist there.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-shaped-forgery-")
        self.addCleanup(unrelated.cleanup)
        os.mkdir(os.path.join(unrelated.name, "inputs"))
        os.mkdir(os.path.join(unrelated.name, "workspace"))
        with self.assertRaises((ContractRefusal, TypeError, AttributeError)):
            self.vector(store=unrelated.name)

    def test_a_caller_cannot_select_an_unrelated_storage_root(self):
        """Derivation below a caller path is still caller path selection.

        The previous shape case puts `inputs` and `workspace` directly below
        the supplied storage root, so the added assignment component makes it
        fail structurally. Reproduce the exact layout the mint derives and an
        unrelated ordinary directory becomes a custody mount.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-storage-forgery-")
        self.addCleanup(unrelated.cleanup)
        home = os.path.join(unrelated.name, "attempt-1")
        os.mkdir(home)
        os.mkdir(os.path.join(home, "workspace"))
        with self.assertRaises((ContractRefusal, TypeError, AttributeError)):
            self.vector(store=unrelated.name)
        # AND CONFIGURING IT IS THE ONLY WAY IN, which is the half that makes
        # the refusal above a boundary rather than a type quibble: a second
        # store cannot be configured over the first, so a caller cannot reach
        # this directory by taking the deployment's own route either.
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.configure_workspace_storage(self.store, unrelated.name)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_a_configured_store_capability_cannot_be_retargeted(self):
        """A caller-held wrapper cannot be the durable storage authority.

        The dossier already records that ``object.__setattr__`` reaches every
        slot in this language and that no private/frozen representation closes
        the boundary.  ``WorkspaceStorage.place`` repeats that exact shape: a
        holder can replace the recorded path after configuration, and the
        custody mint reads the replacement without reopening manager-owned
        durable state.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-retarget-store-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "attempt-1", "workspace")
        os.makedirs(workspace)
        # A HELD CAPABILITY CAN STILL BE RETARGETED -- object.__setattr__
        # reaches every slot and no representation closes that, which this
        # dossier has said since round six. What changed is that nothing
        # reads a held one: the vector opens the record itself, so the
        # retarget cannot reach the mount.
        held = workspaces.configured_workspace_storage(self.store)
        object.__setattr__(held, "place", unrelated.name)
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            self.mounted(self.vector()))
        self.assertNotIn(unrelated.name, " ".join(self.vector()))

    def test_a_refused_parent_link_creates_nothing_through_its_target(self):
        """Validate every parent before creating the optional result root.

        DRIVEN THROUGH THE VECTOR, which is the only door left. The aliased
        home sits inside the CONFIGURED store, which is where a worker-era
        alias would actually appear and the only place the derivation looks.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-result-target-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        os.symlink(unrelated.name,
                   os.path.join(self.storage, "attempt-through-link"))
        with self.assertRaises(ContractRefusal):
            self.vector(assignment_id="attempt-through-link", which="result")
        self.assertFalse(os.path.exists(os.path.join(workspace, "result")),
                         "the refused mint created through its parent link")

    def test_an_attempt_identity_cannot_carry_a_path(self):
        """An attempt is NAMED. `boundaries.identity` owns durable text and
        says nothing about path syntax, so a name carrying a separator would
        otherwise compose a home outside the storage root."""
        for named in ("../elsewhere", "a/b", "..", "."):
            with self.subTest(assignment=named):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(assignment_id=named)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))

    def test_a_caller_cannot_retarget_authentic_allocated_roots(self):
        """Nominal provenance is not authority while its paths are mutable."""
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-retargeted-roots-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # THE REFUSAL MOVED EARLIER THAN THIS CASE EXPECTED, and the assertion
        # follows it rather than the other way round. The correction made the
        # allocation answer IMMUTABLE, so the retarget is refused at the write
        # instead of being detected afterwards at the mint -- which is a
        # stronger guarantee: there is no window in which an authentic object
        # holds foreign paths at all. What the case requires is unchanged --
        # a caller cannot retarget an authentic answer -- so both ends are
        # inside the assertion and either one satisfies it.
        with self.assertRaises(ContractRefusal):
            roots["inputs"] = inputs
            roots["workspace"] = workspace
        # AND THE ANSWER IS UNCHANGED: the attempt left nothing behind.
        self.assertNotEqual(roots["workspace"], workspace)
        for closed in (lambda: roots.update({"workspace": workspace}),
                       lambda: roots.pop("workspace"),
                       lambda: roots.setdefault("other", workspace),
                       lambda: roots.clear()):
            with self.assertRaises(ContractRefusal):
                closed()

    def test_in_place_union_cannot_retarget_allocated_roots(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-ior-roots-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        with self.assertRaises(ContractRefusal):
            roots.__ior__({"workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)

    def test_base_dict_methods_cannot_bypass_the_capability_boundary(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-dict-roots-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        # PYTHON REFUSES THIS, NOT US, and that is the correction rather than
        # a shortfall. The previous cut overrode `__setitem__` on a `dict`
        # subclass, so an explicit base-class call reached the mutable builtin
        # underneath and succeeded. The answer is no longer a dict at all, so
        # `dict.__setitem__` fails on its own argument type -- a refusal we
        # could not have written and cannot be talked out of.
        with self.assertRaises((ContractRefusal, TypeError)):
            dict.__setitem__(roots, "workspace", workspace)
        self.assertNotEqual(roots["workspace"], workspace)
        # And the door this type DOES own answers in our own words.
        with self.assertRaises(ContractRefusal):
            roots["workspace"] = workspace

    def test_base_dict_update_cannot_mint_an_unrelated_custody_root(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-dict-mint-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # THE RETARGET CANNOT HAPPEN AT ALL, so the mint is never reached
        # with foreign paths -- which is stronger than detecting them there.
        with self.assertRaises((ContractRefusal, TypeError)):
            dict.update(roots, {"inputs": inputs, "workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)
        # And the derived root is still this attempt's own workspace.
        self.assertIn(f"source={os.path.realpath(roots['workspace'])},",
                      self.mounted(self.vector()))
        self.assertNotIn(os.path.realpath(workspace),
                         " ".join(self.vector()))

    def test_the_private_member_mapping_cannot_retarget_allocated_roots(self):
        """A private NAME is not an immutable representation.

        The wrapper no longer inherits a mutable builtin, but the two paths it
        authorizes still live in an ordinary dict a holder can read through
        the ordinary attribute protocol. Mutating that dict must not turn the
        authentic allocation answer into authority over another host path.
        """
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-member-mint-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # BOTH HALVES, and the second is the one that matters. The backing
        # mapping is now a read-only view over a dict nothing else holds, so
        # the exact sequence this case was written to drive fails at the
        # mutation -- which makes the review's complaint false at its own
        # site.
        with self.assertRaises((AttributeError, TypeError)):
            roots._members.update({"inputs": inputs, "workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)
        # AND THE GUARANTEE DOES NOT REST ON THAT. Six rounds were spent
        # closing doors onto this object; the correction is that the mint no
        # longer reads a path from it at all, so even a successfully edited
        # answer could not choose the mount. Asserted by deriving the root
        # from the allocation operands and finding this attempt's own
        # workspace.
        mount = self.mounted(self.vector())
        self.assertNotIn(os.path.realpath(workspace), mount)
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            mount)

    def test_a_worker_created_result_symlink_cannot_choose_the_mount(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        result = os.path.join(roots["workspace"], "result")
        os.symlink(self.root, result)
        with self.assertRaises(ContractRefusal):
            self.vector(which="result")

    def test_the_mount_is_the_workspace_and_never_its_parent(self):
        """The assignment home holds the deliveries; only the attempt's own
        workspace is mounted."""
        argv = self.vector()
        mount = argv[argv.index("--mount") + 1]
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        self.assertIn(f"source={roots['workspace']},", mount)
        self.assertNotIn(f"source={os.path.dirname(roots['workspace'])},",
                         mount)

    def test_the_container_path_is_not_a_caller_operand(self):
        """A target a caller could choose decides what the program walks."""
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertNotIn("target", signature.parameters)
        self.assertNotIn("custody_root", signature.parameters)

    def test_the_host_path_is_not_a_raw_caller_operand_either(self):
        """An arbitrary absolute host path is not an attempt capability."""
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertNotIn("attempt_root", signature.parameters)

    def test_no_operand_of_the_composition_can_carry_a_path(self):
        """Nine rounds of this Work, asserted as a signature.

        Rounds one to six closed doors onto a caller-held object the mint
        re-read. Round seven found that deriving below a caller's `storage`
        was the same defect one component deeper. Round eight made the store a
        configured record — and round nine found that a capability minted from
        durable state and then HELD is still a path a caller can change with
        `object.__setattr__` before it is read.

        The answer is not a tenth defence. It is that the composition reads
        the durable record itself, so the only operands are this manager's own
        store handle and the attempt's NAME, and nothing path-bearing exists
        for anyone to hold.
        """
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertEqual(list(signature.parameters),
                         ["engine", "run", "image_digest", "name", "store",
                          "assignment_id", "operation", "which"])
        for gone in ("attempt_root", "custody", "storage", "workspace_group",
                     "workspace_storage"):
            self.assertNotIn(gone, signature.parameters)

class TheIdentityIsWhatMakesItUnconditional(CustodyCase):

    def test_it_runs_as_the_owning_worker_identity(self):
        """THE WHOLE MECHANISM, in one assertion.

        The custodian is the same uid the worker ran as, so it OWNS what the
        worker created -- and an owner may chmod its own objects at any mode
        the worker chose. There is no mode a worker can pick that locks it
        out, which is what `unconditional` means here.
        """
        argv = self.vector()
        self.assertEqual(argv[argv.index("--user") + 1], "65532:65532")

    def test_it_carries_the_configured_group_it_needs_to_traverse(self):
        """Measured on a real daemon before it was written: without the group
        the custodian cannot enter the `02770` manager-owned workspace at
        all."""
        argv = self.vector()
        self.assertEqual(argv[argv.index("--group-add") + 1],
                         str(self.group.gid))

    def test_the_group_is_read_from_the_record_rather_than_handed_in(self):
        """W33936's rule, one act further along and one operand fewer.

        The group used to cross as a `WorkspaceGroup` the caller held, which
        is the same shape review [P0] round nine ruled out for the store: a
        capability minted from durable state and then held is a value
        `object.__setattr__` can change before it is read. It is read here
        instead, so an unconfigured deployment refuses at the composition
        rather than at a type check on something somebody passed.
        """
        from baton_v12.worker_manager import ControlStore
        fresh = ControlStore.open(
            os.path.join(self.root, "unconfigured.sqlite3"),
            incarnation="custody-2",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(fresh.close)
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(store=fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_nested_mode_zero_directories_cannot_hide_their_contents(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-depth-")
        self.addCleanup(root.cleanup)
        outer = os.path.join(root.name, "outer")
        inner = os.path.join(outer, "inner")
        os.makedirs(inner)
        with open(os.path.join(inner, "held"), "w") as target:
            target.write("worker-owned")

        def thaw_for_fixture_cleanup():
            for place in (outer, inner):
                if os.path.isdir(place):
                    os.chmod(place, 0o700)

        self.addCleanup(thaw_for_fixture_cleanup)
        os.chmod(inner, 0o000)
        os.chmod(outer, 0o000)
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root.name!r}", 1)
        done = subprocess.run(
            [sys.executable, "-c", program, "normalize"],
            capture_output=True, timeout=30)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        # This process models the custodian and therefore owns `outer`; grant
        # itself traversal only after the act so it can inspect what the act
        # left hidden one level deeper.
        os.chmod(outer, 0o700)
        self.assertEqual(os.lstat(inner).st_mode & 0o070, 0o070)


class EveryObjectMeansLinksToo(CustodyCase):

    def run_program(self, root, operation):
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root!r}", 1)
        return subprocess.run([sys.executable, "-c", program, operation],
                              capture_output=True, timeout=30)

    def test_inspect_reports_a_directory_symlink_without_following_it(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-links-")
        target = tempfile.TemporaryDirectory(prefix="v12-custody-target-")
        self.addCleanup(root.cleanup)
        self.addCleanup(target.cleanup)
        os.symlink(target.name, os.path.join(root.name, "linked-directory"))
        done = self.run_program(root.name, "inspect")
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        answer = json.loads(done.stdout)
        self.assertIn("linked-directory",
                      [one["path"] for one in answer["entries"]])

    def test_discard_unlinks_a_directory_symlink_but_keeps_its_target(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-links-")
        target = tempfile.TemporaryDirectory(prefix="v12-custody-target-")
        self.addCleanup(root.cleanup)
        self.addCleanup(target.cleanup)
        link = os.path.join(root.name, "linked-directory")
        os.symlink(target.name, link)
        done = self.run_program(root.name, "discard")
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        self.assertFalse(os.path.lexists(link))
        self.assertTrue(os.path.isdir(target.name))


class TheReadingActsAreStreamedAndHonestlyBounded(CustodyCase):
    """Review [P1]: `read`, `hash` and `archive` each slurped a whole file.

    Two separate defects came out of one line. A worker file larger than the
    helper's memory bound ENDED the custody act, so a worker could switch
    custody off by writing a big file -- which is exactly the shape of thing
    "unconditional" rules out. And `read` answered a 4096-byte prefix passed
    through `decode("utf-8", "replace")`, which is lossy twice over: it
    truncated without saying so, and it replaced every non-UTF-8 byte with
    U+FFFD, so what came back was neither the file nor a recoverable prefix.
    """

    # THE ADDRESS-SPACE BOUND THIS SUITE IMPOSES, and it is what makes the
    # streaming case a proof rather than an illustration. The helper runs
    # under `--memory 512m` on a daemon; a bare subprocess has no bound at
    # all, so a slurping implementation would pass a large-file case here by
    # simply using the host's RAM. `RLIMIT_AS` reproduces the constraint
    # daemon-free: a whole-file read of the fixture below cannot fit, and a
    # chunked one is never close.
    ADDRESS_SPACE = 192 << 20

    def run_program(self, root, operation, bounded=False):
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root!r}", 1)
        limit = None
        if bounded:
            import resource

            def limit():                                   # noqa: F811
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (self.ADDRESS_SPACE, self.ADDRESS_SPACE))

        return subprocess.run([sys.executable, "-c", program, operation],
                              capture_output=True, timeout=300,
                              preexec_fn=limit)

    def written(self, body, name="left-behind"):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-reading-")
        self.addCleanup(root.cleanup)
        with open(os.path.join(root.name, name), "wb") as target:
            target.write(body)
        return root.name

    def answered(self, root, operation, bounded=False):
        done = self.run_program(root, operation, bounded=bounded)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])
        answer = json.loads(done.stdout)
        return {one["path"]: one for one in answer["entries"]}, answer

    def test_a_file_larger_than_the_helpers_memory_bound_is_still_hashed(self):
        """THE PROPERTY A WORKER MUST NOT BE ABLE TO SWITCH OFF.

        The custody act is run under an address-space bound smaller than the
        file, and a COMPLETE digest is still required back. A whole-file read
        cannot satisfy both; a chunked one satisfies both without noticing.
        """
        import hashlib
        body = b"w36540-streaming-proof-" * (14 << 20)      # ~322 MiB
        self.assertGreater(len(body), self.ADDRESS_SPACE,
                           "the fixture must exceed the bound it proves")
        root = self.written(body)
        entries, _answer = self.answered(root, "hash", bounded=True)
        one = entries["left-behind"]
        self.assertEqual(one["bytes"], len(body))
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())

    def test_the_bound_this_suite_imposes_can_actually_be_reached(self):
        """A bound nothing can hit proves nothing about the code under it.

        This drives the SUPERSEDED behaviour -- one `handle.read()` of the
        whole file -- under the same limit and requires it to fail. Without
        it, the case above would pass against a slurping implementation on any
        host with enough RAM, which is exactly how the defect survived.
        """
        body = b"w36540-streaming-proof-" * (14 << 20)
        root = self.written(body)
        slurping = custody.CUSTODY_PROGRAM.replace(
            "chunk = handle.read(CHUNK)", "chunk = handle.read()", 1)
        program = slurping.replace('ROOT = "/custody"', f"ROOT = {root!r}", 1)

        import resource

        def limit():
            resource.setrlimit(resource.RLIMIT_AS,
                               (self.ADDRESS_SPACE, self.ADDRESS_SPACE))

        done = subprocess.run([sys.executable, "-c", program, "hash"],
                              capture_output=True, timeout=300,
                              preexec_fn=limit)
        self.assertNotEqual(done.returncode, 0,
                            "the whole-file read fitted inside the bound, so "
                            "the streaming case above proves nothing")

    def test_read_carries_bytes_unmangled_and_says_when_it_is_partial(self):
        """Non-UTF-8 bytes are what a worker leaves; U+FFFD is not them."""
        import base64
        import hashlib
        body = bytes(range(256)) * 8
        root = self.written(body)
        entries, _answer = self.answered(root, "read")
        one = entries["left-behind"]
        self.assertTrue(one["complete"])
        self.assertEqual(base64.b64decode(one["content_base64"]), body)
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())

    def test_a_partial_read_is_declared_rather_than_silently_truncated(self):
        import base64
        import hashlib
        body = b"x" * ((1 << 16) + 4096)
        root = self.written(body)
        entries, _answer = self.answered(root, "read")
        one = entries["left-behind"]
        # THE WHOLE FILE IS STILL MEASURED AND DIGESTED, which is what makes
        # the partial carry an evidence bound rather than a blind spot.
        self.assertFalse(one["complete"])
        self.assertEqual(one["bytes"], len(body))
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())
        self.assertEqual(len(base64.b64decode(one["content_base64"])),
                         1 << 16)

    def test_archive_says_it_is_a_manifest_rather_than_content(self):
        """An open ruling, declared in the answer instead of implied by it.

        `archive` returns a description of what was there and not the bytes.
        Whether that satisfies M36166's `archive` is recorded as an open
        question in the finding; what this case fixes is that the answer no
        longer LOOKS like content custody while being a manifest.
        """
        root = self.written(b"held")
        _entries, answer = self.answered(root, "archive")
        self.assertEqual(answer["content"], "manifest-only")
        self.assertIn("tree_digest", answer)


class TheHelperIsShortLivedAndRestricted(CustodyCase):

    def test_the_engine_removes_it_when_the_act_ends(self):
        """`--rm` and foreground: nothing it creates outlives the act, and a
        crash between start and ending leaks no capability to reclaim."""
        argv = self.vector()
        self.assertIn("--rm", argv)
        self.assertNotIn("--detach", argv)

    def test_every_unconditional_restriction_is_composed(self):
        argv = self.vector()
        for flag, value in (("--cap-drop", "ALL"),
                            ("--security-opt", "no-new-privileges"),
                            ("--network", "none")):
            self.assertIn(flag, argv)
            self.assertIn(value, argv)
        self.assertIn("--read-only", argv)

    def test_no_network_credential_or_repository_reaches_it(self):
        """ABSENT rather than denied, which is the stronger statement."""
        argv = self.vector()
        joined = " ".join(argv)
        self.assertIn("--network none", joined)
        for absent in ("credential", "launch", "/home/sl/src"):
            self.assertNotIn(absent, joined)

    def test_an_image_this_build_cannot_name_exactly_is_refused(self):
        for wrong in ("latest", "python:3.13", "sha256:zz", ""):
            with self.subTest(image_digest=wrong):
                with self.assertRaises(ContractRefusal):
                    self.vector(image_digest=wrong)


if __name__ == "__main__":
    unittest.main()
