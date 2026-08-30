"""W36540 — unconditional custody, asked of a REAL daemon.

`test_custody.py` proves what the manager COMPOSED. This proves what the
custody act DID, and the property is one only a daemon can supply: a directory
a real worker created, at a mode the worker chose, that the manager could not
remove BEFORE the act and can remove AFTER it, with nothing else changed
between the two.

THE ACCEPTANCE SENTENCE THIS ANSWERS: *with a worker-created populated
subdirectory at any mode the worker chose, the manager ... recursively deletes
the attempt's exact workspace and result directories.*

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting the container gate.
"""

import json
import os
import subprocess
import tempfile
import unittest
import uuid

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, custody, workspaces

from . import input_roots
from .test_lifecycle_composition import Lifecycle, MARK


class CustodyRemovesWhatTheWorkerLeaves(Lifecycle):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w36540-")
        self.made = []
        self.addCleanup(self._sweep)
        self.store = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="custody-engine-1",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)
        # THE CANONICAL SPELLING, resolved once for the whole class by the
        # lifecycle fixture: docker answers `sha256:<hex>` and podman the bare
        # hex, and a CONFIGURED identity is required to be canonical.
        self.digest = self.image_digest

    def _sweep(self):
        """The manager cannot always remove this tree -- that IS the defect --
        so the fixture takes it away with the same custodian the case does."""
        for name in self.made:
            subprocess.run([self.engine, "rm", "--force", name],
                           capture_output=True, timeout=120)
        if os.path.exists(self.home):
            try:
                None
            except Exception:
                pass
            subprocess.run(["chmod", "-R", "u+rwX", self.home],
                           capture_output=True, timeout=120)
            subprocess.run(["rm", "-rf", self.home], capture_output=True,
                           timeout=120)

    def allocated(self):
        storage = os.path.join(self.home, "storage")
        os.makedirs(storage, exist_ok=True)
        self.storage = storage
        # THE DEPLOYMENT'S ACT, then the manager's own record read back --
        # which is what the custody mint now requires and what a fixture
        # therefore has to perform rather than shortcut.
        workspaces.configure_workspace_storage(self.store, storage)
        return workspaces.assignment_workspace(self.group, storage,
                                               "attempt-1")

    def worker_leaves(self, place, mode=0o700):
        """A REAL worker, creating the exact shape the defect is about."""
        name = f"{MARK}-w36540-{uuid.uuid4().hex[:10]}"
        self.made.append(name)
        program = (
            "import os\n"
            "os.makedirs('/workspace/worker-made-dir/nested', exist_ok=True)\n"
            "open('/workspace/worker-made-dir/nested/deep.txt','w')"
            ".write('the worker got this far')\n"
            f"os.chmod('/workspace/worker-made-dir/nested', {mode})\n"
            "print(os.getuid(), os.getgid())\n")
        done = subprocess.run(
            [self.engine, "run", "--rm", "--name", name, "--user", "65532:65532",
             "--group-add", str(self.group.gid),
             "--mount", f"type=bind,source={place},target=/workspace",
             "--entrypoint", "python3", self.image, "-c", program],
            capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])
        return done.stdout.decode("utf-8").strip()

    def worker_leaves_nested_barriers(self, place):
        """Two hostile directory barriers, so one shallow thaw is no proof."""
        name = f"{MARK}-w36540-{uuid.uuid4().hex[:10]}"
        self.made.append(name)
        program = (
            "import os\n"
            "os.makedirs('/workspace/outer/inner', exist_ok=True)\n"
            "open('/workspace/outer/inner/deep.txt','w').write('held')\n"
            "os.chmod('/workspace/outer/inner', 0o000)\n"
            "os.chmod('/workspace/outer', 0o000)\n")
        done = subprocess.run(
            [self.engine, "run", "--rm", "--name", name,
             "--user", "65532:65532", "--group-add", str(self.group.gid),
             "--mount", f"type=bind,source={place},target=/workspace",
             "--entrypoint", "python3", self.image, "-c", program],
            capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])

    def spawn(self, argv, *, seconds=None):
        """The engine port's run operation, over a real process.

        W43974 review 2026-08-30T05:28:16Z [P0]: `seconds` is the caller's
        deadline and `subprocess.run(timeout=)` is what honours it — it kills
        the child and waits for it before raising, so the call is genuinely
        OVER when this returns or raises. A capability that could not take
        this operand is refused by `custody_act` before any engine call, which
        is why the fixture takes it rather than ignoring it.
        """
        finished = subprocess.run(argv, capture_output=True,
                                  timeout=seconds if seconds else 300)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}

    def custody(self, operation):
        """One custody act over THIS case's allocated attempt.

        It takes no roots operand, and that is the sixth review's correction
        showing through at the call site: the mount is derived from the
        allocation, so there is no object a case could hand over here that
        would choose a different directory.

        REVIEW [P0] ROUND TEN AT THE CALL SITE. There is no argv here either.
        The case supplies the engine PORT and the act performs itself, so
        what a case holds afterwards is the typed answer — and the JSON
        extraction that used to live in every one of these cases is now the
        act's own, which is where it belongs.
        """
        # W43974: THE NAME IS DERIVED and this fixture no longer invents one.
        # It registers the derived identity for teardown instead, which is the
        # same thing a restarted manager can do and a caller-chosen name never
        # allowed.
        self.made.append(custody._custody_identity(
            self.storage, "attempt-1", "workspace", operation))
        return custody.custody_act(
            self.engine, self.spawn, image_digest=self.digest,
            store=self.store, assignment_id="attempt-1", operation=operation)

    def stranded(self, operation="normalize", seconds=120):
        """A REAL helper left behind by a manager that died mid-act.

        Started detached and WITHOUT `--rm` under the identity this act will
        derive, which is exactly the state `--rm` does not cover: the engine
        removes a foreground helper when the act ends, and there was no act.
        """
        name = custody._custody_identity(self.storage, "attempt-1",
                                         "workspace", operation)
        self.made.append(name)
        done = subprocess.run(
            [self.engine, "run", "--detach", "--name", name,
             "--user", "65532:65532", "--entrypoint", "python3", self.image,
             "-c", f"import time; time.sleep({seconds})"],
            capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])
        return name

    def present(self, name):
        """Whether the engine still knows this exact identity."""
        done = subprocess.run(
            [self.engine, "ps", "--all", "--no-trunc", "--format", "{{.Names}}",
             "--filter", f"name={name}"], capture_output=True, timeout=120)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])
        return name in done.stdout.decode("utf-8").split()

    # -- W43974: the helper a dead manager left behind ---------------------

    def test_a_stranded_running_helper_is_reclaimed_and_the_act_completes(self):
        """THE OUTCOME THIS CHILD EXISTS FOR, against a real daemon.

        A helper is left running under the derived identity, as a manager
        killed mid-act would leave one. A fresh act finds it — because the
        identity is derivable and no longer a caller's choice — ends it,
        proves it absent, and performs the custody it was asked for.
        """
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        left = self.stranded()
        self.assertTrue(self.present(left))

        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertEqual(acted.answer["custody"], "normalize")
        self.assertFalse(self.present(left))
        # AND THE TREE IS THE MANAGER'S AGAIN, which is what the custody was
        # for -- a reclamation that did not end with the act performed would
        # have proved only that `docker rm` works.
        self.assertTrue(workspaces.discard_workspace(self.storage,
                                                     "attempt-1"))

    def test_a_stranded_exited_helper_is_reclaimed_too(self):
        """`--rm` never ran for it, so an exited container answering to the
        identity is exactly as much in the way as a running one."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        left = self.stranded(seconds=0)
        subprocess.run([self.engine, "wait", left], capture_output=True,
                       timeout=120)
        self.assertTrue(self.present(left))

        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertFalse(self.present(left))

    def test_a_same_prefix_stranger_is_left_running(self):
        """The engine's name filter is a substring match, so a stranger whose
        name CONTAINS the derived identity is returned by it. The exact
        comparison is this manager's, and it leaves the stranger alone."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        derived = custody._custody_identity(self.storage, "attempt-1",
                                            "workspace", "normalize")
        stranger = derived + "-somebody-else"
        self.made.append(stranger)
        done = subprocess.run(
            [self.engine, "run", "--detach", "--name", stranger,
             "--user", "65532:65532", "--entrypoint", "python3", self.image,
             "-c", "import time; time.sleep(120)"],
            capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])

        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertTrue(self.present(stranger),
                        "the stranger was removed by a name it merely "
                        "contains")

    def test_the_derived_identity_survives_a_new_manager_incarnation(self):
        """RESTART DISCOVERY against a real store: a second manager opening
        the same database under a new incarnation derives the identity its
        predecessor used, and reclaims what it left."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        left = self.stranded()

        successor = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="custody-engine-after-restart",
            clock=lambda: "2026-08-30T00:00:00.000Z")
        self.addCleanup(successor.close)
        acted = custody.custody_act(
            self.engine, self.spawn, image_digest=self.digest,
            store=successor, assignment_id="attempt-1", operation="normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertFalse(self.present(left))

    # -- the acceptance ---------------------------------------------------

    def test_the_manager_removes_the_tree_only_after_the_custody_act(self):
        """THE ACCEPTANCE, in one case, and BOTH halves matter.

        The refusal before the act is what makes the removal after it mean
        something: without it this would prove only that `rm` works.
        """
        roots = self.allocated()
        place = roots["workspace"]
        self.worker_leaves(place)

        # BEFORE: the manager fails closed, naming the owner in the way.
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage, "attempt-1")
        self.assertIn("owned by uid", caught.exception.message)

        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        answered = acted.answer
        self.assertEqual(answered["custody"], "normalize")
        # A TUPLE, and the type is the correction rather than an incidental.
        # W36540 review 2026-08-30T04:07:53Z [P1]: the retained account is
        # frozen all the way down, and the only non-bypassable freeze for a
        # JSON list is a tuple -- a guarded `list` subclass would still equal
        # a list here and `list.append` would still reach past it, which is
        # the shape this record spent six rounds learning not to accept.
        self.assertEqual(answered["running_as"], (65532, 65532))
        self.assertGreater(answered["entries"], 0, acted.rendered)

        # AFTER: the same call, unchanged, and the tree is gone.
        self.assertTrue(workspaces.discard_workspace(self.storage,
                                                     "attempt-1"))
        self.assertFalse(os.path.exists(os.path.join(self.storage,
                                                     "attempt-1")))

    def test_it_holds_at_every_mode_the_worker_can_choose(self):
        """UNCONDITIONAL means the worker does not get a vote.

        `0700` is the umask case; `0000` is the hostile one -- a directory
        with no permission bits at all, which its OWNER may still chmod.
        """
        for mode in (0o700, 0o500, 0o000):
            with self.subTest(mode=oct(mode)):
                roots = self.allocated()
                place = roots["workspace"]
                self.worker_leaves(place, mode=mode)
                acted = self.custody("normalize")
                self.assertTrue(acted.ok, acted.diagnostic)
                self.assertTrue(
                    workspaces.discard_workspace(self.storage, "attempt-1"))

    def test_nested_hostile_modes_do_not_hide_objects_from_custody(self):
        roots = self.allocated()
        self.worker_leaves_nested_barriers(roots["workspace"])
        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertTrue(workspaces.discard_workspace(self.storage,
                                                     "attempt-1"))

    def test_the_custodian_touches_nothing_it_does_not_own(self):
        """The manager's own directories are not the custodian's to change,
        and the act reports how many it left alone."""
        roots = self.allocated()
        place = roots["workspace"]
        self.worker_leaves(place)
        # THE DELIVERIES ARE NOT REACHABLE AT ALL NOW, which is the [P0]
        # correction: the mount is the workspace, not the assignment home. So
        # what this case can still measure is that the manager-owned roots
        # OUTSIDE the mount are untouched, and that the mounted root itself --
        # which the manager owns -- keeps its exact mode through the act.
        before = {one: os.lstat(roots[one]).st_mode & 0o7777
                  for one in ("inputs", "workspace")}
        acted = self.custody("normalize")
        self.assertTrue(acted.ok, acted.diagnostic)
        self.assertGreater(acted.answer["entries"], 0, dict(acted.answer))
        for one, mode in before.items():
            self.assertEqual(os.lstat(roots[one]).st_mode & 0o7777, mode, one)

    def test_the_helper_does_not_outlive_its_act(self):
        """SHORT-LIVED, measured: the engine is asked afterwards."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        name = f"{MARK}-custody-{uuid.uuid4().hex[:10]}"
        self.made.append(name)
        custody.custody_act(
            self.engine, self.spawn, image_digest=self.digest,
            store=self.store, assignment_id="attempt-1",
            operation="normalize")
        found = subprocess.run(
            [self.engine, "ps", "--all", "--quiet", "--filter", f"name={name}"],
            capture_output=True, timeout=120)
        self.assertEqual(found.stdout.decode("utf-8").strip(), "",
                         "the custody helper outlived its act")

    def test_the_inspection_sees_the_attempt_and_nothing_above_it(self):
        """ONE MOUNT: absent rather than denied."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        acted = self.custody("inspect")
        self.assertTrue(acted.ok, acted.diagnostic)
        answered = acted.answer
        paths = [one["path"] for one in answered["entries"]]
        self.assertIn("worker-made-dir", paths)
        # REVIEW [P0]: the deliveries are ABSENT, not merely skipped.
        for forbidden in ("credentials", "credential-state", "inputs",
                          "custody"):
            self.assertNotIn(forbidden, paths, dict(answered))
        for forbidden in ("credential-state", "credentials", "custody",
                          "inputs"):
            self.assertFalse(
                any(one == forbidden or one.startswith(forbidden + "/")
                    for one in paths),
                f"the custody helper could see the manager-owned {forbidden} "
                f"tree: {paths}")
        for one in paths:
            self.assertFalse(one.startswith(".."), one)
            self.assertFalse(os.path.isabs(one), one)

    def test_a_verb_outside_the_vocabulary_never_reaches_the_engine(self):
        roots = self.allocated()
        reached = []
        with self.assertRaises(ContractRefusal):
            custody.custody_act(
                self.engine, lambda argv: reached.append(argv),
                image_digest=self.digest,
                store=self.store, assignment_id="attempt-1",
                operation="sh")
        self.assertEqual(reached, [], "a refused verb reached the engine")


class DockerCustody(CustodyRemovesWhatTheWorkerLeaves, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanCustody(CustodyRemovesWhatTheWorkerLeaves, unittest.TestCase):
    engine = "podman"
    required = False
