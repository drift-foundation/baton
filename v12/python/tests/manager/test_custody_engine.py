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

    def minted(self, which="workspace"):
        """THE CAPABILITY, DERIVED from the allocation -- never a host path
        and, since W36540's sixth review, never read off an object either."""
        return custody.attempt_custody_root(self.group, self.storage,
                                            "attempt-1", which)

    def custody(self, operation):
        """One custody act over THIS case's allocated attempt.

        It takes no roots operand, and that is the sixth review's correction
        showing through at the call site: the mount is derived from the
        allocation, so there is no object a case could hand over here that
        would choose a different directory.
        """
        name = f"{MARK}-custody-{uuid.uuid4().hex[:10]}"
        self.made.append(name)
        argv = custody.custody_vector(
            self.engine, image_digest=self.digest, name=name,
            custody=self.minted(), operation=operation,
            workspace_group=self.group)
        done = subprocess.run(argv, capture_output=True, timeout=300)
        return done.returncode, done.stdout.decode("utf-8", "replace")

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

        code, answer = self.custody("normalize")
        self.assertEqual(code, 0, answer)
        answered = json.loads(answer.strip().splitlines()[-1])
        self.assertEqual(answered["custody"], "normalize")
        self.assertEqual(answered["running_as"], [65532, 65532])
        self.assertGreater(answered["entries"], 0, answered)

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
                code, _answer = self.custody("normalize")
                self.assertEqual(code, 0)
                self.assertTrue(
                    workspaces.discard_workspace(self.storage, "attempt-1"))

    def test_nested_hostile_modes_do_not_hide_objects_from_custody(self):
        roots = self.allocated()
        self.worker_leaves_nested_barriers(roots["workspace"])
        code, answer = self.custody("normalize")
        self.assertEqual(code, 0, answer)
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
        code, answer = self.custody("normalize")
        self.assertEqual(code, 0, answer)
        answered = json.loads(answer.strip().splitlines()[-1])
        self.assertGreater(answered["entries"], 0, answered)
        for one, mode in before.items():
            self.assertEqual(os.lstat(roots[one]).st_mode & 0o7777, mode, one)

    def test_the_helper_does_not_outlive_its_act(self):
        """SHORT-LIVED, measured: the engine is asked afterwards."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        name = f"{MARK}-custody-{uuid.uuid4().hex[:10]}"
        argv = custody.custody_vector(
            self.engine, image_digest=self.digest, name=name,
            custody=self.minted(),
            operation="normalize", workspace_group=self.group)
        subprocess.run(argv, capture_output=True, timeout=300)
        found = subprocess.run(
            [self.engine, "ps", "--all", "--quiet", "--filter", f"name={name}"],
            capture_output=True, timeout=120)
        self.assertEqual(found.stdout.decode("utf-8").strip(), "",
                         "the custody helper outlived its act")

    def test_the_inspection_sees_the_attempt_and_nothing_above_it(self):
        """ONE MOUNT: absent rather than denied."""
        roots = self.allocated()
        self.worker_leaves(roots["workspace"])
        code, answer = self.custody("inspect")
        self.assertEqual(code, 0, answer)
        answered = json.loads(answer.strip().splitlines()[-1])
        paths = [one["path"] for one in answered["entries"]]
        self.assertIn("worker-made-dir", paths)
        # REVIEW [P0]: the deliveries are ABSENT, not merely skipped.
        for forbidden in ("credentials", "credential-state", "inputs",
                          "custody"):
            self.assertNotIn(forbidden, paths, answered)
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
        with self.assertRaises(ContractRefusal):
            custody.custody_vector(
                self.engine, image_digest=self.digest, name="baton-custody-x",
                custody=self.minted(),
                operation="sh", workspace_group=self.group)


class DockerCustody(CustodyRemovesWhatTheWorkerLeaves, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanCustody(CustodyRemovesWhatTheWorkerLeaves, unittest.TestCase):
    engine = "podman"
    required = False
