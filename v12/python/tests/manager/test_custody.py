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
        self.held = self.custody_root()

    def opened(self):
        from baton_v12.worker_manager import ControlStore
        store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="custody-1",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(store.close)
        return store

    def custody_root(self, which="workspace"):
        """The capability, minted from the layout this manager established."""
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        return custody.attempt_custody_root(roots, which)

    def vector(self, **overrides):
        operands = {"image_digest": IMAGE, "name": "baton-custody-1",
                    "custody": self.held, "operation": "normalize",
                    "workspace_group": self.group}
        operands.update(overrides)
        return custody.custody_vector("docker", **operands)


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
        self.assertIn(f"source={self.held.place}", mount)
        self.assertIn(f"target={custody.CUSTODY_ROOT}", mount)
        self.assertIn("readonly=false", mount)

    def test_an_arbitrary_absolute_path_is_not_a_custody_capability(self):
        """Review [P0]: a repository, a credential root or an unrelated
        sibling cannot be selected, because there is no path operand at all."""
        for wrong in ("/etc", "/home/sl/src", self.root, "relative", None, 5,
                      {"place": "/etc"}):
            with self.subTest(custody=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(custody=wrong)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))

    def test_a_custody_root_cannot_be_constructed_by_a_caller(self):
        with self.assertRaises(ContractRefusal):
            custody.CustodyRoot("/etc", "workspace")

    def test_a_caller_mapping_cannot_launder_an_unrelated_host_root(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        forged = {"inputs": roots["inputs"], "workspace": self.root}
        with self.assertRaises(ContractRefusal):
            custody.attempt_custody_root(forged)

    def test_a_caller_cannot_forge_the_expected_directory_shape(self):
        unrelated = tempfile.TemporaryDirectory(prefix="v12-shaped-forgery-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        with self.assertRaises(ContractRefusal):
            custody.attempt_custody_root(
                {"inputs": inputs, "workspace": workspace})

    def test_a_worker_created_result_symlink_cannot_choose_the_mount(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        result = os.path.join(roots["workspace"], "result")
        os.symlink(self.root, result)
        with self.assertRaises(ContractRefusal):
            custody.attempt_custody_root(roots, "result")

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
        signature = inspect.signature(custody.custody_vector)
        self.assertNotIn("target", signature.parameters)
        self.assertNotIn("custody_root", signature.parameters)

    def test_the_host_path_is_not_a_raw_caller_operand_either(self):
        """An arbitrary absolute host path is not an attempt capability."""
        import inspect
        signature = inspect.signature(custody.custody_vector)
        self.assertNotIn("attempt_root", signature.parameters)


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

    def test_a_group_a_caller_minted_is_refused(self):
        """W33936's rule, one act further along."""
        for wrong in (self.group.gid, None, "1000", object()):
            with self.subTest(workspace_group=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(workspace_group=wrong)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
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
